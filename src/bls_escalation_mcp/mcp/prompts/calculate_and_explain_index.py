"""STUB: planned prompt ``calculate_and_explain_index`` (not registered)."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt()
    def calculate_and_explain_index(spec_id: str) -> str:
        """Guide a source-backed calculation and explain contributions,
        provenance and limits.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
