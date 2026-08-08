"""Base task: retry/backoff defaults for business worker tasks.

Business tasks extend ``BaseTask`` and implement ``run``. Retry policy
follows API Contracts §7 (exponential backoff, 1s × 2, cap 60s, max 5
retries) for retryable failures.
"""

from typing import Any

from celery import Task


class BaseTask(Task):
    """Celery task with the project's retry defaults baked in."""

    autoretry_for: tuple[type[Exception], ...] = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = False

    def on_failure(self, exc: Any, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        # Skeleton: structured failure logging ships with the monitoring phase.
        super().on_failure(exc, task_id, args, kwargs, einfo)
