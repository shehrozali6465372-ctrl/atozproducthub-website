"""FastAPI dependencies: auth, tenancy, and account isolation for routes."""

import uuid

import jwt
from fastapi import Depends, Query, Request

from atoz_backend_core.auth import TokenClaims, decode_token
from atoz_pinterest_service.config import Settings
from atoz_pinterest_service.domain.entities import PinterestAccount, PinterestNiche
from atoz_pinterest_service.errors import (
    AccountIsolationError,
    AuthenticationError,
    PermissionDeniedError,
    ServiceUnavailableError,
    UnsupportedNicheError,
    ValidationError,
)
from atoz_pinterest_service.services import PinterestService


def get_pinterest_service(request: Request) -> PinterestService:
    """Resolve the service instance wired at app startup."""
    service = getattr(request.app.state, "pinterest_service", None)
    if service is None:
        raise ServiceUnavailableError("The Pinterest database is not configured.")
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
    service: PinterestService = Depends(get_pinterest_service),
) -> PinterestNiche:
    """Admin tenancy: the niche must exist in the local registry mirror."""
    niche = await service.get_niche(niche_id)
    if niche is None:
        raise UnsupportedNicheError("The requested niche is not registered.")
    return niche


async def require_active_niche(
    niche: PinterestNiche = Depends(require_niche),
) -> PinterestNiche:
    """Public tenancy: the niche must be registered AND active."""
    if niche.status != "active":
        raise UnsupportedNicheError("The requested niche is not active.")
    return niche


async def resolve_public_niche(
    niche: str | None = Query(default=None, min_length=1, max_length=200),
    service: PinterestService = Depends(get_pinterest_service),
) -> PinterestNiche:
    """Public routes identify the niche by slug (never by id)."""
    if not niche:
        raise UnsupportedNicheError("The 'niche' query parameter is required.")
    found = await service.get_niche_by_slug(niche)
    if found is None or found.status != "active":
        raise UnsupportedNicheError("The requested niche is not registered or active.")
    return found


def get_account_id(account_id: str) -> str:
    """Path account id — the mandatory account-scoped context (blueprint §4)."""
    if not account_id:
        raise AccountIsolationError()
    try:
        return str(uuid.UUID(account_id))
    except ValueError as exc:
        raise AccountIsolationError() from exc


async def require_account(
    account_id: str = Depends(get_account_id),
    niche_id: str = Depends(get_niche_id),
    service: PinterestService = Depends(get_pinterest_service),
) -> PinterestAccount:
    """Admin account tenancy: account must exist in this niche.

    Every account-scoped mutation goes through this dependency, so Account A
    can never be addressed under Account B's niche.
    """
    account = await service.get_account(account_id, niche_id=niche_id)
    if account is None:
        raise UnsupportedNicheError("Pinterest account not found in this niche.")
    return account
