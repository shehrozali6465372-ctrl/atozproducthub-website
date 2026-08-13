"""FastAPI dependencies for admin-service: auth, tenancy, service resolution."""

import uuid

import jwt
from fastapi import Depends, Request

from atoz_admin_service.config import Settings
from atoz_admin_service.errors import (
    AuthenticationError,
    MfaRequiredError,
    PermissionDeniedError,
    ServiceUnavailableError,
    UnsupportedNicheError,
    ValidationError,
)
from atoz_admin_service.services import AdminService
from atoz_backend_core.auth import TokenClaims, decode_token


def get_admin_service(request: Request) -> AdminService:
    """Resolve the service instance wired at app startup."""
    service = getattr(request.app.state, "admin_service", None)
    if service is None:
        raise ServiceUnavailableError("The admin database is not configured.")
    return service


def get_session_manager(request: Request):
    """Resolve the session manager (revocation + MFA state)."""
    manager = getattr(request.app.state, "session_manager", None)
    if manager is None:
        raise ServiceUnavailableError("Session manager is not configured.")
    return manager


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


def require_mfa_verified(permission: str):
    """Privileged actions require a verified MFA session (Task 19 §1)."""

    async def dependency(
        request: Request,
        claims: TokenClaims = Depends(require_permission(permission)),
    ) -> TokenClaims:
        manager = get_session_manager(request)
        session = await manager.get(claims.session_id)
        if session is None or not session.mfa_verified:
            raise MfaRequiredError("MFA verification is required for this action.")
        return claims

    return dependency


def get_niche_id(request: Request) -> str | None:
    """Optional ``X-Niche-Id`` header — tenancy context for scoped rows."""
    raw = request.headers.get("X-Niche-Id")
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError as exc:
        raise ValidationError("X-Niche-Id must be a valid UUID.") from exc


async def require_niche(
    niche_id: str | None = Depends(get_niche_id),
    service: AdminService = Depends(get_admin_service),
):
    """When supplied, the niche must exist in the local registry mirror."""
    if niche_id is None:
        return None
    niche = await service.get_niche(niche_id)
    if niche is None:
        raise UnsupportedNicheError("The requested niche is not registered.")
    return niche
