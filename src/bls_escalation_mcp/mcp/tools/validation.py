from __future__ import annotations

from bls_escalation_mcp.models.validation import ValidationResult
from bls_escalation_mcp.services.validation import ValidationService

service = ValidationService()


def validate_index_spec(spec) -> ValidationResult:
    """Validate a basket specification for obvious structural errors."""
    return service.validate_spec(spec)
