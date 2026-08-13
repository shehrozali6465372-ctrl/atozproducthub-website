"""FastAPI dependencies for automation-service: auth, tenancy, service."""

import uuid

import jwt
from fastapi import Depends, Request

from atoz_automation_service.config import Settings
from atoz_automation_service.errors import (
    AuthenticationError,
    PermissionDeniedError,
    ServiceUnavailableError,
    UnsupportedNicheError,
    ValidationError,
)
from atoz_automation_service.services import AutomationService
from atoz_backend_core.auth import TokenClaims, decode_token


def get_automation_service(request: Request) -> AutomationService:
    """Resolve the service instance wired at app startup."""
    service = getattr(request.app.state, "automation_service", None)
    if service is None:
        raise ServiceUnavailableError("The automation database is not configured.")
    return service


def require_permission(permission: str):
    """Verify the Bearer access token carries ``permission`` (RBAC claim)."""

    def dependency(request: Request) -> TokenClaims:
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


def get_niche_id(request: Request) -> str | None:
    """Optional ``X-Niche-Id`` header — tenancy context for scoped rows.

    Absent header = global scope (``niche_id IS NULL`` rows only); present
    header = strict niche scope (never mixes niches). Invalid UUIDs are
    rejected.
    """
    raw = request.headers.get("X-Niche-Id")
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError as exc:
        raise ValidationError("X-Niche-Id must be a valid UUID.") from exc


async def require_niche(
    niche_id: str | None = Depends(get_niche_id),
    service: AutomationService = Depends(get_automation_service),
):
    """When supplied, the niche must exist in the local registry mirror."""
    if niche_id is None:
        return None
    niche = await service.get_niche(niche_id)
    if niche is None:
        raise UnsupportedNicheError("The requested niche is not registered.")
    return niche
