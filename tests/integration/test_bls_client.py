from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bls_escalation_mcp.clients.bls import BLSClient


@pytest.mark.asyncio
async def test_bls_client_parses_mocked_payload() -> None:
    mocked_response = AsyncMock()
    mocked_response.status_code = 200
    mocked_response.json.return_value = {
        "Results": {
            "series": [
                {
                    "seriesID": "TEST_PPI_001",
                    "data": [
                        {"year": "2024", "period": "M01", "value": "100.0"},
                        {"year": "2025", "period": "M01", "value": "110.0"},
                    ],
                }
            ]
        }
    }
    mocked_response.json = lambda: {
        "Results": {
            "series": [
                {
                    "seriesID": "TEST_PPI_001",
                    "data": [
                        {"year": "2024", "period": "M01", "value": "100.0"},
                        {"year": "2025", "period": "M01", "value": "110.0"},
                    ],
                }
            ]
        }
    }

    client = BLSClient()
    mocked_http = AsyncMock()
    mocked_http.post.return_value = mocked_response
    client._http_client = mocked_http

    observations = await client.get_series_observations(["TEST_PPI_001"], 2024, 2025)
    assert len(observations) == 2
    assert observations[0].series_id == "TEST_PPI_001"
    assert observations[1].value == 110.0
