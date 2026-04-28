from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex._artifacts import read_json
from ops.cortex.proof_reference_pack import CortexProofReferencePack, default_proof_reference_pack_latest_json_path


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


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Expected string or null.")
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
        normalized = " ".join(item.strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _render_bool(value: bool) -> str:
    return "yes" if value else "no"


def _render_list(values: tuple[str, ...]) -> str:
    return " | ".join(values) if values else "none"


@dataclass(frozen=True)
class _ProofReferenceInput:
    reference_id: str
    kind: str
    artifact_path: str | None
    command: str | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class _LifelineReceiptCandidateInput:
    run_id: str
    owner_layer: str
    receipt_ready: bool
    blocked: bool
    blocked_reason: str | None
    known_ambient_debt: tuple[str, ...]
    current_validation_debt: tuple[str, ...]
    references: tuple[_ProofReferenceInput, ...]
    rule_statement: str | None
    pattern_statement: str | None
    failure_mode_statement: str | None
    final_receipt_owner: str | None
    proof_reference_pack_path: Path


@dataclass(frozen=True)
class LifelineReceiptCandidateValidation:
    run_id: str
    candidate_valid: bool
    human_review_ready: bool
    lifeline_write_eligible: bool
    auto_approved: bool
    blocked: bool
    blocked_reason: str | None
    missing_references: tuple[str, ...]
    current_validation_debt: tuple[str, ...]
    known_ambient_debt: tuple[str, ...]
    required_reviewer_action: str
    proof_reference_pack_path: str

    def to_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "candidate_valid": self.candidate_valid,
            "human_review_ready": self.human_review_ready,
            "lifeline_write_eligible": self.lifeline_write_eligible,
            "auto_approved": self.auto_approved,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "missing_references": list(self.missing_references),
            "current_validation_debt": list(self.current_validation_debt),
            "known_ambient_debt": list(self.known_ambient_debt),
            "required_reviewer_action": self.required_reviewer_action,
            "proof_reference_pack_path": self.proof_reference_pack_path,
        }


def _coerce_reference(value: dict[str, Any]) -> _ProofReferenceInput:
    return _ProofReferenceInput(
        reference_id=_require_non_empty_string(value.get("reference_id"), "references.reference_id"),
        kind=_require_non_empty_string(value.get("kind"), "references.kind"),
        artifact_path=_optional_string(value.get("artifact_path")),
        command=_optional_string(value.get("command")),
        notes=_ordered_unique_strings(value.get("notes"), "references.notes"),
    )


def _coerce_candidate_input(payload: dict[str, Any], *, proof_reference_pack_path: Path) -> _LifelineReceiptCandidateInput:
    references_payload = payload.get("references")
    if not isinstance(references_payload, list):
        raise ValueError("Expected list for references.")

    return _LifelineReceiptCandidateInput(
        run_id=_require_non_empty_string(payload.get("run_id"), "run_id"),
        owner_layer=_require_non_empty_string(payload.get("owner_layer"), "owner_layer"),
        receipt_ready=_require_bool(payload.get("receipt_ready"), "receipt_ready"),
        blocked=_require_bool(payload.get("blocked"), "blocked"),
        blocked_reason=_optional_string(payload.get("blocked_reason")),
        known_ambient_debt=_ordered_unique_strings(payload.get("known_ambient_debt"), "known_ambient_debt"),
        current_validation_debt=_ordered_unique_strings(
            payload.get("current_validation_debt"),
            "current_validation_debt",
        ),
        references=tuple(_coerce_reference(_require_object(item, "references[]")) for item in references_payload),
        rule_statement=_optional_string(payload.get("rule_statement")),
        pattern_statement=_optional_string(payload.get("pattern_statement")),
        failure_mode_statement=_optional_string(payload.get("failure_mode_statement")),
        final_receipt_owner=_optional_string(payload.get("final_receipt_owner")),
        proof_reference_pack_path=proof_reference_pack_path.resolve(),
    )


def _load_candidate_input(
    proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
    *,
    root: Path | None = None,
) -> _LifelineReceiptCandidateInput:
    base = (root or atlas_root()).resolve()
    default_path = default_proof_reference_pack_latest_json_path(base).resolve()

    if isinstance(proof_reference_pack, CortexProofReferencePack):
        payload = proof_reference_pack.to_payload(root=base)
        return _coerce_candidate_input(payload, proof_reference_pack_path=default_path)
    if isinstance(proof_reference_pack, dict):
        return _coerce_candidate_input(proof_reference_pack, proof_reference_pack_path=default_path)

    artifact_path = (
        Path(proof_reference_pack).resolve()
        if isinstance(proof_reference_pack, (str, Path))
        else default_path
    )
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Proof reference pack not found at {normalize_slashes(str(artifact_path))}."
        )
    try:
        return _coerce_candidate_input(read_json(artifact_path), proof_reference_pack_path=artifact_path)
    except ValueError as exc:
        raise ValueError(
            f"Malformed Cortex proof reference pack at {normalize_slashes(str(artifact_path))}: {exc}"
        ) from exc


