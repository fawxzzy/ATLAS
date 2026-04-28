from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ops._atlas import normalize_slashes
from ops.cortex.kernel import (
    CortexPosture,
    CortexRuleRecord,
    NextAction,
    VerificationResult,
    default_rule_registry_path,
    default_state_model_path,
    load_kernel_state_model,
    load_rule_registry,
)

PIVOT_CLASSIFICATION = "pivoted"
FAILED_VERIFICATION_STATUS = "failed"
KNOWN_DEBT_VERIFICATION_STATUS = "completed_with_known_debt"
PIVOT_OVERRIDE_RULE_ID = "fitness-owner-adoption-resumes-unless-pivot"
FOOTER_CATCH_UP_PATTERN_ID = "footer-catch-up-precedes-pivot"
KNOWN_DEBT_RULE_ID = "known-validation-debt-stays-ambient-unless-regression"
ROOT_BOUNDARY_RULE_ID = "root-validates-proves-projects"
CORTEX_BOUNDARY_RULE_ID = "cortex-observes-interprets-proves-only"


@dataclass(frozen=True)
class RailStateAssessment:
    posture_id: str
    rail_id: str
    posture_classification: str
    latest_clean_step_id: str
    latest_clean_owner_layer: str
    priority_owner_layer: str
    next_layer: str
    next_action: NextAction
    verification_status: str
    known_validation_debt: tuple[str, ...]
    active_dirty_lane_ids: tuple[str, ...]
    matched_rule_ids: tuple[str, ...]
    rationale: tuple[str, ...]
    boundary_reminders: tuple[str, ...]
    safe_to_proceed: bool


def _load_required_state_model(path: Path) -> CortexPosture:
    if not path.exists():
        raise FileNotFoundError(f"Cortex state model seed not found: {normalize_slashes(str(path))}")
    try:
        return load_kernel_state_model(path=path)
    except ValueError as exc:
        raise ValueError(f"Invalid Cortex state model seed at {normalize_slashes(str(path))}: {exc}") from exc


def _load_required_rule_registry(path: Path) -> list[CortexRuleRecord]:
    if not path.exists():
        raise FileNotFoundError(f"Cortex rule registry seed not found: {normalize_slashes(str(path))}")
    try:
        return load_rule_registry(path=path)
    except ValueError as exc:
        raise ValueError(f"Invalid Cortex rule registry seed at {normalize_slashes(str(path))}: {exc}") from exc


def load_and_classify_rail_state(
    *,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    root: Path | None = None,
) -> RailStateAssessment:
    state_path = state_model_path or default_state_model_path(root)
    rule_path = rule_registry_path or default_rule_registry_path(root)
    posture = _load_required_state_model(state_path)
    rules = _load_required_rule_registry(rule_path)
    return classify_rail_state(posture, rules)


def classify_rail_state(
    posture: CortexPosture,
    rules: list[CortexRuleRecord],
) -> RailStateAssessment:
    verification_status, known_debt = _summarize_verification(posture.rail_state.verification)
    safe_to_proceed = verification_status != FAILED_VERIFICATION_STATUS
    next_layer = _determine_next_layer(posture)
    next_action = _determine_next_action(
        posture=posture,
        next_layer=next_layer,
        verification_status=verification_status,
    )

    matched_rules = _matched_rules(posture, next_layer, rules)
    matched_rule_ids = tuple(rule.rule_id for rule in matched_rules)
    rationale = tuple(rule.next_action_hint for rule in matched_rules)

    return RailStateAssessment(
        posture_id=posture.posture_id,
        rail_id=posture.rail_state.rail_id,
        posture_classification=posture.classification,
        latest_clean_step_id=posture.rail_state.latest_clean_step.step_id,
        latest_clean_owner_layer=posture.rail_state.latest_clean_step.owner_layer,
        priority_owner_layer=posture.rail_state.owner_layer if posture.classification == PIVOT_CLASSIFICATION else next_layer,
        next_layer=next_layer,
        next_action=next_action,
        verification_status=verification_status,
        known_validation_debt=known_debt,
        active_dirty_lane_ids=tuple(item.lane_id for item in posture.rail_state.dirty_lanes),
        matched_rule_ids=matched_rule_ids,
        rationale=rationale,
        boundary_reminders=posture.boundary_reminders + posture.rail_state.boundary_reminders,
        safe_to_proceed=safe_to_proceed,
    )


