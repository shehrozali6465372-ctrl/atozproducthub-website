"""Repository layer for the SEO module.

Every repository extends ``atoz_backend_core.repositories`` and enforces
Database Blueprint tenancy: all queries are scoped by ``niche_id`` so one
niche can never read or mutate another niche's SEO/search state.
"""

from collections.abc import Sequence

from sqlalchemy import delete, func, or_, select

from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork
from atoz_seo_service.domain.entities import (
    SeoCrawlReport,
    SeoHealthCheck,
    SeoMetadata,
    SeoNiche,
    SitemapShard,
    UrlRegistry,
)


class SeoNicheRepository(SqlAlchemyRepository[SeoNiche, str]):
    """Niches are a tenant-registry mirror — not niche-scoped themselves."""

    model = SeoNiche

    async def get_by_slug(self, slug: str) -> SeoNiche | None:
        result = await self._session.scalars(select(SeoNiche).where(SeoNiche.slug == slug))
        return result.first()

    async def list_by_status(self, status: str | None = None) -> Sequence[SeoNiche]:
        stmt = select(SeoNiche).order_by(SeoNiche.name)
        if status is not None:
            stmt = stmt.where(SeoNiche.status == status)
        return (await self._session.scalars(stmt)).all()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(SeoNiche.id).where(SeoNiche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(SeoNiche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None


class UrlRegistryRepository(SqlAlchemyRepository[UrlRegistry, str]):
    """URL policy rows are niche-scoped; path uniqueness is per niche."""

    model = UrlRegistry

    async def get_scoped(self, url_id: str, *, niche_id: str) -> UrlRegistry | None:
        stmt = select(UrlRegistry).where(UrlRegistry.id == url_id, UrlRegistry.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def get_by_path(self, path: str, *, niche_id: str) -> UrlRegistry | None:
        stmt = select(UrlRegistry).where(UrlRegistry.path == path, UrlRegistry.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def get_by_entity(
        self, entity_type: str, entity_id: str, *, niche_id: str
    ) -> UrlRegistry | None:
        stmt = select(UrlRegistry).where(
            UrlRegistry.niche_id == niche_id,
            UrlRegistry.entity_type == entity_type,
            UrlRegistry.entity_id == entity_id,
        )
        return (await self._session.scalars(stmt)).first()

    async def get_by_slug(self, slug: str, *, niche_id: str) -> UrlRegistry | None:
        """A slug is a niche-global URL token (service-level invariant).

        The database guarantees ``UNIQUE (niche_id, path)``; this lookup
        matches the final path segment so the same slug cannot be claimed by
        two different entities within one niche.
        """
        stmt = select(UrlRegistry).where(
            UrlRegistry.niche_id == niche_id,
            or_(
                UrlRegistry.path == f"/{slug}",
                UrlRegistry.path.like(f"%/{slug}"),
            ),
        )
        return (await self._session.scalars(stmt)).first()

    async def path_exists(self, path: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(UrlRegistry.id).where(
            UrlRegistry.path == path, UrlRegistry.niche_id == niche_id
        )
        if exclude_id is not None:
            stmt = stmt.where(UrlRegistry.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_active(
        self,
        niche_id: str,
        *,
        entity_types: Sequence[str] | None = None,
        limit: int = 5000,
        offset: int = 0,
    ) -> Sequence[UrlRegistry]:
        stmt = (
            select(UrlRegistry)
            .where(UrlRegistry.niche_id == niche_id, UrlRegistry.status == "active")
            .order_by(UrlRegistry.path)
        )
        if entity_types:
            stmt = stmt.where(UrlRegistry.entity_type.in_(entity_types))
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_active(
        self, niche_id: str, *, entity_types: Sequence[str] | None = None
    ) -> int:
        stmt = select(func.count(UrlRegistry.id)).where(
            UrlRegistry.niche_id == niche_id, UrlRegistry.status == "active"
        )
        if entity_types:
            stmt = stmt.where(UrlRegistry.entity_type.in_(entity_types))
        return int((await self._session.execute(stmt)).scalar_one())


class SeoMetadataRepository(SqlAlchemyRepository[SeoMetadata, str]):
    """Applied metadata is one-to-one with a URL registry row."""

    model = SeoMetadata

    async def get_by_url(self, url_registry_id: str, *, niche_id: str) -> SeoMetadata | None:
        stmt = select(SeoMetadata).where(
            SeoMetadata.url_registry_id == url_registry_id,
            SeoMetadata.niche_id == niche_id,
        )
        return (await self._session.scalars(stmt)).first()


class SitemapShardRepository(SqlAlchemyRepository[SitemapShard, str]):
    """Sitemap shard state is niche-scoped; (group, shard_no) is unique."""

    model = SitemapShard

    async def list_by_niche(
        self, niche_id: str, *, group_name: str | None = None
    ) -> Sequence[SitemapShard]:
        stmt = (
            select(SitemapShard)
            .where(SitemapShard.niche_id == niche_id)
            .order_by(SitemapShard.group_name, SitemapShard.shard_no)
        )
        if group_name is not None:
            stmt = stmt.where(SitemapShard.group_name == group_name)
        return (await self._session.scalars(stmt)).all()

    async def replace_group(
        self, niche_id: str, group_name: str, rows: Sequence[SitemapShard]
    ) -> None:
        """Replace a group's shards atomically within the UoW transaction."""
        await self._session.execute(
            delete(SitemapShard).where(
                SitemapShard.niche_id == niche_id, SitemapShard.group_name == group_name
            )
        )
        for row in rows:
            self._session.add(row)


class SeoCrawlReportRepository(SqlAlchemyRepository[SeoCrawlReport, str]):
    """Crawl reports are niche-scoped; (source, report_date) is unique per niche."""

    model = SeoCrawlReport

    async def list_by_niche(
        self, niche_id: str, *, source: str | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[SeoCrawlReport]:
        stmt = (
            select(SeoCrawlReport)
            .where(SeoCrawlReport.niche_id == niche_id)
            .order_by(SeoCrawlReport.report_date.desc())
        )
        if source is not None:
            stmt = stmt.where(SeoCrawlReport.source == source)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()


class SeoHealthCheckRepository(SqlAlchemyRepository[SeoHealthCheck, str]):
    """Health snapshots are niche-scoped, ordered newest first."""

    model = SeoHealthCheck

    async def list_by_niche(
        self, niche_id: str, *, check_type: str | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[SeoHealthCheck]:
        stmt = (
            select(SeoHealthCheck)
            .where(SeoHealthCheck.niche_id == niche_id)
            .order_by(SeoHealthCheck.checked_at.desc())
        )
        if check_type is not None:
            stmt = stmt.where(SeoHealthCheck.check_type == check_type)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()


class SeoUnitOfWork(SqlAlchemyUnitOfWork):
    """Transaction boundary for the SEO module repositories."""

    @classmethod
    def build(cls, session_factory) -> "SeoUnitOfWork":
        return cls(
            session_factory,
            repositories={
                "niches": SeoNicheRepository,
                "urls": UrlRegistryRepository,
                "metadata": SeoMetadataRepository,
                "shards": SitemapShardRepository,
                "crawl_reports": SeoCrawlReportRepository,
                "health_checks": SeoHealthCheckRepository,
            },
        )
