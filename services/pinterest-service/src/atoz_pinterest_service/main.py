"""Application factory for pinterest-service (skeleton)."""

from atoz_backend_core.app import create_service_app
from atoz_pinterest_service import __version__
from atoz_pinterest_service.config import get_settings
from atoz_pinterest_service.routes import router


def create_app():
    """Build the service app: shared middleware, observability, empty router."""
    settings = get_settings()
    return create_service_app(
        service_name="pinterest-service",
        version=__version__,
        settings=settings,
        description="Pinterest accounts, boards, pins, scheduling — skeleton only.",
        routers=[router],
    )


app = create_app()
