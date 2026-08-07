"""Application configuration (pydantic-settings + environment loading)."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["dev", "staging", "prod", "test"]


class Settings(BaseSettings):
    """Runtime settings, loaded from environment variables and an optional ``.env`` file.

    Variable names are case-insensitive: ``APP_ENV`` maps to ``app_env``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AtozProductHub API"
    app_env: AppEnv = "dev"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"

    # Reserved connection settings (consumed by later phases, M4+).
    database_url: str = "postgresql+psycopg://atoz:atoz@localhost:5432/atoz"
    redis_url: str = "redis://localhost:6379/0"

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
