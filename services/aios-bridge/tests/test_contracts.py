"""Contract validation tests (frozen v1 schemas in libs/contracts/aios/)."""

import pytest

from atoz_aios_bridge.contracts import AiosContractValidator, BridgeContractError

VALID_JOB_REQUEST = {
    "request_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
    "job_type": "pinterest_assets",
    "niche_id": "b8f5f167-f44f-4a01-a0f8-9d4f0d8a7b2f",
    "context": {"pin_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"},
    "callback": {
        "url": "https://atozproducthub.dev/webhooks/aios/job-status",
        "event_contract": "aios.job.status.v1",
    },
}


def test_contracts_dir_resolves_to_libs_contracts_aios() -> None:
    validator = AiosContractValidator()
    assert validator.contracts_dir().name == "aios"
    assert "job-request" in validator.available_contracts()
    assert "heartbeat" in validator.available_contracts()


def test_valid_job_request_passes() -> None:
    validator = AiosContractValidator()
    result = validator.validate("job-request", VALID_JOB_REQUEST)
    assert result["job_type"] == "pinterest_assets"


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: p.pop("request_id"),
        lambda p: p.__setitem__("job_type", "unknown_type"),
        lambda p: p.pop("callback"),
    ],
)
def test_invalid_job_request_rejected(mutator) -> None:
    payload = dict(VALID_JOB_REQUEST)
    mutator(payload)
    with pytest.raises(BridgeContractError):
        AiosContractValidator().validate("job-request", payload)


def test_valid_heartbeat_passes() -> None:
    validator = AiosContractValidator()
    assert validator.validate("heartbeat", {"status": "ok", "latency_ms": 12.5})["status"] == "ok"


def test_invalid_heartbeat_rejected() -> None:
    with pytest.raises(BridgeContractError):
        AiosContractValidator().validate("heartbeat", {"status": "degraded"})
