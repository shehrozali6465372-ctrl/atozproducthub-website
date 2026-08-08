"""Application factory for the AtozProductHub API gateway (M3)."""

from atoz_api import __version__
from atoz_api.auth import build_session_manager
from atoz_api.config import get_settings
from atoz_api.errors import register_exception_handlers
from atoz_api.middleware import AuthMiddleware
from atoz_api.routes import v1_router
from atoz_backend_core.app import create_service_app


def create_app():
    """Build the gateway: shared middleware/observability + auth + API v1."""
    settings = get_settings()

    app = create_service_app(
        service_name="atoz-api",
        version=__version__,
        settings=settings,
        description="AtozProductHub business API gateway — M3 backend foundation.",
        routers=[v1_router],
    )
    # Bearer auth: attaches request.state.auth when valid; never blocks.
    # One session manager shared by the token endpoints and the middleware.
    session_manager = build_session_manager(settings)
    app.add_middleware(AuthMiddleware, settings=settings, session_manager=session_manager)
    app.state.session_manager = session_manager

    register_exception_handlers(app)
    return app


app = create_app()
