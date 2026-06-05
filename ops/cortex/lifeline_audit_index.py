from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path

DEFAULT_LIFELINE_AUDIT_INDEX_RELATIVE_PATH = (
    "repos/lifeline/.lifeline/audits/proof-reference-receipt-index.json"
)


def _require_non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected non-negative integer for {field_name}.")
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean for {field_name}.")
    return value


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field_name}.")
    normalized = " ".join(value.strip().split())
    return normalized or None


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected non-empty string for {field_name}.")
    normalized = normalize_slashes(value.strip())
    if not normalized:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return normalized


def _require_unique_path_list(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        path_value = _require_string(item, f"{field_name}[{index}]")
        if path_value in seen:
            raise ValueError(f"Expected unique string entries for {field_name}.")
        seen.add(path_value)
        normalized.append(path_value)
    return tuple(normalized)


def _require_grouping(value: Any, field_name: str) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected object for {field_name}.")
    grouped: dict[str, tuple[str, ...]] = {}
    for key in sorted(value.keys()):
        grouped[_require_string(key, f"{field_name} key")] = _require_unique_path_list(
            value[key],
            f"{field_name}.{key}",
        )
    return grouped


@dataclass(frozen=True)
class LifelineInvalidReceipt:
    receipt_path: str
    path_source_repo_id: str | None
    path_tranche_id: str | None
    source_repo_id: str | None
    tranche_id: str | None
    receipt_id: str | None
    parsed: bool
    schema_valid: bool
    blocked_reason: str | None
    validation_errors: tuple[str, ...]

    @classmethod
    def from_payload(cls, payload: Any, *, field_name: str) -> "LifelineInvalidReceipt":
        if not isinstance(payload, dict):
            raise ValueError(f"Expected object for {field_name}.")
        schema_valid = _require_bool(payload.get("schema_valid"), f"{field_name}.schema_valid")
        if schema_valid:
            raise ValueError(f"{field_name}.schema_valid must be false for invalid receipt entries.")
        return cls(
            receipt_path=_require_string(payload.get("receipt_path"), f"{field_name}.receipt_path"),
            path_source_repo_id=_optional_string(
                payload.get("path_source_repo_id"),
                f"{field_name}.path_source_repo_id",
            ),
            path_tranche_id=_optional_string(
                payload.get("path_tranche_id"),
                f"{field_name}.path_tranche_id",
            ),
            source_repo_id=_optional_string(
                payload.get("source_repo_id"),
                f"{field_name}.source_repo_id",
            ),
            tranche_id=_optional_string(
                payload.get("tranche_id"),
                f"{field_name}.tranche_id",
            ),
            receipt_id=_optional_string(payload.get("receipt_id"), f"{field_name}.receipt_id"),
            parsed=_require_bool(payload.get("parsed"), f"{field_name}.parsed"),
            schema_valid=schema_valid,
            blocked_reason=_optional_string(
                payload.get("blocked_reason"),
                f"{field_name}.blocked_reason",
            ),
            validation_errors=_require_unique_path_list(
                payload.get("validation_errors"),
                f"{field_name}.validation_errors",
            ),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "receipt_path": self.receipt_path,
            "path_source_repo_id": self.path_source_repo_id,
            "path_tranche_id": self.path_tranche_id,
            "source_repo_id": self.source_repo_id,
            "tranche_id": self.tranche_id,
            "receipt_id": self.receipt_id,
            "parsed": self.parsed,
            "schema_valid": self.schema_valid,
            "blocked_reason": self.blocked_reason,
            "validation_errors": list(self.validation_errors),
        }


@dataclass(frozen=True)
class LifelineAuditIndexBlocker:
    code: str
    message: str
    receipt_paths: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "receipt_paths": list(self.receipt_paths),
        }


