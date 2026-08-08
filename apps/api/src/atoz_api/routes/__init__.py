"""API v1 routes (gateway). Versioning: everything under ``/api/v1``."""

from fastapi import APIRouter

from atoz_api.routes.auth_routes import router as auth_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)

__all__ = ["v1_router"]
