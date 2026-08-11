"""Explicit niche + Pinterest-account isolation tests (Task 18 §8)."""

from .fixtures import build_service, scenario, utc_dt


def test_pinterest_account_metrics_are_account_scoped() -> None:
    async def runner() -> None:
        _session_factory, service, _backbone, _warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        account_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        day = utc_dt(2026, 8, 5, 10)
        for index in range(3):
            await service.ingest_event(
                niche_slug="kitchen",
                event={
                    "event_id": f"acct-a-{index}",
                    "event_type": "pin_click",
                    "pinterest_account_id": account_a,
                    "occurred_at": day,
                },
            )
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": "acct-b-01",
                "event_type": "pin_click",
                "pinterest_account_id": account_b,
                "occurred_at": day,
            },
        )
        await service.run_rollups(niche_id=niche.id, from_date=day.date(), to_date=day.date())

        account_a_metrics = await service.metrics(
            niche.id, from_date=day.date(), to_date=day.date(), account_id=account_a
        )
        account_b_metrics = await service.metrics(
            niche.id, from_date=day.date(), to_date=day.date(), account_id=account_b
        )
        a_clicks = {m["metric_key"]: m["value"] for m in account_a_metrics}
        b_clicks = {m["metric_key"]: m["value"] for m in account_b_metrics}
        assert a_clicks["pinterest.pin_clicks"] == 3
        assert b_clicks["pinterest.pin_clicks"] == 1
        assert all(m["pinterest_account_id"] == account_a for m in account_a_metrics)
        assert all(m["pinterest_account_id"] == account_b for m in account_b_metrics)

    scenario(runner)


def test_ledger_never_exposes_another_account() -> None:
    async def runner() -> None:
        _session_factory, service, _backbone, _warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        day = utc_dt(2026, 8, 6, 10)
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": "ledger-acct-01",
                "event_type": "pin_click",
                "pinterest_account_id": account_a,
                "occurred_at": day,
            },
        )
        rows = await service.list_events(niche.id, account_id=account_a)
        assert len(rows) == 1
        other = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        rows_other = await service.list_events(niche.id, account_id=other)
        assert rows_other == []
        rows_unscoped = await service.list_events(niche.id)
        assert len(rows_unscoped) == 1

    scenario(runner)


def test_ten_accounts_never_leak_across_account_scoped_queries() -> None:
    """At 10 simulated Pinterest accounts, account-scoped reads and rollups
    never expose another account's events or metrics (Task 18 §8, M8 DoD)."""
    import uuid

    async def runner() -> None:
        _session_factory, service, _backbone, _warehouse = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        accounts = [str(uuid.uuid4()) for _ in range(10)]
        day = utc_dt(2026, 8, 7, 10)
        for index, account in enumerate(accounts):
            for event_index in range(3):
                await service.ingest_event(
                    niche_slug="kitchen",
                    event={
                        "event_id": f"iso10-{index}-{event_index}",
                        "event_type": "pin_click",
                        "pinterest_account_id": account,
                        "occurred_at": day,
                    },
                )
        await service.run_rollups(niche_id=niche.id, from_date=day.date(), to_date=day.date())

        for index, account in enumerate(accounts):
            events = await service.list_events(niche.id, account_id=account)
            assert len(events) == 3, f"account {index} sees {len(events)} events"
            assert all(row["pinterest_account_id"] == account for row in events)
            account_metrics = await service.metrics(
                niche.id, from_date=day.date(), to_date=day.date(), account_id=account
            )
            assert all(m["pinterest_account_id"] == account for m in account_metrics)
            clicks = {m["metric_key"]: m["value"] for m in account_metrics}
            assert clicks["pinterest.pin_clicks"] == 3

        all_events = await service.list_events(niche.id)
        assert len(all_events) == 30

    scenario(runner)
