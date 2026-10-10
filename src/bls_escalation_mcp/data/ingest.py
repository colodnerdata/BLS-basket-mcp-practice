"""Ingest BLS flat files into the catalogue, observations, and manifest.

Owner-invoked command — deliberately **not** an MCP tool, so judges and
clients cannot trigger ingestion (see ``docs/ROADMAP.md`` M2'):

    uv run --locked poe build-catalogue

ingests the checked-in ``docs/sample_data/`` directory into the configured
database and updates ``data/manifest.json`` (git) plus the
``ingestion_log`` table (the database's receipt). Every ingest is recorded
with the file's sha256, size, counts, and period-code warnings; a later
hash mismatch on re-ingestion surfaces as an explicit manifest change
instead of a silent revision.

The network fetcher that downloads fresh files (conditional GET, one
request at a time, per ``docs/bls_etiquette.md``) is a separate change;
this module ingests local files only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from importlib.metadata import version as package_version
from pathlib import Path
from typing import cast

from bls_escalation_mcp.data.flat_file import (
    PROGRAM_DIR_URLS,
    FlatFileProgram,
    ParsedObservation,
    ParsedSeries,
    parse_code_mapping,
    parse_data_file,
    parse_series_file,
)
from bls_escalation_mcp.data.manifest import (
    DEFAULT_MANIFEST_PATH,
    FileKind,
    IngestionManifest,
    ManifestFile,
    load_manifest,
    save_manifest,
)
from bls_escalation_mcp.db.connection import get_database_path
from bls_escalation_mcp.db.schema import initialize_schema
from bls_escalation_mcp.models.enums import BLSProgram, Periodicity
from bls_escalation_mcp.models.observations import Observation
from bls_escalation_mcp.models.periods import EconomicPeriod
from bls_escalation_mcp.models.series import SeriesMetadata
from bls_escalation_mcp.repositories.ingestion_log import (
    IngestionLogRepository,
)
from bls_escalation_mcp.repositories.observations import ObservationRepository
from bls_escalation_mcp.repositories.series import SeriesRepository

_SERIES_NAME = re.compile(r"^(pc|pd)\.series$")
_MAPPING_NAME = re.compile(
    r"^(pc|pd)\.(industry|product|period|footnote|seasonal)(\.txt)?$"
)
_DATA_NAME = re.compile(r"^(pc|pd)\.data\..+?(\.sample|\.head)?$")


_SLICE_SUFFIXES = (".sample", ".head", ".slice")


def classify_file(name: str) -> tuple[FlatFileProgram, FileKind, str] | None:
    """Return ``(program, kind, canonical upstream name)`` or ``None``.

    The owner-saved samples and test slices carry ``.txt``/``.sample``/
    ``.head``/``.slice`` suffixes that the canonical upstream filenames do
    not have; the canonical name is what ``source_url`` and the header
    probe refer to.
    """
    base = name
    for suffix in _SLICE_SUFFIXES:
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    if match := _SERIES_NAME.match(base):
        return cast("FlatFileProgram", match.group(1)), "series", base
    if match := _MAPPING_NAME.match(base):
        program, basename, _ = match.groups()
        return (
            cast("FlatFileProgram", program),
            "mapping",
            (f"{program}.{basename}"),
        )
    if match := _DATA_NAME.match(base):
        return cast("FlatFileProgram", match.group(1)), "data", base
    return None


def _period_of(year: int, code: str) -> EconomicPeriod:
    """A stored begin/end period, keeping the M13 identity distinct."""
    if code == "M13":
        return EconomicPeriod(
            year=year, periodicity=Periodicity.ANNUAL_AVERAGE
        )
    if match := re.fullmatch(r"M(\d{2})", code):
        return EconomicPeriod(
            year=year,
            month=int(match.group(1)),
            periodicity=Periodicity.MONTHLY,
        )
    raise ValueError(f"Unknown begin/end period code {code!r}")


class IngestionService:
    """Parse flat files and persist them with a dual provenance record.

    Domain-persistence boundary: parsing lives in ``data.flat_file``, SQL
    in the repositories, and this service owns how one file becomes rows
    plus one manifest/log entry.
    """

    def __init__(self, database_path: str | None, manifest_path: Path) -> None:
        self.database_path = database_path
        self.manifest_path = manifest_path
        self.series_repo = SeriesRepository(database_path)
        self.observation_repo = ObservationRepository(database_path)
        self.log_repo = IngestionLogRepository(database_path)
        # In-memory per-run context: mapping names and per-series units
        # accumulate as files ingest so later files can use them.
        self.names: dict[tuple[str, str], dict[str, str]] = {}
        self.footnotes: dict[str, dict[str, str]] = {}
        self.units: dict[str, str | None] = {}

    def ingest_file(
        self,
        path: Path,
        *,
        program: FlatFileProgram,
        kind: FileKind,
        canonical_name: str,
        ingested_by: str,
        downloaded_at: datetime | None = None,
        notes: str | None = None,
    ) -> ManifestFile:
        """Ingest one file and record it in the manifest and the log."""
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        label = str(path)
        series_loaded = observations_loaded = 0
        rows_parsed = 0
        warnings: dict[str, int] = {}

        if kind == "mapping":
            key_columns = 2 if canonical_name.endswith(".product") else 1
            mapping, rows_parsed = parse_code_mapping(
                text, file_label=label, key_columns=key_columns
            )
            map_name = canonical_name.rsplit(".", 1)[-1]
            if map_name == "footnote":
                self.footnotes[program] = mapping
            else:
                self.names[(program, map_name)] = mapping
        elif kind == "series":
            series, outcome = parse_series_file(
                text, program, file_label=label
            )
            rows_parsed = len(series)
            warnings = dict(outcome.warnings)
            metadata = [
                self._to_metadata(program, parsed) for parsed in series
            ]
            self.series_repo.upsert_many(metadata)
            series_loaded = len(metadata)
            for meta in metadata:
                self.units[meta.series_id] = meta.units
        else:  # data
            observations_parsed, outcome = parse_data_file(
                text, file_label=label
            )
            rows_parsed = len(observations_parsed) + outcome.skipped_rows
            warnings = dict(outcome.warnings)
            observations = [
                self._to_observation(program, canonical_name, parsed)
                for parsed in observations_parsed
            ]
            self.observation_repo.save_many(observations)
            observations_loaded = len(observations)

        entry = ManifestFile(
            file_id=f"{program}/{canonical_name}",
            program=program,
            kind=kind,
            source_url=PROGRAM_DIR_URLS[program] + canonical_name,
            path_in_repo=_repo_relative(path),
            downloaded_at=downloaded_at,
            bls_last_modified=self._probe_last_modified(
                path.parent, canonical_name
            ),
            size_bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            ingested_at=datetime.now(UTC),
            ingested_by=ingested_by,
            rows_parsed=rows_parsed,
            series_loaded=series_loaded,
            observations_loaded=observations_loaded,
            period_warnings=warnings,
            notes=notes,
        )
        manifest = load_manifest(self.manifest_path)
        manifest.upsert(entry)
        save_manifest(self.manifest_path, manifest)
        self.log_repo.record(entry)
        return entry

    def ingest_directory(
        self,
        directory: Path,
        *,
        ingested_by: str,
        downloaded_at: datetime | None = None,
        notes: str | None = None,
    ) -> list[ManifestFile]:
        """Ingest every recognized file in ``directory``.

        Mappings go first (later files use their names/footnotes), then
        series, then data partitions. Unrecognized files are skipped and
        reported, never parsed on a guess.
        """
        classified = []
        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue
            result = classify_file(path.name)
            if result is None:
                continue
            classified.append((path, *result))
        order = {"mapping": 0, "series": 1, "data": 2}
        classified.sort(key=lambda item: order[item[2]])
        return [
            self.ingest_file(
                path,
                program=program,
                kind=kind,
                canonical_name=canonical,
                ingested_by=ingested_by,
                downloaded_at=downloaded_at,
                notes=notes,
            )
            for path, program, kind, canonical in classified
        ]

    def _to_metadata(
        self, program: FlatFileProgram, parsed: ParsedSeries
    ) -> SeriesMetadata:
        """Build catalogue metadata; PD titles come from mapping files."""
        if program == "pc":
            title = parsed.title or f"PPI NAICS {parsed.industry_code}"
            classification = "NAICS"
            active = True
            description = None
            units = (
                f"index (base {parsed.base_or_bench_date}=100)"
                if parsed.base_or_bench_date
                else "index"
            )
        else:
            product = self.names.get(("pd", "product"), {})
            industry = self.names.get(("pd", "industry"), {})
            title = (
                product.get(f"{parsed.industry_code}\t{parsed.product_code}")
                or industry.get(parsed.industry_code)
                or f"SIC {parsed.industry_code}/{parsed.product_code}"
            )
            classification = "SIC"
            active = False  # PD is the discontinued SIC-based program.
            description = (
                "PPI discontinued SIC-based series (PD); titles are "
                "synthesized from the PD industry/product mappings"
            )
            units = (
                f"index (bench {parsed.base_or_bench_date}=100)"
                if parsed.base_or_bench_date
                else "index"
            )
        return SeriesMetadata(
            series_id=parsed.series_id,
            program=BLSProgram.PPI,
            title=title,
            description=description,
            classification_system=classification,
            classification_code=parsed.industry_code,
            industry_code=parsed.industry_code,
            commodity_code=parsed.product_code,
            periodicity=Periodicity.MONTHLY,
            seasonal_adjustment=(
                parsed.seasonal_code == "S" if parsed.seasonal_code else None
            ),
            units=units,
            first_period=_period_of(parsed.begin_year, parsed.begin_period),
            latest_period=_period_of(parsed.end_year, parsed.end_period),
            active=active,
            source_url=PROGRAM_DIR_URLS[program] + f"{program}.series",
        )

    def _to_observation(
        self,
        program: FlatFileProgram,
        canonical_name: str,
        parsed: ParsedObservation,
    ) -> Observation:
        units = self.units.get(parsed.series_id)
        if units is None:
            existing = self.series_repo.get(parsed.series_id)
            units = existing.units if existing else None
        codes = parsed.footnote_codes.split()
        footnote_map = self.footnotes.get(program, {})
        return Observation(
            series_id=parsed.series_id,
            period=EconomicPeriod(
                year=parsed.year,
                month=parsed.month,
                periodicity=(
                    Periodicity.MONTHLY
                    if parsed.month is not None
                    else Periodicity.ANNUAL_AVERAGE
                ),
            ),
            value=parsed.value,
            units=units,
            retrieved_at=datetime.now(UTC),
            source=PROGRAM_DIR_URLS[program] + canonical_name,
            is_preliminary="P" in codes,
            footnotes=[
                footnote_map.get(code, code) for code in sorted(set(codes))
            ],
        )

    @staticmethod
    def _probe_last_modified(
        directory: Path, canonical_name: str
    ) -> str | None:
        """Use a header probe's JSON (same directory) for Last-Modified."""
        for probe in sorted(directory.glob("*_headers_probe.json")):
            rows = json.loads(probe.read_text("utf-8")).get("files", [])
            for row in rows:
                if row.get("file") == canonical_name:
                    return row.get("last-modified") or None
        return None


