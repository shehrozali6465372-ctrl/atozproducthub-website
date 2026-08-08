"""Background worker scaffolding (Celery).

Skeleton only: app factory, base task with retry/backoff defaults, and beat
schedule hooks. Business tasks arrive with their modules in Phase 4+.
"""

from atoz_backend_core.workers.app import create_celery_app
from atoz_backend_core.workers.base_task import BaseTask

__all__ = ["BaseTask", "create_celery_app"]
