from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import read_json, stable_json_digest, write_json
from ops.cortex.feedback import CortexFeedbackResult
from ops.cortex.feedback_artifact import _coerce_feedback_result, default_feedback_latest_json_path
from ops.cortex.loop import CORTEX_RUN_RESULT_CONTRACT_VERSION
from ops.cortex.receipt_handoff import (
    CortexReceiptHandoffDraft,
    _coerce_receipt_handoff_draft,
    default_receipt_handoff_latest_json_path,
)
from ops.cortex.run_ledger import CortexRunLedgerAppliedRules
from ops.cortex.verification_ingest import KNOWN_STACK_VALIDATION_BASELINE, VerificationDebtCounts

CANONICAL_STACK_VALIDATION_COMMAND = "python .\\ops\\validation\\validate_stack.py"
PROOF_REFERENCE_PACK_CONTRACT_VERSION = "atlas.cortex.proof-reference-pack.v1"


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


def _render_list(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


def _render_bool(value: bool) -> str:
    return "yes" if value else "no"


def _run_artifact_stem(run_id: str) -> str:
    normalized = normalize_slashes(_require_non_empty_string(run_id, "run_id"))
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized.replace("/", "__"))
    stem = sanitized.strip(".-")
    if not stem:
        raise ValueError("Expected run_id to produce a usable artifact filename.")
    return stem


def _merged_rule_ids(applied_rules: CortexRunLedgerAppliedRules) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in (
        applied_rules.decision_rule_ids,
        applied_rules.plan_rule_ids,
        applied_rules.rule_ids,
    ):
        for rule_id in group:
            normalized = " ".join(rule_id.strip().split())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return tuple(ordered)


