"""JSON-LD schema tests (schema.org builders)."""

import json

from atoz_seo_service.domain.jsonld import (
    article_schema,
    breadcrumb_schema,
    collection_schema,
    landing_schema,
    product_schema,
    render,
)


def test_article_schema_has_required_entities() -> None:
    blob = article_schema(
        headline="Kitchen guide",
        description="A guide.",
        url="https://atozproducthub.dev/articles/kitchen-guide",
        date_published="2026-08-01",
    )
    rendered = render(blob)
    data = json.loads(rendered)
    assert data["@type"] == "Article"
    assert data["@context"] == "https://schema.org"
    assert data["headline"] == "Kitchen guide"
    assert data["author"]["@type"] == "Organization"
    assert data["mainEntityOfPage"]["@id"].endswith("/articles/kitchen-guide")


def test_product_schema_has_offer() -> None:
    blob = product_schema(
        name="Cast iron skillet",
        description="A pan.",
        url="https://atozproducthub.dev/products/cast-iron",
    )
    data = json.loads(render(blob))
    assert data["@type"] == "Product"
    assert data["offers"]["@type"] == "Offer"


def test_breadcrumb_schema_positions() -> None:
    blob = breadcrumb_schema(
        items=[
            ("Home", "/"),
            ("Kitchen", "/categories/kitchen"),
            ("Guide", "/articles/kitchen-guide"),
        ]
    )
    data = json.loads(render(blob))
    items = data["itemListElement"]
    assert [item["position"] for item in items] == [1, 2, 3]
    assert items[1]["item"].endswith("/categories/kitchen")


def test_collection_schema_has_item_list() -> None:
    blob = collection_schema(
        name="Kitchen Buys",
        description="Best picks.",
        url="https://atozproducthub.dev/collections/kitchen-buys",
        items=[{"@type": "Product", "name": "Pan"}],
    )
    data = json.loads(render(blob))
    assert data["@type"] == "CollectionPage"
    assert data["mainEntity"]["@type"] == "ItemList"


def test_landing_schema_webpage() -> None:
    blob = landing_schema(
        headline="Pack light",
        description="One-bag system.",
        url="https://atozproducthub.dev/landing/pack-light",
    )
    data = json.loads(render(blob))
    assert data["@type"] == "WebPage"
    assert data["publisher"]["@type"] == "Organization"


def test_render_is_deterministic() -> None:
    first = render(article_schema(headline="A", description="B", url="https://x.dev/a"))
    second = render(article_schema(headline="A", description="B", url="https://x.dev/a"))
    assert first == second
