from __future__ import annotations

from typing import Protocol, runtime_checkable

from bls_escalation_mcp.models.series import SeriesMetadata


@runtime_checkable
class BaseLoader(Protocol):
    def load(self) -> int:
        """Load metadata and upsert it to the repository."""

    def parse_metadata(self, records: list[dict]) -> list[SeriesMetadata]:
        """Convert source records to `SeriesMetadata` models."""

    def upsert(self, series: list[SeriesMetadata]) -> None:
        """Persist series metadata to the repository."""
