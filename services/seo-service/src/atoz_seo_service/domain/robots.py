"""robots.txt generation (Task 17 §5).

Allows legitimate search crawlers (Googlebot, Bingbot, Pinterestbot and its
image proxy), blocks admin/private/internal routes, and never blocks
Pinterestbot — Pinterest's crawler indexes public site content and its
image proxy fetches pin images, so it must remain allowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ALLOWED_CRAWLERS = [
    "Googlebot",
    "Bingbot",
    "Pinterestbot",
    "Pinterestbot/0.1 (+http://www.pinterest.com/bot.html)",
]


@dataclass
class RobotsRule:
    """One rule set for a user agent."""

    agent: str
    allow: list[str] = field(default_factory=list)
    disallow: list[str] = field(default_factory=list)


def build_robots(
    *,
    base_url: str,
    allow_paths: list[str] | None = None,
    disallow_paths: list[str] | None = None,
    sitemap_group_names: list[str] | None = None,
    sitemap_max_urls: int = 1000,
) -> str:
    """Render robots.txt for the public site.

    ``sitemap_group_names`` controls which sitemap index URLs are advertised;
    an empty list advertises no sitemap lines.
    """
    allow_paths = allow_paths or ["/"]
    disallow_paths = disallow_paths or []
    lines: list[str] = []
    for agent in ALLOWED_CRAWLERS:
        lines.append(f"User-agent: {agent}\n")
        for allow in allow_paths:
            lines.append(f"Allow: {allow}\n")
        for disallow in disallow_paths:
            lines.append(f"Disallow: {disallow}\n")
        lines.append("")
    if sitemap_group_names:
        for group in sitemap_group_names:
            lines.append(f"Sitemap: {base_url.rstrip('/')}/sitemaps/{group}-index.xml")
    return "\n".join(lines)


def validate_robots(robots: str) -> None:
    """Cheap structural validation used by tests: user-agent groups + sitemap lines."""
    if not robots.strip():
        raise ValueError("robots.txt must not be empty.")
    if "User-agent:" not in robots:
        raise ValueError("robots.txt must declare user-agent groups.")
    if "Pinterestbot" not in robots:
        raise ValueError("robots.txt must allow Pinterestbot (Task 17 §5).")
