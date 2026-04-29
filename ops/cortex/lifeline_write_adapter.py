from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import read_json, stable_json_digest, write_json_if_changed
from ops.cortex.lifeline_receipt_candidate import (
    LifelineReceiptCandidateValidation,
    validate_lifeline_receipt_candidate,
)
from ops.cortex.proof_reference_pack import (
    CortexProofReferencePack,
    default_proof_reference_pack_latest_json_path,
)

LIFELINE_WRITE_READY_CONTRACT_VERSION = "atlas.cortex.lifeline-write-ready.v1"


def _require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected object for {field_name}.")
    return value


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected non-empty string for {field_name}.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return normalized


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field_name}.")
    normalized = " ".join(value.strip().split())
    return normalized or None


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean for {field_name}.")
    return value


def _ordered_unique_strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected string entries in {field_name}.")
        normalized = normalize_slashes(" ".join(item.strip().split()))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _run_artifact_stem(run_id: str) -> str:
    normalized = normalize_slashes(_require_non_empty_string(run_id, "run_id"))
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized.replace("/", "__"))
    stem = sanitized.strip(".-")
    if not stem:
        raise ValueError("Expected run_id to produce a usable artifact filename.")
    return stem


def _resolved_lifeline_write_ready_dir(
    *,
    root: Path | None = None,
    lifeline_write_ready_root: Path | None = None,
) -> Path:
    base = (root or atlas_root()).resolve()
    return (
        lifeline_write_ready_root.resolve()
        if lifeline_write_ready_root is not None
        else base / "runtime" / "cortex" / "lifeline-write-ready"
    )


def default_lifeline_write_ready_dir(root: Path | None = None) -> Path:
    return _resolved_lifeline_write_ready_dir(root=root)


def default_lifeline_write_ready_latest_json_path(
    root: Path | None = None,
    *,
    lifeline_write_ready_root: Path | None = None,
) -> Path:
    output_root = _resolved_lifeline_write_ready_dir(
        root=root,
        lifeline_write_ready_root=lifeline_write_ready_root,
    )
    return output_root / "latest.json"


def default_lifeline_write_ready_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    lifeline_write_ready_root: Path | None = None,
) -> Path:
    output_root = _resolved_lifeline_write_ready_dir(
        root=root,
        lifeline_write_ready_root=lifeline_write_ready_root,
    )
    return output_root / "runs" / f"{_run_artifact_stem(run_id)}.json"


@dataclass(frozen=True)
class LifelineWriteApproval:
    explicit_human_approval: bool
    approved_at: str | None = None
    reviewer_id: str | None = None
    reviewer_label: str | None = None
    approval_note: str | None = None

    def __post_init__(self) -> None:
        approved_at = _optional_string(self.approved_at, "approved_at")
        reviewer_id = _optional_string(self.reviewer_id, "reviewer_id")
        reviewer_label = _optional_string(self.reviewer_label, "reviewer_label")
        approval_note = _optional_string(self.approval_note, "approval_note")
        if self.explicit_human_approval:
            if reviewer_id is None and reviewer_label is None:
                raise ValueError("Explicit human approval requires reviewer_id or reviewer_label.")
            if approval_note is None:
                raise ValueError("Explicit human approval requires approval_note.")
        object.__setattr__(self, "approved_at", approved_at)
        object.__setattr__(self, "reviewer_id", reviewer_id)
        object.__setattr__(self, "reviewer_label", reviewer_label)
        object.__setattr__(self, "approval_note", approval_note)

    def to_payload(self) -> dict[str, object]:
        return {
            "explicit_human_approval": self.explicit_human_approval,
            "approved_at": self.approved_at,
            "reviewer_id": self.reviewer_id,
            "reviewer_label": self.reviewer_label,
            "approval_note": self.approval_note,
        }


