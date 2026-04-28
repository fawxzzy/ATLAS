from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ops._atlas import atlas_root, normalize_slashes, resolve_atlas_path
from ops.cortex._artifacts import read_json
from ops.cortex.kernel import CortexProofSummary
from ops.cortex.proof_receipt import (
    ProofReceiptDraft,
    ProofReceiptDraftInput,
    ProofReceiptKnownDebtSummary,
    build_proof_receipt_draft,
)
from ops.cortex.run_ledger import CortexRunLedgerAppliedRules, CortexRunLedgerSummary, summarize_run_ledger
from ops.cortex.verification_ingest import (
    STACK_VALIDATION_COMMAND_TOKEN,
    VerificationIngestResult,
    VerificationOutcome,
    ingest_verification_outcome,
)


def _ordered_unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(str(value).strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null for {field_name}.")
    normalized = " ".join(value.strip().split())
    return normalized or None


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected non-empty string for {field_name}.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return normalized


def _string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {field_name}.")
    ordered: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected string entries in {field_name}.")
        normalized = normalize_slashes(item.strip())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _is_stack_validation_command(command: str) -> bool:
    return STACK_VALIDATION_COMMAND_TOKEN in normalize_slashes(command).lower()


def _with_next_required_layer(
    proof_summary: CortexProofSummary,
    next_required_layer: str | None,
) -> CortexProofSummary:
    if proof_summary.next_required_layer is not None or next_required_layer is None:
        return proof_summary
    return CortexProofSummary(
        proof_id=proof_summary.proof_id,
        command=proof_summary.command,
        verification=proof_summary.verification,
        touched_files=proof_summary.touched_files,
        owner_layer=proof_summary.owner_layer,
        next_required_layer=next_required_layer,
        receipt_ready=proof_summary.receipt_ready,
        evidence=proof_summary.evidence,
    )


def _stack_validation_status(result: VerificationIngestResult | None) -> str:
    if result is None:
        return "not_run"
    if result.classification == "stack_validation_known_ambient_debt":
        return "known_ambient_debt"
    if result.classification == "stack_validation_changed_debt":
        return "changed_debt"
    return "passed"


def _blocked_reason(
    *,
    blocked: bool,
    receipt_draft: ProofReceiptDraft,
    ledger_summary: CortexRunLedgerSummary,
    current_validation_debt: tuple[str, ...],
) -> str | None:
    if not blocked:
        return None
    if receipt_draft.failed_commands:
        return receipt_draft.failed_commands[0]
    if current_validation_debt:
        return current_validation_debt[0]
    if ledger_summary.blocked_reason:
        return ledger_summary.blocked_reason
    return receipt_draft.boundary_statement


@dataclass(frozen=True)
class CortexFeedbackInput:
    verification_outcomes: tuple[VerificationOutcome | dict[str, Any], ...]
    root: Path | None = None
    runs_root: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.verification_outcomes, tuple):
            object.__setattr__(self, "verification_outcomes", tuple(self.verification_outcomes))

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CortexFeedbackInput":
        if not isinstance(payload, dict):
            raise ValueError("Expected feedback input payload to be an object.")
        outcomes = payload.get("verification_outcomes")
        if not isinstance(outcomes, list):
            raise ValueError("Expected list for verification_outcomes.")
        root_value = payload.get("root")
        runs_root_value = payload.get("runs_root")
        root = Path(root_value) if isinstance(root_value, str) and root_value.strip() else None
        runs_root = Path(runs_root_value) if isinstance(runs_root_value, str) and runs_root_value.strip() else None
        return cls(
            verification_outcomes=tuple(outcomes),
            root=root,
            runs_root=runs_root,
        )


@dataclass(frozen=True)
class CortexFeedbackResult:
    run_id: str
    selected_next_action: str
    owner_layer: str
    next_required_layer: str | None
    targeted_verification_passed: bool
    stack_validation_status: str
    known_ambient_debt: tuple[str, ...]
    current_validation_debt: tuple[str, ...]
    receipt_ready: bool
    tranche_complete: bool
    blocked: bool
    blocked_reason: str | None
    proof_summary: CortexProofSummary
    receipt_draft: ProofReceiptDraft
    ledger_summary: CortexRunLedgerSummary
    applied_rules: CortexRunLedgerAppliedRules = field(default_factory=CortexRunLedgerAppliedRules)
    failure_modes_avoided: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "selected_next_action": self.selected_next_action,
            "owner_layer": self.owner_layer,
            "next_required_layer": self.next_required_layer,
            "targeted_verification_passed": self.targeted_verification_passed,
            "stack_validation_status": self.stack_validation_status,
            "known_ambient_debt": list(self.known_ambient_debt),
            "current_validation_debt": list(self.current_validation_debt),
            "receipt_ready": self.receipt_ready,
            "tranche_complete": self.tranche_complete,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "proof_summary": self.proof_summary.to_payload(),
            "receipt_draft": self.receipt_draft.to_payload(),
            "ledger_summary": self.ledger_summary.to_payload(),
            "applied_rules": self.applied_rules.to_payload(),
            "failure_modes_avoided": list(self.failure_modes_avoided),
        }


@dataclass(frozen=True)
class _FeedbackRunContext:
    summary: CortexRunLedgerSummary
    touched_files: tuple[str, ...]


