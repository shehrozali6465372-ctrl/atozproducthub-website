"""Signed link tokens for the server-controlled redirector.

Redirect security model (M5 scope):
- The browser never supplies a destination URL; it only supplies a token.
- ``token`` in ``link_tokens`` is the opaque random id stored server-side.
- The full signed identifier is ``{token}.{hmac}`` where the HMAC is derived
  from the random token id and the service signing secret — so a guessed or
  tampered token fails signature validation before any lookup or redirect.
- Resolution validates signature, token record, expiry, revocation, link
  status, then records the click and redirects to the *stored*
  ``destination_url`` (never a client-supplied value).
"""

import hashlib
import hmac
import secrets


def _hmac_hex(value: str, *, secret: str) -> str:
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()[:32]


def new_signed_token(*, secret: str) -> str:
    """Return ``{random}.{hmac}``; the random part is stored in the DB."""
    raw = secrets.token_urlsafe(24)
    return f"{raw}.{_hmac_hex(raw, secret=secret)}"


def token_from_signed(signed: str) -> str:
    """Extract the stored random token id from a signed identifier."""
    return signed.rsplit(".", 1)[0]


def sign_token(raw: str, *, secret: str) -> str:
    """Return the signed identifier ``{raw}.{hmac}`` for a stored token."""
    return f"{raw}.{_hmac_hex(raw, secret=secret)}"


def validate_signed_token(signed: str, *, secret: str) -> str | None:
    """Return the random token id when the HMAC signature matches, else None."""
    if "." not in signed:
        return None
    raw, signature = signed.rsplit(".", 1)
    if not raw or not signature:
        return None
    expected = _hmac_hex(raw, secret=secret)
    if not hmac.compare_digest(signature, expected):
        return None
    return raw
