"""Structured JSON logging tests."""

import json
import logging

from atoz_backend_core.logging import JsonFormatter, configure_logging, request_id_var


def _record(msg: str = "hello", level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord(
        name="atoz.test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )


def test_json_formatter_emits_valid_json() -> None:
    formatter = JsonFormatter(service="atoz-test", env="test")
    parsed = json.loads(formatter.format(_record("hello world")))
    assert parsed["msg"] == "hello world"
    assert parsed["service"] == "atoz-test"
    assert parsed["env"] == "test"
    assert parsed["level"] == "INFO"


def test_json_formatter_includes_extra_fields() -> None:
    formatter = JsonFormatter(service="atoz-test", env="test")
    record = _record("warn", logging.WARNING)
    record.extra_fields = {"status": 500, "path": "/x"}
    parsed = json.loads(formatter.format(record))
    assert parsed["status"] == 500
    assert parsed["path"] == "/x"


def test_json_formatter_includes_request_id() -> None:
    formatter = JsonFormatter(service="atoz-test", env="test")
    token = request_id_var.set("req-123")
    try:
        parsed = json.loads(formatter.format(_record()))
    finally:
        request_id_var.reset(token)
    assert parsed["request_id"] == "req-123"


def test_configure_logging_accepts_unknown_level() -> None:
    configure_logging("NOT_A_LEVEL", service="atoz-test", env="test")  # no crash
