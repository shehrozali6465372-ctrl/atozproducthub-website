"""Slug generation and uniqueness tests."""

from atoz_content_service.domain.slug import slugify, unique_slug


def test_slugify_lowercases_and_hyphenates() -> None:
    assert slugify("My Kitchen Guide") == "my-kitchen-guide"
    assert slugify("  10 Best Gadgets 2026! ") == "10-best-gadgets-2026"
    assert slugify("A--B___C") == "a-b-c"
    # ASCII-only policy: non-ASCII letters become separators.
    assert slugify("Ünïcode & Emoji 🔥") == "n-code-emoji"


def test_slugify_empty_falls_back() -> None:
    assert slugify("!!!") == "untitled"
    assert slugify("") == "untitled"


def test_unique_slug_first_is_free() -> None:
    assert unique_slug("kitchen", taken=set()) == "kitchen"
    assert unique_slug("kitchen", taken={"office"}) == "kitchen"


def test_unique_slug_suffixes_until_free() -> None:
    taken = {"kitchen", "kitchen-2", "kitchen-3"}
    assert unique_slug("kitchen", taken=taken) == "kitchen-4"
    assert unique_slug("kitchen", taken={"kitchen"}) == "kitchen-2"
    assert unique_slug("kitchen", taken={"kitchen", "kitchen-2"}) == "kitchen-3"
