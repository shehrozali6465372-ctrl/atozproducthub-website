"""Application factory for automation-service (M10 automation foundation)."""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_automation_service import __version__
from atoz_automation_service.config import Settings, get_settings
from atoz_automation_service.errors import register_exception_handlers
from atoz_automation_service.executors import build_default_registry
from atoz_automation_service.repositories import AutomationUnitOfWork
from atoz_automation_service.routes import admin_router
from atoz_automation_service.services import AutomationService
from atoz_backend_core.app import create_service_app
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the automation database (automation_db)."""
    return create_session_factory(create_engine(database_url))


def build_automation_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    event_bus: InMemoryEventBus | None = None,
) -> AutomationService | None:
    """Wire the automation service; returns None when no DB is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    publisher = EventPublisher(event_bus or InMemoryEventBus(), publisher="automation-service")
    return AutomationService(
        uow_factory=lambda: AutomationUnitOfWork.build(session_factory),
        event_publisher=publisher,
        settings=settings,
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    event_bus: InMemoryEventBus | None = None,
) -> FastAPI:
    """Build the automation-service app (health/readiness + admin API)."""
    settings = settings or get_settings()

    app = create_service_app(
        service_name="automation-service",
        version=__version__,
        settings=settings,
        description=(
            "Business automation engine foundation — M10: durable rule/run "
            "state machines, scheduler + queue ledgers, retry policy, and "
            "AI OS Bridge correlation records. Business layer only; no AI."
        ),
        routers=[admin_router],
    )
    app.state.settings = settings
    app.state.automation_service = build_automation_service(
        settings, session_factory=session_factory, event_bus=event_bus
    )
    app.state.executor_registry = build_default_registry()
    register_exception_handlers(app)
    return app


app = create_app()
