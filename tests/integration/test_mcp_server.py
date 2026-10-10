"""Exercise the MCP JSON boundary using real FastMCP in-memory clients."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from fastmcp import Client
from fastmcp.exceptions import ToolError

from bls_escalation_mcp.models.series import SeriesMetadata
from bls_escalation_mcp.repositories.series import SeriesRepository
from tests.harness import CannedTransport, server_env

BASE = {"year": 2024, "periodicity": "ANNUAL"}
TARGET = {"year": 2025, "periodicity": "ANNUAL"}
COMPONENTS = [
    {
        "id": "steel",
        "name": "Steel",
        "component_type": "MATERIAL",
        "weight": 0.6,
        "series_id": "TEST_PPI_001",
    },
    {
        "id": "labor",
        "name": "Labor",
        "component_type": "LABOR",
        "weight": 0.4,
        "series_id": "TEST_ECI_001",
    },
]


def spec_arguments() -> dict:
    return {
        "id": "basket-1",
        "name": "Fixture basket",
        "base_period": BASE,
        "target_period": TARGET,
        "components": COMPONENTS,
    }


@pytest_asyncio.fixture
async def client(tmp_path: Path) -> AsyncIterator[Client]:
    def check(body: dict[str, Any]) -> None:
        assert body["registrationkey"] == "fixture-secret"
        assert body["startyear"] == "2024"
        assert body["endyear"] == "2025"

    transport = CannedTransport(check=check)
    async with server_env(tmp_path, transport=transport) as env:
        # Startup initializes the database before any tools are called.
        resources = await env.client.list_resources()
        assert len(resources) == 3
        repo = SeriesRepository(str(env.db_path))
        repo.upsert(
            SeriesMetadata(
                series_id="TEST_PPI_001",
                program="PPI",
                title="Fixture steel",
                active=True,
            )
        )
        yield env.client


@pytest.mark.asyncio
async def test_discovery_and_contracts(client: Client) -> None:
    tools = {tool.name: tool for tool in await client.list_tools()}
    assert set(tools) == {
        "get_bls_access_status",
        "search_series",
        "describe_series",
        "get_series_data",
        "create_index_spec",
        "save_index_spec",
        "get_index_spec",
        "calculate_component_escalation",
        "calculate_index_spec",
        "calculate_labor_locality_factor",
        "validate_index_spec",
    }
    for tool in tools.values():
        assert tool.description
        assert "ctx" not in tool.inputSchema["properties"]
        assert "api_key" not in tool.inputSchema["properties"]
        assert "database_path" not in tool.inputSchema["properties"]
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is (
            tool.name != "save_index_spec"
        )
        assert tool.annotations.openWorldHint is (
            tool.name == "get_series_data"
        )
    for name in ("validate_index_spec", "calculate_index_spec"):
        spec_schema = tools[name].inputSchema["properties"]["spec"]
        assert spec_schema["type"] == "object"
        assert "components" in spec_schema["properties"]
        assert "base_period" in spec_schema["required"]
    assert (
        tools["create_index_spec"].inputSchema["properties"]["base_period"][
            "type"
        ]
        == "object"
    )
    assert (
        "temporal_composite_factor"
        in tools["calculate_index_spec"].outputSchema["properties"]
    )
    save = tools["save_index_spec"].annotations
    assert save.destructiveHint is True
    assert save.idempotentHint is False
    templates = await client.list_resource_templates()
    assert templates[0].uriTemplate == "bls://series/{series_id}"
    assert templates[0].mimeType == "application/json"


@pytest.mark.asyncio
async def test_json_workflow_and_persistence(client: Client) -> None:
    found = await client.call_tool(
        "search_series",
        {
            "request": {
                "query": "steel",
                "programs": ["PPI"],
            }
        },
    )
    assert (
        found.structured_content["result"][0]["series"]["series_id"]
        == "TEST_PPI_001"
    )
    described = await client.call_tool(
        "describe_series",
        {
            "series_id": "TEST_PPI_001",
        },
    )
    assert described.structured_content["result"]["title"] == "Fixture steel"
    created = await client.call_tool("create_index_spec", spec_arguments())
    spec = created.structured_content
    assert spec["components"][0]["weight"] == 0.6
    assert spec["created_at"].endswith("Z")
    # Creation does not save anything.
    absent = await client.call_tool("get_index_spec", {"spec_id": spec["id"]})
    assert absent.structured_content == {"result": None}
    validated = await client.call_tool("validate_index_spec", {"spec": spec})
    assert validated.structured_content == {"valid": True, "findings": []}

    resolved = []
    for component, base, target, locality in (
        (COMPONENTS[0], 100, 110, 1),
        (COMPONENTS[1], 200, 240, 1.25),
    ):
        value = await client.call_tool(
            "calculate_component_escalation",
            {
                "component": component,
                "base_value": base,
                "target_value": target,
                "locality_factor": locality,
            },
        )
        resolved.append(value.structured_content)
    result = await client.call_tool(
        "calculate_index_spec",
        {
            "spec": spec,
            "component_values": resolved,
        },
    )
    calculation = result.structured_content
    # Independent arithmetic: .6*1.1+.4*1.2=1.14; localized .6*1.1+.4*1.5=1.26.
    assert calculation["temporal_composite_factor"] == pytest.approx(1.14)
    assert calculation["localized_composite_factor"] == pytest.approx(1.26)
    assert calculation["temporal_percent_change"] == pytest.approx(14)
    assert calculation["localized_percent_change"] == pytest.approx(26)
    assert calculation["specification_id"] == spec["id"]
    assert calculation["base_period"] == spec["base_period"]

    saved = await client.call_tool("save_index_spec", {"spec": spec})
    read = await client.call_tool("get_index_spec", {"spec_id": spec["id"]})
    assert read.structured_content["result"] == saved.structured_content
    revised = dict(spec, name="Revised basket")
    await client.call_tool("save_index_spec", {"spec": revised})
    read = await client.call_tool("get_index_spec", {"spec_id": spec["id"]})
    assert read.structured_content["result"]["name"] == "Revised basket"


@pytest.mark.asyncio
async def test_observations_locality_and_resources(client: Client) -> None:
    result = await client.call_tool(
        "get_series_data",
        {
            "series_ids": ["TEST_PPI_001"],
            "start_year": 2024,
            "end_year": 2025,
        },
    )
    assert result.data is not None  # Output schema is reconstructible.
    observations = result.structured_content["result"]
    assert len(observations) == 2
    assert float(observations[1]["value"]) == 110
    assert observations[0]["period"]["month"] == 1
    assert observations[0]["is_preliminary"] is None
    assert observations[1]["footnotes"] == ["Preliminary"]
    locality = await client.call_tool(
        "calculate_labor_locality_factor",
        {
            "input_data": {
                "reference_wage": 40,
                "target_wage": 50,
                "source_year": 2025,
            },
        },
    )
    assert locality.structured_content["locality_factor"] == 1.25
    series = await client.read_resource("bls://series/TEST_PPI_001")
    assert series[0].mimeType == "application/json"
    assert json.loads(series[0].text)["title"] == "Fixture steel"
    for uri, phrase in (
        ("methodology://composite-index", "Temporal factor"),
        ("methodology://locality-adjustment", "Locality factor"),
    ):
        resource = await client.read_resource(uri)
        assert resource[0].mimeType == "text/plain"
        assert phrase in resource[0].text


@pytest.mark.asyncio
async def test_validation_and_domain_errors(client: Client) -> None:
    invalid = dict(spec_arguments(), components=[])
    findings = await client.call_tool("validate_index_spec", {"spec": invalid})
    assert findings.structured_content["valid"] is False
    assert "NO_COMPONENTS" in {
        finding["code"] for finding in findings.structured_content["findings"]
    }
    with pytest.raises(ToolError):
        await client.call_tool(
            "create_index_spec",
            dict(
                spec_arguments(),
                base_period={"year": 2024, "periodicity": "MONTHLY"},
            ),
        )
    with pytest.raises(ToolError, match="cannot be zero"):
        await client.call_tool(
            "calculate_component_escalation",
            {
                "component": COMPONENTS[0],
                "base_value": 0,
                "target_value": 110,
            },
        )
    with pytest.raises(ToolError, match="At least one component"):
        await client.call_tool(
            "calculate_index_spec",
            {
                "spec": spec_arguments(),
                "component_values": [],
            },
        )
    with pytest.raises(ToolError, match="end_year"):
        await client.call_tool(
            "get_series_data",
            {
                "series_ids": ["TEST"],
                "start_year": 2025,
                "end_year": 2024,
            },
        )


@pytest.mark.asyncio
async def test_resource_first_startup_and_cleanup_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import bls_escalation_mcp.lifespan as lifecycle

    starts = []
    initialize = lifecycle.initialize_database

    def counted_initialize(path: str) -> None:
        starts.append(path)
        initialize(path)

    monkeypatch.setattr(lifecycle, "initialize_database", counted_initialize)
    with pytest.raises(RuntimeError, match="caller failed"):
        async with server_env(tmp_path, key=None, db_name="fresh.db") as env:
            # Read an unseeded series resource first: no SQL/table error.
            with pytest.raises(Exception, match="was not found"):
                await env.client.read_resource("bls://series/unknown")
            await env.client.call_tool("search_series", {"request": {}})
            assert starts == [str(env.db_path)]
            raise RuntimeError("caller failed")
    # server_env's teardown asserts the injected transport was closed.


@pytest.mark.asyncio
async def test_fixed_component_validation_and_calculation(
    client: Client,
) -> None:
    fixed = {
        "id": "fixed",
        "name": "Unindexed share",
        "component_type": "FIXED_UNINDEXED",
        "weight": 1.0,
    }
    created = await client.call_tool(
        "create_index_spec", dict(spec_arguments(), components=[fixed])
    )
    spec = created.structured_content
    assert spec["components"][0]["temporal_adjustment_enabled"] is True
    validated = await client.call_tool("validate_index_spec", {"spec": spec})
    assert validated.structured_content == {"valid": True, "findings": []}
    calculated = await client.call_tool(
        "calculate_component_escalation",
        {"component": fixed, "base_value": 100, "target_value": 200},
    )
    assert calculated.structured_content["temporal_factor"] == 1.0
    composite = await client.call_tool(
        "calculate_index_spec",
        {"spec": spec, "component_values": [calculated.structured_content]},
    )
    assert composite.structured_content["temporal_composite_factor"] == 1.0
    assert composite.structured_content["temporal_percent_change"] == 0.0
    # Fixed components still reject a series, while indexed ones require it.
    for component, expected in (
        (dict(fixed, series_id="TEST"), "FIXED_COMPONENT_HAS_SERIES"),
        (dict(fixed, component_type="MATERIAL"), "MISSING_SERIES_ID"),
    ):
        invalid = dict(spec, components=[component])
        result = await client.call_tool(
            "validate_index_spec", {"spec": invalid}
        )
        assert result.structured_content["valid"] is False
        assert {f["code"] for f in result.structured_content["findings"]} == {
            expected
        }
