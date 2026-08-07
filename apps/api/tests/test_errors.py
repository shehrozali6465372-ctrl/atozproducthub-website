"""RFC 7807 problem+json error handling tests."""

from atoz_api.errors import AppError

PROBLEM_KEYS = {"type", "title", "status", "code", "detail", "instance", "retryable"}


def test_not_found_problem_json(client) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert PROBLEM_KEYS.issubset(body.keys())
    assert body["code"] == "NOT_FOUND"
    assert body["retryable"] is False


def test_validation_error_problem_json(app, client) -> None:
    @app.get("/probe/{value}")
    def probe(value: int) -> dict[str, int]:
        return {"value": value}

    response = client.get("/probe/not-a-number")
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_FAILED"
    assert body["status"] == 422


def test_app_error_problem_json(app, client) -> None:
    @app.get("/boom")
    def boom() -> dict[str, str]:
        raise AppError(502, "BAD_GATEWAY", "upstream failed", retryable=True)

    response = client.get("/boom")
    assert response.status_code == 502
    body = response.json()
    assert body["code"] == "BAD_GATEWAY"
    assert body["retryable"] is True


def test_unhandled_error_problem_json(app, client) -> None:
    @app.get("/crash")
    def crash() -> dict[str, str]:
        raise RuntimeError("boom")

    response = client.get("/crash")
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["retryable"] is True
