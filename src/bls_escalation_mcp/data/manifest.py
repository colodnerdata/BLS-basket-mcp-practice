"""The ingestion manifest: git's authoritative record of the snapshot.

Per the 2026-10-10 entry in ``docs/DECISIONS.md`` the snapshot is recorded
twice: this file (``data/manifest.json``, in git, authoritative for "what
the database should contain") and the ``ingestion_log`` table (the
database's receipt). ``poe verify-ingest`` checks that they agree and that
checked-in files still hash to what was ingested — so any device can
rebuild the database, and a silent upstream revision surfaces as a hash
mismatch instead of a silent change.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

MANIFEST_SCHEMA_VERSION = 1
DEFAULT_MANIFEST_PATH = Path("data/manifest.json")

FileKind = Literal["series", "mapping", "data"]


class ManifestFile(BaseModel):
    """One ingested source file: provenance plus parse statistics.

    ``downloaded_at`` is ``None`` for the owner-saved snapshot files that
    predate this manifest (their notes and ``bls_last_modified`` carry what
    is known about them).
    """

    file_id: str
    program: str
    kind: FileKind
    source_url: str | None = None
    path_in_repo: str | None = None
    downloaded_at: datetime | None = None
    bls_last_modified: str | None = None
    size_bytes: int
    sha256: str
    ingested_at: datetime
    ingested_by: str
    rows_parsed: int = 0
    series_loaded: int = 0
    observations_loaded: int = 0
    period_warnings: dict[str, int] = Field(default_factory=dict)
    status: Literal["active"] = "active"
    notes: str | None = None


class IngestionManifest(BaseModel):
    """The full manifest document, written deterministically."""

    schema_version: int = MANIFEST_SCHEMA_VERSION
    files: list[ManifestFile] = Field(default_factory=list)

    def upsert(self, entry: ManifestFile) -> None:
        """Replace any existing record of the same file and re-add it."""
        self.files = [f for f in self.files if f.file_id != entry.file_id]
        self.files.append(entry)


def load_manifest(path: Path) -> IngestionManifest:
    """Load ``path``, returning an empty manifest when it does not exist."""
    if not path.exists():
        return IngestionManifest()
    return IngestionManifest.model_validate_json(path.read_text("utf-8"))


def save_manifest(path: Path, manifest: IngestionManifest) -> None:
    """Write the manifest with stable ordering so diffs stay minimal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = manifest.model_copy(
        update={"files": sorted(manifest.files, key=lambda f: f.file_id)}
    )
    payload = json.dumps(
        ordered.model_dump(mode="json"), indent=2, sort_keys=False
    )
    path.write_text(payload + "\n", encoding="utf-8")
