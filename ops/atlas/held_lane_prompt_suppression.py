from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops._atlas import normalize_slashes

SCHEMA_VERSION = "atlas.held_lane_prompt_suppression.v1"

STATUS_OK = "ok"
STATUS_SUPPRESS = "suppress"
STATUS_ALLOW = "allow"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

DECISION_SUPPRESS_CONTINUATION = "suppress_continuation"
DECISION_ALLOW_EXACT_PACKET = "allow_exact_packet"
DECISION_ALLOW_OPERATOR_SELECTED_PACKET = "allow_operator_selected_packet"
DECISION_ALLOW_VALIDATION_CLEANUP = "allow_validation_cleanup"
DECISION_ALLOW_WORKER_RECONCILIATION = "allow_worker_reconciliation"
DECISION_BLOCKED_BY_SCOPE_LOCK = "blocked_by_scope_lock"
DECISION_BLOCKED_BY_OWNER_LANE_FALLBACK = "blocked_by_owner_lane_fallback"
DECISION_INTERNAL_ERROR = "internal_error"

OUTPUT_FIELDS = [
    "schema_version",
    "status",
    "decision",
    "root_clean",
    "validation_state",
    "selector_action",
    "planner_status",
    "selected_packet",
    "selected_packet_source",
    "selected_packet_classification",
    "packet_authority_risk",
    "owner_lane_fallback_forbidden",
    "exact_packet_available",
    "operator_selected_packet",
    "suppression_reason",
    "allowed_next_actions",
    "playbook_rule_refs",
    "failure_mode_refs",
    "safe_to_continue",
]

PLAYBOOK_RULE_REFS = [
    "docs/PLAYBOOK_NOTES.md#marker-ratchet-threshold",
    "docs/PLAYBOOK_NOTES.md#implementation-readiness-before-worker-routing",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md#explicit-artifact-ref-handoff",
    "docs/standards/WORKER-ORCHESTRATION.md#handoff-artifacts",
    "AGENTS.md#Routing",
    "AGENTS.md#Execution-Cadence",
]

FAILURE_MODE_REFS = [
    "held lane reopened by wording instead of changed evidence",
    "owner repo drift treated as ATLAS root blocker",
    "Fitness or Mazer selected as a fallback from a root-governance session",
    "secret, deploy, workflow, or protected-surface authority inferred from a held root state",
    "stale completed packet rerun after durable receipt already exists",
    "marker movement claimed without receipt-backed ratchet condition",
]

SAFE_INPUT_PREFIXES = ("tmp/", "runtime/receipts/validation/")
PROTECTED_PREFIXES = (
    ".github/workflows/",
    ".playwright-mcp/",
    ".vercel/",
    "archive/",
    "repos/",
    "secrets/",
)
OWNER_LANE_TERMS = (
    "fitness",
    "mazer",
    "fawxzzy-fitness",
    "repos/fawxzzy-fitness",
    "repos/mazer",
)
OWNER_FALLBACK_TERMS = (
    "owner lane fallback",
    "owner-lane fallback",
    "owner repo fallback",
    "owner-repo fallback",
    "switch to fitness",
    "switch to mazer",
    "fitness fallback",
    "mazer fallback",
)
PROTECTED_TERMS = (
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    ".env",
    "archive/",
    "browserstack",
    "deploy",
    "deployment",
    "final receipt",
    "release readiness",
    "release-readiness",
    "secret",
    "stripe",
    "supabase",
    "vercel",
    "workflow dispatch",
    "workflow_dispatch",
)
MARKER_AUTHORITY_TERMS = (
    "advance marker",
    "claim marker",
    "increase marker",
    "marker movement",
    "marker to ",
    "move marker",
    "moves marker",
    "moving marker",
    "ratchet marker",
    "ratchet to ",
)
SAFE_PLANNER_CLASSIFICATIONS = (
    "docs_only_packet",
    "implementation_ready_packet",
    "immediately_executable_packet",
)
NO_PACKET_TERMS = (
    "",
    "none",
    "null",
    "no immediate",
    "no immediate root packet",
    "no_immediate_root_packet",
)
STALE_TERMS = (
    "already complete",
    "already completed",
    "completed packet",
    "durably completed",
    "stale",
)
WORKER_TERMS = (
    "first-implementation worker",
    "held-lane prompt suppression",
    "implementation readiness",
    "implementation-readiness",
    "reconciliation",
    "worker cluster",
    "worker packet",
)


