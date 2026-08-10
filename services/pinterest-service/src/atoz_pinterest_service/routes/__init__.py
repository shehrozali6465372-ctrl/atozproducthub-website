"""Pinterest API routes: admin management, public reads, and OAuth callback."""

from atoz_pinterest_service.routes.admin import router as admin_router
from atoz_pinterest_service.routes.oauth import router as oauth_router
from atoz_pinterest_service.routes.public import router as public_router

__all__ = ["admin_router", "public_router", "oauth_router"]
