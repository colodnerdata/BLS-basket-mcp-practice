from __future__ import annotations

from decimal import Decimal

from bls_escalation_mcp.exceptions import CalculationError, InvalidWeightsError
from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.calculations import (
    ComponentCalculation,
    EscalationCalculationResult,
)
from bls_escalation_mcp.models.enums import ComponentType
from bls_escalation_mcp.models.specifications import EscalationIndexSpec


class EscalationCalculationService:
    """Deterministic calculation service for fixed-weight index."""

    def __init__(self, weight_tolerance: float = 1e-4) -> None:
        self.weight_tolerance = weight_tolerance

    def calculate_component(
        self,
        component: EscalationComponent,
        base_value: float | Decimal,
        target_value: float | Decimal,
        locality_factor: float | Decimal = 1,
    ) -> ComponentCalculation:
        base = Decimal(str(base_value))
        target = Decimal(str(target_value))
        locality = Decimal(str(locality_factor))

        if component.component_type == ComponentType.FIXED_UNINDEXED:
            temporal_factor = Decimal("1")
        else:
            if base == 0:
                raise CalculationError(
                    f"Base value for component '{component.id}' "
                    "cannot be zero."
                )
            temporal_factor = target / base

        combined_factor = temporal_factor * locality
        weighted_contribution = (
            Decimal(str(component.weight)) * combined_factor
        )

        return ComponentCalculation(
            component_id=component.id,
            series_id=component.series_id,
            weight=float(component.weight),
            base_period=None,
            target_period=None,
            base_value=float(base),
            target_value=float(target),
            temporal_factor=float(temporal_factor),
            locality_factor=float(locality),
            combined_factor=float(combined_factor),
            weighted_contribution=float(weighted_contribution),
        )

    def calculate_composite(
        self,
        spec: EscalationIndexSpec,
        component_values: list[ComponentCalculation],
    ) -> EscalationCalculationResult:
        if not component_values:
            raise InvalidWeightsError(
                "At least one component value is required "
                "to calculate a composite."
            )

        total_weight = sum(item.weight for item in component_values)
        tolerance = self.weight_tolerance
        if abs(total_weight - 1.0) > tolerance:
            raise InvalidWeightsError(
                "Component weights must sum to 1 within tolerance; "
                f"received {total_weight:.6f}."
            )

        temporal = sum(
            item.weight * item.temporal_factor for item in component_values
        )
        localized = sum(
            item.weight * item.combined_factor for item in component_values
        )
        temporal_percent = (temporal - 1) * 100
        localized_percent = (localized - 1) * 100

        return EscalationCalculationResult(
            specification_id=str(spec.id),
            base_period=spec.base_period,
            target_period=spec.target_period,
            temporal_composite_factor=float(temporal),
            localized_composite_factor=float(localized),
            temporal_percent_change=float(temporal_percent),
            localized_percent_change=float(localized_percent),
            components=component_values,
            warnings=[],
        )
