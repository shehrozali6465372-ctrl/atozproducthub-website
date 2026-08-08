"""Shared service configuration (pydantic-settings + environment loading)."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["dev", "staging", "prod", "test"]


class BaseServiceSettings(BaseSettings):
    """Runtime settings shared by the gateway and every business service.

    Loaded from environment variables and an optional ``.env`` file;
    variable names are case-insensitive (``APP_ENV`` → ``app_env``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AtozProductHub Service"
    app_env: AppEnv = "dev"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"

    # Connections are optional in M3: health checks report them as
    # "not_configured" until Phase 4 wires real schemas.
    database_url: str | None = None
    redis_url: str | None = None

    # Observability (OpenTelemetry hooks; no-op unless enabled).
    otel_enabled: bool = False
    otel_service_name: str = "atoz-service"
    otel_exporter_endpoint: str = "http://localhost:4318/v1/traces"

    # CORS (frontend origins; gateway overrides per environment).
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Rate limiting (API Contracts §7: per-IP budgets, 429 + Retry-After).
    rate_limit_enabled: bool = True
    rate_limit_per_second: float = 100.0
    rate_limit_burst: int = 150

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_service_settings() -> BaseServiceSettings:
    """Return the cached default settings (subclasses may define their own)."""
    return BaseServiceSettings()
