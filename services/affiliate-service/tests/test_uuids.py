"""UUID v7 generation tests (backend-core re-export)."""

from atoz_affiliate_service.uuids import uuid7


def test_uuid7_shape_and_version() -> None:
    value = uuid7()
    assert len(value) == 36
    assert value[14] == "7"
    assert value[19] in "89ab"


def test_uuid7_unique_and_monotonic() -> None:
    values = sorted(uuid7() for _ in range(500))
    assert len(set(values)) == 500
    assert values == sorted(values)
