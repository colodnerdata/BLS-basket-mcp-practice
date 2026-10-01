import json
from pathlib import Path

import httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from bls_escalation_mcp.config import Settings
from bls_escalation_mcp.server import create_server


@pytest.mark.asyncio
@pytest.mark.parametrize("key", [None, "", "  ", "test-private-key"])
async def test_access_setup_and_preflight(
    tmp_path: Path, key: str | None
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = json.loads(request.content)
        assert body["registrationkey"] == "test-private-key"
        assert len(body["seriesid"]) == 50
        assert body["startyear"] == "2000"
        assert body["endyear"] == "2019"
        return httpx.Response(
            200,
            json={
                "status": "REQUEST_SUCCEEDED",
                "Results": {
                    "series": [
                        {
                            "seriesID": "TEST",
                            "data": [
                                {
                                    "year": "2000",
                                    "period": "M01",
                                    "value": "100",
                                }
                            ],
                        }
                    ],
                },
            },
        )

    server = create_server(
        Settings(database_path=str(tmp_path / "access.db"), bls_api_key=key),
        http_transport=httpx.MockTransport(respond),
    )
    async with Client(server) as client:
        initialized = await client.initialize()
        assert "get_bls_access_status" in initialized.instructions
        status = await client.call_tool("get_bls_access_status", {})
        state = status.structured_content
        assert state["credential_status"] == (
            "configured_unverified" if key and key.strip() else "missing"
        )
        assert state["verification_supported"] is False
        assert state["remaining_daily_queries"] is None
        assert state["automatic_batching_supported"] is False
        assert state["limits"]["years_per_query"] == 20
        setup = await client.read_resource("setup://bls-api")
        assert setup[0].mimeType == "text/markdown"
        assert "https://data.bls.gov/registrationEngine/" in setup[0].text
        assert "Restart the server" in setup[0].text
        tools = await client.list_tools()
        exposed = (
            json.dumps([tool.model_dump(mode="json") for tool in tools])
            + json.dumps(state)
            + setup[0].text
            + initialized.instructions
        )
        assert "test-private-key" not in exposed
        assert requests == []  # Setup/status never consume remote quota.
        await client.call_tool("search_series", {"request": {}})
        await client.call_tool(
            "calculate_labor_locality_factor",
            {"input_data": {"reference_wage": 40, "target_wage": 50}},
        )
        args = {
            "series_ids": ["TEST"] + [f"TEST{i}" for i in range(49)],
            "start_year": 2000,
            "end_year": 2019,
        }
        if not key or not key.strip():
            with pytest.raises(ToolError, match="setup://bls-api"):
                await client.call_tool("get_series_data", args)
            assert requests == []
        else:
            for invalid, phrase in (
                (dict(args, end_year=2020), "20 inclusive"),
                (
                    dict(args, series_ids=args["series_ids"] + ["EXTRA"]),
                    "50 series",
                ),
            ):
                with pytest.raises(ToolError, match=phrase):
                    await client.call_tool("get_series_data", invalid)
            assert requests == []
            result = await client.call_tool("get_series_data", args)
            assert len(result.structured_content["result"]) == 1
            assert len(requests) == 1
            after = await client.call_tool("get_bls_access_status", {})
            assert after.structured_content["credential_status"] == (
                "configured_unverified"
            )  # A data response alone does not authenticate the key.