def _finding_reason(code: str, message: str, **details: Any) -> str:
    if not details:
        return f"{code}: {message}"
    rendered = ", ".join(f"{key}={value}" for key, value in sorted(details.items()))
    return f"{code}: {message} ({rendered})"


def _normalized_relative(value: str) -> str:
    return normalize_slashes(value).strip("/")


def _path_contains_env(relative_path: str) -> bool:
    return any(part.startswith(".env") for part in _normalized_relative(relative_path).split("/"))


def _validate_artifact_path(*, root: Path, artifact_path: str) -> tuple[Path | None, str | None]:
    candidate = Path(artifact_path)
    if candidate.is_absolute():
        return None, _finding_reason("absolute_input_path", "Input path must be root-relative.", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if not relative_path:
        return None, _finding_reason("empty_input_path", "Input path must not be empty.")
    if ".." in Path(relative_path).parts:
        return None, _finding_reason("parent_traversal_input_path", "Input path must not use parent traversal.", path=relative_path)
    if _path_contains_env(relative_path):
        return None, _finding_reason("secret_input_path", "Input path must not target .env files.", path=relative_path)
    if any(relative_path == prefix.rstrip("/") or relative_path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return None, _finding_reason("protected_input_path", "Input path targets a protected surface.", path=relative_path)
    if not relative_path.endswith(".json"):
        return None, _finding_reason("non_json_input_path", "Input path must be a JSON artifact.", path=relative_path)
    if not any(relative_path.startswith(prefix) for prefix in SAFE_INPUT_PREFIXES):
        return None, _finding_reason("unadmitted_input_path", "Input reads are admitted only from root-relative tmp/**.json or validation receipt JSON.", path=relative_path)

    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding_reason("outside_root_input_path", "Input path must stay inside the ATLAS root.", path=relative_path)
    if not resolved.exists():
        return None, _finding_reason("missing_input_path", "Input artifact does not exist.", path=relative_path)
    return resolved, None


def validate_output_path(*, root: Path, output_path: str) -> tuple[Path | None, str | None]:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return None, _finding_reason("absolute_output_path", "Output path must be root-relative.", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if not relative_path:
        return None, _finding_reason("empty_output_path", "Output path must not be empty.")
    if ".." in Path(relative_path).parts:
        return None, _finding_reason("parent_traversal_output_path", "Output path must not use parent traversal.", path=relative_path)
    if _path_contains_env(relative_path):
        return None, _finding_reason("secret_output_path", "Output path must not target .env files.", path=relative_path)
    if any(relative_path == prefix.rstrip("/") or relative_path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return None, _finding_reason("protected_output_path", "Output path targets a protected surface.", path=relative_path)
    if not relative_path.startswith("tmp/") or not relative_path.endswith(".json"):
        return None, _finding_reason("protected_output_path", "Output writes are admitted only to root-relative tmp/**.json.", path=relative_path)

    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding_reason("outside_root_output_path", "Output path must stay inside the ATLAS root.", path=relative_path)
    return resolved, None


def _load_json_artifact(*, root: Path, artifact_path: str) -> tuple[dict[str, Any] | None, str | None]:
    resolved, path_error = _validate_artifact_path(root=root, artifact_path=artifact_path)
    if path_error is not None:
        return None, path_error
    assert resolved is not None
    try:
        loaded = json.loads(resolved.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return None, _finding_reason("invalid_json_input", "Input artifact is not valid JSON.", path=_normalized_relative(artifact_path), error=str(exc))
    except OSError as exc:
        return None, _finding_reason("input_read_failed", "Input artifact could not be read.", path=_normalized_relative(artifact_path), error=str(exc))
    if not isinstance(loaded, dict):
        return None, _finding_reason("invalid_json_shape", "Input artifact JSON must be an object.", path=_normalized_relative(artifact_path))
    return loaded, None


def _ordered_validation_state(value: Any) -> OrderedDict[str, int]:
    if not isinstance(value, dict):
        value = {}
    source: dict[str, Any] = value
    for key in ("validation_state", "validation", "summary"):
        nested = source.get(key)
        if isinstance(nested, dict):
            source = nested
            break
    return OrderedDict(
        [
            ("critical", _int_count(source.get("critical", source.get("critical_count", 0)))),
            ("error", _int_count(source.get("error", source.get("error_count", 0)))),
            ("warning", _int_count(source.get("warning", source.get("warning_count", 0)))),
            ("info", _int_count(source.get("info", source.get("info_count", 0)))),
        ]
    )


def _int_count(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def _root_clean(closeout: dict[str, Any], validation_state: dict[str, int]) -> bool:
    if isinstance(closeout.get("root_clean"), bool):
        return bool(closeout["root_clean"])
    if isinstance(closeout.get("dirty_repo_count"), int):
        return int(closeout["dirty_repo_count"]) == 0
    inventory = closeout.get("inventory")
    if isinstance(inventory, dict) and isinstance(inventory.get("dirty_repo_count"), int):
        return int(inventory["dirty_repo_count"]) == 0
    published_inventory = closeout.get("published_inventory")
    if isinstance(published_inventory, dict) and isinstance(published_inventory.get("dirty_repo_count"), int):
        return int(published_inventory["dirty_repo_count"]) == 0
    return validation_state.get("critical", 0) == 0 and validation_state.get("error", 0) == 0


def _selector_action(selector: dict[str, Any]) -> str | None:
    for key in ("operator_action", "selector_action", "action"):
        value = selector.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    selected = selector.get("selection")
    if isinstance(selected, dict):
        value = selected.get("operator_action") or selected.get("action")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _planner_status(planner: dict[str, Any]) -> str | None:
    value = planner.get("status")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _selected_packet(selector: dict[str, Any], planner: dict[str, Any]) -> str | None:
    selector_action = _selector_action(selector)
    selector_current_packet = None
    if selector_action not in {"no_immediate_root_packet", "hold_current_lane", "held", "hold"}:
        selector_current_packet = selector.get("selected_current_packet")
    for value in (
        planner.get("selected_packet"),
        planner.get("recommended_next_selection"),
        planner.get("packet"),
        selector.get("selected_packet"),
        selector_current_packet,
        selector.get("next_packet"),
        selector.get("next_after_current_packet"),
    ):
        rendered = _string_value(value)
        if rendered:
            return rendered
    return None


def _selected_packet_source(selector: dict[str, Any], planner: dict[str, Any], selected_packet: str | None, operator_packet: str | None) -> str | None:
    if operator_packet:
        return "operator_selected_packet"
    if selected_packet is None:
        return None
    if _string_value(planner.get("selected_packet")) == selected_packet:
        return "planner_selected_packet"
    for item in planner.get("candidate_scores") or []:
        if isinstance(item, dict) and _string_value(item.get("packet")) == selected_packet:
            return "planner_candidate_packet"
    selector_action = _selector_action(selector)
    if selector_action not in {"no_immediate_root_packet", "hold_current_lane", "held", "hold"} and _string_value(selector.get("selected_current_packet")) == selected_packet:
        return "selector_current_packet"
    if _string_value(selector.get("next_packet")) == selected_packet or _string_value(selector.get("next_after_current_packet")) == selected_packet:
        return "selector_next_packet"
    return "unknown"


def _planner_candidate_for_packet(planner: dict[str, Any], packet: str | None) -> dict[str, Any] | None:
    if packet is None:
        return None
    for item in planner.get("candidate_scores") or []:
        if isinstance(item, dict) and _string_value(item.get("packet")) == packet:
            return item
    return None


def _planner_packet_is_safe(candidate: dict[str, Any] | None) -> bool:
    if not isinstance(candidate, dict):
        return False
    return candidate.get("safe_to_select") is True and _string_value(candidate.get("classification")) in SAFE_PLANNER_CLASSIFICATIONS


def _candidate_text(*values: Any) -> str:
    rendered: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            rendered.append(value)
            continue
        if isinstance(value, dict):
            for key in ("selected_packet", "recommended_next_selection", "packet", "operator_action", "status", "classification", "reason", "mode"):
                rendered_value = value.get(key)
                if isinstance(rendered_value, str):
                    rendered.append(rendered_value)
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    rendered.extend(str(item.get(key) or "") for key in ("packet", "marker", "classification", "reason", "mode"))
                elif isinstance(item, str):
                    rendered.append(item)
    return " ".join(rendered).lower()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms if term)


def _packet_authority_risk(
    *,
    selected_text: str,
    selected_or_candidate_text: str,
    owner_fallback_forbidden: bool,
) -> str:
    if _has_any(selected_text, PROTECTED_TERMS):
        return "protected_secret_deploy_workflow_or_final_receipt_authority"
    if _has_any(selected_text, MARKER_AUTHORITY_TERMS):
        return "marker_movement_authority_claim"
    if owner_fallback_forbidden and _has_any(selected_text, OWNER_LANE_TERMS):
        return "owner_lane_mutation"
    if _has_any(selected_text, OWNER_FALLBACK_TERMS) or ("owner" in selected_text and "fallback" in selected_text):
        return "owner_lane_fallback"
    if _has_any(selected_or_candidate_text, STALE_TERMS):
        return "stale_or_completed_packet"
    return "none"


def _exact_packet_available(packet: str | None) -> bool:
    if packet is None:
        return False
    text = packet.strip().lower()
    if not text:
        return False
    if any(text == term or text.startswith(f"{term}:") for term in NO_PACKET_TERMS if term):
        return False
    return "no immediate" not in text


def _owner_lane_fallback_forbidden(closeout: dict[str, Any]) -> bool:
    value = closeout.get("owner_lane_fallback_forbidden")
    return bool(value) if isinstance(value, bool) else True


def _allowed_actions(decision: str) -> list[str]:
    return {
        DECISION_SUPPRESS_CONTINUATION: [
            "stop_and_report_held_root_state",
            "wait_for_exact_root_packet_or_material_state_change",
        ],
        DECISION_ALLOW_EXACT_PACKET: [
            "run_exact_root_packet",
            "verify_and_record_receipt_before_marker_ratchet",
        ],
        DECISION_ALLOW_OPERATOR_SELECTED_PACKET: [
            "run_operator_selected_packet_with_scope_lock",
            "verify_no_owner_or_protected_surfaces",
        ],
        DECISION_ALLOW_VALIDATION_CLEANUP: [
            "run_stack_validation_cleanup",
            "rerun_suppression_helper_after_clean",
        ],
        DECISION_ALLOW_WORKER_RECONCILIATION: [
            "run_worker_or_reconciliation_packet",
            "commit_only_allowed_worker_scope_when_clean",
        ],
        DECISION_BLOCKED_BY_SCOPE_LOCK: [
            "stop_without_mutation",
            "narrow_packet_to_root_allowed_surfaces",
        ],
        DECISION_BLOCKED_BY_OWNER_LANE_FALLBACK: [
            "stop_without_mutation",
            "route_fitness_or_mazer_to_separate_owner_lane",
        ],
        DECISION_INTERNAL_ERROR: [
            "fix_helper_input_or_fixture",
            "rerun_with_valid_json_artifacts",
        ],
    }.get(decision, ["stop_without_mutation"])


def _decision_to_status(decision: str) -> str:
    if decision == DECISION_SUPPRESS_CONTINUATION:
        return STATUS_SUPPRESS
    if decision.startswith("allow_"):
        return STATUS_ALLOW
    if decision.startswith("blocked_"):
        return STATUS_BLOCKED
    if decision == DECISION_INTERNAL_ERROR:
        return STATUS_INTERNAL_ERROR
    return STATUS_OK


def _build_payload(
    *,
    decision: str,
    root_clean: bool,
    validation_state: OrderedDict[str, int],
    selector_action: str | None,
    planner_status: str | None,
    selected_packet: str | None,
    selected_packet_source: str | None,
    selected_packet_classification: str | None,
    packet_authority_risk: str,
    owner_lane_fallback_forbidden: bool,
    exact_packet_available: bool,
    operator_selected_packet: str | None,
    suppression_reason: str,
) -> OrderedDict[str, Any]:
    status = _decision_to_status(decision)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("decision", decision),
            ("root_clean", root_clean),
            ("validation_state", validation_state),
            ("selector_action", selector_action),
            ("planner_status", planner_status),
            ("selected_packet", selected_packet),
            ("selected_packet_source", selected_packet_source),
            ("selected_packet_classification", selected_packet_classification),
            ("packet_authority_risk", packet_authority_risk),
            ("owner_lane_fallback_forbidden", owner_lane_fallback_forbidden),
            ("exact_packet_available", exact_packet_available),
            ("operator_selected_packet", operator_selected_packet),
            ("suppression_reason", suppression_reason),
            ("allowed_next_actions", _allowed_actions(decision)),
            ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
            ("failure_mode_refs", FAILURE_MODE_REFS),
            ("safe_to_continue", status == STATUS_ALLOW or status == STATUS_OK),
        ]
    )


def build_report(
    *,
    selector_report: dict[str, Any] | None = None,
    planner_report: dict[str, Any] | None = None,
    closeout_report: dict[str, Any] | None = None,
    operator_selected_packet: str | None = None,
    external_proof_present: bool = False,
) -> OrderedDict[str, Any]:
    selector = selector_report or {}
    planner = planner_report or {}
    closeout = closeout_report or {}
    validation_state = _ordered_validation_state(closeout)
    root_clean = _root_clean(closeout, validation_state)
    selector_action = _selector_action(selector)
    planner_status = _planner_status(planner)
    selected_packet = _selected_packet(selector, planner)
    operator_packet = _string_value(operator_selected_packet)
    selected_packet_source = _selected_packet_source(selector, planner, selected_packet, operator_packet)
    planner_candidate = _planner_candidate_for_packet(planner, selected_packet)
    selected_packet_classification = _string_value(planner_candidate.get("classification")) if isinstance(planner_candidate, dict) else None
    selected_packet_planner_safe = _planner_packet_is_safe(planner_candidate)
    exact_packet = _exact_packet_available(selected_packet)
    owner_fallback_forbidden = _owner_lane_fallback_forbidden(closeout)
    selected_text = _candidate_text(selected_packet, operator_packet)
    selected_or_candidate_text = _candidate_text(selected_packet, operator_packet, planner.get("candidate_scores"))
    packet_authority_risk = _packet_authority_risk(
        selected_text=selected_text,
        selected_or_candidate_text=selected_or_candidate_text,
        owner_fallback_forbidden=owner_fallback_forbidden,
    )

    if packet_authority_risk == "protected_secret_deploy_workflow_or_final_receipt_authority":
        decision = DECISION_BLOCKED_BY_SCOPE_LOCK
        reason = "Selected continuation touches protected, secret, deploy, workflow, or final-receipt authority."
    elif packet_authority_risk == "marker_movement_authority_claim":
        decision = DECISION_BLOCKED_BY_SCOPE_LOCK
        reason = "Selected continuation claims marker movement authority instead of using receipt-backed proof."
    elif packet_authority_risk == "owner_lane_mutation":
        decision = DECISION_BLOCKED_BY_OWNER_LANE_FALLBACK
        reason = "Selected continuation tries to route Fitness or Mazer from an ATLAS-root governance lane."
    elif packet_authority_risk == "owner_lane_fallback":
        decision = DECISION_BLOCKED_BY_SCOPE_LOCK
        reason = "Selected continuation tries to use owner-lane fallback despite root scope lock."
    elif packet_authority_risk == "stale_or_completed_packet":
        decision = DECISION_SUPPRESS_CONTINUATION
        reason = "Candidate packet appears stale or already completed; no rerun authority is inferred."
    elif validation_state["critical"] > 0 or validation_state["error"] > 0 or not root_clean:
        decision = DECISION_ALLOW_VALIDATION_CLEANUP
        reason = "Root or validation state is not clean; cleanup/recheck is allowed before suppression."
    elif operator_packet:
        decision = DECISION_ALLOW_OPERATOR_SELECTED_PACKET
        reason = "Operator explicitly selected a bounded root packet."
    elif external_proof_present:
        decision = DECISION_ALLOW_EXACT_PACKET
        reason = "External proof was supplied and admitted; suppression would be stale."
    elif exact_packet and selected_packet_planner_safe:
        decision = DECISION_ALLOW_EXACT_PACKET
        reason = "Planner-selected packet is explicitly safe to select; marker or ratchet wording alone is not authority."
    elif exact_packet and _has_any(selected_text, WORKER_TERMS):
        decision = DECISION_ALLOW_WORKER_RECONCILIATION
        reason = "A worker, readiness, or reconciliation packet is available and should not be suppressed."
    elif exact_packet:
        decision = DECISION_ALLOW_EXACT_PACKET
        reason = "An exact root packet is available."
    else:
        held_selector = selector_action in {None, "no_immediate_root_packet", "hold_current_lane", "held", "hold"}
        no_safe_planner_packet = planner_status in {None, "ok", "advisory_matrix", "advisory_recommendation", "held", "blocked"}
        if root_clean and validation_state["critical"] == 0 and validation_state["error"] == 0 and held_selector and no_safe_planner_packet and owner_fallback_forbidden:
            decision = DECISION_SUPPRESS_CONTINUATION
            reason = "Clean held root state has no exact packet or operator-selected packet; owner-lane fallback is forbidden."
        else:
            decision = DECISION_BLOCKED_BY_SCOPE_LOCK
            reason = "State is ambiguous; fail closed instead of inferring continuation authority."

    return _build_payload(
        decision=decision,
        root_clean=root_clean,
        validation_state=validation_state,
        selector_action=selector_action,
        planner_status=planner_status,
        selected_packet=selected_packet,
        selected_packet_source=selected_packet_source,
        selected_packet_classification=selected_packet_classification,
        packet_authority_risk=packet_authority_risk,
        owner_lane_fallback_forbidden=owner_fallback_forbidden,
        exact_packet_available=exact_packet,
        operator_selected_packet=operator_packet,
        suppression_reason=reason,
    )


def _git_stdout(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _live_selector_report(root: Path) -> dict[str, Any]:
    text = subprocess.check_output(
        [sys.executable, str(root / "ops" / "atlas" / "marker_knockout_selector.py"), "--format", "json"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    loaded = json.loads(text)
    return loaded if isinstance(loaded, dict) else {}


def _live_planner_report(root: Path) -> dict[str, Any]:
    text = subprocess.check_output(
        [sys.executable, str(root / "ops" / "atlas" / "marker_aware_next_packet_planner.py"), "--json"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    loaded = json.loads(text)
    return loaded if isinstance(loaded, dict) else {}


def _live_closeout_report(root: Path) -> dict[str, Any]:
    dirty = _git_stdout(root, "status", "--porcelain")
    validation_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    validation: dict[str, Any] = {}
    if validation_path.exists():
        try:
            loaded = json.loads(validation_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                validation = loaded
        except (OSError, json.JSONDecodeError):
            validation = {}
    return {
        "root_clean": dirty == "",
        "validation_state": _ordered_validation_state(validation),
        "owner_lane_fallback_forbidden": True,
    }


def _load_or_live_reports(
    *,
    root: Path,
    selector_output: str | None,
    planner_output: str | None,
    closeout_output: str | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, str | None]:
    if selector_output:
        selector, error = _load_json_artifact(root=root, artifact_path=selector_output)
        if error is not None:
            return None, None, None, error
    else:
        selector = _live_selector_report(root)

    if planner_output:
        planner, error = _load_json_artifact(root=root, artifact_path=planner_output)
        if error is not None:
            return None, None, None, error
    else:
        planner = _live_planner_report(root)

    if closeout_output:
        closeout, error = _load_json_artifact(root=root, artifact_path=closeout_output)
        if error is not None:
            return None, None, None, error
    else:
        closeout = _live_closeout_report(root)

    return selector, planner, closeout, None


def _error_report(reason: str, *, decision: str = DECISION_INTERNAL_ERROR) -> OrderedDict[str, Any]:
    return _build_payload(
        decision=decision,
        root_clean=False,
        validation_state=OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)]),
        selector_action=None,
        planner_status=None,
        selected_packet=None,
        selected_packet_source=None,
        selected_packet_classification=None,
        packet_authority_risk="internal_error",
        owner_lane_fallback_forbidden=True,
        exact_packet_available=False,
        operator_selected_packet=None,
        suppression_reason=reason,
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status in {STATUS_OK, STATUS_ALLOW}:
        return 0
    if status == STATUS_SUPPRESS:
        return 1 if strict else 0
    if status == STATUS_BLOCKED:
        return 2
    return 3


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Decision: {report.get('decision')}",
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
            f"Reason: {report.get('suppression_reason')}",
            "",
            json_text,
        ]
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Suppress held-lane continuation prompts when ATLAS root has no exact admissible packet.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--selector-output", help="Optional root-relative selector JSON artifact.")
    parser.add_argument("--planner-output", help="Optional root-relative planner JSON artifact.")
    parser.add_argument("--closeout-output", help="Optional root-relative closeout JSON artifact.")
    parser.add_argument("--operator-selected-packet", help="Explicit operator-selected root packet name.")
    parser.add_argument("--external-proof-present", action="store_true", help="Allow continuation when an admitted external proof path exists.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for suppressed held-lane states.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        selector, planner, closeout, load_error = _load_or_live_reports(
            root=root,
            selector_output=args.selector_output,
            planner_output=args.planner_output,
            closeout_output=args.closeout_output,
        )
        if load_error is not None:
            report = _error_report(load_error)
        else:
            report = build_report(
                selector_report=selector,
                planner_report=planner,
                closeout_report=closeout,
                operator_selected_packet=args.operator_selected_packet,
                external_proof_present=bool(args.external_proof_present),
            )

        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report = _build_payload(
                    decision=DECISION_BLOCKED_BY_SCOPE_LOCK,
                    root_clean=bool(report.get("root_clean")),
                    validation_state=_ordered_validation_state({"validation_state": report.get("validation_state")}),
                    selector_action=report.get("selector_action") if isinstance(report.get("selector_action"), str) else None,
                    planner_status=report.get("planner_status") if isinstance(report.get("planner_status"), str) else None,
                    selected_packet=report.get("selected_packet") if isinstance(report.get("selected_packet"), str) else None,
                    selected_packet_source=report.get("selected_packet_source") if isinstance(report.get("selected_packet_source"), str) else None,
                    selected_packet_classification=report.get("selected_packet_classification") if isinstance(report.get("selected_packet_classification"), str) else None,
                    packet_authority_risk=report.get("packet_authority_risk") if isinstance(report.get("packet_authority_risk"), str) else "output_path_error",
                    owner_lane_fallback_forbidden=bool(report.get("owner_lane_fallback_forbidden")),
                    exact_packet_available=bool(report.get("exact_packet_available")),
                    operator_selected_packet=report.get("operator_selected_packet") if isinstance(report.get("operator_selected_packet"), str) else None,
                    suppression_reason=output_error,
                )
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=bool(args.strict))
    except Exception as exc:
        report = _error_report(_finding_reason("internal_error", "Held-lane prompt suppression failed.", error=str(exc)))
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
