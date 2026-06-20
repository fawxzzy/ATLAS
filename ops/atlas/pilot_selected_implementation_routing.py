from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ops.atlas.pilot_selection_criteria import evaluate_pilot_selection_criteria

ALLOWED_ROUTING_REASONS = {
    "selection_status_not_pilot_selected",
    "selection_reasons_present",
    "selected_pilot_missing",
    "selected_pilot_not_explicit",
    "protected_surface_violation",
    "repo_discovery_invented",
    "branch_worktree_enumeration_invented",
    "execution_home_inference_invented",
    "owner_repo_mutation_invented",
    "playbook_doctrine_export_invented",
}
REPO_DISCOVERY_KEYS = {
    "candidate_pool",
    "discovered_candidates",
    "repo_discovery",
    "repo_inventory",
}
BRANCH_WORKTREE_ENUMERATION_KEYS = {
    "branch_catalog",
    "branch_enumeration",
    "branch_inventory",
    "branches",
    "worktree_catalog",
    "worktree_enumeration",
    "worktree_inventory",
    "worktrees",
}
EXECUTION_HOME_INFERENCE_KEYS = {
    "_stack_home",
    "command_home",
    "execution_home",
    "execution_home_inference",
    "helper_home",
    "runtime_home",
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
PLAYBOOK_DOCTRINE_EXPORT_KEYS = {
    "doctrine_export",
    "playbook_doctrine",
    "playbook_doctrine_export",
    "playbook_export",
    "playbook_sync",
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
        if reason in ALLOWED_ROUTING_REASONS and reason not in reasons[:index]
    ]


def evaluate_pilot_selected_implementation_routing(bundle: Mapping[str, Any]) -> dict[str, Any]:
    selection_status = _normalized_text(bundle.get("selection_status"))
    selection_reasons = _normalized_reason_list(bundle.get("selection_reasons"))
    selected_pilot = _preserved_candidate(bundle.get("selected_pilot"))

    payload = {
        "selection_status": selection_status,
        "selected_pilot": selected_pilot,
        "selection_reasons": selection_reasons,
    }

    reasons: list[str] = []
    if _contains_forbidden_key(bundle, REPO_DISCOVERY_KEYS):
        reasons.append("repo_discovery_invented")
    if _contains_forbidden_key(bundle, BRANCH_WORKTREE_ENUMERATION_KEYS):
        reasons.append("branch_worktree_enumeration_invented")
    if _contains_forbidden_key(bundle, EXECUTION_HOME_INFERENCE_KEYS):
        reasons.append("execution_home_inference_invented")
    if _contains_forbidden_key(bundle, OWNER_REPO_MUTATION_KEYS):
        reasons.append("owner_repo_mutation_invented")
    if _contains_forbidden_key(bundle, PLAYBOOK_DOCTRINE_EXPORT_KEYS):
        reasons.append("playbook_doctrine_export_invented")

    implementation_route: dict[str, Any] | None = None
    if not reasons:
        if selection_status != "pilot_selected":
            reasons.append("selection_status_not_pilot_selected")
        elif selection_reasons:
            reasons.append("selection_reasons_present")
        elif "selected_pilot" not in bundle or bundle.get("selected_pilot") is None:
            reasons.append("selected_pilot_missing")
        elif not isinstance(bundle.get("selected_pilot"), Mapping):
            reasons.append("selected_pilot_not_explicit")
        else:
            evaluation = evaluate_pilot_selection_criteria(bundle["selected_pilot"])
            if "protected_surface_violation" in evaluation["rejection_reasons"]:
                reasons.append("protected_surface_violation")
            elif evaluation["status"] != "admissible":
                reasons.append("selected_pilot_not_explicit")
            else:
                implementation_route = dict(bundle["selected_pilot"])

    reasons = _dedupe_allowed_reasons(reasons)
    payload["routing_status"] = "implementation_route_admissible" if not reasons and implementation_route else "no_route"
    payload["implementation_route"] = implementation_route if payload["routing_status"] == "implementation_route_admissible" else None
    payload["routing_reasons"] = [] if payload["routing_status"] == "implementation_route_admissible" else reasons
    return payload