@dataclass(frozen=True)
class LifelineReceiptInput:
    source_repo_id: str
    tranche_id: str
    proof_summary_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_repo_id",
            _require_non_empty_string(self.source_repo_id, "source_repo_id"),
        )
        object.__setattr__(
            self,
            "tranche_id",
            _require_non_empty_string(self.tranche_id, "tranche_id"),
        )
        object.__setattr__(
            self,
            "proof_summary_ref",
            normalize_slashes(_require_non_empty_string(self.proof_summary_ref, "proof_summary_ref")),
        )

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        proof_summary_path = resolve_atlas_path(self.proof_summary_ref, root=base)
        if not proof_summary_path.exists():
            raise FileNotFoundError(
                f"ATLAS UI proof summary not found at {normalize_slashes(str(proof_summary_path))}."
            )
        proof_summary_payload = read_json(proof_summary_path)
        owner_repo_id = _require_non_empty_string(
            proof_summary_payload.get("owner_repo_id"),
            "proof_summary.owner_repo_id",
        )
        if owner_repo_id != self.source_repo_id:
            raise ValueError(
                "source_repo_id must match proof summary owner_repo_id for Lifeline receipt compatibility."
            )
        semantic_proof = _require_object(proof_summary_payload.get("semantic_proof"), "proof_summary.semantic_proof")
        visual_proof = _require_object(proof_summary_payload.get("visual_proof"), "proof_summary.visual_proof")
        payload = {
            "source_repo_id": self.source_repo_id,
            "tranche_id": self.tranche_id,
            "proof_summary": {
                "owner_repo_id": owner_repo_id,
                "summary_ref": normalize_slashes(atlas_relative(proof_summary_path, root=base)),
                "report_id": _require_non_empty_string(
                    proof_summary_payload.get("report_id"),
                    "proof_summary.report_id",
                ),
            },
            "proof_refs": {
                "semantic_report_ref": normalize_slashes(
                    _require_non_empty_string(
                        semantic_proof.get("report_ref"),
                        "proof_summary.semantic_proof.report_ref",
                    )
                ),
                "semantic_report_id": _optional_string(
                    semantic_proof.get("report_id"),
                    "proof_summary.semantic_proof.report_id",
                ),
                "visual_report_ref": normalize_slashes(
                    _require_non_empty_string(
                        visual_proof.get("report_ref"),
                        "proof_summary.visual_proof.report_ref",
                    )
                ),
                "visual_report_id": _optional_string(
                    visual_proof.get("report_id"),
                    "proof_summary.visual_proof.report_id",
                ),
            },
        }
        payload["source_refs"] = [
            payload["proof_summary"]["summary_ref"],
            payload["proof_refs"]["semantic_report_ref"],
            payload["proof_refs"]["visual_report_ref"],
        ]
        return payload


@dataclass(frozen=True)
class LifelineWriteAdapterResult:
    run_id: str
    candidate_valid: bool
    human_review_ready: bool
    lifeline_write_eligible: bool
    explicit_human_approval: bool
    auto_approved: bool
    receipt_written: bool
    receipt_path: str | None
    blocked: bool
    blocked_reason: str | None
    reviewer_action: str
    proof_reference_pack_path: str
    lifeline_boundary_statement: str | None
    missing_references: tuple[str, ...] = ()
    current_validation_debt: tuple[str, ...] = ()
    known_ambient_debt: tuple[str, ...] = ()
    write_ready_artifact_written: bool = False
    write_ready_artifact_path: str | None = None
    final_receipt_ready: bool = False
    final_receipt_blocked_reason: str | None = None
    prepared_receipt_payload: dict[str, object] | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "candidate_valid": self.candidate_valid,
            "human_review_ready": self.human_review_ready,
            "lifeline_write_eligible": self.lifeline_write_eligible,
            "explicit_human_approval": self.explicit_human_approval,
            "auto_approved": self.auto_approved,
            "receipt_written": self.receipt_written,
            "receipt_path": self.receipt_path,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "reviewer_action": self.reviewer_action,
            "proof_reference_pack_path": self.proof_reference_pack_path,
            "lifeline_boundary_statement": self.lifeline_boundary_statement,
            "missing_references": list(self.missing_references),
            "current_validation_debt": list(self.current_validation_debt),
            "known_ambient_debt": list(self.known_ambient_debt),
            "write_ready_artifact_written": self.write_ready_artifact_written,
            "write_ready_artifact_path": self.write_ready_artifact_path,
            "final_receipt_ready": self.final_receipt_ready,
            "final_receipt_blocked_reason": self.final_receipt_blocked_reason,
            "prepared_receipt_payload": self.prepared_receipt_payload,
        }


