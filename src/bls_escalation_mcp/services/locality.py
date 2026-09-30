from __future__ import annotations

from bls_escalation_mcp.exceptions import CalculationError
from bls_escalation_mcp.models.locality import (
    LaborLocalityInput,
    LaborLocalityResult,
)


class LocalityService:
    """Minimal locality service for labor wage ratio calculations."""

    def calculate_labor_locality_factor(
        self,
        input_data: LaborLocalityInput,
    ) -> LaborLocalityResult:
        reference_wage = float(input_data.reference_wage)
        target_wage = float(input_data.target_wage)

        if reference_wage <= 0:
            raise CalculationError("reference_wage must be greater than zero.")
        if target_wage < 0:
            raise CalculationError("target_wage must be zero or positive.")

        # TODO: integrate OEWS lookup and area mapping once the
        # schema is confirmed.
        locality_factor = target_wage / reference_wage

        return LaborLocalityResult(
            occupation_code=input_data.occupation_code,
            reference_locality=input_data.reference_locality,
            target_locality=input_data.target_locality,
            reference_wage=reference_wage,
            target_wage=target_wage,
            locality_factor=locality_factor,
            wage_statistic=input_data.wage_statistic,
            source_year=input_data.source_year,
        )
