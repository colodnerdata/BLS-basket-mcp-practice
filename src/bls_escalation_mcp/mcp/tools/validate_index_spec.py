from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import domain_errors, get_services
from bls_escalation_mcp.models.specifications import EscalationIndexSpec
from bls_escalation_mcp.models.validation import ValidationResult


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def validate_index_spec(
        spec: EscalationIndexSpec, ctx: Context
    ) -> ValidationResult:
        """Return structured findings without altering the specification."""
        with domain_errors():
            return get_services(ctx).validation.validate_spec(spec)
