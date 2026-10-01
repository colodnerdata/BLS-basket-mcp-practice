import pytest

from bls_escalation_mcp.exceptions import CalculationError
from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.enums import (
    ComponentType,
    Periodicity,
    WeightSource,
)
from bls_escalation_mcp.models.periods import EconomicPeriod
from bls_escalation_mcp.models.specifications import EscalationIndexSpec
from bls_escalation_mcp.services.calculations import (
    EscalationCalculationService,
)

service = EscalationCalculationService()


def _spec() -> EscalationIndexSpec:
    return EscalationIndexSpec(
        id="spec-1",
        name="Test spec",
        base_period=EconomicPeriod(
            year=2024,
            month=1,
            periodicity=Periodicity.MONTHLY,
        ),
        target_period=EconomicPeriod(
            year=2025,
            month=1,
            periodicity=Periodicity.MONTHLY,
        ),
        components=[],
    )


def test_one_component_weight_one() -> None:
    component = EscalationComponent(
        id="c1",
        name="Test component",
        component_type=ComponentType.MATERIAL,
        weight=1.0,
        weight_source=WeightSource.USER_PROVIDED,
        series_id="TEST_PPI_001",
    )
    result = service.calculate_component(component, 100, 110)
    assert result.temporal_factor == pytest.approx(1.1)


def test_if_every_temporal_factor_equals_one_works() -> None:
    spec = _spec()
    component_values = [
        service.calculate_component(
            EscalationComponent(
                id="a",
                name="A",
                component_type=ComponentType.MATERIAL,
                weight=0.5,
                series_id="TEST_PPI_001",
            ),
            100,
            100,
        ),
        service.calculate_component(
            EscalationComponent(
                id="b",
                name="B",
                component_type=ComponentType.MATERIAL,
                weight=0.5,
                series_id="TEST_PPI_002",
            ),
            20,
            20,
        ),
    ]
    result = service.calculate_composite(spec, component_values)
    assert result.temporal_composite_factor == pytest.approx(1.0)


def test_locality_factor_one_keeps_localized_equal_to_temporal() -> None:
    spec = _spec()
    component_values = [
        service.calculate_component(
            EscalationComponent(
                id="a",
                name="A",
                component_type=ComponentType.MATERIAL,
                weight=0.5,
                series_id="TEST_PPI_001",
            ),
            100,
            120,
            locality_factor=1.0,
        ),
        service.calculate_component(
            EscalationComponent(
                id="b",
                name="B",
                component_type=ComponentType.MATERIAL,
                weight=0.5,
                series_id="TEST_PPI_002",
            ),
            50,
            75,
            locality_factor=1.0,
        ),
    ]
    result = service.calculate_composite(spec, component_values)
    assert result.temporal_composite_factor == pytest.approx(
        result.localized_composite_factor
    )


def test_fixed_unindexed_component_has_temporal_factor_one() -> None:
    component = EscalationComponent(
        id="fixed-1",
        name="Fixed cost",
        component_type=ComponentType.FIXED_UNINDEXED,
        weight=0.25,
    )
    result = service.calculate_component(component, 100, 200)
    assert result.temporal_factor == pytest.approx(1.0)


def test_order_of_components_does_not_change_result() -> None:
    spec = _spec()
    items_a = [
        service.calculate_component(
            EscalationComponent(
                id="a",
                name="A",
                component_type=ComponentType.MATERIAL,
                weight=0.25,
                series_id="TEST_PPI_001",
            ),
            100,
            120,
        ),
        service.calculate_component(
            EscalationComponent(
                id="b",
                name="B",
                component_type=ComponentType.MATERIAL,
                weight=0.75,
                series_id="TEST_PPI_002",
            ),
            100,
            110,
        ),
    ]
    items_b = [items_a[1], items_a[0]]
    result_a = service.calculate_composite(spec, items_a)
    result_b = service.calculate_composite(spec, items_b)
    assert result_a.temporal_composite_factor == pytest.approx(
        result_b.temporal_composite_factor
    )


def test_weighted_component_contributions_sum_to_composite_factor() -> None:
    spec = _spec()
    component_values = [
        service.calculate_component(
            EscalationComponent(
                id="a",
                name="A",
                component_type=ComponentType.MATERIAL,
                weight=0.6,
                series_id="TEST_PPI_001",
            ),
            100,
            120,
        ),
        service.calculate_component(
            EscalationComponent(
                id="b",
                name="B",
                component_type=ComponentType.MATERIAL,
                weight=0.4,
                series_id="TEST_PPI_002",
            ),
            100,
            110,
        ),
    ]
    total = sum(
        item.weight * item.temporal_factor for item in component_values
    )
    result = service.calculate_composite(spec, component_values)
    assert result.temporal_composite_factor == pytest.approx(total)


def test_zero_base_value_raises() -> None:
    component = EscalationComponent(
        id="z",
        name="Zero base",
        component_type=ComponentType.MATERIAL,
        weight=1.0,
        series_id="TEST_PPI_001",
    )
    with pytest.raises(CalculationError):
        service.calculate_component(component, 0, 100)
