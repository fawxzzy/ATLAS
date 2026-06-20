from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ops.atlas.pilot_selection_criteria import evaluate_pilot_selection_criteria

CANDIDATE_KEYS = ("candidate_a", "candidate_b")
PRESERVED_CANDIDATE_FIELDS = (
    "criteria_status",
    "allowed_write_scope",
    "checkpoint_surface",
    "verification_gate",
    "closeout_artifact",
    "park_or_escalation_rule",
    "protected_surface_exclusions",
)
REQUIRED_COMPARISON_FIELDS = PRESERVED_CANDIDATE_FIELDS[1:]
ALLOWED_OUTCOMES = {
    "candidate_a_preferred",
    "candidate_b_preferred",
    "tie",
    "not_comparable",
}
ALLOWED_REASONS = {
    "candidate_a_not_criteria_admissible",
    "candidate_b_not_criteria_admissible",
    "candidate_fields_hidden",
    "protected_surface_violation",
    "repo_discovery_invented",
    "execution_home_tiebreak_invented",
    "insufficient_comparison_signal",
}
REPO_DISCOVERY_KEYS = {
    "branch_inventory",
    "candidate_pool",
    "discovered_candidates",
    "repo_discovery",
    "repo_inventory",
    "worktree_inventory",
}
EXECUTION_HOME_KEYS = {
    "_stack_home",
    "execution_home",
    "execution_home_tiebreak",
    "helper_home",
}
IGNORED_NO_WINNER_CONVERSION_KEYS = {
    "pilot_winner",
    "winner_conversion",
}
VAGUE_SIGNAL_TOKENS = (
    "eventual",
    "if needed",
    "if possible",
    "later",
    "manual",
    "operator memory",
    "review manually",
    "when available",
)


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalized_exclusions(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _normalized_text(item).lower()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _as_candidate_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _candidate_fields_hidden(candidate: Mapping[str, Any]) -> bool:
    return any(field not in candidate for field in REQUIRED_COMPARISON_FIELDS)


def _contains_forbidden_key(value: Any, forbidden_keys: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if not isinstance(key, str):
                continue
            lowered = key.strip().lower()
            if lowered in forbidden_keys:
                return True
            if lowered in IGNORED_NO_WINNER_CONVERSION_KEYS:
                continue
            if _contains_forbidden_key(nested_value, forbidden_keys):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key(item, forbidden_keys) for item in value)
    return False


def _surface_quality(value: str) -> int:
    lowered = value.lower()
    score = 0
    if "/" in value or "\\" in value:
        score += 2
    if any(token in lowered for token in (".md", ".json", ".py")):
        score += 1
    if any(token in lowered for token in ("python ", "pytest", "unittest", "validate_stack")):
        score += 2
    if any(token in lowered for token in VAGUE_SIGNAL_TOKENS):
        score -= 2
    return score


def _scope_width(value: str) -> int:
    segments = [
        segment.strip()
        for chunk in value.replace("\n", ";").split(";")
        for segment in chunk.split(",")
    ]
    items: list[str] = []
    for segment in segments:
        if not segment:
            continue
        lowered = segment.lower()
        if " and " in lowered:
            parts = [part.strip() for part in segment.split(" and ") if part.strip()]
            items.extend(parts or [segment])
            continue
        if " plus " in lowered:
            parts = [part.strip() for part in segment.split(" plus ") if part.strip()]
            items.extend(parts or [segment])
            continue
        items.append(segment)
    width = max(1, len(items))
    return width * 100 + len(value)


def _park_quality(value: str) -> int:
    lowered = value.lower()
    score = 0
    if any(token in lowered for token in ("stop", "return", "escalate")):
        score += 2
    if "if " in lowered:
        score += 1
    if any(token in lowered for token in VAGUE_SIGNAL_TOKENS):
        score -= 1
    return score


def _comparison_key(candidate: Mapping[str, Any]) -> tuple[int, int, int, int]:
    proof_rank = _surface_quality(candidate["checkpoint_surface"]) + (2 * _surface_quality(candidate["verification_gate"]))
    scope_rank = -_scope_width(candidate["allowed_write_scope"])
    closeout_rank = _surface_quality(candidate["closeout_artifact"])
    park_rank = _park_quality(candidate["park_or_escalation_rule"])
    return (proof_rank, scope_rank, closeout_rank, park_rank)


def _preserved_candidate(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "criteria_status": evaluation["status"],
        "allowed_write_scope": evaluation["allowed_write_scope"],
        "checkpoint_surface": evaluation["checkpoint_surface"],
        "verification_gate": evaluation["verification_gate"],
        "closeout_artifact": evaluation["closeout_artifact"],
        "park_or_escalation_rule": evaluation["park_or_escalation_rule"],
        "protected_surface_exclusions": _normalized_exclusions(evaluation["protected_surface_exclusions"]),
    }


def evaluate_pilot_candidate_comparison(bundle: Mapping[str, Any]) -> dict[str, Any]:
    candidate_inputs = {
        label: _as_candidate_mapping(bundle.get(label))
        for label in CANDIDATE_KEYS
    }
    candidate_evaluations = {
        label: evaluate_pilot_selection_criteria(candidate)
        for label, candidate in candidate_inputs.items()
    }
    payload = {
        label: _preserved_candidate(candidate_evaluations[label])
        for label in CANDIDATE_KEYS
    }

    reasons: list[str] = []
    if _contains_forbidden_key(bundle, REPO_DISCOVERY_KEYS):
        reasons.append("repo_discovery_invented")
    if _contains_forbidden_key(bundle, EXECUTION_HOME_KEYS):
        reasons.append("execution_home_tiebreak_invented")

    for label in CANDIDATE_KEYS:
        evaluation = candidate_evaluations[label]
        candidate = candidate_inputs[label]

        if _candidate_fields_hidden(candidate):
            reasons.append("candidate_fields_hidden")
            continue
        if "protected_surface_violation" in evaluation["rejection_reasons"]:
            reasons.append("protected_surface_violation")
            continue
        if evaluation["status"] != "admissible":
            reasons.append(f"{label}_not_criteria_admissible")

    reasons = [reason for index, reason in enumerate(reasons) if reason in ALLOWED_REASONS and reason not in reasons[:index]]

    if reasons:
        payload["comparison_outcome"] = "not_comparable"
        payload["comparison_reasons"] = reasons
        return payload

    candidate_a_key = _comparison_key(payload["candidate_a"])
    candidate_b_key = _comparison_key(payload["candidate_b"])
    if candidate_a_key == candidate_b_key:
        signal_strength = sum(candidate_a_key) + sum(candidate_b_key)
        payload["comparison_outcome"] = "tie" if signal_strength else "not_comparable"
        payload["comparison_reasons"] = [] if signal_strength else ["insufficient_comparison_signal"]
        return payload

    payload["comparison_outcome"] = (
        "candidate_a_preferred" if candidate_a_key > candidate_b_key else "candidate_b_preferred"
    )
    payload["comparison_reasons"] = []
    return payload
