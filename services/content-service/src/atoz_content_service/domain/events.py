"""Domain events for content lifecycle changes (API Contracts §11).

The website emits business events only — never AI OS data. Consumers
(search, SEO, analytics, renderer, Redis invalidation) tolerate additive
payload fields.

Frozen event types (12-api-contracts.md §11):
- ``content:published.v1``   {article_id, niche_id, url, checksum}
- ``content:updated.v1``     {article_id, niche_id}
- ``content:unpublished.v1`` {article_id, niche_id}
"""

from atoz_backend_core.events.envelope import EventEnvelope, new_event_id


def content_published_event(
    *, article_id: str, niche_id: str, url: str, checksum: str
) -> EventEnvelope:
    return EventEnvelope(
        type="content:published.v1",
        event_id=new_event_id(),
        payload={
            "article_id": article_id,
            "niche_id": niche_id,
            "url": url,
            "checksum": checksum,
        },
        aggregate_id=article_id,
    )


def content_updated_event(*, article_id: str, niche_id: str, status: str) -> EventEnvelope:
    return EventEnvelope(
        type="content:updated.v1",
        event_id=new_event_id(),
        payload={"article_id": article_id, "niche_id": niche_id, "status": status},
        aggregate_id=article_id,
    )


def content_unpublished_event(*, article_id: str, niche_id: str) -> EventEnvelope:
    return EventEnvelope(
        type="content:unpublished.v1",
        event_id=new_event_id(),
        payload={"article_id": article_id, "niche_id": niche_id},
        aggregate_id=article_id,
    )
