from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from bls_escalation_mcp.models.enums import Periodicity


class EconomicPeriod(BaseModel):
    """Typed representation for a BLS observation period."""

    model_config = ConfigDict(frozen=True)

    year: int
    month: int | None = None
    quarter: int | None = None
    periodicity: Periodicity

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("year must be positive")
        return value

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1 or value > 12:
            raise ValueError("month must be between 1 and 12")
        return value

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1 or value > 4:
            raise ValueError("quarter must be between 1 and 4")
        return value

    @model_validator(mode="after")
    def validate_combinations(self) -> EconomicPeriod:
        if self.month is not None and self.quarter is not None:
            raise ValueError("month and quarter cannot both be set")

        if self.periodicity == Periodicity.MONTHLY:
            if self.month is None:
                raise ValueError("monthly periods require a month")
            if self.quarter is not None:
                raise ValueError("monthly periods cannot include a quarter")
        elif self.periodicity == Periodicity.QUARTERLY:
            if self.quarter is None:
                raise ValueError("quarterly periods require a quarter")
            if self.month is not None:
                raise ValueError("quarterly periods cannot include a month")
        elif self.periodicity in {
            Periodicity.ANNUAL,
            Periodicity.ANNUAL_AVERAGE,
        }:
            if self.month is not None or self.quarter is not None:
                raise ValueError(
                    "annual periods cannot include month or quarter values"
                )
        return self

    @property
    def sort_key(self) -> tuple[int, int, int]:
        month_part = self.month if self.month is not None else 0
        quarter_part = self.quarter if self.quarter is not None else 0
        return (self.year, month_part or quarter_part * 3, 0)

    def __str__(self) -> str:
        if self.periodicity == Periodicity.MONTHLY and self.month is not None:
            return f"{self.year}-M{self.month:02d}"
        if (
            self.periodicity == Periodicity.QUARTERLY
            and self.quarter is not None
        ):
            return f"{self.year}-Q{self.quarter}"
        if self.periodicity == Periodicity.ANNUAL_AVERAGE:
            return f"{self.year}-M13"
        return str(self.year)

    @classmethod
    def from_storage(cls, value: str) -> EconomicPeriod:
        """Decode stored periods, preserving their month/quarter identity."""
        parts = value.split("-")
        if len(parts) == 1:
            return cls(year=int(value), periodicity=Periodicity.ANNUAL)
        if len(parts) != 2:
            raise ValueError(f"Invalid stored period: {value}")
        year, code = parts
        if code == "M13":
            return cls(year=int(year), periodicity=Periodicity.ANNUAL_AVERAGE)
        if code.startswith("M"):
            return cls(
                year=int(year),
                month=int(code[1:]),
                periodicity=Periodicity.MONTHLY,
            )
        if code.startswith("Q"):
            return cls(
                year=int(year),
                quarter=int(code[1:]),
                periodicity=Periodicity.QUARTERLY,
            )
        raise ValueError(f"Invalid stored period: {value}")

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EconomicPeriod):
            return NotImplemented
        return self.sort_key < other.sort_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EconomicPeriod):
            return NotImplemented
        return (
            self.year == other.year
            and self.month == other.month
            and self.quarter == other.quarter
            and self.periodicity == other.periodicity
        )
