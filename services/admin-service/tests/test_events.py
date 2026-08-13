"""Internal event ingestion tests (API Contracts §8, Task 19 §5).

Signatures are HMAC-SHA256 over the raw request bytes; replays are
idempotent on (source, event_id); invalid signatures are rejected before
any state change.
"""

from .fixtures import (
    TEST_EVENT_SECRET,
    api_client,
    build_app,
    event_signature,
    scenario,
)

SOURCE = "content-service"


def _payload(event_id: str = "evt-0001", event_type: str = "content:published.v1") -> dict:
    return {
        "type": event_type,
        "event_id": event_id,
        "payload": {"niche_id": "n-1", "article_id": "a-1"},
        "aggregate_id": "a-1",
    }


def _signed_headers(source: str, signature: str) -> dict[str, str]:
    return {"X-Event-Source": source, "X-Event-Signature": signature}


def test_valid_event_is_ingested_and_recorded() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            payload = _payload()
            signature = event_signature(TEST_EVENT_SECRET, payload)
            response = await client.post(
                "/api/v1/admin/events/ingest",
                headers=_signed_headers(SOURCE, signature),
                json=payload,
            )
            assert response.status_code == 202
            body = response.json()
            assert body["status"] == "processed"
            assert body["event_id"] == "evt-0001"

            # The operation log recorded the domain event.
            logs = await client.get(
                "/api/v1/admin/logs/operations", headers=_signed_headers(SOURCE, signature)
            )
            # Operation logs require admin RBAC; use the service instead.
            records = await app.state.admin_service.list_operation_logs()
            assert any(r.operation == "content.publish" for r in records)
            assert logs.status_code == 401  # no bearer token -> rejected

    scenario(run)


def test_invalid_signature_is_rejected() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            payload = _payload()
            response = await client.post(
                "/api/v1/admin/events/ingest",
                headers=_signed_headers(SOURCE, "bad" * 16),
                json=payload,
            )
            assert response.status_code == 401
            assert response.json()["code"] == "UNAUTHENTICATED"

            records = await app.state.admin_service.list_webhook_logs()
            assert records == []

    scenario(run)


def test_replayed_event_is_idempotent() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            payload = _payload()
            signature = event_signature(TEST_EVENT_SECRET, payload)
            first = await client.post(
                "/api/v1/admin/events/ingest",
                headers=_signed_headers(SOURCE, signature),
                json=payload,
            )
            second = await client.post(
                "/api/v1/admin/events/ingest",
                headers=_signed_headers(SOURCE, signature),
                json=payload,
            )
            assert first.status_code == 202
            assert second.status_code == 202
            assert first.json()["id"] == second.json()["id"]

            records = await app.state.admin_service.list_webhook_logs()
            assert len(records) == 1

    scenario(run)


def test_missing_headers_and_bad_payloads_fail_validation() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            payload = _payload()
            missing_source = await client.post(
                "/api/v1/admin/events/ingest",
                headers={"X-Event-Signature": "x" * 64},
                json=payload,
            )
            assert missing_source.status_code == 422

            missing_signature = await client.post(
                "/api/v1/admin/events/ingest",
                headers={"X-Event-Source": SOURCE},
                json=payload,
            )
            assert missing_signature.status_code == 422

            incomplete = await client.post(
                "/api/v1/admin/events/ingest",
                headers=_signed_headers(SOURCE, event_signature(TEST_EVENT_SECRET, {"foo": "bar"})),
                json={"foo": "bar"},
            )
            assert incomplete.status_code == 422

    scenario(run)


def test_payload_size_limit_is_enforced() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            payload = _payload(event_id="big-evt")
            payload["payload"] = {"blob": "x" * 200_000}
            signature = event_signature(TEST_EVENT_SECRET, payload)
            response = await client.post(
                "/api/v1/admin/events/ingest",
                headers=_signed_headers(SOURCE, signature),
                json=payload,
            )
            assert response.status_code == 422

    scenario(run)
