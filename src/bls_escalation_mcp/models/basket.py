from __future__ import annotations

from pydantic import BaseModel

from bls_escalation_mcp.models.enums import (
    BLSProgram,
    ComponentType,
    MatchType,
    WeightSource,
)


class EscalationComponent(BaseModel):
    id: str
    name: str
    description: str | None = None
    component_type: ComponentType
    weight: float
    weight_source: WeightSource = WeightSource.USER_PROVIDED
    series_id: str | None = None
    series_program: BLSProgram | None = None
    official_series_title: str | None = None
    match_type: MatchType = MatchType.UNKNOWN
    proxy_reason: str | None = None
    temporal_adjustment_enabled: bool = True
    locality_adjustment_enabled: bool = False
    notes: str | None = None
