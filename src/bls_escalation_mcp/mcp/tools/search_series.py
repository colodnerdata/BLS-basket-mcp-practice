from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.series import (
    SeriesSearchRequest,
    SeriesSearchResult,
)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def search_series(
        request: SeriesSearchRequest, ctx: Context
    ) -> list[SeriesSearchResult]:
        """Search the local catalogue by text and explicit program filters."""
        with domain_errors():
            return get_services(ctx).catalogue.search(request)
