from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class BLSQueryLimits(BaseModel):
    """Published limits, not a measurement of remaining quota."""

    daily_queries: int = 500
    series_per_query: int = 50
    years_per_query: int = 20
    requests_per_window: int = 50
    window_seconds: int = 10
    checked_on: str = "2026-10-01"
    source_url: str = "https://www.bls.gov/developers/api_faqs.htm"


class BLSAccessStatus(BaseModel):
    """Configuration-only status; never includes credential material."""

    credential_status: Literal["missing", "configured_unverified"]
    access_mode: Literal["setup_required", "registered_v2"]
    verification_supported: bool = False
    remaining_daily_queries: int | None = None
    automatic_batching_supported: bool = False
    setup_resource_uri: str = "setup://bls-api"
    registration_url: str = "https://data.bls.gov/registrationEngine/"
    limits: BLSQueryLimits
    next_action: str
