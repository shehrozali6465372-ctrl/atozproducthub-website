"""Application factory for the AtozProductHub API gateway."""

from fastapi import FastAPI

from atoz_api import __version__
from atoz_api.api import router
from atoz_api.config import get_settings
from atoz_api.errors import register_exception_handlers
from atoz_api.logging import configure_logging
from atoz_api.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    """Build a configured FastAPI application (M1 foundation)."""
    settings = get_settings()
    configure_logging(settings.app_log_level, env=settings.app_env)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AtozProductHub business API gateway — M1 foundation.",
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
