"""Celery application for automation-service (M10 Step 2).

Business executors (Pinterest publishing, sitemap rebuild, affiliate
reconciliation, analytics rollups, AI OS dispatch) run as Celery tasks
against the durable ``queue_items`` ledger; the DB-driven scheduler tick is
woken by a Beat schedule.

Celery conventions applied (per Celery docs for production reliability):
``acks_late=True`` with ``worker_prefetch_multiplier=1`` so a crashed worker
does not lose claimed work; explicit time limits; ``max_retries=0`` on tasks
because retries belong to the durable ledger (never unbounded worker
auto-retries); and a single-scheduler Beat strategy (Redis ``SET NX EX``
lock in the tick) so duplicate periodic triggers are impossible.
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
        task_routes={
            "automation.run_executor": {"queue": "automation"},
            "automation.beat_tick": {"queue": "celery"},
        },
        beat_schedule={
            "automation-beat-tick": {
                "task": "automation.beat_tick",
                "schedule": settings.beat_tick_interval_seconds,
            },
        },
    )
    return app


# Module-level singleton imported by ``celery -A`` worker/Beat commands.
celery_app = build_celery_app()
