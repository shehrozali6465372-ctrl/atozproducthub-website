"""HMAC-SHA256 request signing (API Contracts §8).

Outgoing requests carry ``X-AIOS-Signature``, ``X-AIOS-Timestamp``, and
``X-AIOS-Nonce``; incoming webhooks are verified with the same scheme.
Signing authenticates transport — it carries no content intelligence.
"""

import hashlib
import hmac
import time
import uuid
from typing import Any

ALGORITHM = "sha256"


def _canonical(method: str, path: str, timestamp: str, nonce: str, body: str) -> bytes:
    return f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n{body}".encode()


class AiosSigner:
    """Sign outgoing requests with HMAC-SHA256 over the canonical message."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("aios_api_key must be configured before signing")
        self._key = api_key.encode("utf-8")

    def sign(
        self,
        *,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> dict[str, str]:
        import json

        timestamp = timestamp or str(int(time.time()))
        nonce = uuid.uuid4().hex
        payload = json.dumps(body or {}, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            self._key, _canonical(method, path, timestamp, nonce, payload), hashlib.sha256
        ).hexdigest()
        return {
            "X-AIOS-Signature": signature,
            "X-AIOS-Timestamp": timestamp,
            "X-AIOS-Nonce": nonce,
            "X-AIOS-Algorithm": ALGORITHM,
        }


def verify_signature(
    *,
    api_key: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body: str,
    signature: str,
    allowed_skew_seconds: int = 300,
) -> bool:
    """Verify an incoming signature; also rejects stale timestamps."""
    try:
        if abs(int(time.time()) - int(timestamp)) > allowed_skew_seconds:
            return False
    except ValueError:
        return False
    expected = hmac.new(
        api_key.encode("utf-8"),
        _canonical(method, path, timestamp, nonce, body),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
