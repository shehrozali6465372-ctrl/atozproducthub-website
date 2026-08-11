"""Service tests: ingestion, rollups, read models, and niche isolation."""

from datetime import datetime

from atoz_backend_core.events.envelope import EventEnvelope

from .fixtures import build_service, scenario, utc_dt


async def _seed_day(service, *, niche_id: str, day: datetime, count: int = 3) -> None:
    for index in range(count):
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": f"seed-{day.day}-{index}",
                "event_type": "page_view",
                "session_id": f"s{index}",
                "page_url": f"/articles/guide-{index}",
                "referrer": "https://pinterest.com" if index % 2 else None,
                "user_pseudo_id": f"u{index}",
                "traits": {"device": "mobile", "country": "US", "duration_sec": 30},
                "occurred_at": day,
            },
        )


def test_ingest_and_rollup_build_read_models() -> None:
    async def runner() -> None:
        _session_factory, service, backbone, warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        day = utc_dt(2026, 8, 1, 10)
        await _seed_day(service, niche_id=niche.id, day=day, count=4)
        assert len(backbone.published) == 0  # drained into the warehouse
        assert len(warehouse.rows) == 4

        results = await service.run_rollups(
            niche_id=niche.id, from_date=day.date(), to_date=day.date()
        )
        assert len(results) == 1
        assert results[0]["traffic_rows"] >= 1
        assert results[0]["metric_rows"] >= 1
        assert results[0]["snapshot_kinds"] == ["daily"]

        traffic = await service.traffic_series(niche.id, from_date=day.date(), to_date=day.date())
        total = sum(point["pageviews"] for point in traffic)
        assert total == 4
        sources = {point["source"] for point in traffic}
        assert "pinterest" in sources and "direct" in sources

        overview = await service.overview(niche.id, from_date=day.date(), to_date=day.date())
        assert overview["pageviews"] == 4
        assert overview["sessions"] == 4

        pages = await service.top_pages(niche.id, from_date=day.date(), to_date=day.date())
        assert sum(row["pageviews"] for row in pages) == 4

    scenario(runner)


def test_rollup_is_idempotent_and_weekly_snapshot_on_sunday() -> None:
    async def runner() -> None:
        _session_factory, service, _backbone, _warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        sunday = utc_dt(2026, 8, 2, 10)  # 2026-08-02 is a Sunday
        await _seed_day(service, niche_id=niche.id, day=sunday, count=2)
        await service.run_rollups(niche_id=niche.id, from_date=sunday.date(), to_date=sunday.date())
        second = await service.run_rollups(
            niche_id=niche.id, from_date=sunday.date(), to_date=sunday.date()
        )
        # Idempotent: the same number of rows after a second run.
        traffic = await service.traffic_series(
            niche.id, from_date=sunday.date(), to_date=sunday.date()
        )
        assert len(traffic) == 2  # pinterest + direct
        snapshots = await service.list_snapshots(niche.id)
        kinds = {snapshot["snapshot_kind"] for snapshot in snapshots}
        assert kinds == {"daily", "weekly"}
        assert second[0]["traffic_rows"] == len(traffic)

    scenario(runner)


def test_affiliate_pinterest_and_revenue_metrics() -> None:
    async def runner() -> None:
        _session_factory, service, _backbone, _warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = "11111111-1111-4111-8111-111111111111"
        day = utc_dt(2026, 8, 3, 10)
        for index, event_type in enumerate(
            ("pin_click", "pin_click", "affiliate_click", "conversion")
        ):
            await service.ingest_event(
                niche_slug="kitchen",
                event={
                    "event_id": f"metric-{index}",
                    "event_type": event_type,
                    "pinterest_account_id": account,
                    "session_id": "sess-m",
                    "traits": {"amount": 10.0} if event_type == "conversion" else {},
                    "occurred_at": day,
                },
            )
        await service.ingest_webhook_event(
            EventEnvelope(
                type="revenue:attributed.v1",
                event_id="evt-rev-01",
                payload={
                    "niche_id": niche.id,
                    "transaction_id": "tx-1",
                    "amount": 49.99,
                    "commission": 4.99,
                },
                occurred_at=day.timestamp(),
            )
        )
        await service.run_rollups(niche_id=niche.id, from_date=day.date(), to_date=day.date())
        metrics = await service.metrics(niche.id, from_date=day.date(), to_date=day.date())
        by_key = {(m["metric_key"], m["pinterest_account_id"]): m["value"] for m in metrics}
        assert by_key[("pinterest.pin_clicks", account)] == 2
        assert by_key[("affiliate.clicks", account)] == 1
        assert by_key[("affiliate.conversions", account)] == 1
        assert by_key[("revenue.amount", None)] == 49.99
        assert by_key[("revenue.commission", None)] == 4.99
        # Per-account isolation: querying with account A sees only A's metrics.
        account_metrics = await service.metrics(
            niche.id, from_date=day.date(), to_date=day.date(), account_id=account
        )
        assert all(m["pinterest_account_id"] == account for m in account_metrics)

    scenario(runner)


def test_niches_never_leak_into_each_other() -> None:
    async def runner() -> None:
        _session_factory, service, _backbone, _warehouse = await build_service()
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        day = utc_dt(2026, 8, 4, 10)
        for index in range(2):
            await service.ingest_event(
                niche_slug="kitchen",
                event={
                    "event_id": f"kitchen-{index}",
                    "event_type": "page_view",
                    "session_id": "s",
                    "page_url": "/articles/a",
                    "user_pseudo_id": "u",
                    "occurred_at": day,
                },
            )
        await service.ingest_event(
            niche_slug="travel",
            event={
                "event_id": "travel-1",
                "event_type": "page_view",
                "session_id": "s2",
                "page_url": "/articles/travel",
                "user_pseudo_id": "u2",
                "occurred_at": day,
            },
        )
        await service.run_rollups(niche_id=n1.id, from_date=day.date(), to_date=day.date())
        await service.run_rollups(niche_id=n2.id, from_date=day.date(), to_date=day.date())
        kitchen_overview = await service.overview(n1.id, from_date=day.date(), to_date=day.date())
        travel_overview = await service.overview(n2.id, from_date=day.date(), to_date=day.date())
        assert kitchen_overview["pageviews"] == 2
        assert travel_overview["pageviews"] == 1
        kitchen_pages = await service.top_pages(n1.id, from_date=day.date(), to_date=day.date())
        assert all("/articles/a" in row["page_url"] for row in kitchen_pages)

    scenario(runner)
