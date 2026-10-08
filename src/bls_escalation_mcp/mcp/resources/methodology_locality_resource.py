from __future__ import annotations

from fastmcp import FastMCP


def locality_adjustment_methodology() -> str:
    return (
        "Locality factor = target_locality_wage / reference_locality_wage. "
        "This is separate from the temporal factor and is normally "
        "defaulted to 1.0 unless explicitly applied."
    )


def register(mcp: FastMCP) -> None:
    @mcp.resource("methodology://locality-adjustment", mime_type="text/plain")
    def methodology_locality_resource() -> str:
        """Read the separate, explicitly applied labor locality methodology."""
        return locality_adjustment_methodology()
