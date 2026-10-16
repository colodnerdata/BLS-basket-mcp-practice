"""STUB: planned resource ``bls://snapshot`` (not registered)."""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.resources import ResourceResult


def register(mcp: FastMCP) -> None:
    @mcp.resource("bls://snapshot", mime_type="application/json")
    def snapshot_resource(ctx: Context) -> ResourceResult:
        """Read snapshot identity, per-file retrieval dates and hashes, and
        verification scope.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
