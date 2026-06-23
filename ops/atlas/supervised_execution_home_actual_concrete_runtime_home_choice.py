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
from ops.atlas.supervised_execution_home_concrete_runtime_home_choice import (
    CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE,
    CONTRACT_RECEIPT_REFS as CONCRETE_RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS,
    QUESTION_PROMPT as CONCRETE_RUNTIME_HOME_CHOICE_QUESTION_PROMPT,
)

ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE = (
    "actual_concrete_runtime_home_choice_admissible"
)
NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE = "no_actual_concrete_runtime_home_choice"
QUESTION_PROMPT = (
    "Which later admitted surface, if any, may choose one actual concrete runtime-home "
    "value for the already-admitted concrete-runtime-home-choice seam for `stack "
    "supervised-execution-home` without choosing one actual concrete runtime-home "
    "value now or widening into concrete implementation-surface choice, `_stack` "
    "implementation, worker authority, owner-repo edits, actual owner-side mutation "
    "authority, Playbook doctrine export, or protected-surface exceptions?"
)
CONTRACT_RECEIPT_REFS = (
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-ACTUAL-CONCRETE-RUNTIME-HOME-CHOICE-CONTRACT-FREEZE-PASS-581-2026-06-23.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-ACTUAL-CONCRETE-RUNTIME-HOME-CHOICE-OWNER-SURFACE-ADMISSION-PASS-582-2026-06-23.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-ACTUAL-CONCRETE-RUNTIME-HOME-CHOICE-SUPPORTING-LANE-ADMISSION-PASS-583-2026-06-23.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-ACTUAL-CONCRETE-RUNTIME-HOME-CHOICE-FIRST-IMPLEMENTATION-ADMISSION-PASS-584-2026-06-23.md",
)
ALLOWED_PAYLOAD_KEYS = {
    "candidate_ref",
    "owner_surface_statement",
    "support_posture_statement",
    "admitted_evidence_summary",
    "blocked_question_summary",
    "authoritative_receipt_refs",
}
CONCRETE_STACK_COMMAND_HOME_KEYS = {
    "concrete_stack_command_home",
    "concrete_stack_command_home_choice",
    "stack_command_home",
    "stack_command_home_choice",
}
CONCRETE_COMMAND_FILE_KEYS = {
    "command_file",
    "command_file_choice",
    "command_file_path",
    "concrete_command_file",
    "stack_command_file",
}
STACK_COMMAND_IMPLEMENTATION_SURFACE_KEYS = {
    "concrete_stack_command_implementation_surface",
    "concrete_stack_command_implementation_surface_choice",
    "stack_command_implementation_surface",
    "stack_command_implementation_surface_choice",
    "stack_command_surface",
    "stack_command_surface_choice",
}
ACTUAL_CONCRETE_RUNTIME_HOME_VALUE_KEYS = {
    "_stack_home",
    "actual_concrete_runtime_home",
    "actual_concrete_runtime_home_choice",
    "actual_concrete_runtime_home_value",
    "actual_runtime_home",
    "actual_runtime_home_choice",
    "actual_runtime_home_value",
    "concrete_runtime_home",
    "concrete_runtime_home_value",
    "execution_home",
    "execution_home_inference",
    "helper_home",
    "runtime_home",
    "runtime_home_value",
}
STACK_COMMAND_IMPLEMENTATION_KEYS = {
    "_stack_command_implementation",
    "stack_command_behavior",
    "stack_command_implementation",
    "stack_supervised_execution_home_implementation",
}
WORKER_AUTHORITY_KEYS = {
    "dispatch_worker",
    "launch_worker",
    "routing_authority",
    "worker_authority",
    "worker_dispatch",
    "worker_launch",
    "worker_launch_authority",
}
OWNER_OR_MUTATION_AUTHORITY_KEYS = {
    "actual_owner_side_mutation_authority",
    "mutation_execution_authority",
    "owner_repo_edit_authority",
    "owner_repo_write",
    "owner_repo_write_authority",
}
PLAYBOOK_DOCTRINE_EXPORT_KEYS = {
    "doctrine_export",
    "playbook_doctrine",
    "playbook_doctrine_export",
    "playbook_export",
    "playbook_sync",
}
PROTECTED_SURFACE_EXCEPTION_KEYS = {
    "protected_surface",
    "protected_surface_exception",
    "protected_surface_override",
}
LIVE_REPO_OR_TRANSCRIPT_KEYS = {
    "branch",
    "branch_inventory",
    "branches",
    "chat_history",
    "hidden_transcript",
    "live_repo",
    "live_repo_discovery",
    "live_repos",
    "repo_inventory",
    "transcript_memory",
    "worktree",
    "worktree_inventory",
    "worktrees",
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


def _contains_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if isinstance(key, str) and key.strip().lower() in keys:
                return True
            if _contains_key(nested_value, keys):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_key(item, keys) for item in value)
    return False


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


