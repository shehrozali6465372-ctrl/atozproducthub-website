"""Domain events for the analytics module (API Contracts §11).

The analytics service publishes business events only — never AI OS data.
``analytics:rollup-completed.v1`` informs automation/observability that
daily/weekly read models were refreshed.
"""

from atoz_backend_core.events.envelope import EventEnvelope, new_event_id


def rollup_completed_event(
    *, niche_id: str, rollup_date: str, snapshot_kinds: list[str]
) -> EventEnvelope:
    return EventEnvelope(
        type="analytics:rollup-completed.v1",
        event_id=new_event_id(),
        payload={
            "niche_id": niche_id,
            "rollup_date": rollup_date,
            "snapshot_kinds": snapshot_kinds,
        },
        aggregate_id=niche_id,
    )
