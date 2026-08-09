"""FastAPI dependencies: auth, tenancy, and service access for content routes."""

import uuid

import jwt
from fastapi import Depends, Query, Request

from atoz_backend_core.auth import TokenClaims, decode_token
from atoz_content_service.config import Settings
from atoz_content_service.domain.entities import Niche
from atoz_content_service.domain.enums import NicheStatus
from atoz_content_service.errors import (
    AuthenticationError,
    PermissionDeniedError,
    ServiceUnavailableError,
    UnsupportedNicheError,
    ValidationError,
)
from atoz_content_service.services import ContentService


def get_content_service(request: Request) -> ContentService:
    """Resolve the service instance wired at app startup."""
    service = getattr(request.app.state, "content_service", None)
    if service is None:
        raise ServiceUnavailableError("The content database is not configured.")
    return service


def require_permission(permission: str):
    """Verify the Bearer access token carries ``permission`` (RBAC claim)."""

    def dependency(request: Request) -> TokenClaims:
        # The app's settings (not the cached module singleton) carry the
        # JWT secret so tests and deployments can override per app instance.
        settings: Settings = request.app.state.settings
        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            raise AuthenticationError("Bearer access token required.")
        try:
            claims = decode_token(
                header[7:].strip(), secret=settings.jwt_secret, expected_type="access"
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired access token.") from exc
        if permission not in claims.permissions:
            raise PermissionDeniedError(f"Missing permission: {permission}.")
        return claims

    return dependency


def get_niche_id(request: Request) -> str:
    """Mandatory ``X-Niche-Id`` header — the tenancy context (DB Blueprint §4)."""
    raw = request.headers.get("X-Niche-Id")
    if not raw:
        raise ValidationError("X-Niche-Id header is required for niche-scoped requests.")
    try:
        return str(uuid.UUID(raw))
    except ValueError as exc:
        raise ValidationError("X-Niche-Id must be a valid UUID.") from exc


async def require_niche(
    niche_id: str = Depends(get_niche_id),
    service: ContentService = Depends(get_content_service),
) -> Niche:
    """Admin tenancy: the niche must exist (any status is manageable)."""
    niche = await service.get_niche(niche_id)
    if niche is None:
        raise UnsupportedNicheError("The requested niche is not registered.")
    return niche


async def require_active_niche(
    niche: Niche = Depends(require_niche),
) -> Niche:
    """Public tenancy: the niche must be registered AND active."""
    if niche.status != NicheStatus.ACTIVE:
        raise UnsupportedNicheError("The requested niche is not active.")
    return niche


async def resolve_public_niche(
    niche: str | None = Query(default=None, min_length=1, max_length=200),
    service: ContentService = Depends(get_content_service),
) -> Niche:
    """Public routes identify the niche by slug (never by id)."""
    if not niche:
        raise UnsupportedNicheError("The 'niche' query parameter is required.")
    found = await service.get_niche_by_slug(niche)
    if found is None or found.status != NicheStatus.ACTIVE:
        raise UnsupportedNicheError("The requested niche is not registered or active.")
    return found
