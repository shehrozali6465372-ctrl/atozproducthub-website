"""Application factory for analytics-service (skeleton)."""

from atoz_analytics_service import __version__
from atoz_analytics_service.config import get_settings
from atoz_analytics_service.routes import router
from atoz_backend_core.app import create_service_app


def create_app():
    """Build the service app: shared middleware, observability, empty router."""
    settings = get_settings()
    return create_service_app(
        service_name="analytics-service",
        version=__version__,
        settings=settings,
        description="Analytics events, metrics, reports — skeleton only.",
        routers=[router],
    )


app = create_app()
