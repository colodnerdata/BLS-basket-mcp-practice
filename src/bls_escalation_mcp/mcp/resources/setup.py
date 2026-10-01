from __future__ import annotations

from fastmcp import Context, FastMCP

from bls_escalation_mcp.mcp.adapters import get_services


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("setup://bls-api", mime_type="text/markdown")
    def bls_api_setup(ctx: Context) -> str:
        """Read registration, local key configuration, and BLS query limits."""
        return get_services(ctx).access.setup_guide()
