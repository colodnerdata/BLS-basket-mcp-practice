"""Verify the ingestion manifest: git record vs files vs database.

Checks, all offline (part of ``poe check``):

1. Every manifest file with ``path_in_repo`` exists, and its size and
   sha256 match — a silent upstream or local revision surfaces here.
2. Re-parsing each checked-in file reproduces the recorded file-level
   facts: row/series counts, missing-row counts, period-code warnings, and
   ECI eligibility skips — all derivable from the file alone. Counts that
   depend on catalog membership (``observations_loaded``,
   ``skipped_rows``) are intentionally not recomputed here; they are
   verified against the database receipt in check 3.
3. When a database exists (default ``./bls_catalog.db``), its
   ``ingestion_log`` receipt must agree with the manifest on file count
   and per-file hash/counts. No database means check 3 is skipped and
   reported, not hidden: CI on a clean checkout verifies the manifest
   against the checked-in slices only.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import cast

from bls_escalation_mcp.data.flat_file import (
    FlatFileProgram,
    eci_is_index,
    parse_code_mapping,
    parse_data_file,
    parse_series_file,
)
from bls_escalation_mcp.data.manifest import (
    DEFAULT_MANIFEST_PATH,
    ManifestFile,
    load_manifest,
)
from bls_escalation_mcp.db.connection import get_database_path
from bls_escalation_mcp.repositories.ingestion_log import (
    IngestionLogRepository,
)


def file_mismatches(entry: ManifestFile, repo_root: Path) -> list[str]:
    """Recompute a checked-in file's facts and compare with the record."""
    if entry.path_in_repo is None:
        return []
    path = repo_root / entry.path_in_repo
    label = f"{entry.file_id} ({entry.path_in_repo})"
    if not path.exists():
        return [f"{label}: file is missing from the checkout"]
    raw = path.read_bytes()
    problems = []
    if len(raw) != entry.size_bytes:
        problems.append(
            f"{label}: size {len(raw)} != recorded {entry.size_bytes}"
        )
    digest = hashlib.sha256(raw).hexdigest()
    if digest != entry.sha256:
        problems.append(f"{label}: sha256 {digest} != {entry.sha256}")

    text = raw.decode("utf-8")
    skipped_series: dict[str, int] = {}
    missing_rows = 0
    if entry.kind == "series":
        # The manifest only records programs whose parsers exist (pc/pd);
        # other programs cannot enter it, so this cast is safe by design.
        program = cast(FlatFileProgram, entry.program)
        parsed_series, _ = parse_series_file(text, program, file_label=label)
        rows_parsed = len(parsed_series)
        if entry.program == "ci":
            # Recompute the ECI eligibility gate so its skips are verified
            # too, not just the survivor count.
            skipped = Counter(
                f"periodicity_{series.periodicity_code}"
                for series in parsed_series
                if not eci_is_index(series)
            )
            skipped_series = dict(skipped)
            series_loaded = len(parsed_series) - sum(skipped.values())
        else:
            series_loaded = rows_parsed
        warnings: dict[str, int] = {}
    elif entry.kind == "mapping":
        key_columns = 2 if entry.file_id.endswith(".product") else 1
        _, rows_parsed = parse_code_mapping(
            text,
            file_label=label,
            key_columns=key_columns,
            name_column=1 if entry.program == "ci" else None,
        )
        series_loaded = 0
        warnings = {}
    else:
        parsed_observations, outcome = parse_data_file(text, file_label=label)
        rows_parsed = len(parsed_observations) + outcome.skipped_rows
        series_loaded = 0
        missing_rows = outcome.missing_rows
        warnings = dict(outcome.warnings)
    for field, actual, recorded in (
        ("rows_parsed", rows_parsed, entry.rows_parsed),
        ("series_loaded", series_loaded, entry.series_loaded),
        ("missing_rows", missing_rows, entry.missing_rows),
    ):
        if actual != recorded:
            problems.append(
                f"{label}: recomputed {field} {actual} != recorded {recorded}"
            )
    if warnings != entry.period_warnings:
        problems.append(
            f"{label}: recomputed period warnings {warnings} != recorded "
            f"{entry.period_warnings}"
        )
    if skipped_series != entry.skipped_series:
        problems.append(
            f"{label}: recomputed skipped series {skipped_series} != "
            f"recorded {entry.skipped_series}"
        )
    return problems


def log_mismatches(
    entries: list[ManifestFile], database_path: str
) -> list[str]:
    """Compare the manifest against the database's ingestion receipt."""
    recorded = {entry.file_id: entry for entry in entries}
    logged = {
        entry.file_id: entry
        for entry in IngestionLogRepository(database_path).list()
    }
    problems: list[str] = []
    for missing in sorted(set(recorded) - set(logged)):
        problems.append(f"{missing}: in the manifest but not ingestion_log")
    for extra in sorted(set(logged) - set(recorded)):
        problems.append(f"{extra}: in ingestion_log but not the manifest")
    for file_id in sorted(set(recorded) & set(logged)):
        current, receipt = recorded[file_id], logged[file_id]
        for field in (
            "sha256",
            "size_bytes",
            "rows_parsed",
            "series_loaded",
            "observations_loaded",
            "missing_rows",
            "skipped_rows",
            "skipped_series",
            "status",
        ):
            if getattr(current, field) != getattr(receipt, field):
                problems.append(
                    f"{file_id}: manifest {field} "
                    f"{getattr(current, field)} != log "
                    f"{getattr(receipt, field)}"
                )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument(
        "--db",
        default=None,
        help="Database to compare (default: configured; skipped if absent)",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help=argparse.SUPPRESS
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    problems: list[str] = []
    for entry in manifest.files:
        problems.extend(file_mismatches(entry, args.repo_root))

    database_path = get_database_path(args.db)
    if Path(database_path).exists():
        problems.extend(log_mismatches(manifest.files, database_path))
        db_note = f"log compared against {database_path}"
    else:
        db_note = f"no database at {database_path}; log comparison skipped"

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(
        f"verify-ingest: {len(manifest.files)} manifest files consistent "
        f"({db_note})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
