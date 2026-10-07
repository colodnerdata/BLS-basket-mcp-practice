from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.calculations import (
    ComponentCalculation,
)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def calculate_component_escalation(
        component: EscalationComponent,
        base_value: float,
        target_value: float,
        ctx: Context,
        locality_factor: float = 1.0,
    ) -> ComponentCalculation:
        """Calculate from supplied values and an explicit locality factor."""
        with domain_errors():
            return get_services(ctx).calculations.calculate_component(
                component,
                base_value,
                target_value,
                locality_factor,
            )
