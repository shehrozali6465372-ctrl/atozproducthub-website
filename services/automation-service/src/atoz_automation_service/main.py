"""Application factory for automation-service (skeleton)."""

from atoz_automation_service import __version__
from atoz_automation_service.config import get_settings
from atoz_automation_service.routes import router
from atoz_backend_core.app import create_service_app


def create_app():
    """Build the service app: shared middleware, observability, empty router."""
    settings = get_settings()
    return create_service_app(
        service_name="automation-service",
        version=__version__,
        settings=settings,
        description="Business automation workflows — skeleton only (ADR-0002).",
        routers=[router],
    )


app = create_app()
