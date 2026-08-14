"""Application factory for analytics-service (M8 analytics business layer)."""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_analytics_service import __version__
from atoz_analytics_service.config import Settings, get_settings
from atoz_analytics_service.domain.pipeline import (
    ClickHouseWarehouse,
    EventBackbone,
    InMemoryEventBackbone,
    InMemoryWarehouse,
    KafkaEventBackbone,
    PipelineWorker,
    Warehouse,
)
from atoz_analytics_service.errors import register_exception_handlers
from atoz_analytics_service.routes import admin_router, public_router, webhook_router
from atoz_analytics_service.services import AnalyticsService
from atoz_backend_core.app import create_service_app
from atoz_backend_core.db.postgres import create_engine, create_session_factory
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Async session factory for the analytics database (analytics_db)."""
    return create_session_factory(create_engine(database_url))


def build_backbone(settings: Settings) -> EventBackbone:
    """Production backbone is Kafka; dev/CI default is in-memory."""
    if settings.kafka_enabled:
        return KafkaEventBackbone(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            topic=settings.kafka_topic,
            security_protocol=settings.kafka_security_protocol,
            sasl_mechanism=settings.kafka_sasl_mechanism,
            sasl_username=settings.kafka_sasl_username,
            sasl_password=settings.kafka_sasl_password,
        )
    return InMemoryEventBackbone()


def build_warehouse(settings: Settings) -> Warehouse:
    """Production warehouse is ClickHouse; dev/CI default is in-memory."""
    if settings.warehouse_enabled:
        return ClickHouseWarehouse(
            base_url=settings.clickhouse_url,
            database=settings.clickhouse_database,
            table=settings.clickhouse_table,
        )
    return InMemoryWarehouse()


def build_analytics_service(
    settings: Settings,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    backbone: EventBackbone | None = None,
    warehouse: Warehouse | None = None,
) -> AnalyticsService | None:
    """Wire the business service; returns None when no database is configured."""
    if session_factory is None:
        if not settings.database_url:
            return None
        session_factory = build_session_factory(settings.database_url)
    backbone = backbone or build_backbone(settings)
    warehouse = warehouse or build_warehouse(settings)
    publisher = EventPublisher(InMemoryEventBus(), publisher="analytics-service")
    return AnalyticsService(
        uow_factory=lambda: AnalyticsService.build_uow(session_factory),
        event_publisher=publisher,
        settings=settings,
        backbone=backbone,
        warehouse=warehouse,
        pipeline_worker=PipelineWorker(backbone, warehouse),
    )


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    backbone: EventBackbone | None = None,
    warehouse: Warehouse | None = None,
) -> FastAPI:
    """Build the analytics service app (health/readiness + analytics API)."""
    settings = settings or get_settings()

    app = create_service_app(
        service_name="analytics-service",
        version=__version__,
        settings=settings,
        description=(
            "Analytics business module — M8: first-party event collector, "
            "append-only ledger, Kafka/ClickHouse pipeline, daily rollups, "
            "and niche-scoped read models. Business layer only; no AI."
        ),
        routers=[public_router, admin_router, webhook_router],
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.analytics_service = build_analytics_service(
        settings, session_factory=session_factory, backbone=backbone, warehouse=warehouse
    )
    register_exception_handlers(app)
    return app


app = create_app()
