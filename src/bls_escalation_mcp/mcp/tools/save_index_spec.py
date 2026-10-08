from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.specifications import EscalationIndexSpec


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        }
    )
    def save_index_spec(
        spec: EscalationIndexSpec, ctx: Context
    ) -> EscalationIndexSpec:
        """Save locally, replacing the same ID and updating its timestamp."""
        with domain_errors():
            return get_services(ctx).specifications.save(spec)
