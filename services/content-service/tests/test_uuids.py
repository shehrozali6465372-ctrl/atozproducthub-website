"""UUID v7 generation tests."""

from atoz_content_service.uuids import uuid7


def test_uuid7_shape_and_version() -> None:
    value = uuid7()
    assert len(value) == 36
    assert value[14] == "7"  # RFC 9562 version nibble
    assert value[19] in "89ab"  # RFC 4122 variant


def test_uuid7_unique_and_monotonic() -> None:
    values = sorted(uuid7() for _ in range(1000))
    assert len(set(values)) == 1000
    assert values == sorted(values)


def test_uuid7_is_time_ordered() -> None:
    first, second = uuid7(), uuid7()
    assert second > first