def _coerce_approval(value: LifelineWriteApproval | dict[str, Any]) -> LifelineWriteApproval:
    if isinstance(value, LifelineWriteApproval):
        return value
    payload = _require_object(value, "approval")
    return LifelineWriteApproval(
        explicit_human_approval=_require_bool(
            payload.get("explicit_human_approval"),
            "approval.explicit_human_approval",
        ),
        approved_at=_optional_string(payload.get("approved_at"), "approval.approved_at"),
        reviewer_id=_optional_string(payload.get("reviewer_id"), "approval.reviewer_id"),
        reviewer_label=_optional_string(payload.get("reviewer_label"), "approval.reviewer_label"),
        approval_note=_optional_string(payload.get("approval_note"), "approval.approval_note"),
    )


def _coerce_lifeline_receipt_input(
    value: LifelineReceiptInput | dict[str, Any] | None,
    *,
    root: Path,
) -> dict[str, object] | None:
    if value is None:
        return None
    if isinstance(value, LifelineReceiptInput):
        return value.to_payload(root=root)
    payload = _require_object(value, "lifeline_receipt_input")
    if "proof_summary_ref" in payload:
        return LifelineReceiptInput(
            source_repo_id=_require_non_empty_string(
                payload.get("source_repo_id"),
                "lifeline_receipt_input.source_repo_id",
            ),
            tranche_id=_require_non_empty_string(
                payload.get("tranche_id"),
                "lifeline_receipt_input.tranche_id",
            ),
            proof_summary_ref=_require_non_empty_string(
                payload.get("proof_summary_ref"),
                "lifeline_receipt_input.proof_summary_ref",
            ),
        ).to_payload(root=root)
    return {
        "source_repo_id": _require_non_empty_string(
            payload.get("source_repo_id"),
            "lifeline_receipt_input.source_repo_id",
        ),
        "tranche_id": _require_non_empty_string(
            payload.get("tranche_id"),
            "lifeline_receipt_input.tranche_id",
        ),
        "proof_summary": _require_object(
            payload.get("proof_summary"),
            "lifeline_receipt_input.proof_summary",
        ),
        "proof_refs": _require_object(
            payload.get("proof_refs"),
            "lifeline_receipt_input.proof_refs",
        ),
        "source_refs": list(_ordered_unique_strings(payload.get("source_refs"), "lifeline_receipt_input.source_refs")),
    }


def _load_pack_payload(
    proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None,
    *,
    root: Path,
) -> tuple[dict[str, Any], Path]:
    default_path = default_proof_reference_pack_latest_json_path(root).resolve()
    if isinstance(proof_reference_pack, CortexProofReferencePack):
        return proof_reference_pack.to_payload(root=root), default_path
    if isinstance(proof_reference_pack, dict):
        return proof_reference_pack, default_path

    artifact_path = (
        Path(proof_reference_pack).resolve()
        if isinstance(proof_reference_pack, (str, Path))
        else default_path
    )
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Proof reference pack not found at {normalize_slashes(str(artifact_path))}."
        )
    return read_json(artifact_path), artifact_path


def _pack_path_ref(path: Path, *, root: Path) -> str:
    return normalize_slashes(atlas_relative(path, root=root))


def _boundary_statement_from_pack(payload: dict[str, Any]) -> str | None:
    references = payload.get("references")
    if not isinstance(references, list):
        return None
    prefix = "Boundary statement="
    for item in references:
        if not isinstance(item, dict):
            continue
        if item.get("kind") != "cortex_receipt_handoff_draft":
            continue
        notes = item.get("notes")
        if not isinstance(notes, list):
            continue
        for note in notes:
            if not isinstance(note, str) or not note.startswith(prefix):
                continue
            statement = " ".join(note[len(prefix) :].strip().split())
            if statement:
                return statement
    return None


