"""Celery skeleton: app factory and base task."""

from atoz_backend_core.workers.app import create_celery_app
from atoz_backend_core.workers.base_task import BaseTask


def test_celery_app_factory() -> None:
    app = create_celery_app(name="content-service", broker_url="redis://localhost:6379/9")
    assert app.main == "content-service"
    assert app.conf.task_default_queue == "content-service-q"
    assert app.conf.timezone == "UTC"


def test_base_task_retry_defaults() -> None:
    assert BaseTask.retry_kwargs == {"max_retries": 5}
    assert BaseTask.retry_backoff is True
    assert BaseTask.retry_backoff_max == 60
    assert BaseTask.retry_jitter is False
