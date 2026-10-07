"""Dependency-free HTTP probes; these do not check BLS or database health."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from bls_escalation_mcp import __version__


def register_routes(mcp: FastMCP) -> None:
    """Register infrastructure routes alongside /mcp."""

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> JSONResponse:
        return JSONResponse(
            {"status": "healthy", "service": "bls-escalation-mcp"}
        )

    @mcp.custom_route("/version", methods=["GET"])
    async def version(request: Request) -> JSONResponse:
        return JSONResponse({"version": __version__})