@dataclass(frozen=True)
class CortexLifelineAuditIndexSummary:
    receipt_count: int
    valid_receipt_count: int
    invalid_receipt_count: int
    receipts_by_source_repo_id: dict[str, tuple[str, ...]]
    receipts_by_tranche_id: dict[str, tuple[str, ...]]
    proof_reference_count_total: int
    receipts_with_ambient_debt: tuple[str, ...]
    receipts_with_current_validation_debt: tuple[str, ...]
    receipts_missing_boundary_statement: tuple[str, ...]
    receipts_with_auto_approved_not_false: tuple[str, ...]
    invalid_receipts: tuple[LifelineInvalidReceipt, ...]
    lifeline_audit_index_path: str
    cortex_read_only: bool
    connector_publication_blocked: bool
    connector_publication_blockers: tuple[LifelineAuditIndexBlocker, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "receipt_count": self.receipt_count,
            "valid_receipt_count": self.valid_receipt_count,
            "invalid_receipt_count": self.invalid_receipt_count,
            "receipts_by_source_repo_id": {
                key: list(value) for key, value in self.receipts_by_source_repo_id.items()
            },
            "receipts_by_tranche_id": {
                key: list(value) for key, value in self.receipts_by_tranche_id.items()
            },
            "proof_reference_count_total": self.proof_reference_count_total,
            "receipts_with_ambient_debt": list(self.receipts_with_ambient_debt),
            "receipts_with_current_validation_debt": list(
                self.receipts_with_current_validation_debt
            ),
            "receipts_missing_boundary_statement": list(
                self.receipts_missing_boundary_statement
            ),
            "receipts_with_auto_approved_not_false": list(
                self.receipts_with_auto_approved_not_false
            ),
            "invalid_receipts": [entry.to_payload() for entry in self.invalid_receipts],
            "lifeline_audit_index_path": self.lifeline_audit_index_path,
            "cortex_read_only": self.cortex_read_only,
            "connector_publication_blocked": self.connector_publication_blocked,
            "connector_publication_blockers": [
                blocker.to_payload() for blocker in self.connector_publication_blockers
            ],
        }


def default_lifeline_audit_index_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return resolve_atlas_path(DEFAULT_LIFELINE_AUDIT_INDEX_RELATIVE_PATH, root=base)


def _resolved_lifeline_audit_index_path(
    audit_index_path: str | Path | None,
    *,
    root: Path,
) -> Path:
    if audit_index_path is None:
        return default_lifeline_audit_index_path(root)
    return resolve_atlas_path(audit_index_path, root=root)


def _display_path(path: Path, *, root: Path) -> str:
    return normalize_slashes(atlas_relative(path, root=root))


def _read_audit_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise error
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Malformed Lifeline audit index JSON at {normalize_slashes(str(path))}: {error.msg}."
        ) from error
    if not isinstance(payload, dict):
        raise ValueError(
            f"Malformed Lifeline audit index JSON at {normalize_slashes(str(path))}: expected top-level object."
        )
    return payload