def _question_card_is_explicit(value: Any, candidate_path: str) -> bool:
    if not isinstance(value, Mapping):
        return False
    question_card = dict(value)
    return (
        set(question_card.keys())
        == {"question", "candidate_ref", "authoritative_receipt_refs"}
        and _normalized_text(question_card.get("question"))
        == CONCRETE_RUNTIME_HOME_CHOICE_QUESTION_PROMPT
        and _normalized_path(question_card.get("candidate_ref")) == candidate_path
        and _normalized_string_list(question_card.get("authoritative_receipt_refs"))
        == list(CONCRETE_RUNTIME_HOME_CHOICE_CONTRACT_RECEIPT_REFS)
    )


def _bundle_posture_is_explicit(
    bundle: Mapping[str, Any],
    candidate_path: str,
    payload: dict[str, Any],
) -> bool:
    return (
        _normalized_text(bundle.get("command")) == SUPERVISED_EXECUTION_HOME_COMMAND
        and candidate_path != ""
        and _normalized_text(bundle.get("result_class")) == RESULT_CLASS_CONTRACT_VISIBLE
        and _normalized_text(bundle.get("owner_surface")) == OWNER_SURFACE
        and _normalized_text(bundle.get("support_posture")) == SUPPORT_POSTURE
        and _normalized_text(bundle.get("routing_note")) == SUCCESS_ROUTING_NOTE
        and _payload_is_explicit(payload, candidate_path)
    )


