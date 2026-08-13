"""Service configuration for automation-service (M10 automation foundation).

Inherits the shared backend-core settings and adds the automation module
tuning: JWT verification for the admin API, the durable queue retry policy
(exponential backoff), the job-run retry bound, and the Celery broker/backend
URLs (scaffold only — no tasks in the foundation).
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

    # Celery scaffold (Step 2 wires executors): broker/backend from env.
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
