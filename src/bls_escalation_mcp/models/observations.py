from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from bls_escalation_mcp.models.periods import EconomicPeriod


class Observation(BaseModel):
    series_id: str
    period: EconomicPeriod
    value: Decimal
    units: str | None = None
    retrieved_at: datetime
    source: str
    is_preliminary: bool | None = None
    footnotes: list[str] = Field(default_factory=list)


class SeriesObservations(BaseModel):
    series_id: str
    observations: list[Observation] = Field(default_factory=list)
