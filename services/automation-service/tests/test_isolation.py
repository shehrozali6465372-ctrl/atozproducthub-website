"""Tenancy isolation tests: 10 niches never leak across rule/run/job/queue data.

Enforces Database Blueprint §4: every scoped business record carries
``niche_id``; all queries and mutations are niche-scoped server-side; the
global scope (``niche_id IS NULL``) is a distinct compartment.
"""

from .fixtures import build_service, scenario

NICHE_COUNT = 10


async def _make_service():
    _, service, _, captured = await build_service()
    return service, captured


async def _seed_ten_niches(service):
    """Create 10 real local niche mirrors; returns (niche_id, slug) list."""
    niches = []
    for i in range(NICHE_COUNT):
        slug = f"niche-{i:02d}"
        niche = await service.create_niche(name=f"Niche {i}", slug=slug, status="active")
        niches.append((niche.id, slug))
    return niches


async def _seed_business_data(service, niche_id):
    """Create one of each automation object for a niche; returns ids."""
    rule = await service.create_rule(
        niche_id=niche_id, code="isolation-rule", trigger_type="manual"
    )
    rule = await service.enable_rule(rule.id, niche_id)
    run, _ = await service.trigger_rule(
        rule_id=rule.id, niche_id=niche_id, idempotency_key=f"key-{niche_id}"
    )
    job = await service.create_scheduled_job(
        niche_id=niche_id,
        job_key="isolation-job",
        cron_expr="0 * * * *",
        queue="default",
        handler="handlers.isolation",
    )
    job_run, queue_item = await service.enqueue_job(job.id, niche_id)
    aios = await service.create_aios_job(
        niche_id=niche_id, job_id=f"aios-{niche_id}", contract="AIOS.Content.Intake"
    )
    return {
        "rule": rule.id,
        "run": run.id,
        "job": job.id,
        "job_run": job_run.id,
        "queue_item": queue_item.id,
        "aios": aios[0].id,
    }


def test_ten_niche_full_isolation() -> None:
    async def run():
        service, _ = await _make_service()
        niches = await _seed_ten_niches(service)
        records = {}
        for niche_id, _slug in niches:
            records[niche_id] = await _seed_business_data(service, niche_id)

        for niche_id, _slug in niches:
            expected = records[niche_id]
            # Rules: only this niche's rule is visible.
            rules = await service.list_rules(niche_id)
            assert [r.id for r in rules] == [expected["rule"]]
            # Runs: only this niche's run.
            runs = await service.list_runs(niche_id)
            assert [r.id for r in runs] == [expected["run"]]
            # Scheduled jobs + job runs.
            jobs = await service.list_scheduled_jobs(niche_id)
            assert [j.id for j in jobs] == [expected["job"]]
            job_runs = await service.list_job_runs(niche_id)
            assert [j.id for j in job_runs] == [expected["job_run"]]
            # Queue items.
            items = await service.list_queue(niche_id)
            assert [i.id for i in items] == [expected["queue_item"]]
            # AI OS job records.
            aios = await service.list_aios_jobs(niche_id)
            assert [a.id for a in aios] == [expected["aios"]]

        # Global scope sees none of the niche data (and vice versa).
        assert await service.list_rules(None) == []
        assert await service.list_runs(None) == []
        assert await service.list_queue(None) == []
        assert await service.list_scheduled_jobs(None) == []

    scenario(run)


def test_no_cross_niche_mutation() -> None:
    async def run():
        service, _ = await _make_service()
        niches = await _seed_ten_niches(service)
        records = {}
        for niche_id, _slug in niches:
            records[niche_id] = await _seed_business_data(service, niche_id)

        from atoz_automation_service.errors import NotFoundError

        # Every other niche must be unable to mutate niche-0's objects.
        target = niches[0][0]
        for niche_id, _slug in niches[1:]:
            try:
                await service.trigger_rule(rule_id=records[target]["rule"], niche_id=niche_id)
                raise AssertionError("cross-niche rule trigger leaked")
            except NotFoundError:
                pass
            try:
                await service.complete_run(records[target]["run"], niche_id)
                raise AssertionError("cross-niche run mutation leaked")
            except NotFoundError:
                pass
            try:
                await service.claim_queue_item(records[target]["queue_item"], niche_id)
                raise AssertionError("cross-niche queue claim leaked")
            except NotFoundError:
                pass
            try:
                await service.set_aios_job_status(
                    niche_id=niche_id,
                    job_id=f"aios-{target}",
                    contract="AIOS.Content.Intake",
                    status="in_progress",
                )
                raise AssertionError("cross-niche aios mutation leaked")
            except NotFoundError:
                pass
        # The owning niche can still mutate.
        await service.complete_run(records[target]["run"], target)
        assert (await service.list_runs(target))[0].status == "success"

    scenario(run)


def test_global_and_niche_compartments_are_separate() -> None:
    async def run():
        service, _ = await _make_service()
        niche_id = await service.create_niche(name="G", slug="g", status="active")
        # A global rule is invisible in niche scope.
        global_rule = await service.create_rule(
            niche_id=None, code="global-rule", trigger_type="manual"
        )
        assert await service.get_rule(global_rule.id, niche_id.id) is None
        assert await service.get_rule(global_rule.id, None) is not None
        # A niche rule is invisible in global scope.
        niche_rule = await service.create_rule(
            niche_id=niche_id.id, code="niche-rule", trigger_type="manual"
        )
        assert await service.get_rule(niche_rule.id, None) is None
        assert await service.get_rule(niche_rule.id, niche_id.id) is not None

    scenario(run)
