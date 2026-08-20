"""Centralized application settings, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All external configuration for SentinelIQ.

    Values are read from environment variables (or a local `.env`
    file — see `.env.example`). Nothing in the rest of the codebase
    should call `os.environ` directly; go through `get_settings()`
    instead so configuration stays in one auditable place.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "SentinelIQ"
    app_env: str = "development"
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://sentineliq:sentineliq@localhost:5432/sentineliq"

    # --- AWS ---
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_bucket: str = "sentineliq-raw-logs"

    # --- Claude / Anthropic ---
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (env is read once per process)."""
    return Settings()
