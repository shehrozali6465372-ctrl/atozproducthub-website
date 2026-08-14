"""Celery app/worker tests (M10 Step 2): task registration, beat schedule."""

import pytest

from atoz_automation_service.celery_app import build_celery_app
from atoz_automation_service.celery_worker import beat_tick, run_executor
from atoz_automation_service.config import Settings

from .fixtures import make_settings


def test_celery_app_configuration() -> None:
    app = build_celery_app(make_settings(celery_broker_url="memory://"))
    assert app.main == "atoz_automation"
    assert app.conf.task_acks_late is True
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.beat_schedule["automation-beat-tick"]["task"] == "automation.beat_tick"
    assert app.conf.task_routes["automation.run_executor"] == {"queue": "automation"}


def test_celery_tasks_registered() -> None:
    app = build_celery_app(make_settings(celery_broker_url="memory://"))
    # Registering tasks happens at import; verify the names resolve.
    assert app.tasks["automation.run_executor"].name == "automation.run_executor"
    assert app.tasks["automation.beat_tick"].name == "automation.beat_tick"
    assert run_executor.max_retries == 0
    assert beat_tick.max_retries == 0


def test_worker_requires_database_url() -> None:
    settings = Settings(app_env="test", rate_limit_enabled=False, database_url="")
    from atoz_automation_service.celery_worker import _require_database

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        _require_database(settings)
