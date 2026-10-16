"""STUB: planned prompt ``design_escalation_basket`` (not registered)."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt()
    def design_escalation_basket(
        project_description: str,
        base_period: str = "",
        target_period: str = "",
        locality: str = "",
        archetype_id: str = "",
    ) -> str:
        """Clarify scope, periods, shares and evidence; propose a reviewable
        component table.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
