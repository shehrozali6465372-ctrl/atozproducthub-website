"""UUID v7 generation (time-ordered) for automation-service primary keys."""

import os
import time

_UUID7_EPOCH_OFFSET = 0x01B21DD213814000


def uuid7() -> str:
    """Return a UUIDv7 string: 48-bit ms timestamp + random bits (RFC 9562)."""
    timestamp_ms = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), "big")
    rand_b = int.from_bytes(os.urandom(6), "big")
    value = (
        ((timestamp_ms + _UUID7_EPOCH_OFFSET) & 0xFFFFFFFFFFFFFFFF) << 80
        | (0x7 << 76)
        | (rand_a & 0x0FFF) << 64
        | (0x80 << 56)
        | rand_b
    )
    hex_str = f"{value:032x}"
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"
