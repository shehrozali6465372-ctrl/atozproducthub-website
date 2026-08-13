"""Service configuration for admin-service (M9 admin & operations layer).

Inherits the shared backend-core settings and adds the admin module
tuning: JWT verification for the admin API, the shared event-ingestion
secret, operator session controls, and the sibling-service health URLs used
by the operations dashboard (system status probes).
"""

from functools import lru_cache

from pydantic import Field

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for admin-service."""

    app_name: str = "AtozProductHub Admin Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-admin-jwt-secret-change-in-production"
    admin_read_permission: str = "admin:read"
    admin_write_permission: str = "admin:write"

    # Shared secret used to authenticate internal event ingestion
    # (content:published.v1, pin:published.v1, affiliate:click.v1, ...).
    # Dev default; producers must share the production value.
    event_webhook_secret: str = "dev-only-admin-event-secret-change-in-production"

    # Operator session controls (API Contracts §4: MFA required for
    # privileged actions; sessions revocable).
    session_ttl_seconds: int = 3600
    session_mfa_required_permissions: list[str] = Field(
        default_factory=lambda: ["admin:write", "automation:write"]
    )

    # Sibling business services probed by /system/status. Empty in dev; the
    # compose/CI stack injects the real URLs.
    service_health_urls: dict[str, str] = Field(default_factory=dict)

    # Durable queue + ops limits (Task 19 §5).
    queue_max_attempts: int = 5
    audit_export_max_rows: int = 5000
    audit_default_page_size: int = 50
    operation_log_max_details_bytes: int = 8192


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
