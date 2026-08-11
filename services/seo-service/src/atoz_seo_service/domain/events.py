"""Domain events for the SEO module (API Contracts §11).

The website emits business events only — never AI OS data. The SEO service
consumes content/product lifecycle events to index/de-index search
documents, and publishes the frozen ``seo:sitemap-rebuilt.v1`` event after
sitemap regeneration so CDN/analytics consumers can react.
"""

from atoz_backend_core.events.envelope import EventEnvelope, new_event_id


def sitemap_rebuilt_event(*, niche_id: str, group_name: str, shard_count: int) -> EventEnvelope:
    return EventEnvelope(
        type="seo:sitemap-rebuilt.v1",
        event_id=new_event_id(),
        payload={"niche_id": niche_id, "group_name": group_name, "shard_count": shard_count},
        aggregate_id=niche_id,
    )


def search_indexed_event(*, entity_id: str, niche_id: str, entity_type: str) -> EventEnvelope:
    return EventEnvelope(
        type="search:indexed.v1",
        event_id=new_event_id(),
        payload={"entity_id": entity_id, "niche_id": niche_id, "entity_type": entity_type},
        aggregate_id=entity_id,
    )


def search_removed_event(*, entity_id: str, niche_id: str, entity_type: str) -> EventEnvelope:
    return EventEnvelope(
        type="search:removed.v1",
        event_id=new_event_id(),
        payload={"entity_id": entity_id, "niche_id": niche_id, "entity_type": entity_type},
        aggregate_id=entity_id,
    )
