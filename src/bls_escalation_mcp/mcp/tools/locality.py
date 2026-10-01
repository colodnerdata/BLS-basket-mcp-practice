from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.locality import (
    LaborLocalityInput,
    LaborLocalityResult,
)


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def calculate_labor_locality_factor(
        input_data: LaborLocalityInput, ctx: Context
    ) -> LaborLocalityResult:
        """Compute a labor wage ratio from supplied wages."""
        with domain_errors():
            return get_services(ctx).locality.calculate_labor_locality_factor(
                input_data
            )
