"""Gateway configuration (pydantic-settings + environment loading).

Inherits the shared backend-core settings and adds JWT/auth placeholders.
Phase 5 (Authentication) replaces the dev identity with OIDC; until then
the dev credentials are local-only and disabled in production.
"""

from functools import lru_cache

from atoz_backend_core.config import BaseServiceSettings

# Dev-only password hash for the placeholder auth endpoint (Phase 5 = OIDC).
# Password: dev-admin (local environments and tests only; disabled in prod).
DEV_ADMIN_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$nhz6k4Zk2LasobNIuOv2dw$"
    "taDfV3H7Z1LGZvAl578lUxbguHeJjuZAQbFh+ubIBps"
)


class Settings(BaseServiceSettings):
    """Runtime settings for the API gateway."""

    app_name: str = "AtozProductHub API"

    # JWT (dev defaults; production overrides via environment/secrets).
    jwt_secret: str = "dev-only-jwt-secret-change-in-production"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 604800

    # Dev identity placeholder (Phase 5 replaces with OIDC; never enabled in prod).
    auth_dev_subject: str = "dev-admin"
    auth_dev_password_hash: str = DEV_ADMIN_PASSWORD_HASH
    auth_dev_permissions: tuple[str, ...] = ("auth:read", "admin:read", "analytics:read")


@lru_cache
def get_settings() -> Settings:
    """Return the cached gateway settings."""
    return Settings()
