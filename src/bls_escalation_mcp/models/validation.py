from __future__ import annotations

from pydantic import BaseModel, Field

from bls_escalation_mcp.models.enums import ValidationSeverity


class ValidationFinding(BaseModel):
    code: str
    severity: ValidationSeverity
    message: str
    component_id: str | None = None
    series_id: str | None = None
    suggested_action: str | None = None


class ValidationResult(BaseModel):
    valid: bool
    findings: list[ValidationFinding] = Field(default_factory=list)
