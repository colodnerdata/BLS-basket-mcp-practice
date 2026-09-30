import json

from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.enums import ComponentType, Periodicity
from bls_escalation_mcp.models.periods import EconomicPeriod
from bls_escalation_mcp.models.specifications import EscalationIndexSpec


def test_json_serialization_round_trip() -> None:
    spec = EscalationIndexSpec(
        id="spec-1",
        name="Test spec",
        base_period=EconomicPeriod(year=2024, month=1, periodicity=Periodicity.MONTHLY),
        target_period=EconomicPeriod(year=2025, month=1, periodicity=Periodicity.MONTHLY),
        components=[
            EscalationComponent(
                id="component-1",
                name="Materials",
                component_type=ComponentType.MATERIAL,
                weight=0.6,
                series_id="TEST_PPI_001",
            )
        ],
    )
    payload = spec.model_dump(mode="json")
    assert "base_period" in json.dumps(payload)
    round_tripped = EscalationIndexSpec.model_validate(payload)
    assert round_tripped.id == spec.id
    assert round_tripped.components[0].id == "component-1"
