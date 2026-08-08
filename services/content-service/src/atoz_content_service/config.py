"""Service configuration (pydantic-settings + environment loading)."""

from functools import lru_cache

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for content-service; inherits the shared backend core."""

    app_name: str = "AtozProductHub Content Service"


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
