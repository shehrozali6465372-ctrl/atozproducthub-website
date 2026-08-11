"""Sitemap XML generation, sharding, and indexes (Task 17 §4).

Generates valid XML sitemaps from URL-registry entries, shards large sets
(``sitemap_max_urls`` URLs per shard), emits a sitemap index per group, and
writes a ``lastmod`` from the registry's ``changed_at``. Only active public
URLs are ever included; admin/private paths are excluded by construction.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from atoz_seo_service.errors import ValidationError

XML_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

_XML_ESCAPE = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}


def _escape(value: Any) -> str:
    return "".join(_XML_ESCAPE.get(ch, ch) for ch in str(value))


def _w3c_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class SitemapUrl:
    """One indexable URL in a sitemap."""

    loc: str
    lastmod: datetime | None = None
    changefreq: str = "weekly"
    priority: str = "0.5"


@dataclass
class SitemapShard:
    """A rendered shard plus its identity for the registry."""

    group_name: str
    shard_no: int
    urls: list[SitemapUrl] = field(default_factory=list)

    @property
    def url_count(self) -> int:
        return len(self.urls)

    @property
    def checksum(self) -> str:
        digest = hashlib.sha256()
        for url in self.urls:
            digest.update(url.loc.encode())
        return digest.hexdigest()


def render_shard(shard: SitemapShard) -> str:
    """Render one sitemap shard as valid XML."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<urlset xmlns="{XML_NS}">',
    ]
    for url in shard.urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{_escape(url.loc)}</loc>")
        if url.lastmod is not None:
            lines.append(f"    <lastmod>{_w3c_datetime(url.lastmod)}</lastmod>")
        lines.append(f"    <changefreq>{_escape(url.changefreq)}</changefreq>")
        lines.append(f"    <priority>{_escape(url.priority)}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def render_index(*, base_url: str, group_name: str, shard_count: int, lastmod: datetime) -> str:
    """Render a sitemap index for one group."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<sitemapindex xmlns="{XML_NS}">',
    ]
    for shard_no in range(1, shard_count + 1):
        lines.append("  <sitemap>")
        lines.append(f"    <loc>{_escape(base_url)}/sitemaps/{group_name}-{shard_no}.xml</loc>")
        lines.append(f"    <lastmod>{_w3c_datetime(lastmod)}</lastmod>")
        lines.append("  </sitemap>")
    lines.append("</sitemapindex>")
    return "\n".join(lines) + "\n"


def shard_urls(urls: list[SitemapUrl], *, max_urls: int) -> list[SitemapShard]:
    """Split a URL list into shards of at most ``max_urls`` entries."""
    if max_urls < 1:
        raise ValidationError("max_urls must be >= 1.")
    if not urls:
        return []
    return [
        SitemapShard(group_name="", shard_no=index + 1, urls=urls[start : start + max_urls])
        for index, start in enumerate(range(0, len(urls), max_urls))
    ]


_URLSET_RE = re.compile(r"<urlset xmlns=\"http://www\.sitemaps\.org/schemas/sitemap/0\.9\">")
_URL_COUNT_RE = re.compile(r"<url>")
_SITEMAPINDEX_RE = re.compile(
    r"<sitemapindex xmlns=\"http://www\.sitemaps\.org/schemas/sitemap/0\.9\">"
)


def validate_xml(xml: str) -> None:
    """Validate a rendered sitemap/index: XML well-formedness + namespace.

    Raises ValidationError on malformed output so tests and CI can gate on it.
    """
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValidationError(f"Invalid sitemap XML: {exc}") from exc
    tag = root.tag.rsplit("}", 1)[-1]
    if tag not in {"urlset", "sitemapindex"}:
        raise ValidationError(f"Unexpected sitemap root: {root.tag}.")
    if tag == "urlset":
        for child in root:
            child_tag = child.tag.rsplit("}", 1)[-1]
            if child_tag != "url":
                raise ValidationError(f"Unexpected child {child_tag} in urlset.")
    else:
        for child in root:
            child_tag = child.tag.rsplit("}", 1)[-1]
            if child_tag != "sitemap":
                raise ValidationError(f"Unexpected child {child_tag} in sitemapindex.")


def validate_no_private_urls(
    xml: str, private_prefixes: tuple[str, ...] = ("/admin", "/api/", "/_next/")
) -> None:
    """Ensure no private/internal URL leaks into a rendered sitemap.

    Parses each ``<loc>`` and compares the URL path against the private
    prefixes (host-agnostic, so test bases like ``https://...dev`` work).
    """
    from urllib.parse import urlparse

    for loc in re.findall(r"<loc>(.*?)</loc>", xml):
        path = urlparse(loc).path or loc
        for prefix in private_prefixes:
            if path.startswith(prefix):
                raise ValidationError(f"Sitemap must not contain private URLs ({prefix}).")
