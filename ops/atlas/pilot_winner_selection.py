from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ops.atlas.pilot_selection_criteria import evaluate_pilot_selection_criteria

ALLOWED_SELECTION_REASONS = {
    "conversion_status_not_winner_selected",
    "conversion_reasons_present",
    "pilot_winner_missing",
    "pilot_winner_not_explicit",
    "protected_surface_violation",
    "repo_discovery_invented",
    "owner_readiness_tiebreak_invented",
    "execution_home_tiebreak_invented",
    "owner_repo_mutation_invented",
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
OWNER_REPO_MUTATION_KEYS = {
    "dispatch_worker",
    "launch_worker",
    "owner_repo_mutation",
    "owner_repo_write",
    "routing_authority",
    "worker_dispatch",
    "worker_launch",
    "worker_launch_authority",
}


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalized_reason_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    reasons: list[str] = []
    for item in value:
        reason = _normalized_text(item)
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


def _preserved_candidate(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


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
        if reason in ALLOWED_SELECTION_REASONS and reason not in reasons[:index]
    ]


def evaluate_pilot_winner_selection(bundle: Mapping[str, Any]) -> dict[str, Any]:
    conversion_status = _normalized_text(bundle.get("conversion_status"))
    conversion_reasons = _normalized_reason_list(bundle.get("conversion_reasons"))
    pilot_winner = _preserved_candidate(bundle.get("pilot_winner"))

    payload = {
        "conversion_status": conversion_status,
        "pilot_winner": pilot_winner,
        "conversion_reasons": conversion_reasons,
    }

    reasons: list[str] = []
    if _contains_forbidden_key(bundle, REPO_DISCOVERY_KEYS):
        reasons.append("repo_discovery_invented")
    if _contains_forbidden_key(bundle, OWNER_READINESS_KEYS):
        reasons.append("owner_readiness_tiebreak_invented")
    if _contains_forbidden_key(bundle, EXECUTION_HOME_KEYS):
        reasons.append("execution_home_tiebreak_invented")
    if _contains_forbidden_key(bundle, OWNER_REPO_MUTATION_KEYS):
        reasons.append("owner_repo_mutation_invented")

    selected_pilot: dict[str, Any] | None = None
    if not reasons:
        if conversion_status != "winner_selected":
            reasons.append("conversion_status_not_winner_selected")
        elif conversion_reasons:
            reasons.append("conversion_reasons_present")
        elif "pilot_winner" not in bundle or bundle.get("pilot_winner") is None:
            reasons.append("pilot_winner_missing")
        elif not isinstance(bundle.get("pilot_winner"), Mapping):
            reasons.append("pilot_winner_not_explicit")
        else:
            evaluation = evaluate_pilot_selection_criteria(bundle["pilot_winner"])
            if "protected_surface_violation" in evaluation["rejection_reasons"]:
                reasons.append("protected_surface_violation")
            elif evaluation["status"] != "admissible":
                reasons.append("pilot_winner_not_explicit")
            else:
                selected_pilot = dict(bundle["pilot_winner"])

    reasons = _dedupe_allowed_reasons(reasons)
    payload["selection_status"] = "pilot_selected" if not reasons and selected_pilot is not None else "no_selection"
    payload["selected_pilot"] = selected_pilot if payload["selection_status"] == "pilot_selected" else None
    payload["selection_reasons"] = [] if payload["selection_status"] == "pilot_selected" else reasons
    return payload
