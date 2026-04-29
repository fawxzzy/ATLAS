from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.connector_proof_reference_candidate import (
    CONNECTOR_PROOF_REFERENCE_CANDIDATE_CONTRACT_VERSION,
    default_connector_proof_reference_candidate_latest_json_path,
)
from ops.cortex.proof_reference_pack import (
    PROOF_REFERENCE_PACK_CONTRACT_VERSION,
    default_proof_reference_pack_latest_json_path,
)
from ops.cortex.verification_ingest import VerificationDebtCounts

INTEGRATED_PROOF_REFERENCE_PACK_CONTRACT_VERSION = (
    "atlas.cortex.integrated-proof-reference-pack.v1"
)

_GLOBAL_CANDIDATE_BLOCKER_CODES = {
    "invalid_receipts_present",
    "current_validation_debt_present",
    "auto_approved_violation",
    "missing_boundary_statement",
}


def _require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected object for {field_name}.")
    return value


def _normalize_string(value: str) -> str:
    return " ".join(value.strip().split())


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected non-empty string for {field_name}.")
    normalized = _normalize_string(value)
    if not normalized:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return normalized


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field_name}.")
    normalized = _normalize_string(value)
    return normalized or None


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean for {field_name}.")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    return value


def _ordered_unique_strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        normalized = _require_non_empty_string(item, f"{field_name}[{index}]")
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _render_bool(value: bool) -> str:
    return "yes" if value else "no"


def _render_list(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


def _run_artifact_stem(run_id: str) -> str:
    normalized = normalize_slashes(_require_non_empty_string(run_id, "run_id"))
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized.replace("/", "__"))
    stem = sanitized.strip(".-")
    if not stem:
        raise ValueError("Expected run_id to produce a usable artifact filename.")
    return stem


def _slug(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalize_slashes(value).lower())
    collapsed = re.sub(r"-{2,}", "-", sanitized).strip(".-")
    return collapsed or "reference"


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise error
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Malformed {label} JSON at {normalize_slashes(str(path))}: {error.msg}."
        ) from error
    if not isinstance(payload, dict):
        raise ValueError(
            f"Malformed {label} JSON at {normalize_slashes(str(path))}: expected top-level object."
        )
    return payload


def _looks_like_url(value: str) -> bool:
    return "://" in value


def _merge_ordered_strings(*groups: tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            normalized = normalize_slashes(str(value).strip())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return tuple(ordered)


@dataclass(frozen=True)
class ConnectorProofReferenceIntegrationBlocker:
    source: str
    code: str
    message: str
    reference_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "source": self.source,
            "code": self.code,
            "message": self.message,
            "reference_ids": list(self.reference_ids),
        }


@dataclass(frozen=True)
class IntegratedProofReference:
    reference_id: str
    kind: str
    owner_layer: str
    artifact_path: Path | None
    url: str | None
    command: str | None
    claim: str
    status: str
    notes: tuple[str, ...]
    source: str
    source_candidate_id: str | None
    source_inventory_path: str | None

    def __post_init__(self) -> None:
        locator_count = sum(
            1
            for value in (self.artifact_path, self.url, self.command)
            if value is not None
        )
        if locator_count != 1:
            raise ValueError(
                "IntegratedProofReference requires exactly one of artifact_path, url, or command."
            )

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "reference_id": self.reference_id,
            "kind": self.kind,
            "owner_layer": self.owner_layer,
            "artifact_path": (
                atlas_relative(self.artifact_path, root=base)
                if self.artifact_path is not None
                else None
            ),
            "url": self.url,
            "command": self.command,
            "claim": self.claim,
            "status": self.status,
            "notes": list(self.notes),
            "source": self.source,
            "source_candidate_id": self.source_candidate_id,
            "source_inventory_path": self.source_inventory_path,
        }


