"""Production configuration for the AtozProductHub API gateway."""

from functools import lru_cache

from pydantic import model_validator

from atoz_backend_core.config import BaseServiceSettings

DEV_ADMIN_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$nhz6k4Zk2LasobNIuOv2dw$"
    "taDfV3H7Z1LGZvAl578lUxbguHeJjuZAQbFh+ubIBps"
)


class Settings(BaseServiceSettings):
    """Runtime settings for the API gateway and authentication issuer."""

    app_name: str = "AtozProductHub API"
    jwt_secret: str = "dev-only-jwt-secret-change-in-production"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 604800

    # Local-only compatibility identity. Production must use injected values.
    auth_dev_subject: str = "dev-admin"
    auth_dev_password_hash: str = DEV_ADMIN_PASSWORD_HASH
    auth_dev_permissions: tuple[str, ...] = ("auth:read", "admin:read", "analytics:read")

    # Production human-admin credential (password is stored only as Argon2id hash).
    auth_admin_subject: str | None = None
    auth_admin_password_hash: str | None = None
    auth_admin_permissions: tuple[str, ...] = (
        "auth:read",
        "admin:read",
        "content:read",
        "content:write",
    )

    # UCOS machine-to-machine credential. The secret is exchanged server-side
    # for a short-lived JWT and is never returned or embedded in an access token.
    ucos_client_id: str | None = None
    ucos_client_secret: str | None = None
    ucos_permissions: tuple[str, ...] = ("content:read", "content:write")

    @model_validator(mode="after")
    def require_production_auth(self) -> "Settings":
        if self.app_env == "prod":
            required = {
                "AUTH_ADMIN_SUBJECT": self.auth_admin_subject,
                "AUTH_ADMIN_PASSWORD_HASH": self.auth_admin_password_hash,
                "UCOS_CLIENT_ID": self.ucos_client_id,
                "UCOS_CLIENT_SECRET": self.ucos_client_secret,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(
                    "Production authentication is fail-closed; missing: " + ", ".join(missing)
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
