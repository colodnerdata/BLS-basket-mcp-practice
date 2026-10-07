from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.observations import Observation


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_series_data(
        series_ids: list[str], start_year: int, end_year: int, ctx: Context
    ) -> list[Observation]:
        """Fetch up to 50 known series for at most 20 inclusive years.

        Requires configured BLS_API_KEY; check get_bls_access_status first.
        Results are not cached. Automatic batching is not implemented.
        """
        with domain_errors():
            return await get_services(ctx).observations.fetch(
                series_ids, start_year, end_year
            )
