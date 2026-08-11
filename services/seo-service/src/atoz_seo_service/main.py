"""Application factory for seo-service (M7 SEO + discovery layer)."""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_backend_core.app import create_service_app
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher
from atoz_seo_service import __version__
from atoz_seo_service.config import Settings, get_settings
from atoz_seo_service.errors import register_exception_handlers
from atoz_seo_service.routes import admin_router, public_router, webhook_router
from atoz_seo_service.services import SearchIndexFactory, SeoService


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the SEO database (seo_db)."""
    return create_session_factory(create_engine(database_url))


def build_seo_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    search_index=None,
) -> SeoService | None:
    """Wire the business service; returns None when no database is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    publisher = EventPublisher(InMemoryEventBus(), publisher="seo-service")
    index = search_index or SearchIndexFactory.build(settings)
    return SeoService(
        uow_factory=lambda: SeoService.build_uow(session_factory),
        event_publisher=publisher,
        settings=settings,
        search_index=index,
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    search_index=None,
) -> FastAPI:
    """Build the SEO service app (health/readiness + SEO/search API)."""
    settings = settings or get_settings()

    app = create_service_app(
        service_name="seo-service",
        version=__version__,
        settings=settings,
        description=(
            "SEO & discovery business module — M7: URL registry, applied "
            "metadata (canonical/robots/OG/JSON-LD), sharded sitemaps, "
            "robots.txt, and niche-scoped lexical search indexing. Business "
            "layer only; no AI functionality."
        ),
        routers=[public_router, admin_router, webhook_router],
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.seo_service = build_seo_service(
        settings, session_factory=session_factory, search_index=search_index
    )
    register_exception_handlers(app)
    return app


app = create_app()
