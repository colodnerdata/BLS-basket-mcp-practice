from __future__ import annotations

from bls_escalation_mcp.clients.bls import BLSClient
from bls_escalation_mcp.exceptions import InvalidPeriodError
from bls_escalation_mcp.models.observations import Observation


class ObservationService:
    """Retrieve observations without persisting or replacing them."""

    def __init__(self, client: BLSClient) -> None:
        self.client = client

    async def fetch(
        self, series_ids: list[str], start_year: int, end_year: int
    ) -> list[Observation]:
        if start_year <= 0 or end_year < start_year:
            raise InvalidPeriodError(
                "Years must be positive and end_year must be >= start_year."
            )
        return await self.client.get_series_observations(
            series_ids, start_year, end_year
        )
