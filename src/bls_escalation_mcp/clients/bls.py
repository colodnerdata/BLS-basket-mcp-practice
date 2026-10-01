from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from bls_escalation_mcp.exceptions import BLSAPIError, ObservationNotFoundError
from bls_escalation_mcp.models.enums import Periodicity
from bls_escalation_mcp.models.observations import Observation
from bls_escalation_mcp.models.periods import EconomicPeriod


class BLSClient:
    """Small client for retrieving known BLS series IDs."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.bls.gov/publicAPI/v2",
        timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http_client = http_client

    async def get_series_observations(
        self,
        series_ids: list[str],
        start_year: int,
        end_year: int,
    ) -> list[Observation]:
        if not series_ids:
            return []
        if self._http_client is not None:
            return await self._request_observations(
                self._http_client, series_ids, start_year, end_year
            )
        # Standalone callers get a bounded client lifetime too.
        # Injected clients are owned by their caller.
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._request_observations(
                client, series_ids, start_year, end_year
            )

    async def _request_observations(
        self,
        client: httpx.AsyncClient,
        series_ids: list[str],
        start_year: int,
        end_year: int,
    ) -> list[Observation]:
        payload: dict[str, Any] = {
            "seriesid": list(series_ids),
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        if self.api_key:
            payload["registrationkey"] = self.api_key

        try:
            response = await client.post(
                f"{self.base_url}/timeseries/data/",
                json=payload,
            )
        except httpx.HTTPError as exc:  # pragma: no cover
            raise BLSAPIError(
                "Error retrieving BLS series observations."
            ) from exc

        if response.status_code >= 400:
            raise BLSAPIError(
                f"BLS API request failed with status {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise BLSAPIError("BLS API response was not valid JSON.") from exc

        if data.get("status") == "REQUEST_ERROR":
            message = data.get("message", "BLS API request error")
            raise BLSAPIError(str(message))

        parsed = self.parse_response(data)
        if not parsed:
            raise ObservationNotFoundError(
                "No observations were returned for the provided series IDs."
            )
        return parsed

    @staticmethod
    def parse_response(payload: dict[str, Any]) -> list[Observation]:
        """Parse a BLS time-series payload into typed observations."""
        observations: list[Observation] = []
        for series in payload.get("Results", {}).get("series", []):
            series_id = series.get("seriesID")
            for item in series.get("data", []):
                period_code = item.get("period")
                period_name = item.get("year")
                if not period_name:
                    continue
                try:
                    period = EconomicPeriod(
                        year=int(period_name),
                        month=(
                            int(period_code[1:])
                            if period_code and period_code.startswith("M")
                            else None
                        ),
                        quarter=(
                            int(period_code[1:])
                            if period_code and period_code.startswith("Q")
                            else None
                        ),
                        periodicity=(
                            Periodicity.MONTHLY
                            if period_code and period_code.startswith("M")
                            else Periodicity.QUARTERLY
                            if period_code and period_code.startswith("Q")
                            else Periodicity.ANNUAL
                        ),
                    )
                except ValueError:
                    continue
                value = item.get("value")
                try:
                    numeric_value = Decimal(str(value))
                    if not numeric_value.is_finite():
                        raise ValueError("non-finite value")
                except (InvalidOperation, TypeError, ValueError) as exc:
                    raise BLSAPIError(
                        f"Missing or non-numeric observation for {series_id} "
                        f"at {period}."
                    ) from exc
                footnotes = [
                    note["text"]
                    for note in (item.get("footnotes") or [])
                    if isinstance(note, dict) and note.get("text")
                ]
                observations.append(
                    Observation(
                        series_id=series_id,
                        period=period,
                        value=numeric_value,
                        units=item.get("units", "index"),
                        retrieved_at=datetime.now(UTC),
                        source="BLS",
                        is_preliminary=None,
                        footnotes=footnotes,
                    )
                )
        return observations
