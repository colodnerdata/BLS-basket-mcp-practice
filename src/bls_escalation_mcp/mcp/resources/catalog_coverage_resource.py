"""STUB: planned resource ``bls://catalog/coverage`` (not registered)."""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.resources import ResourceResult


def register(mcp: FastMCP) -> None:
    @mcp.resource("bls://catalog/coverage", mime_type="application/json")
    def catalog_coverage_resource(ctx: Context) -> ResourceResult:
        """Read programs, value types, periodicities, and catalog vs
        observation coverage.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