@dataclass(frozen=True)
class ConnectorProofReferenceIntegrationResult:
    run_id: str
    owner_layer: str
    selected_next_action: str
    next_required_layer: str | None
    receipt_ready: bool
    blocked: bool
    blocked_reason: str | None
    pack_status: str
    review_status: str
    known_ambient_debt: tuple[str, ...]
    current_validation_debt: tuple[str, ...]
    touched_files: tuple[str, ...]
    targeted_verification_commands: tuple[str, ...]
    stack_validation_command: str
    stack_validation_status: str
    known_ambient_baseline: VerificationDebtCounts
    base_pack_path: str
    candidate_artifact_path: str
    candidate_set_run_id: str
    lifeline_audit_index_path: str | None
    integration_blockers: tuple[ConnectorProofReferenceIntegrationBlocker, ...]
    base_reference_count: int
    eligible_candidate_count: int
    integrated_candidate_count: int
    skipped_candidate_count: int
    candidate_source_counts: dict[str, int]
    references: tuple[IntegratedProofReference, ...]
    rule_statement: str
    pattern_statement: str
    failure_mode_statement: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "contract_version": INTEGRATED_PROOF_REFERENCE_PACK_CONTRACT_VERSION,
            "run_id": self.run_id,
            "owner_layer": self.owner_layer,
            "selected_next_action": self.selected_next_action,
            "next_required_layer": self.next_required_layer,
            "receipt_ready": self.receipt_ready,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "pack_status": self.pack_status,
            "review_status": self.review_status,
            "known_ambient_debt": list(self.known_ambient_debt),
            "current_validation_debt": list(self.current_validation_debt),
            "touched_files": list(self.touched_files),
            "targeted_verification_commands": list(self.targeted_verification_commands),
            "stack_validation": {
                "command": self.stack_validation_command,
                "status": self.stack_validation_status,
                "known_ambient_baseline": self.known_ambient_baseline.to_payload(),
                "known_ambient_debt": list(self.known_ambient_debt),
                "current_validation_debt": list(self.current_validation_debt),
            },
            "base_pack_path": self.base_pack_path,
            "candidate_artifact_path": self.candidate_artifact_path,
            "candidate_set_run_id": self.candidate_set_run_id,
            "lifeline_audit_index_path": self.lifeline_audit_index_path,
            "integration_blockers": [
                blocker.to_payload() for blocker in self.integration_blockers
            ],
            "base_reference_count": self.base_reference_count,
            "eligible_candidate_count": self.eligible_candidate_count,
            "integrated_candidate_count": self.integrated_candidate_count,
            "skipped_candidate_count": self.skipped_candidate_count,
            "candidate_source_counts": dict(sorted(self.candidate_source_counts.items())),
            "references": [reference.to_payload(root=base) for reference in self.references],
            "rule_statement": self.rule_statement,
            "pattern_statement": self.pattern_statement,
            "failure_mode_statement": self.failure_mode_statement,
            "final_receipt_owner": "lifeline",
        }


@dataclass(frozen=True)
class PersistedConnectorProofReferenceIntegrationResult:
    latest_artifact_path: Path
    latest_summary_path: Path | None
    run_artifact_path: Path
    run_summary_path: Path | None
    payload_digest: str
    payload: dict[str, object]
    summary: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "latest_artifact_path": atlas_relative(self.latest_artifact_path, root=base),
            "latest_summary_path": (
                atlas_relative(self.latest_summary_path, root=base)
                if self.latest_summary_path is not None
                else None
            ),
            "run_artifact_path": atlas_relative(self.run_artifact_path, root=base),
            "run_summary_path": (
                atlas_relative(self.run_summary_path, root=base)
                if self.run_summary_path is not None
                else None
            ),
            "payload_digest": self.payload_digest,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class _BasePackReference:
    reference_id: str
    kind: str
    owner_layer: str
    artifact_path: str | None
    command: str | None
    claim: str
    status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class _LoadedBasePack:
    artifact_path: Path
    run_id: str
    owner_layer: str
    selected_next_action: str
    next_required_layer: str | None
    receipt_ready: bool
    blocked: bool
    blocked_reason: str | None
    pack_status: str
    review_status: str
    known_ambient_debt: tuple[str, ...]
    current_validation_debt: tuple[str, ...]
    touched_files: tuple[str, ...]
    targeted_verification_commands: tuple[str, ...]
    stack_validation_command: str
    stack_validation_status: str
    known_ambient_baseline: VerificationDebtCounts
    references: tuple[_BasePackReference, ...]


@dataclass(frozen=True)
class _CandidateBlocker:
    source: str
    code: str
    message: str
    reference_ids: tuple[str, ...]


@dataclass(frozen=True)
class _LoadedCandidate:
    candidate_id: str
    source: str
    kind: str
    owner_layer: str
    claim: str
    status: str
    artifact_or_url: str | None
    observed_at: str | None
    eligible_for_proof_reference: bool
    blockers: tuple[str, ...]
    source_inventory_path: str
    source_reference_id: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class _LoadedCandidateSet:
    artifact_path: Path
    run_id: str
    owner_layer: str
    source_inventory_path: str
    source_inventory_run_id: str
    lifeline_audit_index_path: str | None
    candidate_set_blocked: bool
    candidate_set_blockers: tuple[_CandidateBlocker, ...]
    candidates: tuple[_LoadedCandidate, ...]
    source_counts: dict[str, int]


