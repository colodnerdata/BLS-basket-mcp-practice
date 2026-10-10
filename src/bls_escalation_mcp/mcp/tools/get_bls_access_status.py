from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import get_services
from bls_escalation_mcp.models.access import BLSAccessStatus


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def get_bls_access_status(ctx: Context) -> BLSAccessStatus:
        """Check configuration and published limits without HTTP or secrets.

        Before live retrieval, use this tool and read setup://bls-api if setup
        is required. A configured key is unverified; remaining quota
        is unknown.
        Never ask for an API key in chat or as a tool argument.
        """
        return get_services(ctx).access.status()
