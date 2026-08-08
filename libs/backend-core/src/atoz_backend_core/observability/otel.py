"""OpenTelemetry hooks (guarded).

Tracing is a no-op unless ``otel_enabled`` is set; the heavy instrumentation
dependencies live in the ``[otel]`` extra and are never required for the base
install. When enabled, FastAPI instrumentation and an OTLP HTTP exporter are
wired; failures degrade to no-op so tracing can never take a service down.
"""

import logging

logger = logging.getLogger("atoz.otel")


def setup_otel(app, *, settings) -> None:
    """Configure OpenTelemetry tracing hooks for a FastAPI app."""
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(
            resource=Resource.create({"service.name": settings.otel_service_name})
        )
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint))
        )
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        logger.info(
            "opentelemetry enabled",
            extra={"extra_fields": {"endpoint": settings.otel_exporter_endpoint}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("opentelemetry disabled: %s", exc)
