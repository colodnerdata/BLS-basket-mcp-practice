from __future__ import annotations

from datetime import datetime

from bls_escalation_mcp.db.connection import initialize_database
from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.specifications import EscalationIndexSpec
from bls_escalation_mcp.repositories.specifications import (
    SpecificationRepository,
)
from bls_escalation_mcp.services.specifications import SpecificationService


def create_index_spec(
    *,
    id: str,
    name: str,
    base_period,
    target_period,
    components: list[EscalationComponent] | None = None,
    description: str | None = None,
    project_description: str | None = None,
) -> EscalationIndexSpec:
    """Create a specification object without automatically persisting it."""
    return EscalationIndexSpec(
        id=id,
        name=name,
        description=description,
        project_description=project_description,
        base_period=base_period,
        target_period=target_period,
        components=components or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def save_index_spec(spec: EscalationIndexSpec) -> EscalationIndexSpec:
    initialize_database()
    repository = SpecificationRepository()
    return SpecificationService(repository).save(spec)


def get_index_spec(spec_id: str) -> EscalationIndexSpec | None:
    initialize_database()
    repository = SpecificationRepository()
    return SpecificationService(repository).get(spec_id)
