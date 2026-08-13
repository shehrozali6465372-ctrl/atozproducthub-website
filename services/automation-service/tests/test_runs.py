"""Automation run history tests: idempotent triggers, transitions, append-only."""

from atoz_automation_service.errors import NotFoundError, ValidationError

from .fixtures import build_service, scenario


async def _make_service():
    _, service, _, captured = await build_service()
    return service, captured


async def _enabled_rule(service, *, niche_id=None, code="run-rule"):
    rule = await service.create_rule(niche_id=niche_id, code=code, trigger_type="manual")
    return await service.enable_rule(rule.id, niche_id)


def test_trigger_creates_running_run_and_event() -> None:
    async def run():
        service, captured = await _make_service()
        rule = await _enabled_rule(service)
        run, created = await service.trigger_rule(
            rule_id=rule.id, niche_id=None, triggered_by="admin-1"
        )
        assert created is True
        assert run.status == "running"
        assert run.automation_rule_id == rule.id
        assert run.triggered_by == "admin-1"
        assert any(e.type == "automation:run-started.v1" for e in captured)

    scenario(run)


def test_trigger_rejects_disabled_rule() -> None:
    async def run():
        service, _ = await _make_service()
        rule = await service.create_rule(niche_id=None, code="off", trigger_type="manual")
        try:
            await service.trigger_rule(rule_id=rule.id, niche_id=None)
            raise AssertionError("expected ValidationError")
        except ValidationError:
            pass

    scenario(run)


def test_trigger_idempotent_with_same_key() -> None:
    async def run():
        service, _ = await _make_service()
        rule = await _enabled_rule(service)
        first, created_first = await service.trigger_rule(
            rule_id=rule.id, niche_id=None, idempotency_key="req-abc-123"
        )
        second, created_second = await service.trigger_rule(
            rule_id=rule.id, niche_id=None, idempotency_key="req-abc-123"
        )
        third, created_third = await service.trigger_rule(
            rule_id=rule.id, niche_id=None, idempotency_key="req-abc-456"
        )
        assert created_first is True
        assert created_second is False
        assert second.id == first.id
        assert created_third is True
        assert third.id != first.id
        runs = await service.list_runs(None)
        assert len(runs) == 2

    scenario(run)


def test_run_complete_and_fail_transitions() -> None:
    async def run():
        service, captured = await _make_service()
        rule = await _enabled_rule(service)
        run, _ = await service.trigger_rule(rule_id=rule.id, niche_id=None)
        done = await service.complete_run(run.id, None, summary="ok")
        assert done.status == "success"
        assert done.finished_at is not None
        assert any(e.type == "automation:run-succeeded.v1" for e in captured)
        try:
            await service.complete_run(run.id, None)
            raise AssertionError("expected ValidationError on double complete")
        except ValidationError:
            pass
        run2, _ = await service.trigger_rule(rule_id=rule.id, niche_id=None)
        failed = await service.fail_run(run2.id, None, error="boom")
        assert failed.status == "failed"
        assert failed.error == "boom"
        assert any(e.type == "automation:run-failed.v1" for e in captured)

    scenario(run)


def test_run_history_is_append_only() -> None:
    async def run():
        service, _ = await _make_service()
        rule = await _enabled_rule(service)
        for i in range(3):
            await service.trigger_rule(rule_id=rule.id, niche_id=None, idempotency_key=f"k-{i}")
        runs = await service.list_runs(None)
        assert len(runs) == 3
        assert await service.run_count_by_status(None, "running") == 3
        assert await service.run_count_by_status(None, "success") == 0

    scenario(run)


def test_run_cross_niche_trigger_blocked() -> None:
    async def run():
        service, _ = await _make_service()
        niche_a = await service.create_niche(name="A", slug="a", status="active")
        niche_b = await service.create_niche(name="B", slug="b", status="active")
        rule = await _enabled_rule(service, niche_id=niche_a.id)
        try:
            await service.trigger_rule(rule_id=rule.id, niche_id=niche_b.id)
            raise AssertionError("expected NotFoundError")
        except NotFoundError:
            pass
        # Correct scope works.
        run, created = await service.trigger_rule(rule_id=rule.id, niche_id=niche_a.id)
        assert created is True and run.niche_id == niche_a.id

    scenario(run)
