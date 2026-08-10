"""Affiliate API routes: public reads, admin management, and webhooks."""

from atoz_affiliate_service.routes.admin import router as admin_router
from atoz_affiliate_service.routes.public import router as public_router
from atoz_affiliate_service.routes.webhooks import router as webhook_router

__all__ = ["admin_router", "public_router", "webhook_router"]