def _resolved_integrated_pack_dir(
    *,
    root: Path | None = None,
    integrated_pack_root: Path | None = None,
) -> Path:
    base = (root or atlas_root()).resolve()
    return (
        integrated_pack_root.resolve()
        if integrated_pack_root is not None
        else base / "runtime" / "cortex" / "proof-reference-packs" / "integrated"
    )


def default_integrated_proof_reference_pack_dir(root: Path | None = None) -> Path:
    return _resolved_integrated_pack_dir(root=root)


def default_integrated_proof_reference_pack_latest_json_path(
    root: Path | None = None,
    *,
    integrated_pack_root: Path | None = None,
) -> Path:
    return _resolved_integrated_pack_dir(
        root=root,
        integrated_pack_root=integrated_pack_root,
    ) / "latest.json"


def default_integrated_proof_reference_pack_latest_summary_path(
    root: Path | None = None,
    *,
    integrated_pack_root: Path | None = None,
) -> Path:
    return _resolved_integrated_pack_dir(
        root=root,
        integrated_pack_root=integrated_pack_root,
    ) / "latest.txt"


def default_integrated_proof_reference_pack_run_dir(
    root: Path | None = None,
    *,
    integrated_pack_root: Path | None = None,
) -> Path:
    return _resolved_integrated_pack_dir(
        root=root,
        integrated_pack_root=integrated_pack_root,
    ) / "runs"


def default_integrated_proof_reference_pack_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    integrated_pack_root: Path | None = None,
) -> Path:
    return default_integrated_proof_reference_pack_run_dir(
        root=root,
        integrated_pack_root=integrated_pack_root,
    ) / f"{_run_artifact_stem(run_id)}.json"


def default_integrated_proof_reference_pack_run_summary_path(
    run_id: str,
    root: Path | None = None,
    *,
    integrated_pack_root: Path | None = None,
) -> Path:
    return default_integrated_proof_reference_pack_run_dir(
        root=root,
        integrated_pack_root=integrated_pack_root,
    ) / f"{_run_artifact_stem(run_id)}.txt"


def _coerce_base_reference(payload: Any, *, field_name: str) -> _BasePackReference:
    value = _require_object(payload, field_name)
    artifact_path = _optional_string(value.get("artifact_path"), f"{field_name}.artifact_path")
    command = _optional_string(value.get("command"), f"{field_name}.command")
    if (artifact_path is None) == (command is None):
        raise ValueError(
            f"Expected exactly one of artifact_path or command for {field_name}."
        )
    return _BasePackReference(
        reference_id=_require_non_empty_string(
            value.get("reference_id"),
            f"{field_name}.reference_id",
        ),
        kind=_require_non_empty_string(value.get("kind"), f"{field_name}.kind").lower(),
        owner_layer=_require_non_empty_string(
            value.get("owner_layer"),
            f"{field_name}.owner_layer",
        ).lower(),
        artifact_path=normalize_slashes(artifact_path) if artifact_path is not None else None,
        command=command,
        claim=_require_non_empty_string(value.get("claim"), f"{field_name}.claim"),
        status=_require_non_empty_string(value.get("status"), f"{field_name}.status").lower(),
        notes=_ordered_unique_strings(value.get("notes"), f"{field_name}.notes"),
    )


