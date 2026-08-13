"""Admin-service API routes: admin/ops control plane + event ingestion."""

from atoz_admin_service.routes.admin import router as admin_router
from atoz_admin_service.routes.events import router as events_router

__all__ = ["admin_router", "events_router"]
