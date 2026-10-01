from __future__ import annotations

from bls_escalation_mcp.models.series import SeriesMetadata


class ECILoader:
    """TODO: map authoritative ECI fields after confirming the schema."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path

    def load(self) -> int:
        # TODO: parse real ECI bulk files and upsert to the catalogue.
        return 0

    def parse_metadata(self, records: list[dict]) -> list[SeriesMetadata]:
        return []