def _coerce_base_pack(path: Path) -> _LoadedBasePack:
    if not path.exists():
        raise FileNotFoundError(
            f"Base proof-reference pack not found at {normalize_slashes(str(path))}."
        )
    payload = _read_json_object(path, label="base proof-reference pack")
    contract_version = _require_non_empty_string(
        payload.get("contract_version"),
        "contract_version",
    )
    if contract_version != PROOF_REFERENCE_PACK_CONTRACT_VERSION:
        raise ValueError(
            "Malformed base proof-reference pack JSON at "
            f"{normalize_slashes(str(path))}: expected contract_version "
            f"{PROOF_REFERENCE_PACK_CONTRACT_VERSION}."
        )
    references_payload = _require_list(payload.get("references"), "references")
    references = tuple(
        _coerce_base_reference(item, field_name=f"references[{index}]")
        for index, item in enumerate(references_payload)
    )
    stack_validation = _require_object(payload.get("stack_validation"), "stack_validation")
    return _LoadedBasePack(
        artifact_path=path.resolve(),
        run_id=_require_non_empty_string(payload.get("run_id"), "run_id"),
        owner_layer=_require_non_empty_string(payload.get("owner_layer"), "owner_layer").lower(),
        selected_next_action=_require_non_empty_string(
            payload.get("selected_next_action"),
            "selected_next_action",
        ),
        next_required_layer=_optional_string(
            payload.get("next_required_layer"),
            "next_required_layer",
        ),
        receipt_ready=_require_bool(payload.get("receipt_ready"), "receipt_ready"),
        blocked=_require_bool(payload.get("blocked"), "blocked"),
        blocked_reason=_optional_string(payload.get("blocked_reason"), "blocked_reason"),
        pack_status=_require_non_empty_string(payload.get("pack_status"), "pack_status").lower(),
        review_status=_require_non_empty_string(payload.get("review_status"), "review_status").lower(),
        known_ambient_debt=_ordered_unique_strings(
            payload.get("known_ambient_debt"),
            "known_ambient_debt",
        ),
        current_validation_debt=_ordered_unique_strings(
            payload.get("current_validation_debt"),
            "current_validation_debt",
        ),
        touched_files=_ordered_unique_strings(payload.get("touched_files"), "touched_files"),
        targeted_verification_commands=_ordered_unique_strings(
            payload.get("targeted_verification_commands"),
            "targeted_verification_commands",
        ),
        stack_validation_command=_require_non_empty_string(
            stack_validation.get("command"),
            "stack_validation.command",
        ),
        stack_validation_status=_require_non_empty_string(
            stack_validation.get("status"),
            "stack_validation.status",
        ).lower(),
        known_ambient_baseline=VerificationDebtCounts.from_payload(
            _require_object(
                stack_validation.get("known_ambient_baseline"),
                "stack_validation.known_ambient_baseline",
            ),
            field_name="stack_validation.known_ambient_baseline",
        ),
        references=references,
    )


def _coerce_candidate_blocker(payload: Any, *, field_name: str) -> _CandidateBlocker:
    value = _require_object(payload, field_name)
    return _CandidateBlocker(
        source=_require_non_empty_string(value.get("source"), f"{field_name}.source").lower(),
        code=_require_non_empty_string(value.get("code"), f"{field_name}.code"),
        message=_require_non_empty_string(value.get("message"), f"{field_name}.message"),
        reference_ids=_ordered_unique_strings(
            value.get("reference_ids"),
            f"{field_name}.reference_ids",
        ),
    )


def _coerce_candidate(payload: Any, *, field_name: str) -> _LoadedCandidate:
    value = _require_object(payload, field_name)
    artifact_or_url = _optional_string(
        value.get("artifact_or_url"),
        f"{field_name}.artifact_or_url",
    )
    return _LoadedCandidate(
        candidate_id=_require_non_empty_string(
            value.get("candidate_id"),
            f"{field_name}.candidate_id",
        ),
        source=_require_non_empty_string(value.get("source"), f"{field_name}.source").lower(),
        kind=_require_non_empty_string(value.get("kind"), f"{field_name}.kind").lower(),
        owner_layer=_require_non_empty_string(
            value.get("owner_layer"),
            f"{field_name}.owner_layer",
        ).lower(),
        claim=_require_non_empty_string(value.get("claim"), f"{field_name}.claim"),
        status=_require_non_empty_string(value.get("status"), f"{field_name}.status").lower(),
        artifact_or_url=normalize_slashes(artifact_or_url) if artifact_or_url is not None else None,
        observed_at=_optional_string(value.get("observed_at"), f"{field_name}.observed_at"),
        eligible_for_proof_reference=_require_bool(
            value.get("eligible_for_proof_reference"),
            f"{field_name}.eligible_for_proof_reference",
        ),
        blockers=_ordered_unique_strings(value.get("blockers"), f"{field_name}.blockers"),
        source_inventory_path=normalize_slashes(
            _require_non_empty_string(
                value.get("source_inventory_path"),
                f"{field_name}.source_inventory_path",
            )
        ),
        source_reference_id=_require_non_empty_string(
            value.get("source_reference_id"),
            f"{field_name}.source_reference_id",
        ),
        notes=_ordered_unique_strings(value.get("notes"), f"{field_name}.notes"),
    )


