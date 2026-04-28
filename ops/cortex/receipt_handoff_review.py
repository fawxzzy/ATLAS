from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex._artifacts import read_json
from ops.cortex.receipt_handoff import default_receipt_handoff_latest_json_path
from ops.cortex.run_ledger import CortexRunLedgerAppliedRules


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
        normalized = " ".join(item.strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


@dataclass(frozen=True)
class CortexReceiptHandoffReviewInput:
    run_id: str
    receipt_title: str
    owner_layer: str
    selected_next_action: str
    next_required_layer: str | None
    tranche_complete: bool
    receipt_ready: bool
    blocked: bool
    blocked_reason: str | None
    known_ambient_debt: tuple[str, ...]
    current_validation_debt: tuple[str, ...]
    applied_rules: CortexRunLedgerAppliedRules
    failure_modes_avoided: tuple[str, ...]
    reviewer_action_required: str
    review_status: str | None = None


@dataclass(frozen=True)
class CortexReceiptHandoffReviewDecision:
    handoff_valid: bool
    human_review_ready: bool
    lifeline_candidate: bool
    auto_approved: bool
    blocked: bool
    blocked_reason: str | None
    required_reviewer_action: str

    def to_payload(self) -> dict[str, object]:
        return {
            "handoff_valid": self.handoff_valid,
            "human_review_ready": self.human_review_ready,
            "lifeline_candidate": self.lifeline_candidate,
            "auto_approved": self.auto_approved,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "required_reviewer_action": self.required_reviewer_action,
        }


def _coerce_review_input(value: dict[str, Any]) -> CortexReceiptHandoffReviewInput:
    return CortexReceiptHandoffReviewInput(
        run_id=_require_non_empty_string(value.get("run_id"), "run_id"),
        receipt_title=_require_non_empty_string(value.get("receipt_title"), "receipt_title"),
        owner_layer=_require_non_empty_string(value.get("owner_layer"), "owner_layer"),
        selected_next_action=_require_non_empty_string(
            value.get("selected_next_action"),
            "selected_next_action",
        ),
        next_required_layer=_optional_string(value.get("next_required_layer"), "next_required_layer"),
        tranche_complete=_require_bool(value.get("tranche_complete"), "tranche_complete"),
        receipt_ready=_require_bool(value.get("receipt_ready"), "receipt_ready"),
        blocked=_require_bool(value.get("blocked"), "blocked"),
        blocked_reason=_optional_string(value.get("blocked_reason"), "blocked_reason"),
        known_ambient_debt=_ordered_unique_strings(value.get("known_ambient_debt"), "known_ambient_debt"),
        current_validation_debt=_ordered_unique_strings(
            value.get("current_validation_debt"),
            "current_validation_debt",
        ),
        applied_rules=CortexRunLedgerAppliedRules.from_payload(
            _require_object(value.get("applied_rules"), "applied_rules")
        ),
        failure_modes_avoided=_ordered_unique_strings(
            value.get("failure_modes_avoided"),
            "failure_modes_avoided",
        ),
        reviewer_action_required=_require_non_empty_string(
            value.get("reviewer_action_required"),
            "reviewer_action_required",
        ),
        review_status=_optional_string(value.get("review_status"), "review_status"),
    )


def _load_review_input(
    draft_artifact: CortexReceiptHandoffReviewInput | dict[str, Any] | str | Path | None = None,
    *,
    root: Path | None = None,
) -> CortexReceiptHandoffReviewInput:
    if isinstance(draft_artifact, CortexReceiptHandoffReviewInput):
        return draft_artifact
    if isinstance(draft_artifact, dict):
        return _coerce_review_input(draft_artifact)

    base = (root or atlas_root()).resolve()
    artifact_path = (
        Path(draft_artifact).resolve()
        if isinstance(draft_artifact, (str, Path))
        else default_receipt_handoff_latest_json_path(base)
    )
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Receipt handoff draft not found at {normalize_slashes(str(artifact_path))}."
        )
    try:
        return _coerce_review_input(read_json(artifact_path))
    except ValueError as exc:
        raise ValueError(
            f"Malformed Cortex receipt handoff draft at {normalize_slashes(str(artifact_path))}: {exc}"
        ) from exc


def _contract_issues(draft: CortexReceiptHandoffReviewInput) -> tuple[str, ...]:
    issues: list[str] = []
    if draft.owner_layer != "cortex":
        issues.append("owner_layer must be 'cortex' for Cortex receipt handoff review.")
    if draft.current_validation_debt and not draft.blocked:
        issues.append("blocked must be true when current_validation_debt is present.")
    if not draft.receipt_ready and not draft.blocked:
        issues.append("blocked must be true when receipt_ready is false.")
    if draft.blocked and draft.blocked_reason is None:
        issues.append("blocked_reason must be present when blocked is true.")
    if not draft.blocked and draft.blocked_reason is not None:
        issues.append("blocked_reason must be null when blocked is false.")
    if draft.review_status == "blocked" and not draft.blocked:
        issues.append("review_status='blocked' requires blocked=true.")
    if draft.review_status == "review_ready" and draft.blocked:
        issues.append("review_status='review_ready' requires blocked=false.")
    return tuple(issues)


def _derived_blocked_reason(
    draft: CortexReceiptHandoffReviewInput,
    *,
    issues: tuple[str, ...],
) -> str | None:
    if issues:
        return issues[0]
    if draft.blocked:
        return draft.blocked_reason
    if draft.current_validation_debt:
        return draft.current_validation_debt[0]
    if not draft.receipt_ready:
        return "receipt_ready is false."
    return None


def _required_reviewer_action(
    draft: CortexReceiptHandoffReviewInput,
    *,
    handoff_valid: bool,
    blocked: bool,
    blocked_reason: str | None,
) -> str:
    if not handoff_valid:
        return (
            "Fix the Cortex handoff contract before review: "
            f"{blocked_reason or 'the draft is internally inconsistent.'}"
        )
    if blocked:
        return draft.reviewer_action_required
    return (
        "Human review may proceed on this Cortex handoff draft. "
        "It remains review-ready only and is never auto-approved."
    )


class CortexReceiptHandoffReviewGate:
    def review(
        self,
        draft_artifact: CortexReceiptHandoffReviewInput | dict[str, Any] | str | Path | None = None,
        *,
        root: Path | None = None,
    ) -> CortexReceiptHandoffReviewDecision:
        draft = _load_review_input(draft_artifact, root=root)
        issues = _contract_issues(draft)
        handoff_valid = not issues
        blocked_reason = _derived_blocked_reason(draft, issues=issues)
        blocked = bool(issues) or draft.blocked or bool(draft.current_validation_debt) or not draft.receipt_ready
        human_review_ready = handoff_valid
        lifeline_candidate = handoff_valid and human_review_ready and not blocked
        return CortexReceiptHandoffReviewDecision(
            handoff_valid=handoff_valid,
            human_review_ready=human_review_ready,
            lifeline_candidate=lifeline_candidate,
            auto_approved=False,
            blocked=blocked,
            blocked_reason=blocked_reason,
            required_reviewer_action=_required_reviewer_action(
                draft,
                handoff_valid=handoff_valid,
                blocked=blocked,
                blocked_reason=blocked_reason,
            ),
        )


def review_receipt_handoff(
    draft_artifact: CortexReceiptHandoffReviewInput | dict[str, Any] | str | Path | None = None,
    *,
    root: Path | None = None,
) -> CortexReceiptHandoffReviewDecision:
    return CortexReceiptHandoffReviewGate().review(draft_artifact, root=root)
