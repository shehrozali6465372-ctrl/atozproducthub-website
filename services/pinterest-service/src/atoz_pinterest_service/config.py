"""Service configuration (pydantic-settings + environment loading).

Inherits the shared backend-core settings and adds the Pinterest module
tuning: JWT verification for the admin API, OAuth client registration,
per-account rate limits, and public-read defaults. Secret material (OAuth
client secret, access/refresh tokens) is never stored here — tokens live in
Vault behind ``vault_ref`` (Database Blueprint §5.2); dev-only defaults are
marked and must be replaced via Vault in production.
"""

from functools import lru_cache

from pydantic import Field

from atoz_backend_core.config import BaseServiceSettings

# Pinterest API v5 minimum scopes for board/pin management (Task 16 scope).
DEFAULT_SCOPES = ["boards:read", "boards:write", "pins:read", "pins:write"]


class Settings(BaseServiceSettings):
    """Runtime settings for pinterest-service."""

    app_name: str = "AtozProductHub Pinterest Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-pinterest-jwt-secret-change-in-production"
    admin_read_permission: str = "pinterest:read"
    admin_write_permission: str = "pinterest:write"

    # OAuth 2.0 authorization-code flow (API Contracts §8.5).
    oauth_client_id: str = "dev-only-pinterest-client-id"
    oauth_client_secret_ref: str = "vault://pinterest/oauth/client-secret"
    oauth_redirect_uri: str = "http://localhost:8400/oauth/callback"
    oauth_authorize_url: str = "https://www.pinterest.com/oauth/"
    oauth_token_url: str = "https://api.pinterest.com/v5/oauth/token"
    oauth_state_secret: str = "dev-only-pinterest-oauth-state-secret-change-in-production"
    oauth_scopes: list[str] = Field(default_factory=lambda: list(DEFAULT_SCOPES))

    # Pinterest API base + version (typed client, org_read/org_write budgets).
    pinterest_api_base: str = "https://api.pinterest.com/v5"
    request_timeout_seconds: float = 15.0
    max_retries: int = 3
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 30.0
    # Per-account token buckets by rate-limit category (never one global
    # limiter): org_read and org_write are Pinterest's documented categories.
    rate_limit_read_per_minute: int = 600
    rate_limit_write_per_minute: int = 200

    # Queue worker defaults (pin publishing).
    queue_batch_size: int = 10
    publish_retry_attempts: int = 3

    # Public read defaults (API Contracts §7: budgets are per surface).
    default_page_size: int = 20
    max_page_size: int = 100

    # Canonical site origin used in pin destination URLs.
    public_base_url: str = "https://atozproducthub.com"


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
