"""SEO business service facade (M7).

Owns the discovery use cases: niche tenancy mirror, URL registry + applied
metadata (canonical/robots/OG/JSON-LD), sitemap shard generation, robots
rendering, niche-scoped search indexing driven by content/product domain
events, crawl-report ingestion boundaries (GSC/Bing), and SEO health
snapshots.

The service NEVER performs AI work: metadata intelligence arrives via the
AI OS Bridge and is validated, stored, and served as business data. No
LLM/model SDKs are imported anywhere in this package.
"""

import hashlib
import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher
from atoz_seo_service.config import SITEMAP_GROUPS, Settings
from atoz_seo_service.domain.canonical import canonical_url, entity_path, normalize_path
from atoz_seo_service.domain.entities import (
    SeoCrawlReport,
    SeoHealthCheck,
    SeoMetadata,
    SeoNiche,
    SitemapShard,
    UrlRegistry,
)
from atoz_seo_service.domain.enums import (
    CrawlSource,
    EntityType,
    EventKind,
    HealthCheckType,
    RobotsRule,
    SearchDocType,
    ShardStatus,
    UrlStatus,
)
from atoz_seo_service.domain.events import (
    search_indexed_event,
    search_removed_event,
    sitemap_rebuilt_event,
)
from atoz_seo_service.domain.jsonld import (
    article_schema,
    breadcrumb_schema,
    landing_schema,
    product_schema,
)
from atoz_seo_service.domain.jsonld import (
    render as render_jsonld,
)
from atoz_seo_service.domain.robots import build_robots
from atoz_seo_service.domain.search import (
    InMemorySearchIndex,
    SearchDocument,
    SearchIndex,
    SearchPage,
    TypesenseSearchIndex,
)
from atoz_seo_service.domain.sitemaps import (
    SitemapShard as RenderedShard,
)
from atoz_seo_service.domain.sitemaps import (
    SitemapUrl,
    render_index,
    render_shard,
    shard_urls,
)
from atoz_seo_service.errors import (
    DuplicateError,
    NotFoundError,
    RemoteApiError,
    ValidationError,
)
from atoz_seo_service.repositories import SeoUnitOfWork
from atoz_seo_service.uuids import uuid7

logger = logging.getLogger("atoz.seo.service")

