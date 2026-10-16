from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bls_escalation_mcp.clients.bls import BLSClient
from tests.harness import CANNED_SUCCESS, load_bls_fixture


@pytest.mark.asyncio
async def test_bls_client_parses_mocked_payload() -> None:
    mocked_response = AsyncMock()
    mocked_response.status_code = 200
    mocked_response.json = lambda: load_bls_fixture(CANNED_SUCCESS)

    client = BLSClient()
    mocked_http = AsyncMock()
    mocked_http.post.return_value = mocked_response
    client._http_client = mocked_http

    observations = await client.get_series_observations(
        ["TEST_PPI_001"],
        2024,
        2025,
    )
    assert len(observations) == 2
    assert observations[0].series_id == "TEST_PPI_001"
    assert observations[1].value == 110.0
