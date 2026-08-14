"""Service configuration for automation-service (M10 Step 2).

Inherits the shared backend-core settings and adds the automation module
tuning: JWT verification for the admin API, sibling-service endpoints and
secrets used by the executors (service-to-service JWT, Vault in
production), the durable queue retry policy, executor timeouts, the Celery
broker/backend URLs, and the default notification recipient.
"""

from functools import lru_cache

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for automation-service."""

    app_name: str = "AtozProductHub Automation Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-automation-jwt-secret-change-in-production"
    automation_read_permission: str = "automation:read"
    automation_write_permission: str = "automation:write"

    # Durable queue retry policy (Task 20 §5): exponential backoff + jitter.
    queue_max_attempts: int = 5
    queue_retry_base_delay_seconds: float = 30.0
    queue_retry_max_delay_seconds: float = 86400.0
    queue_retry_jitter: float = 0.1

    # Job-run retry bound (Platform job_runs carry their own attempts column).
    job_max_attempts: int = 5

    # Celery scaffold + execution (M10 Step 2): broker/backend from env.
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    # Executor runtime limits.
    executor_timeout_seconds: float = 300.0
    beat_tick_interval_seconds: int = 60
    beat_lock_ttl_seconds: int = 55

    # Notifications: best-effort, at-most-once per outcome. When no
    # recipient is configured the executor skips notifications entirely
    # (routing per operator lands with the Authentication milestone).
    default_notification_recipient_id: str | None = None
    admin_base_url: str = "http://localhost:8700"
    admin_jwt_secret: str = "dev-only-admin-jwt-secret-change-in-production"
    admin_write_permission: str = "admin:write"
    # Shared secret for the admin-service internal notification channel
    # (``X-Internal-Token``); empty in dev = header not sent/enforced.
    admin_internal_token: str = ""

    # Sibling business services called by the executors (service-to-service
    # JWT minted against each sibling's secret; production via Vault).
    pinterest_base_url: str = "http://localhost:8400"
    pinterest_jwt_secret: str = "dev-only-pinterest-jwt-secret-change-in-production"
    pinterest_write_permission: str = "pinterest:write"
    seo_base_url: str = "http://localhost:8500"
    seo_jwt_secret: str = "dev-only-seo-jwt-secret-change-in-production"
    seo_write_permission: str = "seo:write"
    affiliate_base_url: str = "http://localhost:8300"
    affiliate_jwt_secret: str = "dev-only-affiliate-jwt-secret-change-in-production"
    affiliate_write_permission: str = "affiliate:write"
    analytics_base_url: str = "http://localhost:8600"
    analytics_jwt_secret: str = "dev-only-analytics-jwt-secret-change-in-production"
    analytics_write_permission: str = "analytics:write"

    # AI OS Bridge (the only AI OS contact point).
    aios_bridge_base_url: str = "http://localhost:8100"
    aios_bridge_internal_token: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