class CortexFeedbackLoop:
    def classify(self, request: CortexFeedbackInput | dict[str, Any]) -> CortexFeedbackResult:
        resolved_request = CortexFeedbackInput.from_payload(request) if isinstance(request, dict) else request
        if not isinstance(resolved_request, CortexFeedbackInput):
            raise ValueError("Expected CortexFeedbackInput or payload dictionary.")

        base = (resolved_request.root or atlas_root()).resolve()
        runs_root = (
            resolve_atlas_path(resolved_request.runs_root, root=base)
            if resolved_request.runs_root is not None
            else None
        )
        run_context = self._load_run_context(root=base, runs_root=runs_root)
        targeted_ingest, stack_ingest = self._split_and_ingest_outcomes(resolved_request.verification_outcomes)

        proof_summary = _with_next_required_layer(
            targeted_ingest.proof_summary,
            run_context.summary.next_required_layer,
        )
        ambient_notes = (
            ("Known ambient debt remains on the ledger and does not become current-tranche debt.",)
            if stack_ingest is not None and stack_ingest.ambient_debt
            else ()
        )
        receipt_draft = build_proof_receipt_draft(
            ProofReceiptDraftInput(
                proof_summary=proof_summary,
                touched_files=run_context.touched_files or proof_summary.touched_files,
                owner_layer=run_context.summary.owner_layer,
                next_required_layer=proof_summary.next_required_layer,
                known_debt_summary=ProofReceiptKnownDebtSummary(
                    ambient_debt=(),
                    current_validation_debt=stack_ingest.current_validation_debt if stack_ingest is not None else (),
                    owner_boundary_status="dirty" if targeted_ingest.current_tranche_failure else "clean",
                    notes=ambient_notes,
                ),
            )
        )
        ledger_summary = summarize_run_ledger(
            root=base,
            runs_root=runs_root,
            proof_summary=proof_summary,
            verification_ingest=stack_ingest,
        )

        targeted_verification_passed = (
            targeted_ingest.proof_summary.verification.status == "passed" and not targeted_ingest.current_tranche_failure
        )
        stack_validation_status = _stack_validation_status(stack_ingest)
        known_ambient_debt = ledger_summary.known_ambient_debt
        current_validation_debt = _ordered_unique_strings(
            (*receipt_draft.known_debt.current_validation_debt, *ledger_summary.current_validation_debt)
        )
        receipt_ready = receipt_draft.receipt_ready
        tranche_complete = targeted_verification_passed and receipt_ready and not current_validation_debt
        blocked = not tranche_complete
        blocked_reason = _blocked_reason(
            blocked=blocked,
            receipt_draft=receipt_draft,
            ledger_summary=ledger_summary,
            current_validation_debt=current_validation_debt,
        )

        return CortexFeedbackResult(
            run_id=ledger_summary.latest_run_id,
            selected_next_action=ledger_summary.selected_next_action,
            owner_layer=ledger_summary.owner_layer,
            next_required_layer=receipt_draft.next_required_layer or ledger_summary.next_required_layer,
            targeted_verification_passed=targeted_verification_passed,
            stack_validation_status=stack_validation_status,
            known_ambient_debt=known_ambient_debt,
            current_validation_debt=current_validation_debt,
            receipt_ready=receipt_ready,
            tranche_complete=tranche_complete,
            blocked=blocked,
            blocked_reason=blocked_reason,
            proof_summary=proof_summary,
            receipt_draft=receipt_draft,
            ledger_summary=ledger_summary,
            applied_rules=ledger_summary.applied_rules,
            failure_modes_avoided=ledger_summary.failure_modes_avoided,
        )

    @staticmethod
    def _load_run_context(*, root: Path, runs_root: Path | None) -> _FeedbackRunContext:
        summary = summarize_run_ledger(root=root, runs_root=runs_root)
        artifact_path = resolve_atlas_path(summary.latest_run_path, root=root)
        payload = read_json(artifact_path)
        proof_receipt_draft = payload.get("proof_receipt_draft")
        if not isinstance(proof_receipt_draft, dict):
            raise ValueError("Expected object for proof_receipt_draft.")
        touched_files = _string_list(proof_receipt_draft.get("touched_files"), "proof_receipt_draft.touched_files")
        return _FeedbackRunContext(summary=summary, touched_files=touched_files)

    @staticmethod
    def _split_and_ingest_outcomes(
        outcomes: tuple[VerificationOutcome | dict[str, Any], ...],
    ) -> tuple[VerificationIngestResult, VerificationIngestResult | None]:
        if not outcomes:
            raise ValueError("Cortex feedback classification requires verification_outcomes.")

        targeted: list[VerificationOutcome] = []
        stack: list[VerificationOutcome] = []
        for outcome in outcomes:
            resolved = VerificationOutcome.from_payload(outcome) if isinstance(outcome, dict) else outcome
            if not isinstance(resolved, VerificationOutcome):
                raise ValueError("Expected VerificationOutcome or payload dictionary in verification_outcomes.")
            if _is_stack_validation_command(resolved.command):
                stack.append(resolved)
            else:
                targeted.append(resolved)

        if len(targeted) != 1:
            raise ValueError("Cortex feedback classification requires exactly one targeted verification outcome.")
        if len(stack) > 1:
            raise ValueError("Cortex feedback classification supports at most one stack validation outcome.")

        targeted_ingest = ingest_verification_outcome(targeted[0])
        stack_ingest = ingest_verification_outcome(stack[0]) if stack else None
        return targeted_ingest, stack_ingest


def classify_feedback(request: CortexFeedbackInput | dict[str, Any]) -> CortexFeedbackResult:
    return CortexFeedbackLoop().classify(request)
