from __future__ import annotations

import httpx
from fastmcp import FastMCP

from bls_escalation_mcp.config import Settings, get_settings
from bls_escalation_mcp.lifespan import create_lifespan
from bls_escalation_mcp.mcp.resources import methodology, series
from bls_escalation_mcp.mcp.tools import (
    calculations,
    discovery,
    locality,
    observations,
    specifications,
    validation,
)


def create_server(
    settings: Settings | None = None,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> FastMCP:
    """Assemble a server; open dependencies only at startup."""
    settings = settings if settings is not None else get_settings()
    mcp = FastMCP(
        "BLS Cost Escalation",
        lifespan=create_lifespan(settings, http_transport),
        mask_error_details=True,
    )
    for module in (
        discovery,
        observations,
        specifications,
        calculations,
        locality,
        validation,
    ):
        module.register_tools(mcp)
    series.register_resources(mcp)
    methodology.register_resources(mcp)
    return mcp


if __name__ == "__main__":
    create_server().run()
