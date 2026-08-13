"""Celery application scaffold for automation-service (Task 20 §9).

Foundation only: the application, worker, and Beat entry points exist and
are configurable via environment; **no business tasks are registered yet**.
Step 2 wires executors (Pinterest publishing, sitemap rebuild, affiliate
reconciliation, AI OS job dispatch) as Celery tasks against the durable
``queue_items`` ledger.

Celery conventions applied now (per Celery docs for production reliability):
``acks_late=True`` with ``worker_prefetch_multiplier=1`` so a crashed worker
does not lose claimed work; explicit time limits; Beat is configured from an
empty schedule placeholder and must be run with a single-scheduler locking
strategy in production to avoid duplicate periodic triggers.
"""

from celery import Celery

from atoz_automation_service.config import Settings, get_settings


def build_celery_app(settings: Settings | None = None) -> Celery:
    """Create the Celery application bound to the service settings."""
    settings = settings or get_settings()
    app = Celery(
        "atoz_automation",
        broker=settings.celery_broker_url,
        backend=settings.celery_backend_url,
        include=["atoz_automation_service.celery_worker"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,
        task_soft_time_limit=3300,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=200,
        task_routes={},  # Step 2 registers routes per business queue
        beat_schedule={},  # Step 2 registers the production scheduler
    )
    return app


# Module-level singleton imported by ``celery -A`` worker/Beat commands.
celery_app = build_celery_app()
