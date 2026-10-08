"""Explicit registration of individual MCP resources."""

from fastmcp import FastMCP

from bls_escalation_mcp.mcp.resources import (
    bls_api_setup,
    methodology_composite_index_resource,
    methodology_locality_resource,
    series_resource,
)


def register_resources(mcp: FastMCP) -> None:
    """Register every resource exactly once."""
    methodology_composite_index_resource.register(mcp)
    methodology_locality_resource.register(mcp)
    series_resource.register(mcp)
    bls_api_setup.register(mcp)
