"""Application factory for the AI OS Bridge (skeleton)."""

from atoz_aios_bridge import __version__
from atoz_aios_bridge.api import router
from atoz_aios_bridge.config import get_settings
from atoz_backend_core.app import create_service_app


def create_app():
    """Build the bridge app: shared middleware, observability, bridge status."""
    settings = get_settings()
    return create_service_app(
        service_name="aios-bridge",
        version=__version__,
        settings=settings,
        description="AI OS Bridge — the only AI OS contact point. Transport only; no AI logic.",
        routers=[router],
    )


app = create_app()
