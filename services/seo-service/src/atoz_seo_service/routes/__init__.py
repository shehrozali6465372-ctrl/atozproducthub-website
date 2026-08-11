"""SEO API routes: admin management, public reads, and event ingestion."""

from atoz_seo_service.routes.admin import router as admin_router
from atoz_seo_service.routes.public import router as public_router
from atoz_seo_service.routes.webhooks import router as webhook_router

__all__ = ["admin_router", "public_router", "webhook_router"]
