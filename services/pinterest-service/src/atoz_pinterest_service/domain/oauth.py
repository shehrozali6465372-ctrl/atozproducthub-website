"""Pinterest OAuth 2.0 authorization-code flow primitives.

Implements state/CSRF protection (HMAC-signed state bound to the pending
account) and PKCE (plain code verifier) per Pinterest API v5 guidance.
Token exchange and refresh live in the service layer; token VALUES are
written to Vault behind ``vault_ref`` and never stored in the database or
returned to clients (Database Blueprint §5.2).
"""

import base64
import hashlib
import hmac
import os
import secrets
import urllib.parse


def new_state(secret: str, account_id: str) -> str:
    """HMAC-signed OAuth state bound to the pending account (CSRF protection).

    The returned token embeds the account id + a one-time nonce + signature;
    the callback re-derives the signature with the same server secret, so a
    forged state without the secret cannot pass verification.
    """
    nonce = secrets.token_urlsafe(16)
    body = f"{account_id}:{nonce}"
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}:{signature}"


def verify_state(secret: str, state: str) -> str | None:
    """Verify an OAuth state and return the embedded account id (or None)."""
    try:
        account_id, nonce, signature = state.split(":", 2)
    except ValueError:
        return None
    expected = hmac.new(
        secret.encode(), f"{account_id}:{nonce}".encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return account_id


def new_code_verifier() -> str:
    """PKCE plain code verifier (43–128 chars, unreserved characters)."""
    return base64.urlsafe_b64encode(os.urandom(48)).rstrip(b"=").decode()


def code_challenge(verifier: str) -> str:
    """S256 PKCE challenge derived from the verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def build_authorize_url(
    *,
    authorize_url: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge_value: str,
    scopes: list[str],
) -> str:
    """Build the Pinterest authorization URL with minimal scopes."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": code_challenge_value,
        "code_challenge_method": "S256",
    }
    return f"{authorize_url}?{urllib.parse.urlencode(params)}"


def parse_callback_params(query_params: dict[str, str]) -> tuple[str, str | None, str | None]:
    """Extract (code, state, error) from the OAuth callback query params.

    Raises ValueError when both an error and a usable code are absent.
    """
    error = query_params.get("error")
    code = query_params.get("code")
    state = query_params.get("state")
    if error:
        return "", state, error
    if not code or not state:
        raise ValueError("OAuth callback missing 'code' or 'state' parameter.")
    return code, state, None
