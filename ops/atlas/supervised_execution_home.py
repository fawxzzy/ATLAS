from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

SUCCESS_ROUTING_NOTE = (
    "one explicit preserved actual_owner_side_mutation candidate remains contract-visible for "
    "supervised execution-home posture only; no command-home, runtime-home, worker, owner-repo, "
    "or actual owner-side mutation authority is implied"
)
REPAIR_ROUTING_NOTE = (
    "repair explicit candidate, authoritative contract, or derivative restart contradiction "
    "before supervised execution-home posture can continue"
)
COMMAND = "stack supervised-execution-home"
OWNER_SURFACE = "_stack Readiness control-plane surfaces in ATLAS root receipts, restart mirrors, and continuity surfaces"
SUPPORT_POSTURE = "none yet"
ACTUAL_MUTATION_STATUS_ADMISSIBLE = "actual_owner_side_mutation_admissible"
RESULT_CLASS_CONTRACT_VISIBLE = "contract-visible"
RESULT_CLASS_CANDIDATE_MISSING = "candidate-missing"
RESULT_CLASS_CANDIDATE_NON_ADMISSIBLE = "candidate-non-admissible"
RESULT_CLASS_CONTRACT_TRUTH_UNAVAILABLE = "contract-truth-unavailable"
BLOCKED_QUESTIONS = [
    "whether one later packet separately admits command-home choice or runtime-home choice for supervised execution-home behavior",
    "whether one later packet separately admits worker authority, owner-repo edits, actual owner-side mutation authority, or Playbook doctrine export",
]
ACTUAL_MUTATION_RESULT_REF = "ops/atlas/pilot_selected_actual_owner_side_mutation.py"
CONTRACT_RECEIPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-COMMAND-DESIGN-PASS-518-2026-06-21.md",
        (
            "`stack supervised-execution-home`",
            "`contract-visible`",
            "`candidate-missing`",
            "`candidate-non-admissible`",
            "`contract-truth-unavailable`",
        ),
    ),
    (
        "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-EVIDENCE-ADMISSION-AND-CONTRADICTION-DISCIPLINE-PASS-519-2026-06-21.md",
        (
            "forbidden-evidence contradiction",
            "actual owner-side mutation authority",
            "command-home",
            "runtime-home",
        ),
    ),
    (
        "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-REPORT-CONTRACT-AND-NO-MUTATION-GUARD-PASS-520-2026-06-21.md",
        (
            SUCCESS_ROUTING_NOTE,
            REPAIR_ROUTING_NOTE,
            "`contract-visible`",
            "`candidate-missing`",
            "`candidate-non-admissible`",
            "`contract-truth-unavailable`",
        ),
    ),
    (
        "docs/ops/_STACK-READINESS-SUPERVISED-EXECUTION-HOME-IMPLEMENTATION-ADMISSION-AND-NO-MUTATION-GUARD-PASS-521-2026-06-21.md",
        (
            "`command`",
            "`normalized_candidate_path`",
            "`owner_surface`",
            "`support_posture`",
            "`blocked_questions`",
            "`routing_note`",
            "`payload`",
        ),
    ),
)
COMMAND_HOME_KEYS = {"command_home"}
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


def _normalized_candidate_path(value: Any) -> str:
    candidate_path = _normalized_text(value).replace("\\", "/")
    while candidate_path.startswith("./"):
        candidate_path = candidate_path[2:]
    while "//" in candidate_path:
        candidate_path = candidate_path.replace("//", "/")
    return candidate_path


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


def _forbidden_posture_reasons(bundle: Mapping[str, Any]) -> list[str]:
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
        if _contains_forbidden_key(bundle, forbidden_keys) and reason not in reasons:
            reasons.append(reason)
    return reasons


def _repo_root(root: Path | None) -> Path:
    return root if root is not None else Path(__file__).resolve().parents[2]


def _contract_refs() -> list[str]:
    return [relative_path for relative_path, _required_phrases in CONTRACT_RECEIPTS]


