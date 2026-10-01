from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SourceProvenance(BaseModel):
    source_name: str
    source_url: str | None = None
    retrieved_at: datetime | None = None
    series_id: str | None = None
    notes: str | None = None


class CalculationLedger(BaseModel):
    calculation_id: str
    specification: str | None = None
    result: str | None = None
    observations_used: list[str] = Field(default_factory=list)
    provenance: list[SourceProvenance] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
