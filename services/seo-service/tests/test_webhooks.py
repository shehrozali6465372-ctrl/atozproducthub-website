"""Event ingestion tests: HMAC signature verification + idempotent indexing."""

from atoz_content_service.domain.events import content_published_event

from .fixtures import api_client, build_app, build_service, event_signature, make_settings, scenario


def test_webhook_rejects_invalid_signature() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        service = app.state.seo_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        event = content_published_event(
            article_id="art-1", niche_id=niche.id, url="/articles/a", checksum="1"
        )
        payload = {
            "type": event.type,
            "event_id": event.event_id,
            "aggregate_id": event.aggregate_id,
            "payload": event.payload,
        }
        async with await api_client(app) as client:
            response = await client.post(
                "/webhooks/v1/events",
                json=payload,
                headers={"X-Event-Signature": "deadbeef"},
            )
            assert response.status_code == 401
            # Missing header is also rejected.
            response = await client.post("/webhooks/v1/events", json=payload)
            assert response.status_code == 401

    scenario(runner)


def test_webhook_indexes_and_is_idempotent() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        service = app.state.seo_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        event = content_published_event(
            article_id="art-1", niche_id=niche.id, url="/articles/a", checksum="1"
        )
        payload = {
            "type": event.type,
            "event_id": event.event_id,
            "aggregate_id": event.aggregate_id,
            "payload": event.payload,
        }
        signature = event_signature(make_settings().event_webhook_secret, payload)
        async with await api_client(app) as client:
            for _ in range(2):  # repeated delivery must not create duplicates
                response = await client.post(
                    "/webhooks/v1/events",
                    json=payload,
                    headers={"X-Event-Signature": signature},
                )
                assert response.status_code == 202
        page = await service.search(query="untitled", niche_id=niche.id)
        assert page.total == 1

    scenario(runner)


def test_unsupported_event_rejected() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        payload = {
            "type": "unknown:event.v1",
            "event_id": "e1",
            "aggregate_id": "a",
            "payload": {"niche_id": niche.id},
        }
        signature = event_signature(make_settings().event_webhook_secret, payload)
        app, _engine, _bus, _captured = await build_app()
        async with await api_client(app) as client:
            response = await client.post(
                "/webhooks/v1/events", json=payload, headers={"X-Event-Signature": signature}
            )
            assert response.status_code == 422

    scenario(runner)
