from __future__ import annotations

import json
from datetime import UTC, datetime

from bls_escalation_mcp.db.connection import db_connection
from bls_escalation_mcp.models.specifications import EscalationIndexSpec


class SpecificationRepository:
    """Simple repository for saved index specifications."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path

    def save(self, spec: EscalationIndexSpec) -> EscalationIndexSpec:
        now = datetime.now(UTC).isoformat()
        spec.updated_at = datetime.fromisoformat(now)
        payload = json.dumps(spec.model_dump(mode="json"))
        with db_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO saved_index_specs (
                    id, name, spec_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    spec_json = excluded.spec_json,
                    updated_at = excluded.updated_at
                """,
                (
                    spec.id,
                    spec.name,
                    payload,
                    spec.created_at.isoformat(),
                    spec.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return spec

    def get(self, spec_id: str) -> EscalationIndexSpec | None:
        with db_connection(self.database_path) as conn:
            row = conn.execute(
                "SELECT spec_json FROM saved_index_specs WHERE id = ?",
                (spec_id,),
            ).fetchone()
        if row is None:
            return None
        return EscalationIndexSpec.model_validate_json(row["spec_json"])

    def list(self) -> list[EscalationIndexSpec]:
        with db_connection(self.database_path) as conn:
            rows = conn.execute(
                "SELECT spec_json FROM saved_index_specs "
                "ORDER BY updated_at DESC"
            ).fetchall()
        return [
            EscalationIndexSpec.model_validate_json(row["spec_json"])
            for row in rows
        ]

    def delete(self, spec_id: str) -> None:
        with db_connection(self.database_path) as conn:
            conn.execute(
                "DELETE FROM saved_index_specs WHERE id = ?", (spec_id,)
            )
            conn.commit()
