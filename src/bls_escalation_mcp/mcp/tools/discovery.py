from __future__ import annotations

from bls_escalation_mcp.db.connection import initialize_database
from bls_escalation_mcp.models.enums import BLSProgram
from bls_escalation_mcp.models.series import (
    SeriesMetadata,
    SeriesSearchRequest,
    SeriesSearchResult,
)
from bls_escalation_mcp.repositories.series import SeriesRepository
from bls_escalation_mcp.services.series_catalogue import SeriesCatalogueService


def _catalogue_service() -> SeriesCatalogueService:
    initialize_database()
    return SeriesCatalogueService(SeriesRepository())


def search_series(request: SeriesSearchRequest) -> list[SeriesSearchResult]:
    """Find BLS series records by simple text and program filters."""
    service = _catalogue_service()
    return service.search(request)


def describe_series(series_id: str) -> SeriesMetadata | None:
    """Return a series record by ID."""
    service = _catalogue_service()
    return service.get(series_id)


def find_related_series(
    series_id: str, programs: list[BLSProgram] | None = None
) -> list[SeriesMetadata]:
    """TODO: implement semantic or structural matching to related series."""
    del programs
    service = _catalogue_service()
    result = service.get(series_id)
    return [result] if result else []
