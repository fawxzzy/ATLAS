from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ops.atlas.supervised_execution_home import (
    COMMAND as SUPERVISED_EXECUTION_HOME_COMMAND,
    OWNER_SURFACE,
    RESULT_CLASS_CONTRACT_VISIBLE,
    SUCCESS_ROUTING_NOTE,
    SUPPORT_POSTURE,
)

COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE = "command_home_selection_admissible"
NO_COMMAND_HOME_SELECTION = "no_command_home_selection"
QUESTION_PROMPT = (
    "Which later admitted surface, if any, owns the concrete command home for "
    "`stack supervised-execution-home` without inferring runtime-home, worker authority, "
    "owner-repo edits, actual owner-side mutation authority, or Playbook doctrine export?"
)
CONTRACT_RECEIPT_REFS = (
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-HOME-SELECTION-CONTRACT-FREEZE-PASS-525-2026-06-21.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-HOME-OWNER-SURFACE-ADMISSION-PASS-526-2026-06-21.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-HOME-SUPPORTING-LANE-ADMISSION-PASS-527-2026-06-21.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-HOME-FIRST-IMPLEMENTATION-ADMISSION-PASS-528-2026-06-21.md",
)
ALLOWED_PAYLOAD_KEYS = {
    "candidate_ref",
    "owner_surface_statement",
    "support_posture_statement",
    "admitted_evidence_summary",
    "blocked_question_summary",
    "authoritative_receipt_refs",
}
COMMAND_HOME_KEYS = {"command_file", "command_file_path", "command_home", "command_path"}
RUNTIME_HOME_KEYS = {"_stack_home", "execution_home", "execution_home_inference", "helper_home", "runtime_home"}
WORKER_AUTHORITY_KEYS = {
    "dispatch_worker",
    "launch_worker",
    "routing_authority",
    "worker_authority",
    "worker_dispatch",
    "worker_launch",
    "worker_launch_authority",
}
OWNER_REPO_EDIT_KEYS = {"owner_repo_edit_authority", "owner_repo_write", "owner_repo_write_authority"}
ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_KEYS = {
    "actual_owner_side_mutation_authority",
    "mutation_execution_authority",
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


def _normalized_path(value: Any) -> str:
    normalized = _normalized_text(value).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized


def _normalized_string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    normalized: list[str] = []
    for item in value:
        item_text = _normalized_text(item)
        if item_text and item_text not in normalized:
            normalized.append(item_text)
    return normalized


def _preserved_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


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


def _forbidden_selection_reasons(value: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    checks = (
        (COMMAND_HOME_KEYS, "command_home_inference_invented"),
        (RUNTIME_HOME_KEYS, "runtime_home_inference_invented"),
        (WORKER_AUTHORITY_KEYS, "worker_authority_invented"),
        (OWNER_REPO_EDIT_KEYS, "owner_repo_edit_authority_invented"),
        (
            ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_KEYS,
            "actual_owner_side_mutation_authority_invented",
        ),
        (PLAYBOOK_DOCTRINE_EXPORT_KEYS, "playbook_doctrine_export_invented"),
    )
    for forbidden_keys, reason in checks:
        if _contains_forbidden_key(value, forbidden_keys) and reason not in reasons:
            reasons.append(reason)
    return reasons


def _payload_is_explicit(payload: dict[str, Any], candidate_path: str) -> bool:
    if set(payload.keys()) != ALLOWED_PAYLOAD_KEYS:
        return False
    if _normalized_path(payload.get("candidate_ref")) != candidate_path:
        return False
    if _normalized_text(payload.get("owner_surface_statement")) != OWNER_SURFACE:
        return False
    if _normalized_text(payload.get("support_posture_statement")) != SUPPORT_POSTURE:
        return False
    if not _normalized_text(payload.get("admitted_evidence_summary")):
        return False
    if not _normalized_text(payload.get("blocked_question_summary")):
        return False
    if not _normalized_string_list(payload.get("authoritative_receipt_refs")):
        return False
    return True


def _selection_reasons(bundle: Mapping[str, Any], candidate_path: str) -> list[str]:
    reasons: list[str] = []
    if _normalized_text(bundle.get("result_class")) != RESULT_CLASS_CONTRACT_VISIBLE:
        reasons.append("result_class_not_contract_visible")
    if _normalized_text(bundle.get("routing_note")) != SUCCESS_ROUTING_NOTE:
        reasons.append("routing_note_not_posture_only")
    if _normalized_text(bundle.get("command")) != SUPERVISED_EXECUTION_HOME_COMMAND:
        reasons.append("command_not_stack_supervised_execution_home")
    if not candidate_path:
        reasons.append("normalized_candidate_path_missing")
    if _normalized_text(bundle.get("owner_surface")) != OWNER_SURFACE:
        reasons.append("owner_surface_not_explicit")
    if _normalized_text(bundle.get("support_posture")) != SUPPORT_POSTURE:
        reasons.append("support_posture_not_none_yet")

    for reason in _forbidden_selection_reasons(bundle):
        if reason not in reasons:
            reasons.append(reason)

    if not reasons and not _payload_is_explicit(_preserved_mapping(bundle.get("payload")), candidate_path):
        reasons.append("payload_not_explicit")

    return reasons


def _question_card(candidate_path: str) -> dict[str, Any]:
    return {
        "question": QUESTION_PROMPT,
        "candidate_ref": candidate_path,
        "authoritative_receipt_refs": list(CONTRACT_RECEIPT_REFS),
    }


def evaluate_supervised_execution_home_command_home(bundle: Mapping[str, Any]) -> dict[str, Any]:
    candidate_path = _normalized_path(bundle.get("normalized_candidate_path"))
    payload = _preserved_mapping(bundle.get("payload"))
    reasons = _selection_reasons(bundle, candidate_path)

    return {
        "command": _normalized_text(bundle.get("command")),
        "normalized_candidate_path": candidate_path,
        "result_class": _normalized_text(bundle.get("result_class")),
        "owner_surface": _normalized_text(bundle.get("owner_surface")),
        "support_posture": _normalized_text(bundle.get("support_posture")),
        "admitted_evidence_refs": _normalized_string_list(bundle.get("admitted_evidence_refs")),
        "blocked_questions": _normalized_string_list(bundle.get("blocked_questions")),
        "routing_note": _normalized_text(bundle.get("routing_note")),
        "payload": payload,
        "command_home_selection_status": (
            COMMAND_HOME_SELECTION_STATUS_ADMISSIBLE if not reasons else NO_COMMAND_HOME_SELECTION
        ),
        "command_home_selection_question": _question_card(candidate_path) if not reasons else None,
        "command_home_selection_reasons": reasons,
    }
