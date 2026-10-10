"""Exercise the Python smoke workflow through a real MCP client."""

from __future__ import annotations

import httpx
import pytest
from fastmcp import Client, FastMCP

from bls_escalation_mcp.config import Settings
from bls_escalation_mcp.server import create_server
from bls_escalation_mcp.smoke import check_server, main


@pytest.mark.asyncio
async def test_smoke_workflow_has_no_upstream_calls(tmp_path, capsys):
    requests = []

    def unexpected(request):
        requests.append(request)
        return httpx.Response(500)

    server = create_server(
        Settings(database_path=str(tmp_path / "smoke.db"), bls_api_key=None),
        http_transport=httpx.MockTransport(unexpected),
    )
    await check_server(Client(server))
    assert not requests
    assert "110 / 100 = 1.1" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_smoke_rejects_unrelated_server():
    with pytest.raises(ValueError, match="tools are missing"):
        await check_server(Client(FastMCP("Unrelated server")))


@pytest.mark.parametrize(
    "argv",
    [
        ["--url", "http://example.com/mcp"],
        ["--url", "******127.0.0.1:8000/mcp"],
        ["--timeout", "0"],
        ["--timeout", "nan"],
    ],
)
def test_main_rejects_invalid_local_url_and_timeout(monkeypatch, argv):
    monkeypatch.setattr("sys.argv", ["smoke", *argv])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
