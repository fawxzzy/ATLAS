from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ops.cortex.kernel import (
    CortexPosture,
    CortexProofSummary,
    CortexRuleRecord,
    VerificationResult,
    default_proof_summary_examples_path,
    default_rule_registry_path,
    default_state_model_path,
    load_kernel_state_model,
    load_proof_summary_examples,
    load_rule_registry,
)
from ops.cortex.proof_receipt import (
    ProofReceiptDraft,
    ProofReceiptDraftInput,
    ProofReceiptKnownDebtSummary,
    build_proof_receipt_draft,
)
from ops.cortex.rail_state import RailStateAssessment, classify_rail_state
from ops.cortex.worker_plan import WorkerPlan, build_worker_plan

CORTEX_RUN_RESULT_CONTRACT_VERSION = "atlas.cortex.run-result.v1"


def _ordered_unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _ordered_unique_rules(values: Iterable[CortexRuleRecord]) -> tuple[CortexRuleRecord, ...]:
    ordered: list[CortexRuleRecord] = []
    seen: set[str] = set()
    for rule in values:
        if rule.rule_id in seen:
            continue
        seen.add(rule.rule_id)
        ordered.append(rule)
    return tuple(ordered)


def _rail_state_assessment_payload(assessment: RailStateAssessment) -> dict[str, object]:
    return {
        "posture_id": assessment.posture_id,
        "rail_id": assessment.rail_id,
        "posture_classification": assessment.posture_classification,
        "latest_clean_step_id": assessment.latest_clean_step_id,
        "latest_clean_owner_layer": assessment.latest_clean_owner_layer,
        "priority_owner_layer": assessment.priority_owner_layer,
        "next_layer": assessment.next_layer,
        "next_action": assessment.next_action.to_payload(),
        "verification_status": assessment.verification_status,
        "known_validation_debt": list(assessment.known_validation_debt),
        "active_dirty_lane_ids": list(assessment.active_dirty_lane_ids),
        "matched_rule_ids": list(assessment.matched_rule_ids),
        "rationale": list(assessment.rationale),
        "boundary_reminders": list(assessment.boundary_reminders),
        "safe_to_proceed": assessment.safe_to_proceed,
    }


def _combined_rules(
    assessment: RailStateAssessment,
    worker_plan: WorkerPlan,
    rules: list[CortexRuleRecord],
) -> tuple[CortexRuleRecord, ...]:
    index = {rule.rule_id: rule for rule in rules}
    ordered_ids = assessment.matched_rule_ids + worker_plan.matched_rule_ids
    return _ordered_unique_rules(index[rule_id] for rule_id in ordered_ids if rule_id in index)


def _rule_ids_for_kind(rules: Iterable[CortexRuleRecord], kind: str) -> tuple[str, ...]:
    return _ordered_unique_strings(rule.rule_id for rule in rules if rule.kind == kind)


def _rule_statements_for_kind(rules: Iterable[CortexRuleRecord], kind: str) -> tuple[str, ...]:
    return _ordered_unique_strings(rule.statement for rule in rules if rule.kind == kind)


def _proof_summary_score(summary: CortexProofSummary, verification_steps: tuple[str, ...]) -> tuple[int, int, str]:
    command_matches = 0 if summary.command in verification_steps else 1
    clean_candidate = 0 if not summary.verification.failed and summary.receipt_ready else 1
    return (command_matches, clean_candidate, summary.proof_id)


def _synthetic_proof_summary(
    *,
    assessment: RailStateAssessment,
    worker_plan: WorkerPlan,
) -> CortexProofSummary:
    failed = () if assessment.safe_to_proceed else ("Current-tranche verification remains blocked.",)
    passed = (
        (f"Verification expectation prepared for {assessment.next_action.action_id}.",)
        if assessment.safe_to_proceed
        else ()
    )
    return CortexProofSummary(
        proof_id=f"{assessment.next_action.action_id}-proof-draft",
        command=worker_plan.verification_steps[0] if worker_plan.verification_steps else f"verify-{assessment.next_action.action_id}",
        verification=VerificationResult(
            status="passed" if assessment.safe_to_proceed else "failed",
            passed=passed,
            failed=failed,
            known_debt=(),
            notes=assessment.rationale,
        ),
        touched_files=worker_plan.files_to_modify,
        owner_layer=assessment.next_action.owner_layer,
        next_required_layer="cortex",
        receipt_ready=assessment.safe_to_proceed,
        evidence=assessment.matched_rule_ids,
    )


