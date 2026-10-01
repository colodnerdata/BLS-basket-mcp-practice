from __future__ import annotations

from bls_escalation_mcp.models.series import SeriesMetadata


class OEWSLoader:
    """TODO: map OEWS fields after confirming the authoritative schema."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path

    def load(self) -> int:
        # TODO: parse OEWS source files and upsert series metadata.
        return 0

    def parse_metadata(self, records: list[dict]) -> list[SeriesMetadata]:
        return []
