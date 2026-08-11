"""JSON-LD schema builders for the business layer (Task 17 §3/§7).

Generates schema.org structured data for articles, products, breadcrumbs,
and collections from business data stored in the SEO service. This is pure
presentation logic — never AI generation. Metadata intelligence from the AI
OS arrives via the Bridge and is stored/validated, not generated here.
"""

from __future__ import annotations

import json
from typing import Any


def _ld(type_: str, **fields: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"@context": "https://schema.org", "@type": type_}
    data.update(fields)
    return data


def article_schema(
    *,
    headline: str,
    description: str,
    url: str,
    date_published: str | None = None,
    date_modified: str | None = None,
    author: str = "AtozProductHub",
    publisher: str = "AtozProductHub",
    image_url: str | None = None,
) -> dict[str, Any]:
    """schema.org Article (article pages)."""
    return _ld(
        "Article",
        headline=headline,
        description=description,
        mainEntityOfPage={"@type": "WebPage", "@id": url},
        url=url,
        datePublished=date_published,
        dateModified=date_modified or date_published,
        author={"@type": "Organization", "name": author},
        publisher={"@type": "Organization", "name": publisher},
        image=image_url or None,
    )


def product_schema(
    *,
    name: str,
    description: str,
    url: str,
    image_url: str | None = None,
    offers: dict[str, Any] | None = None,
    aggregate_rating: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """schema.org Product (product pages)."""
    return _ld(
        "Product",
        name=name,
        description=description,
        url=url,
        image=image_url or None,
        offers=offers
        or {"@type": "Offer", "availability": "https://schema.org/InStock", "priceCurrency": "USD"},
        aggregateRating=aggregate_rating,
    )


def breadcrumb_schema(*, items: list[tuple[str, str]]) -> dict[str, Any]:
    """schema.org BreadcrumbList (all content pages)."""
    return _ld(
        "BreadcrumbList",
        itemListElement=[
            {"@type": "ListItem", "position": index + 1, "name": label, "item": url}
            for index, (label, url) in enumerate(items)
        ],
    )


def collection_schema(
    *,
    name: str,
    description: str,
    url: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """schema.org CollectionPage + ItemList (category/tag/collection pages)."""
    return _ld(
        "CollectionPage",
        name=name,
        description=description,
        url=url,
        mainEntity={"@type": "ItemList", "itemListElement": items},
    )


def landing_schema(
    *,
    headline: str,
    description: str,
    url: str,
    publisher: str = "AtozProductHub",
) -> dict[str, Any]:
    """schema.org WebPage for Pinterest landing pages."""
    return _ld(
        "WebPage",
        headline=headline,
        description=description,
        url=url,
        publisher={"@type": "Organization", "name": publisher},
    )


def render(blob: dict[str, Any]) -> str:
    """Serialize a JSON-LD blob (compact, stable key order for checksums)."""
    return json.dumps(blob, sort_keys=True, separators=(",", ":"))