def _merge_ordered_strings(*groups: tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            normalized = normalize_slashes(" ".join(str(value).strip().split()))
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return tuple(ordered)


def _resolved_proof_reference_pack_dir(
    *,
    root: Path | None = None,
    proof_reference_pack_root: Path | None = None,
) -> Path:
    base = (root or atlas_root()).resolve()
    return (
        proof_reference_pack_root.resolve()
        if proof_reference_pack_root is not None
        else base / "runtime" / "cortex" / "proof-reference-packs"
    )


def default_proof_reference_pack_dir(root: Path | None = None) -> Path:
    return _resolved_proof_reference_pack_dir(root=root)


def default_proof_reference_pack_latest_json_path(
    root: Path | None = None,
    *,
    proof_reference_pack_root: Path | None = None,
) -> Path:
    return _resolved_proof_reference_pack_dir(root=root, proof_reference_pack_root=proof_reference_pack_root) / "latest.json"


def default_proof_reference_pack_latest_summary_path(
    root: Path | None = None,
    *,
    proof_reference_pack_root: Path | None = None,
) -> Path:
    return _resolved_proof_reference_pack_dir(root=root, proof_reference_pack_root=proof_reference_pack_root) / "latest.txt"


def default_proof_reference_pack_run_dir(
    root: Path | None = None,
    *,
    proof_reference_pack_root: Path | None = None,
) -> Path:
    return _resolved_proof_reference_pack_dir(root=root, proof_reference_pack_root=proof_reference_pack_root) / "runs"


def default_proof_reference_pack_run_json_path(
    run_id: str,
    root: Path | None = None,
    *,
    proof_reference_pack_root: Path | None = None,
) -> Path:
    return default_proof_reference_pack_run_dir(root=root, proof_reference_pack_root=proof_reference_pack_root) / f"{_run_artifact_stem(run_id)}.json"


def default_proof_reference_pack_run_summary_path(
    run_id: str,
    root: Path | None = None,
    *,
    proof_reference_pack_root: Path | None = None,
) -> Path:
    return default_proof_reference_pack_run_dir(root=root, proof_reference_pack_root=proof_reference_pack_root) / f"{_run_artifact_stem(run_id)}.txt"


@dataclass(frozen=True)
class CortexProofReference:
    reference_id: str
    kind: str
    owner_layer: str
    artifact_path: Path | None
    command: str | None
    claim: str
    status: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        has_artifact_path = self.artifact_path is not None
        has_command = self.command is not None
        if has_artifact_path == has_command:
            raise ValueError("CortexProofReference requires exactly one of artifact_path or command.")

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "reference_id": self.reference_id,
            "kind": self.kind,
            "owner_layer": self.owner_layer,
            "artifact_path": atlas_relative(self.artifact_path, root=base) if self.artifact_path is not None else None,
            "command": self.command,
            "claim": self.claim,
            "status": self.status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CortexProofReferencePack:
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
    applied_rules: CortexRunLedgerAppliedRules
    failure_modes_avoided: tuple[str, ...]
    run_artifact_path: Path
    feedback_artifact_path: Path
    handoff_artifact_path: Path
    targeted_verification_commands: tuple[str, ...]
    stack_validation_command: str
    stack_validation_status: str
    known_ambient_baseline: VerificationDebtCounts
    references: tuple[CortexProofReference, ...]
    rule_statement: str
    pattern_statement: str
    failure_mode_statement: str

    def to_payload(self, *, root: Path | None = None) -> dict[str, object]:
        base = (root or atlas_root()).resolve()
        return {
            "contract_version": PROOF_REFERENCE_PACK_CONTRACT_VERSION,
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
            "applied_rules": self.applied_rules.to_payload(),
            "failure_modes_avoided": list(self.failure_modes_avoided),
            "run_artifact_path": atlas_relative(self.run_artifact_path, root=base),
            "feedback_artifact_path": atlas_relative(self.feedback_artifact_path, root=base),
            "handoff_artifact_path": atlas_relative(self.handoff_artifact_path, root=base),
            "targeted_verification_commands": list(self.targeted_verification_commands),
            "stack_validation": {
                "command": self.stack_validation_command,
                "status": self.stack_validation_status,
                "known_ambient_baseline": self.known_ambient_baseline.to_payload(),
                "known_ambient_debt": list(self.known_ambient_debt),
                "current_validation_debt": list(self.current_validation_debt),
            },
            "references": [reference.to_payload(root=base) for reference in self.references],
            "rule_statement": self.rule_statement,
            "pattern_statement": self.pattern_statement,
            "failure_mode_statement": self.failure_mode_statement,
            "final_receipt_owner": "lifeline",
        }


@dataclass(frozen=True)
class PersistedCortexProofReferencePack:
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
                atlas_relative(self.latest_summary_path, root=base) if self.latest_summary_path is not None else None
            ),
            "run_artifact_path": atlas_relative(self.run_artifact_path, root=base),
            "run_summary_path": (
                atlas_relative(self.run_summary_path, root=base) if self.run_summary_path is not None else None
            ),
            "payload_digest": self.payload_digest,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class _LoadedRunArtifact:
    artifact_path: Path
    run_id: str
    selected_next_action: str
    owner_layer: str
    next_required_layer: str | None
    receipt_ready: bool
    known_ambient_debt: tuple[str, ...]
    verification_expectation: tuple[str, ...]
    touched_files: tuple[str, ...]
    applied_rules: CortexRunLedgerAppliedRules
    failure_modes_avoided: tuple[str, ...]


def _derive_run_id(payload: dict[str, Any], path: Path) -> str:
    explicit = payload.get("run_id")
    if explicit is not None:
        return _require_non_empty_string(explicit, "run_id")
    return _require_non_empty_string(path.name.removesuffix(path.suffix), "run_id")


def _default_run_artifact_candidates(*, root: Path, run_id: str | None) -> tuple[Path, ...]:
    candidates = [root / "runtime" / "cortex" / "runs" / "latest.json"]
    if run_id:
        candidates.append(root / "runtime" / "cortex" / "runs" / f"{_run_artifact_stem(run_id)}.json")
    candidates.append(root / "runtime" / "cortex" / "runs" / "cortex-run-result.latest.json")
    ordered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
    return tuple(ordered)