def _extract_lifeline_receipt_input(payload: dict[str, Any]) -> dict[str, Any] | None:
    value = payload.get("lifeline_receipt_input")
    return value if isinstance(value, dict) else None


def _missing_lifeline_receipt_inputs(payload: dict[str, Any]) -> tuple[str, ...]:
    lifeline_input = _extract_lifeline_receipt_input(payload)
    required_paths = (
        ("source_repo_id",),
        ("tranche_id",),
        ("proof_summary", "owner_repo_id"),
        ("proof_summary", "summary_ref"),
        ("proof_summary", "report_id"),
        ("proof_refs", "semantic_report_ref"),
        ("proof_refs", "visual_report_ref"),
        ("source_refs",),
    )
    missing: list[str] = []
    for path_parts in required_paths:
        cursor: Any = lifeline_input
        for part in path_parts:
            if not isinstance(cursor, dict) or part not in cursor:
                cursor = None
                break
            cursor = cursor.get(part)
        field_label = ".".join(path_parts)
        if path_parts == ("source_refs",):
            if not isinstance(cursor, list) or not any(isinstance(item, str) and item.strip() for item in cursor):
                missing.append(field_label)
            continue
        if not isinstance(cursor, str) or not cursor.strip():
            missing.append(field_label)
    if lifeline_input is not None:
        source_repo_id = lifeline_input.get("source_repo_id")
        proof_summary = lifeline_input.get("proof_summary")
        if (
            isinstance(source_repo_id, str)
            and source_repo_id.strip()
            and isinstance(proof_summary, dict)
            and isinstance(proof_summary.get("owner_repo_id"), str)
            and proof_summary.get("owner_repo_id", "").strip()
            and proof_summary.get("owner_repo_id", "").strip() != source_repo_id.strip()
        ):
            missing.append("proof_summary.owner_repo_id_matches_source_repo_id")
    return tuple(missing)


def _final_receipt_blocked_reason(missing_fields: tuple[str, ...]) -> str | None:
    if not missing_fields:
        return None
    return (
        "Lifeline final receipt emission remains ambiguous for Cortex proof-reference packs; "
        f"missing mapped inputs: {', '.join(missing_fields)}."
    )


def _gating_blocked_reason(
    validation: LifelineReceiptCandidateValidation,
    *,
    approval: LifelineWriteApproval,
) -> str | None:
    if validation.auto_approved:
        return "auto_approved must remain false."
    if not validation.candidate_valid:
        return validation.blocked_reason or "Candidate validation failed."
    if validation.missing_references:
        return f"Missing required proof references: {', '.join(validation.missing_references)}."
    if not validation.human_review_ready:
        return validation.blocked_reason or "human_review_ready is false."
    if not validation.lifeline_write_eligible:
        if validation.current_validation_debt:
            return validation.current_validation_debt[0]
        return validation.blocked_reason or "lifeline_write_eligible is false."
    if not approval.explicit_human_approval:
        return "Explicit human approval is required before any Lifeline write path."
    if validation.current_validation_debt:
        return validation.current_validation_debt[0]
    return None


def _reviewer_action(
    *,
    blocked: bool,
    blocked_reason: str | None,
    final_receipt_ready: bool,
    final_receipt_blocked_reason: str | None,
    write_ready_artifact_path: str | None,
) -> str:
    if blocked:
        return (
            "Do not write any Lifeline artifact: "
            f"{blocked_reason or 'the Cortex candidate is not eligible for approval-gated write preparation.'}"
        )
    if final_receipt_ready:
        return (
            "Explicit human approval is recorded. The candidate is ready for a narrow Lifeline final receipt write."
        )
    if write_ready_artifact_path is not None:
        return (
            "Explicit human approval is recorded. Cortex persisted a write-ready artifact only; "
            f"final Lifeline receipt emission is still withheld because {final_receipt_blocked_reason or 'the owner-repo mapping remains ambiguous'}"
        )
    return (
        "Explicit human approval is recorded. Prepare-only mode applies; "
        f"final Lifeline receipt emission is still withheld because {final_receipt_blocked_reason or 'the owner-repo mapping remains ambiguous'}"
    )


