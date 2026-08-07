"""System endpoints (M1 foundation only — no business logic)."""

from fastapi import APIRouter

from atoz_api import __version__
from atoz_api.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return service health, name, version, and environment."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "atoz-api",
        "version": __version__,
        "environment": settings.app_env,
    }
