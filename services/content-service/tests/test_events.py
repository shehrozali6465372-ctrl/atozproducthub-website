"""Content domain event envelope tests (API Contracts §11)."""

from atoz_content_service.domain.events import (
    content_published_event,
    content_unpublished_event,
    content_updated_event,
)


def test_published_event_contract() -> None:
    event = content_published_event(
        article_id="a1", niche_id="n1", url="https://atozproducthub.dev/articles/x", checksum="c1"
    )
    event.validate_type()
    assert event.type == "content:published.v1"
    assert event.payload == {
        "article_id": "a1",
        "niche_id": "n1",
        "url": "https://atozproducthub.dev/articles/x",
        "checksum": "c1",
    }
    assert event.aggregate_id == "a1"
    assert event.event_id


def test_updated_event_contract() -> None:
    event = content_updated_event(article_id="a1", niche_id="n1", status="draft")
    event.validate_type()
    assert event.type == "content:updated.v1"
    assert event.payload == {"article_id": "a1", "niche_id": "n1", "status": "draft"}


def test_unpublished_event_contract() -> None:
    event = content_unpublished_event(article_id="a1", niche_id="n1")
    event.validate_type()
    assert event.type == "content:unpublished.v1"
    assert event.payload == {"article_id": "a1", "niche_id": "n1"}
