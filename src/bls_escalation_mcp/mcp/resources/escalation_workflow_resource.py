"""STUB: planned resource ``guide://escalation-workflow`` (not registered)."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.resource("guide://escalation-workflow", mime_type="text/markdown")
    def escalation_workflow_resource() -> str:
        """Read the project-to-index workflow, checkpoints, and links."""
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
