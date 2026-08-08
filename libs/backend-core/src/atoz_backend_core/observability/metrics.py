"""Prometheus metrics: HTTP request counters/durations and app info.

Exposed at ``/metrics`` (OpenMetrics text format) for the Grafana stack.
"""

import time

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
app_info = Gauge(
    "app_info",
    "Application identity and version",
    ["service", "version"],
)


def register_app_metrics(*, service: str, version: str) -> None:
    app_info.labels(service=service, version=version).set(1)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record method/path/status counters and durations for every request."""

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started
        path = request.url.path
        http_requests_total.labels(
            method=request.method, path=path, status=response.status_code
        ).inc()
        http_request_duration_seconds.labels(method=request.method, path=path).observe(duration)
        return response


def metrics_response() -> Response:
    """Return the OpenMetrics payload for the ``/metrics`` endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
