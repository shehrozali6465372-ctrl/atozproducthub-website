"""AI OS contract loading and validation (libs/contracts/aios/).

The Bridge validates every outbound request and every inbound payload
against the frozen v1 JSON Schemas before anything is forwarded.
"""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CONTRACT_FILES = {
    "content-intake": "content-intake.schema.json",
    "job-request": "job-request.schema.json",
    "job-status": "job-status.schema.json",
    "seo-metadata": "seo-metadata.schema.json",
    "pinterest-assets": "pinterest-assets.schema.json",
    "analytics-insights": "analytics-insights.schema.json",
    "heartbeat": "heartbeat.schema.json",
}


class BridgeContractError(ValueError):
    """Raised when a payload violates its frozen AI OS contract."""


def default_contracts_dir() -> Path:
    """Locate ``libs/contracts/aios`` from the source checkout.

    In installed (non-source) contexts, set ``AIOS_CONTRACTS_DIR`` to the
    deployed contracts directory.
    """
    here = Path(__file__).resolve()
    candidate = here.parents[4] / "libs" / "contracts" / "aios"
    return candidate


def _load_schema(contracts_dir: Path, contract: str) -> dict[str, Any]:
    filename = CONTRACT_FILES.get(contract)
    if filename is None:
        raise BridgeContractError(f"unknown AI OS contract: {contract!r}")
    path = contracts_dir / filename
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise BridgeContractError(
            f"contract schema not found: {path} (set AIOS_CONTRACTS_DIR)"
        ) from exc


class AiosContractValidator:
    """Validate payloads against the frozen AI OS contract schemas."""

    def __init__(self, contracts_dir: str | Path | None = None) -> None:
        self._dir = Path(contracts_dir) if contracts_dir else default_contracts_dir()
        self._validators: dict[str, Draft202012Validator] = {}

    def _validator(self, contract: str) -> Draft202012Validator:
        validator = self._validators.get(contract)
        if validator is None:
            validator = Draft202012Validator(_load_schema(self._dir, contract))
            self._validators[contract] = validator
        return validator

    def validate(self, contract: str, payload: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(self._validator(contract).iter_errors(payload), key=lambda e: list(e.path))
        if errors:
            first = errors[0]
            raise BridgeContractError(
                f"{contract} validation failed at {list(first.path) or '$'}: {first.message}"
            )
        return payload

    def contracts_dir(self) -> Path:
        return self._dir

    def available_contracts(self) -> list[str]:
        return sorted(
            name for name in CONTRACT_FILES if (self._dir / CONTRACT_FILES[name]).exists()
        )
