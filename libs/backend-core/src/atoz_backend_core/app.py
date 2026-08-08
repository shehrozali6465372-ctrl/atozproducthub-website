"""Shared FastAPI application factory for services and the gateway.

Wires middleware (request ID, security headers, rate limiting, metrics,
CORS, compression), observability routes (``/health``, ``/ready``,
``/metrics``), OpenTelemetry hooks, and OpenAPI metadata. No business
routes — consumers add their own routers.
"""

from collections.abc import Sequence

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from atoz_backend_core.config import BaseServiceSettings
from atoz_backend_core.db.postgres import check_database
from atoz_backend_core.db.redis import check_redis
from atoz_backend_core.logging import configure_logging
from atoz_backend_core.middleware.rate_limit import RateLimitMiddleware
from atoz_backend_core.middleware.request_id import RequestIdMiddleware
from atoz_backend_core.middleware.security_headers import SecurityHeadersMiddleware
from atoz_backend_core.observability.metrics import (
    MetricsMiddleware,
    metrics_response,
    register_app_metrics,
)
from atoz_backend_core.observability.otel import setup_otel

OPS_TAGS = [
    {"name": "system", "description": "Health, readiness, and metrics probes."},
]


def add_default_middleware(app: FastAPI, settings: BaseServiceSettings) -> None:
    """Add the shared middleware stack (order matters: outermost first)."""
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.rate_limit_enabled,
        rate=settings.rate_limit_per_second,
        burst=settings.rate_limit_burst,
    )
    app.add_middleware(SecurityHeadersMiddleware, production=settings.is_production)
    app.add_middleware(RequestIdMiddleware)


def add_observability_routes(
    app: FastAPI,
    *,
    settings: BaseServiceSettings,
    service_name: str,
    version: str,
) -> None:
    """Add ``/health``, ``/ready``, and ``/metrics`` endpoints."""

    @app.get("/health", tags=["system"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": service_name,
            "version": version,
            "environment": settings.app_env,
        }

    @app.get("/ready", tags=["system"], summary="Readiness probe")
    async def ready() -> JSONResponse:
        checks = [
            await check_database(settings.database_url),
            await check_redis(settings.redis_url),
        ]
        configured = [c for c in checks if c["status"] != "not_configured"]
        all_ok = all(c["status"] == "ok" for c in configured)
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={
                "status": "ok" if all_ok else "degraded",
                "service": service_name,
                "version": version,
                "components": checks,
            },
        )

    @app.get(
        "/metrics",
        tags=["system"],
        summary="Prometheus metrics",
        include_in_schema=False,
    )
    async def metrics():
        return metrics_response()


def configure_openapi(
    app: FastAPI,
    *,
    settings: BaseServiceSettings,
    service_name: str,
    version: str,
    description: str,
) -> None:
    """Set OpenAPI metadata: title, version, tags, and server origin."""
    app.title = f"{settings.app_name} — {service_name}"
    app.version = version
    app.description = description
    app.openapi_tags = OPS_TAGS
    app.servers = [{"url": "/", "description": "Current origin"}]


def create_service_app(
    *,
    service_name: str,
    version: str,
    settings: BaseServiceSettings,
    description: str = "AtozProductHub business service skeleton.",
    routers: Sequence[APIRouter] = (),
) -> FastAPI:
    """Build a production-ready skeleton app for a business service."""
    configure_logging(settings.app_log_level, service=service_name, env=settings.app_env)
    app = FastAPI()
    configure_openapi(
        app,
        settings=settings,
        service_name=service_name,
        version=version,
        description=description,
    )
    add_default_middleware(app, settings)
    add_observability_routes(
        app,
        settings=settings,
        service_name=service_name,
        version=version,
    )
    register_app_metrics(service=service_name, version=version)
    setup_otel(app, settings=settings)
    for router in routers:
        app.include_router(router)
    return app
