"""Admin Content API tests: authz, tenancy header, CRUD, lifecycle, versions."""

import asyncio

from .fixtures import access_token, api_client, build_app


def _run(coro):
    return asyncio.run(coro)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _seed(app, niche_slug: str = "kitchen") -> tuple[dict[str, str], str, str, str, str, str]:
    """Create niche + category + tag + draft article; return ids and token."""
    svc = app.state.content_service
    niche = await svc.create_niche(name="Kitchen", slug=niche_slug)
    await svc.update_niche(niche.id, status="active")
    category = await svc.create_category(niche.id, name="Cookware", slug="cookware")
    tag = await svc.create_tag(niche.id, name="Guide", slug="guide")
    article = await svc.create_article(
        niche.id,
        title="Kitchen Guide",
        excerpt="E",
        body="Body one.",
        category_ids=[category.id],
        primary_category_id=category.id,
        tag_ids=[tag.id],
    )
    token = access_token()
    return (
        {"X-Niche-Id": niche.id, **_auth(token)},
        token,
        niche.id,
        article.id,
        category.id,
        tag.id,
    )


def test_admin_requires_auth_and_permissions() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers, token, niche_id, article_id, category_id, tag_id = await _seed(app)
            async with await api_client(app) as client:
                # No token.
                response = await client.get("/api/v1/admin/articles")
                assert response.status_code == 401
                assert response.json()["code"] == "UNAUTHENTICATED"

                # Invalid token.
                response = await client.get(
                    "/api/v1/admin/articles", headers={"Authorization": "Bearer garbage"}
                )
                assert response.status_code == 401

                # Token without the required permission.
                reader_only = access_token(permissions=("content:read",))
                response = await client.post(
                    "/api/v1/admin/articles",
                    headers={**headers, **_auth(reader_only)},
                    json={"title": "Nope", "body": "x"},
                )
                assert response.status_code == 403
                assert response.json()["code"] == "FORBIDDEN"

                # Valid token + permission succeeds.
                response = await client.get("/api/v1/admin/articles", headers=headers)
                assert response.status_code == 200
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_requires_niche_header() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers, token, *_ = await _seed(app)
            async with await api_client(app) as client:
                missing = await client.get("/api/v1/admin/articles", headers=_auth(token))
                assert missing.status_code == 422
                assert missing.json()["code"] == "VALIDATION_FAILED"

                invalid = await client.get(
                    "/api/v1/admin/articles",
                    headers={**_auth(token), "X-Niche-Id": "not-a-uuid"},
                )
                assert invalid.status_code == 422

                unknown = await client.get(
                    "/api/v1/admin/articles",
                    headers={**_auth(token), "X-Niche-Id": "00000000-0000-0000-0000-000000000000"},
                )
                assert unknown.status_code == 422
                assert unknown.json()["code"] == "UNSUPPORTED_NICHE"
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_article_crud_and_lifecycle() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers, token, niche_id, article_id, category_id, tag_id = await _seed(app)
            async with await api_client(app) as client:
                # Create a draft.
                created = await client.post(
                    "/api/v1/admin/articles",
                    headers=headers,
                    json={
                        "title": "Second Guide",
                        "excerpt": "Ex",
                        "body": "Fresh body.",
                        "category_ids": [category_id],
                        "primary_category_id": category_id,
                        "tag_ids": [tag_id],
                        "change_summary": "first draft",
                    },
                )
                assert created.status_code == 201
                created_body = created.json()
                assert created_body["status"] == "draft"
                assert created_body["slug"] == "second-guide"
                assert created_body["content_checksum"]

                # Submit -> approve.
                submitted = await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "submit"},
                )
                assert submitted.status_code == 200
                assert submitted.json()["status"] == "review"
                approved = await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "approve"},
                )
                assert approved.json()["status"] == "published"
                assert approved.json()["author_ref"] == "tester"

                # Invalid transition -> 422 VALIDATION_FAILED.
                invalid = await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "submit"},
                )
                assert invalid.status_code == 422
                assert invalid.json()["code"] == "VALIDATION_FAILED"

                # Update while published -> snapshot stays (checksum unchanged),
                # a new version is created, and the public page still serves
                # the old published body.
                updated = await client.patch(
                    f"/api/v1/admin/articles/{created_body['id']}",
                    headers=headers,
                    json={"body": "Edited body.", "change_summary": "edit"},
                )
                assert updated.json()["content_checksum"] == approved.json()["content_checksum"]

                versions = await client.get(
                    f"/api/v1/admin/articles/{created_body['id']}/versions", headers=headers
                )
                assert versions.json()["total"] == 2

                public = await client.get("/api/v1/public/articles/second-guide?niche=kitchen")
                assert public.json()["body"] == ["Fresh body."]

                # Re-publish applies the latest draft version.
                republished = await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "publish"},
                )
                assert republished.status_code == 200
                assert republished.json()["content_checksum"] != approved.json()["content_checksum"]

                # Unpublish -> archive -> restore -> delete.
                await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "unpublish"},
                )
                await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "archive"},
                )
                await client.post(
                    f"/api/v1/admin/articles/{created_body['id']}/lifecycle",
                    headers=headers,
                    json={"action": "restore"},
                )
                deleted = await client.delete(
                    f"/api/v1/admin/articles/{created_body['id']}", headers=headers
                )
                assert deleted.status_code == 204
                gone = await client.get(
                    f"/api/v1/admin/articles/{created_body['id']}", headers=headers
                )
                assert gone.status_code == 404
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_tenancy_isolation_across_http() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers_a, token_a, niche_a, article_a, category_a, tag_a = await _seed(app, "kitchen")
            svc = app.state.content_service
            niche_b = await svc.create_niche(name="Travel", slug="travel")
            await svc.update_niche(niche_b.id, status="active")
            headers_b = {
                "X-Niche-Id": niche_b.id,
                **{"Authorization": headers_a["Authorization"]},
            }
            async with await api_client(app) as client:
                # Cross-niche reads 404.
                response = await client.get(
                    f"/api/v1/admin/articles/{article_a}", headers=headers_b
                )
                assert response.status_code == 404
                # Cross-niche updates 404.
                response = await client.patch(
                    f"/api/v1/admin/articles/{article_a}",
                    headers=headers_b,
                    json={"title": "Hacked"},
                )
                assert response.status_code == 404
                # Cross-niche lifecycle 404.
                response = await client.post(
                    f"/api/v1/admin/articles/{article_a}/lifecycle",
                    headers=headers_b,
                    json={"action": "publish"},
                )
                assert response.status_code == 404
                # Lists never mix.
                listing_b = await client.get("/api/v1/admin/articles", headers=headers_b)
                assert listing_b.json()["total"] == 0
                # Same slug is fine in both niches.
                created_b = await client.post(
                    "/api/v1/admin/articles",
                    headers=headers_b,
                    json={"title": "Kitchen Guide", "body": "other"},
                )
                assert created_b.status_code == 201
                assert created_b.json()["slug"] == "kitchen-guide"
                # Cross-niche taxonomy ids are rejected.
                rejected = await client.post(
                    "/api/v1/admin/articles",
                    headers=headers_b,
                    json={"title": "Bad", "body": "x", "category_ids": [category_a]},
                )
                assert rejected.status_code == 422
                assert rejected.json()["code"] == "VALIDATION_FAILED"
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_slug_conflict_returns_duplicate() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers, token, niche_id, article_id, category_id, tag_id = await _seed(app)
            async with await api_client(app) as client:
                response = await client.post(
                    "/api/v1/admin/articles",
                    headers=headers,
                    json={"title": "Kitchen Guide", "slug": "kitchen-guide", "body": "x"},
                )
                assert response.status_code == 409
                assert response.json()["code"] == "DUPLICATE"
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_niche_and_taxonomy_management() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers, token, niche_id, article_id, category_id, tag_id = await _seed(app)
            async with await api_client(app) as client:
                niches = await client.get("/api/v1/admin/niches", headers=headers)
                assert len(niches.json()) == 1

                updated_niche = await client.patch(
                    f"/api/v1/admin/niches/{niche_id}",
                    headers=headers,
                    json={"status": "active"},
                )
                assert updated_niche.json()["status"] == "active"

                categories = await client.get("/api/v1/admin/categories", headers=headers)
                assert [c["slug"] for c in categories.json()] == ["cookware"]
                new_category = await client.post(
                    "/api/v1/admin/categories",
                    headers=headers,
                    json={"name": "Gadgets", "slug": "gadgets"},
                )
                assert new_category.status_code == 201

                tags = await client.get("/api/v1/admin/tags", headers=headers)
                assert [t["slug"] for t in tags.json()] == ["guide"]
                new_tag = await client.post(
                    "/api/v1/admin/tags",
                    headers=headers,
                    json={"name": "Roundup", "slug": "roundup"},
                )
                assert new_tag.status_code == 201

                # Deleting a linked category conflicts.
                blocked = await client.delete(
                    f"/api/v1/admin/categories/{category_id}", headers=headers
                )
                assert blocked.status_code == 409
                # Deleting an unlinked category works.
                freed = await client.delete(
                    f"/api/v1/admin/categories/{new_category.json()['id']}", headers=headers
                )
                assert freed.status_code == 204
                freed_tag = await client.delete(
                    f"/api/v1/admin/tags/{new_tag.json()['id']}", headers=headers
                )
                assert freed_tag.status_code == 204
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_validation_and_not_found_codes() -> None:
    async def scenario() -> None:
        app, engine, store, bus, events = await build_app()
        try:
            headers, token, niche_id, article_id, category_id, tag_id = await _seed(app)
            async with await api_client(app) as client:
                bad_payload = await client.post(
                    "/api/v1/admin/articles", headers=headers, json={"title": ""}
                )
                assert bad_payload.status_code == 422
                assert bad_payload.json()["code"] == "VALIDATION_FAILED"

                missing = await client.get(
                    "/api/v1/admin/articles/00000000-0000-0000-0000-000000000000",
                    headers=headers,
                )
                assert missing.status_code == 404

                bad_lifecycle = await client.post(
                    f"/api/v1/admin/articles/{article_id}/lifecycle",
                    headers=headers,
                    json={"action": "explode"},
                )
                assert bad_lifecycle.status_code == 422

                # Unknown lifecycle action fails at schema level (422).
                assert bad_lifecycle.json()["code"] == "VALIDATION_FAILED"
        finally:
            await engine.dispose()

    _run(scenario())
