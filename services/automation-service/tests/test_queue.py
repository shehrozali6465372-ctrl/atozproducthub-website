"""Durable queue ledger tests: idempotent enqueue, claim/complete/fail, retries."""

from datetime import UTC, datetime

from atoz_automation_service.errors import NotFoundError, ValidationError

from .fixtures import build_service, scenario


def _now() -> datetime:
    return datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


async def _make_service():
    _, service, _, captured = await build_service()
    return service, captured


def test_enqueue_is_idempotent_for_open_item() -> None:
    async def run():
        service, _ = await _make_service()
        first, created_first = await service.enqueue(
            niche_id=None, queue="pins", payload_ref="pin:abc", run_at=_now()
        )
        second, created_second = await service.enqueue(
            niche_id=None, queue="pins", payload_ref="pin:abc", run_at=_now()
        )
        third, created_third = await service.enqueue(
            niche_id=None, queue="pins", payload_ref="pin:def", run_at=_now()
        )
        assert created_first is True
        assert created_second is False
        assert second.id == first.id
        assert created_third is True
        items = await service.list_queue(None)
        assert len(items) == 2

    scenario(run)


def test_claim_complete_flow() -> None:
    async def run():
        service, _ = await _make_service()
        item, _ = await service.enqueue(niche_id=None, queue="jobs", payload_ref="job:1")
        assert item.state == "queued" and item.attempts == 0
        claimed = await service.claim_queue_item(item.id, None)
        assert claimed.state == "claimed" and claimed.attempts == 1
        try:
            await service.claim_queue_item(item.id, None)
            raise AssertionError("expected ValidationError on double claim")
        except ValidationError:
            pass
        done = await service.complete_queue_item(item.id, None)
        assert done.state == "done"
        assert done.completed_at is not None
        try:
            await service.complete_queue_item(item.id, None)
            raise AssertionError("expected ValidationError on completing done item")
        except ValidationError:
            pass

    scenario(run)


def test_fail_without_retry_marks_failed() -> None:
    async def run():
        service, _ = await _make_service()
        item, _ = await service.enqueue(niche_id=None, queue="jobs", payload_ref="job:fail")
        await service.claim_queue_item(item.id, None)
        failed = await service.fail_queue_item(item.id, None, error="nope", retry=False)
        assert failed.state == "failed"
        assert failed.error == "nope"
        assert failed.completed_at is not None

    scenario(run)


def test_fail_with_retry_requeues_with_backoff() -> None:
    async def run():
        service, _ = await _make_service()
        item, _ = await service.enqueue(niche_id=None, queue="jobs", payload_ref="job:retry")
        await service.claim_queue_item(item.id, None)  # attempts -> 1
        requeued = await service.fail_queue_item(item.id, None, error="retry me", retry=True)
        assert requeued.state == "queued"
        assert requeued.run_at > _now()  # backoff pushes the run_at forward
        assert requeued.attempts == 1
        # It can be claimed again.
        claimed = await service.claim_queue_item(item.id, None)
        assert claimed.attempts == 2

    scenario(run)


def test_fail_retry_until_max_attempts() -> None:
    async def run():
        service, _ = await _make_service()
        item, _ = await service.enqueue(
            niche_id=None, queue="jobs", payload_ref="job:exhaust", max_attempts=3
        )
        for _ in range(2):
            await service.claim_queue_item(item.id, None)
            await service.fail_queue_item(item.id, None, error="again", retry=True)
        await service.claim_queue_item(item.id, None)  # attempts -> 3
        final = await service.fail_queue_item(item.id, None, error="exhausted", retry=True)
        assert final.state == "failed"
        assert final.error == "exhausted"
        assert final.attempts == 3
        assert final.completed_at is not None

    scenario(run)


def test_queue_operations_are_niche_scoped() -> None:
    async def run():
        service, _ = await _make_service()
        niche_a = await service.create_niche(name="A", slug="qa", status="active")
        niche_b = await service.create_niche(name="B", slug="qb", status="active")
        item_a, _ = await service.enqueue(niche_id=niche_a.id, queue="jobs", payload_ref="a:1")
        item_b, _ = await service.enqueue(niche_id=niche_b.id, queue="jobs", payload_ref="b:1")
        a_items = await service.list_queue(niche_a.id)
        b_items = await service.list_queue(niche_b.id)
        assert [i.id for i in a_items] == [item_a.id]
        assert [i.id for i in b_items] == [item_b.id]
        assert await service.list_queue(None) == []
        try:
            await service.claim_queue_item(item_a.id, niche_b.id)
            raise AssertionError("expected NotFoundError cross-niche")
        except NotFoundError:
            pass

    scenario(run)


def test_enqueue_rejects_invalid_payload() -> None:
    async def run():
        service, _ = await _make_service()
        try:
            await service.enqueue(niche_id=None, queue="", payload_ref="x")
            raise AssertionError("expected ValidationError")
        except ValidationError:
            pass

    scenario(run)