def _prepared_payload(
    *,
    result: LifelineWriteAdapterResult,
    approval: LifelineWriteApproval,
    proof_reference_pack_digest: str,
    required_lifeline_inputs_missing: tuple[str, ...],
    selected_next_action: str,
    lifeline_receipt_input: dict[str, object] | None,
) -> dict[str, object]:
    payload = {
        "contract_version": LIFELINE_WRITE_READY_CONTRACT_VERSION,
        "run_id": result.run_id,
        "selected_next_action": selected_next_action,
        "proof_reference_pack_path": result.proof_reference_pack_path,
        "proof_reference_pack_digest": proof_reference_pack_digest,
        "candidate_valid": result.candidate_valid,
        "human_review_ready": result.human_review_ready,
        "lifeline_write_eligible": result.lifeline_write_eligible,
        "explicit_human_approval": result.explicit_human_approval,
        "auto_approved": False,
        "blocked": result.blocked,
        "blocked_reason": result.blocked_reason,
        "reviewer_action": result.reviewer_action,
        "lifeline_boundary_statement": result.lifeline_boundary_statement,
        "missing_references": list(result.missing_references),
        "current_validation_debt": list(result.current_validation_debt),
        "known_ambient_debt": list(result.known_ambient_debt),
        "approval": approval.to_payload(),
        "final_receipt_owner": "lifeline",
        "final_receipt_ready": result.final_receipt_ready,
        "final_receipt_blocked_reason": result.final_receipt_blocked_reason,
        "required_lifeline_inputs_missing": list(required_lifeline_inputs_missing),
        "write_scope": "cortex_write_ready_artifact_only",
    }
    if lifeline_receipt_input is not None:
        payload["lifeline_receipt_input"] = lifeline_receipt_input
    return payload


