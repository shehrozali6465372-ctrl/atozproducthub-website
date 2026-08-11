"""robots.txt tests (Task 17 §5).

Crawlers allowed, admin blocked, Pinterestbot + image proxy never blocked.
"""

from atoz_seo_service.domain.robots import build_robots, validate_robots


def test_robots_allows_legitimate_crawlers_and_blocks_admin() -> None:
    robots = build_robots(
        base_url="https://atozproducthub.dev",
        allow_paths=["/", "/articles/", "/products/"],
        disallow_paths=["/admin", "/api/", "/search"],
        sitemap_group_names=["articles", "products"],
        sitemap_max_urls=1000,
    )
    validate_robots(robots)
    assert "User-agent: Googlebot" in robots
    assert "User-agent: Bingbot" in robots
    assert "User-agent: Pinterestbot" in robots
    assert "Disallow: /admin" in robots
    assert "Disallow: /api/" in robots
    assert "Sitemap: https://atozproducthub.dev/sitemaps/articles-index.xml" in robots


def test_robots_never_blocks_pinterestbot_or_image_proxy() -> None:
    robots = build_robots(base_url="https://atozproducthub.dev", disallow_paths=["/admin"])
    # Pinterestbot must be explicitly allowed (Pinterest indexes public
    # content; its image proxy fetches pin images — never block it).
    pinterest_group = robots.split("User-agent: Pinterestbot")[1].split("User-agent:")[0]
    assert "Disallow: /admin" in pinterest_group
    assert not any(line.strip() == "Disallow: /" for line in pinterest_group.splitlines())
    # No blanket Pinterestbot disallow anywhere in the file.
    assert not any(
        line.startswith("Disallow: /") and line.strip() == "Disallow: /"
        for line in pinterest_group.splitlines()
    )


def test_robots_without_pinterestbot_is_invalid() -> None:
    robots = "User-agent: Googlebot\nDisallow: /admin\n"
    try:
        validate_robots(robots)
        raise AssertionError("expected failure")
    except ValueError as exc:
        assert "Pinterestbot" in str(exc)
