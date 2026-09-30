from __future__ import annotations

from pydantic import BaseModel, Field


class Locality(BaseModel):
    name: str
    area_code: str | None = None
    area_type: str | None = None
    state: str | None = None
    source: str | None = None
    aliases: list[str] = Field(default_factory=list)


class LaborLocalityInput(BaseModel):
    occupation_code: str | None = None
    reference_locality: str | None = None
    target_locality: str | None = None
    reference_wage: float
    target_wage: float
    wage_statistic: str | None = None
    source_year: int | None = None


class LaborLocalityResult(BaseModel):
    occupation_code: str | None = None
    reference_locality: str | None = None
    target_locality: str | None = None
    reference_wage: float
    target_wage: float
    locality_factor: float
    wage_statistic: str | None = None
    source_year: int | None = None
