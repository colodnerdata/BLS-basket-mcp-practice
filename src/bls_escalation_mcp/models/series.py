from __future__ import annotations

from pydantic import BaseModel

from bls_escalation_mcp.models.enums import BLSProgram, Periodicity
from bls_escalation_mcp.models.periods import EconomicPeriod


class SeriesMetadata(BaseModel):
    series_id: str
    program: BLSProgram
    title: str
    description: str | None = None
    classification_system: str | None = None
    classification_code: str | None = None
    parent_code: str | None = None
    industry_code: str | None = None
    commodity_code: str | None = None
    occupation_code: str | None = None
    geography: str | None = None
    area_code: str | None = None
    periodicity: Periodicity | None = None
    seasonal_adjustment: bool | None = None
    units: str | None = None
    first_period: EconomicPeriod | None = None
    latest_period: EconomicPeriod | None = None
    active: bool | None = None
    source_url: str | None = None


class SeriesSearchRequest(BaseModel):
    query: str = ""
    programs: list[BLSProgram] | None = None
    active_only: bool = True
    limit: int = 25


class SeriesSearchResult(BaseModel):
    series: SeriesMetadata
    match_score: float | None = None
    match_reason: str | None = None
