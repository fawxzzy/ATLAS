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

EXECUTION_CLASSES = {"read_only", "repo_worktree", "canonical_workspace"}
READY_STATES = {"READY", "ADMITTED", "QUEUED"}
MUTATING_EXECUTION_CLASSES = {"repo_worktree", "canonical_workspace"}
EVENT_ID_PATTERN = re.compile(r"^onv1_[0-9a-f]{64}$")
PAYLOAD_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RESUMABLE_RUNTIME_STATES = {"idle", "notloaded"}
TERMINAL_SUCCESS_STATES = {"ACCEPTED", "COMPLETE", "COMPLETED", "MERGED", "SUCCESS"}

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


def validate_program_path(root: Path, path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(path, root)
    if error is not None or ref is None:
        return None, error
    if not ref.endswith(".json"):
        return None, _finding("program_not_json", "Program path must end with .json.", path=ref)
    resolved = (root / ref).resolve()
    if not resolved.exists():
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
    return payload, errors


def _canonical_payload_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


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
    intents = [item for item in program.get("delivery_intents", []) if isinstance(item, dict)]
    intent_index = {str(item.get("reservation_id")): item for item in intents if item.get("reservation_id")}
    leases = [item for item in program.get("active_leases", []) if isinstance(item, dict)]
    for result in results:
        reservation_id = str(result.get("reservation_id") or "")
        intent = intent_index.get(reservation_id)
        if intent is None:
            findings.append(_finding("delivery_intent_not_found", "Delivery result has no prepared intent.", reservation_id=reservation_id or None))
            continue
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
            if prior_turn not in {None, turn_id}:
                findings.append(_finding("delivery_turn_id_collision", "One reservation resolved to multiple turn IDs.", reservation_id=reservation_id))
                continue
            intent["status"] = "delivered"
            intent["turn_id"] = turn_id
        elif status == "RECOVERY_REQUIRED":
            intent["status"] = "recovery-required"
            for lease in leases:
                if lease.get("reservation_id") == reservation_id:
                    lease["status"] = "recovery-required"
        else:
            findings.append(_finding("delivery_result_status_invalid", "Delivery result status must be DELIVERED or RECOVERY_REQUIRED.", reservation_id=reservation_id))
    program["delivery_intents"] = intents
    program["active_leases"] = leases
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


def _terminal_success(payload: dict[str, Any]) -> bool:
    if payload.get("terminal") is not True:
        return False
    state = str(payload.get("canonical_lifecycle_state") or payload.get("state") or payload.get("status") or "").upper()
    tokens = set(state.split("_"))
    denied = {"BLOCKED", "FAILED", "LATENCY", "PENDING", "UNKNOWN"}
    return not tokens.intersection(denied) and bool(tokens.intersection(TERMINAL_SUCCESS_STATES | {"PASS"}))


def reconcile_runtime_program(
    *,
    program: dict[str, Any],
    bindings_payload: dict[str, Any],
    envelopes: list[dict[str, Any]],
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
            matching_intents = [
                intent
                for intent in delivery_intents
                if str(intent.get("reservation_id") or "") == reservation_id
                and str(intent.get("packet_id") or "") == packet_id
                and str(intent.get("writer_scope") or "") == writer_scope
                and str(intent.get("turn_id") or "") == turn_id
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
        repository = str(payload.get("repository") or "")
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
                ("runtime_thread_id", runtime_thread_id),
                ("runtime_status", runtime_status),
                ("authority", OrderedDict([("event_id", event_id), ("payload_digest", payload_digest)])),
                ("idempotency_key", envelope.get("idempotency_key")),
            ]
        )
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
                ("writer_scope", packet.get("writer_scope")),
                ("logical_role_id", packet.get("logical_role_id")),
                ("runtime_thread_id", packet.get("runtime_thread_id")),
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


def _resource_claims(value: Any) -> OrderedDict[str, list[str]]:
    raw = value if isinstance(value, dict) else {}
    return OrderedDict(
        (kind, _string_list(raw.get(kind, [])))
        for kind in ("files", "worktrees", "ports", "browsers", "external_writers")
    )


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
    repository = str(item.get("repository") or ("fawxzzy/ATLAS" if default_root else "")) or None
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
    elif _is_protected_packet(packet):
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


def _candidate_from_standing_packet(*, item: Any, program: dict[str, Any]) -> OrderedDict[str, Any]:
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
    blocked_reason = None
    if not packet_id or not packet:
        blocked_reason = "standing_packet_identity_required"
    elif state not in READY_STATES:
        blocked_reason = "standing_packet_not_ready"
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
    elif _is_protected_packet(packet) and raw.get("protected_surface_authorized") is not True:
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
            ("cross_marker_signal_applied", False),
            ("authority", raw.get("authority")),
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
    same_repository = bool(left.get("repository")) and left.get("repository") == right.get("repository")
    files_overlap = any(
        _patterns_overlap(a, b)
        for a in left_claims.get("files", [])
        for b in right_claims.get("files", [])
    )
    if same_repository and files_overlap:
        conflicts.append("files")
    if left_mutates and right_mutates and same_repository:
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


def _active_lease_candidate(
    lease: dict[str, Any],
    *,
    standing_packets: dict[str, dict[str, Any]],
) -> OrderedDict[str, Any]:
    packet = standing_packets.get(str(lease.get("packet_id") or ""), {})
    return OrderedDict(
        [
            ("packet_id", lease.get("packet_id")),
            ("repository", lease.get("repository") or packet.get("repository")),
            ("writer_scope", lease.get("writer_scope")),
            ("execution_class", lease.get("execution_class") or packet.get("execution_class")),
            ("resource_claims", _resource_claims(lease.get("resource_claims") or packet.get("resource_claims"))),
        ]
    )


def _select_execution_wave(
    *,
    program: dict[str, Any],
    candidates: list[OrderedDict[str, Any]],
) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    selected: list[OrderedDict[str, Any]] = []
    blocked: list[OrderedDict[str, Any]] = []
    deferred: list[OrderedDict[str, Any]] = []
    active_scopes = _active_writer_scopes(program)
    completed = set(_string_list(program.get("completed_packets", [])))
    max_writers_value = program.get("max_parallel_writers", 4)
    max_writers = max(0, int(4 if max_writers_value is None else max_writers_value))
    max_read_only_value = program.get("max_parallel_read_only", 2)
    max_read_only = max(0, int(2 if max_read_only_value is None else max_read_only_value))
    active_leases = [item for item in program.get("active_leases", []) if isinstance(item, dict)]
    standing_packets = {
        str(item.get("packet_id")): item
        for item in program.get("standing_packets", [])
        if isinstance(item, dict) and item.get("packet_id")
    }
    active_lease_candidates = [
        (lease, _active_lease_candidate(lease, standing_packets=standing_packets))
        for lease in active_leases
        if str(lease.get("status") or "").lower() in {"active", "recovery-required"}
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
        if candidate.get("writer_scope") in active_scopes:
            candidate["blocked_reason"] = "writer_scope_leased"
            blocked.append(candidate)
            continue
        if missing_dependencies:
            candidate["blocked_reason"] = "dependencies_not_complete"
            candidate["missing_dependencies"] = missing_dependencies
            blocked.append(candidate)
            continue
        lease_conflicts = [
            (lease, _candidate_conflicts(candidate, leased_candidate))
            for lease, leased_candidate in active_lease_candidates
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
            "- Each owner stages only its admitted paths in its admitted worktree and branch.",
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

    for job in selected:
        packet_id = str(job.get("packet_id") or "")
        packet = packet_index.get(packet_id)
        if packet is None or str(packet.get("state") or "").upper() not in READY_STATES:
            raise RuntimeError(f"selected packet is no longer READY: {packet_id}")
        writer_scope = str(job.get("writer_scope") or "")
        if any(
            str(lease.get("writer_scope") or "") == writer_scope
            and str(lease.get("status") or "").lower() in {"active", "recovery-required"}
            for lease in active_leases
        ):
            raise RuntimeError(f"writer scope became leased before reservation: {writer_scope}")
        authority = packet.get("authority") if isinstance(packet.get("authority"), dict) else {}
        reservation_seed = "|".join(
            [
                packet_id,
                writer_scope,
                str(packet.get("runtime_thread_id") or ""),
                str(authority.get("event_id") or ""),
            ]
        )
        reservation_id = "rsrv_" + hashlib.sha256(reservation_seed.encode("utf-8")).hexdigest()
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
            candidate = _candidate_from_standing_packet(item=item, program=program)
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
        # Validation owns only atlas.root and its file surface. Keep every
        # candidate whose declared resources are disjoint from that scope.
        disjoint_candidates = [
            candidate
            for candidate in sorted_candidates
            if not _candidate_conflicts(candidate, validation_cleanup_candidate)
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
                "python ops/atlas/autonomous_lane_scheduler.py --json --program tmp/atlas/autonomous-work-program.json --bindings tmp/atlas/standing-role-bindings.latest.json --envelopes tmp/atlas/autonomous-inbox-events.jsonl --max-candidates 30 --output tmp/atlas/autonomous-lane-scheduler.latest.json --prompt-output tmp/atlas/codex-autocomplete-prompt.latest.md",
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
        program_path, program_path_error = validate_program_path(root, args.program)
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
            program, program_errors = load_program(root, args.program)
            if program is None or program_errors:
                payload = _blocked_report(args=args, blockers=program_errors, stop_reason="invalid_scheduler_inputs")
                print(json.dumps(payload, indent=2))
                return 2
            loaded_program_digest = _canonical_payload_digest(program)
            loaded_revision = int(program.get("revision", 0) or 0)
            bridge_findings: list[OrderedDict[str, Any]] = []
            if delivery_results_path is not None:
                program, delivery_findings = apply_delivery_results(
                    program=program,
                    results=_load_envelopes(delivery_results_path),
                )
                bridge_findings.extend(delivery_findings)
            if bindings_path is not None and envelopes_path is not None:
                bindings_payload = _load_json_object(bindings_path, label="bindings")
                envelopes = _load_envelopes(envelopes_path)
                program, bridge_findings = reconcile_runtime_program(
                    program=program,
                    bindings_payload=bindings_payload,
                    envelopes=envelopes,
                )
            if args.allow_reselection:
                program["allow_reselection"] = True

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
            program_changed = _canonical_payload_digest(program) != loaded_program_digest
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
