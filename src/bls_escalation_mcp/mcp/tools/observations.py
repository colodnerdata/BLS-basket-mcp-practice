from __future__ import annotations

from bls_escalation_mcp.clients.bls import BLSClient
from bls_escalation_mcp.models.observations import Observation


async def get_series_data(
    series_ids: list[str],
    start_year: int,
    end_year: int,
) -> list[Observation]:
    """Fetch known BLS series observations for a bounded year range."""
    client = BLSClient()
    return await client.get_series_observations(
        series_ids, start_year, end_year
    )
