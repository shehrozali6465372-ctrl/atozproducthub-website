"""Content API routes: public reads + admin content management."""

from atoz_content_service.routes.admin import router as admin_router
from atoz_content_service.routes.public import router as public_router

__all__ = ["admin_router", "public_router"]
