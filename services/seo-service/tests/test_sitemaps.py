"""Sitemap tests: XML validity, sharding, lastmod, and private-URL prevention."""

from datetime import UTC, datetime

from atoz_seo_service.domain.sitemaps import (
    SitemapShard,
    SitemapUrl,
    render_index,
    render_shard,
    shard_urls,
    validate_no_private_urls,
    validate_xml,
)


def _urls(count: int) -> list[SitemapUrl]:
    return [
        SitemapUrl(
            loc=f"https://atozproducthub.dev/articles/guide-{index}",
            lastmod=datetime(2026, 8, 1, tzinfo=UTC),
        )
        for index in range(count)
    ]


def test_shard_urls_splits_at_limit() -> None:
    shards = shard_urls(_urls(7), max_urls=3)
    assert [len(s.urls) for s in shards] == [3, 3, 1]
    assert [s.shard_no for s in shards] == [1, 2, 3]
    assert sum(s.url_count for s in shards) == 7


def test_shard_urls_empty() -> None:
    assert shard_urls([], max_urls=10) == []


def test_render_shard_is_valid_xml() -> None:
    shard = SitemapShard(group_name="articles", shard_no=1, urls=_urls(2))
    xml = render_shard(shard)
    validate_xml(xml)
    assert "<loc>https://atozproducthub.dev/articles/guide-0</loc>" in xml
    assert "<lastmod>2026-08-01T00:00:00Z</lastmod>" in xml


def test_render_shard_escapes_xml_special_chars() -> None:
    url = SitemapUrl(loc="https://atozproducthub.dev/a?x=1&y=2")
    xml = render_shard(SitemapShard(group_name="articles", shard_no=1, urls=[url]))
    validate_xml(xml)
    assert "&amp;" in xml


def test_render_index_valid_and_lists_shards() -> None:
    xml = render_index(
        base_url="https://atozproducthub.dev",
        group_name="articles",
        shard_count=2,
        lastmod=datetime(2026, 8, 1, tzinfo=UTC),
    )
    validate_xml(xml)
    assert "/sitemaps/articles-1.xml" in xml
    assert "/sitemaps/articles-2.xml" in xml


def test_private_urls_rejected() -> None:
    xml = render_shard(
        SitemapShard(
            group_name="articles",
            shard_no=1,
            urls=[SitemapUrl(loc="https://atozproducthub.dev/admin/dashboard")],
        )
    )
    try:
        validate_no_private_urls(xml)
        raise AssertionError("expected ValidationError")
    except Exception as exc:
        assert "private" in str(exc)


def test_lastmod_w3c_format_for_naive_datetime() -> None:
    naive = datetime(2026, 8, 1, 12, 30)
    xml = render_shard(
        SitemapShard(
            group_name="products",
            shard_no=1,
            urls=[SitemapUrl(loc="https://x.dev/p", lastmod=naive)],
        )
    )
    validate_xml(xml)
    assert "<lastmod>2026-08-01T12:30:00Z</lastmod>" in xml
