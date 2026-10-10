from __future__ import annotations

import httpx
from fastmcp import FastMCP

from bls_escalation_mcp.config import Settings, get_settings
from bls_escalation_mcp.lifespan import create_lifespan
from bls_escalation_mcp.mcp.resources import register_resources
from bls_escalation_mcp.mcp.tools import register_tools
from bls_escalation_mcp.routes import register_routes


def create_server(
    settings: Settings | None = None,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> FastMCP:
    """Assemble a server; open dependencies only at startup."""
    settings = settings if settings is not None else get_settings()
    mcp = FastMCP(
        "BLS Cost Escalation",
        instructions=(
            "Before live BLS retrieval, call get_bls_access_status. If setup "
            "is required, read setup://bls-api and guide the user through "
            "registration and local configuration. Never request keys in "
            "chat or tool arguments. Ask the user to confirm configuration, "
            "restart/reconnect, and recheck status. Configured keys are "
            "unverified, not authenticated. catalog exploration and "
            "supplied-value calculations can continue during setup. "
            "Retrieval supports at most 50 series and 20 inclusive calendar "
            "years per call; automatic batching and quota tracking are "
            "not implemented. Do not claim missing data is zero."
        ),
        lifespan=create_lifespan(settings, http_transport),
        mask_error_details=True,
    )
    register_tools(mcp)
    register_resources(mcp)
    register_routes(mcp)
    return mcp


if __name__ == "__main__":
    create_server().run()
