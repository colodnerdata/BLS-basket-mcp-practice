from __future__ import annotations

from fastmcp import FastMCP


def composite_index_methodology() -> str:
    return (
        "Temporal factor = target_value / base_value. "
        "Weighted composite = sum(weight * temporal_factor). "
        "Percent change = (factor - 1) * 100."
    )


def locality_adjustment_methodology() -> str:
    return (
        "Locality factor = target_locality_wage / reference_locality_wage. "
        "This is separate from the temporal factor and is normally "
        "defaulted to 1.0 unless explicitly applied."
    )


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("methodology://composite-index", mime_type="text/plain")
    def methodology_composite_index_resource() -> str:
        """Read the fixed-weight temporal composite methodology."""
        return composite_index_methodology()

    @mcp.resource("methodology://locality-adjustment", mime_type="text/plain")
    def methodology_locality_resource() -> str:
        """Read the separate, explicitly applied labor locality methodology."""
        return locality_adjustment_methodology()
