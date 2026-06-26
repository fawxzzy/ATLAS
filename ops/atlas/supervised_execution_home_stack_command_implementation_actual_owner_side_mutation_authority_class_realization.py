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
from ops.atlas.supervised_execution_home_stack_command_implementation_actual_owner_side_mutation_surface_realization import (
    ACTUAL_CONCRETE_COMMAND_FILE_CHOICE_ATTEMPT_KEYS,
    ACTUAL_CONCRETE_COMMAND_FILE_DOWNSTREAM_RUNTIME_HOME_VALUE_PLACEMENT_ATTEMPT_KEYS,
    ACTUAL_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE_KEYS,
    ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_CLASS_KEYS,
    ACTUAL_OWNER_SIDE_MUTATION_SURFACE_KEYS,
    CONTRACT_RECEIPT_REFS as STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_CONTRACT_RECEIPT_REFS,
    LIVE_REPO_OR_TRANSCRIPT_KEYS,
    PASSTHROUGH_FIELDS as STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_PASSTHROUGH_FIELDS,
    PLAYBOOK_DOCTRINE_EXPORT_KEYS,
    PROTECTED_SURFACE_EXCEPTION_KEYS,
    QUESTION_PROMPT as STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_QUESTION_PROMPT,
    STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_STATUS_ADMISSIBLE,
    STACK_COMMAND_IMPLEMENTATION_KEYS,
    STACK_EXECUTION_HOME_KEYS,
)

STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_CLASS_REALIZATION_STATUS_ADMISSIBLE = (
    "stack_command_implementation_actual_owner_side_mutation_authority_class_realization_admissible"
)
NO_STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_CLASS_REALIZATION = (
    "no_stack_command_implementation_actual_owner_side_mutation_authority_class_realization"
)
QUESTION_PROMPT = (
    "How, if at all, may any later admitted surface realize one actual owner-side "
    "mutation authority class allowed by the already-admitted _stack command "
    "implementation actual owner-side mutation surface seam, the now-bounded "
    "actual owner-side mutation authority-class seam, and the now-bounded "
    "actual owner-side mutation surface realization seam for `stack "
    "supervised-execution-home` without realizing one actual owner-side "
    "mutation surface now, realizing one actual owner-side mutation authority "
    "class now, one actual `_stack` execution-home surface, one actual concrete "
    "command file, one actual downstream runtime-home value placement, one "
    "actual concrete `_stack` command implementation-surface choice, one "
    "actual `_stack` command implementation, one Playbook doctrine export "
    "path, deploy or publication work, or one protected-surface touch?"
)
CONTRACT_RECEIPT_REFS = (
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-REALIZATION-CONTRACT-FREEZE-PASS-733-2026-06-26.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-REALIZATION-OWNER-SURFACE-ADMISSION-PASS-734-2026-06-26.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-REALIZATION-SUPPORTING-LANE-ADMISSION-PASS-735-2026-06-26.md",
    "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-REALIZATION-FIRST-IMPLEMENTATION-ADMISSION-PASS-736-2026-06-26.md",
)
ALLOWED_PAYLOAD_KEYS = {
    "candidate_ref",
    "owner_surface_statement",
    "support_posture_statement",
    "admitted_evidence_summary",
    "blocked_question_summary",
    "authoritative_receipt_refs",
}
PASSTHROUGH_FIELDS = (
    *STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_PASSTHROUGH_FIELDS,
    "stack_command_implementation_actual_owner_side_mutation_surface_realization_status",
    "stack_command_implementation_actual_owner_side_mutation_surface_realization_question",
    "stack_command_implementation_actual_owner_side_mutation_surface_realization_reasons",
)


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
        == STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_QUESTION_PROMPT
        and _normalized_path(question_card.get("candidate_ref")) == candidate_path
        and _normalized_string_list(question_card.get("authoritative_receipt_refs"))
        == list(STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_CONTRACT_RECEIPT_REFS)
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
            ACTUAL_OWNER_SIDE_MUTATION_SURFACE_KEYS,
            "actual_owner_side_mutation_surface_realization_attempted",
        ),
        (
            ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_CLASS_KEYS,
            "actual_owner_side_mutation_authority_class_realization_attempted",
        ),
        (STACK_EXECUTION_HOME_KEYS, "stack_execution_home_inference_attempted"),
        (
            ACTUAL_CONCRETE_COMMAND_FILE_CHOICE_ATTEMPT_KEYS,
            "actual_concrete_command_file_choice_attempted",
        ),
        (
            ACTUAL_CONCRETE_COMMAND_FILE_DOWNSTREAM_RUNTIME_HOME_VALUE_PLACEMENT_ATTEMPT_KEYS,
            "actual_concrete_command_file_downstream_runtime_home_value_placement_attempted",
        ),
        (
            ACTUAL_CONCRETE_STACK_COMMAND_IMPLEMENTATION_SURFACE_CHOICE_KEYS,
            "actual_concrete_stack_command_implementation_surface_choice_attempted",
        ),
        (STACK_COMMAND_IMPLEMENTATION_KEYS, "stack_command_implementation_attempted"),
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
        _normalized_text(
            bundle.get("stack_command_implementation_actual_owner_side_mutation_surface_realization_status")
        )
        != STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_SURFACE_REALIZATION_STATUS_ADMISSIBLE
    ):
        return ["stack_command_implementation_actual_owner_side_mutation_surface_realization_status_not_admissible"]

    reasons: list[str] = []
    if not _question_card_is_explicit(
        bundle.get("stack_command_implementation_actual_owner_side_mutation_surface_realization_question"),
        candidate_path,
    ):
        reasons.append(
            "stack_command_implementation_actual_owner_side_mutation_surface_realization_question_not_explicit"
        )
    if _normalized_string_list(
        bundle.get("stack_command_implementation_actual_owner_side_mutation_surface_realization_reasons")
    ):
        reasons.append(
            "stack_command_implementation_actual_owner_side_mutation_surface_realization_reasons_present"
        )
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


