"""HashiCorp Vault client (M11 Phase C — guarded integration boundary).

The business layer never stores credentials in code or git. In production
the deployment pipeline injects environment variables sourced from Vault;
services may also hold ``vault://path`` references (e.g. Pinterest OAuth
secrets, SEO service accounts). This client resolves those references
against the Vault KV API when ``VAULT_ADDR``/``VAULT_TOKEN`` are present
and is a strict no-op otherwise, so dev/test environments never depend on
a Vault server.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx

logger = logging.getLogger("atoz.vault")

_VAULT_TOKEN_HEADER = "X-Vault-Token"
_VAULT_VERSION_HEADER = "X-Vault-Request"


@dataclass(frozen=True)
class VaultRef:
    """Parsed ``vault://path`` or ``vault://path?key=field`` reference."""

    path: str
    key: str | None = None

    @classmethod
    def parse(cls, ref: str) -> VaultRef | None:
        """Parse a ``vault://`` reference; return ``None`` for non-refs."""
        if not ref or not ref.startswith("vault://"):
            return None
        parsed = urlparse(ref)
        path = parsed.netloc + parsed.path
        query = parse_qs(parsed.query)
        key = query.get("key", [None])[0]
        return cls(path=path.lstrip("/"), key=key)


class VaultSecretsClient:
    """Thin KV v2 read client. Constructing is free; use only when needed.

    ``kv_mount`` is the KV secrets engine mount path (default ``secret``).
    """

    def __init__(
        self,
        *,
        addr: str | None = None,
        token: str | None = None,
        kv_mount: str = "secret",
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._addr = (addr or "").rstrip("/")
        self._token = token or ""
        self._kv_mount = kv_mount
        self._timeout = timeout_seconds
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self._addr and self._token)

    async def read_secret(self, path: str) -> dict[str, object] | None:
        """Read a KV v2 secret at ``secret/data/<path>``; ``None`` if absent."""
        if not self.configured:
            logger.debug("vault not configured; skipping read of %s", path)
            return None
        url = f"{self._addr}/v1/{self._kv_mount}/data/{path.lstrip('/')}"
        headers = {_VAULT_TOKEN_HEADER: self._token, _VAULT_VERSION_HEADER: "true"}
        async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            payload = response.json()
        data = payload.get("data", {}).get("data", {})
        return data if isinstance(data, dict) else None

    async def resolve(self, ref: str) -> str | None:
        """Resolve a ``vault://path?key=field`` reference to a string value."""
        parsed = VaultRef.parse(ref)
        if parsed is None:
            return None
        secret = await self.read_secret(parsed.path)
        if secret is None:
            logger.warning("vault secret not found: %s", parsed.path)
            return None
        if parsed.key is not None:
            value = secret.get(parsed.key)
        elif len(secret) == 1:
            value = next(iter(secret.values()))
        else:
            value = None
        if not isinstance(value, str):
            logger.warning("vault field %s/%s is not a string", parsed.path, parsed.key)
            return None
        return value