def _summarize_verification(results: tuple[VerificationResult, ...]) -> tuple[str, tuple[str, ...]]:
    known_debt: list[str] = []
    saw_known_debt = False
    for result in results:
        known_debt.extend(result.known_debt)
        if result.status == FAILED_VERIFICATION_STATUS or result.failed:
            return FAILED_VERIFICATION_STATUS, tuple(dict.fromkeys(known_debt))
        if result.status == KNOWN_DEBT_VERIFICATION_STATUS or result.known_debt:
            saw_known_debt = True
    if saw_known_debt:
        return KNOWN_DEBT_VERIFICATION_STATUS, tuple(dict.fromkeys(known_debt))
    return "passed", tuple(dict.fromkeys(known_debt))


def _determine_next_layer(posture: CortexPosture) -> str:
    if posture.classification == PIVOT_CLASSIFICATION:
        return posture.rail_state.owner_layer

    latest_owner = posture.rail_state.latest_clean_step.owner_layer
    if latest_owner == "atlas":
        return "fitness"
    if latest_owner == "fitness":
        return "atlas"
    return posture.rail_state.next_action.owner_layer


def _determine_next_action(
    *,
    posture: CortexPosture,
    next_layer: str,
    verification_status: str,
) -> NextAction:
    seeded = posture.rail_state.next_action
    if verification_status == FAILED_VERIFICATION_STATUS:
        return NextAction(
            action_id=f"stabilize-{posture.rail_state.rail_id}",
            owner_layer=posture.rail_state.owner_layer,
            title="Resolve the blocking verification failure before opening a new lane.",
            rationale="Current-tranche verification failures block further rail progression until the failing lane is stabilized.",
            required_inputs=seeded.required_inputs,
            verification_plan=seeded.verification_plan,
            receipt_scope=seeded.receipt_scope,
        )

    if seeded.owner_layer == next_layer:
        return seeded

    if next_layer == "fitness":
        return NextAction(
            action_id="resume-fitness-owner-adoption",
            owner_layer="fitness",
            title="Resume the Fitness owner-adoption lane.",
            rationale="Without an active Cortex priority pivot, the rail alternates back to Fitness after the matching ATLAS/Cortex catch-up.",
            required_inputs=seeded.required_inputs,
            verification_plan=seeded.verification_plan,
            receipt_scope=seeded.receipt_scope,
        )

    if next_layer == "atlas":
        return NextAction(
            action_id="atlas-cortex-catch-up",
            owner_layer="atlas",
            title="Perform the matching ATLAS/Cortex catch-up.",
            rationale="Without an active Cortex priority pivot, the alternating rail returns to the ATLAS/Cortex catch-up after a clean Fitness step.",
            required_inputs=seeded.required_inputs,
            verification_plan=seeded.verification_plan,
            receipt_scope=seeded.receipt_scope,
        )

    return NextAction(
        action_id=f"route-to-{next_layer}",
        owner_layer=next_layer,
        title=f"Route the next tranche into {next_layer}.",
        rationale="The current rail state requires an explicit owner-layer handoff before additional work proceeds.",
        required_inputs=seeded.required_inputs,
        verification_plan=seeded.verification_plan,
        receipt_scope=seeded.receipt_scope,
    )


def _matched_rules(
    posture: CortexPosture,
    next_layer: str,
    rules: list[CortexRuleRecord],
) -> list[CortexRuleRecord]:
    index = {rule.rule_id: rule for rule in rules}
    ordered_ids: list[str] = []

    if verification_status := _summarize_verification(posture.rail_state.verification)[0]:
        if verification_status == KNOWN_DEBT_VERIFICATION_STATUS and KNOWN_DEBT_RULE_ID in index:
            ordered_ids.append(KNOWN_DEBT_RULE_ID)
    if posture.classification == PIVOT_CLASSIFICATION and PIVOT_OVERRIDE_RULE_ID in index:
        ordered_ids.append(PIVOT_OVERRIDE_RULE_ID)
    if ROOT_BOUNDARY_RULE_ID in index:
        ordered_ids.append(ROOT_BOUNDARY_RULE_ID)
    if CORTEX_BOUNDARY_RULE_ID in index:
        ordered_ids.append(CORTEX_BOUNDARY_RULE_ID)
    if posture.classification != PIVOT_CLASSIFICATION and next_layer == "fitness" and PIVOT_OVERRIDE_RULE_ID in index:
        ordered_ids.append(PIVOT_OVERRIDE_RULE_ID)
    if posture.classification != PIVOT_CLASSIFICATION and next_layer == "atlas" and FOOTER_CATCH_UP_PATTERN_ID in index:
        ordered_ids.append(FOOTER_CATCH_UP_PATTERN_ID)

    seen: set[str] = set()
    matched: list[CortexRuleRecord] = []
    for rule_id in ordered_ids:
        if rule_id in seen:
            continue
        seen.add(rule_id)
        matched.append(index[rule_id])
    return matched