def _find_reference(
    references: tuple[_ProofReferenceInput, ...],
    *,
    kind: str,
    needs_artifact_path: bool = False,
    needs_command: bool = False,
) -> _ProofReferenceInput | None:
    for reference in references:
        if reference.kind != kind:
            continue
        if needs_artifact_path and reference.artifact_path is None:
            continue
        if needs_command and reference.command is None:
            continue
        return reference
    return None


def _missing_references(candidate: _LifelineReceiptCandidateInput) -> tuple[str, ...]:
    required = (
        ("run artifact reference", "cortex_run_artifact", True, False),
        ("feedback artifact reference", "cortex_feedback_artifact", True, False),
        ("handoff draft reference", "cortex_receipt_handoff_draft", True, False),
        ("targeted verification command reference", "targeted_verification_command", False, True),
        ("stack validation reference", "stack_validation_command", False, True),
        ("applied rules reference", "applied_rules", True, False),
        ("failure modes avoided reference", "failure_modes_avoided", True, False),
    )
    missing: list[str] = []
    for label, kind, needs_artifact_path, needs_command in required:
        if _find_reference(
            candidate.references,
            kind=kind,
            needs_artifact_path=needs_artifact_path,
            needs_command=needs_command,
        ) is None:
            missing.append(label)
    return tuple(missing)


def _boundary_statement(candidate: _LifelineReceiptCandidateInput) -> str | None:
    handoff_reference = _find_reference(candidate.references, kind="cortex_receipt_handoff_draft", needs_artifact_path=True)
    if handoff_reference is None:
        return None
    prefix = "Boundary statement="
    for note in handoff_reference.notes:
        if note.startswith(prefix):
            statement = " ".join(note[len(prefix) :].strip().split())
            if statement:
                return statement
    return None


def _lifeline_boundary_preserved(candidate: _LifelineReceiptCandidateInput) -> bool:
    if candidate.final_receipt_owner != "lifeline":
        return False
    if candidate.rule_statement is None:
        return False
    return "lifeline remains the final receipt owner" in candidate.rule_statement.lower()


def _derived_blocked_reason(
    candidate: _LifelineReceiptCandidateInput,
    *,
    missing_references: tuple[str, ...],
    boundary_statement: str | None,
    lifeline_boundary_preserved: bool,
) -> str | None:
    if candidate.owner_layer != "cortex":
        return "owner_layer must be 'cortex' for Lifeline receipt candidate validation."
    if missing_references:
        return f"Missing required proof references: {', '.join(missing_references)}."
    if boundary_statement is None:
        return "Missing boundary statement on the receipt handoff reference."
    if not lifeline_boundary_preserved:
        return "Lifeline final-owner boundary is not preserved."
    if candidate.current_validation_debt:
        return candidate.current_validation_debt[0]
    if candidate.blocked:
        return candidate.blocked_reason or "Proof reference pack is blocked."
    if not candidate.receipt_ready:
        return "receipt_ready is false."
    return None


def _required_reviewer_action(
    *,
    candidate_valid: bool,
    blocked: bool,
    blocked_reason: str | None,
) -> str:
    if not candidate_valid:
        return (
            "Fix the Cortex proof-reference pack before Lifeline candidate review: "
            f"{blocked_reason or 'required evidence is incomplete.'}"
        )
    if blocked:
        return (
            "Human review must not advance this candidate to any Lifeline write path until the blocker is resolved: "
            f"{blocked_reason or 'the proof-reference pack is blocked.'} "
            "This artifact remains unapproved, and Lifeline remains the final receipt owner."
        )
    return (
        "Human review may evaluate this Cortex proof-reference pack as a Lifeline receipt candidate. "
        "It is never auto-approved, and Lifeline remains the final receipt owner."
    )