def _attempt_reasons(bundle: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    checks = (
        (
            CONCRETE_STACK_COMMAND_HOME_KEYS,
            "concrete_stack_command_home_choice_attempted",
        ),
        (CONCRETE_COMMAND_FILE_KEYS, "concrete_command_file_choice_attempted"),
        (
            STACK_COMMAND_IMPLEMENTATION_SURFACE_KEYS,
            "stack_command_implementation_surface_choice_attempted",
        ),
        (
            ACTUAL_CONCRETE_RUNTIME_HOME_VALUE_KEYS,
            "actual_concrete_runtime_home_value_attempted",
        ),
        (STACK_COMMAND_IMPLEMENTATION_KEYS, "stack_command_implementation_attempted"),
        (WORKER_AUTHORITY_KEYS, "worker_authority_attempted"),
        (
            OWNER_OR_MUTATION_AUTHORITY_KEYS,
            "owner_repo_or_actual_mutation_authority_attempted",
        ),
        (PLAYBOOK_DOCTRINE_EXPORT_KEYS, "playbook_doctrine_export_attempted"),
        (PROTECTED_SURFACE_EXCEPTION_KEYS, "protected_surface_exception_attempted"),
    )
    for keys, reason in checks:
        if _contains_key(bundle, keys) and reason not in reasons:
            reasons.append(reason)
    return reasons


def _selection_reasons(
    bundle: Mapping[str, Any],
    candidate_path: str,
    payload: dict[str, Any],
) -> list[str]:
    if (
        _normalized_text(bundle.get("concrete_runtime_home_choice_status"))
        != CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE
    ):
        return ["concrete_runtime_home_choice_status_not_admissible"]

    reasons: list[str] = []
    if not _question_card_is_explicit(
        bundle.get("concrete_runtime_home_choice_question"), candidate_path
    ):
        reasons.append("concrete_runtime_home_choice_question_not_explicit")
    if _normalized_string_list(bundle.get("concrete_runtime_home_choice_reasons")):
        reasons.append("concrete_runtime_home_choice_reasons_present")
    if _contains_key(bundle, LIVE_REPO_OR_TRANSCRIPT_KEYS):
        reasons.append("live_repo_discovery_or_hidden_transcript_dependency")

    for reason in _attempt_reasons(bundle):
        if reason not in reasons:
            reasons.append(reason)

    if not reasons and not _bundle_posture_is_explicit(bundle, candidate_path, payload):
        reasons.append("forbidden_evidence_class_used")

    return reasons


def _question_card(candidate_path: str) -> dict[str, Any]:
    return {
        "question": QUESTION_PROMPT,
        "candidate_ref": candidate_path,
        "authoritative_receipt_refs": list(CONTRACT_RECEIPT_REFS),
    }


def evaluate_supervised_execution_home_actual_concrete_runtime_home_choice(
    bundle: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_path = _normalized_path(bundle.get("normalized_candidate_path"))
    payload = _preserved_mapping(bundle.get("payload"))
    command_home_selection_question = bundle.get("command_home_selection_question")
    concrete_command_home_question = bundle.get("concrete_command_home_question")
    concrete_stack_command_home_selection_question = bundle.get(
        "concrete_stack_command_home_selection_question"
    )
    concrete_command_file_selection_question = bundle.get(
        "concrete_command_file_selection_question"
    )
    concrete_stack_command_implementation_surface_selection_question = bundle.get(
        "concrete_stack_command_implementation_surface_selection_question"
    )
    runtime_home_selection_question = bundle.get("runtime_home_selection_question")
    runtime_home_choice_question = bundle.get("runtime_home_choice_question")
    concrete_runtime_home_choice_question = bundle.get(
        "concrete_runtime_home_choice_question"
    )
    reasons = _selection_reasons(bundle, candidate_path, payload)

    return {
        "command": _normalized_text(bundle.get("command")),
        "normalized_candidate_path": candidate_path,
        "result_class": _normalized_text(bundle.get("result_class")),
        "owner_surface": _normalized_text(bundle.get("owner_surface")),
        "support_posture": _normalized_text(bundle.get("support_posture")),
        "admitted_evidence_refs": _normalized_string_list(
            bundle.get("admitted_evidence_refs")
        ),
        "blocked_questions": _normalized_string_list(bundle.get("blocked_questions")),
        "routing_note": _normalized_text(bundle.get("routing_note")),
        "payload": payload,
        "command_home_selection_status": _normalized_text(
            bundle.get("command_home_selection_status")
        ),
        "command_home_selection_question": (
            dict(command_home_selection_question)
            if isinstance(command_home_selection_question, Mapping)
            else None
        ),
        "command_home_selection_reasons": _normalized_string_list(
            bundle.get("command_home_selection_reasons")
        ),
        "concrete_command_home_status": _normalized_text(
            bundle.get("concrete_command_home_status")
        ),
        "concrete_command_home_question": (
            dict(concrete_command_home_question)
            if isinstance(concrete_command_home_question, Mapping)
            else None
        ),
        "concrete_command_home_reasons": _normalized_string_list(
            bundle.get("concrete_command_home_reasons")
        ),
        "concrete_stack_command_home_selection_status": _normalized_text(
            bundle.get("concrete_stack_command_home_selection_status")
        ),
        "concrete_stack_command_home_selection_question": (
            dict(concrete_stack_command_home_selection_question)
            if isinstance(concrete_stack_command_home_selection_question, Mapping)
            else None
        ),
        "concrete_stack_command_home_selection_reasons": _normalized_string_list(
            bundle.get("concrete_stack_command_home_selection_reasons")
        ),
        "concrete_command_file_selection_status": _normalized_text(
            bundle.get("concrete_command_file_selection_status")
        ),
        "concrete_command_file_selection_question": (
            dict(concrete_command_file_selection_question)
            if isinstance(concrete_command_file_selection_question, Mapping)
            else None
        ),
        "concrete_command_file_selection_reasons": _normalized_string_list(
            bundle.get("concrete_command_file_selection_reasons")
        ),
        "concrete_stack_command_implementation_surface_selection_status": _normalized_text(
            bundle.get("concrete_stack_command_implementation_surface_selection_status")
        ),
        "concrete_stack_command_implementation_surface_selection_question": (
            dict(concrete_stack_command_implementation_surface_selection_question)
            if isinstance(
                concrete_stack_command_implementation_surface_selection_question,
                Mapping,
            )
            else None
        ),
        "concrete_stack_command_implementation_surface_selection_reasons": (
            _normalized_string_list(
                bundle.get("concrete_stack_command_implementation_surface_selection_reasons")
            )
        ),
        "runtime_home_selection_status": _normalized_text(
            bundle.get("runtime_home_selection_status")
        ),
        "runtime_home_selection_question": (
            dict(runtime_home_selection_question)
            if isinstance(runtime_home_selection_question, Mapping)
            else None
        ),
        "runtime_home_selection_reasons": _normalized_string_list(
            bundle.get("runtime_home_selection_reasons")
        ),
        "runtime_home_choice_status": _normalized_text(bundle.get("runtime_home_choice_status")),
        "runtime_home_choice_question": (
            dict(runtime_home_choice_question)
            if isinstance(runtime_home_choice_question, Mapping)
            else None
        ),
        "runtime_home_choice_reasons": _normalized_string_list(
            bundle.get("runtime_home_choice_reasons")
        ),
        "concrete_runtime_home_choice_status": _normalized_text(
            bundle.get("concrete_runtime_home_choice_status")
        ),
        "concrete_runtime_home_choice_question": (
            dict(concrete_runtime_home_choice_question)
            if isinstance(concrete_runtime_home_choice_question, Mapping)
            else None
        ),
        "concrete_runtime_home_choice_reasons": _normalized_string_list(
            bundle.get("concrete_runtime_home_choice_reasons")
        ),
        "actual_concrete_runtime_home_choice_status": (
            ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE_STATUS_ADMISSIBLE
            if not reasons
            else NO_ACTUAL_CONCRETE_RUNTIME_HOME_CHOICE
        ),
        "actual_concrete_runtime_home_choice_question": (
            _question_card(candidate_path) if not reasons else None
        ),
        "actual_concrete_runtime_home_choice_reasons": reasons,
    }
