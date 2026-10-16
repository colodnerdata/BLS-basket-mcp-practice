"""STUB: planned prompt ``review_index_spec`` (not registered)."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt()
    def review_index_spec(spec_id: str) -> str:
        """Review a saved specification, call validation, and expose unresolved
        assumptions.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
