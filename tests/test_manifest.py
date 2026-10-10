"""Manifest model and verification-logic tests (offline, fixture files)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bls_escalation_mcp.data.ingest import IngestionService
from bls_escalation_mcp.data.manifest import load_manifest, save_manifest
from bls_escalation_mcp.data.verify import file_mismatches, log_mismatches
from bls_escalation_mcp.db.schema import initialize_schema
from tests.harness import FIXTURES_DIR

FLAT = FIXTURES_DIR / "flatfile"


@pytest.fixture
def harness_env(tmp_path: Path):
    """A tmp database + manifest with the flat-file fixtures ingested."""
    database = tmp_path / "verify.db"
    manifest_path = tmp_path / "manifest.json"
    initialize_schema(str(database))
    service = IngestionService(str(database), manifest_path)
    entries = service.ingest_directory(FLAT, ingested_by="test")
    return database, manifest_path, entries


def test_ingest_records_dual_provenance(harness_env) -> None:
    database, manifest_path, entries = harness_env
    manifest = load_manifest(manifest_path)
    # 13 fixture files: 3 series slices, 7 mapping slices, 2 real data
    # slices plus the header-only (empty) data slice.
    assert len(entries) == len(manifest.files) == 13
    by_id = {entry.file_id: entry for entry in manifest.files}
    series = by_id["pc/pc.series"]
    assert series.series_loaded == 4
    assert series.rows_parsed == 4
    assert len(series.sha256) == 64
    assert series.path_in_repo == "tests/fixtures/bls/flatfile/pc.series.slice"
    observed = by_id["pc/pc.data.20.ComputerProduct"]
    assert observed.observations_loaded == 5
    # The ECI eligibility gate's skips are recorded, not silent.
    ci = by_id["ci/ci.series"]
    assert ci.rows_parsed == 4
    assert ci.series_loaded == 3
    assert ci.skipped_series == {"periodicity_Q": 1}
    # Round-trip stability: save twice, byte-identical.
    first_save = manifest_path.read_text("utf-8")
    save_manifest(manifest_path, manifest)
    assert manifest_path.read_text("utf-8") == first_save


def test_verify_passes_on_consistent_records(harness_env) -> None:
    database, manifest_path, _ = harness_env
    manifest = load_manifest(manifest_path)
    for entry in manifest.files:
        assert file_mismatches(entry, Path.cwd()) == []
    assert log_mismatches(manifest.files, str(database)) == []


def test_verify_catches_tampered_counts_and_hash(harness_env) -> None:
    database, manifest_path, _ = harness_env
    manifest = load_manifest(manifest_path)
    tampered = manifest.files[0].model_copy(
        update={"rows_parsed": 999, "sha256": "0" * 64}
    )
    problems = file_mismatches(tampered, Path.cwd())
    assert any("sha256" in problem for problem in problems)
    assert any("rows_parsed" in problem for problem in problems)


def test_verify_catches_missing_file_and_log_drift(harness_env) -> None:
    database, manifest_path, _ = harness_env
    manifest = load_manifest(manifest_path)
    missing = manifest.files[0].model_copy(
        update={"path_in_repo": "tests/fixtures/bls/flatfile/none.tsv"}
    )
    assert file_mismatches(missing, Path.cwd()) == [
        f"{missing.file_id} (tests/fixtures/bls/flatfile/none.tsv): file "
        "is missing from the checkout"
    ]
    drifted = manifest.files[0].model_copy(update={"observations_loaded": 1})
    problems = log_mismatches([drifted, *manifest.files[1:]], str(database))
    assert any("observations_loaded" in problem for problem in problems)


def test_verify_flags_unlogged_manifest_entries(harness_env) -> None:
    database, manifest_path, _ = harness_env
    manifest = load_manifest(manifest_path)
    extra = manifest.files[0].model_copy(
        update={"file_id": "pc/pc.data.0.Current"}
    )
    problems = log_mismatches([*manifest.files, extra], str(database))
    assert problems == [
        "pc/pc.data.0.Current: in the manifest but not ingestion_log"
    ]