class LifelineReceiptCandidateValidator:
    def validate(
        self,
        proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
        *,
        root: Path | None = None,
    ) -> LifelineReceiptCandidateValidation:
        candidate = _load_candidate_input(proof_reference_pack, root=root)
        missing_references = _missing_references(candidate)
        boundary_statement = _boundary_statement(candidate)
        lifeline_boundary_preserved = _lifeline_boundary_preserved(candidate)
        candidate_valid = (
            candidate.owner_layer == "cortex"
            and not missing_references
            and boundary_statement is not None
            and lifeline_boundary_preserved
        )
        blocked_reason = _derived_blocked_reason(
            candidate,
            missing_references=missing_references,
            boundary_statement=boundary_statement,
            lifeline_boundary_preserved=lifeline_boundary_preserved,
        )
        blocked = (
            not candidate_valid
            or candidate.blocked
            or bool(candidate.current_validation_debt)
            or not candidate.receipt_ready
        )
        human_review_ready = candidate_valid and not blocked
        lifeline_write_eligible = candidate_valid and not blocked and not candidate.current_validation_debt
        return LifelineReceiptCandidateValidation(
            run_id=candidate.run_id,
            candidate_valid=candidate_valid,
            human_review_ready=human_review_ready,
            lifeline_write_eligible=lifeline_write_eligible,
            auto_approved=False,
            blocked=blocked,
            blocked_reason=blocked_reason,
            missing_references=missing_references,
            current_validation_debt=candidate.current_validation_debt,
            known_ambient_debt=candidate.known_ambient_debt,
            required_reviewer_action=_required_reviewer_action(
                candidate_valid=candidate_valid,
                blocked=blocked,
                blocked_reason=blocked_reason,
            ),
            proof_reference_pack_path=normalize_slashes(str(candidate.proof_reference_pack_path)),
        )


def validate_lifeline_receipt_candidate(
    proof_reference_pack: CortexProofReferencePack | dict[str, Any] | str | Path | None = None,
    *,
    root: Path | None = None,
) -> LifelineReceiptCandidateValidation:
    return LifelineReceiptCandidateValidator().validate(proof_reference_pack, root=root)


def render_lifeline_candidate_summary(
    validation: LifelineReceiptCandidateValidation | dict[str, Any],
) -> str:
    resolved = (
        validation
        if isinstance(validation, LifelineReceiptCandidateValidation)
        else LifelineReceiptCandidateValidation(
            run_id=_require_non_empty_string(validation.get("run_id"), "run_id"),
            candidate_valid=_require_bool(validation.get("candidate_valid"), "candidate_valid"),
            human_review_ready=_require_bool(validation.get("human_review_ready"), "human_review_ready"),
            lifeline_write_eligible=_require_bool(
                validation.get("lifeline_write_eligible"),
                "lifeline_write_eligible",
            ),
            auto_approved=_require_bool(validation.get("auto_approved"), "auto_approved"),
            blocked=_require_bool(validation.get("blocked"), "blocked"),
            blocked_reason=_optional_string(validation.get("blocked_reason")),
            missing_references=_ordered_unique_strings(
                validation.get("missing_references"),
                "missing_references",
            ),
            current_validation_debt=_ordered_unique_strings(
                validation.get("current_validation_debt"),
                "current_validation_debt",
            ),
            known_ambient_debt=_ordered_unique_strings(
                validation.get("known_ambient_debt"),
                "known_ambient_debt",
            ),
            required_reviewer_action=_require_non_empty_string(
                validation.get("required_reviewer_action"),
                "required_reviewer_action",
            ),
            proof_reference_pack_path=_require_non_empty_string(
                validation.get("proof_reference_pack_path"),
                "proof_reference_pack_path",
            ),
        )
    )
    lines = [
        "Lifeline Receipt Candidate Validation",
        f"- Run id: {resolved.run_id}",
        f"- Candidate valid: {_render_bool(resolved.candidate_valid)}",
        f"- Human review ready: {_render_bool(resolved.human_review_ready)}",
        f"- Lifeline write eligible: {_render_bool(resolved.lifeline_write_eligible)}",
        f"- Auto approved: {_render_bool(resolved.auto_approved)}",
        f"- Blocked: {_render_bool(resolved.blocked)}",
        f"- Blocked reason: {resolved.blocked_reason or 'none'}",
        f"- Missing references: {_render_list(resolved.missing_references)}",
        f"- Current validation debt: {_render_list(resolved.current_validation_debt)}",
        f"- Known ambient debt: {_render_list(resolved.known_ambient_debt)}",
        f"- Proof reference pack path: {resolved.proof_reference_pack_path}",
        f"- Required reviewer action: {resolved.required_reviewer_action}",
    ]
    return "\n".join(lines) + "\n"
