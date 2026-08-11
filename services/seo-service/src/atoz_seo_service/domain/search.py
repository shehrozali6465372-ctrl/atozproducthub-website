"""Search index boundary (Database Blueprint §10 — lexical search only).

The SEO service never does semantic/vector search: Typesense provides
typo-tolerant lexical search with niche filtering. ``SearchIndex`` is the
port; ``TypesenseSearchIndex`` talks to the Typesense REST API (server-side
only, never from the frontend), and ``InMemorySearchIndex`` backs dev/tests
without a Typesense dependency.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

from atoz_seo_service.errors import RemoteApiError, SearchUnavailableError

logger = logging.getLogger("atoz.seo.search")

COLLECTION_SCHEMA: dict[str, Any] = {
    "name": "seo_content",
    "fields": [
        {"name": "id", "type": "string", "facet": False},
        {"name": "type", "type": "string", "facet": True},
        {"name": "niche_id", "type": "string", "facet": True},
        {"name": "slug", "type": "string", "facet": False},
        {"name": "title", "type": "string", "facet": False},
        {"name": "excerpt", "type": "string", "facet": False},
        {"name": "url", "type": "string", "facet": False},
        {"name": "tags", "type": "string[]", "facet": False},
        {"name": "price_cents", "type": "int32", "facet": False, "optional": True},
        {"name": "published_at", "type": "string", "facet": False, "optional": True},
        {"name": "updated_ts", "type": "int64", "facet": False},
    ],
    "default_sorting_field": "updated_ts",
}


@dataclass
class SearchDocument:
    """One indexable business document."""

    id: str
    type: str
    niche_id: str
    slug: str
    title: str
    excerpt: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)
    price_cents: int | None = None
    published_at: str | None = None
    updated_at: datetime | None = None

    def to_typesense_doc(self) -> dict[str, Any]:
        updated_ts = int((self.updated_at or datetime.now(UTC)).timestamp())
        return {
            "id": self.id,
            "type": self.type,
            "niche_id": self.niche_id,
            "slug": self.slug,
            "title": self.title,
            "excerpt": self.excerpt,
            "url": self.url,
            "tags": self.tags,
            "price_cents": self.price_cents,
            "published_at": self.published_at,
            "updated_ts": updated_ts,
        }


@dataclass
class SearchHit:
    """One search result."""

    id: str
    type: str
    niche_id: str
    slug: str
    title: str
    excerpt: str
    url: str
    score: float = 0.0


@dataclass
class SearchPage:
    """Paginated search results."""

    items: list[SearchHit]
    page: int
    page_size: int
    total: int


class SearchIndex(ABC):
    """Port over the Typesense boundary (never in frontend code)."""

    @abstractmethod
    async def ensure_collection(self) -> None: ...

    @abstractmethod
    async def upsert(self, document: SearchDocument) -> None: ...

    @abstractmethod
    async def delete(self, document_id: str, *, niche_id: str) -> bool: ...

    @abstractmethod
    async def search(
        self,
        *,
        query: str,
        niche_id: str,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchPage: ...


class TypesenseSearchIndex(SearchIndex):
    """Typesense REST client (collection per service, niche-filtered queries)."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        collection: str = "seo_content",
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._collection = collection
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout_seconds,
            headers={"X-Typesense-Api-Key": api_key},
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def ensure_collection(self) -> None:
        schema = dict(COLLECTION_SCHEMA)
        schema["name"] = self._collection
        response = await self._client.put(f"/collections/{self._collection}", json=schema)
        if response.status_code not in (200, 201, 409):
            raise RemoteApiError(
                f"Typesense collection setup failed: {response.status_code} {response.text[:200]}",
                retryable=response.status_code >= 500,
            )

    async def upsert(self, document: SearchDocument) -> None:
        response = await self._client.post(
            f"/collections/{self._collection}/documents?action=upsert",
            json=document.to_typesense_doc(),
        )
        if response.status_code not in (200, 201):
            raise RemoteApiError(
                f"Typesense upsert failed: {response.status_code} {response.text[:200]}",
                retryable=response.status_code >= 500,
            )

    async def delete(self, document_id: str, *, niche_id: str) -> bool:
        response = await self._client.delete(
            f"/collections/{self._collection}/documents/{document_id}",
            params={"filter_by": f"niche_id:={niche_id}"},
        )
        if response.status_code == 404:
            return False
        if response.status_code not in (200, 204):
            raise RemoteApiError(
                f"Typesense delete failed: {response.status_code} {response.text[:200]}",
                retryable=response.status_code >= 500,
            )
        return True

    async def search(
        self,
        *,
        query: str,
        niche_id: str,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchPage:
        params: dict[str, Any] = {
            "q": query,
            "query_by": "title,excerpt,tags",
            "filter_by": f"niche_id:={niche_id}",
            "sort_by": "updated_ts:desc",
            "page": max(page, 1),
            "per_page": min(max(page_size, 1), 250),
        }
        if types:
            params["filter_by"] += f" && type:=[{','.join(types)}]"
        try:
            response = await self._client.get(
                f"/collections/{self._collection}/documents/search", params=params
            )
        except httpx.HTTPError as exc:
            raise SearchUnavailableError(f"Search backend unreachable: {exc}") from exc
        if response.status_code != 200:
            raise RemoteApiError(
                f"Typesense search failed: {response.status_code} {response.text[:200]}",
                retryable=response.status_code >= 500,
            )
        payload = response.json()
        found = int(payload.get("found", 0))
        items = [
            SearchHit(
                id=str(hit.get("id", "")),
                type=str(hit.get("type", "")),
                niche_id=str(hit.get("niche_id", "")),
                slug=str(hit.get("slug", "")),
                title=str(hit.get("title", "")),
                excerpt=str(hit.get("excerpt", "")),
                url=str(hit.get("url", "")),
                score=float(hit.get("text_match", 0) or 0),
            )
            for hit in payload.get("hits", [])
            if hit.get("document", {})
        ]
        return SearchPage(items=items, page=page, page_size=page_size, total=found)


class InMemorySearchIndex(SearchIndex):
    """Dev/test index: niche-filtered in-memory documents with pagination."""

    def __init__(self) -> None:
        self._docs: dict[tuple[str, str], SearchDocument] = {}  # (niche_id, id) -> doc

    async def ensure_collection(self) -> None:
        return None

    async def upsert(self, document: SearchDocument) -> None:
        self._docs[(document.niche_id, document.id)] = document

    async def delete(self, document_id: str, *, niche_id: str) -> bool:
        return self._docs.pop((niche_id, document_id), None) is not None

    async def search(
        self,
        *,
        query: str,
        niche_id: str,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchPage:
        needle = query.strip().lower()
        matched = [
            doc
            for (niche, _doc_id), doc in self._docs.items()
            if niche == niche_id and (types is None or doc.type in types)
        ]
        if needle:
            matched = [
                doc
                for doc in matched
                if needle in doc.title.lower()
                or needle in doc.excerpt.lower()
                or needle in " ".join(doc.tags).lower()
            ]
        matched.sort(key=lambda doc: doc.updated_at or datetime.min, reverse=True)
        total = len(matched)
        start = (max(page, 1) - 1) * max(page_size, 1)
        return SearchPage(
            items=[
                SearchHit(
                    id=doc.id,
                    type=doc.type,
                    niche_id=doc.niche_id,
                    slug=doc.slug,
                    title=doc.title,
                    excerpt=doc.excerpt,
                    url=doc.url,
                    score=1.0,
                )
                for doc in matched[start : start + page_size]
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
