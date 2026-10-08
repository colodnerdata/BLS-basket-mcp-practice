from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.specifications import EscalationIndexSpec


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def get_index_spec(
        spec_id: str, ctx: Context
    ) -> EscalationIndexSpec | None:
        """Read a saved specification; return null when the ID is absent."""
        with domain_errors():
            return get_services(ctx).specifications.get(spec_id)
