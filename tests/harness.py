"""Shared helpers for the integration suite (imported; see conftest.py).

Kept as a real module (not conftest-only) so integration modules can import
the transport and server helpers explicitly.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Client

from bls_escalation_mcp.config import Settings
from bls_escalation_mcp.server import create_server

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bls"
CANNED_SUCCESS = "v2_timeseries_success.json"


def load_bls_fixture(name: str) -> dict[str, Any]:
    """Load a canned payload by filename (see tests/fixtures/bls/README)."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def bls_payload(
    series_id: str = "TEST_PPI_001",
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a fresh copy of the canned success payload, re-pointed.

    A new dict each call so a test may mutate the result without affecting
    other tests.
    """
    payload = load_bls_fixture(CANNED_SUCCESS)
    series = payload["Results"]["series"][0]
    series["seriesID"] = series_id
    if items is not None:
        series["data"] = items
    return payload


class CannedTransport(httpx.MockTransport):
    """Mock transport recording requests and serving one canned payload.

    ``check``, when given, runs assertions against each decoded request
    body. ``closed`` records whether the server lifespan closed this
    transport, including on failure paths.
    """

    def __init__(
        self,
        payload: dict[str, Any] | None = None,
        check: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.requests: list[httpx.Request] = []
        self.closed = False
        self._payload = payload if payload is not None else bls_payload()
        self._check = check
        super().__init__(self._respond)

    def _respond(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._check is not None:
            self._check(json.loads(request.content))
        return httpx.Response(200, json=self._payload)

    async def aclose(self) -> None:
        self.closed = True
        await super().aclose()


@dataclass
class ServerEnv:
    """A connected in-memory client plus its transport and database path."""

    client: Client
    transport: CannedTransport
    db_path: Path


@asynccontextmanager
async def server_env(
    tmp_path: Path,
    *,
    key: str | None = "fixture-secret",
    transport: CannedTransport | None = None,
    db_name: str = "nested/catalog.db",
) -> AsyncIterator[ServerEnv]:
    """Run the real server against a temporary database and canned transport.

    Asserts the factory has no persistence side effects (the database file
    does not exist before startup) and, in a ``finally`` block, that the
    lifespan closed the injected transport — including when the body raised.
    """
    db_path = tmp_path / db_name
    transport = transport if transport is not None else CannedTransport()
    server = create_server(
        Settings(database_path=str(db_path), bls_api_key=key),
        http_transport=transport,
    )
    assert not db_path.exists()  # Factory has no persistence side effects.
    try:
        async with Client(server) as client:
            yield ServerEnv(client, transport, db_path)
    finally:
        assert transport.closed, "Lifespan must close the injected transport"
