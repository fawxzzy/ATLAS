from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import read_json, stable_json_digest, write_json_if_changed
from ops.cortex.lifeline_write_adapter import (
    LIFELINE_WRITE_READY_CONTRACT_VERSION,
    default_lifeline_write_ready_latest_json_path,
)

LIFELINE_RECEIPT_CANDIDATE_CONTRACT_VERSION = "atlas.cortex.lifeline-receipt-candidate.v1"
LIFELINE_PROOF_REFERENCE_RECEIPT_CONTRACT_VERSION = "atlas.lifeline.proof-reference.receipt.v1"
LIFELINE_PROOF_REFERENCE_RECEIPT_RUNNER_VERSION = "cortex.lifeline-receipt-payload.v1"


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


def _lifeline_owner_boundary_statement(boundary_statement: str) -> str:
    normalized = _require_non_empty_string(boundary_statement, "lifeline_boundary_statement")
    lowered = normalized.lower()
    if (
        "cortex" in lowered
        and "lifeline" in lowered
        and "final receipt truth" in lowered
    ):
        return normalized
    return (
        "Cortex prepared the proof-reference material, but Lifeline owns final receipt truth "
        "and writes the final receipt only after explicit human approval. "
        f"Source boundary context: {normalized}"
    )


def _run_artifact_stem(run_id: str) -> str:
    normalized = normalize_slashes(_require_non_empty_string(run_id, "run_id"))
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized.replace("/", "__"))
    stem = sanitized.strip(".-")
    if not stem:
        raise ValueError("Expected run_id to produce a usable artifact filename.")
    return stem


def _resolved_candidate_dir(
    *,
    root: Path | None = None,
    candidate_root: Path | None = None,
) -> Path:
    base = (root or atlas_root()).resolve()
    return (
        candidate_root.resolve()
        if candidate_root is not None
        else base / "runtime" / "cortex" / "lifeline-receipt-candidates"
    )


def default_lifeline_receipt_candidate_dir(root: Path | None = None) -> Path:
    return _resolved_candidate_dir(root=root)


