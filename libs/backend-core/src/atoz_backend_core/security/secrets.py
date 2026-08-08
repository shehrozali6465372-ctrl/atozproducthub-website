"""Secrets loading with Vault hooks.

M3 provides the Env-backed client plus a Vault KV v2 client. No secret value
is ever committed; configuration references vault paths only.
"""

import os
from typing import Protocol

import httpx


class SecretsClient(Protocol):
    """Reads a secret by name. Implementations never log values."""

    def get(self, name: str) -> str: ...


class EnvSecretsClient:
    """Resolve secrets from environment variables (default implementation)."""

    def __init__(self, prefix: str = "SECRET_") -> None:
        self._prefix = prefix

    def get(self, name: str) -> str:
        key = f"{self._prefix}{name.upper()}"
        try:
            return os.environ[key]
        except KeyError as exc:
            raise KeyError(f"secret not found: {key}") from exc


class VaultSecretsClient:
    """Hashicorp Vault KV v2 client.

    Reads ``VAULT_ADDR`` / ``VAULT_TOKEN`` (or explicit args). Only mount,
    path, and name are ever logged — never values.
    """

    def __init__(
        self,
        *,
        addr: str | None = None,
        token: str | None = None,
        mount: str = "secret",
        timeout: float = 5.0,
    ) -> None:
        self._addr = (addr or os.environ.get("VAULT_ADDR", "")).rstrip("/")
        self._token = token or os.environ.get("VAULT_TOKEN", "")
        self._mount = mount
        self._timeout = timeout
        if not self._addr or not self._token:
            raise RuntimeError("VAULT_ADDR and VAULT_TOKEN are required for VaultSecretsClient")

    def get(self, name: str) -> str:
        response = httpx.get(
            f"{self._addr}/v1/{self._mount}/data/{name}",
            headers={"X-Vault-Token": self._token},
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json().get("data", {}).get("data", {})
        value = data.get(name)
        if value is None:
            raise KeyError(f"secret not found in vault: {self._mount}/{name}")
        return str(value)
