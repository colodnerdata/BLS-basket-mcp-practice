import pytest

from bls_escalation_mcp.exceptions import CalculationError
from bls_escalation_mcp.models.locality import LaborLocalityInput
from bls_escalation_mcp.services.locality import LocalityService


service = LocalityService()


def test_labor_locality_factor_for_reference_and_target_wages() -> None:
    result = service.calculate_labor_locality_factor(
        LaborLocalityInput(
            occupation_code="SOC-1",
            reference_locality="A",
            target_locality="B",
            reference_wage=40,
            target_wage=50,
            wage_statistic="mean_hourly",
            source_year=2024,
        )
    )
    assert result.locality_factor == pytest.approx(1.25)


def test_zero_reference_wage_invalid() -> None:
    with pytest.raises(CalculationError):
        service.calculate_labor_locality_factor(
            LaborLocalityInput(
                reference_locality="A",
                target_locality="B",
                reference_wage=0,
                target_wage=50,
            )
        )