def _select_proof_summary(
    *,
    assessment: RailStateAssessment,
    worker_plan: WorkerPlan,
    proof_summaries: list[CortexProofSummary],
    proof_summary: CortexProofSummary | None,
) -> CortexProofSummary:
    if proof_summary is not None:
        return proof_summary

    candidates = [item for item in proof_summaries if item.owner_layer == assessment.next_action.owner_layer]
    if candidates:
        return sorted(
            candidates,
            key=lambda item: _proof_summary_score(item, worker_plan.verification_steps),
        )[0]

    return _synthetic_proof_summary(assessment=assessment, worker_plan=worker_plan)


def _receipt_boundary_status(proof_summary: CortexProofSummary) -> str:
    if proof_summary.verification.failed:
        return "dirty"
    return "clean"


def _receipt_notes(known_ambient_debt: tuple[str, ...]) -> tuple[str, ...]:
    if not known_ambient_debt:
        return ()
    return (
        "Known ambient debt stays on the CortexRunResult ledger and does not become current-tranche debt by itself.",
    )


@dataclass(frozen=True)
class AppliedRuleTrace:
    selected_next_action_id: str
    selected_owner_layer: str
    decision_rule_ids: tuple[str, ...]
    plan_rule_ids: tuple[str, ...]
    rule_ids: tuple[str, ...]
    pattern_ids: tuple[str, ...]
    failure_mode_ids: tuple[str, ...]
    failure_modes_avoided: tuple[str, ...]
    why_selected: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "selected_next_action_id": self.selected_next_action_id,
            "selected_owner_layer": self.selected_owner_layer,
            "decision_rule_ids": list(self.decision_rule_ids),
            "plan_rule_ids": list(self.plan_rule_ids),
            "rule_ids": list(self.rule_ids),
            "pattern_ids": list(self.pattern_ids),
            "failure_mode_ids": list(self.failure_mode_ids),
            "failure_modes_avoided": list(self.failure_modes_avoided),
            "why_selected": list(self.why_selected),
        }


def _build_applied_rule_trace(
    assessment: RailStateAssessment,
    worker_plan: WorkerPlan,
    rules_applied: tuple[CortexRuleRecord, ...],
) -> AppliedRuleTrace:
    return AppliedRuleTrace(
        selected_next_action_id=assessment.next_action.action_id,
        selected_owner_layer=assessment.next_action.owner_layer,
        decision_rule_ids=assessment.matched_rule_ids,
        plan_rule_ids=worker_plan.matched_rule_ids,
        rule_ids=_rule_ids_for_kind(rules_applied, "rule"),
        pattern_ids=_rule_ids_for_kind(rules_applied, "pattern"),
        failure_mode_ids=_rule_ids_for_kind(rules_applied, "failure_mode"),
        failure_modes_avoided=_rule_statements_for_kind(rules_applied, "failure_mode"),
        why_selected=_ordered_unique_strings((assessment.next_action.rationale, *assessment.rationale)),
    )


@dataclass(frozen=True)
class CortexRunResult:
    posture: CortexPosture
    rail_state: RailStateAssessment
    selected_next_action: dict[str, object]
    verification_expectation: tuple[str, ...]
    worker_plan: WorkerPlan
    proof_receipt_draft: ProofReceiptDraft
    known_ambient_debt: tuple[str, ...]
    rules_applied: tuple[CortexRuleRecord, ...]
    applied_rule_trace: AppliedRuleTrace
    failure_modes_avoided: tuple[str, ...]
    receipt_ready: bool
    next_required_layer: str | None

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": CORTEX_RUN_RESULT_CONTRACT_VERSION,
            "posture": self.posture.to_payload(),
            "rail_state": _rail_state_assessment_payload(self.rail_state),
            "selected_next_action": dict(self.selected_next_action),
            "verification_expectation": list(self.verification_expectation),
            "worker_plan": self.worker_plan.to_payload(),
            "proof_receipt_draft": self.proof_receipt_draft.to_payload(),
            "known_ambient_debt": list(self.known_ambient_debt),
            "rules_applied": [rule.to_payload() for rule in self.rules_applied],
            "applied_rule_trace": self.applied_rule_trace.to_payload(),
            "failure_modes_avoided": list(self.failure_modes_avoided),
            "receipt_ready": self.receipt_ready,
            "next_required_layer": self.next_required_layer,
        }


