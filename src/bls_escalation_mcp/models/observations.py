from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

from bls_escalation_mcp.models.periods import EconomicPeriod


class Observation(BaseModel):
    series_id: str
    period: EconomicPeriod
    # Preserve decimal text without a regex schema incompatible with some
    # MCP clients; internal arithmetic still receives a Decimal.
    value: Annotated[
        Decimal, PlainSerializer(str, return_type=str, when_used="json")
    ]
    units: str | None = None
    retrieved_at: datetime
    source: str
    is_preliminary: bool | None = None
    footnotes: list[str] = Field(default_factory=list)


class SeriesObservations(BaseModel):
    series_id: str
    observations: list[Observation] = Field(default_factory=list)
