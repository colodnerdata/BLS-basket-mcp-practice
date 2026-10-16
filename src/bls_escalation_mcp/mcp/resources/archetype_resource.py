"""STUB (not registered):
planned resource ``basket://archetypes/{archetype_id}``."""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.resources import ResourceResult


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        "basket://archetypes/{archetype_id}", mime_type="application/json"
    )
    def archetype_resource(archetype_id: str, ctx: Context) -> ResourceResult:
        """Read one reviewed archetype: decomposition, candidate searches, and
        examples.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
