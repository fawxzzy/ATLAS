from __future__ import annotations

"""Select deterministic dependency-ready waves under conflict-group leases."""

import argparse
import hashlib
import fnmatch
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas import ai_work_session_preflight
from ops.atlas import marker_aware_next_packet_planner as planner

SCHEMA_VERSION = "atlas.autonomous_lane_scheduler.v2"
PROGRAM_SCHEMA_VERSION = "atlas.autonomous-work-program.v2"
LEGACY_PROGRAM_SCHEMA_VERSION = "atlas.autonomous-work-program.v1"

STATUS_EXECUTE = "execute"
STATUS_HOLD = "hold"
STATUS_VALIDATION_CLEANUP = "validation_cleanup"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

DECISION_VALIDATION_CLEANUP = "validation_cleanup"
DECISION_WORKER_RECONCILIATION = "worker_reconciliation"
DECISION_ROUTED_WORKER = "routed_worker"
DECISION_EXACT_MANIFEST_PACKET = "exact_manifest_packet"
DECISION_OPERATOR_PROGRAM_PACKET = "operator_program_packet"
DECISION_CROSS_MARKER_OPPORTUNITY = "cross_marker_opportunity"
DECISION_PLANNER_CANDIDATE = "planner_candidate"
DECISION_EXECUTION_WAVE = "execution_wave"
DECISION_HOLD = "hold"

PHASE_WORKER_RECONCILIATION = "worker_reconciliation"
PHASE_WORKER_IMPLEMENTATION = "worker_implementation"
PHASE_IMPLEMENTATION_READINESS = "implementation_readiness"
PHASE_PROMPT_PACK = "prompt_pack"
PHASE_FIRST_IMPLEMENTATION_ADMISSION = "first_implementation_admission"
PHASE_CONTRACT_FREEZE = "contract_freeze"
PHASE_SELECTOR = "selector"
PHASE_HOLD = "hold"

EXECUTION_CLASSES = {"read_only", "repo_worktree", "canonical_workspace", "external_mutation"}
READY_STATES = {"READY", "ADMITTED", "QUEUED"}
RECOVERY_READY_STATE = "RECOVERY_READY"
MUTATING_EXECUTION_CLASSES = {"repo_worktree", "canonical_workspace", "external_mutation"}
REPOSITORY_MUTATING_EXECUTION_CLASSES = {"repo_worktree", "canonical_workspace"}
EVENT_ID_PATTERN = re.compile(r"^onv1_[0-9a-f]{64}$")
PAYLOAD_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RESUMABLE_RUNTIME_STATES = {"idle", "notloaded"}
TERMINAL_SUCCESS_STATES = {"ACCEPTED", "COMPLETE", "COMPLETED", "MERGED", "SUCCESS"}
STANDING_LOCAL_SOURCE_PREPARATION = "standing_local_source_preparation"
STANDING_LOCAL_SOURCE_ROLES = {"atlas.main", "fawxzzy.questions"}
COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
MAX_STANDING_LOCAL_SOURCE_PATHS = 32
STANDING_LOCAL_PROTECTED_PATHS = (".env", ".git/", ".github/workflows/", "secrets/")
RECOVERY_RECONCILIATION_BASIS = "COMPLETE_TARGET_TASK_HISTORY"
RECOVERY_ABSENCE_EVIDENCE_SCHEMA = "atlas.scheduler.delivery-recovery-evidence.v1"
RECOVERY_ABSENCE_EVENT_CLASS = "DELIVERY_RECOVERY_ABSENCE_PROOF"
RECOVERY_ABSENCE_ENVELOPE_KIND = "DELIVERY_RECOVERY_PROOF"
RECOVERY_ABSENCE_CALL_STATE = "TERMINALLY_LOST"
RECOVERY_ABSENCE_AUTHORITIES = {"atlas.main", "atlas.workflow-architect"}

