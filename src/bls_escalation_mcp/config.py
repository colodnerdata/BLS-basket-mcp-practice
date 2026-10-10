from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the local BLS escalation MCP scaffold."""

    bls_api_key: str | None = Field(default=None, alias="BLS_API_KEY")
    database_path: str = Field(
        default="./bls_catalogue.db",
        alias="BLS_DATABASE_PATH",
    )
    http_timeout_seconds: float = Field(
        default=10.0,
        alias="BLS_HTTP_TIMEOUT_SECONDS",
    )
    http_retry_count: int = Field(default=2, alias="BLS_HTTP_RETRY_COUNT")
    weight_tolerance: float = Field(
        default=1e-4,
        alias="BLS_WEIGHT_TOLERANCE",
    )
    log_level: str = Field(default="INFO", alias="BLS_LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BLS_",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )


def get_settings() -> Settings:
    """Return a settings instance configured from environment variables."""
    return Settings()
