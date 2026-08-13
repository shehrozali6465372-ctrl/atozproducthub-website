"""Automation rule lifecycle tests (state machine + tenancy + events)."""

from atoz_automation_service.errors import DuplicateError, NotFoundError, ValidationError
from atoz_automation_service.services import AutomationService
from atoz_automation_service.uuids import uuid7

from .fixtures import build_service, scenario


async def _seed_niche(service: AutomationService, slug: str, name: str) -> str:
    niche = await service.create_niche(name=name, slug=slug, status="active")
    return niche.id


async def _make_service():
    _, service, _, captured = await build_service()
    return service, captured


def test_create_rule_defaults_to_disabled() -> None:
    async def run():
        service, _ = await _make_service()
        rule = await service.create_rule(
            niche_id=None, code="daily-report", trigger_type="schedule"
        )
        assert rule.status == "disabled"
        assert rule.niche_id is None
        assert rule.trigger_type == "schedule"

    scenario(run)


def test_create_rule_rejects_duplicate_code() -> None:
    async def run():
        service, _ = await _make_service()
        await service.create_rule(niche_id=None, code="pin-replenish", trigger_type="event")
        try:
            await service.create_rule(niche_id=None, code="pin-replenish", trigger_type="manual")
            raise AssertionError("expected DuplicateError")
        except DuplicateError:
            pass

    scenario(run)


def test_same_code_allowed_across_niches_and_global() -> None:
    async def run():
        service, _ = await _make_service()
        niche_a = await _seed_niche(service, "niche-a", "Niche A")
        niche_b = await _seed_niche(service, "niche-b", "Niche B")
        await service.create_rule(niche_id=None, code="report", trigger_type="schedule")
        await service.create_rule(niche_id=niche_a, code="report", trigger_type="schedule")
        await service.create_rule(niche_id=niche_b, code="report", trigger_type="schedule")
        global_rules = await service.list_rules(None)
        a_rules = await service.list_rules(niche_a)
        assert len(global_rules) == 1 and global_rules[0].niche_id is None
        assert len(a_rules) == 1 and a_rules[0].niche_id == niche_a

    scenario(run)


def test_rule_state_machine_transitions() -> None:
    async def run():
        service, _ = await _make_service()
        rule = await service.create_rule(niche_id=None, code="nightly", trigger_type="schedule")
        enabled = await service.enable_rule(rule.id, None)
        assert enabled.status == "enabled"
        try:
            await service.enable_rule(rule.id, None)
            raise AssertionError("expected ValidationError on enabled->enabled")
        except ValidationError:
            pass
        disabled = await service.disable_rule(rule.id, None)
        assert disabled.status == "disabled"
        try:
            await service.disable_rule(rule.id, None)
            raise AssertionError("expected ValidationError on disabled->disabled")
        except ValidationError:
            pass

    scenario(run)


def test_rule_events_published() -> None:
    async def run():
        service, captured = await _make_service()
        rule = await service.create_rule(niche_id=None, code="event-rule", trigger_type="event")
        await service.enable_rule(rule.id, None)
        await service.disable_rule(rule.id, None)
        types = [e.type for e in captured]
        assert "automation:rule-enabled.v1" in types
        assert "automation:rule-disabled.v1" in types

    scenario(run)


def test_rule_requires_valid_trigger_type() -> None:
    async def run():
        service, _ = await _make_service()
        try:
            await service.create_rule(niche_id=None, code="bad", trigger_type="ai")
            raise AssertionError("expected ValidationError")
        except ValidationError:
            pass

    scenario(run)


def test_rule_unregistered_niche_rejected() -> None:
    async def run():
        service, _ = await _make_service()
        try:
            await service.create_rule(niche_id=uuid7(), code="x", trigger_type="manual")
            raise AssertionError("expected ValidationError")
        except ValidationError:
            pass

    scenario(run)


def test_rule_not_found_across_scopes() -> None:
    async def run():
        service, _ = await _make_service()
        niche_a = await _seed_niche(service, "scope-a", "Scope A")
        rule = await service.create_rule(niche_id=niche_a, code="scoped", trigger_type="manual")
        # Same niche resolves.
        assert await service.get_rule(rule.id, niche_a) is not None
        # Different niche must NOT resolve (no leakage).
        assert await service.get_rule(rule.id, None) is None
        try:
            await service.enable_rule(rule.id, None)
            raise AssertionError("expected NotFoundError")
        except NotFoundError:
            pass

    scenario(run)
