"""STUB (not registered):
planned resource ``index://specifications/{spec_id}``."""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.resources import ResourceResult


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        "index://specifications/{spec_id}", mime_type="application/json"
    )
    def index_specification_resource(
        spec_id: str, ctx: Context
    ) -> ResourceResult:
        """Read a saved specification with assumptions and rationale."""
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
