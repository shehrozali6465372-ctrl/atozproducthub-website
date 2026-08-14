"""AI OS Bridge configuration (pydantic-settings + environment loading)."""

from functools import lru_cache

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for the AI OS Bridge.

    ``AIOS_API_KEY`` comes from the environment/secret manager only — it is
    never committed. All other values are non-secret transport tuning.
    """

    app_name: str = "AtozProductHub AI OS Bridge"

    # AI OS endpoint (the only outbound target of the business layer).
    aios_base_url: str = "http://localhost:8100"
    aios_api_key: str = ""
    aios_timeout_seconds: float = 10.0

    # API Contracts §7: exponential backoff 1s x 2, cap 60s, max 5 retries.
    aios_max_retries: int = 5
    aios_retry_backoff_base: float = 1.0
    aios_retry_backoff_cap: float = 60.0

    # Circuit breaker (API Contracts §7): 50% failure / 60s recovery default.
    aios_circuit_failure_threshold: int = 5
    aios_circuit_recovery_timeout: float = 60.0

    # Contract schemas live in libs/contracts/aios/ (overridable in tests).
    aios_contracts_dir: str | None = None

    # Callback target for AI OS job-status webhooks (internal URL — never a
    # frontend URL). The inbound receiver verifies the AI OS signature
    # before processing.
    aios_callback_url: str = "http://localhost:8100/bridge/jobs/status"

    # Shared secret for business-layer service accounts (automation
    # executor dispatch). Empty in dev = header not enforced; production
    # sets a Vault-issued shared secret.
    internal_token: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return the cached bridge settings."""
    return Settings()
