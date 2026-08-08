"""Application factory for content-service (skeleton)."""

from atoz_backend_core.app import create_service_app
from atoz_content_service import __version__
from atoz_content_service.config import get_settings
from atoz_content_service.routes import router


def create_app():
    """Build the service app: shared middleware, observability, empty router."""
    settings = get_settings()
    return create_service_app(
        service_name="content-service",
        version=__version__,
        settings=settings,
        description="Content & articles business module (CMS) — skeleton only.",
        routers=[router],
    )


app = create_app()
