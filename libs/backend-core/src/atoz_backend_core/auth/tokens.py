"""JWT access/refresh tokens (PyJWT) — API Contracts §4 (Admin API).

Access tokens carry the subject and a permissions snapshot; refresh tokens
carry the session id and token type. Tokens are stateless; sessions provide
revocation (see sessions.py).
"""

import time
import uuid
from dataclasses import dataclass
from typing import Any

import jwt

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    token_type: str
    session_id: str
    permissions: tuple[str, ...] = ()
    expires_at: int = 0
    raw: dict[str, Any] | None = None


def _encode(
    *,
    secret: str,
    subject: str,
    token_type: str,
    session_id: str,
    ttl_seconds: int,
    permissions: tuple[str, ...] = (),
    algorithm: str = "HS256",
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "sid": session_id,
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": uuid.uuid4().hex,
    }
    if permissions:
        payload["perms"] = list(permissions)
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_access_token(
    *,
    secret: str,
    subject: str,
    session_id: str,
    permissions: tuple[str, ...],
    ttl_seconds: int = 900,
) -> str:
    """Create a short-lived access token carrying the permissions snapshot."""
    return _encode(
        secret=secret,
        subject=subject,
        token_type=TOKEN_TYPE_ACCESS,
        session_id=session_id,
        ttl_seconds=ttl_seconds,
        permissions=permissions,
    )


def create_refresh_token(
    *,
    secret: str,
    subject: str,
    session_id: str,
    ttl_seconds: int = 604800,
) -> str:
    """Create a long-lived refresh token bound to a session."""
    return _encode(
        secret=secret,
        subject=subject,
        token_type=TOKEN_TYPE_REFRESH,
        session_id=session_id,
        ttl_seconds=ttl_seconds,
    )


def decode_token(
    token: str,
    *,
    secret: str,
    expected_type: str,
    algorithms: tuple[str, ...] = ("HS256",),
) -> TokenClaims:
    """Decode and validate a token; raises ``jwt.PyJWTError`` on failure."""
    payload = jwt.decode(token, secret, algorithms=algorithms)
    token_type = payload.get("type")
    if token_type != expected_type:
        raise jwt.InvalidTokenError(f"expected token type {expected_type!r}, got {token_type!r}")
    return TokenClaims(
        subject=str(payload["sub"]),
        token_type=token_type,
        session_id=str(payload["sid"]),
        permissions=tuple(payload.get("perms") or ()),
        expires_at=int(payload["exp"]),
        raw=payload,
    )