def _load_feedback_result(
    feedback_artifact: CortexFeedbackResult | dict[str, Any] | str | Path | None,
    *,
    root: Path,
) -> tuple[CortexFeedbackResult, Path]:
    if isinstance(feedback_artifact, CortexFeedbackResult):
        return feedback_artifact, default_feedback_latest_json_path(root).resolve()
    if isinstance(feedback_artifact, dict):
        return _coerce_feedback_result(feedback_artifact), default_feedback_latest_json_path(root).resolve()

    artifact_path = (
        Path(feedback_artifact).resolve()
        if isinstance(feedback_artifact, (str, Path))
        else default_feedback_latest_json_path(root).resolve()
    )
    if not artifact_path.exists():
        raise FileNotFoundError(f"Feedback artifact not found at {normalize_slashes(str(artifact_path))}.")
    try:
        return _coerce_feedback_result(read_json(artifact_path)), artifact_path
    except ValueError as exc:
        raise ValueError(
            f"Malformed Cortex feedback artifact at {normalize_slashes(str(artifact_path))}: {exc}"
        ) from exc


def _load_receipt_handoff_draft(
    handoff_artifact: CortexReceiptHandoffDraft | dict[str, Any] | str | Path | None,
    *,
    root: Path,
) -> tuple[CortexReceiptHandoffDraft, Path]:
    if isinstance(handoff_artifact, CortexReceiptHandoffDraft):
        return handoff_artifact, default_receipt_handoff_latest_json_path(root).resolve()
    if isinstance(handoff_artifact, dict):
        return _coerce_receipt_handoff_draft(handoff_artifact), default_receipt_handoff_latest_json_path(root).resolve()

    artifact_path = (
        Path(handoff_artifact).resolve()
        if isinstance(handoff_artifact, (str, Path))
        else default_receipt_handoff_latest_json_path(root).resolve()
    )
    if not artifact_path.exists():
        raise FileNotFoundError(f"Receipt handoff draft not found at {normalize_slashes(str(artifact_path))}.")
    try:
        return _coerce_receipt_handoff_draft(read_json(artifact_path)), artifact_path
    except ValueError as exc:
        raise ValueError(
            f"Malformed Cortex receipt handoff draft at {normalize_slashes(str(artifact_path))}: {exc}"
        ) from exc


def _coerce_run_artifact_payload(payload: dict[str, Any], path: Path) -> _LoadedRunArtifact:
    if payload.get("contract_version") != CORTEX_RUN_RESULT_CONTRACT_VERSION:
        raise ValueError(f"expected contract_version {CORTEX_RUN_RESULT_CONTRACT_VERSION}.")

    selected_next_action = _require_object(payload.get("selected_next_action"), "selected_next_action")
    proof_receipt_draft = _require_object(payload.get("proof_receipt_draft"), "proof_receipt_draft")
    applied_rule_trace = _require_object(payload.get("applied_rule_trace"), "applied_rule_trace")

    return _LoadedRunArtifact(
        artifact_path=path.resolve(),
        run_id=_derive_run_id(payload, path),
        selected_next_action=_require_non_empty_string(selected_next_action.get("action_id"), "selected_next_action.action_id"),
        owner_layer=_require_non_empty_string(selected_next_action.get("owner_layer"), "selected_next_action.owner_layer"),
        next_required_layer=_optional_string(payload.get("next_required_layer"), "next_required_layer"),
        receipt_ready=_require_bool(payload.get("receipt_ready"), "receipt_ready"),
        known_ambient_debt=_ordered_unique_strings(payload.get("known_ambient_debt"), "known_ambient_debt"),
        verification_expectation=_ordered_unique_strings(payload.get("verification_expectation"), "verification_expectation"),
        touched_files=_ordered_unique_strings(proof_receipt_draft.get("touched_files"), "proof_receipt_draft.touched_files"),
        applied_rules=CortexRunLedgerAppliedRules.from_payload(applied_rule_trace),
        failure_modes_avoided=_ordered_unique_strings(payload.get("failure_modes_avoided"), "failure_modes_avoided"),
    )


