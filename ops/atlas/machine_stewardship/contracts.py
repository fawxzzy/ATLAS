from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from ops.atlas.ui_standards.validate import validate_json_schema

ATLAS_ROOT = Path(__file__).resolve().parents[3]

CONTRACT_SCHEMA_PATHS: dict[str, Path] = {
    "atlas.machine-observed-state.v1": Path("schemas/atlas.machine-observed-state.v1.json"),
    "atlas.machine-desired-state.v1": Path("schemas/atlas.machine-desired-state.v1.json"),
    "atlas.machine-action-proposal.v1": Path("schemas/atlas.machine-action-proposal.v1.json"),
    "atlas.machine-execution-receipt.v1": Path("schemas/atlas.machine-execution-receipt.v1.json"),
    "atlas.machine-policy.v1": Path("schemas/atlas.machine-policy.v1.json"),
}

OBSERVED_STATE_VOLATILE_FIELDS = ("/collected_at_utc", "/observation_id")


class ContractValidationError(ValueError):
    """Raised when a machine-stewardship document violates its versioned contract."""

    def __init__(self, contract_version: str, errors: list[str]) -> None:
        self.contract_version = contract_version
        self.errors = tuple(errors)
        super().__init__(f"{contract_version} validation failed: {'; '.join(errors)}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic compact UTF-8 JSON bytes with array order preserved."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@lru_cache(maxsize=len(CONTRACT_SCHEMA_PATHS))
def load_schema(contract_version: str) -> dict[str, Any]:
    relative_path = CONTRACT_SCHEMA_PATHS.get(contract_version)
    if relative_path is None:
        raise ValueError(f"Unsupported machine contract version: {contract_version!r}")
    payload = json.loads((ATLAS_ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Schema {relative_path.as_posix()} must contain a JSON object.")
    return payload


def validate_contract(
    document: Mapping[str, Any],
    *,
    expected_contract_version: str | None = None,
) -> list[str]:
    """Return stable validation errors without mutating the supplied document."""

    contract_version = document.get("contract_version")
    if not isinstance(contract_version, str):
        return ["$.contract_version: must identify a supported machine contract"]
    if expected_contract_version is not None and contract_version != expected_contract_version:
        return [
            "$.contract_version: "
            f"expected {expected_contract_version!r}, received {contract_version!r}"
        ]
    try:
        schema = load_schema(contract_version)
    except ValueError as exc:
        return [f"$.contract_version: {exc}"]
    return sorted(validate_json_schema(dict(document), schema))


def require_valid_contract(
    document: Mapping[str, Any],
    *,
    expected_contract_version: str | None = None,
) -> None:
    errors = validate_contract(
        document,
        expected_contract_version=expected_contract_version,
    )
    if errors:
        version = str(document.get("contract_version", "<missing>"))
        raise ContractValidationError(version, errors)


def _decode_pointer_segment(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _remove_json_pointer(document: dict[str, Any], pointer: str) -> None:
    if not pointer.startswith("/") or pointer == "/":
        raise ValueError(f"Volatile field must be a concrete JSON pointer: {pointer!r}")
    segments = [_decode_pointer_segment(segment) for segment in pointer[1:].split("/")]
    current: Any = document
    for segment in segments[:-1]:
        if not isinstance(current, dict) or segment not in current:
            return
        current = current[segment]
    if isinstance(current, dict):
        current.pop(segments[-1], None)


def normalize_nonvolatile(document: Mapping[str, Any]) -> dict[str, Any]:
    """Remove only contract-declared volatile fields from a validated observation."""

    require_valid_contract(document)
    normalized = copy.deepcopy(dict(document))
    volatile_fields = normalized.get("volatile_fields", [])
    if volatile_fields:
        if tuple(volatile_fields) != OBSERVED_STATE_VOLATILE_FIELDS:
            raise ValueError("Only the observed-state v1 volatile-field set is supported.")
        for pointer in volatile_fields:
            _remove_json_pointer(normalized, pointer)
    return normalized
