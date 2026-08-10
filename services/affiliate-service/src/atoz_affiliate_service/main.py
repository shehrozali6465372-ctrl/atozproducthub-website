"""Application factory for affiliate-service (M5 affiliate business layer)."""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_affiliate_service import __version__
from atoz_affiliate_service.config import Settings, get_settings
from atoz_affiliate_service.errors import register_exception_handlers
from atoz_affiliate_service.routes import admin_router, public_router, webhook_router
from atoz_affiliate_service.services import AffiliateService
from atoz_backend_core.app import create_service_app
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the affiliate database (affiliate_db)."""
    return create_session_factory(create_engine(database_url))


def build_affiliate_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> AffiliateService | None:
    """Wire the business service; returns None when no database is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    publisher = EventPublisher(InMemoryEventBus(), publisher="affiliate-service")
    return AffiliateService(
        uow_factory=lambda: AffiliateService.build_uow(session_factory),
        event_publisher=publisher,
        settings=settings,
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    """Build the affiliate service app (health/readiness + affiliate API)."""
    settings = settings or get_settings()

    app = create_service_app(
        service_name="affiliate-service",
        version=__version__,
        settings=settings,
        description=(
            "Affiliate business module — M5: networks, merchants, offers, "
            "links, signed redirects, click/conversion ledgers, commissions, "
            "reconciliation, and the public/admin affiliate API. "
            "Business layer only; no AI functionality."
        ),
        routers=[public_router, admin_router, webhook_router],
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.affiliate_service = build_affiliate_service(settings, session_factory=session_factory)
    register_exception_handlers(app)
    return app


app = create_app()