def run_cortex_loop(
    posture: CortexPosture | None = None,
    rules: list[CortexRuleRecord] | None = None,
    proof_summaries: list[CortexProofSummary] | None = None,
    *,
    proof_summary: CortexProofSummary | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    proof_summary_examples_path: Path | None = None,
    root: Path | None = None,
    files_to_modify: list[str] | None = None,
    files_to_avoid: list[str] | None = None,
) -> CortexRunResult:
    resolved_posture = posture or load_kernel_state_model(path=state_model_path or default_state_model_path(root))
    resolved_rules = rules or load_rule_registry(path=rule_registry_path or default_rule_registry_path(root))
    resolved_proof_summaries = proof_summaries or load_proof_summary_examples(
        path=proof_summary_examples_path or default_proof_summary_examples_path(root)
    )

    assessment = classify_rail_state(resolved_posture, resolved_rules)
    worker_plan = build_worker_plan(
        resolved_posture,
        resolved_posture.rail_state,
        assessment.next_action,
        resolved_rules,
        files_to_modify=files_to_modify,
        files_to_avoid=files_to_avoid,
    )
    resolved_proof_summary = _select_proof_summary(
        assessment=assessment,
        worker_plan=worker_plan,
        proof_summaries=resolved_proof_summaries,
        proof_summary=proof_summary,
    )
    known_ambient_debt = _ordered_unique_strings(assessment.known_validation_debt)
    proof_receipt_draft = build_proof_receipt_draft(
        ProofReceiptDraftInput(
            proof_summary=resolved_proof_summary,
            touched_files=resolved_proof_summary.touched_files or worker_plan.files_to_modify,
            owner_layer=resolved_proof_summary.owner_layer,
            next_required_layer=resolved_proof_summary.next_required_layer,
            known_debt_summary=ProofReceiptKnownDebtSummary(
                ambient_debt=(),
                current_validation_debt=(),
                owner_boundary_status=_receipt_boundary_status(resolved_proof_summary),
                notes=_receipt_notes(known_ambient_debt),
            ),
        )
    )
    rules_applied = _combined_rules(assessment, worker_plan, resolved_rules)
    applied_rule_trace = _build_applied_rule_trace(assessment, worker_plan, rules_applied)
    return CortexRunResult(
        posture=resolved_posture,
        rail_state=assessment,
        selected_next_action=assessment.next_action.to_payload(),
        verification_expectation=worker_plan.verification_steps,
        worker_plan=worker_plan,
        proof_receipt_draft=proof_receipt_draft,
        known_ambient_debt=known_ambient_debt,
        rules_applied=rules_applied,
        applied_rule_trace=applied_rule_trace,
        failure_modes_avoided=applied_rule_trace.failure_modes_avoided,
        receipt_ready=proof_receipt_draft.receipt_ready,
        next_required_layer=proof_receipt_draft.next_required_layer,
    )


def load_and_run_cortex_loop(
    *,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    proof_summary_examples_path: Path | None = None,
    proof_summary: CortexProofSummary | None = None,
    root: Path | None = None,
    files_to_modify: list[str] | None = None,
    files_to_avoid: list[str] | None = None,
) -> CortexRunResult:
    return run_cortex_loop(
        proof_summary=proof_summary,
        state_model_path=state_model_path,
        rule_registry_path=rule_registry_path,
        proof_summary_examples_path=proof_summary_examples_path,
        root=root,
        files_to_modify=files_to_modify,
        files_to_avoid=files_to_avoid,
    )
