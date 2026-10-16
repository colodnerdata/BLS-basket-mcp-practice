"""STUB: planned prompt ``review_labor_locality`` (not registered)."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt()
    def review_labor_locality(
        spec_id: str, reference_locality: str = "", target_locality: str = ""
    ) -> str:
        """Clarify geographic intent and request comparable supplied wage
        evidence.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
