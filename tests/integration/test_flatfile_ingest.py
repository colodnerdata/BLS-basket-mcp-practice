"""Offline ingestion of the real checked-in samples (docs/sample_data/).

This is the recorded-replay layer for M2': the owner-saved PC/PD files
parse into the catalog and observation store with hand-verified counts
and identities, and the manifest/log dual record agrees afterwards.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from bls_escalation_mcp.data.ingest import IngestionService
from bls_escalation_mcp.data.manifest import load_manifest
from bls_escalation_mcp.data.verify import log_mismatches, main
from bls_escalation_mcp.db.schema import initialize_schema
from bls_escalation_mcp.models.enums import BLSProgram, Periodicity
from bls_escalation_mcp.models.series import SeriesSearchRequest
from bls_escalation_mcp.repositories.observations import ObservationRepository
from bls_escalation_mcp.repositories.series import SeriesRepository

SAMPLES = Path("docs/sample_data")


@pytest.fixture(scope="module")
def ingested(tmp_path_factory):
    """Ingest docs/sample_data once per module into a scratch database."""
    tmp_path = tmp_path_factory.mktemp("ingest")
    database = tmp_path / "catalog.db"
    manifest_path = tmp_path / "manifest.json"
    initialize_schema(str(database))
    service = IngestionService(str(database), manifest_path)
    entries = service.ingest_directory(SAMPLES, ingested_by="test")
    return {
        "database": database,
        "manifest_path": manifest_path,
        "entries": entries,
    }


def test_series_catalog_counts_match_files(ingested) -> None:
    repository = SeriesRepository(str(ingested["database"]))
    series = repository.list_by_program(BLSProgram.PPI)
    # Verified file counts: 4,510 PC + 17,439 PD data rows (bulk_files.md).
    assert len(series) == 4510 + 17439


def test_pc_series_metadata(ingested) -> None:
    repository = SeriesRepository(str(ingested["database"]))
    series = repository.get("PCU1133--1133--")
    assert series is not None
    assert "Logging" in series.title
    assert series.classification_system == "NAICS"
    assert series.classification_code == "1133--"
    assert series.seasonal_adjustment is False
    assert series.periodicity == Periodicity.MONTHLY
    assert series.units == "index (base 198112=100)"
    assert str(series.first_period) == "1981-M12"
    assert str(series.latest_period) == "2026-M08"
    assert series.active is True


def test_pd_series_metadata(ingested) -> None:
    repository = SeriesRepository(str(ingested["database"]))
    series = repository.get("PDU1011#")
    assert series is not None
    assert series.classification_system == "SIC"
    assert series.active is False  # discontinued program
    assert str(series.latest_period) == "2003-M13"  # annual average ends it
    assert series.title  # synthesized from the PD mappings
    assert "discontinued" in (series.description or "")


def test_search_finds_real_series(ingested) -> None:
    repository = SeriesRepository(str(ingested["database"]))
    found = repository.search(
        SeriesSearchRequest(query="Logging", active_only=True)
    )
    assert any(s.series_id.startswith("PCU1133") for s in found)


def test_pc_observations_exact_and_preliminary(ingested) -> None:
    repository = ObservationRepository(str(ingested["database"]))
    observations = repository.get_series_observations("PCU334519334519S")
    by_period = {str(obs.period): obs for obs in observations}
    assert by_period["2025-M02"].value == Decimal("234.780")
    preliminary = by_period["2026-M05"]
    assert preliminary.is_preliminary is True
    assert any("Preliminary" in note for note in preliminary.footnotes)
    assert preliminary.units == "index (base 198506=100)"
    final = by_period["2026-M04"]
    assert final.is_preliminary is False


def test_m13_is_a_distinct_annual_average(ingested) -> None:
    repository = ObservationRepository(str(ingested["database"]))
    observations = repository.get_series_observations("PDU3411#")
    identity = {
        str(obs.period): obs.period.periodicity for obs in observations
    }
    assert identity["1969-M12"] == Periodicity.MONTHLY
    assert identity["1969-M13"] == Periodicity.ANNUAL_AVERAGE
    values = {str(obs.period): obs.value for obs in observations}
    assert values["1969-M13"] == Decimal("35.0") != values["1969-M12"]


def test_manifest_and_log_agree_after_ingest(ingested) -> None:
    manifest = load_manifest(ingested["manifest_path"])
    assert len(manifest.files) == len(ingested["entries"])
    assert log_mismatches(manifest.files, str(ingested["database"])) == []


def test_verify_cli_passes(ingested, monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "verify",
            "--manifest",
            str(ingested["manifest_path"]),
            "--db",
            str(ingested["database"]),
        ],
    )
    assert main() == 0