def _coerce_run_artifact(path: Path) -> _LoadedRunArtifact:
    try:
        return _coerce_run_artifact_payload(read_json(path), path)
    except ValueError as exc:
        raise ValueError(
            f"Malformed Cortex run artifact at {normalize_slashes(str(path))}: {exc}"
        ) from exc


def _load_run_artifact(
    run_artifact: dict[str, Any] | str | Path | None,
    *,
    root: Path,
    expected_run_id: str | None,
) -> tuple[_LoadedRunArtifact, Path]:
    if isinstance(run_artifact, dict):
        explicit_path = root / "runtime" / "cortex" / "runs" / "latest.json"
        return _coerce_run_artifact_payload(run_artifact, explicit_path), explicit_path.resolve()

    if isinstance(run_artifact, (str, Path)):
        artifact_path = Path(run_artifact).resolve()
        if not artifact_path.exists():
            raise FileNotFoundError(f"Cortex run artifact not found at {normalize_slashes(str(artifact_path))}.")
        return _coerce_run_artifact(artifact_path), artifact_path

    candidates = _default_run_artifact_candidates(root=root, run_id=expected_run_id)
    for candidate in candidates:
        if not candidate.exists():
            continue
        loaded = _coerce_run_artifact(candidate)
        if expected_run_id is None or loaded.run_id == expected_run_id:
            return loaded, candidate

    preferred = candidates[0] if candidates else root / "runtime" / "cortex" / "runs" / "latest.json"
    raise FileNotFoundError(f"Cortex run artifact not found at {normalize_slashes(str(preferred))}.")