def _coerce_candidate_set(path: Path) -> _LoadedCandidateSet:
    if not path.exists():
        raise FileNotFoundError(
            f"Connector proof-reference candidate artifact not found at {normalize_slashes(str(path))}."
        )
    payload = _read_json_object(path, label="connector proof-reference candidate artifact")
    contract_version = _require_non_empty_string(
        payload.get("contract_version"),
        "contract_version",
    )
    if contract_version != CONNECTOR_PROOF_REFERENCE_CANDIDATE_CONTRACT_VERSION:
        raise ValueError(
            "Malformed connector proof-reference candidate artifact JSON at "
            f"{normalize_slashes(str(path))}: expected contract_version "
            f"{CONNECTOR_PROOF_REFERENCE_CANDIDATE_CONTRACT_VERSION}."
        )
    blockers_payload = _require_list(
        payload.get("candidate_set_blockers"),
        "candidate_set_blockers",
    )
    blockers = tuple(
        _coerce_candidate_blocker(item, field_name=f"candidate_set_blockers[{index}]")
        for index, item in enumerate(blockers_payload)
    )
    candidates_payload = _require_list(payload.get("candidates"), "candidates")
    candidates = tuple(
        _coerce_candidate(item, field_name=f"candidates[{index}]")
        for index, item in enumerate(candidates_payload)
    )
    source_counts_payload = _require_object(payload.get("source_counts"), "source_counts")
    source_counts: dict[str, int] = {}
    for key in sorted(source_counts_payload):
        value = source_counts_payload[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Expected integer for source_counts.{key}.")
        source_counts[_require_non_empty_string(key, "source_counts key")] = value
    return _LoadedCandidateSet(
        artifact_path=path.resolve(),
        run_id=_require_non_empty_string(payload.get("run_id"), "run_id"),
        owner_layer=_require_non_empty_string(payload.get("owner_layer"), "owner_layer").lower(),
        source_inventory_path=normalize_slashes(
            _require_non_empty_string(
                payload.get("source_inventory_path"),
                "source_inventory_path",
            )
        ),
        source_inventory_run_id=_require_non_empty_string(
            payload.get("source_inventory_run_id"),
            "source_inventory_run_id",
        ),
        lifeline_audit_index_path=_optional_string(
            payload.get("lifeline_audit_index_path"),
            "lifeline_audit_index_path",
        ),
        candidate_set_blocked=_require_bool(
            payload.get("candidate_set_blocked"),
            "candidate_set_blocked",
        ),
        candidate_set_blockers=blockers,
        candidates=candidates,
        source_counts=source_counts,
    )


def _base_reference_to_integrated(
    reference: _BasePackReference,
    *,
    root: Path,
) -> IntegratedProofReference:
    artifact_path = (
        resolve_atlas_path(reference.artifact_path, root=root)
        if reference.artifact_path is not None
        else None
    )
    return IntegratedProofReference(
        reference_id=reference.reference_id,
        kind=reference.kind,
        owner_layer=reference.owner_layer,
        artifact_path=artifact_path,
        url=None,
        command=reference.command,
        claim=reference.claim,
        status=reference.status,
        notes=_merge_ordered_strings(
            reference.notes,
            ("Preserved from the base Cortex proof-reference pack.",),
        ),
        source="base_pack",
        source_candidate_id=None,
        source_inventory_path=None,
    )


def _candidate_reference_id(candidate: _LoadedCandidate) -> str:
    return (
        f"connector-{_slug(candidate.source)}-"
        f"{_slug(candidate.kind)}-{_slug(candidate.source_reference_id)}"
    )


def _candidate_reference_notes(candidate: _LoadedCandidate) -> tuple[str, ...]:
    extra: list[str] = [
        f"Integrated from connector proof-reference candidate {candidate.candidate_id}.",
        f"Source inventory path={candidate.source_inventory_path}.",
    ]
    if candidate.observed_at is not None:
        extra.append(f"Observed at={candidate.observed_at}.")
    return _merge_ordered_strings(candidate.notes, tuple(extra))


def _candidate_to_integrated(
    candidate: _LoadedCandidate,
    *,
    root: Path,
) -> IntegratedProofReference:
    if candidate.artifact_or_url is None:
        raise ValueError(
            "Eligible connector proof-reference candidate is missing an artifact_or_url locator."
        )
    if _looks_like_url(candidate.artifact_or_url):
        artifact_path: Path | None = None
        url: str | None = candidate.artifact_or_url
    else:
        artifact_path = resolve_atlas_path(candidate.artifact_or_url, root=root)
        url = None
    return IntegratedProofReference(
        reference_id=_candidate_reference_id(candidate),
        kind=candidate.kind,
        owner_layer=candidate.owner_layer,
        artifact_path=artifact_path,
        url=url,
        command=None,
        claim=candidate.claim,
        status=candidate.status,
        notes=_candidate_reference_notes(candidate),
        source="connector_candidate",
        source_candidate_id=candidate.candidate_id,
        source_inventory_path=candidate.source_inventory_path,
    )


def _candidate_is_integrable(candidate: _LoadedCandidate) -> bool:
    return (
        candidate.eligible_for_proof_reference
        and not candidate.blockers
        and candidate.artifact_or_url is not None
        and bool(candidate.source_reference_id)
        and bool(candidate.owner_layer)
    )


def _candidate_sort_key(candidate: _LoadedCandidate) -> tuple[str, ...]:
    return (
        candidate.source,
        candidate.kind,
        candidate.source_reference_id,
        candidate.artifact_or_url or "",
        candidate.status,
        candidate.claim,
        candidate.owner_layer,
        candidate.observed_at or "",
    )


def _reference_canonical_key(reference: IntegratedProofReference) -> tuple[str, ...]:
    return (
        reference.kind,
        reference.owner_layer,
        normalize_slashes(str(reference.artifact_path)) if reference.artifact_path is not None else "",
        reference.url or "",
        reference.command or "",
        reference.claim,
        reference.source_candidate_id or "",
        reference.source_inventory_path or "",
    )


def _dedupe_references(
    base_references: tuple[IntegratedProofReference, ...],
    candidate_references: tuple[IntegratedProofReference, ...],
) -> tuple[IntegratedProofReference, ...]:
    ordered: list[IntegratedProofReference] = []
    seen_reference_ids: set[str] = set()
    seen_canonical: set[tuple[str, ...]] = set()
    for reference in (*base_references, *candidate_references):
        canonical = _reference_canonical_key(reference)
        if reference.reference_id in seen_reference_ids or canonical in seen_canonical:
            continue
        seen_reference_ids.add(reference.reference_id)
        seen_canonical.add(canonical)
        ordered.append(reference)
    return tuple(ordered)


def _integration_blockers(
    base_pack: _LoadedBasePack,
    candidate_set: _LoadedCandidateSet,
) -> tuple[ConnectorProofReferenceIntegrationBlocker, ...]:
    blockers: list[ConnectorProofReferenceIntegrationBlocker] = []
    if base_pack.current_validation_debt:
        blockers.append(
            ConnectorProofReferenceIntegrationBlocker(
                source="base_pack",
                code="base_pack_current_validation_debt",
                message=(
                    "The base Cortex proof-reference pack still carries current validation debt; "
                    "connector-backed pack integration must remain blocked."
                ),
                reference_ids=base_pack.current_validation_debt,
            )
        )
    if candidate_set.candidate_set_blocked:
        blockers.extend(
            ConnectorProofReferenceIntegrationBlocker(
                source=blocker.source,
                code=blocker.code,
                message=blocker.message,
                reference_ids=blocker.reference_ids,
            )
            for blocker in candidate_set.candidate_set_blockers
            if blocker.code in _GLOBAL_CANDIDATE_BLOCKER_CODES
        )
        if not candidate_set.candidate_set_blockers:
            blockers.append(
                ConnectorProofReferenceIntegrationBlocker(
                    source="candidate_set",
                    code="candidate_set_blocked",
                    message=(
                        "The connector proof-reference candidate set reported a global block "
                        "without enumerated blocker details."
                    ),
                    reference_ids=(),
                )
            )
    merged: dict[tuple[str, str], ConnectorProofReferenceIntegrationBlocker] = {}
    for blocker in blockers:
        key = (blocker.source, blocker.code)
        existing = merged.get(key)
        if existing is None:
            merged[key] = blocker
            continue
        merged[key] = ConnectorProofReferenceIntegrationBlocker(
            source=existing.source,
            code=existing.code,
            message=existing.message,
            reference_ids=_merge_ordered_strings(
                existing.reference_ids,
                blocker.reference_ids,
            ),
        )
    return tuple(merged[key] for key in sorted(merged))


def _blocked_reason(
    base_pack: _LoadedBasePack,
    integration_blockers: tuple[ConnectorProofReferenceIntegrationBlocker, ...],
) -> str | None:
    if integration_blockers:
        return "; ".join(blocker.code for blocker in integration_blockers)
    return base_pack.blocked_reason


def integrate_connector_candidates(
    base_pack_path: str | Path | None = None,
    connector_candidate_path: str | Path | None = None,
    *,
    root: Path | None = None,
) -> ConnectorProofReferenceIntegrationResult:
    base = (root or atlas_root()).resolve()
    resolved_base_pack_path = (
        default_proof_reference_pack_latest_json_path(base)
        if base_pack_path is None
        else resolve_atlas_path(base_pack_path, root=base)
    )
    resolved_candidate_path = (
        default_connector_proof_reference_candidate_latest_json_path(base)
        if connector_candidate_path is None
        else resolve_atlas_path(connector_candidate_path, root=base)
    )
    loaded_base_pack = _coerce_base_pack(resolved_base_pack_path)
    loaded_candidate_set = _coerce_candidate_set(resolved_candidate_path)
    integration_blockers = _integration_blockers(loaded_base_pack, loaded_candidate_set)
    blocked = loaded_base_pack.blocked or bool(integration_blockers)

    base_references = tuple(
        _base_reference_to_integrated(reference, root=base)
        for reference in loaded_base_pack.references
    )
    eligible_candidates = tuple(
        candidate
        for candidate in sorted(loaded_candidate_set.candidates, key=_candidate_sort_key)
        if _candidate_is_integrable(candidate)
    )
    candidate_references = (
        ()
        if blocked
        else tuple(
            _candidate_to_integrated(candidate, root=base)
            for candidate in eligible_candidates
        )
    )
    merged_references = _dedupe_references(base_references, candidate_references)
    integrated_candidate_count = sum(
        1 for reference in merged_references if reference.source == "connector_candidate"
    )
    pack_status = "blocked" if blocked else loaded_base_pack.pack_status
    review_status = "blocked" if blocked else loaded_base_pack.review_status
    return ConnectorProofReferenceIntegrationResult(
        run_id=loaded_base_pack.run_id,
        owner_layer="cortex",
        selected_next_action=loaded_base_pack.selected_next_action,
        next_required_layer=loaded_base_pack.next_required_layer,
        receipt_ready=loaded_base_pack.receipt_ready and not blocked,
        blocked=blocked,
        blocked_reason=_blocked_reason(loaded_base_pack, integration_blockers),
        pack_status=pack_status,
        review_status=review_status,
        known_ambient_debt=loaded_base_pack.known_ambient_debt,
        current_validation_debt=loaded_base_pack.current_validation_debt,
        touched_files=loaded_base_pack.touched_files,
        targeted_verification_commands=loaded_base_pack.targeted_verification_commands,
        stack_validation_command=loaded_base_pack.stack_validation_command,
        stack_validation_status=loaded_base_pack.stack_validation_status,
        known_ambient_baseline=loaded_base_pack.known_ambient_baseline,
        base_pack_path=atlas_relative(loaded_base_pack.artifact_path, root=base),
        candidate_artifact_path=atlas_relative(loaded_candidate_set.artifact_path, root=base),
        candidate_set_run_id=loaded_candidate_set.run_id,
        lifeline_audit_index_path=loaded_candidate_set.lifeline_audit_index_path,
        integration_blockers=integration_blockers,
        base_reference_count=len(base_references),
        eligible_candidate_count=sum(
            1 for candidate in loaded_candidate_set.candidates if candidate.eligible_for_proof_reference
        ),
        integrated_candidate_count=integrated_candidate_count,
        skipped_candidate_count=max(len(eligible_candidates) - integrated_candidate_count, 0)
        + sum(
            1
            for candidate in loaded_candidate_set.candidates
            if not _candidate_is_integrable(candidate)
        ),
        candidate_source_counts=dict(sorted(loaded_candidate_set.source_counts.items())),
        references=merged_references,
        rule_statement=(
            "Connector-backed candidates may enter Cortex proof-reference packs only after "
            "candidate-set blockers, validation debt, audit-index blockers, and individual "
            "candidate blockers are clear."
        ),
        pattern_statement=(
            "Connector evidence flows through inventory -> candidate -> gated pack integration "
            "before any receipt or publication path can consume it."
        ),
        failure_mode_statement=(
            "Do not let connector candidates mutate Lifeline receipts, publish evidence, "
            "overwrite the original proof pack, or bypass gating just because validation is "
            "back at baseline."
        ),
    )


def render_integrated_pack_summary(
    result: ConnectorProofReferenceIntegrationResult,
) -> str:
    lines = [
        "Cortex Integrated Proof Reference Pack",
        f"- Run id: {result.run_id}",
        f"- Owner layer: {result.owner_layer}",
        f"- Base pack path: {result.base_pack_path}",
        f"- Candidate artifact path: {result.candidate_artifact_path}",
        f"- Candidate set run id: {result.candidate_set_run_id}",
        f"- Lifeline audit index path: {result.lifeline_audit_index_path or 'none'}",
        f"- Pack status: {result.pack_status}",
        f"- Review status: {result.review_status}",
        f"- Receipt ready: {_render_bool(result.receipt_ready)}",
        f"- Blocked: {_render_bool(result.blocked)}",
        f"- Blocked reason: {result.blocked_reason or 'none'}",
        (
            "- Integration blockers: "
            f"{_render_list(tuple(blocker.code for blocker in result.integration_blockers))}"
        ),
        f"- Base reference count: {result.base_reference_count}",
        f"- Eligible candidate count: {result.eligible_candidate_count}",
        f"- Integrated candidate count: {result.integrated_candidate_count}",
        f"- Skipped candidate count: {result.skipped_candidate_count}",
        f"- Stack validation command: {result.stack_validation_command}",
        f"- Stack validation status: {result.stack_validation_status}",
        f"- Targeted verification commands: {_render_list(result.targeted_verification_commands)}",
        f"- Rule: {result.rule_statement}",
        f"- Pattern: {result.pattern_statement}",
        f"- Failure mode: {result.failure_mode_statement}",
    ]
    return "\n".join(lines) + "\n"


def _write_summary(path: Path, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")


class ConnectorProofReferenceIntegrator:
    def write(
        self,
        base_pack_path: str | Path | None = None,
        connector_candidate_path: str | Path | None = None,
        *,
        root: Path | None = None,
        integrated_pack_root: Path | None = None,
        latest_json_path: Path | None = None,
        latest_summary_path: Path | None = None,
        run_json_path: Path | None = None,
        run_summary_path: Path | None = None,
        write_summary: bool = True,
    ) -> PersistedConnectorProofReferenceIntegrationResult:
        base = (root or atlas_root()).resolve()
        output_root = _resolved_integrated_pack_dir(
            root=base,
            integrated_pack_root=integrated_pack_root,
        )
        result = integrate_connector_candidates(
            base_pack_path,
            connector_candidate_path,
            root=base,
        )
        payload = result.to_payload(root=base)
        summary = render_integrated_pack_summary(result)
        resolved_latest_json_path = (
            latest_json_path.resolve()
            if latest_json_path is not None
            else default_integrated_proof_reference_pack_latest_json_path(
                base,
                integrated_pack_root=output_root,
            )
        )
        resolved_run_json_path = (
            run_json_path.resolve()
            if run_json_path is not None
            else default_integrated_proof_reference_pack_run_json_path(
                result.run_id,
                base,
                integrated_pack_root=output_root,
            )
        )
        resolved_latest_summary_path = None
        resolved_run_summary_path = None
        if write_summary:
            resolved_latest_summary_path = (
                latest_summary_path.resolve()
                if latest_summary_path is not None
                else default_integrated_proof_reference_pack_latest_summary_path(
                    base,
                    integrated_pack_root=output_root,
                )
            )
            resolved_run_summary_path = (
                run_summary_path.resolve()
                if run_summary_path is not None
                else default_integrated_proof_reference_pack_run_summary_path(
                    result.run_id,
                    base,
                    integrated_pack_root=output_root,
                )
            )
        write_json(resolved_latest_json_path, payload)
        write_json(resolved_run_json_path, payload)
        if resolved_latest_summary_path is not None:
            _write_summary(resolved_latest_summary_path, summary)
        if resolved_run_summary_path is not None:
            _write_summary(resolved_run_summary_path, summary)
        return PersistedConnectorProofReferenceIntegrationResult(
            latest_artifact_path=resolved_latest_json_path,
            latest_summary_path=resolved_latest_summary_path,
            run_artifact_path=resolved_run_json_path,
            run_summary_path=resolved_run_summary_path,
            payload_digest=stable_json_digest(payload),
            payload=payload,
            summary=summary,
        )


def write_integrated_proof_reference_pack(
    base_pack_path: str | Path | None = None,
    connector_candidate_path: str | Path | None = None,
    *,
    root: Path | None = None,
    integrated_pack_root: Path | None = None,
    latest_json_path: Path | None = None,
    latest_summary_path: Path | None = None,
    run_json_path: Path | None = None,
    run_summary_path: Path | None = None,
    write_summary: bool = True,
) -> PersistedConnectorProofReferenceIntegrationResult:
    return ConnectorProofReferenceIntegrator().write(
        base_pack_path,
        connector_candidate_path,
        root=root,
        integrated_pack_root=integrated_pack_root,
        latest_json_path=latest_json_path,
        latest_summary_path=latest_summary_path,
        run_json_path=run_json_path,
        run_summary_path=run_summary_path,
        write_summary=write_summary,
    )
