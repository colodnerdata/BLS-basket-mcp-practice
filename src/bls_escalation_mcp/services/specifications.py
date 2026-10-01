from __future__ import annotations

from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.periods import EconomicPeriod
from bls_escalation_mcp.models.specifications import EscalationIndexSpec
from bls_escalation_mcp.repositories.specifications import (
    SpecificationRepository,
)


class SpecificationService:
    """Simple specification persistence service."""

    def __init__(self, repository: SpecificationRepository) -> None:
        self.repository = repository

    def create(
        self,
        *,
        id: str,
        name: str,
        base_period: EconomicPeriod,
        target_period: EconomicPeriod,
        components: list[EscalationComponent] | None = None,
        description: str | None = None,
        project_description: str | None = None,
    ) -> EscalationIndexSpec:
        """Create without persistence or implicit methodological changes."""
        return EscalationIndexSpec(
            id=id,
            name=name,
            base_period=base_period,
            target_period=target_period,
            components=components or [],
            description=description,
            project_description=project_description,
        )

    def save(self, spec: EscalationIndexSpec) -> EscalationIndexSpec:
        return self.repository.save(spec)

    def get(self, spec_id: str) -> EscalationIndexSpec | None:
        return self.repository.get(spec_id)

    def list(self) -> list[EscalationIndexSpec]:
        return self.repository.list()
