"""Read-only checks against a running MCP server; no live BLS requests."""

from __future__ import annotations

import argparse
import asyncio
import math
from urllib.parse import urlsplit

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def check_server(client: Client) -> None:
    """Verify discovery, guidance, and an independently computed factor."""
    async with client:
        tools = {tool.name for tool in await client.list_tools()}
        required = {"get_bls_access_status", "calculate_component_escalation"}
        if not required <= tools:
            raise ValueError("Required smoke-test tools are missing")
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        print(
            f"PASS discovery: {len(tools)} tools, {len(resources)} resources, "
            f"{len(templates)} resource templates"
        )
        status = await client.call_tool("get_bls_access_status", {})
        if not status.structured_content:
            raise ValueError("Access status has no structured output")
        print("PASS access status (configuration only; key not verified)")
        for uri in (
            "setup://bls-api",
            "methodology://composite-index",
            "methodology://locality-adjustment",
        ):
            content = await client.read_resource(uri)
            if not content or not any(
                getattr(item, "text", "") for item in content
            ):
                raise ValueError("Expected guidance resource is empty")
        print("PASS setup and methodology resources")
        result = await client.call_tool(
            "calculate_component_escalation",
            {
                "component": {
                    "id": "smoke",
                    "name": "Supplied-value smoke check",
                    "component_type": "MATERIAL",
                    "weight": 1.0,
                    "series_id": "SMOKE_SUPPLIED_VALUES",
                },
                "base_value": 100,
                "target_value": 110,
                "locality_factor": 1.0,
            },
        )
        data = result.structured_content
        if not data or not math.isclose(
            data["temporal_factor"], 1.1, rel_tol=1e-12
        ):
            raise ValueError("Expected temporal factor 1.1")
        print("PASS calculation: 110 / 100 = 1.1")


def local_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
    follow_redirects: bool = False,
) -> httpx.AsyncClient:
    """Connect directly to loopback without system proxies."""
    return httpx.AsyncClient(
        headers=headers,
        timeout=timeout or httpx.Timeout(30),
        auth=auth,
        trust_env=False,
        follow_redirects=follow_redirects,
    )


def main() -> None:
    """Connect to HTTP with a bounded total duration and safe errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    url = urlsplit(args.url)
    if (
        url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "localhost", "::1"}
        or url.username
        or url.password
    ):
        parser.error("--url must be a local HTTP URL without credentials")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")

    async def run() -> None:
        # Loopback checks must not be routed through system HTTP proxies.
        transport = StreamableHttpTransport(
            args.url,
            httpx_client_factory=local_http_client,
        )
        async with asyncio.timeout(args.timeout):
            await check_server(Client(transport))

    try:
        asyncio.run(run())
    except Exception:
        print(
            "FAIL smoke check. Confirm the server is running, the URL ends "
            "in /mcp, and the transport is HTTP. "
            "Check server logs for details."
        )
        raise SystemExit(1) from None
    print("PASS smoke check complete; no BLS requests or specification writes")


if __name__ == "__main__":
    main()
