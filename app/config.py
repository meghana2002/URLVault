"""Application configuration powered by Pydantic Settings.

All values are sourced from environment variables (or a local `.env` file
in development). This keeps the service 12-factor compliant.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ------------------------------------------------------
    app_name: str = "http-metadata-inventory-service"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # --- MongoDB ----------------------------------------------------------
    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db: str = "metadata_inventory"
    mongo_collection: str = "metadata"
    mongo_max_pool_size: int = 50
    startup_retry_seconds: int = 30

    # --- HTTP collector ---------------------------------------------------
    http_timeout_seconds: float = Field(default=15.0, ge=1.0, le=120.0)
    http_max_redirects: int = Field(default=5, ge=0, le=20)
    http_user_agent: str = "MetadataInventoryBot/1.0"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached `Settings` instance (one per process)."""
    return Settings()