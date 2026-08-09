"""Application factory for content-service (M4 CMS business layer)."""

from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_backend_core.app import create_service_app
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher
from atoz_content_service import __version__
from atoz_content_service.config import Settings, get_settings
from atoz_content_service.errors import register_exception_handlers
from atoz_content_service.routes import admin_router, public_router
from atoz_content_service.services import ContentService
from atoz_content_service.storage import ContentStore, LocalContentStore


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the content database (content_db)."""
    return create_session_factory(create_engine(database_url))


def build_content_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    content_store: ContentStore | None = None,
) -> ContentService | None:
    """Wire the business service; returns None when no database is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    store = content_store or LocalContentStore(Path(settings.content_storage_dir))
    publisher = EventPublisher(InMemoryEventBus(), publisher="content-service")
    return ContentService(
        uow_factory=lambda: ContentService.build_uow(session_factory),
        content_store=store,
        event_publisher=publisher,
        settings=settings,
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    content_store: ContentStore | None = None,
) -> FastAPI:
    """Build the content service app (health/readiness + content API)."""
    settings = settings or get_settings()

    app = create_service_app(
        service_name="content-service",
        version=__version__,
        settings=settings,
        description=(
            "Content & articles business module (CMS) — M4: content domain, "
            "lifecycle, versioning, taxonomy, and the public/admin content API. "
            "Business layer only; no AI functionality."
        ),
        routers=[public_router, admin_router],
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.content_service = build_content_service(
        settings, session_factory=session_factory, content_store=content_store
    )
    register_exception_handlers(app)
    return app


app = create_app()
