from __future__ import annotations

from bls_escalation_mcp.models.specifications import EscalationIndexSpec
from bls_escalation_mcp.repositories.specifications import (
    SpecificationRepository,
)


class SpecificationService:
    """Simple specification persistence service."""

    def __init__(self, repository: SpecificationRepository) -> None:
        self.repository = repository

    def save(self, spec: EscalationIndexSpec) -> EscalationIndexSpec:
        return self.repository.save(spec)

    def get(self, spec_id: str) -> EscalationIndexSpec | None:
        return self.repository.get(spec_id)

    def list(self) -> list[EscalationIndexSpec]:
        return self.repository.list()
