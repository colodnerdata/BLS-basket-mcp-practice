from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ResourceError
from fastmcp.resources import ResourceContent, ResourceResult

from bls_escalation_mcp.mcp.adapters import get_services


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("bls://series/{series_id}", mime_type="application/json")
    def series_resource(series_id: str, ctx: Context) -> ResourceResult:
        """Read catalogue metadata as JSON for one known series ID."""
        series = get_services(ctx).catalogue.get(series_id)
        if series is None:
            raise ResourceError(f"Series '{series_id}' was not found.")
        return ResourceResult(
            [
                ResourceContent(
                    series.model_dump(mode="json"),
                    mime_type="application/json",
                )
            ]
        )
