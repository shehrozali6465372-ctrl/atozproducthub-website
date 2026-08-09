"""Service configuration (pydantic-settings + environment loading).

Inherits the shared backend-core settings and adds the content module
tuning: JWT verification for the admin API, local content storage, and
public-read defaults.
"""

from functools import lru_cache

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for content-service."""

    app_name: str = "AtozProductHub Content Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-content-jwt-secret-change-in-production"
    admin_read_permission: str = "content:read"
    admin_write_permission: str = "content:write"

    # Content bodies live outside the database (Database Blueprint §2.1):
    # object storage in production, a local directory in dev/tests.
    content_storage_dir: str = "var/content"

    # Public read defaults (API Contracts §7: budgets are per surface).
    default_page_size: int = 20
    max_page_size: int = 100

    # Canonical site origin used in content events (API Contracts §11).
    public_base_url: str = "https://atozproducthub.com"


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
