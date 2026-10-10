from __future__ import annotations

from fastmcp import FastMCP


def composite_index_methodology() -> str:
    return (
        "Temporal factor = target_value / base_value. "
        "Weighted composite = sum(weight * temporal_factor). "
        "Percent change = (factor - 1) * 100."
    )


def register(mcp: FastMCP) -> None:
    @mcp.resource("methodology://composite-index", mime_type="text/plain")
    def methodology_composite_index_resource() -> str:
        """Read the fixed-weight temporal composite methodology."""
        return composite_index_methodology()