SAFE_CLASSIFICATIONS = {
    planner.CLASS_IMPLEMENTATION_READY,
    planner.CLASS_IMMEDIATE,
    planner.CLASS_DOCS_ONLY,
}
DOCS_ONLY_PHASES = {
    PHASE_IMPLEMENTATION_READINESS,
    PHASE_PROMPT_PACK,
    PHASE_FIRST_IMPLEMENTATION_ADMISSION,
    PHASE_CONTRACT_FREEZE,
    PHASE_SELECTOR,
}
OWNER_LANE_TERMS = (
    "fitness",
    "mazer",
    "discordos",
    "foundation",
    "trove",
    "stream",
    "owner repo",
    "owner-repo",
    "playbook owner repo",
    "repos/playbook",
    "repos\\playbook",
)
PROTECTED_TERMS = (
    ".env",
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    "archive/",
    "deploy",
    "deployment",
    "provider mutation",
    "production mutation",
    "secret",
    "workflow dispatch",
)
AUTHORITY_DENIALS = [
    "unadmitted-owner-repo-mutation",
    "unadmitted-platform-mutation",
    "unadmitted-deploy",
    "secret-handling",
    "workflow-dispatch",
    "final-receipt",
    "marker-movement",
    "hidden-transcript-ingestion",
]
BASELINE_COMMANDS = [
    "git status -sb",
    "git branch --show-current",
    "git fetch origin main",
    "git rev-list --left-right --count origin/main...HEAD",
    "git log -15 --oneline --decorate",
    "git diff --name-only",
    "git diff --cached --name-only",
    "python ops/validation/validate_stack.py",
    "python ops/atlas/marker_knockout_selector.py --format json",
    "python ops/atlas/continuity_manifest_health.py",
    "python ops/atlas/continuity_open_marker_restart_index.py",
    "python ops/atlas/continuity_coverage.py",
]


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _dedupe_findings(findings: list[OrderedDict[str, Any]]) -> list[OrderedDict[str, Any]]:
    unique: list[OrderedDict[str, Any]] = []
    seen: set[str] = set()
    for finding in findings:
        identity = json.dumps(finding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(finding)
    return unique


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


def _branch_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _parity_state(root: Path) -> OrderedDict[str, Any]:
    raw = _git_stdout(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    if raw is None:
        return OrderedDict([("status", "unknown"), ("behind", None), ("ahead", None)])
    parts = raw.split()
    if len(parts) != 2:
        return OrderedDict([("status", "unknown"), ("behind", None), ("ahead", None)])
    behind = int(parts[0])
    ahead = int(parts[1])
    return OrderedDict([("status", "clean" if behind == 0 and ahead == 0 else "drift"), ("behind", behind), ("ahead", ahead)])


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    if ref.startswith("repos/") or ref.startswith("archive/") or ref.startswith("secrets/"):
        return None, _finding("protected_path_forbidden", "Path targets a protected surface.", path=ref)
    if any(part.startswith(".env") for part in ref.split("/")):
        return None, _finding("secret_path_forbidden", "Path targets an env secret surface.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def validate_program_path(
    root: Path,
    path: str,
    *,
    allow_missing: bool = False,
) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(path, root)
    if error is not None or ref is None:
        return None, error
    if not ref.endswith(".json"):
        return None, _finding("program_not_json", "Program path must end with .json.", path=ref)
    resolved = (root / ref).resolve()
    if not resolved.exists() and not allow_missing:
        return None, _finding("program_missing", "Program path does not exist.", path=ref)
    return resolved, None


def validate_output_path(root: Path, path: str, *, suffix: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(path, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/atlas/") or not ref.endswith(suffix):
        return None, _finding("protected_output_path", f"Output path must be under tmp/atlas/** and end with {suffix}.", path=ref)
    return (root / ref).resolve(), None


def validate_input_path(
    root: Path,
    path: str,
    *,
    suffixes: tuple[str, ...],
) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(path, root)
    if error is not None or ref is None:
        return None, error
    if not ref.endswith(suffixes):
        return None, _finding("input_suffix_forbidden", "Input path has an unsupported suffix.", path=ref, suffixes=list(suffixes))
    resolved = (root / ref).resolve()
    if not resolved.exists():
        return None, _finding("input_missing", "Input path does not exist.", path=ref)
    return resolved, None


def load_program(root: Path, program_path: str) -> tuple[dict[str, Any] | None, list[OrderedDict[str, Any]]]:
    resolved, error = validate_program_path(root, program_path)
    if error is not None or resolved is None:
        return None, [error] if error is not None else []
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [_finding("program_invalid_json", "Program file is not valid JSON.", path=program_path, error=str(exc))]
    if not isinstance(payload, dict):
        return None, [_finding("program_invalid_shape", "Program payload must be a JSON object.", path=program_path)]
    errors: list[OrderedDict[str, Any]] = []
    if payload.get("schema_version") not in {PROGRAM_SCHEMA_VERSION, LEGACY_PROGRAM_SCHEMA_VERSION}:
        errors.append(
            _finding(
                "program_schema_mismatch",
                "Program schema_version is not admitted.",
                expected=[LEGACY_PROGRAM_SCHEMA_VERSION, PROGRAM_SCHEMA_VERSION],
                actual=payload.get("schema_version"),
            )
        )
    for field in (
        "standing_packets",
        "active_leases",
        "scope_holds",
        "delivery_intents",
        "completed_packets",
        "completed_receipts",
        "processed_events",
        "released_leases",
    ):
        if field in payload and not isinstance(payload[field], list):
            errors.append(_finding("program_invalid_shape", f"{field} must be an array.", field=field))
    for field in ("max_parallel_writers", "max_parallel_read_only"):
        if field in payload and (not isinstance(payload[field], int) or payload[field] < 0):
            errors.append(_finding("program_invalid_shape", f"{field} must be a non-negative integer.", field=field))
    if isinstance(payload.get("active_leases"), list):
        for lease in payload["active_leases"]:
            if not isinstance(lease, dict) or not isinstance(lease.get("writer_scope"), str) or not lease["writer_scope"]:
                errors.append(_finding("program_invalid_active_lease", "Every active lease entry must name writer_scope."))
                continue
            if not isinstance(lease.get("repository"), str) or not lease["repository"].strip():
                errors.append(_finding("program_invalid_active_lease", "Every active lease entry must persist repository."))
            if lease.get("execution_class") not in MUTATING_EXECUTION_CLASSES:
                errors.append(_finding("program_invalid_active_lease", "Every active lease entry must persist a mutating execution_class."))
            if not isinstance(lease.get("resource_claims"), dict):
                errors.append(_finding("program_invalid_active_lease", "Every active lease entry must persist resource_claims."))
    return payload, errors


def _canonical_payload_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _initial_runtime_program() -> OrderedDict[str, Any]:
    """Return the deterministic empty snapshot used to replay durable journals."""

    empty_snapshot = {"bindings": [], "events": []}
    return OrderedDict(
        [
            ("schema_version", PROGRAM_SCHEMA_VERSION),
            ("revision", 1),
            ("source_snapshot_digest", _canonical_payload_digest(empty_snapshot)),
            ("max_parallel_writers", 4),
            ("max_parallel_read_only", 2),
            ("standing_packets", []),
            ("active_leases", []),
            ("scope_holds", []),
            ("delivery_intents", []),
            ("completed_packets", []),
            ("completed_receipts", []),
            ("released_leases", []),
            ("processed_events", []),
        ]
    )


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _load_envelopes(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        envelopes: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"envelope line {line_number} must be a JSON object")
            envelopes.append(value)
        return envelopes
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("envelopes"), list):
        return [item for item in payload["envelopes"] if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("envelope input must be a JSON object, array, or JSONL stream")


def apply_delivery_results(
    *,
    program: dict[str, Any],
    results: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[OrderedDict[str, Any]]]:
    """Settle app-native delivery using exact prepared-intent correlations."""

    findings: list[OrderedDict[str, Any]] = []
    unresolved_recovery_findings: OrderedDict[str, OrderedDict[str, Any]] = OrderedDict()
    unresolved_turn_collision_findings: OrderedDict[str, OrderedDict[str, Any]] = OrderedDict()
    unresolved_completed_turn_findings: OrderedDict[tuple[str, str], OrderedDict[str, Any]] = OrderedDict()
    intents = [item for item in program.get("delivery_intents", []) if isinstance(item, dict)]
    intent_index = {str(item.get("reservation_id")): item for item in intents if item.get("reservation_id")}
    leases = [item for item in program.get("active_leases", []) if isinstance(item, dict)]
    standing = [item for item in program.get("standing_packets", []) if isinstance(item, dict)]
    packet_index = {str(item.get("packet_id")): item for item in standing if item.get("packet_id")}
    completed_receipts = [item for item in program.get("completed_receipts", []) if isinstance(item, dict)]
    for result in results:
        reservation_id = str(result.get("reservation_id") or "")
        intent = intent_index.get(reservation_id)
        if intent is None:
            packet_id = str(result.get("packet_id") or "")
            completed_matches = [
                receipt
                for receipt in completed_receipts
                if str(receipt.get("reservation_id") or "") == reservation_id
                and str(receipt.get("packet_id") or "") == packet_id
            ]
            if len(completed_matches) == 1:
                completed = completed_matches[0]
                persisted_identity = {
                    "runtime_thread_id": completed.get("runtime_thread_id"),
                    "event_id": completed.get("event_id"),
                    "payload_digest": completed.get("payload_digest"),
                }
                if any(
                    value and str(result.get(field) or "") != str(value)
                    for field, value in persisted_identity.items()
                ):
                    findings.append(
                        _finding(
                            "delivery_result_correlation_mismatch",
                            "Delivery result does not match its completed receipt.",
                            reservation_id=reservation_id,
                        )
                    )
                    continue
                status = str(result.get("status") or "").upper()
                if completed.get("recovery_absence_evidence_digest"):
                    supplied_turn_id = str(result.get("turn_id") or "")
                    if status == "RECOVERY_REQUIRED" and not supplied_turn_id:
                        continue
                    findings.append(
                        _finding(
                            "recovery_absence_contradicted_by_delivery_evidence",
                            "A delivery result contradicted a completed proof that the original call was terminally absent.",
                            reservation_id=reservation_id,
                            turn_id=supplied_turn_id or None,
                        )
                    )
                    continue
                if not isinstance(completed.get("turn_id"), str) or not completed.get("turn_id"):
                    findings.append(
                        _finding(
                            "delivery_result_correlation_mismatch",
                            "Delivery result does not match its completed receipt.",
                            reservation_id=reservation_id,
                        )
                    )
                    continue
                if status == "RECOVERY_REQUIRED":
                    continue
                if status == "DELIVERED":
                    completed_turn_id = str(completed.get("turn_id") or "")
                    result_turn_id = str(result.get("turn_id") or "")
                    superseded_turn_ids = set(_string_list(completed.get("superseded_turn_ids")))
                    if completed_turn_id in superseded_turn_ids:
                        findings.append(
                            _finding(
                                "completed_receipt_self_supersession_forbidden",
                                "A completed receipt cannot supersede its own current turn.",
                                reservation_id=reservation_id,
                                turn_id=completed_turn_id,
                            )
                        )
                        continue
                    if result_turn_id in superseded_turn_ids:
                        continue
                    if result_turn_id == completed_turn_id:
                        supplied_supersedes_turn_id = str(result.get("supersedes_turn_id") or "")
                        if supplied_supersedes_turn_id == completed_turn_id:
                            findings.append(
                                _finding(
                                    "completed_receipt_self_supersession_forbidden",
                                    "A completed receipt cannot supersede its own current turn.",
                                    reservation_id=reservation_id,
                                    turn_id=completed_turn_id,
                                )
                            )
                            continue
                        exact_recovery = bool(
                            supplied_supersedes_turn_id
                            and result.get("history_reconciled") is True
                            and result.get("reconciliation_basis") == RECOVERY_RECONCILIATION_BASIS
                            and str(result.get("reconciled_event_id") or "") == str(completed.get("event_id") or "")
                            and result.get("effects_match_intent") is True
                        )
                        if exact_recovery:
                            unresolved_completed_turn_findings.pop(
                                (reservation_id, supplied_supersedes_turn_id),
                                None,
                            )
                            completed["superseded_turn_ids"] = sorted(
                                superseded_turn_ids | {supplied_supersedes_turn_id}
                            )
                        continue
                    unresolved_completed_turn_findings[(reservation_id, result_turn_id)] = _finding(
                        "delivery_result_correlation_mismatch",
                        "Delivery result does not match its completed receipt.",
                        reservation_id=reservation_id,
                        turn_id=result_turn_id or None,
                    )
                    continue
                findings.append(
                    _finding(
                        "delivery_result_correlation_mismatch",
                        "Delivery result does not match its completed receipt.",
                        reservation_id=reservation_id,
                    )
                )
                continue
            packet = packet_index.get(packet_id)
            authority = packet.get("authority") if isinstance(packet, dict) and isinstance(packet.get("authority"), dict) else {}
            runtime_thread_id = str(packet.get("runtime_thread_id") or "") if isinstance(packet, dict) else ""
            writer_scope = str(packet.get("writer_scope") or "") if isinstance(packet, dict) else ""
            reservation_seed = "|".join(
                [
                    packet_id,
                    writer_scope,
                    runtime_thread_id,
                    str(authority.get("event_id") or ""),
                ]
            )
            expected_reservation = "rsrv_" + hashlib.sha256(reservation_seed.encode("utf-8")).hexdigest()
            recoverable = bool(
                packet
                and str(packet.get("state") or "").upper() in READY_STATES | {"ACTIVE"}
                and reservation_id == expected_reservation
                and str(result.get("runtime_thread_id") or "") == runtime_thread_id
                and str(result.get("event_id") or "") == str(authority.get("event_id") or "")
                and str(result.get("payload_digest") or "") == str(authority.get("payload_digest") or "")
            )
            if not recoverable:
                findings.append(
                    _finding(
                        "delivery_intent_not_found",
                        "Delivery result has no prepared intent or exact replayable reservation.",
                        reservation_id=reservation_id or None,
                    )
                )
                continue
            packet["state"] = "ACTIVE"
            packet["dispatch_reservation"] = OrderedDict(
                [
                    ("reservation_id", reservation_id),
                    ("runtime_thread_id", runtime_thread_id),
                    ("recovered_from_delivery_journal", True),
                ]
            )
            intent = OrderedDict(
                [
                    ("reservation_id", reservation_id),
                    ("packet_id", packet_id),
                    ("logical_role_id", packet.get("logical_role_id")),
                    ("runtime_thread_id", runtime_thread_id),
                    ("writer_scope", writer_scope),
                    ("event_id", authority.get("event_id")),
                    ("payload_digest", authority.get("payload_digest")),
                    ("status", "prepared"),
                    ("turn_id", None),
                    ("recovered_from_delivery_journal", True),
                ]
            )
            intents.append(intent)
            intent_index[reservation_id] = intent
            if packet.get("execution_class") in MUTATING_EXECUTION_CLASSES:
                leases.append(
                    OrderedDict(
                        [
                            ("reservation_id", reservation_id),
                            ("packet_id", packet_id),
                            ("logical_role_id", packet.get("logical_role_id")),
                            ("runtime_thread_id", runtime_thread_id),
                            ("writer_scope", writer_scope),
                            ("repository", packet.get("repository")),
                            ("execution_class", packet.get("execution_class")),
                            ("resource_claims", _resource_claims(packet.get("resource_claims"))),
                            ("status", "active"),
                            ("authority_event_id", authority.get("event_id")),
                            ("recovered_from_delivery_journal", True),
                        ]
                    )
                )
        exact_fields = ("packet_id", "runtime_thread_id", "event_id", "payload_digest")
        if any(str(result.get(field) or "") != str(intent.get(field) or "") for field in exact_fields):
            findings.append(_finding("delivery_result_correlation_mismatch", "Delivery result does not match its prepared intent.", reservation_id=reservation_id))
            continue
        status = str(result.get("status") or "").upper()
        if status == "DELIVERED":
            turn_id = result.get("turn_id")
            if not isinstance(turn_id, str) or not turn_id:
                findings.append(_finding("delivery_turn_id_required", "Delivered result must include the returned turn_id.", reservation_id=reservation_id))
                continue
            prior_turn = intent.get("turn_id")
            pending_superseded_turn_id = intent.get("recovery_superseded_turn_id")
            superseded_turn_ids = set(_string_list(intent.get("superseded_turn_ids")))
            if turn_id in superseded_turn_ids or turn_id == pending_superseded_turn_id:
                continue
            if prior_turn not in {None, turn_id}:
                unresolved_turn_collision_findings[reservation_id] = _finding(
                    "delivery_turn_id_collision",
                    "One reservation resolved to multiple turn IDs.",
                    reservation_id=reservation_id,
                )
                continue
            if str(intent.get("status") or "").lower() == "recovery-required":
                superseded_turn_id = pending_superseded_turn_id
                recovery_exact = (
                    result.get("history_reconciled") is True
                    and result.get("reconciliation_basis") == RECOVERY_RECONCILIATION_BASIS
                    and str(result.get("reconciled_event_id") or "") == str(intent.get("event_id") or "")
                    and result.get("effects_match_intent") is True
                    and (
                        superseded_turn_id in {None, ""}
                        or str(result.get("supersedes_turn_id") or "") == str(superseded_turn_id)
                    )
                )
                if not recovery_exact:
                    unresolved_recovery_findings[reservation_id] = _finding(
                        "delivery_recovery_evidence_required",
                        "A recovery-required intent needs complete-history evidence before delivery can be accepted.",
                        reservation_id=reservation_id,
                    )
                    continue
                unresolved_recovery_findings.pop(reservation_id, None)
                intent.pop("recovery_superseded_turn_id", None)
                if superseded_turn_id not in {None, ""}:
                    intent["superseded_turn_ids"] = sorted(superseded_turn_ids | {str(superseded_turn_id)})
            intent["status"] = "delivered"
            intent["turn_id"] = turn_id
            for lease in leases:
                if lease.get("reservation_id") == reservation_id:
                    lease["status"] = "active"
        elif status == "RECOVERY_REQUIRED":
            prior_turn = intent.get("turn_id")
            superseded_turn_id = intent.get("recovery_superseded_turn_id") or prior_turn
            supplied_superseded_turn_id = result.get("superseded_turn_id")
            already_superseded_turn_ids = set(_string_list(intent.get("superseded_turn_ids")))
            if supplied_superseded_turn_id in already_superseded_turn_ids:
                unresolved_recovery_findings.pop(reservation_id, None)
                unresolved_turn_collision_findings.pop(reservation_id, None)
                continue
            if superseded_turn_id not in {None, ""} and str(supplied_superseded_turn_id or "") != str(superseded_turn_id):
                unresolved_recovery_findings[reservation_id] = _finding(
                    "delivery_recovery_supersession_required",
                    "Recovery must name the interrupted turn it supersedes before a new turn can be accepted.",
                    reservation_id=reservation_id,
                )
                continue
            unresolved_recovery_findings.pop(reservation_id, None)
            unresolved_turn_collision_findings.pop(reservation_id, None)
            intent["status"] = "recovery-required"
            intent["turn_id"] = None
            if superseded_turn_id not in {None, ""}:
                intent["recovery_superseded_turn_id"] = superseded_turn_id
            for lease in leases:
                if lease.get("reservation_id") == reservation_id:
                    lease["status"] = "recovery-required"
        else:
            findings.append(_finding("delivery_result_status_invalid", "Delivery result status must be DELIVERED or RECOVERY_REQUIRED.", reservation_id=reservation_id))
    findings.extend(unresolved_turn_collision_findings.values())
    findings.extend(unresolved_recovery_findings.values())
    findings.extend(unresolved_completed_turn_findings.values())
    program["delivery_intents"] = intents
    program["active_leases"] = leases
    program["standing_packets"] = standing
    return program, findings


def _binding_index(bindings_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bindings = bindings_payload.get("bindings", [])
    if not isinstance(bindings, list):
        return {}
    return {
        str(item["role_id"]): item
        for item in bindings
        if isinstance(item, dict) and isinstance(item.get("role_id"), str) and item["role_id"]
    }


def _deterministic_reservation_id(packet: dict[str, Any]) -> str:
    authority = packet.get("authority") if isinstance(packet.get("authority"), dict) else {}
    reservation_seed = "|".join(
        [
            str(packet.get("packet_id") or ""),
            str(packet.get("writer_scope") or ""),
            str(packet.get("runtime_thread_id") or ""),
            str(authority.get("event_id") or ""),
        ]
    )
    return "rsrv_" + hashlib.sha256(reservation_seed.encode("utf-8")).hexdigest()


def _terminal_success(payload: dict[str, Any]) -> bool:
    if payload.get("terminal") is not True:
        return False
    state = str(payload.get("canonical_lifecycle_state") or payload.get("state") or payload.get("status") or "").upper()
    tokens = set(state.split("_"))
    denied = {"BLOCKED", "FAILED", "LATENCY", "PENDING", "UNKNOWN"}
    return not tokens.intersection(denied) and bool(tokens.intersection(TERMINAL_SUCCESS_STATES | {"PASS"}))


def _terminal_cancellation(payload: dict[str, Any]) -> bool:
    if payload.get("terminal") is not True:
        return False
    state = str(payload.get("canonical_lifecycle_state") or payload.get("state") or payload.get("status") or "").upper()
    return bool(set(state.split("_")).intersection({"CANCELLED", "SUPERSEDED"}))


def _blocker_resume_authority(payload: dict[str, Any]) -> bool:
    """Identify the only envelope allowed to reactivate a blocked reservation."""

    return (
        payload.get("resume_authority") is True
        and str(payload.get("canonical_lifecycle_state") or "").upper() == "BLOCKER_CLEARED_RESUME_AUTHORITY"
    )


def _recovery_absence_evidence_violation(
    *,
    payload: dict[str, Any],
    packet: dict[str, Any],
    intent: dict[str, Any],
    reservation_id: str,
) -> str | None:
    """Validate a closed, content-addressed proof that an ambiguous send had no effect."""

    evidence = payload.get("delivery_recovery_evidence")
    evidence_digest = payload.get("delivery_recovery_evidence_digest")
    required_keys = {
        "schema",
        "reconciliation_basis",
        "target_history_receipt_event_id",
        "target_history_receipt_payload_digest",
        "history_complete",
        "original_call_state",
        "reservation_id",
        "packet_id",
        "writer_scope",
        "runtime_thread_id",
        "event_id",
        "payload_digest",
        "matching_turn_ids",
        "active_matching_turn_ids",
        "effects_match_intent",
    }
    if not isinstance(evidence, dict) or set(evidence) != required_keys:
        return "recovery_absence_evidence_shape_invalid"
    if not isinstance(evidence_digest, str) or not PAYLOAD_DIGEST_PATTERN.fullmatch(evidence_digest):
        return "recovery_absence_evidence_digest_invalid"
    if _canonical_payload_digest(evidence) != evidence_digest:
        return "recovery_absence_evidence_digest_mismatch"
    history_receipt_event_id = evidence.get("target_history_receipt_event_id")
    history_receipt_payload_digest = evidence.get("target_history_receipt_payload_digest")
    if (
        not isinstance(history_receipt_event_id, str)
        or not EVENT_ID_PATTERN.fullmatch(history_receipt_event_id)
        or not isinstance(history_receipt_payload_digest, str)
        or not PAYLOAD_DIGEST_PATTERN.fullmatch(history_receipt_payload_digest)
    ):
        return "recovery_absence_history_receipt_invalid"
    expected_identity = {
        "reservation_id": reservation_id,
        "packet_id": packet.get("packet_id"),
        "writer_scope": packet.get("writer_scope"),
        "runtime_thread_id": intent.get("runtime_thread_id"),
        "event_id": intent.get("event_id"),
        "payload_digest": intent.get("payload_digest"),
    }
    if any(str(evidence.get(field) or "") != str(value or "") for field, value in expected_identity.items()):
        return "recovery_absence_evidence_identity_mismatch"
    if (
        evidence.get("schema") != RECOVERY_ABSENCE_EVIDENCE_SCHEMA
        or evidence.get("reconciliation_basis") != RECOVERY_RECONCILIATION_BASIS
        or evidence.get("history_complete") is not True
        or evidence.get("original_call_state") != RECOVERY_ABSENCE_CALL_STATE
        or evidence.get("effects_match_intent") is not False
        or evidence.get("matching_turn_ids") != []
        or evidence.get("active_matching_turn_ids") != []
    ):
        return "recovery_absence_not_proven"
    return None


def _recovery_successor_violation(
    *,
    payload: dict[str, Any],
    packet: dict[str, Any],
    packets: dict[str, dict[str, Any]],
    delivery_intents: list[dict[str, Any]],
    active_leases: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    """Require one already-admitted, content-addressed successor before releasing recovery."""

    packet_id = str(packet.get("packet_id") or "")
    successors = [
        candidate
        for candidate in packets.values()
        if str(candidate.get("replaces_packet_id") or "") == packet_id
    ]
    if len(successors) != 1:
        return None, "recovery_absence_exact_successor_required"
    successor = successors[0]
    successor_packet_id = str(payload.get("superseded_by_packet_id") or "")
    successor_event_id = str(payload.get("successor_event_id") or "")
    successor_payload_digest = str(payload.get("successor_payload_digest") or "")
    authority = successor.get("authority") if isinstance(successor.get("authority"), dict) else {}
    if (
        not successor_packet_id
        or successor_packet_id == packet_id
        or str(successor.get("packet_id") or "") != successor_packet_id
        or str(authority.get("event_id") or "") != successor_event_id
        or str(authority.get("payload_digest") or "") != successor_payload_digest
        or not EVENT_ID_PATTERN.fullmatch(successor_event_id)
        or not PAYLOAD_DIGEST_PATTERN.fullmatch(successor_payload_digest)
    ):
        return None, "recovery_absence_successor_identity_mismatch"
    invariant_fields = (
        "logical_role_id",
        "repository",
        "writer_scope",
        "execution_class",
        "runtime_thread_id",
        "protected_surface_authorized",
    )
    if any(successor.get(field) != packet.get(field) for field in invariant_fields):
        return None, "recovery_absence_successor_scope_mismatch"
    if (
        _resource_claims(successor.get("resource_claims")) != _resource_claims(packet.get("resource_claims"))
        or _string_list(successor.get("dependencies")) != _string_list(packet.get("dependencies"))
        or str(successor.get("state") or "").upper() not in READY_STATES
    ):
        return None, "recovery_absence_successor_scope_mismatch"
    if any(str(intent.get("packet_id") or "") == successor_packet_id for intent in delivery_intents) or any(
        str(lease.get("packet_id") or "") == successor_packet_id for lease in active_leases
    ):
        return None, "recovery_absence_successor_already_dispatched"
    return successor, None


def reconcile_runtime_program(
    *,
    program: dict[str, Any],
    bindings_payload: dict[str, Any],
    envelopes: list[dict[str, Any]],
    root: Path | None = None,
) -> tuple[dict[str, Any], list[OrderedDict[str, Any]]]:
    """Build scheduler v2 state from immutable envelopes and standing bindings."""

    reconciled = json.loads(json.dumps(program))
    reconciled["schema_version"] = PROGRAM_SCHEMA_VERSION
    reconciled.pop("forbidden_owner_lanes", None)
    findings: list[OrderedDict[str, Any]] = []
    bindings = _binding_index(bindings_payload)
    standing = [item for item in reconciled.get("standing_packets", []) if isinstance(item, dict)]
    active_leases = [item for item in reconciled.get("active_leases", []) if isinstance(item, dict)]
    delivery_intents = [item for item in reconciled.get("delivery_intents", []) if isinstance(item, dict)]
    completed = set(_string_list(reconciled.get("completed_packets", [])))
    completed_receipts = [item for item in reconciled.get("completed_receipts", []) if isinstance(item, dict)]
    released = [item for item in reconciled.get("released_leases", []) if isinstance(item, dict)]
    processed_items = [item for item in reconciled.get("processed_events", []) if isinstance(item, dict)]
    processed = {
        str(item.get("event_id")): str(item.get("payload_digest"))
        for item in processed_items
        if isinstance(item.get("event_id"), str) and isinstance(item.get("payload_digest"), str)
    }
    packets = {str(item.get("packet_id")): item for item in standing if item.get("packet_id")}

    for envelope in envelopes:
        event_id = envelope.get("event_id")
        payload_digest = envelope.get("payload_digest")
        payload = envelope.get("payload")
        if (
            not isinstance(event_id, str)
            or not EVENT_ID_PATTERN.fullmatch(event_id)
            or not isinstance(payload_digest, str)
            or not PAYLOAD_DIGEST_PATTERN.fullmatch(payload_digest)
            or not isinstance(payload, dict)
        ):
            findings.append(_finding("noncanonical_envelope", "Envelope identity or payload is not canonical."))
            continue
        expected_digest = _canonical_payload_digest(payload)
        expected_event_id = "onv1_" + expected_digest.removeprefix("sha256:")
        if payload_digest != expected_digest or event_id != expected_event_id:
            findings.append(
                _finding(
                    "envelope_digest_mismatch",
                    "Envelope event_id and payload_digest must match canonical payload bytes.",
                    event_id=event_id,
                )
            )
            continue
        prior_digest = processed.get(event_id)
        if prior_digest is not None:
            if prior_digest != payload_digest:
                findings.append(_finding("event_identity_collision", "One event_id carried more than one digest.", event_id=event_id))
            continue
        processed[event_id] = payload_digest
        processed_items.append(OrderedDict([("event_id", event_id), ("payload_digest", payload_digest)]))

        packet_id = str(payload.get("packet_id") or "")
        writer_scope = str(payload.get("writer_scope") or "")
        if _blocker_resume_authority(payload):
            packet = packets.get(packet_id)
            reservation_id = str(payload.get("reservation_id") or "")
            prior_receipt_event_id = str(payload.get("prior_blocking_receipt_event_id") or "")
            prior_receipt_digest = str(payload.get("prior_blocking_receipt_payload_digest") or "")
            current_turn_id = str(payload.get("current_delivered_turn_id") or "")
            dispatch_reservation = packet.get("dispatch_reservation") if isinstance(packet, dict) else {}
            blocking_receipt = packet.get("blocking_receipt") if isinstance(packet, dict) else {}
            prior_resume_authority = packet.get("resume_authority") if isinstance(packet, dict) else None
            if prior_resume_authority is None:
                current_delivery_authority = packet.get("authority") if isinstance(packet, dict) else {}
            elif _authority_is_canonical(prior_resume_authority):
                current_delivery_authority = prior_resume_authority
            else:
                current_delivery_authority = {}
            matching_intents = [
                intent
                for intent in delivery_intents
                if str(intent.get("reservation_id") or "") == reservation_id
                and str(intent.get("packet_id") or "") == packet_id
                and str(intent.get("writer_scope") or "") == writer_scope
                and str(intent.get("turn_id") or "") == current_turn_id
                and str(intent.get("status") or "").lower() == "delivered"
                and str(intent.get("event_id") or "") == str(current_delivery_authority.get("event_id") or "")
                and str(intent.get("payload_digest") or "") == str(current_delivery_authority.get("payload_digest") or "")
            ]
            matching_leases = [
                lease
                for lease in active_leases
                if str(lease.get("reservation_id") or "") == reservation_id
                and str(lease.get("packet_id") or "") == packet_id
                and str(lease.get("writer_scope") or "") == writer_scope
                and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
            ]
            resume_correlation_exact = bool(
                envelope.get("source_role_id") == "atlas.main"
                and packet
                and str(packet.get("state") or "").upper() == "BLOCKED"
                and str(packet.get("writer_scope") or "") == writer_scope
                and str(dispatch_reservation.get("reservation_id") or "") == reservation_id
                and str(blocking_receipt.get("event_id") or "") == prior_receipt_event_id
                and str(blocking_receipt.get("payload_digest") or "") == prior_receipt_digest
                and len(matching_intents) == 1
                and len(matching_leases) == 1
                and _authority_is_canonical(current_delivery_authority)
            )
            logical_role_id = str(packet.get("logical_role_id") or "") if packet else ""
            current_binding = bindings.get(logical_role_id)
            current_runtime_thread_id = (
                str(current_binding.get("current_runtime_id") or "")
                if isinstance(current_binding, dict)
                else ""
            )
            retained_runtime_thread_id = (
                str(matching_intents[0].get("runtime_thread_id") or "")
                if len(matching_intents) == 1
                else ""
            )
            runtime_binding_exact = bool(
                isinstance(current_binding, dict)
                and current_binding.get("archived") is not True
                and current_runtime_thread_id
                and current_runtime_thread_id == retained_runtime_thread_id
            )
            exact_resume = bool(resume_correlation_exact and runtime_binding_exact)
            if not exact_resume:
                processed.pop(event_id, None)
                processed_items = [item for item in processed_items if item.get("event_id") != event_id]
                finding_code = (
                    "blocker_resume_runtime_binding_drift"
                    if resume_correlation_exact and not runtime_binding_exact
                    else "blocker_resume_correlation_required"
                )
                finding_message = (
                    "Blocker-cleared recovery must retain the exact runtime binding from its delivered intent."
                    if finding_code == "blocker_resume_runtime_binding_drift"
                    else "Blocker-cleared resume authority must exactly match one blocked packet, receipt, delivered intent, and retained lease."
                )
                findings.append(
                    _finding(
                        finding_code,
                        finding_message,
                        event_id=event_id,
                        packet_id=packet_id or None,
                        writer_scope=writer_scope or None,
                        expected_runtime_thread_id=retained_runtime_thread_id or None,
                        observed_runtime_thread_id=current_runtime_thread_id or None,
                    )
                )
                continue
            if _authority_is_canonical(prior_resume_authority):
                resume_history = [
                    item
                    for item in packet.get("resume_authority_history", [])
                    if isinstance(item, dict) and _authority_is_canonical(item)
                ]
                if not any(item.get("event_id") == prior_resume_authority.get("event_id") for item in resume_history):
                    resume_history.append(OrderedDict(prior_resume_authority))
                packet["resume_authority_history"] = resume_history
            packet["state"] = RECOVERY_READY_STATE
            packet["resume_authority"] = OrderedDict(
                [
                    ("event_id", event_id),
                    ("payload_digest", payload_digest),
                    ("reservation_id", reservation_id),
                    ("prior_blocking_receipt_event_id", prior_receipt_event_id),
                    ("prior_blocking_receipt_payload_digest", prior_receipt_digest),
                    ("current_delivered_turn_id", current_turn_id),
                ]
            )
            intent = matching_intents[0]
            superseded_authorities = [
                item
                for item in intent.get("superseded_delivery_authorities", [])
                if isinstance(item, dict) and _authority_is_canonical(item)
            ]
            if not any(item.get("event_id") == current_delivery_authority.get("event_id") for item in superseded_authorities):
                superseded_authorities.append(
                    OrderedDict(
                        [
                            ("event_id", current_delivery_authority.get("event_id")),
                            ("payload_digest", current_delivery_authority.get("payload_digest")),
                        ]
                    )
                )
            intent["superseded_delivery_authorities"] = superseded_authorities
            intent["event_id"] = event_id
            intent["payload_digest"] = payload_digest
            intent["status"] = "recovery-required"
            intent["turn_id"] = None
            intent["recovery_superseded_turn_id"] = current_turn_id
            matching_leases[0]["status"] = "recovery-required"
            continue
        if _terminal_cancellation(payload):
            packet = packets.get(packet_id)
            reservation_id = str(payload.get("reservation_id") or "")
            correlated_intents = [
                intent
                for intent in delivery_intents
                if str(intent.get("packet_id") or "") == packet_id
                and str(intent.get("writer_scope") or "") == writer_scope
            ]
            correlated_leases = [
                lease
                for lease in active_leases
                if str(lease.get("packet_id") or "") == packet_id
                and str(lease.get("writer_scope") or "") == writer_scope
            ]
            packet_state = str(packet.get("state") or "").upper() if packet else ""
            ready_cancellation = bool(
                packet
                and packet_state == "READY"
                and not correlated_intents
                and not correlated_leases
                and (not reservation_id or reservation_id == _deterministic_reservation_id(packet))
            )
            prepared_intents = [
                intent
                for intent in correlated_intents
                if str(intent.get("reservation_id") or "") == reservation_id
                and str(intent.get("status") or "").lower() == "prepared"
                and not intent.get("turn_id")
            ]
            prepared_leases = [
                lease
                for lease in correlated_leases
                if str(lease.get("reservation_id") or "") == reservation_id
                and str(lease.get("status") or "").lower() == "active"
            ]
            prepared_cancellation = bool(
                packet
                and packet_state == "ACTIVE"
                and reservation_id
                and len(prepared_intents) == 1
                and (
                    (str(packet.get("execution_class") or "") == "read_only" and not correlated_leases)
                    or len(prepared_leases) == 1
                )
            )
            recovery_attempted = bool(
                payload.get("event_class") == RECOVERY_ABSENCE_EVENT_CLASS
                or payload.get("delivery_recovery_evidence") is not None
                or payload.get("delivery_recovery_evidence_digest") is not None
            )
            recovery_absence_cancellation = False
            recovery_absence_violation: str | None = None
            recovery_intents = [
                intent
                for intent in correlated_intents
                if str(intent.get("reservation_id") or "") == reservation_id
                and str(intent.get("status") or "").lower() == "recovery-required"
                and intent.get("turn_id") is None
                and not intent.get("recovery_superseded_turn_id")
            ]
            recovery_leases = [
                lease
                for lease in correlated_leases
                if str(lease.get("reservation_id") or "") == reservation_id
                and str(lease.get("status") or "").lower() == "recovery-required"
            ]
            recovery_successor: dict[str, Any] | None = None
            if recovery_attempted:
                mutating_recovery = bool(
                    packet and str(packet.get("execution_class") or "") in MUTATING_EXECUTION_CLASSES
                )
                recovery_correlation_exact = bool(
                    envelope.get("kind") == RECOVERY_ABSENCE_ENVELOPE_KIND
                    and envelope.get("source_role_id") in RECOVERY_ABSENCE_AUTHORITIES
                    and packet
                    and packet_state == "ACTIVE"
                    and reservation_id
                    and isinstance(packet.get("dispatch_reservation"), dict)
                    and str(packet["dispatch_reservation"].get("reservation_id") or "") == reservation_id
                    and len(correlated_intents) == 1
                    and len(recovery_intents) == 1
                    and ((mutating_recovery and len(recovery_leases) == 1) or (not mutating_recovery and not correlated_leases))
                    and not payload.get("turn_id")
                )
                if not recovery_correlation_exact:
                    recovery_absence_violation = "recovery_absence_correlation_required"
                else:
                    recovery_absence_violation = _recovery_absence_evidence_violation(
                        payload=payload,
                        packet=packet,
                        intent=recovery_intents[0],
                        reservation_id=reservation_id,
                    )
                if recovery_absence_violation is None:
                    recovery_successor, recovery_absence_violation = _recovery_successor_violation(
                        payload=payload,
                        packet=packet,
                        packets=packets,
                        delivery_intents=delivery_intents,
                        active_leases=active_leases,
                    )
                recovery_absence_cancellation = recovery_absence_violation is None
            if recovery_attempted and not recovery_absence_cancellation:
                processed.pop(event_id, None)
                processed_items = [item for item in processed_items if item.get("event_id") != event_id]
                findings.append(
                    _finding(
                        recovery_absence_violation or "recovery_absence_correlation_required",
                        "Recovery absence may retire only one exact orphaned reservation with closed history proof and one admitted successor.",
                        event_id=event_id,
                        packet_id=packet_id or None,
                        writer_scope=writer_scope or None,
                        reservation_id=reservation_id or None,
                    )
                )
                continue
            if (
                (
                    (not recovery_absence_cancellation and envelope.get("source_role_id") != "atlas.main")
                    or (
                        recovery_absence_cancellation
                        and envelope.get("source_role_id") not in RECOVERY_ABSENCE_AUTHORITIES
                    )
                )
                or not packet_id
                or not writer_scope
                or not packet
                or str(packet.get("writer_scope") or "") != writer_scope
                or not (ready_cancellation or prepared_cancellation or recovery_absence_cancellation)
            ):
                processed.pop(event_id, None)
                processed_items = [item for item in processed_items if item.get("event_id") != event_id]
                findings.append(
                    _finding(
                        "terminal_cancellation_correlation_required",
                        "Cancellation must come from ATLAS MAIN and match one READY or prepared, never-delivered packet.",
                        event_id=event_id,
                        packet_id=packet_id or None,
                        writer_scope=writer_scope or None,
                    )
                )
                continue
            if recovery_absence_cancellation:
                recovery_intent = recovery_intents[0]
                delivery_intents.remove(recovery_intent)
                if recovery_leases:
                    lease = recovery_leases[0]
                    active_leases.remove(lease)
                    released.append(
                        OrderedDict(
                            [
                                ("reservation_id", lease.get("reservation_id")),
                                ("packet_id", packet_id),
                                ("writer_scope", writer_scope),
                                ("status", "recovery-absence-proven"),
                                ("receipt_event_id", event_id),
                                ("successor_packet_id", recovery_successor.get("packet_id") if recovery_successor else None),
                            ]
                        )
                    )
            elif prepared_cancellation:
                delivery_intents.remove(prepared_intents[0])
                if prepared_leases:
                    lease = prepared_leases[0]
                    active_leases.remove(lease)
                    released.append(
                        OrderedDict(
                            [
                                ("reservation_id", lease.get("reservation_id")),
                                ("packet_id", packet_id),
                                ("writer_scope", writer_scope),
                                ("status", "cancelled-before-delivery"),
                                ("receipt_event_id", event_id),
                            ]
                        )
                    )
            completed.add(packet_id)
            completion = OrderedDict(
                [
                    ("packet_id", packet_id),
                    ("writer_scope", writer_scope),
                    ("reservation_id", reservation_id or None),
                    ("turn_id", None),
                    ("receipt_event_id", event_id),
                    ("receipt_payload_digest", payload_digest),
                    ("terminal_disposition", str(payload.get("canonical_lifecycle_state") or "SUPERSEDED")),
                    ("superseded_by_packet_id", payload.get("superseded_by_packet_id")),
                ]
            )
            if recovery_absence_cancellation:
                recovery_intent = recovery_intents[0]
                completion.update(
                    OrderedDict(
                        [
                            ("runtime_thread_id", recovery_intent.get("runtime_thread_id")),
                            ("event_id", recovery_intent.get("event_id")),
                            ("payload_digest", recovery_intent.get("payload_digest")),
                            ("recovery_absence_evidence_digest", payload.get("delivery_recovery_evidence_digest")),
                            ("successor_event_id", payload.get("successor_event_id")),
                            ("successor_payload_digest", payload.get("successor_payload_digest")),
                        ]
                    )
                )
            completed_receipts.append(completion)
            packets.pop(packet_id, None)
            continue
        if payload.get("terminal") is True and not _terminal_success(payload):
            packet = packets.get(packet_id)
            reservation_id = str(payload.get("reservation_id") or "")
            turn_id = str(payload.get("turn_id") or "")
            matching_intents = [
                intent
                for intent in delivery_intents
                if str(intent.get("reservation_id") or "") == reservation_id
                and str(intent.get("packet_id") or "") == packet_id
                and str(intent.get("writer_scope") or "") == writer_scope
                and str(intent.get("turn_id") or "") == turn_id
                and str(intent.get("status") or "").lower() == "delivered"
            ]
            matching_blocked_leases = [
                lease
                for lease in active_leases
                if str(lease.get("reservation_id") or "") == reservation_id
                and str(lease.get("packet_id") or "") == packet_id
                and str(lease.get("writer_scope") or "") == writer_scope
                and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
            ]
            mutating_blocked_receipt = bool(
                packet
                and payload.get("blocking") is True
                and str(packet.get("writer_scope") or "") == writer_scope
                and str(packet.get("execution_class") or "") in MUTATING_EXECUTION_CLASSES
            )
            mutating_blocked_terminal = bool(
                mutating_blocked_receipt
                and str(packet.get("state") or "").upper() == "ACTIVE"
                and isinstance(packet.get("dispatch_reservation"), dict)
                and str(packet["dispatch_reservation"].get("reservation_id") or "") == reservation_id
                and len(matching_intents) == 1
                and len(matching_blocked_leases) == 1
            )
            if mutating_blocked_terminal:
                packet["state"] = "BLOCKED"
                packet["blocking_receipt"] = OrderedDict(
                    [
                        ("event_id", event_id),
                        ("payload_digest", payload_digest),
                        ("canonical_lifecycle_state", payload.get("canonical_lifecycle_state")),
                        ("turn_id", turn_id),
                    ]
                )
                continue
            if mutating_blocked_receipt:
                processed.pop(event_id, None)
                processed_items = [item for item in processed_items if item.get("event_id") != event_id]
                findings.append(
                    _finding(
                        "terminal_mutating_blocker_correlation_required",
                        "A mutating blocking receipt must match one active packet reservation, delivered intent, and lease.",
                        event_id=event_id,
                        packet_id=packet_id or None,
                        writer_scope=writer_scope or None,
                    )
                )
                continue
            read_only_terminal = bool(
                packet
                and str(packet.get("writer_scope") or "") == writer_scope
                and str(packet.get("execution_class") or "") == "read_only"
                and str(packet.get("state") or "").upper() == "ACTIVE"
                and isinstance(packet.get("dispatch_reservation"), dict)
                and not any(str(lease.get("reservation_id") or "") == reservation_id for lease in active_leases)
            )
            if not packet_id or not writer_scope or not reservation_id or not turn_id or len(matching_intents) != 1 or not read_only_terminal:
                processed.pop(event_id, None)
                processed_items = [item for item in processed_items if item.get("event_id") != event_id]
                findings.append(
                    _finding(
                        "terminal_read_only_correlation_required",
                        "Terminal read-only evidence must correlate exactly one delivered read-only packet.",
                        event_id=event_id,
                        packet_id=packet_id or None,
                        writer_scope=writer_scope or None,
                    )
                )
                continue
            completed.add(packet_id)
            completed_receipts.append(
                OrderedDict(
                    [
                        ("packet_id", packet_id),
                        ("writer_scope", writer_scope),
                        ("reservation_id", reservation_id),
                        ("turn_id", turn_id),
                        ("runtime_thread_id", matching_intents[0].get("runtime_thread_id")),
                        ("event_id", matching_intents[0].get("event_id")),
                        ("payload_digest", matching_intents[0].get("payload_digest")),
                        ("superseded_turn_ids", _string_list(matching_intents[0].get("superseded_turn_ids"))),
                        ("receipt_event_id", event_id),
                        ("receipt_payload_digest", payload_digest),
                        ("terminal_disposition", str(payload.get("canonical_lifecycle_state") or "TERMINAL")),
                    ]
                )
            )
            packets.pop(packet_id, None)
            delivery_intents.remove(matching_intents[0])
            continue
        if _terminal_success(payload):
            packet = packets.get(packet_id)
            matching = [
                lease
                for lease in active_leases
                if str(lease.get("packet_id") or "") == packet_id
                and str(lease.get("writer_scope") or "") == writer_scope
                and str(lease.get("reservation_id") or "") == str(payload.get("reservation_id") or "")
                and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
            ]
            reservation_id = str(payload.get("reservation_id") or "")
            turn_id = str(payload.get("turn_id") or "")
            correlated_intents = [
                intent
                for intent in delivery_intents
                if str(intent.get("reservation_id") or "") == reservation_id
                and str(intent.get("packet_id") or "") == packet_id
                and str(intent.get("writer_scope") or "") == writer_scope
            ]
            matching_intents = [
                intent
                for intent in correlated_intents
                if str(intent.get("turn_id") or "") == turn_id
                and str(intent.get("status") or "").lower() == "delivered"
            ]
            read_only_match = bool(
                packet
                and str(packet.get("writer_scope") or "") == writer_scope
                and str(packet.get("execution_class") or "") == "read_only"
                and str(packet.get("state") or "").upper() == "ACTIVE"
                and isinstance(packet.get("dispatch_reservation"), dict)
            )
            if (
                not packet_id
                or not writer_scope
                or not reservation_id
                or not turn_id
                or len(matching_intents) != 1
                or (len(matching) != 1 and not read_only_match)
            ):
                processed.pop(event_id, None)
                processed_items = [item for item in processed_items if item.get("event_id") != event_id]
                findings.append(
                    _finding(
                        "terminal_lease_correlation_required",
                        "Terminal receipt must correlate exactly one active packet and writer-scope lease.",
                        event_id=event_id,
                        packet_id=packet_id or None,
                        writer_scope=writer_scope or None,
                    )
                )
                continue
            if matching:
                lease = matching[0]
                active_leases.remove(lease)
                released.append(
                    OrderedDict(
                        [
                            ("reservation_id", lease.get("reservation_id")),
                            ("packet_id", packet_id),
                            ("writer_scope", writer_scope),
                            ("status", "released"),
                            ("receipt_event_id", event_id),
                        ]
                    )
                )
            completed.add(packet_id)
            completed_receipts.append(
                OrderedDict(
                    [
                        ("packet_id", packet_id),
                        ("writer_scope", writer_scope),
                        ("reservation_id", reservation_id),
                        ("turn_id", turn_id),
                        ("runtime_thread_id", matching_intents[0].get("runtime_thread_id")),
                        ("event_id", matching_intents[0].get("event_id")),
                        ("payload_digest", matching_intents[0].get("payload_digest")),
                        ("superseded_turn_ids", _string_list(matching_intents[0].get("superseded_turn_ids"))),
                        ("receipt_event_id", event_id),
                        ("receipt_payload_digest", payload_digest),
                    ]
                )
            )
            packets.pop(packet_id, None)
            delivery_intents.remove(matching_intents[0])
            continue

        state = str(payload.get("canonical_lifecycle_state") or payload.get("state") or "").upper()
        if state not in READY_STATES:
            continue
        role_id = str(payload.get("logical_role_id") or "")
        repository = _repository_identity(payload.get("repository"))
        execution_class = str(payload.get("execution_class") or "")
        if not packet_id or not role_id or not repository or not writer_scope or execution_class not in EXECUTION_CLASSES:
            findings.append(
                _finding(
                    "ready_packet_scope_required",
                    "READY authority must name packet, role, repository, writer scope, and execution class.",
                    event_id=event_id,
                )
            )
            continue
        standing_violation = _standing_local_source_preparation_violation(
            payload,
            source_role_id=envelope.get("source_role_id"),
            root=root,
        )
        if standing_violation:
            findings.append(
                _finding(
                    standing_violation,
                    "Standing local source-preparation authority failed its bounded packet contract.",
                    event_id=event_id,
                    packet_id=packet_id,
                )
            )
            continue
        binding = bindings.get(role_id)
        runtime_thread_id = binding.get("current_runtime_id") if binding else None
        runtime_status = str(binding.get("runtime_status") or "missing") if binding else "missing"
        archived = binding.get("archived") if binding else None
        if archived is True:
            runtime_status = "archived"
        if not isinstance(runtime_thread_id, str) or not runtime_thread_id or archived is True:
            findings.append(
                _finding(
                    "standing_binding_unavailable",
                    "READY packet has no usable unarchived standing runtime binding.",
                    event_id=event_id,
                    logical_role_id=role_id,
                )
            )
        candidate = OrderedDict(
            [
                ("packet_id", packet_id),
                ("packet", str(payload.get("objective") or payload.get("packet") or packet_id)),
                ("state", state),
                ("logical_role_id", role_id),
                ("repository", repository),
                ("writer_scope", writer_scope),
                ("execution_class", execution_class),
                ("dependencies", _string_list(payload.get("dependencies", []))),
                ("resource_claims", _resource_claims(payload.get("resource_claims"))),
                ("protected_surface_authorized", payload.get("protected_surface_authorized") is True),
                ("authority_class", payload.get("authority_class")),
                ("source_role_id", envelope.get("source_role_id")),
                ("source_preparation", payload.get("source_preparation")),
                ("runtime_thread_id", runtime_thread_id),
                ("runtime_status", runtime_status),
                ("authority", OrderedDict([("event_id", event_id), ("payload_digest", payload_digest)])),
                ("idempotency_key", envelope.get("idempotency_key")),
            ]
        )
        if isinstance(payload.get("replaces_packet_id"), str) and payload.get("replaces_packet_id"):
            candidate["replaces_packet_id"] = payload.get("replaces_packet_id")
        prior = packets.get(packet_id)
        if prior is not None and prior.get("authority") != candidate.get("authority"):
            findings.append(_finding("packet_identity_collision", "One packet_id carried multiple immutable authorities.", packet_id=packet_id))
            continue
        packets[packet_id] = candidate

    for packet in packets.values():
        binding = bindings.get(str(packet.get("logical_role_id") or ""))
        if binding:
            packet["runtime_thread_id"] = binding.get("current_runtime_id")
            packet["runtime_status"] = "archived" if binding.get("archived") is True else str(binding.get("runtime_status") or "missing")

    preserved_holds = [
        item
        for item in reconciled.get("scope_holds", [])
        if isinstance(item, dict) and item.get("derived_from_runtime_status") is not True
    ]
    leased_scopes = {
        str(lease.get("writer_scope"))
        for lease in active_leases
        if str(lease.get("status") or "").lower() in {"active", "recovery-required"}
    }
    derived_holds = [
        OrderedDict(
            [
                ("packet_id", packet.get("packet_id")),
                ("writer_scope", packet.get("writer_scope")),
                ("logical_role_id", packet.get("logical_role_id")),
                ("runtime_thread_id", packet.get("runtime_thread_id")),
                ("repository", packet.get("repository")),
                ("execution_class", packet.get("execution_class")),
                ("resource_claims", _resource_claims(packet.get("resource_claims"))),
                ("status", "active-without-correlated-lease"),
                ("derived_from_runtime_status", True),
            ]
        )
        for packet in packets.values()
        if str(packet.get("runtime_status") or "").lower() == "active"
        and str(packet.get("writer_scope") or "") not in leased_scopes
    ]

    reconciled["standing_packets"] = [packets[key] for key in sorted(packets) if key not in completed]
    reconciled["active_leases"] = active_leases
    reconciled["scope_holds"] = preserved_holds + derived_holds
    reconciled["delivery_intents"] = delivery_intents
    reconciled["released_leases"] = released
    reconciled["completed_packets"] = sorted(completed)
    reconciled["completed_receipts"] = completed_receipts
    reconciled["processed_events"] = processed_items
    reconciled["bridge_findings"] = findings
    reconciled["source_snapshot_digest"] = _canonical_payload_digest(
        {
            "bindings": [
                {
                    "role_id": role_id,
                    "runtime_thread_id": binding.get("current_runtime_id"),
                    "runtime_status": binding.get("runtime_status"),
                    "archived": binding.get("archived"),
                }
                for role_id, binding in sorted(bindings.items())
            ],
            "events": [
                {"event_id": item.get("event_id"), "payload_digest": item.get("payload_digest")}
                for item in processed_items
            ],
        }
    )
    return reconciled, findings


def _load_selector(root: Path) -> dict[str, Any]:
    selector_text = subprocess.check_output(
        [sys.executable, str(root / "ops" / "atlas" / "marker_knockout_selector.py"), "--format", "json"],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    payload = json.loads(selector_text)
    return payload if isinstance(payload, dict) else {}


def _scope_lock(program: dict[str, Any]) -> OrderedDict[str, Any]:
    max_writers_value = program.get("max_parallel_writers", 4)
    max_read_only_value = program.get("max_parallel_read_only", 2)
    return OrderedDict(
        [
            ("scope", "conflict-group-bounded"),
            ("allowed_markers", list(program.get("allowed_markers", []))),
            ("excluded_markers", list(program.get("excluded_markers", []))),
            ("forbidden_writer_scopes", list(program.get("forbidden_writer_scopes", []))),
            ("forbidden_owner_lanes", list(program.get("forbidden_owner_lanes", []))),
            ("max_parallel_writers", int(4 if max_writers_value is None else max_writers_value)),
            ("max_parallel_read_only", int(2 if max_read_only_value is None else max_read_only_value)),
            ("one_writer_per_conflict_group", True),
            ("continue_after_terminal_receipt", True),
        ]
    )


def _phase_from_packet(packet: str, mode: str, classification: str) -> str:
    lowered_packet = packet.lower()
    lowered_mode = mode.lower()
    if "worker cluster reconciliation" in lowered_packet or "worker-cluster reconciliation" in lowered_packet or "reconciliation" in lowered_packet:
        return PHASE_WORKER_RECONCILIATION
    if "worker packet" in lowered_packet or classification == planner.CLASS_IMPLEMENTATION_READY:
        return PHASE_WORKER_IMPLEMENTATION
    if "implementation-readiness" in lowered_packet or "implementation readiness" in lowered_mode:
        return PHASE_IMPLEMENTATION_READINESS
    if "prompt-pack" in lowered_packet or "worker handoff contract" in lowered_packet:
        return PHASE_PROMPT_PACK
    if "first-implementation admission" in lowered_packet or "first implementation admission" in lowered_mode:
        return PHASE_FIRST_IMPLEMENTATION_ADMISSION
    if "contract freeze" in lowered_packet:
        return PHASE_CONTRACT_FREEZE
    if "reselection" in lowered_packet or "selector" in lowered_packet:
        return PHASE_SELECTOR
    if classification == planner.CLASS_DOCS_ONLY:
        return PHASE_CONTRACT_FREEZE
    return PHASE_HOLD


def _file_overlap_risk(phase: str) -> str:
    if phase in {PHASE_WORKER_RECONCILIATION, PHASE_WORKER_IMPLEMENTATION}:
        return "medium"
    if phase in DOCS_ONLY_PHASES:
        return "low"
    return "high"


def _is_owner_lane(packet: str) -> bool:
    lowered = packet.lower()
    return any(term in lowered for term in OWNER_LANE_TERMS)


def _is_protected_packet(packet: str) -> bool:
    lowered = packet.lower()
    return any(term in lowered for term in PROTECTED_TERMS)


def _is_stale_packet(packet: str, classification: str) -> bool:
    lowered = packet.lower()
    return classification in {planner.CLASS_HELD, planner.CLASS_STALE, planner.CLASS_NO_ACTION} or lowered.startswith("no immediate") or "already completed" in lowered


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).replace("\\", "/") for item in value if isinstance(item, str) and item.strip()})


def _repository_identity(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip().replace("\\", "/")
    lowered = raw.casefold()
    if lowered.startswith("git@github.com:"):
        path = raw.split(":", 1)[1]
    elif "://" in raw:
        parsed = urlsplit(raw)
        if parsed.hostname is None or parsed.hostname.casefold() != "github.com" or parsed.query or parsed.fragment:
            return ""
        path = parsed.path
    elif lowered.startswith("github.com/"):
        path = raw[len("github.com/") :]
    else:
        path = raw
    path = path.strip("/")
    if path.casefold().endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return ""
    return "/".join(part.casefold() for part in parts)


def _external_writer_identity(value: str) -> str:
    raw = value.strip()
    if "://" in raw:
        parsed = urlsplit(raw)
        parts = parsed.path.strip("/").split("/")
        if parsed.hostname and parsed.hostname.casefold() == "github.com" and len(parts) >= 3:
            locator = parts[2].casefold()
            if locator == "pull":
                if len(parts) < 4 or not parts[3].isdigit():
                    return ""
                repository = _repository_identity("/".join(parts[:2]))
                if repository:
                    return f"github-pr:{repository}#{int(parts[3])}"
            if locator in {"pr", "prs"} or locator.startswith("pull"):
                return ""
        return raw.casefold()
    prefix, separator, remainder = raw.partition(":")
    normalized_prefix = prefix.casefold()
    if not separator or normalized_prefix not in {"github", "github-pr", "git-branch"}:
        return value.strip()
    repository_token, suffix_separator, suffix = remainder.partition(":")
    repository, pr_separator, pr_number = repository_token.partition("#")
    normalized_repository = _repository_identity(repository)
    if not normalized_repository:
        return ""
    if pr_separator:
        if not pr_number.isdigit():
            return ""
        return f"github-pr:{normalized_repository}#{int(pr_number)}"
    if normalized_prefix == "github-pr":
        return ""
    normalized = f"{normalized_prefix}:{normalized_repository}"
    if suffix_separator:
        normalized += f":{suffix}"
    return normalized


def _resource_claims(value: Any) -> OrderedDict[str, list[str]]:
    raw = value if isinstance(value, dict) else {}
    claims = OrderedDict(
        (kind, _string_list(raw.get(kind, [])))
        for kind in ("files", "worktrees", "ports", "browsers", "external_writers")
    )
    claims["external_writers"] = sorted(
        identity
        for identity in {_external_writer_identity(item) for item in claims["external_writers"]}
        if identity
    )
    return claims


def _safe_standing_local_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    lowered = normalized.casefold()
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[a-zA-Z]:", normalized)
        or any(token in normalized for token in "*?[")
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        return False
    return not any(
        lowered == prefix.rstrip("/") or lowered.startswith(prefix)
        for prefix in STANDING_LOCAL_PROTECTED_PATHS
    )


def _safe_standing_local_worktree_claim(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return bool(
        path == normalized == normalized.strip()
        and not normalized.startswith("/")
        and not re.match(r"^[a-zA-Z]:", normalized)
        and not any(token in normalized for token in "*?[")
        and all(part not in {"", ".", ".."} for part in normalized.split("/"))
    )


def _path_identity(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _standing_local_worktree_evidence_violation(
    *,
    root: Path | None,
    worktree_claim: str,
    repository: str,
    parent_commit: str,
) -> str | None:
    if root is None:
        return "standing_worktree_evidence_required"
    try:
        root_resolved = root.resolve(strict=True)
        claimed_path = root / Path(worktree_claim)
        claimed_absolute = Path(os.path.abspath(claimed_path))
        worktree = claimed_absolute.resolve(strict=True)
    except (OSError, RuntimeError):
        return "standing_worktree_evidence_unavailable"
    if _path_identity(worktree) != _path_identity(claimed_absolute):
        return "standing_worktree_indirection_forbidden"
    if _path_identity(worktree) == _path_identity(root_resolved) or not worktree.is_dir():
        return "standing_isolated_worktree_required"
    if not (worktree / ".git").is_file():
        return "standing_registered_worktree_required"

    top_level = _git_stdout(worktree, "rev-parse", "--show-toplevel")
    head = _git_stdout(worktree, "rev-parse", "HEAD")
    origin = _git_stdout(worktree, "remote", "get-url", "origin")
    registered = _git_stdout(worktree, "worktree", "list", "--porcelain")
    if None in {top_level, head, origin, registered}:
        return "standing_worktree_evidence_unavailable"
    try:
        top_level_path = Path(str(top_level)).resolve(strict=True)
    except (OSError, RuntimeError):
        return "standing_worktree_evidence_unavailable"
    if _path_identity(top_level_path) != _path_identity(worktree):
        return "standing_worktree_top_level_mismatch"

    registered_paths: set[str] = set()
    for line in str(registered).splitlines():
        if not line.startswith("worktree "):
            continue
        try:
            registered_path = Path(line.removeprefix("worktree ")).resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        registered_paths.add(_path_identity(registered_path))
    if _path_identity(worktree) not in registered_paths:
        return "standing_registered_worktree_required"
    if _repository_identity(origin) != _repository_identity(repository):
        return "standing_worktree_repository_mismatch"
    if head != parent_commit:
        return "standing_worktree_parent_mismatch"
    return None


def _standing_local_source_preparation_violation(
    payload: dict[str, Any],
    *,
    source_role_id: Any,
    root: Path | None = None,
) -> str | None:
    authority_class = payload.get("authority_class")
    if authority_class is None:
        return None
    if authority_class != STANDING_LOCAL_SOURCE_PREPARATION:
        return "standing_authority_class_unknown"
    if source_role_id not in STANDING_LOCAL_SOURCE_ROLES:
        return "standing_source_role_forbidden"
    if not str(payload.get("logical_role_id") or "").startswith("owner."):
        return "standing_owner_role_required"
    if payload.get("execution_class") != "repo_worktree":
        return "standing_repo_worktree_required"
    if payload.get("protected_surface_authorized") is True:
        return "standing_protected_surface_forbidden"

    preparation = payload.get("source_preparation")
    if not isinstance(preparation, dict):
        return "standing_source_preparation_required"
    if preparation.get("mode") != "LOCAL_ONLY_UNSTAGED":
        return "standing_local_unstaged_mode_required"
    if preparation.get("publication") != "HELD":
        return "standing_publication_hold_required"
    if not isinstance(preparation.get("parent_commit"), str) or not COMMIT_SHA_PATTERN.fullmatch(
        preparation["parent_commit"]
    ):
        return "standing_parent_commit_required"

    raw_path_allowlist = preparation.get("path_allowlist")
    if not isinstance(raw_path_allowlist, list) or not raw_path_allowlist:
        return "standing_path_allowlist_required"
    if len(raw_path_allowlist) > MAX_STANDING_LOCAL_SOURCE_PATHS:
        return "standing_path_allowlist_required"
    if not all(isinstance(path, str) and path == path.strip().replace("\\", "/") for path in raw_path_allowlist):
        return "standing_path_allowlist_not_canonical"
    path_allowlist = _string_list(raw_path_allowlist)
    if len(path_allowlist) != len(raw_path_allowlist):
        return "standing_path_allowlist_not_canonical"
    if not all(_safe_standing_local_path(path) for path in path_allowlist):
        return "standing_path_allowlist_unsafe"

    raw_claims = payload.get("resource_claims")
    claim_kinds = {"files", "worktrees", "ports", "browsers", "external_writers"}
    if not isinstance(raw_claims, dict) or set(raw_claims) - claim_kinds:
        return "standing_resource_claims_invalid"
    if any(not isinstance(raw_claims.get(kind, []), list) for kind in claim_kinds):
        return "standing_resource_claims_invalid"
    claims = _resource_claims(raw_claims)
    if claims["files"] != path_allowlist:
        return "standing_file_claims_must_match_allowlist"
    if (
        len(claims["worktrees"]) != 1
        or raw_claims.get("worktrees") != claims["worktrees"]
        or not _safe_standing_local_worktree_claim(claims["worktrees"][0])
    ):
        return "standing_isolated_worktree_required"
    if any(_string_list(raw_claims.get(kind, [])) for kind in ("ports", "browsers", "external_writers")):
        return "standing_external_resource_claim_forbidden"
    if violation := _standing_local_worktree_evidence_violation(
        root=root,
        worktree_claim=claims["worktrees"][0],
        repository=str(payload.get("repository") or ""),
        parent_commit=preparation["parent_commit"],
    ):
        return violation
    return None


def _authority_is_canonical(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and isinstance(value.get("event_id"), str)
        and EVENT_ID_PATTERN.fullmatch(value["event_id"])
        and isinstance(value.get("payload_digest"), str)
        and PAYLOAD_DIGEST_PATTERN.fullmatch(value["payload_digest"])
    )


def _candidate_identity(
    *,
    packet: str,
    item: dict[str, Any],
    default_root: bool,
) -> tuple[str | None, str | None, str | None, str | None]:
    execution_class = str(item.get("execution_class") or ("canonical_workspace" if default_root else ""))
    repository = _repository_identity(item.get("repository") or ("fawxzzy/ATLAS" if default_root else "")) or None
    writer_scope = str(item.get("writer_scope") or ("atlas.root" if default_root else "")) or None
    logical_role_id = str(item.get("logical_role_id") or ("atlas.main" if default_root else "")) or None
    if execution_class == "read_only":
        writer_scope = writer_scope or "read-only"
    return execution_class or None, repository, writer_scope, logical_role_id


def _phase_priority_rank(program: dict[str, Any], phase: str) -> int:
    priorities = list(program.get("phase_priority", []))
    try:
        return priorities.index(phase)
    except ValueError:
        return len(priorities) + 1


def _slugify_marker(marker: str) -> str:
    return "-".join(token for token in "".join(ch if ch.isalnum() else " " for ch in marker).split()).upper()


def _reselection_receipt(marker: str) -> str:
    return f"docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-{_slugify_marker(marker)}-2026-07-10.md"


def _candidate_from_planner_item(
    *,
    item: dict[str, Any],
    active_marker: str | None,
    active_lane_is_held: bool,
    program: dict[str, Any],
    recent_docs_only_streak: int,
) -> OrderedDict[str, Any]:
    marker = str(item.get("marker") or "")
    packet = str(item.get("packet") or "")
    classification = str(item.get("classification") or "")
    mode = str(item.get("mode") or "")
    phase = _phase_from_packet(packet, mode, classification)
    score = int(item.get("score") or 0)
    allowed_markers = set(program.get("allowed_markers", []))
    excluded_markers = set(program.get("excluded_markers", []))
    max_docs_only_streak = int(program.get("max_docs_only_streak", 2) or 2)
    requires_reselection = bool(active_lane_is_held and active_marker and marker and marker != active_marker)
    blocked_reason = None
    stale_reason = None
    requires_external_input = classification in {planner.CLASS_EXTERNAL_PROOF, planner.CLASS_PROOF_GATED, planner.CLASS_OWNER_BLOCKED}
    owner_metadata_required = _is_owner_lane(packet) and not all(
        isinstance(item.get(field), str) and str(item[field]).strip()
        for field in ("repository", "writer_scope", "logical_role_id", "execution_class")
    )
    execution_class, repository, writer_scope, logical_role_id = _candidate_identity(
        packet=packet,
        item=item,
        default_root=not _is_owner_lane(packet),
    )
    if marker and allowed_markers and marker not in allowed_markers:
        blocked_reason = "marker_not_allowed_by_program"
    elif marker in excluded_markers:
        blocked_reason = "marker_excluded_by_program"
    elif owner_metadata_required:
        blocked_reason = "owner_lane_metadata_required"
    elif execution_class not in EXECUTION_CLASSES:
        blocked_reason = "invalid_execution_class"
    elif writer_scope in set(program.get("forbidden_writer_scopes", [])):
        blocked_reason = "writer_scope_forbidden"
    elif execution_class == "external_mutation" and not _resource_claims(item.get("resource_claims")).get("external_writers"):
        blocked_reason = "external_writer_claim_required"
    elif execution_class != "read_only" and _is_protected_packet(packet):
        blocked_reason = "protected_or_platform_mutation_forbidden"
    elif requires_external_input:
        blocked_reason = "requires_external_input"
    elif recent_docs_only_streak >= max_docs_only_streak and phase in DOCS_ONLY_PHASES:
        blocked_reason = "docs_only_streak_limit"
    elif _is_stale_packet(packet, classification):
        stale_reason = "held_or_stale_packet"
    safe = classification in SAFE_CLASSIFICATIONS and blocked_reason is None and stale_reason is None
    proof_delta = "implementation_backed" if phase in {PHASE_WORKER_RECONCILIATION, PHASE_WORKER_IMPLEMENTATION} else "docs_or_contract"
    return OrderedDict(
        [
            ("marker", marker),
            ("lane", marker),
            ("packet_id", str(item.get("packet_id") or packet) or None),
            ("packet", packet or None),
            ("phase", phase),
            ("score", score),
            ("source", "planner"),
            ("proof_delta", proof_delta),
            ("blocked_reason", blocked_reason),
            ("stale_reason", stale_reason),
            ("file_overlap_risk", _file_overlap_risk(phase)),
            ("requires_external_input", requires_external_input),
            ("requires_reselection", requires_reselection and bool(program.get("allow_reselection"))),
            ("safe", safe),
            ("classification", classification),
            ("logical_role_id", logical_role_id),
            ("repository", repository),
            ("writer_scope", writer_scope),
            ("execution_class", execution_class),
            ("dependencies", _string_list(item.get("dependencies", []))),
            ("resource_claims", _resource_claims(item.get("resource_claims"))),
            ("cross_marker_signal_applied", bool(item.get("cross_marker_signal_applied"))),
        ]
    )


def _candidate_from_standing_packet(*, item: Any, program: dict[str, Any], root: Path) -> OrderedDict[str, Any]:
    raw = item if isinstance(item, dict) else {}
    packet = str(raw.get("packet") or raw.get("packet_id") or "")
    packet_id = str(raw.get("packet_id") or packet)
    state = str(raw.get("state") or "").upper()
    execution_class, repository, writer_scope, logical_role_id = _candidate_identity(
        packet=packet,
        item=raw,
        default_root=False,
    )
    runtime_status = str(raw.get("runtime_status") or "missing").lower()
    runtime_thread_id = raw.get("runtime_thread_id")
    dispatch_reservation = raw.get("dispatch_reservation") if isinstance(raw.get("dispatch_reservation"), dict) else {}
    resume_authority = raw.get("resume_authority") if isinstance(raw.get("resume_authority"), dict) else {}
    recovery_resume = bool(
        state == RECOVERY_READY_STATE
        and str(dispatch_reservation.get("reservation_id") or "")
        and str(resume_authority.get("reservation_id") or "") == str(dispatch_reservation.get("reservation_id") or "")
        and str(resume_authority.get("event_id") or "")
        and str(resume_authority.get("payload_digest") or "")
        and str(resume_authority.get("current_delivered_turn_id") or "")
    )
    blocked_reason = None
    if not packet_id or not packet:
        blocked_reason = "standing_packet_identity_required"
    elif state not in READY_STATES and not recovery_resume:
        blocked_reason = "resume_authority_correlation_required" if state == RECOVERY_READY_STATE else "standing_packet_not_ready"
    elif execution_class not in EXECUTION_CLASSES:
        blocked_reason = "invalid_execution_class"
    elif not repository or not logical_role_id or not writer_scope:
        blocked_reason = "standing_packet_scope_required"
    elif not isinstance(runtime_thread_id, str) or not runtime_thread_id:
        blocked_reason = "standing_binding_required"
    elif runtime_status not in RESUMABLE_RUNTIME_STATES:
        blocked_reason = "standing_role_active" if runtime_status == "active" else "standing_binding_not_resumable"
    elif writer_scope in set(program.get("forbidden_writer_scopes", [])):
        blocked_reason = "writer_scope_forbidden"
    elif not _authority_is_canonical(raw.get("authority")):
        blocked_reason = "canonical_authority_required"
    elif standing_violation := _standing_local_source_preparation_violation(
        raw,
        source_role_id=raw.get("source_role_id"),
        root=root,
    ):
        blocked_reason = standing_violation
    elif execution_class == "external_mutation" and not _resource_claims(raw.get("resource_claims")).get("external_writers"):
        blocked_reason = "external_writer_claim_required"
    elif (
        execution_class != "read_only"
        and _is_protected_packet(packet)
        and raw.get("protected_surface_authorized") is not True
    ):
        blocked_reason = "protected_or_platform_mutation_forbidden"
    phase = str(raw.get("phase") or PHASE_WORKER_IMPLEMENTATION)
    return OrderedDict(
        [
            ("marker", str(raw.get("marker") or raw.get("lane") or logical_role_id or "")),
            ("lane", str(raw.get("lane") or raw.get("marker") or logical_role_id or "")),
            ("packet_id", packet_id or None),
            ("packet", packet or None),
            ("phase", phase),
            ("score", int(raw.get("score") or 100)),
            ("source", "standing_task"),
            ("proof_delta", str(raw.get("proof_delta") or "implementation_backed")),
            ("blocked_reason", blocked_reason),
            ("stale_reason", None),
            ("file_overlap_risk", str(raw.get("file_overlap_risk") or _file_overlap_risk(phase))),
            ("requires_external_input", False),
            ("requires_reselection", False),
            ("safe", blocked_reason is None),
            ("classification", str(raw.get("classification") or planner.CLASS_IMPLEMENTATION_READY)),
            ("logical_role_id", logical_role_id),
            ("runtime_thread_id", runtime_thread_id),
            ("runtime_status", runtime_status),
            ("repository", repository),
            ("writer_scope", writer_scope),
            ("execution_class", execution_class),
            ("dependencies", _string_list(raw.get("dependencies", []))),
            ("resource_claims", _resource_claims(raw.get("resource_claims"))),
            ("protected_surface_authorized", raw.get("protected_surface_authorized") is True),
            ("authority_class", raw.get("authority_class")),
            ("source_role_id", raw.get("source_role_id")),
            ("source_preparation", raw.get("source_preparation")),
            ("cross_marker_signal_applied", False),
            ("authority", raw.get("authority")),
            ("recovery_resume", recovery_resume),
            ("recovery_reservation_id", dispatch_reservation.get("reservation_id") if recovery_resume else None),
            ("recovery_current_delivered_turn_id", resume_authority.get("current_delivered_turn_id") if recovery_resume else None),
            ("recovery_event_id", resume_authority.get("event_id") if recovery_resume else None),
            ("recovery_payload_digest", resume_authority.get("payload_digest") if recovery_resume else None),
        ]
    )


def _selector_exact_packet(selector: dict[str, Any]) -> tuple[str | None, str | None]:
    action = str(selector.get("operator_action") or "")
    current_packet = str(selector.get("selected_current_packet") or "")
    if action not in {"hold_current_lane", "no_immediate_root_packet", "held", "hold"} and current_packet and not current_packet.lower().startswith("no immediate"):
        return str(selector.get("selected_marker") or ""), current_packet
    return None, None


def _sort_candidates(program: dict[str, Any], candidates: list[OrderedDict[str, Any]]) -> list[OrderedDict[str, Any]]:
    def key(item: OrderedDict[str, Any]) -> tuple[int, int, str]:
        return (
            _phase_priority_rank(program, str(item.get("phase") or "")),
            -int(item.get("score") or 0),
            str(item.get("packet_id") or item.get("packet") or ""),
        )

    return sorted(candidates, key=key)


def _dedupe_candidates(
    candidates: list[OrderedDict[str, Any]],
) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    source_rank = {"selector_current_packet": 0, "standing_task": 1, "planner": 2}
    ordered = sorted(
        candidates,
        key=lambda item: (source_rank.get(str(item.get("source")), 9), str(item.get("packet_id") or "")),
    )
    unique: list[OrderedDict[str, Any]] = []
    duplicates: list[OrderedDict[str, Any]] = []
    seen: set[str] = set()
    for candidate in ordered:
        packet_id = str(candidate.get("packet_id") or "")
        if packet_id in seen:
            duplicate = OrderedDict(candidate)
            duplicate["blocked_reason"] = "duplicate_packet_id"
            duplicates.append(duplicate)
            continue
        seen.add(packet_id)
        unique.append(candidate)
    return unique, duplicates


def _patterns_overlap(left: str, right: str) -> bool:
    if left == right or fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    left_prefix = left.split("**", 1)[0]
    right_prefix = right.split("**", 1)[0]
    return bool(left_prefix and right_prefix and (left.startswith(right_prefix) or right.startswith(left_prefix)))


def _candidate_conflicts(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    conflicts: list[str] = []
    left_mutates = left.get("execution_class") in MUTATING_EXECUTION_CLASSES
    right_mutates = right.get("execution_class") in MUTATING_EXECUTION_CLASSES
    if left_mutates and right_mutates and left.get("writer_scope") == right.get("writer_scope"):
        conflicts.append("writer_scope")
    if left.get("execution_class") == "canonical_workspace" and right.get("execution_class") == "canonical_workspace":
        conflicts.append("canonical_root")
    left_claims = left.get("resource_claims", {})
    right_claims = right.get("resource_claims", {})
    for kind in ("worktrees", "ports", "browsers", "external_writers"):
        if set(left_claims.get(kind, [])).intersection(right_claims.get(kind, [])):
            conflicts.append(kind)
    left_repository = _repository_identity(left.get("repository"))
    right_repository = _repository_identity(right.get("repository"))
    same_repository = bool(left_repository) and left_repository == right_repository
    files_overlap = any(
        _patterns_overlap(a, b)
        for a in left_claims.get("files", [])
        for b in right_claims.get("files", [])
    )
    if same_repository and files_overlap:
        conflicts.append("files")
    left_mutates_repository = left.get("execution_class") in REPOSITORY_MUTATING_EXECUTION_CLASSES
    right_mutates_repository = right.get("execution_class") in REPOSITORY_MUTATING_EXECUTION_CLASSES
    if left_mutates_repository and right_mutates_repository and same_repository:
        if "canonical_workspace" in {left.get("execution_class"), right.get("execution_class")}:
            conflicts.append("canonical_root")
        else:
            complete_isolation_claims = all(
                claims.get(kind)
                for claims in (left_claims, right_claims)
                for kind in ("worktrees", "files")
            )
            worktrees_overlap = any(
                _patterns_overlap(a, b)
                for a in left_claims.get("worktrees", [])
                for b in right_claims.get("worktrees", [])
            )
            if not complete_isolation_claims:
                conflicts.append("repository")
            elif worktrees_overlap:
                conflicts.append("worktrees")
    return sorted(set(conflicts))


def _candidate_conflicts_with_root_validation(
    candidate: dict[str, Any],
    validation_candidate: dict[str, Any],
    *,
    validation_root: Path,
) -> list[str]:
    conflicts = _candidate_conflicts(candidate, validation_candidate)
    # Validation cleanup is a virtual root hold, not a writer. Read-only work
    # may inspect the held checkout; real active leases are enforced later.
    if candidate.get("execution_class") == "read_only":
        return []
    if not conflicts or candidate.get("execution_class") != "repo_worktree":
        return conflicts
    if _repository_identity(candidate.get("repository")) != _repository_identity(validation_candidate.get("repository")):
        return conflicts

    claims = _resource_claims(candidate.get("resource_claims"))
    files = claims["files"]
    worktrees = claims["worktrees"]
    if not files or not worktrees or any(path in {"*", "**"} for path in files):
        return conflicts
    if any(any(token in path for token in "*?[") for path in worktrees):
        return conflicts

    validation_worktree = str(validation_root.resolve()).replace("\\", "/").casefold().rstrip("/")
    claimed_worktrees = {
        str(Path(path).resolve()).replace("\\", "/").casefold().rstrip("/")
        for path in worktrees
    }
    if validation_worktree in claimed_worktrees:
        return conflicts

    # Root validation owns the checkout being validated, not every isolated
    # checkout of the same repository. General wave selection still enforces
    # same-repository file/worktree isolation between actual source writers.
    return []


def _active_writer_scopes(program: dict[str, Any]) -> set[str]:
    leases = program.get("active_leases", [])
    if not isinstance(leases, list):
        return set()
    leased = {
        str(lease.get("writer_scope"))
        for lease in leases
        if isinstance(lease, dict)
        and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
        and isinstance(lease.get("writer_scope"), str)
        and lease["writer_scope"]
    }
    holds = program.get("scope_holds", [])
    if isinstance(holds, list):
        leased.update(
            str(hold.get("writer_scope"))
            for hold in holds
            if isinstance(hold, dict) and isinstance(hold.get("writer_scope"), str) and hold["writer_scope"]
        )
    return leased


def _exact_recovery_reservation(
    candidate: dict[str, Any],
    *,
    active_leases: list[dict[str, Any]],
    delivery_intents: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return the sole retained lease and intent a resume may reuse."""

    if candidate.get("recovery_resume") is not True:
        return None, None
    reservation_id = str(candidate.get("recovery_reservation_id") or "")
    packet_id = str(candidate.get("packet_id") or "")
    writer_scope = str(candidate.get("writer_scope") or "")
    superseded_turn_id = str(candidate.get("recovery_current_delivered_turn_id") or "")
    recovery_event_id = str(candidate.get("recovery_event_id") or "")
    recovery_payload_digest = str(candidate.get("recovery_payload_digest") or "")
    matching_leases = [
        lease
        for lease in active_leases
        if str(lease.get("reservation_id") or "") == reservation_id
        and str(lease.get("packet_id") or "") == packet_id
        and str(lease.get("writer_scope") or "") == writer_scope
        and str(lease.get("status") or "").lower() == "recovery-required"
    ]
    matching_intents = [
        intent
        for intent in delivery_intents
        if str(intent.get("reservation_id") or "") == reservation_id
        and str(intent.get("packet_id") or "") == packet_id
        and str(intent.get("writer_scope") or "") == writer_scope
        and str(intent.get("status") or "").lower() == "recovery-required"
        and intent.get("turn_id") in {None, ""}
        and str(intent.get("recovery_superseded_turn_id") or "") == superseded_turn_id
        and str(intent.get("event_id") or "") == recovery_event_id
        and str(intent.get("payload_digest") or "") == recovery_payload_digest
    ]
    if len(matching_leases) != 1 or len(matching_intents) != 1:
        return None, None
    return matching_leases[0], matching_intents[0]


def _active_lease_candidate(
    lease: dict[str, Any],
) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("packet_id", lease.get("packet_id")),
            ("repository", lease.get("repository")),
            ("writer_scope", lease.get("writer_scope")),
            ("execution_class", lease.get("execution_class")),
            ("resource_claims", _resource_claims(lease.get("resource_claims"))),
        ]
    )


def _active_lease_identity_complete(lease: dict[str, Any]) -> bool:
    if not _repository_identity(lease.get("repository")) or lease.get("execution_class") not in MUTATING_EXECUTION_CLASSES:
        return False
    if not isinstance(lease.get("resource_claims"), dict):
        return False
    if lease.get("execution_class") == "external_mutation":
        return bool(_resource_claims(lease.get("resource_claims"))["external_writers"])
    return True


def _active_runtime_hold_candidate(hold: dict[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("packet_id", hold.get("packet_id")),
            ("repository", hold.get("repository")),
            ("writer_scope", hold.get("writer_scope")),
            ("execution_class", hold.get("execution_class")),
            ("resource_claims", _resource_claims(hold.get("resource_claims"))),
        ]
    )


def _active_runtime_hold_identity_complete(hold: dict[str, Any]) -> bool:
    if not (
        hold.get("derived_from_runtime_status") is True
        and hold.get("status") == "active-without-correlated-lease"
        and _repository_identity(hold.get("repository"))
        and hold.get("execution_class") in EXECUTION_CLASSES
        and isinstance(hold.get("resource_claims"), dict)
    ):
        return False
    if hold.get("execution_class") == "external_mutation":
        return bool(_resource_claims(hold.get("resource_claims"))["external_writers"])
    return True


def _select_execution_wave(
    *,
    program: dict[str, Any],
    candidates: list[OrderedDict[str, Any]],
) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    selected: list[OrderedDict[str, Any]] = []
    blocked: list[OrderedDict[str, Any]] = []
    deferred: list[OrderedDict[str, Any]] = []
    active_scopes = _active_writer_scopes(program)
    held_scopes = {
        str(hold.get("writer_scope"))
        for hold in program.get("scope_holds", [])
        if isinstance(hold, dict) and isinstance(hold.get("writer_scope"), str) and hold["writer_scope"]
    }
    completed = set(_string_list(program.get("completed_packets", [])))
    max_writers_value = program.get("max_parallel_writers", 4)
    max_writers = max(0, int(4 if max_writers_value is None else max_writers_value))
    max_read_only_value = program.get("max_parallel_read_only", 2)
    max_read_only = max(0, int(2 if max_read_only_value is None else max_read_only_value))
    active_leases = [item for item in program.get("active_leases", []) if isinstance(item, dict)]
    delivery_intents = [item for item in program.get("delivery_intents", []) if isinstance(item, dict)]
    active_lease_candidates = [
        (lease, _active_lease_candidate(lease))
        for lease in active_leases
        if str(lease.get("status") or "").lower() in {"active", "recovery-required"}
    ]
    incomplete_active_leases = [
        lease
        for lease in active_leases
        if str(lease.get("status") or "").lower() in {"active", "recovery-required"}
        and not _active_lease_identity_complete(lease)
    ]
    active_runtime_holds = [
        hold
        for hold in program.get("scope_holds", [])
        if isinstance(hold, dict) and hold.get("derived_from_runtime_status") is True
    ]
    active_runtime_hold_candidates = [
        (hold, _active_runtime_hold_candidate(hold))
        for hold in active_runtime_holds
        if _active_runtime_hold_identity_complete(hold)
    ]
    incomplete_active_runtime_holds = [
        hold for hold in active_runtime_holds if not _active_runtime_hold_identity_complete(hold)
    ]
    writer_count = sum(
        1
        for lease in active_leases
        if str(lease.get("status") or "").lower() in {"active", "recovery-required"}
    )
    read_only_count = sum(
        1
        for packet in program.get("standing_packets", [])
        if isinstance(packet, dict)
        and str(packet.get("execution_class") or "") == "read_only"
        and str(packet.get("state") or "").upper() == "ACTIVE"
        and isinstance(packet.get("dispatch_reservation"), dict)
    )
    for candidate in candidates:
        candidate = OrderedDict(candidate)
        dependencies = set(candidate.get("dependencies", []))
        missing_dependencies = sorted(dependencies - completed)
        recovery_lease, recovery_intent = _exact_recovery_reservation(
            candidate,
            active_leases=active_leases,
            delivery_intents=delivery_intents,
        )
        recovery_resume = recovery_lease is not None and recovery_intent is not None
        if candidate.get("writer_scope") in held_scopes:
            candidate["blocked_reason"] = (
                "recovery_writer_scope_hold"
                if candidate.get("recovery_resume") is True
                else "writer_scope_leased"
            )
            blocked.append(candidate)
            continue
        if candidate.get("writer_scope") in active_scopes and not recovery_resume:
            candidate["blocked_reason"] = (
                "recovery_reservation_correlation_required"
                if candidate.get("recovery_resume") is True
                else "writer_scope_leased"
            )
            blocked.append(candidate)
            continue
        if recovery_resume and any(
            lease is not recovery_lease
            and str(lease.get("writer_scope") or "") == str(candidate.get("writer_scope") or "")
            and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
            for lease in active_leases
        ):
            candidate["blocked_reason"] = "recovery_peer_writer_scope_conflict"
            blocked.append(candidate)
            continue
        if missing_dependencies:
            candidate["blocked_reason"] = "dependencies_not_complete"
            candidate["missing_dependencies"] = missing_dependencies
            blocked.append(candidate)
            continue
        if candidate.get("execution_class") in MUTATING_EXECUTION_CLASSES and incomplete_active_leases:
            candidate["blocked_reason"] = "active_lease_identity_incomplete"
            candidate["conflicts_with"] = [
                OrderedDict(
                    [
                        ("packet_id", lease.get("packet_id")),
                        ("reservation_id", lease.get("reservation_id")),
                        ("resource_kinds", ["unknown_mutating_scope"]),
                    ]
                )
                for lease in incomplete_active_leases
            ]
            blocked.append(candidate)
            continue
        if candidate.get("execution_class") in MUTATING_EXECUTION_CLASSES and incomplete_active_runtime_holds:
            candidate["blocked_reason"] = "active_runtime_hold_identity_incomplete"
            candidate["conflicts_with"] = [
                OrderedDict(
                    [
                        ("packet_id", hold.get("packet_id")),
                        ("writer_scope", hold.get("writer_scope")),
                        ("resource_kinds", ["unknown_active_runtime_scope"]),
                    ]
                )
                for hold in incomplete_active_runtime_holds
            ]
            blocked.append(candidate)
            continue
        lease_conflicts = [
            (lease, _candidate_conflicts(candidate, leased_candidate))
            for lease, leased_candidate in active_lease_candidates
            if lease is not recovery_lease
        ]
        lease_conflicts = [(lease, kinds) for lease, kinds in lease_conflicts if kinds]
        if lease_conflicts:
            candidate["blocked_reason"] = "active_lease_resource_conflict"
            candidate["conflicts_with"] = [
                OrderedDict(
                    [
                        ("packet_id", lease.get("packet_id")),
                        ("reservation_id", lease.get("reservation_id")),
                        ("resource_kinds", kinds),
                    ]
                )
                for lease, kinds in lease_conflicts
            ]
            blocked.append(candidate)
            continue
        runtime_hold_conflicts = [
            (hold, _candidate_conflicts(candidate, held_candidate))
            for hold, held_candidate in active_runtime_hold_candidates
        ]
        runtime_hold_conflicts = [(hold, kinds) for hold, kinds in runtime_hold_conflicts if kinds]
        if runtime_hold_conflicts:
            candidate["blocked_reason"] = "active_runtime_resource_conflict"
            candidate["conflicts_with"] = [
                OrderedDict(
                    [
                        ("packet_id", hold.get("packet_id")),
                        ("writer_scope", hold.get("writer_scope")),
                        ("resource_kinds", kinds),
                    ]
                )
                for hold, kinds in runtime_hold_conflicts
            ]
            blocked.append(candidate)
            continue
        conflicts = [
            (other, _candidate_conflicts(candidate, other))
            for other in selected
        ]
        conflicts = [(other, kinds) for other, kinds in conflicts if kinds]
        if conflicts:
            candidate["deferred_reason"] = "resource_conflict"
            candidate["conflicts_with"] = [
                OrderedDict(
                    [
                        ("packet_id", other.get("packet_id")),
                        ("resource_kinds", kinds),
                    ]
                )
                for other, kinds in conflicts
            ]
            deferred.append(candidate)
            continue
        if candidate.get("execution_class") == "read_only":
            if read_only_count >= max_read_only:
                candidate["deferred_reason"] = "read_only_wave_limit"
                deferred.append(candidate)
                continue
            read_only_count += 1
        else:
            if recovery_resume:
                selected.append(candidate)
                continue
            if writer_count >= max_writers:
                candidate["deferred_reason"] = "writer_wave_limit"
                deferred.append(candidate)
                continue
            writer_count += 1
        selected.append(candidate)
    return selected, blocked, deferred


def _validation_state(preflight_report: dict[str, Any]) -> OrderedDict[str, Any]:
    validation = preflight_report.get("validation", {}) if isinstance(preflight_report.get("validation"), dict) else {}
    projection = preflight_report.get("projection_freshness", {}) if isinstance(preflight_report.get("projection_freshness"), dict) else {}
    residue = preflight_report.get("local_residue", {}) if isinstance(preflight_report.get("local_residue"), dict) else {}
    return OrderedDict(
        [
            ("critical", int(validation.get("critical", 0) or 0)),
            ("error", int(validation.get("error", 0) or 0)),
            ("warning", int(validation.get("warning", 0) or 0)),
            ("info", int(validation.get("info", 0) or 0)),
            ("projection_status", projection.get("status")),
            ("inventory_matches_live_working_set", projection.get("inventory_matches_live_working_set")),
            ("root_dirty_path_count", len(residue.get("root_dirty_paths", []) if isinstance(residue.get("root_dirty_paths"), list) else [])),
        ]
    )


def render_prompt(report: dict[str, Any]) -> str:
    status = str(report.get("status") or "")
    if status == STATUS_HOLD:
        return "\n".join(
            [
                "ATLAS ROOT HELD - NO SAFE AUTOCOMPLETE PACKET",
                "",
                "Do not invent fallback work.",
                f"Stop reason: {report.get('stop_reason')}",
                "Do not invent owner work or widen deploy, secret, provider, or production authority.",
            ]
        ) + "\n"
    if status == STATUS_VALIDATION_CLEANUP:
        return "\n".join(
            [
                "ATLAS ROOT VALIDATION CLEANUP PACKET",
                "",
                "Execute only root cleanup and validation refresh work.",
                f"Reason: {report.get('stop_reason')}",
                f"Branch: `{report.get('git_state', {}).get('branch')}`",
                f"Head: `{report.get('git_state', {}).get('head')}`",
                "",
                "Required preflight:",
                *[f"- `{command}`" for command in BASELINE_COMMANDS],
                "",
                "This cleanup owns the canonical-root writer scope; unrelated admitted owner scopes remain independently schedulable.",
            ]
        ) + "\n"
    selected_jobs = report.get("selected_jobs", [])
    if not selected_jobs and report.get("selected_packet"):
        selected_jobs = [
            {
                "packet_id": report.get("selected_packet"),
                "logical_role_id": "atlas.main",
                "writer_scope": "atlas.root",
                "execution_class": "canonical_workspace",
            }
        ]
    lines = [
        "Run the selected ATLAS execution wave.",
        "",
        f"Selected jobs: `{len(selected_jobs)}`",
        f"Selected packet: `{report.get('selected_packet')}`",
        f"Routing mode: `{report.get('routing_mode')}`",
        f"Branch: `{report.get('git_state', {}).get('branch')}`",
        f"Head: `{report.get('git_state', {}).get('head')}`",
        "",
        "Execution wave:",
    ]
    lines.extend(
        f"- `{job.get('packet_id')}` -> `{job.get('logical_role_id')}` in `{job.get('writer_scope')}` ({job.get('execution_class')})"
        for job in selected_jobs
    )
    local_preparation_jobs = [
        job
        for job in selected_jobs
        if job.get("authority_class") == STANDING_LOCAL_SOURCE_PREPARATION
    ]
    if local_preparation_jobs:
        lines.extend(
            [
                "",
                "Standing local source-preparation boundaries:",
                *[
                    f"- `{job.get('packet_id')}`: edit only `{', '.join(job.get('source_preparation', {}).get('path_allowlist', []))}` "
                    "in its claimed isolated worktree; keep every change unstaged and publication held."
                    for job in local_preparation_jobs
                ],
                "- Do not stage, commit, push, create a branch or PR, request review, merge, run workflows, or access external writers/providers.",
            ]
        )
    lines.extend(
        [
        "",
        "Required preflight:",
        ]
    )
    lines.extend(f"- `{command}`" for command in BASELINE_COMMANDS)
    lines.extend(
        [
            "",
            "Scope lock:",
            "- Execute only the selected packet identities in their named standing roles and writer scopes.",
            "- One mutating job per conflict group; distinct conflict groups may run concurrently.",
            "- An active lease, dependency gap, identity drift, or authority mismatch defers only the affected lane.",
            "- Do not perform unadmitted provider, production, deployment, secret, workflow, `.env*`, `.vercel`, `.playwright-mcp`, or archive actions.",
            "",
        ]
    )
    if report.get("requires_reselection_receipt"):
        lines.extend(
            [
                "Reselection bundle required:",
                f"- Create receipt: `{report.get('reselection_receipt')}`",
                f"- Previous routing: `{report.get('git_state', {}).get('active_lane')}`",
                f"- Selected routing: `{report.get('selected_marker')}`",
                "",
            ]
        )
    lines.extend(
        [
            "Validation commands:",
            "- `python ops/validation/validate_stack.py`",
            "",
            "Commit/push/parity requirements:",
            "- Ordinary publication-authorized jobs stage only their admitted paths in their admitted worktree and branch.",
            "- Standing local source-preparation jobs remain unstaged and local; publication requires a separate exact authority packet.",
            "- Preserve per-packet commit, publication, review, merge, and provider gates.",
            "",
            "Continuation rule: consume terminal receipts, release only their exact leases, and immediately select the next non-conflicting READY wave without waiting for a heartbeat.",
        ]
    )
    return "\n".join(lines) + "\n"


class ProgramLockBusy(RuntimeError):
    pass


@contextmanager
def _exclusive_program_lock(program_path: Path):
    lock_path = program_path.with_suffix(program_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    locked = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise ProgramLockBusy(
                f"scheduler program is already reserved: {normalize_slashes(str(lock_path))}"
            ) from exc
        locked = True
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({"pid": os.getpid()}).encode("ascii"))
        handle.flush()
        yield
    finally:
        try:
            if locked:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def reserve_selected_jobs(
    *,
    program: dict[str, Any],
    report: dict[str, Any],
) -> tuple[dict[str, Any], list[OrderedDict[str, Any]]]:
    """Transition selected standing packets to ACTIVE and acquire writer leases."""

    selected = [item for item in report.get("selected_jobs", []) if isinstance(item, dict) and item.get("source") == "standing_task"]
    if not selected:
        return program, []
    standing = [item for item in program.get("standing_packets", []) if isinstance(item, dict)]
    packet_index = {str(item.get("packet_id")): item for item in standing if item.get("packet_id")}
    active_leases = [item for item in program.get("active_leases", []) if isinstance(item, dict)]
    delivery_intents = [item for item in program.get("delivery_intents", []) if isinstance(item, dict)]
    reservations: list[OrderedDict[str, Any]] = []
    reserved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    recovery_contexts: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    scope_holds = [item for item in program.get("scope_holds", []) if isinstance(item, dict)]
    active_runtime_holds = [item for item in scope_holds if item.get("derived_from_runtime_status") is True]
    for job in selected:
        if job.get("recovery_resume") is not True:
            continue
        packet_id = str(job.get("packet_id") or "")
        packet = packet_index.get(packet_id)
        writer_scope = str(job.get("writer_scope") or "")
        dispatch_reservation = packet.get("dispatch_reservation") if isinstance(packet, dict) else {}
        if not isinstance(dispatch_reservation, dict):
            dispatch_reservation = {}
        recovery_lease, recovery_intent = _exact_recovery_reservation(
            job,
            active_leases=active_leases,
            delivery_intents=delivery_intents,
        )
        resume_authority = packet.get("resume_authority") if isinstance(packet, dict) else {}
        packet_matches_job = bool(
            packet
            and str(packet.get("state") or "").upper() == RECOVERY_READY_STATE
            and str(packet.get("writer_scope") or "") == writer_scope
            and str(packet.get("runtime_thread_id") or "") == str(job.get("runtime_thread_id") or "")
            and str(packet.get("execution_class") or "") == str(job.get("execution_class") or "")
            and str(dispatch_reservation.get("reservation_id") or "")
            == str(job.get("recovery_reservation_id") or "")
            and _authority_is_canonical(resume_authority)
            and str(resume_authority.get("event_id") or "") == str(job.get("recovery_event_id") or "")
            and str(resume_authority.get("payload_digest") or "") == str(job.get("recovery_payload_digest") or "")
            and str(resume_authority.get("current_delivered_turn_id") or "")
            == str(job.get("recovery_current_delivered_turn_id") or "")
        )
        if not packet_matches_job or recovery_lease is None or recovery_intent is None:
            raise RuntimeError(f"recovery reservation lost correlation before dispatch: {packet_id}")
        if any(str(hold.get("writer_scope") or "") == writer_scope for hold in scope_holds):
            raise RuntimeError(f"recovery writer scope became held before dispatch: {writer_scope}")
        peer_leases = [
            lease
            for lease in active_leases
            if lease is not recovery_lease
            and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
        ]
        if any(
            str(lease.get("writer_scope") or "") == writer_scope
            or _candidate_conflicts(job, _active_lease_candidate(lease))
            for lease in peer_leases
        ):
            raise RuntimeError(f"recovery peer lease conflict appeared before dispatch: {packet_id}")
        if job.get("execution_class") in MUTATING_EXECUTION_CLASSES and any(
            not _active_lease_identity_complete(lease) for lease in peer_leases
        ):
            raise RuntimeError(f"recovery lease identity became incomplete before dispatch: {packet_id}")
        if job.get("execution_class") in MUTATING_EXECUTION_CLASSES and any(
            not _active_runtime_hold_identity_complete(hold) for hold in active_runtime_holds
        ):
            raise RuntimeError(f"recovery runtime hold identity became incomplete before dispatch: {packet_id}")
        if any(
            _candidate_conflicts(job, _active_runtime_hold_candidate(hold))
            for hold in active_runtime_holds
            if _active_runtime_hold_identity_complete(hold)
        ):
            raise RuntimeError(f"recovery runtime hold conflict appeared before dispatch: {packet_id}")
        recovery_contexts[packet_id] = (recovery_lease, recovery_intent)

    for job in selected:
        packet_id = str(job.get("packet_id") or "")
        packet = packet_index.get(packet_id)
        writer_scope = str(job.get("writer_scope") or "")
        recovery_lease, recovery_intent = recovery_contexts.get(packet_id, (None, None))
        if job.get("recovery_resume") is not True:
            recovery_lease, recovery_intent = _exact_recovery_reservation(
                job,
                active_leases=active_leases,
                delivery_intents=delivery_intents,
            )
        recovery_resume = recovery_lease is not None and recovery_intent is not None
        if packet is None or (
            not recovery_resume and str(packet.get("state") or "").upper() not in READY_STATES
        ) or (
            job.get("recovery_resume") is True
            and str(packet.get("state") or "").upper() != RECOVERY_READY_STATE
        ):
            raise RuntimeError(f"selected packet is no longer eligible: {packet_id}")
        if job.get("recovery_resume") is True and not recovery_resume:
            raise RuntimeError(f"recovery reservation lost correlation before dispatch: {packet_id}")
        authority = packet.get("authority") if isinstance(packet.get("authority"), dict) else {}
        if recovery_resume:
            reservation_id = str(job.get("recovery_reservation_id") or "")
            packet["state"] = "ACTIVE"
            packet["dispatch_reservation"]["resumed_at"] = reserved_at
            recovery_intent["status"] = "prepared"
            recovery_intent["prepared_at"] = reserved_at
            recovery_intent["recovery_resumed_at"] = reserved_at
            recovery_lease["status"] = "active"
            recovery_lease["resumed_at"] = reserved_at
            reservation = OrderedDict(
                [
                    ("reservation_id", reservation_id),
                    ("packet_id", packet_id),
                    ("logical_role_id", job.get("logical_role_id")),
                    ("runtime_thread_id", packet.get("runtime_thread_id")),
                    ("writer_scope", writer_scope),
                    ("execution_class", job.get("execution_class")),
                    ("reserved_at", reserved_at),
                    ("recovery_resume", True),
                ]
            )
            job["reservation_id"] = reservation_id
            job["runtime_thread_id"] = packet.get("runtime_thread_id")
            reservations.append(reservation)
            continue
        if any(
            str(lease.get("writer_scope") or "") == writer_scope
            and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
            for lease in active_leases
        ):
            raise RuntimeError(f"writer scope became leased before reservation: {writer_scope}")
        reservation_id = _deterministic_reservation_id(packet)
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = OrderedDict(
            [
                ("reservation_id", reservation_id),
                ("reserved_at", reserved_at),
                ("runtime_thread_id", packet.get("runtime_thread_id")),
            ]
        )
        reservation = OrderedDict(
            [
                ("reservation_id", reservation_id),
                ("packet_id", packet_id),
                ("logical_role_id", job.get("logical_role_id")),
                ("runtime_thread_id", packet.get("runtime_thread_id")),
                ("writer_scope", writer_scope),
                ("execution_class", job.get("execution_class")),
                ("reserved_at", reserved_at),
            ]
        )
        delivery_intents.append(
            OrderedDict(
                [
                    ("reservation_id", reservation_id),
                    ("packet_id", packet_id),
                    ("logical_role_id", job.get("logical_role_id")),
                    ("runtime_thread_id", packet.get("runtime_thread_id")),
                    ("writer_scope", writer_scope),
                    ("event_id", authority.get("event_id")),
                    ("payload_digest", authority.get("payload_digest")),
                    ("status", "prepared"),
                    ("prepared_at", reserved_at),
                    ("turn_id", None),
                ]
            )
        )
        if job.get("execution_class") in MUTATING_EXECUTION_CLASSES:
            active_leases.append(
                OrderedDict(
                    [
                        ("reservation_id", reservation_id),
                        ("packet_id", packet_id),
                        ("logical_role_id", job.get("logical_role_id")),
                        ("runtime_thread_id", packet.get("runtime_thread_id")),
                        ("writer_scope", writer_scope),
                        ("repository", job.get("repository")),
                        ("execution_class", job.get("execution_class")),
                        ("resource_claims", _resource_claims(job.get("resource_claims"))),
                        ("status", "active"),
                        ("acquired_at", reserved_at),
                        ("authority_event_id", authority.get("event_id")),
                    ]
                )
            )
        job["reservation_id"] = reservation_id
        job["runtime_thread_id"] = packet.get("runtime_thread_id")
        reservations.append(reservation)

    program["standing_packets"] = standing
    program["active_leases"] = active_leases
    program["delivery_intents"] = delivery_intents
    report["dispatch_reservations"] = reservations
    report["program_persisted_before_dispatch"] = True
    return program, reservations


def build_report(
    *,
    root: Path,
    program: dict[str, Any],
    max_candidates: int,
    prompt_output_path: str | None = None,
    current_marker: str | None = None,
    recent_docs_only_streak: int = 0,
    preflight_report: dict[str, Any] | None = None,
    selector_report: dict[str, Any] | None = None,
    planner_report: dict[str, Any] | None = None,
) -> OrderedDict[str, Any]:
    branch, head = _branch_state(root)
    parity = _parity_state(root)
    preflight_report = preflight_report or ai_work_session_preflight.build_report(root=root, scope="root")
    selector_report = selector_report or _load_selector(root)
    planner_report = planner_report or planner.build_report(root=root)

    active_marker = current_marker or str(selector_report.get("selected_marker") or preflight_report.get("markers", {}).get("active_lane") or "")
    active_lane_is_held = bool(selector_report.get("active_lane_is_held") or preflight_report.get("markers", {}).get("active_lane_is_held"))
    validation_state = _validation_state(preflight_report)
    scope_lock = _scope_lock(program)

    candidates: list[OrderedDict[str, Any]] = []
    skipped_candidates: list[OrderedDict[str, Any]] = []
    blocked_candidates: list[OrderedDict[str, Any]] = []
    for item in planner_report.get("candidate_scores", [])[:max_candidates]:
        if not isinstance(item, dict):
            continue
        candidate = _candidate_from_planner_item(
            item=item,
            active_marker=active_marker,
            active_lane_is_held=active_lane_is_held,
            program=program,
            recent_docs_only_streak=recent_docs_only_streak,
        )
        if candidate["safe"]:
            candidates.append(candidate)
        elif candidate["blocked_reason"]:
            blocked_candidates.append(candidate)
        else:
            skipped_candidates.append(candidate)

    standing_packets = program.get("standing_packets", [])
    if isinstance(standing_packets, list):
        for item in standing_packets:
            candidate = _candidate_from_standing_packet(item=item, program=program, root=root)
            if candidate["safe"]:
                candidates.append(candidate)
            else:
                blocked_candidates.append(candidate)

    exact_marker, exact_packet = _selector_exact_packet(selector_report)
    if exact_packet:
        exact_phase = _phase_from_packet(
            exact_packet,
            str(selector_report.get("selected_current_packet_mode") or ""),
            planner.CLASS_IMMEDIATE,
        )
        candidates.append(
            OrderedDict(
                [
                    ("marker", exact_marker),
                    ("lane", exact_marker),
                    ("packet_id", exact_packet),
                    ("packet", exact_packet),
                    ("phase", exact_phase),
                    ("score", 1_000_000),
                    ("source", "selector_current_packet"),
                    ("proof_delta", "implementation_backed"),
                    ("blocked_reason", None),
                    ("stale_reason", None),
                    ("file_overlap_risk", _file_overlap_risk(exact_phase)),
                    ("requires_external_input", False),
                    ("requires_reselection", False),
                    ("safe", True),
                    ("classification", planner.CLASS_IMMEDIATE),
                    ("logical_role_id", "atlas.main"),
                    ("repository", "fawxzzy/ATLAS"),
                    ("writer_scope", "atlas.root"),
                    ("execution_class", "canonical_workspace"),
                    ("dependencies", []),
                    ("resource_claims", _resource_claims({"files": ["**"]})),
                    ("cross_marker_signal_applied", False),
                ]
            )
        )

    candidate_count = len(candidates) + len(skipped_candidates) + len(blocked_candidates)
    candidates, duplicate_candidates = _dedupe_candidates(candidates)
    blocked_candidates.extend(duplicate_candidates)
    sorted_candidates = _sort_candidates(program, candidates)
    selected_jobs: list[OrderedDict[str, Any]] = []
    deferred_candidates: list[OrderedDict[str, Any]] = []
    status = STATUS_HOLD
    decision = DECISION_HOLD
    routing_mode = DECISION_HOLD
    selected_marker = None
    selected_packet = None
    packet_phase = PHASE_HOLD
    selected_packet_source = None
    requires_reselection_receipt = False
    reselection_receipt = None
    stop_reason = "no_safe_candidate"
    safe_to_execute = False

    if validation_state["critical"] > 0 or validation_state["error"] > 0:
        validation_cleanup_candidate = OrderedDict(
            [
                ("marker", "ATLAS root"),
                ("lane", "ATLAS root"),
                ("packet_id", "ATLAS root validation cleanup"),
                ("packet", "ATLAS root validation cleanup"),
                ("phase", PHASE_SELECTOR),
                ("score", 1_000_001),
                ("source", "validation"),
                ("proof_delta", "validation_cleanup"),
                ("blocked_reason", "root_validation_scope_held"),
                ("stale_reason", None),
                ("file_overlap_risk", "high"),
                ("requires_external_input", False),
                ("requires_reselection", False),
                ("safe", False),
                ("classification", "validation_cleanup"),
                ("logical_role_id", "atlas.main"),
                ("repository", "fawxzzy/ATLAS"),
                ("writer_scope", "atlas.root"),
                ("execution_class", "canonical_workspace"),
                ("dependencies", []),
                ("resource_claims", _resource_claims({"files": ["**"]})),
                ("cross_marker_signal_applied", False),
            ]
        )
        # Validation owns the checkout being validated. A same-repository
        # worktree may continue only with complete, distinct isolation claims.
        disjoint_candidates = [
            candidate
            for candidate in sorted_candidates
            if not _candidate_conflicts_with_root_validation(
                candidate,
                validation_cleanup_candidate,
                validation_root=root,
            )
        ]
        selected_jobs, wave_blocked, deferred_candidates = _select_execution_wave(
            program=program,
            candidates=disjoint_candidates,
        )
        blocked_candidates.extend(wave_blocked)
        if selected_jobs:
            blocked_candidates.append(validation_cleanup_candidate)
        else:
            status = STATUS_VALIDATION_CLEANUP
            decision = DECISION_VALIDATION_CLEANUP
            routing_mode = DECISION_VALIDATION_CLEANUP
            selected_marker = "ATLAS root"
            selected_packet = "ATLAS root validation cleanup"
            packet_phase = PHASE_SELECTOR
            selected_packet_source = "validation"
            stop_reason = "critical_or_error_validation"
            safe_to_execute = True
            selected_jobs = [
                OrderedDict(
                    [
                        ("marker", "ATLAS root"),
                        ("lane", "ATLAS root"),
                        ("packet_id", selected_packet),
                        ("packet", selected_packet),
                        ("phase", packet_phase),
                        ("source", selected_packet_source),
                        ("logical_role_id", "atlas.main"),
                        ("repository", "fawxzzy/ATLAS"),
                        ("writer_scope", "atlas.root"),
                        ("execution_class", "canonical_workspace"),
                    ]
                )
            ]
    else:
        selected_jobs, wave_blocked, deferred_candidates = _select_execution_wave(
            program=program,
            candidates=sorted_candidates,
        )
        blocked_candidates.extend(wave_blocked)

    selected_candidate = selected_jobs[0] if selected_jobs else None
    if status != STATUS_VALIDATION_CLEANUP and selected_candidate is not None:
        selected_marker = str(selected_candidate["marker"] or "")
        selected_packet = str(selected_candidate["packet"] or "")
        packet_phase = str(selected_candidate["phase"] or PHASE_HOLD)
        selected_packet_source = str(selected_candidate["source"] or "planner")
        requires_reselection_receipt = bool(selected_candidate["requires_reselection"])
        reselection_receipt = _reselection_receipt(selected_marker) if requires_reselection_receipt else None
        if len(selected_jobs) > 1:
            decision = DECISION_EXECUTION_WAVE
        elif selected_packet_source == "selector_current_packet":
            decision = DECISION_EXACT_MANIFEST_PACKET
        elif packet_phase == PHASE_WORKER_RECONCILIATION:
            decision = DECISION_WORKER_RECONCILIATION
        elif packet_phase == PHASE_WORKER_IMPLEMENTATION:
            decision = DECISION_ROUTED_WORKER
        elif bool(selected_candidate.get("cross_marker_signal_applied")):
            decision = DECISION_CROSS_MARKER_OPPORTUNITY
        elif requires_reselection_receipt:
            decision = DECISION_OPERATOR_PROGRAM_PACKET
        else:
            decision = DECISION_PLANNER_CANDIDATE
        routing_mode = decision
        status = STATUS_EXECUTE
        stop_reason = None
        safe_to_execute = True

    report = OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("decision", decision),
            ("routing_mode", routing_mode),
            ("selected_marker", selected_marker),
            ("selected_lane", selected_marker),
            ("selected_packet", selected_packet),
            ("packet_phase", packet_phase),
            ("selected_packet_source", selected_packet_source),
            ("requires_reselection_receipt", requires_reselection_receipt),
            ("reselection_receipt", reselection_receipt),
            ("candidate_count", candidate_count),
            ("candidates", sorted_candidates),
            ("selected_jobs", selected_jobs),
            ("execution_waves", [OrderedDict([("wave", 1), ("packet_ids", [job.get("packet_id") for job in selected_jobs])])] if selected_jobs else []),
            ("deferred_candidates", deferred_candidates),
            ("skipped_candidates", skipped_candidates),
            ("blocked_candidates", blocked_candidates),
            ("validation_state", validation_state),
            (
                "git_state",
                OrderedDict(
                    [
                        ("branch", branch),
                        ("head", head),
                        ("parity", parity),
                        ("active_lane", active_marker),
                        ("active_lane_is_held", active_lane_is_held),
                    ]
                ),
            ),
            ("scope_lock", scope_lock),
            ("authority_denials", AUTHORITY_DENIALS),
            ("safe_to_execute", safe_to_execute),
            ("stop_reason", stop_reason),
            ("prompt_output", prompt_output_path),
            (
                "next_recommended_command",
                "python ops/atlas/autonomous_lane_scheduler.py --json --program tmp/atlas/autonomous-work-program.json --bindings tmp/atlas/standing-role-bindings.latest.json --envelopes tmp/atlas/autonomous-inbox-events.jsonl --delivery-results tmp/atlas/delivery-results.latest.jsonl --max-candidates 30 --output tmp/atlas/autonomous-lane-scheduler.latest.json --prompt-output tmp/atlas/codex-autocomplete-prompt.latest.md",
            ),
        ]
    )
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select one deterministic conflict-safe ATLAS execution wave.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--program", required=True, help="Root-relative operator work-program JSON path.")
    parser.add_argument("--bindings", help="Root-relative standing-role binding snapshot JSON path.")
    parser.add_argument("--envelopes", help="Root-relative canonical Inbox envelope JSON or JSONL path.")
    parser.add_argument("--delivery-results", help="Root-relative app-native delivery result JSON or JSONL path.")
    parser.add_argument("--output", required=True, help="Root-relative tmp/atlas/**.json output path.")
    parser.add_argument("--prompt-output", required=True, help="Root-relative tmp/atlas/**.md prompt output path.")
    parser.add_argument("--max-candidates", type=int, default=30, help="Maximum planner candidates to consider.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when no executable packet exists.")
    parser.add_argument("--explain", action="store_true", help="Reserved for verbose output compatibility.")
    parser.add_argument("--allow-reselection", action="store_true", help="Override program allow_reselection to true.")
    parser.add_argument("--current-marker", help="Optional explicit current marker override.")
    return parser.parse_args(argv)


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_EXECUTE:
        return 0
    if status == STATUS_HOLD:
        return 2 if strict else 0
    if status == STATUS_VALIDATION_CLEANUP:
        return 2 if strict else 1
    if status == STATUS_BLOCKED:
        return 2
    return 3


def _blocked_report(*, args: argparse.Namespace, blockers: list[OrderedDict[str, Any]], stop_reason: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", STATUS_BLOCKED),
            ("decision", DECISION_HOLD),
            ("routing_mode", DECISION_HOLD),
            ("selected_marker", None),
            ("selected_lane", None),
            ("selected_packet", None),
            ("packet_phase", PHASE_HOLD),
            ("selected_packet_source", None),
            ("requires_reselection_receipt", False),
            ("reselection_receipt", None),
            ("candidate_count", 0),
            ("candidates", []),
            ("selected_jobs", []),
            ("execution_waves", []),
            ("deferred_candidates", []),
            ("skipped_candidates", []),
            ("blocked_candidates", blockers),
            ("validation_state", OrderedDict()),
            ("git_state", OrderedDict()),
            ("scope_lock", OrderedDict()),
            ("authority_denials", AUTHORITY_DENIALS),
            ("safe_to_execute", False),
            ("stop_reason", stop_reason),
            ("prompt_output", args.prompt_output),
            ("next_recommended_command", None),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root()
    try:
        bridge_inputs_complete = bool(args.bindings and args.envelopes)
        program_path, program_path_error = validate_program_path(
            root,
            args.program,
            allow_missing=bridge_inputs_complete,
        )
        output_path, output_error = validate_output_path(root, args.output, suffix=".json")
        prompt_output_path, prompt_output_error = validate_output_path(root, args.prompt_output, suffix=".md")
        bindings_path = None
        envelopes_path = None
        delivery_results_path = None
        bindings_error = None
        envelopes_error = None
        delivery_results_error = None
        if bool(args.bindings) != bool(args.envelopes):
            bindings_error = _finding("bridge_inputs_incomplete", "--bindings and --envelopes must be supplied together.")
        elif args.bindings and args.envelopes:
            bindings_path, bindings_error = validate_input_path(root, args.bindings, suffixes=(".json",))
            envelopes_path, envelopes_error = validate_input_path(root, args.envelopes, suffixes=(".json", ".jsonl"))
        if args.delivery_results:
            delivery_results_path, delivery_results_error = validate_input_path(
                root,
                args.delivery_results,
                suffixes=(".json", ".jsonl"),
            )
        blockers = [
            error
            for error in [program_path_error, output_error, prompt_output_error, bindings_error, envelopes_error, delivery_results_error]
            if error is not None
        ]
        if blockers or program_path is None or output_path is None or prompt_output_path is None:
            payload = _blocked_report(args=args, blockers=blockers, stop_reason="invalid_scheduler_inputs")
            print(json.dumps(payload, indent=2))
            return 2

        with _exclusive_program_lock(program_path):
            program_initialized = not program_path.exists()
            if program_initialized:
                program = _initial_runtime_program()
                program_errors: list[OrderedDict[str, Any]] = []
            else:
                program, program_errors = load_program(root, args.program)
                if program is None or program_errors:
                    payload = _blocked_report(args=args, blockers=program_errors, stop_reason="invalid_scheduler_inputs")
                    print(json.dumps(payload, indent=2))
                    return 2
            loaded_program_digest = _canonical_payload_digest(program)
            loaded_revision = 0 if program_initialized else int(program.get("revision", 0) or 0)
            bridge_findings: list[OrderedDict[str, Any]] = []
            bindings_payload: dict[str, Any] | None = None
            envelopes: list[dict[str, Any]] = []
            if bindings_path is not None and envelopes_path is not None:
                bindings_payload = _load_json_object(bindings_path, label="bindings")
                envelopes = _load_envelopes(envelopes_path)
                nonterminal_envelopes = [
                    envelope
                    for envelope in envelopes
                    if not _terminal_success(envelope.get("payload") if isinstance(envelope.get("payload"), dict) else {})
                    and not _terminal_cancellation(
                        envelope.get("payload") if isinstance(envelope.get("payload"), dict) else {}
                    )
                ]
                program, admission_findings = reconcile_runtime_program(
                    program=program,
                    bindings_payload=bindings_payload,
                    envelopes=nonterminal_envelopes,
                    root=root,
                )
                bridge_findings.extend(admission_findings)
            if delivery_results_path is not None:
                program, delivery_findings = apply_delivery_results(
                    program=program,
                    results=_load_envelopes(delivery_results_path),
                )
                bridge_findings.extend(delivery_findings)
            if bindings_payload is not None:
                program, terminal_findings = reconcile_runtime_program(
                    program=program,
                    bindings_payload=bindings_payload,
                    envelopes=envelopes,
                    root=root,
                )
                bridge_findings.extend(terminal_findings)
            if args.allow_reselection:
                program["allow_reselection"] = True
            bridge_findings = _dedupe_findings(bridge_findings)
            program["bridge_findings"] = bridge_findings

            report = build_report(
                root=root,
                program=program,
                max_candidates=args.max_candidates,
                prompt_output_path=normalize_slashes(args.prompt_output),
                current_marker=args.current_marker,
            )
            program, _ = reserve_selected_jobs(program=program, report=report)
            report["bridge_findings"] = bridge_findings
            report["dispatch_plan"] = [
                OrderedDict(
                    [
                        ("packet_id", job.get("packet_id")),
                        ("logical_role_id", job.get("logical_role_id")),
                        ("runtime_thread_id", job.get("runtime_thread_id")),
                        ("reservation_id", job.get("reservation_id")),
                    ]
                )
                for job in report.get("selected_jobs", [])
                if isinstance(job, dict) and job.get("source") == "standing_task"
            ]
            program_changed = program_initialized or _canonical_payload_digest(program) != loaded_program_digest
            if program_changed:
                program["revision"] = loaded_revision + 1
                _atomic_write_json(program_path, program)
            report["program_revision"] = program.get("revision", loaded_revision)
            prompt_text = render_prompt(report)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            prompt_output_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_output_path.write_text(prompt_text, encoding="utf-8")
            print(json.dumps(report, indent=2))
            return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except ProgramLockBusy as exc:
        payload = _blocked_report(
            args=args,
            blockers=[_finding("program_lock_busy", "Another scheduler invocation owns the atomic reservation lock.", error=str(exc))],
            stop_reason="program_lock_busy",
        )
        print(json.dumps(payload, indent=2))
        return 2
    except Exception as exc:  # pragma: no cover - defensive guard
        payload = _blocked_report(
            args=args,
            blockers=[_finding("internal_error", "Unhandled scheduler exception.", error=str(exc))],
            stop_reason="internal_error",
        )
        payload["status"] = STATUS_INTERNAL_ERROR
        print(json.dumps(payload, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