_SITEMAP_CHANGEFREQ_BY_GROUP = {
    "articles": "weekly",
    "categories": "weekly",
    "tags": "monthly",
    "products": "weekly",
    "landing": "daily",
    "collections": "weekly",
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _checksum(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode())
    return digest.hexdigest()


class SearchIndexFactory:
    """Build the configured SearchIndex; dev default is in-memory."""

    @staticmethod
    def build(settings: Settings, *, transport=None) -> SearchIndex:
        if settings.typesense_api_base and settings.app_env != "test":
            return TypesenseSearchIndex(
                base_url=settings.typesense_api_base,
                api_key=settings.typesense_api_key,
                collection=settings.search_collection,
                transport=transport,
            )
        return InMemorySearchIndex()


class CrawlApi:
    """Google Search Console / Bing Webmaster boundary (Task 17 §6).

    Credentials stay server-side (Vault refs); the production submission
    hooks are placeholders that raise until the Platform provisions the
    service accounts. The interface is tested with mocks; nothing here is
    ever exposed to the frontend.
    """

    async def submit_sitemap(self, *, source: str, sitemap_url: str) -> dict[str, str]:
        raise RemoteApiError(
            f"{source} sitemap submission is not provisioned (credentials via Vault)."
        )

    async def fetch_report(
        self, *, source: str, niche_slug: str, report_date: str
    ) -> dict[str, Any]:
        raise RemoteApiError(f"{source} report fetch is not provisioned (credentials via Vault).")


class SeoService:
    """Facade over the SEO/discovery business layer (one service per app)."""

    def __init__(
        self,
        *,
        uow_factory,
        event_publisher: EventPublisher,
        settings: Settings,
        search_index: SearchIndex | None = None,
        crawl_api: CrawlApi | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._events = event_publisher
        self._settings = settings
        self._search = search_index or SearchIndexFactory.build(settings)
        self._crawl_api = crawl_api or CrawlApi()

    @staticmethod
    def build_uow(session_factory) -> SeoUnitOfWork:
        return SeoUnitOfWork.build(session_factory)

    # ----------------------------------------------------------------- niche
    async def create_niche(self, *, name: str, slug: str, status: str = "draft") -> SeoNiche:
        async with self._uow_factory().transaction() as unit:
            if await unit.niches.slug_exists(slug):
                raise DuplicateError("A niche with this slug already exists.")
            niche = SeoNiche(id=uuid7(), name=name, slug=slug, status=status)
            await unit.niches.add(niche)
            return niche

    async def get_niche(self, niche_id: str) -> SeoNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> SeoNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get_by_slug(slug)

    async def list_niches(self, *, status: str | None = None) -> Sequence[SeoNiche]:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.list_by_status(status)

    # -------------------------------------------------------- URL + metadata
    async def register_url(
        self,
        *,
        niche_id: str,
        entity_type: str,
        entity_id: str,
        slug: str | None = None,
        path: str | None = None,
        status: str = UrlStatus.ACTIVE.value,
        changed_at: datetime | None = None,
    ) -> UrlRegistry:
        """Register a public URL (canonical path + duplicate prevention)."""
        entity_type = _validate_entity_type(entity_type)
        if path is None:
            if not slug:
                raise ValidationError("Either slug or path is required.")
            path = entity_path(entity_type=entity_type, slug=slug)
        path = normalize_path(path)
        async with self._uow_factory().transaction() as unit:
            existing = await unit.urls.get_by_path(path, niche_id=niche_id)
            if existing is not None and existing.entity_id != entity_id:
                raise DuplicateError(f"Path {path} is already registered for another entity.")
            if slug:
                existing_slug = await unit.urls.get_by_slug(slug, niche_id=niche_id)
                if existing_slug is not None and existing_slug.entity_id != entity_id:
                    raise DuplicateError(
                        f"Slug {slug!r} is already used by another entity in this niche."
                    )
            by_entity = await unit.urls.get_by_entity(entity_type, entity_id, niche_id=niche_id)
            if by_entity is not None:
                by_entity.path = path
                by_entity.canonical_path = path
                by_entity.status = status
                by_entity.changed_at = changed_at or _utcnow()
                return by_entity
            row = UrlRegistry(
                id=uuid7(),
                niche_id=niche_id,
                path=path,
                canonical_path=path,
                entity_type=entity_type,
                entity_id=entity_id,
                article_id=entity_id if entity_type == EntityType.ARTICLE.value else None,
                product_id=entity_id if entity_type == EntityType.PRODUCT.value else None,
                status=status,
                changed_at=changed_at or _utcnow(),
            )
            await unit.urls.add(row)
            return row

    async def set_url_status(
        self, *, niche_id: str, entity_type: str, entity_id: str, status: str
    ) -> UrlRegistry | None:
        async with self._uow_factory().transaction() as unit:
            row = await unit.urls.get_by_entity(entity_type, entity_id, niche_id=niche_id)
            if row is None:
                return None
            row.status = status
            row.changed_at = _utcnow()
            meta = await unit.metadata.get_by_url(row.id, niche_id=niche_id)
            if meta is not None:
                meta.robots = (
                    RobotsRule.NOINDEX.value
                    if status != UrlStatus.ACTIVE.value
                    else RobotsRule.INDEX.value
                )
            return row

    async def upsert_metadata(
        self,
        *,
        niche_id: str,
        url_registry_id: str,
        title: str = "",
        meta_description: str = "",
        robots: str = RobotsRule.INDEX.value,
        og: dict[str, Any] | None = None,
        structured_data: list[dict[str, Any]] | None = None,
    ) -> SeoMetadata:
        """Validate + apply SEO metadata to a registered URL (AI OS output path)."""
        if robots not in {rule.value for rule in RobotsRule}:
            raise ValidationError(f"Invalid robots directive: {robots}.")
        og = og or {}
        structured_data = structured_data or []
        async with self._uow_factory().transaction() as unit:
            url = await unit.urls.get_scoped(url_registry_id, niche_id=niche_id)
            if url is None:
                raise NotFoundError("URL registry entry not found in this niche.")
            canonical = canonical_url(
                public_base_url=self._settings.public_base_url, path=url.canonical_path
            )
            checksum = _checksum(
                title,
                meta_description,
                canonical,
                robots,
                json.dumps(og, sort_keys=True),
                json.dumps(structured_data, sort_keys=True),
            )
            existing = await unit.metadata.get_by_url(url_registry_id, niche_id=niche_id)
            if existing is not None:
                existing.title = title
                existing.meta_description = meta_description
                existing.canonical_url = canonical
                existing.robots = robots
                existing.og_json = json.dumps(og, sort_keys=True)
                existing.structured_data_json = json.dumps(structured_data, sort_keys=True)
                existing.checksum = checksum
                return existing
            row = SeoMetadata(
                id=uuid7(),
                niche_id=niche_id,
                url_registry_id=url_registry_id,
                title=title,
                meta_description=meta_description,
                canonical_url=canonical,
                robots=robots,
                og_json=json.dumps(og, sort_keys=True),
                structured_data_json=json.dumps(structured_data, sort_keys=True),
                checksum=checksum,
            )
            await unit.metadata.add(row)
            return row

    async def get_metadata_for_path(self, *, niche_id: str, path: str) -> dict[str, Any] | None:
        """Resolve applied metadata for a normalized public path (frontend reads)."""
        path = normalize_path(path)
        async with self._uow_factory().transaction() as unit:
            url = await unit.urls.get_by_path(path, niche_id=niche_id)
            if url is None or url.status != UrlStatus.ACTIVE.value:
                return None
            meta = await unit.metadata.get_by_url(url.id, niche_id=niche_id)
            return {
                "title": meta.title if meta else "",
                "description": meta.meta_description if meta else "",
                "canonical_url": meta.canonical_url
                if meta
                else canonical_url(
                    public_base_url=self._settings.public_base_url, path=url.canonical_path
                ),
                "robots": meta.robots if meta else RobotsRule.INDEX.value,
                "og": json.loads(meta.og_json) if meta and meta.og_json else {},
                "structured_data": json.loads(meta.structured_data_json)
                if meta and meta.structured_data_json
                else [],
            }

    async def list_urls(
        self,
        niche_id: str,
        *,
        entity_types: Sequence[str] | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> Sequence[UrlRegistry]:
        async with self._uow_factory().transaction() as unit:
            return await unit.urls.list_active(
                niche_id, entity_types=entity_types, limit=limit, offset=offset
            )

    # --------------------------------------------------------------- search
    async def search(
        self,
        *,
        query: str,
        niche_id: str,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchPage:
        """Niche-scoped lexical search (never cross-niche)."""
        page_size = min(max(page_size, 1), self._settings.search_page_size_max)
        return await self._search.search(
            query=query, niche_id=niche_id, types=types, page=page, page_size=page_size
        )

    async def index_document(self, document: SearchDocument) -> None:
        """Index/upsert one business document (idempotent)."""
        await self._search.ensure_collection()
        await self._search.upsert(document)
        await self._events.publish(
            search_indexed_event(
                entity_id=document.id, niche_id=document.niche_id, entity_type=document.type
            )
        )

    async def remove_document(self, *, document_id: str, niche_id: str, entity_type: str) -> bool:
        """De-index a document (idempotent; missing docs are a no-op)."""
        removed = await self._search.delete(document_id, niche_id=niche_id)
        await self._events.publish(
            search_removed_event(entity_id=document_id, niche_id=niche_id, entity_type=entity_type)
        )
        return removed

    # ------------------------------------------------------- event ingestion
    async def handle_event(self, envelope: EventEnvelope) -> None:
        """Dispatch a content/product lifecycle event (Task 17 §8)."""
        kind = envelope.type
        payload = envelope.payload
        niche_id = str(payload.get("niche_id", ""))
        if not niche_id:
            raise ValidationError("Event payload is missing niche_id.")
        if kind == EventKind.CONTENT_PUBLISHED.value:
            await self._index_article(payload, niche_id=niche_id)
        elif kind == EventKind.CONTENT_UPDATED.value:
            await self._reindex_article(payload, niche_id=niche_id)
        elif kind == EventKind.CONTENT_UNPUBLISHED.value:
            article_id = str(payload.get("article_id", ""))
            await self.remove_document(
                document_id=article_id, niche_id=niche_id, entity_type=SearchDocType.ARTICLE.value
            )
            await self.set_url_status(
                niche_id=niche_id,
                entity_type=EntityType.ARTICLE.value,
                entity_id=article_id,
                status=UrlStatus.REMOVED.value,
            )
        elif kind == EventKind.PRODUCT_INGESTED.value:
            await self._index_product(payload, niche_id=niche_id)
        elif kind == EventKind.PRODUCT_REMOVED.value:
            product_id = str(payload.get("product_id", ""))
            await self.remove_document(
                document_id=product_id, niche_id=niche_id, entity_type=SearchDocType.PRODUCT.value
            )
            await self.set_url_status(
                niche_id=niche_id,
                entity_type=EntityType.PRODUCT.value,
                entity_id=product_id,
                status=UrlStatus.REMOVED.value,
            )
        else:
            raise ValidationError(f"Unsupported event type: {kind}.")

    async def _index_article(self, payload: dict[str, Any], *, niche_id: str) -> None:
        article_id = str(payload.get("article_id", ""))
        if not article_id:
            raise ValidationError("content:published.v1 payload is missing article_id.")
        url = str(payload.get("url", "")) or entity_path(
            entity_type=EntityType.ARTICLE.value, slug=article_id
        )
        await self.register_url(
            niche_id=niche_id,
            entity_type=EntityType.ARTICLE.value,
            entity_id=article_id,
            path=url,
        )
        await self.index_document(
            SearchDocument(
                id=article_id,
                type=SearchDocType.ARTICLE.value,
                niche_id=niche_id,
                slug=article_id,
                title=str(payload.get("title", "Untitled article")),
                excerpt=str(payload.get("excerpt", "")),
                url=normalize_path(url),
                published_at=str(payload.get("published_at") or ""),
                updated_at=_utcnow(),
            )
        )

    async def _reindex_article(self, payload: dict[str, Any], *, niche_id: str) -> None:
        article_id = str(payload.get("article_id", ""))
        if not article_id:
            raise ValidationError("content:updated.v1 payload is missing article_id.")
        await self.index_document(
            SearchDocument(
                id=article_id,
                type=SearchDocType.ARTICLE.value,
                niche_id=niche_id,
                slug=article_id,
                title=str(payload.get("title", "Untitled article")),
                excerpt=str(payload.get("excerpt", "")),
                url=normalize_path(str(payload.get("url", f"/articles/{article_id}"))),
                published_at=str(payload.get("published_at") or ""),
                updated_at=_utcnow(),
            )
        )

    async def _index_product(self, payload: dict[str, Any], *, niche_id: str) -> None:
        product_id = str(payload.get("product_id", ""))
        if not product_id:
            raise ValidationError("product:ingested.v1 payload is missing product_id.")
        url = str(payload.get("url", "")) or entity_path(
            entity_type=EntityType.PRODUCT.value, slug=product_id
        )
        await self.register_url(
            niche_id=niche_id,
            entity_type=EntityType.PRODUCT.value,
            entity_id=product_id,
            path=url,
        )
        price = payload.get("price_cents")
        await self.index_document(
            SearchDocument(
                id=product_id,
                type=SearchDocType.PRODUCT.value,
                niche_id=niche_id,
                slug=product_id,
                title=str(payload.get("name", "Untitled product")),
                excerpt=str(payload.get("summary", "")),
                url=normalize_path(url),
                price_cents=int(price) if isinstance(price, int) else None,
                updated_at=_utcnow(),
            )
        )

    # -------------------------------------------------------------- sitemaps
    async def rebuild_sitemap_group(
        self, *, niche_id: str, group_name: str
    ) -> list[dict[str, Any]]:
        """Rebuild one sitemap group: shard the active URL set, record shards,
        and emit ``seo:sitemap-rebuilt.v1``. Returns shard descriptors."""
        if group_name not in SITEMAP_GROUPS:
            raise ValidationError(f"Unknown sitemap group: {group_name}.")
        entity_types = _entity_types_for_group(group_name)
        async with self._uow_factory().transaction() as unit:
            urls = await unit.urls.list_active(
                niche_id, entity_types=entity_types, limit=self._settings.sitemap_group_chunk_urls
            )
            rendered = [
                SitemapUrl(
                    loc=canonical_url(
                        public_base_url=self._settings.public_base_url, path=row.path
                    ),
                    lastmod=row.changed_at,
                    changefreq=_SITEMAP_CHANGEFREQ_BY_GROUP.get(group_name, "weekly"),
                    priority="0.8" if group_name in {"articles", "products"} else "0.5",
                )
                for row in urls
            ]
            shards = shard_urls(rendered, max_urls=self._settings.sitemap_max_urls)
            rows = [
                SitemapShard(
                    id=uuid7(),
                    niche_id=niche_id,
                    group_name=group_name,
                    shard_no=shard.shard_no,
                    object_ref=f"/sitemaps/{group_name}-{shard.shard_no}.xml",
                    url_count=shard.url_count,
                    generated_at=_utcnow(),
                    status=ShardStatus.READY.value,
                    last_url=shard.urls[-1].loc if shard.urls else "",
                )
                for shard in shards
            ]
            await unit.shards.replace_group(niche_id, group_name, rows)
        await self._events.publish(
            sitemap_rebuilt_event(niche_id=niche_id, group_name=group_name, shard_count=len(rows))
        )
        return [
            {
                "group": group_name,
                "shard_no": row.shard_no,
                "object_ref": row.object_ref,
                "url_count": row.url_count,
                "status": row.status,
                "generated_at": row.generated_at.isoformat() if row.generated_at else None,
            }
            for row in rows
        ]

    async def render_sitemap_shard(
        self, *, niche_id: str, group_name: str, shard_no: int
    ) -> str | None:
        """Render a stored shard's XML from the registry (public read path)."""
        if group_name not in SITEMAP_GROUPS:
            return None
        entity_types = _entity_types_for_group(group_name)
        async with self._uow_factory().transaction() as unit:
            rows = await unit.shards.list_by_niche(niche_id, group_name=group_name)
            if not rows:
                return None
            target = next((row for row in rows if row.shard_no == shard_no), None)
            if target is None:
                return None
            offset = (shard_no - 1) * self._settings.sitemap_max_urls
            urls = await unit.urls.list_active(
                niche_id,
                entity_types=entity_types,
                limit=self._settings.sitemap_max_urls,
                offset=offset,
            )
        rendered = [
            SitemapUrl(
                loc=canonical_url(public_base_url=self._settings.public_base_url, path=row.path),
                lastmod=row.changed_at,
                changefreq=_SITEMAP_CHANGEFREQ_BY_GROUP.get(group_name, "weekly"),
                priority="0.8" if group_name in {"articles", "products"} else "0.5",
            )
            for row in urls
        ]
        shard = RenderedShard(group_name=group_name, shard_no=shard_no, urls=rendered)
        return render_shard(shard)

    async def list_sitemap_shards(
        self, niche_id: str, *, group_name: str | None = None
    ) -> Sequence[SitemapShard]:
        async with self._uow_factory().transaction() as unit:
            return await unit.shards.list_by_niche(niche_id, group_name=group_name)

    async def render_sitemap_index(self, *, niche_id: str, group_name: str) -> str | None:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.shards.list_by_niche(niche_id, group_name=group_name)
            if not rows:
                return None
        return render_index(
            base_url=self._settings.public_base_url,
            group_name=group_name,
            shard_count=len(rows),
            lastmod=_utcnow(),
        )

    # ---------------------------------------------------------------- robots
    async def render_robots(self, *, niche_id: str) -> str:
        """Render robots.txt for a niche (Pinterestbot always allowed)."""
        niche = await self.get_niche(niche_id)
        if niche is None or niche.status != "active":
            raise ValidationError("The requested niche is not registered or active.")
        return build_robots(
            base_url=self._settings.public_base_url,
            allow_paths=self._settings.robots_allow,
            disallow_paths=self._settings.robots_disallow,
            sitemap_group_names=SITEMAP_GROUPS,
            sitemap_max_urls=self._settings.sitemap_max_urls,
        )

    # -------------------------------------------------------- crawl boundary
    async def submit_sitemap(self, *, niche_id: str, source: str) -> dict[str, str]:
        """Submit sitemaps to GSC/Bing via the crawl boundary (server-side only)."""
        niche = await self.get_niche(niche_id)
        if niche is None:
            raise NotFoundError("Niche not found.")
        if source not in {CrawlSource.GSC.value, CrawlSource.BING.value}:
            raise ValidationError(f"Unsupported crawl source: {source}.")
        sitemap_url = canonical_url(
            public_base_url=self._settings.public_base_url, path="/sitemaps/root-index.xml"
        )
        return await self._crawl_api.submit_sitemap(source=source, sitemap_url=sitemap_url)

    async def record_crawl_report(
        self,
        *,
        niche_id: str,
        source: str,
        report_date: str,
        pages_indexed: int = 0,
        impressions: int = 0,
        clicks: int = 0,
        position_avg: float = 0.0,
        raw: dict[str, Any] | None = None,
    ) -> SeoCrawlReport:
        if source not in {CrawlSource.GSC.value, CrawlSource.BING.value}:
            raise ValidationError(f"Unsupported crawl source: {source}.")
        async with self._uow_factory().transaction() as unit:
            row = SeoCrawlReport(
                id=uuid7(),
                niche_id=niche_id,
                source=source,
                report_date=report_date,
                pages_indexed=pages_indexed,
                impressions=impressions,
                clicks=clicks,
                position_avg=position_avg,
                raw_json=json.dumps(raw or {}, sort_keys=True),
            )
            await unit.crawl_reports.add(row)
            return row

    async def list_crawl_reports(
        self, niche_id: str, *, source: str | None = None, limit: int = 100
    ) -> Sequence[SeoCrawlReport]:
        async with self._uow_factory().transaction() as unit:
            return await unit.crawl_reports.list_by_niche(niche_id, source=source, limit=limit)

    # ------------------------------------------------------------ health
    async def record_health_check(
        self,
        *,
        niche_id: str,
        check_type: str,
        score: float,
        details: dict[str, Any] | None = None,
        url_registry_id: str | None = None,
    ) -> SeoHealthCheck:
        if check_type not in {item.value for item in HealthCheckType}:
            raise ValidationError(f"Unsupported health check type: {check_type}.")
        async with self._uow_factory().transaction() as unit:
            row = SeoHealthCheck(
                id=uuid7(),
                niche_id=niche_id,
                url_registry_id=url_registry_id,
                check_type=check_type,
                score=score,
                details_json=json.dumps(details or {}, sort_keys=True),
                checked_at=_utcnow(),
            )
            await unit.health_checks.add(row)
            return row

    async def list_health_checks(
        self, niche_id: str, *, check_type: str | None = None, limit: int = 100
    ) -> Sequence[SeoHealthCheck]:
        async with self._uow_factory().transaction() as unit:
            return await unit.health_checks.list_by_niche(
                niche_id, check_type=check_type, limit=limit
            )

    # ------------------------------------------------------------ JSON-LD
    def build_article_jsonld(
        self, *, title: str, description: str, path: str, published_at: str | None = None
    ) -> str:
        url = canonical_url(public_base_url=self._settings.public_base_url, path=path)
        return render_jsonld(
            article_schema(
                headline=title, description=description, url=url, date_published=published_at
            )
        )

    def build_product_jsonld(self, *, name: str, description: str, path: str) -> str:
        url = canonical_url(public_base_url=self._settings.public_base_url, path=path)
        return render_jsonld(product_schema(name=name, description=description, url=url))

    def build_breadcrumb_jsonld(self, *, items: list[tuple[str, str]]) -> str:
        normalized = [
            (label, canonical_url(public_base_url=self._settings.public_base_url, path=path))
            for label, path in items
        ]
        return render_jsonld(breadcrumb_schema(items=normalized))

    def build_landing_jsonld(self, *, title: str, description: str, path: str) -> str:
        url = canonical_url(public_base_url=self._settings.public_base_url, path=path)
        return render_jsonld(landing_schema(headline=title, description=description, url=url))


def _validate_entity_type(entity_type: str) -> str:
    if entity_type not in {item.value for item in EntityType}:
        raise ValidationError(f"Unknown entity type: {entity_type}.")
    return entity_type


def _entity_types_for_group(group_name: str) -> list[str] | None:
    return {
        "articles": [EntityType.ARTICLE.value],
        "categories": [EntityType.CATEGORY.value],
        "tags": [EntityType.TAG.value],
        "products": [EntityType.PRODUCT.value],
        "landing": [EntityType.LANDING.value],
        "collections": [EntityType.COLLECTION.value],
    }.get(group_name)
