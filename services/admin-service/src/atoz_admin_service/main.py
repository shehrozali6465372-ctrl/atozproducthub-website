"""Application factory for admin-service (M9 admin & operations layer)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_admin_service import __version__
from atoz_admin_service.config import Settings, get_settings
from atoz_admin_service.errors import register_exception_handlers
from atoz_admin_service.repositories import AdminUnitOfWork
from atoz_admin_service.routes import admin_router, events_router
from atoz_admin_service.services import AdminService
from atoz_backend_core.app import create_service_app
from atoz_backend_core.auth.sessions import InMemorySessionManager, RedisSessionManager
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the admin database (admin_db)."""
    return create_session_factory(create_engine(database_url))


def build_session_manager(settings: Settings):
    """In-memory in dev/CI; Redis-backed in production (revocation + MFA)."""
    if settings.redis_url:
        return RedisSessionManager(settings.redis_url)
    return InMemorySessionManager()


def build_admin_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> AdminService | None:
    """Wire the control-plane service; returns None when no DB is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    publisher = EventPublisher(InMemoryEventBus(), publisher="admin-service")
    return AdminService(
        uow_factory=lambda: AdminUnitOfWork.build(session_factory),
        event_publisher=publisher,
        settings=settings,
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    """Build the admin-service app (health/readiness + admin & ops API)."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.admin_service is not None:
            await app.state.admin_service.seed_reference_data()
        yield

    app = create_service_app(
        service_name="admin-service",
        version=__version__,
        settings=settings,
        description=(
            "Admin & operations control plane — M9: RBAC hardening, append-only "
            "audit, operations dashboard, queue/webhook visibility, notifications, "
            "and event ingestion. Business layer only; no AI."
        ),
        routers=[admin_router, events_router],
    )
    app.state.settings = settings
    app.state.session_manager = build_session_manager(settings)
    app.state.admin_service = build_admin_service(settings, session_factory=session_factory)
    register_exception_handlers(app)
    app.router.lifespan_context = lifespan
    return app


app = create_app()
