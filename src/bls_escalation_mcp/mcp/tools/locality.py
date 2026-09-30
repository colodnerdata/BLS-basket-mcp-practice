from __future__ import annotations

from bls_escalation_mcp.models.locality import (
    LaborLocalityInput,
    LaborLocalityResult,
)
from bls_escalation_mcp.services.locality import LocalityService

service = LocalityService()


def calculate_labor_locality_factor(
    input_data: LaborLocalityInput,
) -> LaborLocalityResult:
    """Compute a locality factor from supplied reference and target wages."""
    return service.calculate_labor_locality_factor(input_data)
