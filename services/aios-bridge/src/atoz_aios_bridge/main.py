"""Application factory for the AI OS Bridge (skeleton + M10 Step 2 dispatch)."""

from fastapi import FastAPI

from atoz_aios_bridge import __version__
from atoz_aios_bridge.api import router
from atoz_aios_bridge.client import AiosBridgeClient
from atoz_aios_bridge.config import Settings, get_settings
from atoz_aios_bridge.errors import register_exception_handlers
from atoz_backend_core.app import create_service_app


def build_bridge_client(settings: Settings | None = None) -> AiosBridgeClient:
    """Construct the shared AI OS client (transport only)."""
    return AiosBridgeClient(settings or get_settings())


def create_app(
    *,
    settings: Settings | None = None,
    client: AiosBridgeClient | None = None,
) -> FastAPI:
    """Build the bridge app: shared middleware, observability, bridge API."""
    settings = settings or get_settings()
    app = create_service_app(
        service_name="aios-bridge",
        version=__version__,
        settings=settings,
        description=(
            "AI OS Bridge — the only AI OS contact point. Transport only: "
            "validation, retry, timeout, health, auth. No AI logic."
        ),
        routers=[router],
    )
    app.state.settings = settings
    app.state.aios_bridge_client = client or build_bridge_client(settings)
    register_exception_handlers(app)
    return app


app = create_app()
