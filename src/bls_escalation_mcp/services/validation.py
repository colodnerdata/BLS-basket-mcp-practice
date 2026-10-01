from __future__ import annotations

from bls_escalation_mcp.models.enums import ComponentType, ValidationSeverity
from bls_escalation_mcp.models.specifications import EscalationIndexSpec
from bls_escalation_mcp.models.validation import (
    ValidationFinding,
    ValidationResult,
)


class ValidationService:
    """Basic validation service for escalation baskets and specifications."""

    def __init__(self, weight_tolerance: float = 1e-4) -> None:
        self.weight_tolerance = weight_tolerance

    def validate_spec(self, spec: EscalationIndexSpec) -> ValidationResult:
        findings: list[ValidationFinding] = []

        if not spec.components:
            findings.append(
                ValidationFinding(
                    code="NO_COMPONENTS",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        "Specification must contain at least one component."
                    ),
                )
            )

        total_weight = sum(component.weight for component in spec.components)
        if abs(total_weight - 1.0) > self.weight_tolerance:
            findings.append(
                ValidationFinding(
                    code="WEIGHTS_SUM_MISMATCH",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        "Total component weights must equal 1 within"
                        " tolerance; "
                        f"received {total_weight:.6f}."
                    ),
                )
            )

        for component in spec.components:
            if component.weight < 0:
                findings.append(
                    ValidationFinding(
                        code="NEGATIVE_WEIGHT",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Component '{component.id}' has a negative"
                            f" weight: {component.weight}."
                        ),
                        component_id=component.id,
                    )
                )

            if (
                component.component_type != ComponentType.FIXED_UNINDEXED
                and component.temporal_adjustment_enabled
                and not component.series_id
            ):
                findings.append(
                    ValidationFinding(
                        code="MISSING_SERIES_ID",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Component '{component.id}' is temporally"
                            " indexed but has no series ID."
                        ),
                        component_id=component.id,
                    )
                )

            if (
                component.component_type == ComponentType.FIXED_UNINDEXED
                and component.series_id
            ):
                findings.append(
                    ValidationFinding(
                        code="FIXED_COMPONENT_HAS_SERIES",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Fixed/unindexed component '{component.id}' "
                            "should not include a series ID."
                        ),
                        component_id=component.id,
                        series_id=component.series_id,
                    )
                )

            if (
                component.locality_adjustment_enabled
                and component.component_type
                in {ComponentType.MATERIAL, ComponentType.EQUIPMENT}
            ):
                findings.append(
                    ValidationFinding(
                        code="LOCALITY_ON_MATERIAL_OR_EQUIPMENT",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"Component '{component.id}' is a material or"
                            " equipment item with locality enabled; verify"
                            " this is intentional."
                        ),
                        component_id=component.id,
                    )
                )

        if spec.base_period == spec.target_period:
            findings.append(
                ValidationFinding(
                    code="IDENTICAL_BASE_AND_TARGET",
                    severity=ValidationSeverity.ERROR,
                    message="Base and target periods must not be identical.",
                )
            )

        if spec.target_period < spec.base_period:
            findings.append(
                ValidationFinding(
                    code="TARGET_PRECEDES_BASE",
                    severity=ValidationSeverity.WARNING,
                    message=(
                        "Target period precedes base period; confirm this is"
                        " an intentional backwards-looking calculation."
                    ),
                )
            )

        return ValidationResult(
            valid=not any(
                f.severity == ValidationSeverity.ERROR for f in findings
            ),
            findings=findings,
        )
