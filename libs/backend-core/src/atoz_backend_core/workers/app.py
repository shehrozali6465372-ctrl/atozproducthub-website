"""Celery application factory for background workers.

Workers share one broker (Redis) and result backend; each service wires its
own queues (``<service>-q``) so business tasks stay isolated. No tasks are
defined here — services register them in Phase 4+.
"""

from celery import Celery

DEFAULT_BROKER_URL = "redis://localhost:6379/1"
DEFAULT_BACKEND_URL = "redis://localhost:6379/2"


def create_celery_app(
    *,
    name: str,
    broker_url: str = DEFAULT_BROKER_URL,
    backend_url: str = DEFAULT_BACKEND_URL,
    include: tuple[str, ...] = (),
) -> Celery:
    """Build a configured Celery app for a business service."""
    app = Celery(name, broker=broker_url, backend=backend_url, include=list(include))
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=60 * 60,
        task_soft_time_limit=55 * 60,
        broker_connection_retry_on_startup=True,
        task_default_queue=f"{name}-q",
        task_default_exchange=name,
        task_default_routing_key=name,
    )
    return app
