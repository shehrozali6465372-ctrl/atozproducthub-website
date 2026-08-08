"""Route registration for affiliate-service.

M3 ships an empty router: business endpoints arrive with their module
(Phase 4+). Only infrastructure routes (/health, /ready, /metrics) are
active today via the shared app factory.
"""

from fastapi import APIRouter

router = APIRouter(tags=["affiliate-service"])
