"""Secret resolution boundary for Pinterest credentials and tokens.

Token VALUES never enter the database, responses, or logs (Database
Blueprint §5.2). This resolver abstracts Vault: production reads from Vault
via ``vault_ref``; the dev/local resolver reads from environment variables
with a ``PINTEREST_TOKEN_<ACCOUNT_ID>`` naming convention, so local runs and
tests never need a real Vault. The vault hook is a placeholder that raises
until the Platform team provisions the secret backend (same approach as
``atoz_backend_core.security.secrets``).
"""

import os
from abc import ABC, abstractmethod

from atoz_pinterest_service.errors import ServiceUnavailableError


class SecretResolver(ABC):
    """Resolves a secret by reference without ever logging its value."""

    @abstractmethod
    async def get(self, vault_ref: str) -> str: ...


class VaultSecretResolver(SecretResolver):
    """Production resolver — placeholder until the Vault hook is provisioned."""

    async def get(self, vault_ref: str) -> str:
        raise ServiceUnavailableError(f"Vault secret backend is not provisioned (ref={vault_ref}).")


class EnvSecretResolver(SecretResolver):
    """Dev/test resolver: reads secrets from environment variables.

    Token secrets use ``PINTEREST_TOKEN_<ACCOUNT_ID_UPPER>``; the OAuth
    client secret uses ``PINTEREST_OAUTH_CLIENT_SECRET``. Never logs values.
    """

    async def get(self, vault_ref: str) -> str:
        # Normalize a vault ref like vault://pinterest/accounts/<id>/token
        # into an env var name; fall back to the ref itself as a literal for
        # simple test fixtures (e.g. "env:dev-token" or "test:secret").
        if vault_ref.startswith("env:"):
            name = vault_ref[4:].upper().replace("-", "_").replace("/", "_")
            value = os.environ.get(name)
            if not value:
                raise ServiceUnavailableError(f"Missing environment secret {name}.")
            return value
        if vault_ref.startswith("test:"):
            return vault_ref[5:]
        if vault_ref.startswith("vault://"):
            account = vault_ref.rstrip("/").rsplit("/", 1)[-1]
            name = f"PINTEREST_TOKEN_{account.upper()}"
            value = os.environ.get(name)
            if not value:
                raise ServiceUnavailableError(f"Missing environment secret {name}.")
            return value
        raise ServiceUnavailableError(f"Unsupported secret reference: {vault_ref}")


class TokenVault(ABC):
    """Writable token store behind vault_ref (VALUES never in the database)."""

    @abstractmethod
    async def write(self, vault_ref: str, payload: dict[str, str]) -> None: ...

    @abstractmethod
    async def read(self, vault_ref: str) -> dict[str, str]: ...


class InMemoryTokenVault(TokenVault):
    """Dev/test vault: process-local storage keyed by ref."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, str]] = {}

    async def write(self, vault_ref: str, payload: dict[str, str]) -> None:
        self._store[vault_ref] = dict(payload)

    async def read(self, vault_ref: str) -> dict[str, str]:
        payload = self._store.get(vault_ref)
        if not payload:
            raise ServiceUnavailableError(f"No token material found for {vault_ref}.")
        return dict(payload)


class VaultTokenVault(TokenVault):
    """Production vault — placeholder until the Platform Vault hook is wired."""

    async def write(self, vault_ref: str, payload: dict[str, str]) -> None:
        raise ServiceUnavailableError(f"Vault secret backend is not provisioned (ref={vault_ref}).")

    async def read(self, vault_ref: str) -> dict[str, str]:
        raise ServiceUnavailableError(f"Vault secret backend is not provisioned (ref={vault_ref}).")
