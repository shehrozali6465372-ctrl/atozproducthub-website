"""Application factory for affiliate-service (skeleton)."""

from atoz_affiliate_service import __version__
from atoz_affiliate_service.config import get_settings
from atoz_affiliate_service.routes import router
from atoz_backend_core.app import create_service_app


def create_app():
    """Build the service app: shared middleware, observability, empty router."""
    settings = get_settings()
    return create_service_app(
        service_name="affiliate-service",
        version=__version__,
        settings=settings,
        description="Affiliate catalog, links, clicks, commissions — skeleton only.",
        routers=[router],
    )


app = create_app()
