"""Authentication endpoints (v1).

JWT access/refresh tokens, session-backed revocation, and RBAC-protected
identity resolution. Production supports the configured human-admin
credential and the UCOS machine credential; development keeps the local
compatibility identity.
"""

from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from atoz_api.config import Settings, get_settings
from atoz_backend_core.auth import (
    SessionManager,
    create_access_token,
    create_refresh_token,
    decode_token,
    require_permissions,
    verify_password,
)

router = APIRouter(tags=["auth"])


class TokenRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RevokeRequest(BaseModel):
    refresh_token: str


def _session_manager(request: Request) -> SessionManager:
    return request.app.state.session_manager


def _tokens(
    settings: Settings, *, subject: str, session_id: str, permissions: tuple[str, ...]
) -> dict[str, Any]:
    return {
        "access_token": create_access_token(
            secret=settings.jwt_secret,
            subject=subject,
            session_id=session_id,
            permissions=permissions,
            ttl_seconds=settings.jwt_access_ttl_seconds,
        ),
        "refresh_token": create_refresh_token(
            secret=settings.jwt_secret,
            subject=subject,
            session_id=session_id,
            ttl_seconds=settings.jwt_refresh_ttl_seconds,
        ),
        "token_type": "bearer",
        "expires_in": settings.jwt_access_ttl_seconds,
    }


@router.post(
    "/auth/token",
    summary="Exchange configured credentials for tokens",
    responses={
        401: {"description": "Invalid credentials"},
    },
)
async def issue_token(
    payload: TokenRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Exchange a configured human or machine credential for tokens."""
    if settings.app_env == "prod":
        is_admin = (
            settings.auth_admin_subject is not None
            and payload.username == settings.auth_admin_subject
            and settings.auth_admin_password_hash is not None
            and verify_password(payload.password, settings.auth_admin_password_hash)
        )
        is_ucos = (
            settings.ucos_client_id is not None
            and payload.username == settings.ucos_client_id
            and settings.ucos_client_secret is not None
            and payload.password == settings.ucos_client_secret
        )
        if is_admin:
            subject = settings.auth_admin_subject
            permissions = settings.auth_admin_permissions
        elif is_ucos:
            subject = f"ucos:{settings.ucos_client_id}"
            permissions = settings.ucos_permissions
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    else:
        if payload.username != settings.auth_dev_subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        if not settings.auth_dev_password_hash or not verify_password(
            payload.password, settings.auth_dev_password_hash
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        subject = payload.username
        permissions = settings.auth_dev_permissions

    manager = _session_manager(request)
    session = await manager.create(
        subject=subject,
        permissions=permissions,
        ttl_seconds=settings.jwt_refresh_ttl_seconds,
    )
    return _tokens(
        settings,
        subject=session.subject,
        session_id=session.session_id,
        permissions=session.permissions,
    )


@router.post("/auth/refresh", summary="Rotate refresh token for a new access token")
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Validate the refresh token and session, then issue fresh tokens."""
    try:
        claims = decode_token(
            payload.refresh_token, secret=settings.jwt_secret, expected_type="refresh"
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
        ) from exc

    manager = _session_manager(request)
    session = await manager.get(claims.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or revoked."
        )
    return _tokens(
        settings,
        subject=session.subject,
        session_id=session.session_id,
        permissions=session.permissions,
    )


@router.post("/auth/revoke", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the session")
async def revoke_token(
    payload: RevokeRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    """Revoke the session bound to the refresh token (immediate)."""
    try:
        claims = decode_token(
            payload.refresh_token, secret=settings.jwt_secret, expected_type="refresh"
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
        ) from exc
    await _session_manager(request).revoke(claims.session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", summary="Resolve the authenticated identity")
def me(context=Depends(require_permissions("auth:read"))) -> dict[str, Any]:
    """Return the authenticated subject, permissions, and session id."""
    return {
        "subject": context.subject,
        "permissions": list(context.permissions),
        "session_id": context.session_id,
    }