def _build_references(
    *,
    run_artifact: _LoadedRunArtifact,
    feedback_artifact_path: Path,
    feedback: CortexFeedbackResult,
    handoff_artifact_path: Path,
    handoff: CortexReceiptHandoffDraft,
) -> tuple[CortexProofReference, ...]:
    notes_for_feedback = (
        f"Targeted verification passed={_render_bool(feedback.targeted_verification_passed)}.",
        f"Stack validation status={feedback.stack_validation_status}.",
        f"Known ambient debt={_render_list(feedback.known_ambient_debt)}.",
        f"Current validation debt={_render_list(feedback.current_validation_debt)}.",
    )
    references: list[CortexProofReference] = [
        CortexProofReference(
            reference_id="run-artifact",
            kind="cortex_run_artifact",
            owner_layer=run_artifact.owner_layer,
            artifact_path=run_artifact.artifact_path,
            command=None,
            claim="CortexRunResult records the selected action, verification expectation, and applied-rule trace for this lane.",
            status="ready" if run_artifact.receipt_ready else "blocked",
            notes=(
                f"Selected next action={run_artifact.selected_next_action}.",
                f"Verification expectation={_render_list(run_artifact.verification_expectation)}.",
            ),
        ),
        CortexProofReference(
            reference_id="feedback-artifact",
            kind="cortex_feedback_artifact",
            owner_layer=feedback.owner_layer,
            artifact_path=feedback_artifact_path,
            command=None,
            claim="CortexFeedbackResult captures targeted verification outcome and separates current validation debt from ambient stack debt.",
            status="blocked" if feedback.blocked else "ready",
            notes=notes_for_feedback,
        ),
        CortexProofReference(
            reference_id="receipt-handoff-draft",
            kind="cortex_receipt_handoff_draft",
            owner_layer=handoff.owner_layer,
            artifact_path=handoff_artifact_path,
            command=None,
            claim="CortexReceiptHandoffDraft is review material only and does not grant Lifeline approval or receipt ownership.",
            status=handoff.review_status,
            notes=(
                f"Reviewer action={handoff.reviewer_action_required}.",
                f"Boundary statement={handoff.boundary_statement}.",
            ),
        ),
    ]

    targeted_notes = _merge_ordered_strings(
        tuple(f"Passed evidence={item}." for item in handoff.passed_commands),
        tuple(f"Failed evidence={item}." for item in handoff.failed_commands),
    )
    references.append(
        CortexProofReference(
            reference_id="targeted-verification-1",
            kind="targeted_verification_command",
            owner_layer=feedback.proof_summary.owner_layer,
            artifact_path=None,
            command=feedback.proof_summary.command,
            claim="Targeted verification commands provide the concrete proof steps Cortex used before assembling this pack.",
            status="passed" if feedback.targeted_verification_passed else "failed",
            notes=(
                f"Proof id={feedback.proof_summary.proof_id}.",
                f"Selected next action={feedback.selected_next_action}.",
                *targeted_notes,
            ),
        )
    )

    references.append(
        CortexProofReference(
            reference_id="stack-validation",
            kind="stack_validation_command",
            owner_layer="stack",
            artifact_path=None,
            command=CANONICAL_STACK_VALIDATION_COMMAND,
            claim="Stack validation remains reference-first so known ambient debt stays separate from current-tranche validation debt.",
            status=feedback.stack_validation_status,
            notes=(
                f"Known ambient baseline={KNOWN_STACK_VALIDATION_BASELINE.render()}.",
                f"Known ambient debt={_render_list(feedback.known_ambient_debt)}.",
                f"Current validation debt={_render_list(feedback.current_validation_debt)}.",
            ),
        )
    )

    references.append(
        CortexProofReference(
            reference_id="applied-rules",
            kind="applied_rules",
            owner_layer=run_artifact.owner_layer,
            artifact_path=run_artifact.artifact_path,
            command=None,
            claim="Applied rules identify the Cortex decision, plan, and pattern trace that produced this run and handoff.",
            status="tracked",
            notes=(
                f"Decision and plan rules={_render_list(_merged_rule_ids(run_artifact.applied_rules))}.",
                f"Patterns={_render_list(run_artifact.applied_rules.pattern_ids)}.",
                f"Why selected={_render_list(run_artifact.applied_rules.why_selected)}.",
            ),
        )
    )

    references.append(
        CortexProofReference(
            reference_id="failure-modes-avoided",
            kind="failure_modes_avoided",
            owner_layer=run_artifact.owner_layer,
            artifact_path=run_artifact.artifact_path,
            command=None,
            claim="Failure modes avoided stay explicit so the proof-reference pack preserves why Cortex kept the lane narrow.",
            status="tracked",
            notes=(
                f"Failure mode rule ids={_render_list(run_artifact.applied_rules.failure_mode_ids)}.",
                f"Failure modes avoided={_render_list(handoff.failure_modes_avoided or run_artifact.failure_modes_avoided)}.",
            ),
        )
    )

    references.append(
        CortexProofReference(
            reference_id="touched-files",
            kind="touched_files",
            owner_layer=handoff.owner_layer,
            artifact_path=handoff_artifact_path,
            command=None,
            claim="Touched files identify the Cortex-owned surfaces relevant to later Lifeline review without mutating Lifeline.",
            status="available" if handoff.touched_files else "not_available",
            notes=handoff.touched_files or ("No touched files were recorded on the handoff draft.",),
        )
    )
    return tuple(references)


