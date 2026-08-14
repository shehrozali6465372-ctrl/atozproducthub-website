"""Executor registry: name → executor for the Celery task runner."""

from atoz_automation_service.executors.base import Executor


class ExecutorRegistry:
    """Thread-safe registry of executor instances (workers are multi-threaded)."""

    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}
        self._lock = __import__("threading").Lock()

    def register(self, executor: Executor) -> None:
        if not executor.name:
            raise ValueError("executor.name must be set")
        with self._lock:
            self._executors[executor.name] = executor

    def get(self, name: str) -> Executor | None:
        with self._lock:
            return self._executors.get(name)

    def by_queue(self, queue: str) -> Executor | None:
        """Find the single executor bound to a business queue (e.g. ``seo``)."""
        with self._lock:
            matches = [e for e in self._executors.values() if e.queue == queue]
            return matches[0] if len(matches) == 1 else None

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._executors)

    def __contains__(self, name: str) -> bool:
        return self.get(name) is not None
