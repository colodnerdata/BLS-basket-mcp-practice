from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bls_escalation_mcp.models.periods import EconomicPeriod


class ComponentCalculation(BaseModel):
    component_id: str
    series_id: str | None = None
    weight: float
    base_period: EconomicPeriod | None = None
    target_period: EconomicPeriod | None = None
    base_value: float | None = None
    target_value: float | None = None
    temporal_factor: float = 1.0
    locality_factor: float = 1.0
    combined_factor: float = 1.0
    weighted_contribution: float = 0.0


class EscalationCalculationResult(BaseModel):
    specification_id: str
    base_period: EconomicPeriod
    target_period: EconomicPeriod
    temporal_composite_factor: float
    localized_composite_factor: float
    temporal_percent_change: float
    localized_percent_change: float
    components: list[ComponentCalculation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