def _load_contract_state(root: Path) -> tuple[list[str], list[str]]:
    refs: list[str] = []
    errors: list[str] = []
    for relative_path, required_phrases in CONTRACT_RECEIPTS:
        contract_path = root / relative_path
        refs.append(relative_path)
        try:
            contents = contract_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append(f"missing:{relative_path}")
            continue
        except OSError:
            errors.append(f"unreadable:{relative_path}")
            continue

        missing_phrases = [phrase for phrase in required_phrases if phrase not in contents]
        if missing_phrases:
            errors.append(f"contradictory:{relative_path}")
    return refs, errors


def _success_payload(candidate_path: str, contract_refs: list[str]) -> dict[str, Any]:
    return {
        "candidate_ref": candidate_path,
        "owner_surface_statement": OWNER_SURFACE,
        "support_posture_statement": SUPPORT_POSTURE,
        "admitted_evidence_summary": (
            "explicit actual_owner_side_mutation result plus authoritative pass-518-through-pass-521 "
            "supervised execution-home contract receipts"
        ),
        "blocked_question_summary": (
            "command-home, runtime-home, worker-authority, owner-repo-edit, and doctrine-export "
            "decisions remain deferred beyond this posture-only report"
        ),
        "authoritative_receipt_refs": contract_refs,
    }


def _failure_payload(
    contradiction_class: str,
    reasons: list[str],
    contract_refs: list[str],
) -> dict[str, Any]:
    return {
        "contradiction_class": contradiction_class,
        "reasons": reasons,
        "authoritative_receipt_refs": contract_refs,
        "stop_and_return_note": REPAIR_ROUTING_NOTE,
    }


def _base_result(candidate_path: str, admitted_evidence_refs: list[str]) -> dict[str, Any]:
    return {
        "command": COMMAND,
        "normalized_candidate_path": candidate_path,
        "owner_surface": OWNER_SURFACE,
        "support_posture": SUPPORT_POSTURE,
        "admitted_evidence_refs": admitted_evidence_refs,
        "blocked_questions": list(BLOCKED_QUESTIONS),
    }


def evaluate_supervised_execution_home(
    bundle: Mapping[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    actual_mutation_status = _normalized_text(bundle.get("actual_mutation_status"))
    actual_mutation_reasons = _normalized_reason_list(bundle.get("actual_mutation_reasons"))
    actual_owner_side_mutation = _preserved_candidate(bundle.get("actual_owner_side_mutation"))
    normalized_candidate_path = _normalized_candidate_path(
        (actual_owner_side_mutation or {}).get("target_ref"),
    )

    contract_refs, contract_errors = _load_contract_state(_repo_root(root))
    admitted_evidence_refs = [ACTUAL_MUTATION_RESULT_REF, *contract_refs]
    result = _base_result(normalized_candidate_path, admitted_evidence_refs)

    forbidden_reasons = _forbidden_posture_reasons(bundle)
    if contract_errors or forbidden_reasons:
        result["result_class"] = RESULT_CLASS_CONTRACT_TRUTH_UNAVAILABLE
        result["routing_note"] = REPAIR_ROUTING_NOTE
        result["payload"] = _failure_payload(
            "authoritative-contract-contradiction" if contract_errors else "forbidden-evidence-contradiction",
            contract_errors or forbidden_reasons,
            contract_refs,
        )
        return result

    if actual_mutation_status != ACTUAL_MUTATION_STATUS_ADMISSIBLE or actual_mutation_reasons:
        reasons = actual_mutation_reasons or ["actual_mutation_status_not_admissible"]
        result["result_class"] = RESULT_CLASS_CANDIDATE_NON_ADMISSIBLE
        result["routing_note"] = REPAIR_ROUTING_NOTE
        result["payload"] = _failure_payload("authoritative-candidate-contradiction", reasons, contract_refs)
        return result

    if actual_owner_side_mutation is None:
        result["result_class"] = RESULT_CLASS_CANDIDATE_MISSING
        result["routing_note"] = REPAIR_ROUTING_NOTE
        result["payload"] = _failure_payload(
            "missing-explicit-candidate",
            ["actual_owner_side_mutation_missing"],
            contract_refs,
        )
        return result

    result["result_class"] = RESULT_CLASS_CONTRACT_VISIBLE
    result["routing_note"] = SUCCESS_ROUTING_NOTE
    result["payload"] = _success_payload(normalized_candidate_path, contract_refs)
    return result