def build_proof_reference_pack(
    run_artifact: dict[str, Any] | str | Path | None = None,
    feedback_artifact: CortexFeedbackResult | dict[str, Any] | str | Path | None = None,
    handoff_artifact: CortexReceiptHandoffDraft | dict[str, Any] | str | Path | None = None,
    *,
    root: Path | None = None,
) -> CortexProofReferencePack:
    base = (root or atlas_root()).resolve()
    feedback, feedback_artifact_path = _load_feedback_result(feedback_artifact, root=base)
    handoff, handoff_artifact_path = _load_receipt_handoff_draft(handoff_artifact, root=base)
    run, run_artifact_path = _load_run_artifact(run_artifact, root=base, expected_run_id=feedback.run_id)

    if run.run_id != feedback.run_id:
        raise ValueError("Cortex run artifact run_id does not match Cortex feedback artifact run_id.")
    if handoff.run_id != feedback.run_id:
        raise ValueError("Cortex receipt handoff draft run_id does not match Cortex feedback artifact run_id.")
    if run.selected_next_action != feedback.selected_next_action or handoff.selected_next_action != feedback.selected_next_action:
        raise ValueError("Selected next action must match across Cortex run, feedback, and handoff artifacts.")
    if run.owner_layer != feedback.owner_layer or handoff.owner_layer != feedback.owner_layer:
        raise ValueError("owner_layer must match across Cortex run, feedback, and handoff artifacts.")

    touched_files = handoff.touched_files or feedback.receipt_draft.touched_files or run.touched_files
    references = _build_references(
        run_artifact=run,
        feedback_artifact_path=feedback_artifact_path,
        feedback=feedback,
        handoff_artifact_path=handoff_artifact_path,
        handoff=handoff,
    )
    return CortexProofReferencePack(
        run_id=feedback.run_id,
        owner_layer=feedback.owner_layer,
        selected_next_action=feedback.selected_next_action,
        next_required_layer=feedback.next_required_layer or handoff.next_required_layer or run.next_required_layer,
        receipt_ready=feedback.receipt_ready,
        blocked=handoff.blocked,
        blocked_reason=handoff.blocked_reason or feedback.blocked_reason,
        pack_status="blocked" if handoff.blocked else "review_ready",
        review_status=handoff.review_status,
        known_ambient_debt=feedback.known_ambient_debt,
        current_validation_debt=feedback.current_validation_debt,
        touched_files=touched_files,
        applied_rules=feedback.applied_rules,
        failure_modes_avoided=handoff.failure_modes_avoided or feedback.failure_modes_avoided,
        run_artifact_path=run_artifact_path,
        feedback_artifact_path=feedback_artifact_path,
        handoff_artifact_path=handoff_artifact_path,
        targeted_verification_commands=_merge_ordered_strings(
            (feedback.proof_summary.command,),
            run.verification_expectation,
        ),
        stack_validation_command=CANONICAL_STACK_VALIDATION_COMMAND,
        stack_validation_status=feedback.stack_validation_status,
        known_ambient_baseline=KNOWN_STACK_VALIDATION_BASELINE,
        references=references,
        rule_statement="Cortex may assemble proof-reference packs, but Lifeline remains the final receipt owner.",
        pattern_statement="Because Lifeline is proof-reference-first, Cortex should bridge through evidence packs before any write path.",
        failure_mode_statement=(
            "Do not treat a proof-reference pack as a Lifeline receipt, approval, connector publication, or autonomous execution."
        ),
    )


def render_proof_reference_pack_summary(pack: CortexProofReferencePack) -> str:
    lines = [
        "Cortex Proof Reference Pack",
        f"- Run id: {pack.run_id}",
        f"- Owner layer: {pack.owner_layer}",
        f"- Selected next action: {pack.selected_next_action}",
        f"- Next required layer: {pack.next_required_layer or 'none'}",
        f"- Pack status: {pack.pack_status}",
        f"- Review status: {pack.review_status}",
        f"- Receipt ready: {_render_bool(pack.receipt_ready)}",
        f"- Blocked: {_render_bool(pack.blocked)}",
        f"- Blocked reason: {pack.blocked_reason or 'none'}",
        f"- Stack validation status: {pack.stack_validation_status}",
        f"- Known ambient baseline: {pack.known_ambient_baseline.render()}",
        f"- Known ambient debt: {_render_list(pack.known_ambient_debt)}",
        f"- Current validation debt: {_render_list(pack.current_validation_debt)}",
        f"- Targeted verification commands: {_render_list(pack.targeted_verification_commands)}",
        f"- Touched files: {_render_list(pack.touched_files)}",
        f"- Applied rules: {_render_list(_merged_rule_ids(pack.applied_rules))}",
        f"- Failure modes avoided: {_render_list(pack.failure_modes_avoided)}",
        f"- Rule: {pack.rule_statement}",
        f"- Pattern: {pack.pattern_statement}",
        f"- Failure mode: {pack.failure_mode_statement}",
        f"- Reference count: {len(pack.references)}",
    ]
    return "\n".join(lines) + "\n"


