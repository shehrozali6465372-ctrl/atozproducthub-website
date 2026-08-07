"""Structured logging tests."""

import json
import logging

from atoz_api.logging import JsonFormatter


def test_json_formatter_emits_valid_json() -> None:
    formatter = JsonFormatter(service="atoz-api", env="test")
    record = logging.LogRecord(
        name="atoz.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    parsed = json.loads(formatter.format(record))
    assert parsed["msg"] == "hello world"
    assert parsed["service"] == "atoz-api"
    assert parsed["env"] == "test"
    assert parsed["level"] == "INFO"


def test_json_formatter_includes_extra_fields() -> None:
    formatter = JsonFormatter(service="atoz-api", env="test")
    record = logging.LogRecord(
        name="atoz.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="warn",
        args=None,
        exc_info=None,
    )
    record.extra_fields = {"request_id": "abc", "status": 500}
    parsed = json.loads(formatter.format(record))
    assert parsed["request_id"] == "abc"
    assert parsed["status"] == 500
