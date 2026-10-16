"""STUB: planned resource ``basket://archetypes`` (not registered)."""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.resources import ResourceResult


def register(mcp: FastMCP) -> None:
    @mcp.resource("basket://archetypes", mime_type="application/json")
    def archetypes_resource(ctx: Context) -> ResourceResult:
        """List reviewed basket archetypes and their detail URIs."""
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
