from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.basket import EscalationComponent
from bls_escalation_mcp.models.periods import EconomicPeriod
from bls_escalation_mcp.models.specifications import EscalationIndexSpec


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def create_index_spec(
        *,
        id: str,
        name: str,
        base_period: EconomicPeriod,
        target_period: EconomicPeriod,
        ctx: Context,
        components: list[EscalationComponent] | None = None,
        description: str | None = None,
        project_description: str | None = None,
    ) -> EscalationIndexSpec:
        """Create a specification without saving or normalizing it."""
        with domain_errors():
            return get_services(ctx).specifications.create(
                id=id,
                name=name,
                base_period=base_period,
                target_period=target_period,
                components=components,
                description=description,
                project_description=project_description,
            )