def _copy_passthrough_field(bundle: Mapping[str, Any], key: str) -> Any:
    value = bundle.get(key)
    if key.endswith("_question"):
        return dict(value) if isinstance(value, Mapping) else None
    if key.endswith("_reasons"):
        return _normalized_string_list(value)
    return _normalized_text(value)


def evaluate_supervised_execution_home_stack_command_implementation_actual_owner_side_mutation_authority_class_realization(
    bundle: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_path = _normalized_path(bundle.get("normalized_candidate_path"))
    payload = _preserved_mapping(bundle.get("payload"))
    reasons = _selection_reasons(bundle, candidate_path, payload)

    result: dict[str, Any] = {
        "command": _normalized_text(bundle.get("command")),
        "normalized_candidate_path": candidate_path,
        "result_class": _normalized_text(bundle.get("result_class")),
        "owner_surface": _normalized_text(bundle.get("owner_surface")),
        "support_posture": _normalized_text(bundle.get("support_posture")),
        "admitted_evidence_refs": _normalized_string_list(bundle.get("admitted_evidence_refs")),
        "blocked_questions": _normalized_string_list(bundle.get("blocked_questions")),
        "routing_note": _normalized_text(bundle.get("routing_note")),
        "payload": payload,
    }
    for field in PASSTHROUGH_FIELDS:
        result[field] = _copy_passthrough_field(bundle, field)
    result["stack_command_implementation_actual_owner_side_mutation_authority_class_realization_status"] = (
        STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_CLASS_REALIZATION_STATUS_ADMISSIBLE
        if not reasons
        else NO_STACK_COMMAND_IMPLEMENTATION_ACTUAL_OWNER_SIDE_MUTATION_AUTHORITY_CLASS_REALIZATION
    )
    result["stack_command_implementation_actual_owner_side_mutation_authority_class_realization_question"] = (
        _question_card(candidate_path) if not reasons else None
    )
    result["stack_command_implementation_actual_owner_side_mutation_authority_class_realization_reasons"] = reasons
    return result
