from __future__ import annotations

from bls_escalation_mcp.models.series import (
    SeriesMetadata,
    SeriesSearchRequest,
    SeriesSearchResult,
)
from bls_escalation_mcp.repositories.series import SeriesRepository


class SeriesCatalogueService:
    """Small metadata search service for BLS series."""

    def __init__(self, repository: SeriesRepository) -> None:
        self.repository = repository

    def get(self, series_id: str) -> SeriesMetadata | None:
        return self.repository.get(series_id)

    def search(self, request: SeriesSearchRequest) -> list[SeriesSearchResult]:
        matches = self.repository.search(request)
        return [
            SeriesSearchResult(
                series=series,
                match_score=1.0 if request.query else None,
                match_reason="match on title or code"
                if request.query
                else None,
            )
            for series in matches
        ]