def _invalid_receipts(value: Any, field_name: str) -> tuple[LifelineInvalidReceipt, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    entries = [
        LifelineInvalidReceipt.from_payload(item, field_name=f"{field_name}[{index}]")
        for index, item in enumerate(value)
    ]
    receipt_paths = [entry.receipt_path for entry in entries]
    if len(receipt_paths) != len(set(receipt_paths)):
        raise ValueError(f"Expected unique receipt_path values for {field_name}.")
    return tuple(entries)


def _build_blockers(
    *,
    invalid_receipts: tuple[LifelineInvalidReceipt, ...],
    receipts_with_current_validation_debt: tuple[str, ...],
    receipts_with_auto_approved_not_false: tuple[str, ...],
    receipts_missing_boundary_statement: tuple[str, ...],
) -> tuple[LifelineAuditIndexBlocker, ...]:
    blockers: list[LifelineAuditIndexBlocker] = []
    if invalid_receipts:
        blockers.append(
            LifelineAuditIndexBlocker(
                code="invalid_receipts_present",
                message=(
                    "Lifeline audit index reports invalid final receipts; connector-backed "
                    "publication must remain blocked."
                ),
                receipt_paths=tuple(entry.receipt_path for entry in invalid_receipts),
            )
        )
    if receipts_with_current_validation_debt:
        blockers.append(
            LifelineAuditIndexBlocker(
                code="current_validation_debt_present",
                message=(
                    "At least one final receipt still carries current validation debt; "
                    "connector-backed publication must remain blocked."
                ),
                receipt_paths=receipts_with_current_validation_debt,
            )
        )
    if receipts_with_auto_approved_not_false:
        blockers.append(
            LifelineAuditIndexBlocker(
                code="auto_approved_violation",
                message=(
                    "At least one final receipt drifted from auto_approved=false; "
                    "connector-backed publication must remain blocked."
                ),
                receipt_paths=receipts_with_auto_approved_not_false,
            )
        )
    if receipts_missing_boundary_statement:
        blockers.append(
            LifelineAuditIndexBlocker(
                code="missing_boundary_statement",
                message=(
                    "At least one final receipt is missing the Lifeline owner boundary statement; "
                    "connector-backed publication must remain blocked."
                ),
                receipt_paths=receipts_missing_boundary_statement,
            )
        )
    return tuple(blockers)


def summarize_lifeline_audit_index(
    audit_index_path: str | Path | None = None,
    *,
    root: Path | None = None,
) -> CortexLifelineAuditIndexSummary:
    base = (root or atlas_root()).resolve()
    resolved_path = _resolved_lifeline_audit_index_path(audit_index_path, root=base)
    if not resolved_path.exists():
        raise FileNotFoundError(
            f"Lifeline audit index not found at {normalize_slashes(str(resolved_path))}."
        )
    payload = _read_audit_payload(resolved_path)

    receipt_count = _require_non_negative_int(payload.get("receipt_count"), "receipt_count")
    valid_receipt_count = _require_non_negative_int(
        payload.get("valid_receipt_count"),
        "valid_receipt_count",
    )
    invalid_receipt_count = _require_non_negative_int(
        payload.get("invalid_receipt_count"),
        "invalid_receipt_count",
    )
    if receipt_count != valid_receipt_count + invalid_receipt_count:
        raise ValueError(
            "Malformed Lifeline audit index: receipt_count must equal "
            "valid_receipt_count + invalid_receipt_count."
        )
    receipts_by_source_repo_id = _require_grouping(
        payload.get("receipts_by_source_repo_id"),
        "receipts_by_source_repo_id",
    )
    receipts_by_tranche_id = _require_grouping(
        payload.get("receipts_by_tranche_id"),
        "receipts_by_tranche_id",
    )
    proof_reference_count_total = _require_non_negative_int(
        payload.get("proof_reference_count_total"),
        "proof_reference_count_total",
    )
    receipts_with_ambient_debt = _require_unique_path_list(
        payload.get("receipts_with_ambient_debt"),
        "receipts_with_ambient_debt",
    )
    receipts_with_current_validation_debt = _require_unique_path_list(
        payload.get("receipts_with_current_validation_debt"),
        "receipts_with_current_validation_debt",
    )
    receipts_missing_boundary_statement = _require_unique_path_list(
        payload.get("receipts_missing_boundary_statement"),
        "receipts_missing_boundary_statement",
    )
    receipts_with_auto_approved_not_false = _require_unique_path_list(
        payload.get("receipts_with_auto_approved_not_false"),
        "receipts_with_auto_approved_not_false",
    )
    invalid_receipts = _invalid_receipts(payload.get("invalid_receipts"), "invalid_receipts")
    if invalid_receipt_count != len(invalid_receipts):
        raise ValueError(
            "Malformed Lifeline audit index: invalid_receipt_count must match invalid_receipts length."
        )

    blockers = _build_blockers(
        invalid_receipts=invalid_receipts,
        receipts_with_current_validation_debt=receipts_with_current_validation_debt,
        receipts_with_auto_approved_not_false=receipts_with_auto_approved_not_false,
        receipts_missing_boundary_statement=receipts_missing_boundary_statement,
    )
    return CortexLifelineAuditIndexSummary(
        receipt_count=receipt_count,
        valid_receipt_count=valid_receipt_count,
        invalid_receipt_count=invalid_receipt_count,
        receipts_by_source_repo_id=receipts_by_source_repo_id,
        receipts_by_tranche_id=receipts_by_tranche_id,
        proof_reference_count_total=proof_reference_count_total,
        receipts_with_ambient_debt=receipts_with_ambient_debt,
        receipts_with_current_validation_debt=receipts_with_current_validation_debt,
        receipts_missing_boundary_statement=receipts_missing_boundary_statement,
        receipts_with_auto_approved_not_false=receipts_with_auto_approved_not_false,
        invalid_receipts=invalid_receipts,
        lifeline_audit_index_path=_display_path(resolved_path, root=base),
        cortex_read_only=True,
        connector_publication_blocked=bool(blockers),
        connector_publication_blockers=blockers,
    )