def default_lifeline_receipt_candidate_latest_json_path(
    root: Path | None = None,
    *,
    candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(root=root, candidate_root=candidate_root) / "latest.json"


def default_lifeline_receipt_candidate_latest_summary_path(
    root: Path | None = None,
    *,
    candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(root=root, candidate_root=candidate_root) / "latest.txt"


def default_lifeline_receipt_candidate_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(root=root, candidate_root=candidate_root) / "runs" / f"{_run_artifact_stem(run_id)}.json"


def default_lifeline_receipt_candidate_run_summary_path(
    run_id: str,
    root: Path | None = None,
    *,
    candidate_root: Path | None = None,
) -> Path:
    return _resolved_candidate_dir(root=root, candidate_root=candidate_root) / "runs" / f"{_run_artifact_stem(run_id)}.txt"


def default_lifeline_receipt_schema_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "repos" / "fawxzzy-lifeline" / "schemas" / "proof-reference-receipt.schema.json"


@dataclass(frozen=True)
class LifelineReceiptPayloadValidation:
    schema_ref: str
    validation_mode: str
    valid: bool
    errors: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_ref": self.schema_ref,
            "validation_mode": self.validation_mode,
            "valid": self.valid,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class LifelineReceiptCandidateArtifact:
    run_id: str
    selected_next_action: str
    reviewer_action: str
    approval_note: str
    source_cortex_artifact_refs: tuple[str, ...]
    candidate_payload: dict[str, object]
    candidate_payload_digest: str
    schema_validation: LifelineReceiptPayloadValidation
    final_receipt_written: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": LIFELINE_RECEIPT_CANDIDATE_CONTRACT_VERSION,
            "run_id": self.run_id,
            "selected_next_action": self.selected_next_action,
            "reviewer_action": self.reviewer_action,
            "approval_note": self.approval_note,
            "source_cortex_artifact_refs": list(self.source_cortex_artifact_refs),
            "candidate_payload": self.candidate_payload,
            "candidate_payload_digest": self.candidate_payload_digest,
            "schema_validation": self.schema_validation.to_payload(),
            "final_receipt_owner": "lifeline",
            "final_receipt_written": self.final_receipt_written,
            "write_scope": "cortex_candidate_payload_only",
        }


def _write_summary(path: Path, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")


def _load_write_ready_payload(
    write_ready_artifact: str | Path | None,
    *,
    root: Path,
) -> tuple[dict[str, Any], Path]:
    artifact_path = (
        Path(write_ready_artifact).resolve()
        if isinstance(write_ready_artifact, (str, Path))
        else default_lifeline_write_ready_latest_json_path(root).resolve()
    )
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Cortex write-ready artifact not found at {normalize_slashes(str(artifact_path))}."
        )
    payload = read_json(artifact_path)
    if payload.get("contract_version") != LIFELINE_WRITE_READY_CONTRACT_VERSION:
        raise ValueError(
            f"Malformed Cortex write-ready artifact at {normalize_slashes(str(artifact_path))}: "
            f"expected contract_version {LIFELINE_WRITE_READY_CONTRACT_VERSION}."
        )
    return payload, artifact_path


def _receipt_id(payload: dict[str, object]) -> str:
    return stable_json_digest(
        {
            "run_id": payload["receipt_id_input_run_id"],
            "source_repo_id": payload["source_repo_id"],
            "tranche_id": payload["tranche_id"],
            "proof_reference_pack_digest": payload["source_artifacts"]["proof_reference_pack_digest"],
            "approval_note": payload["approval"]["approval_note"],
        }
    )


def _build_candidate_payload(
    payload: dict[str, Any],
    *,
    artifact_path: Path,
    root: Path,
) -> dict[str, object]:
    run_id = _require_non_empty_string(payload.get("run_id"), "run_id")
    selected_next_action = _require_non_empty_string(
        payload.get("selected_next_action"),
        "selected_next_action",
    )
    proof_reference_pack_path = normalize_slashes(
        _require_non_empty_string(payload.get("proof_reference_pack_path"), "proof_reference_pack_path")
    )
    proof_reference_pack_digest = _require_non_empty_string(
        payload.get("proof_reference_pack_digest"),
        "proof_reference_pack_digest",
    )
    reviewer_action = _require_non_empty_string(payload.get("reviewer_action"), "reviewer_action")
    boundary_statement = _lifeline_owner_boundary_statement(
        payload.get("lifeline_boundary_statement"),
    )
    lifeline_input = _require_object(payload.get("lifeline_receipt_input"), "lifeline_receipt_input")
    approval = _require_object(payload.get("approval"), "approval")
    explicit_human_approval = _require_bool(
        approval.get("explicit_human_approval"),
        "approval.explicit_human_approval",
    )
    approved_at = _require_non_empty_string(approval.get("approved_at"), "approval.approved_at")
    approval_note = _require_non_empty_string(approval.get("approval_note"), "approval.approval_note")
    reviewer_id = _optional_string(approval.get("reviewer_id"), "approval.reviewer_id")
    reviewer_label = _optional_string(approval.get("reviewer_label"), "approval.reviewer_label")
    if reviewer_id is None and reviewer_label is None:
        raise ValueError("Malformed Cortex write-ready artifact: approval requires reviewer_id or reviewer_label.")
    if _require_bool(payload.get("auto_approved"), "auto_approved"):
        raise ValueError("Malformed Cortex write-ready artifact: auto_approved must remain false.")
    current_validation_debt = _ordered_unique_strings(
        payload.get("current_validation_debt"),
        "current_validation_debt",
    )
    if current_validation_debt:
        raise ValueError(
            "Cortex write-ready artifact is not eligible for a Lifeline-compatible candidate payload "
            "while current_validation_debt is non-empty."
        )
    known_ambient_debt = _ordered_unique_strings(payload.get("known_ambient_debt"), "known_ambient_debt")
    source_repo_id = _require_non_empty_string(lifeline_input.get("source_repo_id"), "lifeline_receipt_input.source_repo_id")
    tranche_id = _require_non_empty_string(lifeline_input.get("tranche_id"), "lifeline_receipt_input.tranche_id")
    proof_summary = _require_object(lifeline_input.get("proof_summary"), "lifeline_receipt_input.proof_summary")
    proof_refs = _require_object(lifeline_input.get("proof_refs"), "lifeline_receipt_input.proof_refs")
    summary_ref = normalize_slashes(_require_non_empty_string(proof_summary.get("summary_ref"), "proof_summary.summary_ref"))
    semantic_ref = normalize_slashes(
        _require_non_empty_string(proof_refs.get("semantic_report_ref"), "proof_refs.semantic_report_ref")
    )
    visual_ref = normalize_slashes(
        _require_non_empty_string(proof_refs.get("visual_report_ref"), "proof_refs.visual_report_ref")
    )
    source_refs = list(
        _ordered_unique_strings(
            [
                proof_reference_pack_path,
                normalize_slashes(atlas_relative(artifact_path, root=root)),
                summary_ref,
                semantic_ref,
                visual_ref,
                *list(_ordered_unique_strings(lifeline_input.get("source_refs"), "lifeline_receipt_input.source_refs")),
            ],
            "source_refs",
        )
    )
    approval_payload: dict[str, object] = {
        "explicit_human_approval": explicit_human_approval,
        "auto_approved": False,
        "approved_at": approved_at,
        "approval_note": approval_note,
    }
    if reviewer_id is not None:
        approval_payload["reviewer_id"] = reviewer_id
    if reviewer_label is not None:
        approval_payload["reviewer_label"] = reviewer_label
    proof_refs_payload: dict[str, object] = {
        "semantic_report_ref": semantic_ref,
        "visual_report_ref": visual_ref,
    }
    semantic_report_id = _optional_string(proof_refs.get("semantic_report_id"), "proof_refs.semantic_report_id")
    visual_report_id = _optional_string(proof_refs.get("visual_report_id"), "proof_refs.visual_report_id")
    if semantic_report_id is not None:
        proof_refs_payload["semantic_report_id"] = semantic_report_id
    if visual_report_id is not None:
        proof_refs_payload["visual_report_id"] = visual_report_id
    candidate_payload: dict[str, object] = {
        "contract_version": LIFELINE_PROOF_REFERENCE_RECEIPT_CONTRACT_VERSION,
        "receipt_id_input_run_id": run_id,
        "emitted_at": approved_at,
        "runner_version": LIFELINE_PROOF_REFERENCE_RECEIPT_RUNNER_VERSION,
        "status": "proof_reference_accepted",
        "source_repo_id": source_repo_id,
        "tranche_id": tranche_id,
        "source_artifacts": {
            "proof_reference_pack_ref": proof_reference_pack_path,
            "proof_reference_pack_digest": proof_reference_pack_digest,
            "write_ready_artifact_ref": normalize_slashes(atlas_relative(artifact_path, root=root)),
        },
        "approval": approval_payload,
        "boundary": {
            "final_receipt_owner": "lifeline",
            "prepared_by": "cortex",
            "statement": boundary_statement,
        },
        "proof_summary": {
            "owner_repo_id": _require_non_empty_string(proof_summary.get("owner_repo_id"), "proof_summary.owner_repo_id"),
            "summary_ref": summary_ref,
            "report_id": _require_non_empty_string(proof_summary.get("report_id"), "proof_summary.report_id"),
        },
        "proof_refs": proof_refs_payload,
        "source_refs": source_refs,
        "validation_context": {
            "known_ambient_debt": list(known_ambient_debt),
            "current_validation_debt": [],
        },
    }
    candidate_payload["receipt_id"] = _receipt_id(candidate_payload)
    del candidate_payload["receipt_id_input_run_id"]
    return {
        "run_id": run_id,
        "selected_next_action": selected_next_action,
        "reviewer_action": reviewer_action,
        "approval_note": approval_note,
        "candidate_payload": candidate_payload,
    }


def validate_lifeline_receipt_payload(
    candidate_payload: dict[str, Any],
    *,
    root: Path | None = None,
) -> LifelineReceiptPayloadValidation:
    base = (root or atlas_root()).resolve()
    errors: list[str] = []
    expected_fields = {
        "contract_version",
        "receipt_id",
        "emitted_at",
        "runner_version",
        "status",
        "source_repo_id",
        "tranche_id",
        "source_artifacts",
        "approval",
        "boundary",
        "proof_summary",
        "proof_refs",
        "source_refs",
        "validation_context",
    }
    if set(candidate_payload.keys()) != expected_fields:
        missing = sorted(expected_fields - set(candidate_payload.keys()))
        extras = sorted(set(candidate_payload.keys()) - expected_fields)
        if missing:
            errors.append(f"Missing top-level fields: {', '.join(missing)}.")
        if extras:
            errors.append(f"Unexpected top-level fields: {', '.join(extras)}.")
    if candidate_payload.get("contract_version") != LIFELINE_PROOF_REFERENCE_RECEIPT_CONTRACT_VERSION:
        errors.append(
            f"contract_version must be '{LIFELINE_PROOF_REFERENCE_RECEIPT_CONTRACT_VERSION}'."
        )
    if candidate_payload.get("status") != "proof_reference_accepted":
        errors.append("status must be 'proof_reference_accepted'.")
    for field in ("receipt_id", "emitted_at", "runner_version", "source_repo_id", "tranche_id"):
        if not isinstance(candidate_payload.get(field), str) or not str(candidate_payload.get(field)).strip():
            errors.append(f"{field} must be a non-empty string.")
    source_artifacts = candidate_payload.get("source_artifacts")
    if not isinstance(source_artifacts, dict):
        errors.append("source_artifacts must be an object.")
    else:
        for field in ("proof_reference_pack_ref", "proof_reference_pack_digest", "write_ready_artifact_ref"):
            if not isinstance(source_artifacts.get(field), str) or not str(source_artifacts.get(field)).strip():
                errors.append(f"source_artifacts.{field} must be a non-empty string.")
    approval = candidate_payload.get("approval")
    if not isinstance(approval, dict):
        errors.append("approval must be an object.")
    else:
        if approval.get("explicit_human_approval") is not True:
            errors.append("approval.explicit_human_approval must be true.")
        if approval.get("auto_approved") is not False:
            errors.append("approval.auto_approved must be false.")
        for field in ("approved_at", "approval_note"):
            if not isinstance(approval.get(field), str) or not str(approval.get(field)).strip():
                errors.append(f"approval.{field} must be a non-empty string.")
        if not any(
            isinstance(approval.get(field), str) and str(approval.get(field)).strip()
            for field in ("reviewer_id", "reviewer_label")
        ):
            errors.append("approval requires reviewer_id or reviewer_label.")
    boundary = candidate_payload.get("boundary")
    if not isinstance(boundary, dict):
        errors.append("boundary must be an object.")
    else:
        if boundary.get("final_receipt_owner") != "lifeline":
            errors.append("boundary.final_receipt_owner must be 'lifeline'.")
        if boundary.get("prepared_by") != "cortex":
            errors.append("boundary.prepared_by must be 'cortex'.")
        if not isinstance(boundary.get("statement"), str) or not str(boundary.get("statement")).strip():
            errors.append("boundary.statement must be a non-empty string.")
    proof_summary = candidate_payload.get("proof_summary")
    if not isinstance(proof_summary, dict):
        errors.append("proof_summary must be an object.")
    else:
        for field in ("owner_repo_id", "summary_ref", "report_id"):
            if not isinstance(proof_summary.get(field), str) or not str(proof_summary.get(field)).strip():
                errors.append(f"proof_summary.{field} must be a non-empty string.")
    proof_refs = candidate_payload.get("proof_refs")
    if not isinstance(proof_refs, dict):
        errors.append("proof_refs must be an object.")
    else:
        for field in ("semantic_report_ref", "visual_report_ref"):
            if not isinstance(proof_refs.get(field), str) or not str(proof_refs.get(field)).strip():
                errors.append(f"proof_refs.{field} must be a non-empty string.")
        for field in ("semantic_report_id", "visual_report_id"):
            value = proof_refs.get(field)
            if value is not None and (not isinstance(value, str) or not str(value).strip()):
                errors.append(f"proof_refs.{field} must be a non-empty string when present.")
    source_refs = candidate_payload.get("source_refs")
    if not isinstance(source_refs, list) or len(source_refs) < 5:
        errors.append("source_refs must contain at least five non-empty string refs.")
    validation_context = candidate_payload.get("validation_context")
    if not isinstance(validation_context, dict):
        errors.append("validation_context must be an object.")
    else:
        known_ambient_debt = validation_context.get("known_ambient_debt")
        current_validation_debt = validation_context.get("current_validation_debt")
        if not isinstance(known_ambient_debt, list) or not all(
            isinstance(item, str) and item.strip() for item in known_ambient_debt
        ):
            errors.append("validation_context.known_ambient_debt must be an array of non-empty strings.")
        if not isinstance(current_validation_debt, list) or current_validation_debt:
            errors.append("validation_context.current_validation_debt must be an empty array.")
    if (
        isinstance(proof_summary, dict)
        and isinstance(candidate_payload.get("source_repo_id"), str)
        and proof_summary.get("owner_repo_id") != candidate_payload.get("source_repo_id")
    ):
        errors.append("proof_summary.owner_repo_id must match source_repo_id.")
    if isinstance(source_refs, list) and isinstance(source_artifacts, dict) and isinstance(proof_summary, dict) and isinstance(proof_refs, dict):
        required_refs = {
            source_artifacts.get("proof_reference_pack_ref"),
            source_artifacts.get("write_ready_artifact_ref"),
            proof_summary.get("summary_ref"),
            proof_refs.get("semantic_report_ref"),
            proof_refs.get("visual_report_ref"),
        }
        missing_refs = sorted(
            str(item)
            for item in required_refs
            if isinstance(item, str) and item not in source_refs
        )
        if missing_refs:
            errors.append(f"source_refs is missing required refs: {', '.join(missing_refs)}.")
    return LifelineReceiptPayloadValidation(
        schema_ref=normalize_slashes(atlas_relative(default_lifeline_receipt_schema_path(base), root=base)),
        validation_mode="structural",
        valid=not errors,
        errors=tuple(errors),
    )


def render_lifeline_receipt_candidate_summary(artifact: LifelineReceiptCandidateArtifact) -> str:
    lines = [
        "Cortex Lifeline Receipt Candidate",
        f"- Run id: {artifact.run_id}",
        f"- Selected next action: {artifact.selected_next_action}",
        f"- Reviewer action: {artifact.reviewer_action}",
        f"- Candidate payload valid: {'yes' if artifact.schema_validation.valid else 'no'}",
        f"- Final receipt written: {'yes' if artifact.final_receipt_written else 'no'}",
        f"- Source Cortex artifact refs: {' | '.join(artifact.source_cortex_artifact_refs)}",
    ]
    if artifact.schema_validation.errors:
        lines.append(f"- Validation errors: {' | '.join(artifact.schema_validation.errors)}")
    else:
        lines.append("- Validation errors: none")
    return "\n".join(lines) + "\n"


def build_lifeline_receipt_candidate(
    write_ready_artifact: str | Path | None = None,
    *,
    root: Path | None = None,
) -> LifelineReceiptCandidateArtifact:
    base = (root or atlas_root()).resolve()
    payload, artifact_path = _load_write_ready_payload(write_ready_artifact, root=base)
    built = _build_candidate_payload(payload, artifact_path=artifact_path, root=base)
    candidate_payload = built["candidate_payload"]
    validation = validate_lifeline_receipt_payload(candidate_payload, root=base)
    if not validation.valid:
        raise ValueError(
            "Lifeline receipt candidate payload failed structural compatibility validation: "
            + "; ".join(validation.errors)
        )
    write_ready_ref = normalize_slashes(atlas_relative(artifact_path, root=base))
    source_artifacts = candidate_payload.get("source_artifacts", {})
    proof_reference_pack_ref = (
        str(source_artifacts.get("proof_reference_pack_ref"))
        if isinstance(source_artifacts, dict)
        else ""
    )
    return LifelineReceiptCandidateArtifact(
        run_id=str(built["run_id"]),
        selected_next_action=str(built["selected_next_action"]),
        reviewer_action=str(built["reviewer_action"]),
        approval_note=str(built["approval_note"]),
        source_cortex_artifact_refs=(proof_reference_pack_ref, write_ready_ref),
        candidate_payload=candidate_payload,
        candidate_payload_digest=stable_json_digest(candidate_payload),
        schema_validation=validation,
        final_receipt_written=False,
    )


def write_lifeline_receipt_candidate(
    write_ready_artifact: str | Path | None = None,
    *,
    root: Path | None = None,
    candidate_root: Path | None = None,
) -> LifelineReceiptCandidateArtifact:
    base = (root or atlas_root()).resolve()
    artifact = build_lifeline_receipt_candidate(write_ready_artifact, root=base)
    payload = artifact.to_payload()
    summary = render_lifeline_receipt_candidate_summary(artifact)
    latest_json_path = default_lifeline_receipt_candidate_latest_json_path(base, candidate_root=candidate_root)
    latest_summary_path = default_lifeline_receipt_candidate_latest_summary_path(base, candidate_root=candidate_root)
    run_json_path = default_lifeline_receipt_candidate_run_json_path(
        artifact.run_id,
        base,
        candidate_root=candidate_root,
    )
    run_summary_path = default_lifeline_receipt_candidate_run_summary_path(
        artifact.run_id,
        base,
        candidate_root=candidate_root,
    )
    write_json_if_changed(latest_json_path, payload)
    write_json_if_changed(run_json_path, payload)
    _write_summary(latest_summary_path, summary)
    _write_summary(run_summary_path, summary)
    return artifact
