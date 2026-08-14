"""Shared service configuration (pydantic-settings + environment loading)."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["dev", "staging", "prod", "test"]

# Tokens that identify insecure dev-only or placeholder values. The
# production-secrets guard rejects these when APP_ENV=prod so a service can
# never start with credentials it inherited from a dev default (matched as
# substrings so credentials embedded in URLs are caught too).
DEV_ONLY_TOKENS = ("dev-only-", "dev-admin", "CHANGE_ME")

# Field-name markers for secrets that must never be empty in production
# (empty values would silently disable authentication/verification).
SECRET_FIELD_MARKERS = ("secret", "token", "password", "api_key", "_key")


def _contains_dev_token(value: object) -> bool:
    """Recursively scan strings for dev-only/placeholder tokens."""
    if isinstance(value, str):
        return any(token in value for token in DEV_ONLY_TOKENS)
    if isinstance(value, dict):
        return any(_contains_dev_token(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_dev_token(v) for v in value)
    return False


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

    @model_validator(mode="after")
    def _reject_dev_only_secrets_in_production(self) -> "BaseServiceSettings":
        """Fail fast when production runs with a dev-only credential default.

        M11 production hardening (ADR-0012): in ``prod`` every string field
        must carry an injected value. Dev defaults (``dev-only-...``,
        ``dev-admin``, ``CHANGE_ME``) and empty secret placeholders are
        rejected at startup instead of silently reaching a live deployment.
        """
        if self.app_env != "prod":
            return self
        for name, value in self.__dict__.items():
            if _contains_dev_token(value):
                raise ValueError(
                    f"field {name!r} still uses a dev-only default "
                    f"({value!r}); production requires an injected secret"
                )
            if value == "" and any(marker in name.lower() for marker in SECRET_FIELD_MARKERS):
                raise ValueError(
                    f"field {name!r} is empty; production requires an injected "
                    "secret (fail-fast, no silent defaults)"
                )
        return self


@lru_cache
def get_service_settings() -> BaseServiceSettings:
    """Return the cached default settings (subclasses may define their own)."""
    return BaseServiceSettings()
