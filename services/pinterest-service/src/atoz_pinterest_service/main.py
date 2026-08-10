"""Application factory for pinterest-service (M6 Pinterest business layer)."""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_backend_core.app import create_service_app
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher
from atoz_pinterest_service import __version__
from atoz_pinterest_service.config import Settings, get_settings
from atoz_pinterest_service.domain.secrets import EnvSecretResolver, InMemoryTokenVault, TokenVault
from atoz_pinterest_service.errors import register_exception_handlers
from atoz_pinterest_service.routes import admin_router, oauth_router, public_router
from atoz_pinterest_service.services import PinterestService


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the Pinterest database (pinterest_db)."""
    return create_session_factory(create_engine(database_url))


def build_pinterest_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    token_vault: TokenVault | None = None,
) -> PinterestService | None:
    """Wire the business service; returns None when no database is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    publisher = EventPublisher(InMemoryEventBus(), publisher="pinterest-service")
    return PinterestService(
        uow_factory=lambda: PinterestService.build_uow(session_factory),
        event_publisher=publisher,
        settings=settings,
        secret_resolver=EnvSecretResolver(),
        token_vault=token_vault or InMemoryTokenVault(),
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    token_vault: TokenVault | None = None,
) -> FastAPI:
    """Build the pinterest service app (health/readiness + Pinterest API)."""
    settings = settings or get_settings()

    app = create_service_app(
        service_name="pinterest-service",
        version=__version__,
        settings=settings,
        description=(
            "Pinterest business module — M6: 10+ per-niche accounts, OAuth "
            "connect, boards/sections sync, pin queue publishing with "
            "idempotency + retry, per-account rate limits, and per-account "
            "analytics. Business layer only; no AI functionality."
        ),
        routers=[public_router, admin_router, oauth_router],
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.pinterest_service = build_pinterest_service(
        settings, session_factory=session_factory, token_vault=token_vault
    )
    register_exception_handlers(app)
    return app


app = create_app()