def _repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(Path.cwd()).as_posix()
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest local BLS flat files (owner-invoked; offline)."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        action="append",
        default=None,
        help="Directory of flat files (repeatable; default docs/sample_data)",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Database path (default: BLS_DATABASE_PATH / ./bls_catalogue.db)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Manifest path (default: data/manifest.json)",
    )
    parser.add_argument(
        "--downloaded-at",
        default=None,
        help="ISO timestamp the files were downloaded; omit for the "
        "owner-saved pre-manifest snapshot (recorded as unknown)",
    )
    parser.add_argument(
        "--ingested-by",
        default=f"bls_escalation_mcp {package_version('bls_escalation_mcp')}",
        help="Code version label recorded per file (e.g. a git SHA)",
    )
    parser.add_argument(
        "--notes", default=None, help="Free-text provenance note per file"
    )
    args = parser.parse_args()

    database_path = get_database_path(args.db)
    initialize_schema(database_path)
    service = IngestionService(database_path, args.manifest)
    downloaded_at = (
        datetime.fromisoformat(args.downloaded_at)
        if args.downloaded_at
        else None
    )
    directories = args.dir or [Path("docs/sample_data")]
    entries: list[ManifestFile] = []
    for directory in directories:
        entries.extend(
            service.ingest_directory(
                directory,
                ingested_by=args.ingested_by,
                downloaded_at=downloaded_at,
                notes=args.notes,
            )
        )
    manifest: IngestionManifest = load_manifest(args.manifest)
    print(
        f"Ingested {len(entries)} files; catalogue now records "
        f"{sum(e.series_loaded for e in entries)} series rows and "
        f"{sum(e.observations_loaded for e in entries)} observations. "
        f"Manifest: {args.manifest} ({len(manifest.files)} files total). "
        f"Database: {database_path}"
    )
    for entry in entries:
        if entry.period_warnings:
            print(
                f"  {entry.file_id}: skipped period codes "
                f"{entry.period_warnings}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
