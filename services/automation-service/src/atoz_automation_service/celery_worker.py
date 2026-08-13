"""Celery worker entry point (scaffold).

The module is imported by the application ``include`` list so ``celery -A
atoz_automation_service.celery_app:celery_app`` resolves task modules. No
business tasks exist in the M10 foundation; worker execution of ledger work
is Step 2.
"""

from atoz_automation_service.celery_app import celery_app

__all__ = ["celery_app"]
