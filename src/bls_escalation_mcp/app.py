"""Thin transport launcher; server assembly remains in server.py."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from bls_escalation_mcp.server import create_server


class LaunchSettings(BaseSettings):
    """Transport configuration, separate from BLS service configuration."""

    mcp_transport: Literal["stdio", "streamable-http"] = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = Field(default=8000, ge=1, le=65535)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def main() -> None:
    """Use a platform port first, explicit HTTP second, otherwise stdio."""
    settings = LaunchSettings()
    platform_port = os.getenv("DATABRICKS_APP_PORT") or os.getenv("PORT")
    if platform_port:
        port = int(platform_port)
        if not 1 <= port <= 65535:
            raise ValueError("Platform port must be between 1 and 65535")
        create_server().run(transport="http", host="0.0.0.0", port=port)
    elif settings.mcp_transport == "streamable-http":
        create_server().run(
            transport="http", host=settings.mcp_host, port=settings.mcp_port
        )
    else:
        create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
