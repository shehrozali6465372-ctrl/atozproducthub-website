"""Repository tests: niche scoping, append-only ledger, rollup upserts."""

from atoz_analytics_service.errors import ValidationError

from .fixtures import build_service, scenario, utc_dt


def test_ledger_is_append_only() -> None:
    async def runner() -> None:
        session_factory, service, _backbone, _warehouse = await build_service()
        await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": "ledger-001",
                "event_type": "page_view",
                "session_id": "s1",
                "page_url": "/articles/a",
                "occurred_at": utc_dt(2026, 8, 1, 12),
            },
        )
        async with session_factory() as session:
            from atoz_analytics_service.repositories import AnalyticsEventLedgerRepository

            repo = AnalyticsEventLedgerRepository(session)
            row = await repo.get_by_event_id("ledger-001")
            assert row is not None
            assert await repo.event_exists("ledger-001") is True
            try:
                await repo.update(row)
                raise AssertionError("expected append-only guard")
            except ValidationError:
                pass
            try:
                await repo.delete(row.id)
                raise AssertionError("expected append-only guard")
            except ValidationError:
                pass
            assert await repo.get_by_event_id("ledger-001") is not None

    scenario(runner)


def test_traffic_upsert_keeps_one_row_per_source_day() -> None:
    async def runner() -> None:
        session_factory, service, _backbone, _warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        day = utc_dt(2026, 8, 1, 12)
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": "traffic-001",
                "event_type": "page_view",
                "session_id": "s1",
                "page_url": "/a",
                "occurred_at": day,
            },
        )
        await service.run_rollups(niche_id=niche.id, from_date=day.date(), to_date=day.date())
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": "traffic-002",
                "event_type": "page_view",
                "session_id": "s2",
                "page_url": "/b",
                "referrer": "https://www.pinterest.com",
                "occurred_at": day,
            },
        )
        await service.run_rollups(niche_id=niche.id, from_date=day.date(), to_date=day.date())
        async with session_factory() as session:
            from atoz_analytics_service.repositories import TrafficDailyRepository

            repo = TrafficDailyRepository(session)
            rows = await repo.list_range(niche.id, start=day.date(), end=day.date())
            assert len(rows) == 2  # direct + pinterest, never duplicated
            direct = next(row for row in rows if row.source == "direct")
            assert direct.sessions == 1 and direct.pageviews == 1

    scenario(runner)
