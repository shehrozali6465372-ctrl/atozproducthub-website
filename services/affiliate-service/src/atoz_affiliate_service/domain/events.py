"""Domain events for the affiliate module (API Contracts §11).

The website emits business events only — never AI OS data. Consumers
(search, SEO, analytics, read models) tolerate additive payload fields.

Frozen event types (12-api-contracts.md §11):
- ``product:ingested.v1``   {product_id, niche_id, checksum}
- ``affiliate:click.v1``    {click_id, link_token_id, niche_id}
- ``revenue:attributed.v1`` {transaction_id, niche_id, amount}
"""

from atoz_backend_core.events.envelope import EventEnvelope, new_event_id


def product_ingested_event(*, product_id: str, niche_id: str, checksum: str) -> EventEnvelope:
    return EventEnvelope(
        type="product:ingested.v1",
        event_id=new_event_id(),
        payload={"product_id": product_id, "niche_id": niche_id, "checksum": checksum},
        aggregate_id=product_id,
    )


def product_removed_event(*, product_id: str, niche_id: str) -> EventEnvelope:
    return EventEnvelope(
        type="product:removed.v1",
        event_id=new_event_id(),
        payload={"product_id": product_id, "niche_id": niche_id},
        aggregate_id=product_id,
    )


def affiliate_click_event(*, click_id: str, link_token_id: str, niche_id: str) -> EventEnvelope:
    return EventEnvelope(
        type="affiliate:click.v1",
        event_id=new_event_id(),
        payload={"click_id": click_id, "link_token_id": link_token_id, "niche_id": niche_id},
        aggregate_id=click_id,
    )


def revenue_attributed_event(
    *, transaction_id: str, niche_id: str, amount_cents: int, currency: str
) -> EventEnvelope:
    return EventEnvelope(
        type="revenue:attributed.v1",
        event_id=new_event_id(),
        payload={
            "transaction_id": transaction_id,
            "niche_id": niche_id,
            "amount_cents": amount_cents,
            "currency": currency,
        },
        aggregate_id=transaction_id,
    )
