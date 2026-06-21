from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ops.atlas.pilot_selection_criteria import evaluate_pilot_selection_criteria

ALLOWED_IMPLEMENTATION_REASONS = {
    "routing_status_not_implementation_route_admissible",
    "routing_reasons_present",
    "implementation_route_missing",
    "implementation_route_not_explicit",
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
        if reason in ALLOWED_IMPLEMENTATION_REASONS and reason not in reasons[:index]
    ]


def evaluate_pilot_selected_owner_repo_implementation(bundle: Mapping[str, Any]) -> dict[str, Any]:
    selection_status = _normalized_text(bundle.get("selection_status"))
    selection_reasons = _normalized_reason_list(bundle.get("selection_reasons"))
    routing_status = _normalized_text(bundle.get("routing_status"))
    implementation_route = _preserved_candidate(bundle.get("implementation_route"))
    routing_reasons = _normalized_reason_list(bundle.get("routing_reasons"))

    payload = {
        "selection_status": selection_status,
        "selection_reasons": selection_reasons,
        "routing_status": routing_status,
        "implementation_route": implementation_route,
        "routing_reasons": routing_reasons,
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

    owner_repo_implementation: dict[str, Any] | None = None
    if not reasons:
        if routing_status != "implementation_route_admissible":
            reasons.append("routing_status_not_implementation_route_admissible")
        elif routing_reasons:
            reasons.append("routing_reasons_present")
        elif "implementation_route" not in bundle or bundle.get("implementation_route") is None:
            reasons.append("implementation_route_missing")
        elif not isinstance(bundle.get("implementation_route"), Mapping):
            reasons.append("implementation_route_not_explicit")
        else:
            evaluation = evaluate_pilot_selection_criteria(bundle["implementation_route"])
            if "protected_surface_violation" in evaluation["rejection_reasons"]:
                reasons.append("protected_surface_violation")
            elif evaluation["status"] != "admissible":
                reasons.append("implementation_route_not_explicit")
            else:
                owner_repo_implementation = dict(bundle["implementation_route"])

    reasons = _dedupe_allowed_reasons(reasons)
    payload["implementation_status"] = (
        "owner_repo_implementation_admissible" if not reasons and owner_repo_implementation else "no_owner_repo_implementation"
    )
    payload["owner_repo_implementation"] = (
        owner_repo_implementation if payload["implementation_status"] == "owner_repo_implementation_admissible" else None
    )
    payload["implementation_reasons"] = [] if payload["implementation_status"] == "owner_repo_implementation_admissible" else reasons
    return payload
