from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ops.atlas.pilot_selection_criteria import evaluate_pilot_selection_criteria

CANDIDATE_KEYS = ("candidate_a", "candidate_b")
PREFERRED_LABELS = {
    "candidate_a_preferred": "candidate_a",
    "candidate_b_preferred": "candidate_b",
}
ALLOWED_OUTCOMES = set(PREFERRED_LABELS) | {"tie", "not_comparable"}
ALLOWED_CONVERSION_REASONS = {
    "comparison_outcome_not_preferred",
    "comparison_reasons_present",
    "preferred_candidate_missing",
    "preferred_candidate_not_explicit",
    "protected_surface_violation",
    "repo_discovery_invented",
    "owner_readiness_tiebreak_invented",
    "execution_home_tiebreak_invented",
}
REPO_DISCOVERY_KEYS = {
    "branch_inventory",
    "candidate_pool",
    "discovered_candidates",
    "repo_discovery",
    "repo_inventory",
    "worktree_inventory",
}
OWNER_READINESS_KEYS = {
    "owner_ready",
    "owner_readiness",
    "owner_readiness_tiebreak",
    "readiness_tiebreak",
}
EXECUTION_HOME_KEYS = {
    "_stack_home",
    "execution_home",
    "execution_home_tiebreak",
    "helper_home",
}


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _preserved_candidate(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _normalized_reason_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    reasons: list[str] = []
    for item in value:
        reason = _normalized_text(item)
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


def _contains_forbidden_key(value: Any, forbidden_keys: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if isinstance(key, str) and key.strip().lower() in forbidden_keys:
                return True
            if _contains_forbidden_key(nested_value, forbidden_keys):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key(item, forbidden_keys) for item in value)
    return False


def _dedupe_allowed_reasons(reasons: list[str]) -> list[str]:
    return [
        reason
        for index, reason in enumerate(reasons)
        if reason in ALLOWED_CONVERSION_REASONS and reason not in reasons[:index]
    ]


def evaluate_pilot_winner_conversion(bundle: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        label: _preserved_candidate(bundle.get(label))
        for label in CANDIDATE_KEYS
    }

    comparison_outcome = _normalized_text(bundle.get("comparison_outcome"))
    comparison_reasons = _normalized_reason_list(bundle.get("comparison_reasons"))
    payload["comparison_outcome"] = comparison_outcome
    payload["comparison_reasons"] = comparison_reasons

    reasons: list[str] = []
    if _contains_forbidden_key(bundle, REPO_DISCOVERY_KEYS):
        reasons.append("repo_discovery_invented")
    if _contains_forbidden_key(bundle, OWNER_READINESS_KEYS):
        reasons.append("owner_readiness_tiebreak_invented")
    if _contains_forbidden_key(bundle, EXECUTION_HOME_KEYS):
        reasons.append("execution_home_tiebreak_invented")

    preferred_label = PREFERRED_LABELS.get(comparison_outcome)
    if comparison_outcome not in ALLOWED_OUTCOMES or preferred_label is None:
        reasons.append("comparison_outcome_not_preferred")

    if comparison_reasons:
        reasons.append("comparison_reasons_present")

    pilot_winner: dict[str, Any] | None = None
    if preferred_label is not None:
        candidate_value = bundle.get(preferred_label)
        if candidate_value is None:
            reasons.append("preferred_candidate_missing")
        elif not isinstance(candidate_value, Mapping):
            reasons.append("preferred_candidate_not_explicit")
        else:
            evaluation = evaluate_pilot_selection_criteria(candidate_value)
            if "protected_surface_violation" in evaluation["rejection_reasons"]:
                reasons.append("protected_surface_violation")
            elif evaluation["status"] != "admissible":
                reasons.append("preferred_candidate_not_explicit")
            else:
                pilot_winner = dict(candidate_value)

    reasons = _dedupe_allowed_reasons(reasons)
    payload["conversion_status"] = "winner_selected" if not reasons and pilot_winner is not None else "no_winner"
    payload["pilot_winner"] = pilot_winner if payload["conversion_status"] == "winner_selected" else None
    payload["conversion_reasons"] = [] if payload["conversion_status"] == "winner_selected" else reasons
    return payload