class LifelineWriteAdapter:
    def prepare(
        self,
        proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
        *,
        approval: LifelineWriteApproval | dict[str, Any],
        lifeline_receipt_input: LifelineReceiptInput | dict[str, Any] | None = None,
        root: Path | None = None,
    ) -> LifelineWriteAdapterResult:
        base = (root or atlas_root()).resolve()
        resolved_approval = _coerce_approval(approval)
        resolved_lifeline_receipt_input = _coerce_lifeline_receipt_input(
            lifeline_receipt_input,
            root=base,
        )
        pack_payload, pack_path = _load_pack_payload(proof_reference_pack, root=base)
        if resolved_lifeline_receipt_input is not None:
            pack_payload = {**pack_payload, "lifeline_receipt_input": resolved_lifeline_receipt_input}
        validation = validate_lifeline_receipt_candidate(proof_reference_pack, root=base)
        pack_path_ref = _pack_path_ref(pack_path, root=base)
        boundary_statement = _boundary_statement_from_pack(pack_payload)
        gating_blocked_reason = _gating_blocked_reason(validation, approval=resolved_approval)
        blocked = gating_blocked_reason is not None
        required_lifeline_inputs_missing = _missing_lifeline_receipt_inputs(pack_payload)
        final_receipt_ready = not blocked and not required_lifeline_inputs_missing
        final_receipt_blocked_reason = _final_receipt_blocked_reason(required_lifeline_inputs_missing)
        result = LifelineWriteAdapterResult(
            run_id=validation.run_id,
            candidate_valid=validation.candidate_valid,
            human_review_ready=validation.human_review_ready,
            lifeline_write_eligible=validation.lifeline_write_eligible,
            explicit_human_approval=resolved_approval.explicit_human_approval,
            auto_approved=False,
            receipt_written=False,
            receipt_path=None,
            blocked=blocked,
            blocked_reason=gating_blocked_reason,
            reviewer_action="",
            proof_reference_pack_path=pack_path_ref,
            lifeline_boundary_statement=boundary_statement,
            missing_references=validation.missing_references,
            current_validation_debt=validation.current_validation_debt,
            known_ambient_debt=validation.known_ambient_debt,
            final_receipt_ready=final_receipt_ready,
            final_receipt_blocked_reason=final_receipt_blocked_reason,
        )
        prepared = _prepared_payload(
            result=result,
            approval=resolved_approval,
            proof_reference_pack_digest=stable_json_digest(pack_payload),
            required_lifeline_inputs_missing=required_lifeline_inputs_missing,
            selected_next_action=_require_non_empty_string(
                pack_payload.get("selected_next_action"),
                "selected_next_action",
            ),
            lifeline_receipt_input=resolved_lifeline_receipt_input,
        )
        reviewer_action = _reviewer_action(
            blocked=blocked,
            blocked_reason=gating_blocked_reason,
            final_receipt_ready=final_receipt_ready,
            final_receipt_blocked_reason=final_receipt_blocked_reason,
            write_ready_artifact_path=None,
        )
        prepared["reviewer_action"] = reviewer_action
        return LifelineWriteAdapterResult(
            **{
                **result.__dict__,
                "reviewer_action": reviewer_action,
                "prepared_receipt_payload": prepared,
            }
        )

    def write(
        self,
        proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
        *,
        approval: LifelineWriteApproval | dict[str, Any],
        lifeline_receipt_input: LifelineReceiptInput | dict[str, Any] | None = None,
        root: Path | None = None,
        write_ready_artifact_path: Path | None = None,
        lifeline_write_ready_root: Path | None = None,
    ) -> LifelineWriteAdapterResult:
        base = (root or atlas_root()).resolve()
        prepared = self.prepare(
            proof_reference_pack,
            approval=approval,
            lifeline_receipt_input=lifeline_receipt_input,
            root=base,
        )
        if prepared.blocked or prepared.prepared_receipt_payload is None:
            return prepared

        latest_path = default_lifeline_write_ready_latest_json_path(
            base,
            lifeline_write_ready_root=lifeline_write_ready_root,
        )
        resolved_path = (
            write_ready_artifact_path.resolve()
            if write_ready_artifact_path is not None
            else default_lifeline_write_ready_run_json_path(
                prepared.run_id,
                base,
                lifeline_write_ready_root=lifeline_write_ready_root,
            )
        )
        write_json_if_changed(latest_path, prepared.prepared_receipt_payload)
        write_json_if_changed(resolved_path, prepared.prepared_receipt_payload)
        artifact_ref = _pack_path_ref(resolved_path, root=base)
        reviewer_action = _reviewer_action(
            blocked=False,
            blocked_reason=None,
            final_receipt_ready=prepared.final_receipt_ready,
            final_receipt_blocked_reason=prepared.final_receipt_blocked_reason,
            write_ready_artifact_path=artifact_ref,
        )
        payload = dict(prepared.prepared_receipt_payload)
        payload["reviewer_action"] = reviewer_action
        payload["write_ready_artifact_path"] = artifact_ref
        return LifelineWriteAdapterResult(
            **{
                **prepared.__dict__,
                "reviewer_action": reviewer_action,
                "write_ready_artifact_written": True,
                "write_ready_artifact_path": artifact_ref,
                "prepared_receipt_payload": payload,
            }
        )


def prepare_lifeline_receipt_payload(
    proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
    *,
    approval: LifelineWriteApproval | dict[str, Any],
    lifeline_receipt_input: LifelineReceiptInput | dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, object]:
    result = LifelineWriteAdapter().prepare(
        proof_reference_pack,
        approval=approval,
        lifeline_receipt_input=lifeline_receipt_input,
        root=root,
    )
    return dict(result.prepared_receipt_payload or {})


def write_lifeline_receipt_with_approval(
    proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
    *,
    approval: LifelineWriteApproval | dict[str, Any],
    lifeline_receipt_input: LifelineReceiptInput | dict[str, Any] | None = None,
    root: Path | None = None,
    write_ready_artifact_path: Path | None = None,
    lifeline_write_ready_root: Path | None = None,
) -> LifelineWriteAdapterResult:
    return LifelineWriteAdapter().write(
        proof_reference_pack,
        approval=approval,
        lifeline_receipt_input=lifeline_receipt_input,
        root=root,
        write_ready_artifact_path=write_ready_artifact_path,
        lifeline_write_ready_root=lifeline_write_ready_root,
    )
