"""Database-side receipt of ingestion (the ``ingestion_log`` table).

Records one row per ingested source file. The git-side twin is
``data/manifest.json`` (authoritative); this table is what ships inside
the built database, so a server instance can report the snapshot it was
built from. Both sides are written from the same ``ManifestFile`` model.
"""

from __future__ import annotations

import json

from bls_escalation_mcp.data.manifest import ManifestFile
from bls_escalation_mcp.db.connection import db_connection


class IngestionLogRepository:
    """Persist and list ingestion receipts in SQLite."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path

    def record(self, entry: ManifestFile) -> None:
        with db_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO ingestion_log (
                    file_id, program, kind, source_url, path_in_repo,
                    downloaded_at, bls_last_modified, size_bytes, sha256,
                    ingested_at, ingested_by, rows_parsed, series_loaded,
                    observations_loaded, missing_rows, skipped_rows,
                    period_warnings, skipped_series, status
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(file_id) DO UPDATE SET
                    program = excluded.program,
                    kind = excluded.kind,
                    source_url = excluded.source_url,
                    path_in_repo = excluded.path_in_repo,
                    downloaded_at = excluded.downloaded_at,
                    bls_last_modified = excluded.bls_last_modified,
                    size_bytes = excluded.size_bytes,
                    sha256 = excluded.sha256,
                    ingested_at = excluded.ingested_at,
                    ingested_by = excluded.ingested_by,
                    rows_parsed = excluded.rows_parsed,
                    series_loaded = excluded.series_loaded,
                    observations_loaded = excluded.observations_loaded,
                    missing_rows = excluded.missing_rows,
                    skipped_rows = excluded.skipped_rows,
                    period_warnings = excluded.period_warnings,
                    skipped_series = excluded.skipped_series,
                    status = excluded.status
                """,
                (
                    entry.file_id,
                    entry.program,
                    entry.kind,
                    entry.source_url,
                    entry.path_in_repo,
                    entry.downloaded_at.isoformat()
                    if entry.downloaded_at
                    else None,
                    entry.bls_last_modified,
                    entry.size_bytes,
                    entry.sha256,
                    entry.ingested_at.isoformat(),
                    entry.ingested_by,
                    entry.rows_parsed,
                    entry.series_loaded,
                    entry.observations_loaded,
                    entry.missing_rows,
                    json.dumps(entry.skipped_rows, sort_keys=True),
                    json.dumps(entry.period_warnings, sort_keys=True),
                    json.dumps(entry.skipped_series, sort_keys=True),
                    entry.status,
                ),
            )
            conn.commit()

    def list(self) -> list[ManifestFile]:
        """Reconstruct manifest entries from the log's receipt rows."""
        with db_connection(self.database_path) as conn:
            rows = conn.execute(
                "SELECT * FROM ingestion_log ORDER BY file_id"
            ).fetchall()
        entries: list[ManifestFile] = []
        for row in rows:
            entries.append(
                ManifestFile(
                    file_id=row["file_id"],
                    program=row["program"],
                    kind=row["kind"],
                    source_url=row["source_url"],
                    path_in_repo=row["path_in_repo"],
                    downloaded_at=row["downloaded_at"],
                    bls_last_modified=row["bls_last_modified"],
                    size_bytes=row["size_bytes"],
                    sha256=row["sha256"],
                    ingested_at=row["ingested_at"],
                    ingested_by=row["ingested_by"],
                    rows_parsed=row["rows_parsed"],
                    series_loaded=row["series_loaded"],
                    observations_loaded=row["observations_loaded"],
                    missing_rows=row["missing_rows"],
                    skipped_rows=json.loads(row["skipped_rows"] or "{}"),
                    period_warnings=json.loads(row["period_warnings"]),
                    skipped_series=json.loads(row["skipped_series"] or "{}"),
                    status=row["status"],
                )
            )
        return entries
