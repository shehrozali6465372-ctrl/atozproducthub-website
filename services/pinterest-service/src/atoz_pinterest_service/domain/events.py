"""Domain events for the Pinterest module (API Contracts §11).

The website emits business events only — never AI OS data. Consumers
(analytics, attribution, read models) tolerate additive payload fields.

Frozen event types (12-api-contracts.md §11):
- ``pin:scheduled.v1``  {pin_id, account_id, niche_id, run_at}
- ``pin:published.v1``  {pin_id, account_id, niche_id, remote_pin_id}
- ``pin:failed.v1``     {pin_id, account_id, niche_id, error}
- ``account:connected.v1`` {account_id, niche_id}
- ``account:disconnected.v1`` {account_id, niche_id}
"""

from atoz_backend_core.events.envelope import EventEnvelope, new_event_id


def pin_scheduled_event(
    *, pin_id: str, account_id: str, niche_id: str, run_at: str
) -> EventEnvelope:
    return EventEnvelope(
        type="pin:scheduled.v1",
        event_id=new_event_id(),
        payload={
            "pin_id": pin_id,
            "account_id": account_id,
            "niche_id": niche_id,
            "run_at": run_at,
        },
        aggregate_id=pin_id,
    )


def pin_published_event(
    *, pin_id: str, account_id: str, niche_id: str, remote_pin_id: str
) -> EventEnvelope:
    return EventEnvelope(
        type="pin:published.v1",
        event_id=new_event_id(),
        payload={
            "pin_id": pin_id,
            "account_id": account_id,
            "niche_id": niche_id,
            "remote_pin_id": remote_pin_id,
        },
        aggregate_id=pin_id,
    )


def pin_failed_event(*, pin_id: str, account_id: str, niche_id: str, error: str) -> EventEnvelope:
    return EventEnvelope(
        type="pin:failed.v1",
        event_id=new_event_id(),
        payload={"pin_id": pin_id, "account_id": account_id, "niche_id": niche_id, "error": error},
        aggregate_id=pin_id,
    )


def account_connected_event(*, account_id: str, niche_id: str) -> EventEnvelope:
    return EventEnvelope(
        type="account:connected.v1",
        event_id=new_event_id(),
        payload={"account_id": account_id, "niche_id": niche_id},
        aggregate_id=account_id,
    )


def account_disconnected_event(*, account_id: str, niche_id: str) -> EventEnvelope:
    return EventEnvelope(
        type="account:disconnected.v1",
        event_id=new_event_id(),
        payload={"account_id": account_id, "niche_id": niche_id},
        aggregate_id=account_id,
    )
