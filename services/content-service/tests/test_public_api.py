"""Public Read API tests: published-only, niche-slug tenancy, RFC 7807."""

import asyncio

from .fixtures import api_client, build_app


def _run(coro):
    return asyncio.run(coro)


async def _seed(svc) -> None:
    """Create an active niche with one published article, category, and tag."""
    niche = await svc.create_niche(name="Kitchen", slug="kitchen")
    await svc.update_niche(niche.id, status="active")
    category = await svc.create_category(niche.id, name="Cookware", slug="cookware")
    tag = await svc.create_tag(niche.id, name="Guide", slug="guide")
    article = await svc.create_article(
        niche.id,
        title="Kitchen Guide",
        excerpt="Excerpt here",
        body="First paragraph.\n\nSecond paragraph.",
        category_ids=[category.id],
        primary_category_id=category.id,
        tag_ids=[tag.id],
    )
    await svc.transition(niche.id, article.id, "publish", actor="alice")
    draft = await svc.create_article(niche.id, title="Hidden Draft", body="x")
    await svc.transition(niche.id, draft.id, "submit", actor="alice")


def test_public_niches_and_articles_flow() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            svc = app.state.content_service
            await _seed(svc)
            async with await api_client(app) as client:
                niches = (await client.get("/api/v1/public/niches")).json()
                assert [n["slug"] for n in niches] == ["kitchen"]

                listing = (await client.get("/api/v1/public/articles?niche=kitchen")).json()
                assert listing["total"] == 1
                item = listing["items"][0]
                assert item["slug"] == "kitchen-guide"
                assert item["category"] == {
                    "slug": "cookware",
                    "name": "Cookware",
                    "description": "",
                }
                assert item["tags"] == [{"slug": "guide", "name": "Guide"}]
                assert item["read_time_minutes"] >= 1
                assert item["body"] == ["First paragraph.", "Second paragraph."]

                detail = (
                    await client.get("/api/v1/public/articles/kitchen-guide?niche=kitchen")
                ).json()
                assert detail["title"] == "Kitchen Guide"
                assert detail["published_at"]

                categories = (await client.get("/api/v1/public/categories?niche=kitchen")).json()
                assert [c["slug"] for c in categories] == ["cookware"]
                tags = (await client.get("/api/v1/public/tags?niche=kitchen")).json()
                assert [t["slug"] for t in tags] == ["guide"]
        finally:
            await engine.dispose()

    _run(scenario())


def test_public_only_shows_published() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            svc = app.state.content_service
            await _seed(svc)
            async with await api_client(app) as client:
                response = await client.get("/api/v1/public/articles/hidden-draft?niche=kitchen")
                assert response.status_code == 404
                body = response.json()
                assert body["code"] == "NOT_FOUND"
                assert body["status"] == 404
                assert body["type"].startswith("https://atozproducthub.dev/errors/")
                assert body["instance"]
        finally:
            await engine.dispose()

    _run(scenario())


def test_public_requires_active_niche() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            svc = app.state.content_service
            await svc.create_niche(name="Draft Niche", slug="drafty")
            async with await api_client(app) as client:
                missing = await client.get("/api/v1/public/articles")
                assert missing.status_code == 422
                assert missing.json()["code"] == "UNSUPPORTED_NICHE"

                unknown = await client.get("/api/v1/public/articles?niche=nope")
                assert unknown.status_code == 422
                assert unknown.json()["code"] == "UNSUPPORTED_NICHE"

                inactive = await client.get("/api/v1/public/articles?niche=drafty")
                assert inactive.status_code == 422
                assert inactive.json()["code"] == "UNSUPPORTED_NICHE"
        finally:
            await engine.dispose()

    _run(scenario())


def test_public_filters_and_pagination_caps() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            svc = app.state.content_service
            await _seed(svc)
            async with await api_client(app) as client:
                by_category = await client.get(
                    "/api/v1/public/articles?niche=kitchen&category=cookware"
                )
                assert by_category.json()["total"] == 1
                none_cat = await client.get("/api/v1/public/articles?niche=kitchen&category=nope")
                assert none_cat.json()["total"] == 0
                by_tag = await client.get("/api/v1/public/articles?niche=kitchen&tag=guide")
                assert by_tag.json()["total"] == 1

                capped = await client.get("/api/v1/public/articles?niche=kitchen&page_size=9999")
                assert capped.json()["page_size"] == 100
                paged = await client.get("/api/v1/public/articles?niche=kitchen&page=2&page_size=1")
                assert paged.json()["page"] == 2
                assert paged.json()["total"] == 1
        finally:
            await engine.dispose()

    _run(scenario())


def test_public_validation_error_shape() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            svc = app.state.content_service
            await _seed(svc)
            async with await api_client(app) as client:
                response = await client.get("/api/v1/public/articles?niche=kitchen&page=abc")
                assert response.status_code == 422
                body = response.json()
                assert body["code"] == "VALIDATION_FAILED"
                assert body["retryable"] is False
                assert body["instance"] == "/api/v1/public/articles"
        finally:
            await engine.dispose()

    _run(scenario())
