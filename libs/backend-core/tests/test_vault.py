"""Vault client boundary tests (no live server — mocked transport)."""

import asyncio

import httpx

from atoz_backend_core.security.vault import VaultRef, VaultSecretsClient


def _fake_transport(secret: dict[str, object] | None, status: int = 200):
    async def handler(request: httpx.Request) -> httpx.Response:
        if status == 404:
            return httpx.Response(404, request=request)
        return httpx.Response(status, json={"data": {"data": secret}}, request=request)

    return httpx.MockTransport(handler)


def test_ref_parse() -> None:
    assert VaultRef.parse("vault://pinterest/oauth/client-secret?key=value") == VaultRef(
        path="pinterest/oauth/client-secret", key="value"
    )
    assert VaultRef.parse("plain-value") is None
    assert VaultRef.parse("") is None


def test_not_configured_is_noop() -> None:
    client = VaultSecretsClient(addr="", token="")
    assert client.configured is False
    assert asyncio.run(client.read_secret("x/y")) is None
    assert asyncio.run(client.resolve("vault://x/y?key=z")) is None


def test_read_secret_kv_v2() -> None:
    client = VaultSecretsClient(
        addr="http://vault:8200",
        token="dev-root-token",
        transport=_fake_transport({"value": "s3cret", "extra": "ignored"}),
    )
    assert client.configured is True
    assert asyncio.run(client.read_secret("pinterest/oauth/client-secret")) == {
        "value": "s3cret",
        "extra": "ignored",
    }


def test_resolve_keyed_ref() -> None:
    client = VaultSecretsClient(
        addr="http://vault:8200",
        token="dev-root-token",
        transport=_fake_transport({"value": "s3cret"}),
    )
    resolved = asyncio.run(client.resolve("vault://pinterest/oauth/client-secret?key=value"))
    assert resolved == "s3cret"


def test_resolve_single_field_ref() -> None:
    client = VaultSecretsClient(
        addr="http://vault:8200",
        token="dev-root-token",
        transport=_fake_transport({"only": "value"}),
    )
    assert asyncio.run(client.resolve("vault://seo/bing/api-key")) == "value"


def test_resolve_missing_secret_returns_none() -> None:
    client = VaultSecretsClient(
        addr="http://vault:8200",
        token="dev-root-token",
        transport=_fake_transport(None, status=404),
    )
    assert asyncio.run(client.resolve("vault://missing/path?key=value")) is None


def test_resolve_multi_field_without_key_returns_none() -> None:
    client = VaultSecretsClient(
        addr="http://vault:8200",
        token="dev-root-token",
        transport=_fake_transport({"a": "1", "b": "2"}),
    )
    assert asyncio.run(client.resolve("vault://multi/field")) is None
