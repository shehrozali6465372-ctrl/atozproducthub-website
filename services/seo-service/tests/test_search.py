"""Search index tests: niche isolation, indexing/de-indexing, pagination."""

from datetime import UTC, datetime

from atoz_seo_service.domain.search import InMemorySearchIndex, SearchDocument

from .fixtures import scenario


def _doc(
    index: int, *, niche: str = "n-1", doc_type: str = "article", title: str = ""
) -> SearchDocument:
    return SearchDocument(
        id=f"id-{index}",
        type=doc_type,
        niche_id=niche,
        slug=f"slug-{index}",
        title=title or f"Title {index}",
        excerpt=f"Excerpt {index}",
        url=f"/articles/slug-{index}",
        tags=["kitchen", "gear"],
        updated_at=datetime(2026, 8, 1, tzinfo=UTC),
    )


def test_index_search_and_delete() -> None:
    async def runner() -> None:
        index = InMemorySearchIndex()
        await index.ensure_collection()
        await index.upsert(_doc(1, title="Kitchen gadgets"))
        page = await index.search(query="kitchen", niche_id="n-1")
        assert page.total == 1
        assert page.items[0].title == "Kitchen gadgets"
        removed = await index.delete("id-1", niche_id="n-1")
        assert removed is True
        assert (await index.search(query="kitchen", niche_id="n-1")).total == 0

    scenario(runner)


def test_search_never_leaks_across_niches() -> None:
    async def runner() -> None:
        index = InMemorySearchIndex()
        await index.upsert(_doc(1, niche="n-1", title="Kitchen guide"))
        await index.upsert(_doc(2, niche="n-2", title="Travel guide"))
        page_a = await index.search(query="guide", niche_id="n-1")
        page_b = await index.search(query="guide", niche_id="n-2")
        assert [h.id for h in page_a.items] == ["id-1"]
        assert [h.id for h in page_b.items] == ["id-2"]
        # Delete in one niche never touches the other.
        await index.delete("id-1", niche_id="n-1")
        assert (await index.search(query="guide", niche_id="n-2")).total == 1

    scenario(runner)


def test_search_type_filter() -> None:
    async def runner() -> None:
        index = InMemorySearchIndex()
        await index.upsert(_doc(1, doc_type="article", title="Cast iron"))
        await index.upsert(_doc(2, doc_type="product", title="Cast iron pan"))
        page = await index.search(query="cast iron", niche_id="n-1", types=["product"])
        assert [h.id for h in page.items] == ["id-2"]
        assert page.total == 1

    scenario(runner)


def test_search_pagination() -> None:
    async def runner() -> None:
        index = InMemorySearchIndex()
        for number in range(7):
            await index.upsert(_doc(number, title=f"Guide {number}"))
        page1 = await index.search(query="guide", niche_id="n-1", page=1, page_size=3)
        page2 = await index.search(query="guide", niche_id="n-1", page=3, page_size=3)
        assert page1.total == 7
        assert len(page1.items) == 3
        assert len(page2.items) == 1

    scenario(runner)


def test_search_empty_query_returns_all_in_niche() -> None:
    async def runner() -> None:
        index = InMemorySearchIndex()
        await index.upsert(_doc(1, title="Alpha"))
        await index.upsert(_doc(2, title="Beta"))
        page = await index.search(query="", niche_id="n-1")
        assert page.total == 2

    scenario(runner)
