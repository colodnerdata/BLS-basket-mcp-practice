from __future__ import annotations

from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.calculations import ComponentCalculation
from bls_escalation_mcp.services.calculations import (
    EscalationCalculationService,
)

service = EscalationCalculationService()


def calculate_component_escalation(
    component: EscalationComponent,
    base_value: float,
    target_value: float,
    locality_factor: float = 1.0,
) -> ComponentCalculation:
    """Return a single component calculation from the supplied values."""
    return service.calculate_component(
        component,
        base_value,
        target_value,
        locality_factor,
    )


def calculate_index_spec(
    spec,
    component_values: list[ComponentCalculation],
) -> object:
    """Perform a fixed-weight composite calculation for resolved values."""
    return service.calculate_composite(spec, component_values)
