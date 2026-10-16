"""STUB: planned prompt ``review_series_candidates`` (not registered)."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt()
    def review_series_candidates(
        component_description: str,
        base_period: str = "",
        target_period: str = "",
        archetype_id: str = "",
    ) -> str:
        """Compare catalog-backed candidate series, coverage and proxy
        rationale for a component.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
