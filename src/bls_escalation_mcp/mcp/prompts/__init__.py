"""Explicit registration of individual MCP prompts.

The prompt modules in this package are planned stubs
(see docs/mcp_resources_prompts.md) and are intentionally not registered or
wired into ``create_server`` until implemented.
"""

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register every prompt exactly once (none implemented yet)."""
