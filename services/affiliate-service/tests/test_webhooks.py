"""Webhook envelope/signature validation tests (API Contracts §10)."""

import hashlib
import hmac
import json
from datetime import UTC, datetime

import pytest

from atoz_affiliate_service.domain.webhooks import (
    WebhookPayloadError,
    parse_conversion_payload,
    parse_envelope,
    verify_signature,
)

SECRET = "test-webhook-secret"


def _signed_body(payload: dict | None = None, **overrides) -> bytes:
    body = {
        "event_id": "evt-001",
        "type": "network.conversion",
        "version": "v1",
        "source": "amazon",
        "occurred_at": datetime.now(UTC).isoformat(),
        "nonce": "nonce-1",
        "payload": payload
        or {
            "transaction_id": "tx-1",
            "status": "approved",
            "amount_cents": 2500,
            "gross_cents": 50000,
            "currency": "USD",
            "click_token": "raw-token",
            "occurred_at": datetime.now(UTC).isoformat(),
        },
    }
    body.update(overrides)
    return json.dumps(body).encode()


def _signature(raw: bytes) -> str:
    return hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()


def test_verify_signature_accepts_valid() -> None:
    raw = _signed_body()
    assert verify_signature(raw_body=raw, signature=_signature(raw), secret=SECRET)


def test_verify_signature_rejects_invalid() -> None:
    raw = _signed_body()
    assert not verify_signature(raw_body=raw, signature="deadbeef", secret=SECRET)


def test_verify_signature_rejects_wrong_secret() -> None:
    raw = _signed_body()
    sig = hmac.new(b"other", raw, hashlib.sha256).hexdigest()
    assert not verify_signature(raw_body=raw, signature=sig, secret=SECRET)


def test_verify_signature_rejects_body_tampering() -> None:
    raw = _signed_body()
    signature = _signature(raw)
    tampered = raw.replace(b"tx-1", b"tx-2")
    assert not verify_signature(raw_body=tampered, signature=signature, secret=SECRET)


def test_parse_envelope_requires_fields() -> None:
    raw = _signed_body(event_id="evt-2")
    envelope = parse_envelope(raw)
    assert envelope["event_id"] == "evt-2"


def test_parse_envelope_rejects_missing_fields() -> None:
    body = json.dumps({"event_id": "x"}).encode()
    with pytest.raises(WebhookPayloadError):
        parse_envelope(body)


def test_parse_envelope_rejects_non_json() -> None:
    with pytest.raises(WebhookPayloadError):
        parse_envelope(b"not json")


def test_parse_conversion_payload_valid() -> None:
    payload = parse_conversion_payload(
        {
            "transaction_id": "tx-1",
            "status": "pending",
            "amount_cents": "1000",
            "currency": "eur",
            "click_token": "raw-token",
        }
    )
    assert payload["amount_cents"] == 1000
    assert payload["currency"] == "EUR"
    assert payload["click_token"] == "raw-token"


def test_parse_conversion_payload_rejects_bad_amount() -> None:
    with pytest.raises(WebhookPayloadError):
        parse_conversion_payload({"transaction_id": "x", "amount_cents": "NaN", "currency": "USD"})
    with pytest.raises(WebhookPayloadError):
        parse_conversion_payload({"transaction_id": "x", "amount_cents": -1, "currency": "USD"})


def test_parse_conversion_payload_rejects_bad_currency() -> None:
    with pytest.raises(WebhookPayloadError):
        parse_conversion_payload({"transaction_id": "x", "amount_cents": 10, "currency": "US"})
