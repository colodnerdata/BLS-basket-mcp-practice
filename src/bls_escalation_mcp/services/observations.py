from __future__ import annotations

from bls_escalation_mcp.clients.bls import BLSClient
from bls_escalation_mcp.exceptions import BLSAPIError, InvalidPeriodError
from bls_escalation_mcp.models.observations import Observation
from bls_escalation_mcp.services.access import BLSAccessService


class ObservationService:
    """Retrieve observations without persisting or replacing them."""

    def __init__(self, client: BLSClient, access: BLSAccessService) -> None:
        self.client = client
        self.access = access

    async def fetch(
        self, series_ids: list[str], start_year: int, end_year: int
    ) -> list[Observation]:
        if start_year <= 0 or end_year < start_year:
            raise InvalidPeriodError(
                "Years must be positive and end_year must be >= start_year."
            )
        self.access.require_configured()
        limits = self.access.limits
        if len(series_ids) > limits.series_per_query:
            raise BLSAPIError(
                "At most 50 series per call; automatic batching is deferred. "
                "See setup://bls-api and docs/bls_api.md."
            )
        if end_year - start_year + 1 > limits.years_per_query:
            raise BLSAPIError(
                "At most 20 inclusive calendar years per call; automatic "
                "batching is deferred. See setup://bls-api and "
                "docs/bls_api.md."
            )
        return await self.client.get_series_observations(
            series_ids, start_year, end_year
        )
