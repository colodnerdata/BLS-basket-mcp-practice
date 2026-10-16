"""STUB (not registered):
planned resource ``bls://series/{series_id}/coverage``."""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.resources import ResourceResult


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        "bls://series/{series_id}/coverage", mime_type="application/json"
    )
    def series_coverage_resource(
        series_id: str, ctx: Context
    ) -> ResourceResult:
        """Read stored observation periods, counts, and known gaps for one
        series.
        """
        raise NotImplementedError(
            "Planned stub; see docs/mcp_resources_prompts.md."
        )