def _write_summary(path: Path, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")


class CortexProofReferencePackWriter:
    def write(
        self,
        run_artifact: dict[str, Any] | str | Path | None = None,
        feedback_artifact: CortexFeedbackResult | dict[str, Any] | str | Path | None = None,
        handoff_artifact: CortexReceiptHandoffDraft | dict[str, Any] | str | Path | None = None,
        *,
        root: Path | None = None,
        proof_reference_pack_root: Path | None = None,
        latest_json_path: Path | None = None,
        latest_summary_path: Path | None = None,
        run_json_path: Path | None = None,
        run_summary_path: Path | None = None,
        write_summary: bool = True,
    ) -> PersistedCortexProofReferencePack:
        base = (root or atlas_root()).resolve()
        output_root = _resolved_proof_reference_pack_dir(root=base, proof_reference_pack_root=proof_reference_pack_root)
        pack = build_proof_reference_pack(
            run_artifact,
            feedback_artifact,
            handoff_artifact,
            root=base,
        )
        payload = pack.to_payload(root=base)
        summary = render_proof_reference_pack_summary(pack)

        resolved_latest_json_path = (
            latest_json_path.resolve()
            if latest_json_path is not None
            else default_proof_reference_pack_latest_json_path(base, proof_reference_pack_root=output_root)
        )
        resolved_run_json_path = (
            run_json_path.resolve()
            if run_json_path is not None
            else default_proof_reference_pack_run_json_path(pack.run_id, base, proof_reference_pack_root=output_root)
        )
        resolved_latest_summary_path = None
        resolved_run_summary_path = None
        if write_summary:
            resolved_latest_summary_path = (
                latest_summary_path.resolve()
                if latest_summary_path is not None
                else default_proof_reference_pack_latest_summary_path(base, proof_reference_pack_root=output_root)
            )
            resolved_run_summary_path = (
                run_summary_path.resolve()
                if run_summary_path is not None
                else default_proof_reference_pack_run_summary_path(pack.run_id, base, proof_reference_pack_root=output_root)
            )

        write_json(resolved_latest_json_path, payload)
        write_json(resolved_run_json_path, payload)
        if resolved_latest_summary_path is not None:
            _write_summary(resolved_latest_summary_path, summary)
        if resolved_run_summary_path is not None:
            _write_summary(resolved_run_summary_path, summary)

        return PersistedCortexProofReferencePack(
            latest_artifact_path=resolved_latest_json_path,
            latest_summary_path=resolved_latest_summary_path,
            run_artifact_path=resolved_run_json_path,
            run_summary_path=resolved_run_summary_path,
            payload_digest=stable_json_digest(payload),
            payload=payload,
            summary=summary,
        )


def write_proof_reference_pack(
    run_artifact: dict[str, Any] | str | Path | None = None,
    feedback_artifact: CortexFeedbackResult | dict[str, Any] | str | Path | None = None,
    handoff_artifact: CortexReceiptHandoffDraft | dict[str, Any] | str | Path | None = None,
    *,
    root: Path | None = None,
    proof_reference_pack_root: Path | None = None,
    latest_json_path: Path | None = None,
    latest_summary_path: Path | None = None,
    run_json_path: Path | None = None,
    run_summary_path: Path | None = None,
    write_summary: bool = True,
) -> PersistedCortexProofReferencePack:
    return CortexProofReferencePackWriter().write(
        run_artifact,
        feedback_artifact,
        handoff_artifact,
        root=root,
        proof_reference_pack_root=proof_reference_pack_root,
        latest_json_path=latest_json_path,
        latest_summary_path=latest_summary_path,
        run_json_path=run_json_path,
        run_summary_path=run_summary_path,
        write_summary=write_summary,
    )
