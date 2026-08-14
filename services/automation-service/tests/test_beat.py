"""Beat scheduler tests (M10 Step 2): croniter, DB-driven tick, lock."""

from datetime import UTC, datetime

from atoz_automation_service.beat import BeatLock, next_cron_run, run_beat_tick

from .fixtures import build_service, make_settings, scenario


def test_next_cron_run_computes_next_utc() -> None:
    base = datetime(2026, 8, 13, 5, 59, 0, tzinfo=UTC)
    nxt = next_cron_run("0 6 * * *", base=base)
    assert nxt == datetime(2026, 8, 13, 6, 0, 0, tzinfo=UTC)


def test_next_cron_run_invalid_expression_returns_none() -> None:
    assert next_cron_run("not a cron") is None


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def test_beat_tick_enqueues_due_jobs_and_advances_next_run() -> None:
    async def run() -> None:
        session_factory, service, _, _ = await build_service()
        niche = await service.create_niche(name="A", slug="beat-a", status="active")
        job = await service.create_scheduled_job(
            niche_id=niche.id,
            job_key="beat-due",
            cron_expr="0 6 * * *",
            queue="seo",
            handler="seo.sitemap_rebuild",
            next_run_at=datetime(2026, 8, 13, 5, 0, 0, tzinfo=UTC),
        )
        settings = make_settings(celery_broker_url="memory://local")  # no Redis lock
        summary = await run_beat_tick(
            service, settings, now=datetime(2026, 8, 13, 6, 0, 0, tzinfo=UTC)
        )
        assert summary["status"] == "ok"
        assert summary["enqueued"] == 1
        assert summary["jobs"][0]["job_id"] == job.id

        jobs = await service.list_scheduled_jobs(niche.id)
        assert _aware(jobs[0].next_run_at) == datetime(2026, 8, 14, 6, 0, 0, tzinfo=UTC)
        runs = await service.list_job_runs(niche.id)
        assert len(runs) == 1
        items = await service.list_queue(niche.id)
        assert items[0].payload_ref == f"job_run:{runs[0].id}"

    scenario(run)


def test_beat_tick_skips_future_and_disabled_jobs() -> None:
    async def run() -> None:
        _, service, _, _ = await build_service()
        niche = await service.create_niche(name="A", slug="beat-b", status="active")
        await service.create_scheduled_job(
            niche_id=niche.id,
            job_key="future",
            cron_expr="0 6 * * *",
            queue="seo",
            handler="seo.sitemap_rebuild",
            next_run_at=datetime(2026, 8, 14, 6, 0, 0, tzinfo=UTC),  # not due
        )
        disabled = await service.create_scheduled_job(
            niche_id=niche.id,
            job_key="disabled",
            cron_expr="0 6 * * *",
            queue="seo",
            handler="seo.sitemap_rebuild",
            next_run_at=datetime(2026, 8, 13, 5, 0, 0, tzinfo=UTC),
        )
        await service.set_scheduled_job_status(disabled.id, niche.id, enabled=False)
        settings = make_settings(celery_broker_url="memory://local")
        summary = await run_beat_tick(
            service, settings, now=datetime(2026, 8, 13, 6, 0, 0, tzinfo=UTC)
        )
        assert summary["enqueued"] == 0

    scenario(run)


def test_beat_tick_global_scope_scans_all_niches() -> None:
    async def run() -> None:
        _, service, _, _ = await build_service()
        for slug in ("beat-c1", "beat-c2"):
            niche = await service.create_niche(name=slug, slug=slug, status="active")
            await service.create_scheduled_job(
                niche_id=niche.id,
                job_key=f"due-{slug}",
                cron_expr="0 6 * * *",
                queue="seo",
                handler="seo.sitemap_rebuild",
                next_run_at=datetime(2026, 8, 13, 5, 0, 0, tzinfo=UTC),
            )
        settings = make_settings(celery_broker_url="memory://local")
        summary = await run_beat_tick(
            service, settings, now=datetime(2026, 8, 13, 6, 0, 0, tzinfo=UTC)
        )
        assert summary["enqueued"] == 2

    scenario(run)


def test_beat_lock_noop_without_redis() -> None:
    async def run() -> None:
        lock = BeatLock(make_settings(celery_broker_url="memory://local"))
        assert await lock.acquire() is True
        await lock.release()

    scenario(run)


def test_beat_lock_redis_unavailable_is_best_effort() -> None:
    async def run() -> None:
        settings = make_settings(celery_broker_url="redis://127.0.0.1:1/0")
        lock = BeatLock(settings)
        acquired = await lock.acquire()
        assert acquired is False  # unreachable Redis → tick skipped safely
        await lock.release()

    scenario(run)
