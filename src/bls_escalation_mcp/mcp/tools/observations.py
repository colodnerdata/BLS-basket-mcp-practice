from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.observations import Observation


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_series_data(
        series_ids: list[str], start_year: int, end_year: int, ctx: Context
    ) -> list[Observation]:
        """Fetch known BLS series for a year range without caching results."""
        with domain_errors():
            return await get_services(ctx).observations.fetch(
                series_ids, start_year, end_year
            )
