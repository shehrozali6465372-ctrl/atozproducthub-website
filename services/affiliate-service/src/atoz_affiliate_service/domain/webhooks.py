"""Inbound webhook verification (API Contracts §10).

Networks deliver ``network.conversion`` events with the common envelope
``{event_id, type, version, source, occurred_at, nonce, payload}`` and an
``X-Webhook-Signature`` header. The signature is the HMAC-SHA256 of the
**raw request body** using the per-network secret (settings dev default;
production via Vault under the network's ``webhook_secret_ref``).

Idempotency is enforced twice: the receiver logs every delivery by
``(source, event_id)`` and the revenue ledger has
``UNIQUE (network_id, network_transaction_id)`` — repeated deliveries never
create duplicate commission records.
"""

import hashlib
import hmac
import json
from datetime import UTC, datetime


def verify_signature(*, raw_body: bytes, signature: str, secret: str) -> bool:
    """Constant-time check of ``X-Webhook-Signature`` against the raw body."""
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


class WebhookPayloadError(ValueError):
    """Malformed or schema-invalid webhook envelope."""


REQUIRED_ENVELOPE_FIELDS = ("event_id", "type", "version", "source", "occurred_at", "payload")

CONVERSION_PAYLOAD_FIELDS = ("transaction_id", "status", "amount_cents", "currency")


def parse_envelope(body: bytes) -> dict:
    """Parse + validate the common webhook envelope (fast-ack path)."""
    try:
        envelope = json.loads(body)
    except json.JSONDecodeError as exc:
        raise WebhookPayloadError("Webhook body is not valid JSON.") from exc
    if not isinstance(envelope, dict):
        raise WebhookPayloadError("Webhook envelope must be a JSON object.")
    missing = [field for field in REQUIRED_ENVELOPE_FIELDS if field not in envelope]
    if missing:
        raise WebhookPayloadError(f"Missing envelope fields: {', '.join(missing)}.")
    if not isinstance(envelope["payload"], dict):
        raise WebhookPayloadError("Webhook payload must be a JSON object.")
    return envelope


def parse_conversion_payload(payload: dict) -> dict:
    """Validate the ``network.conversion`` payload highlights."""
    missing = [field for field in CONVERSION_PAYLOAD_FIELDS if field not in payload]
    if missing:
        raise WebhookPayloadError(f"Missing conversion fields: {', '.join(missing)}.")
    try:
        amount_cents = int(payload["amount_cents"])
    except (TypeError, ValueError) as exc:
        raise WebhookPayloadError("amount_cents must be an integer.") from exc
    if amount_cents < 0:
        raise WebhookPayloadError("amount_cents must be non-negative.")
    try:
        gross_cents = int(payload.get("gross_cents", amount_cents))
    except (TypeError, ValueError) as exc:
        raise WebhookPayloadError("gross_cents must be an integer.") from exc
    if gross_cents < 0:
        raise WebhookPayloadError("gross_cents must be non-negative.")
    status = str(payload.get("status", "pending"))
    currency = str(payload.get("currency", "USD"))
    if len(currency) != 3 or not currency.isalpha():
        raise WebhookPayloadError("currency must be a 3-letter ISO code.")
    return {
        "transaction_id": str(payload["transaction_id"]),
        "status": status,
        "amount_cents": amount_cents,
        "gross_cents": gross_cents,
        "currency": currency.upper(),
        "click_token": str(payload["click_token"]) if payload.get("click_token") else None,
        "occurred_at": _parse_occurred_at(payload.get("occurred_at")),
    }


def _parse_occurred_at(value) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise WebhookPayloadError("occurred_at must be an ISO-8601 timestamp.") from exc
