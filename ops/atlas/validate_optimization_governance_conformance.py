from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_REF = "docs/prompts/atlas-workflow/STANDING-BASELINE.md"
GOVERNANCE_REF = "docs/registry/ATLAS-WORKFLOW-OPTIMIZATION-GOVERNANCE.v1.json"
ANTI_CHURN_BASELINE_MARKERS = (
    "single non-product-blocking failure observation remains one canonical record",
    "ephemeral reviewer and bounded helper identities form an auxiliary denominator",
    "ephemeral-only identity change must not trigger a material handoff",
)
COMMON_RELEASE_BASELINE_MARKERS = (
    "canonicalize strict same-origin URL paths before exact comparison",
    "validate the immutable expected workspace",
    "a diagnostic must never implicitly link or create a provider project",
)
class ConformanceError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConformanceError(f"unable to read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConformanceError(f"expected JSON object at {path}")
    return value


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConformanceError(f"unable to read TOML {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConformanceError(f"expected TOML table at {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rrule_minutes(rrule: str) -> int | None:
    parts = {}
    for token in rrule.split(";"):
        if "=" not in token:
            return None
        key, value = token.split("=", 1)
        parts[key] = value
    try:
        interval = int(parts.get("INTERVAL", "1"))
    except ValueError:
        return None
    if parts.get("FREQ") == "HOURLY":
        return interval * 60
    if parts.get("FREQ") == "MINUTELY":
        return interval
    return None


def _topology_entries(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    topology = ledger.get("worker_topology")
    if not isinstance(topology, dict):
        raise ConformanceError("integration ledger is missing worker_topology")
    integrator = topology.get("integrator")
    workers = topology.get("bounded_workers")
    if not isinstance(integrator, dict) or not isinstance(workers, list):
        raise ConformanceError("integration ledger topology is malformed")
    entries = [integrator, *workers]
    if any(not isinstance(entry, dict) for entry in entries):
        raise ConformanceError("integration ledger topology entry is malformed")
    return entries


def validate_conformance(
    atlas_root: Path,
    automations_root: Path,
    ledger_path: Path,
    manifest_path: Path,
    now: datetime,
    max_checkpoint_age_hours: float,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    def check(condition: bool, code: str, detail: str) -> None:
        if not condition:
            errors.append({"code": code, "detail": detail})

    ledger = _load_json(ledger_path)
    manifest = _load_json(manifest_path)
    conformance = ledger.get("active_task_governance_conformance")
    if not isinstance(conformance, dict):
        raise ConformanceError("integration ledger is missing active_task_governance_conformance")

    entries = _topology_entries(ledger)
    expected_ids = [entry.get("automation_id") for entry in entries]
    check(len(entries) == 4, "PROGRAM_TASK_DENOMINATOR_DRIFT", f"expected 4 entries, found {len(entries)}")
    check(
        len(set(expected_ids)) == 4 and all(isinstance(value, str) and value for value in expected_ids),
        "AUTOMATION_IDENTITY_DRIFT",
        "four unique nonempty automation ids are required",
    )

    live_automations: list[dict[str, Any]] = []
    for entry in entries:
        automation_id = entry.get("automation_id")
        if not isinstance(automation_id, str) or not automation_id:
            continue
        automation_path = automations_root / automation_id / "automation.toml"
        if not automation_path.is_file():
            check(False, "AUTOMATION_MISSING", automation_id)
            continue
        live = _load_toml(automation_path)
        cadence = _rrule_minutes(str(live.get("rrule", "")))
        expected_cadence = entry.get("cadence_minutes")
        expected_name = entry.get("automation_name", entry.get("title"))
        check(live.get("id") == automation_id, "AUTOMATION_ID_MISMATCH", automation_id)
        check(live.get("kind") == "heartbeat", "AUTOMATION_KIND_MISMATCH", automation_id)
        check(live.get("name") == expected_name, "AUTOMATION_NAME_MISMATCH", automation_id)
        check(live.get("status") == entry.get("schedule_status"), "AUTOMATION_STATUS_DRIFT", automation_id)
        check(live.get("target_thread_id") == entry.get("thread_id"), "AUTOMATION_TARGET_DRIFT", automation_id)
        check(cadence == expected_cadence, "AUTOMATION_CADENCE_DRIFT", automation_id)
        prompt = live.get("prompt")
        normalized_prompt = prompt.lower() if isinstance(prompt, str) else ""
        boundary_markers = (
            "do not create",
            "never create",
            "exactly four codex tasks",
            "additional supervisor",
        )
        check(
            any(marker in normalized_prompt for marker in boundary_markers),
            "FOUR_TASK_BOUNDARY_MISSING",
            automation_id,
        )
        live_automations.append(
            {
                "automation_id": automation_id,
                "name": live.get("name"),
                "status": live.get("status"),
                "rrule": live.get("rrule"),
                "cadence_minutes": cadence,
                "target_thread_id": live.get("target_thread_id"),
                "toml_sha256": f"sha256:{_sha256(automation_path)}",
            }
        )

    visibility = ledger.get("operator_visibility_topology")
    if not isinstance(visibility, dict):
        raise ConformanceError("integration ledger is missing operator_visibility_topology")
    check(visibility.get("task_count") == 1, "STATUS_TASK_DENOMINATOR_DRIFT", str(visibility.get("task_count")))
    check(
        visibility.get("excluded_from_learning_program") is True,
        "STATUS_TASK_PROGRAM_WIDENING",
        "status task must remain outside the four-task learning program",
    )
    status_thread_id = visibility.get("thread_id")
    learning_thread_ids = [entry.get("thread_id") for entry in entries]
    check(
        isinstance(status_thread_id, str) and status_thread_id not in learning_thread_ids,
        "STATUS_TASK_IDENTITY_COLLISION",
        str(status_thread_id),
    )
    status_automation = visibility.get("automation")
    if not isinstance(status_automation, dict):
        raise ConformanceError("operator visibility topology is missing automation")
    status_automation_id = status_automation.get("automation_id")
    check(
        isinstance(status_automation_id, str) and status_automation_id not in expected_ids,
        "STATUS_AUTOMATION_IDENTITY_COLLISION",
        str(status_automation_id),
    )
    status_live: dict[str, Any] = {}
    status_automation_path = automations_root / str(status_automation_id) / "automation.toml"
    if not status_automation_path.is_file():
        check(False, "STATUS_AUTOMATION_MISSING", str(status_automation_id))
    else:
        status_live = _load_toml(status_automation_path)
        status_cadence = _rrule_minutes(str(status_live.get("rrule", "")))
        check(status_live.get("id") == status_automation_id, "STATUS_AUTOMATION_ID_MISMATCH", str(status_automation_id))
        check(status_live.get("kind") == "heartbeat", "STATUS_AUTOMATION_KIND_MISMATCH", str(status_automation_id))
        check(status_live.get("name") == status_automation.get("automation_name"), "STATUS_AUTOMATION_NAME_MISMATCH", str(status_automation_id))
        check(status_live.get("status") == status_automation.get("schedule_status"), "STATUS_AUTOMATION_STATUS_DRIFT", str(status_automation_id))
        check(status_live.get("target_thread_id") == status_thread_id, "STATUS_AUTOMATION_TARGET_DRIFT", str(status_automation_id))
        check(status_cadence == status_automation.get("cadence_minutes"), "STATUS_AUTOMATION_CADENCE_DRIFT", str(status_automation_id))
        expected_status_hash = status_automation.get("toml_sha256")
        observed_status_hash = f"sha256:{_sha256(status_automation_path)}"
        if isinstance(expected_status_hash, str) and expected_status_hash:
            check(observed_status_hash == expected_status_hash, "STATUS_AUTOMATION_HASH_DRIFT", str(status_automation_id))
        status_prompt = str(status_live.get("prompt", "")).lower()
        check(
            "projection-only" in status_prompt or "read-only human atlas dashboard" in status_prompt,
            "STATUS_PROJECTION_BOUNDARY_MISSING",
            str(status_automation_id),
        )
        check("do not dispatch" in status_prompt, "STATUS_DISPATCH_BOUNDARY_MISSING", str(status_automation_id))
        check(
            "do not rewrite files" in status_prompt
            or ("if none changed" in status_prompt and "projection rewrites" in status_prompt),
            "STATUS_NO_DELTA_BOUNDARY_MISSING",
            str(status_automation_id),
        )
        if status_automation.get("identity_first_delta_gate") is True:
            check("identity gate" in status_prompt, "STATUS_IDENTITY_GATE_MISSING", str(status_automation_id))
            check(
                "direct material handoffs" in status_prompt,
                "STATUS_DIRECT_HANDOFF_BOUNDARY_MISSING",
                str(status_automation_id),
            )

    visibility_scope = visibility.get("scope")
    if not isinstance(visibility_scope, dict):
        raise ConformanceError("operator visibility topology is missing scope")
    for field in ("read_only_projection", "dispatch_allowed", "approval_evaluation_allowed", "state_mutation_allowed"):
        expected = field == "read_only_projection"
        check(visibility_scope.get(field) is expected, "STATUS_SCOPE_WIDENING", field)

    projection_refs = visibility.get("projection")
    if not isinstance(projection_refs, dict):
        raise ConformanceError("operator visibility topology is missing projection")
    projection_checks: list[dict[str, Any]] = []
    for label in ("json", "markdown"):
        ref = projection_refs.get(f"{label}_ref")
        expected_hash = projection_refs.get(f"{label}_sha256")
        projection_path = atlas_root / str(ref)
        check(projection_path.is_file(), "STATUS_PROJECTION_MISSING", str(ref))
        observed_hash = f"sha256:{_sha256(projection_path)}" if projection_path.is_file() else None
        check(observed_hash == expected_hash, "STATUS_PROJECTION_HASH_DRIFT", f"{label}:{ref}")
        projection_checks.append({"kind": label, "ref": ref, "expected_sha256": expected_hash, "observed_sha256": observed_hash})

    status_checkpoint = visibility.get("checkpoint")
    if not isinstance(status_checkpoint, dict):
        raise ConformanceError("operator visibility topology is missing checkpoint")
    status_checkpoint_ref = status_checkpoint.get("ref")
    status_checkpoint_path = atlas_root / str(status_checkpoint_ref)
    check(status_checkpoint_path.is_file(), "STATUS_CHECKPOINT_MISSING", str(status_checkpoint_ref))
    status_checkpoint_value = _load_json(status_checkpoint_path) if status_checkpoint_path.is_file() else {}
    status_payload = status_checkpoint_value.get("payload", {}) if isinstance(status_checkpoint_value, dict) else {}
    check(status_payload.get("thread_id") == status_thread_id, "STATUS_CHECKPOINT_THREAD_DRIFT", str(status_thread_id))
    check(status_payload.get("logical_role_id") == "atlas.status-projection", "STATUS_CHECKPOINT_ROLE_DRIFT", str(status_payload.get("logical_role_id")))
    status_receipts = status_payload.get("receipts", []) if isinstance(status_payload, dict) else []
    if not isinstance(status_receipts, list):
        status_receipts = []
    for label in ("json", "markdown"):
        ref = projection_refs.get(f"{label}_ref")
        expected_hash = projection_refs.get(f"{label}_sha256")
        normalized_hash = expected_hash.removeprefix("sha256:") if isinstance(expected_hash, str) else expected_hash
        anchor = f"{ref}#sha256={normalized_hash}"
        check(anchor in status_receipts, "STATUS_CHECKPOINT_RECEIPT_HASH_DRIFT", label)

    questions_consumer = visibility.get("questions_consumer")
    if not isinstance(questions_consumer, dict):
        raise ConformanceError("operator visibility topology is missing questions_consumer")
    questions_automation_id = questions_consumer.get("automation_id")
    questions_path = automations_root / str(questions_automation_id) / "automation.toml"
    check(questions_path.is_file(), "QUESTIONS_AUTOMATION_MISSING", str(questions_automation_id))
    questions_live = _load_toml(questions_path) if questions_path.is_file() else {}
    check(questions_live.get("target_thread_id") == questions_consumer.get("thread_id"), "QUESTIONS_AUTOMATION_TARGET_DRIFT", str(questions_automation_id))
    check(questions_live.get("status") == questions_consumer.get("schedule_status"), "QUESTIONS_AUTOMATION_STATUS_DRIFT", str(questions_automation_id))
    questions_cadence = _rrule_minutes(str(questions_live.get("rrule", "")))
    expected_questions_cadence = questions_consumer.get("cadence_minutes")
    if isinstance(expected_questions_cadence, int):
        check(questions_cadence == expected_questions_cadence, "QUESTIONS_AUTOMATION_CADENCE_DRIFT", str(questions_automation_id))
    expected_questions_hash = questions_consumer.get("toml_sha256")
    if questions_path.is_file() and isinstance(expected_questions_hash, str) and expected_questions_hash:
        observed_questions_hash = f"sha256:{_sha256(questions_path)}"
        check(observed_questions_hash == expected_questions_hash, "QUESTIONS_AUTOMATION_HASH_DRIFT", str(questions_automation_id))
    questions_prompt = str(questions_live.get("prompt", "")).lower()
    check("00 atlas status" in questions_prompt, "QUESTIONS_STATUS_IDENTITY_MISSING", str(questions_automation_id))
    check(
        "must not duplicate routine status refreshes" in questions_prompt
        or "not a scheduler, product owner, status renderer" in questions_prompt,
        "QUESTIONS_STATUS_SUPPRESSION_MISSING",
        str(questions_automation_id),
    )
    if questions_consumer.get("identity_first_delta_gate") is True:
        check(
            "cheap delta gate only" in questions_prompt
            or "compare exact bound checkpoint/receipt identities" in questions_prompt,
            "QUESTIONS_IDENTITY_GATE_MISSING",
            str(questions_automation_id),
        )
        check(
            "do not call task-listing tools" in questions_prompt
            or "without broad reads, task-listing calls" in questions_prompt,
            "QUESTIONS_NO_DELTA_READ_BOUNDARY_MISSING",
            str(questions_automation_id),
        )
    if questions_consumer.get("routes_compact_material_delta_to_status") is True:
        check("route one compact delta-only message" in questions_prompt, "QUESTIONS_STATUS_DELTA_ROUTE_MISSING", str(questions_automation_id))
    if questions_consumer.get("routes_task_value_to_optimization") is True:
        check(
            "task-value finding" in questions_prompt and "02 atlas optimization & learning" in questions_prompt,
            "QUESTIONS_TASK_VALUE_ROUTE_MISSING",
            str(questions_automation_id),
        )
    if questions_consumer.get("two_strike_lane_switch") is True:
        check(
            "one blocked execution plus one unchanged same-class recheck" in questions_prompt
            and "switch lanes" in questions_prompt,
            "QUESTIONS_TWO_STRIKE_LANE_SWITCH_MISSING",
            str(questions_automation_id),
        )

    roles = manifest.get("roles")
    if not isinstance(roles, list):
        raise ConformanceError("workflow manifest roles must be an array")
    baseline_path = atlas_root / BASELINE_REF
    check(baseline_path.is_file(), "BASELINE_FILE_MISSING", BASELINE_REF)
    baseline_text = baseline_path.read_text(encoding="utf-8") if baseline_path.is_file() else ""
    baseline_normalized = " ".join(baseline_text.split())
    missing_anti_churn_markers = [marker for marker in ANTI_CHURN_BASELINE_MARKERS if marker not in baseline_normalized]
    check(
        not missing_anti_churn_markers,
        "ANTI_CHURN_BASELINE_MISSING",
        ",".join(missing_anti_churn_markers),
    )
    missing_common_release_markers = [
        marker for marker in COMMON_RELEASE_BASELINE_MARKERS if marker not in baseline_normalized
    ]
    check(
        not missing_common_release_markers,
        "COMMON_RELEASE_CONTROL_BASELINE_MISSING",
        ",".join(missing_common_release_markers),
    )
    governance_path = atlas_root / GOVERNANCE_REF
    check(governance_path.is_file(), "OPTIMIZATION_GOVERNANCE_MISSING", GOVERNANCE_REF)
    governance = _load_json(governance_path) if governance_path.is_file() else {}
    anti_churn = governance.get("anti_churn") if isinstance(governance, dict) else None
    check(isinstance(anti_churn, dict), "ANTI_CHURN_POLICY_MISSING", GOVERNANCE_REF)
    failure_gate = anti_churn.get("single_observation_failure_gate", {}) if isinstance(anti_churn, dict) else {}
    census_gate = anti_churn.get("census_identity_classes", {}) if isinstance(anti_churn, dict) else {}
    avoided = anti_churn.get("avoided_amplification_measurement", {}) if isinstance(anti_churn, dict) else {}
    check(
        failure_gate.get("canonical_observation_only") is True
        and failure_gate.get("default_state") == "recorded-no-fanout-no-promotion-no-implementation"
        and len(failure_gate.get("escalation_any_of", [])) == 3,
        "SINGLE_OBSERVATION_FANOUT_GATE_DRIFT",
        str(failure_gate),
    )
    check(
        census_gate.get("material_denominator") == "standing and user-visible task identities"
        and census_gate.get("auxiliary_denominator") == "ephemeral reviewer and bounded helper identities"
        and census_gate.get("ephemeral_only_material_delta_handoff") is False,
        "EPHEMERAL_IDENTITY_HANDOFF_GATE_DRIFT",
        str(census_gate),
    )
    observed_lower_bound = avoided.get("observed_lower_bound", {}) if isinstance(avoided, dict) else {}
    check(
        isinstance(observed_lower_bound.get("material_downstream_wakes_or_handoffs"), int)
        and observed_lower_bound.get("material_downstream_wakes_or_handoffs") >= 0
        and isinstance(observed_lower_bound.get("downstream_receipts_or_adoptions"), int)
        and observed_lower_bound.get("downstream_receipts_or_adoptions") >= 0,
        "ANTI_CHURN_MEASUREMENT_INVALID",
        str(observed_lower_bound),
    )
    common_controls = governance.get("common_release_safety_controls") if isinstance(governance, dict) else None
    check(isinstance(common_controls, dict), "COMMON_RELEASE_CONTROLS_MISSING", GOVERNANCE_REF)
    pc024 = common_controls.get("pc024", {}) if isinstance(common_controls, dict) else {}
    pc025 = common_controls.get("pc025", {}) if isinstance(common_controls, dict) else {}
    check(
        common_controls.get("decision_id") == "ACCEPT_BOUNDED_COMMON_CONTROL_R001"
        and common_controls.get("status") == "INSTALLED",
        "COMMON_RELEASE_CONTROL_DECISION_DRIFT",
        str(common_controls.get("decision_id") if isinstance(common_controls, dict) else None),
    )
    check(
        common_controls.get("local_installation_state") == "installed-and-verified-in-canonical-dirty-root"
        and common_controls.get("publication_state") == "current-main-candidate-unmerged",
        "COMMON_RELEASE_CONTROL_PUBLICATION_STATE_DRIFT",
        str(common_controls.get("publication_state") if isinstance(common_controls, dict) else None),
    )
    check(pc024.get("status") == "INSTALLED", "PC024_COMMON_CONTROL_NOT_INSTALLED", str(pc024))
    check(pc025.get("status") == "INSTALLED", "PC025_COMMON_CONTROL_NOT_INSTALLED", str(pc025))
    check(pc025.get("provider_effects") == 0, "PC025_PROVIDER_EFFECT_BOUNDARY_DRIFT", str(pc025.get("provider_effects")))
    common_control_refs = [
        common_controls.get("engineering_memory_ref"),
        common_controls.get("implementation_ref"),
        common_controls.get("focused_test_ref"),
    ] if isinstance(common_controls, dict) else []
    missing_common_control_refs = [
        str(ref) for ref in common_control_refs if not isinstance(ref, str) or not (atlas_root / ref).is_file()
    ]
    check(
        not missing_common_control_refs,
        "COMMON_RELEASE_CONTROL_ARTIFACT_MISSING",
        ",".join(missing_common_control_refs),
    )
    seed_ids = common_controls.get("engineering_memory_seed_ids", []) if isinstance(common_controls, dict) else []
    memory_policy_ref = "docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json"
    memory_policy_path = atlas_root / memory_policy_ref
    memory_policy = _load_json(memory_policy_path) if memory_policy_path.is_file() else {}
    observed_seed_ids = {
        seed.get("id")
        for seed in memory_policy.get("knowledge_seeds", [])
        if isinstance(seed, dict)
        and seed.get("status") == "accepted-atlas-root"
        and seed.get("playbook_promotion") == "installed-common-control"
    }
    check(
        isinstance(seed_ids, list) and len(seed_ids) == 4 and set(seed_ids) <= observed_seed_ids,
        "COMMON_RELEASE_ENGINEERING_MEMORY_PROMOTION_MISSING",
        ",".join(sorted(set(seed_ids) - observed_seed_ids)) if isinstance(seed_ids, list) else "invalid seed list",
    )
    covered_roles: list[str] = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        role_id = role.get("role_id")
        fragments = role.get("prompt_template", {}).get("fragments", [])
        if BASELINE_REF in fragments:
            covered_roles.append(str(role_id))
        else:
            check(False, "ROLE_BASELINE_MISSING", str(role_id))
    denominator = conformance.get("manifest_role_denominator")
    check(denominator == len(roles), "MANIFEST_ROLE_DENOMINATOR_STALE", f"ledger={denominator} manifest={len(roles)}")

    memory_refs = conformance.get("engineering_memory_gate_refs", [])
    if not isinstance(memory_refs, list):
        raise ConformanceError("engineering_memory_gate_refs must be an array")
    missing_memory_refs = [ref for ref in memory_refs if not (atlas_root / str(ref)).is_file()]
    check(not missing_memory_refs, "ENGINEERING_MEMORY_GATE_MISSING", ",".join(map(str, missing_memory_refs)))

    seam_refs = conformance.get("job_receipt_seam_refs", [])
    if not isinstance(seam_refs, list):
        raise ConformanceError("job_receipt_seam_refs must be an array")
    missing_seam_refs = [ref for ref in seam_refs if not (atlas_root / str(ref)).is_file()]
    check(not missing_seam_refs, "JOB_RECEIPT_SEAM_MISSING", ",".join(map(str, missing_seam_refs)))

    latest_receipt_ref = ledger.get("automation", {}).get("latest_active_successor_ref")
    latest_receipt_path = atlas_root / str(latest_receipt_ref)
    check(latest_receipt_path.is_file(), "LATEST_RECEIPT_MISSING", str(latest_receipt_ref))
    latest_receipt = _load_json(latest_receipt_path) if latest_receipt_path.is_file() else {}
    check(
        latest_receipt.get("contract_version") == "atlas.execution-receipt.v2",
        "LATEST_RECEIPT_CONTRACT_DRIFT",
        str(latest_receipt_ref),
    )
    latest_job_path = latest_receipt_path.with_name("job-envelope.json")
    check(latest_job_path.is_file(), "LATEST_JOB_MISSING", str(latest_job_path))
    latest_job = _load_json(latest_job_path) if latest_job_path.is_file() else {}
    check(
        latest_job.get("contract_version") == "atlas.job-envelope.v2",
        "LATEST_JOB_CONTRACT_DRIFT",
        str(latest_job_path),
    )

    integrator = entries[0]
    thread_id = integrator.get("thread_id")
    checkpoint_path = atlas_root / "runtime" / "atlas" / "thread-context" / str(thread_id) / "latest.json"
    check(checkpoint_path.is_file(), "CHECKPOINT_MISSING", str(thread_id))
    checkpoint = _load_json(checkpoint_path) if checkpoint_path.is_file() else {}
    payload = checkpoint.get("payload", {}) if isinstance(checkpoint, dict) else {}
    checkpoint_receipts = payload.get("receipts", []) if isinstance(payload, dict) else []
    latest_receipt_anchor = (
        f"{latest_receipt_ref}#sha256={_sha256(latest_receipt_path)}"
        if latest_receipt_path.is_file()
        else None
    )
    contains_latest_receipt = latest_receipt_ref in checkpoint_receipts or latest_receipt_anchor in checkpoint_receipts
    check(contains_latest_receipt, "CHECKPOINT_RECEIPT_STALE", str(latest_receipt_ref))
    recorded_at = payload.get("recorded_at") if isinstance(payload, dict) else None
    checkpoint_age_hours: float | None = None
    if isinstance(recorded_at, str):
        checkpoint_age_hours = max(0.0, (now - _parse_datetime(recorded_at)).total_seconds() / 3600)
        check(
            checkpoint_age_hours <= max_checkpoint_age_hours,
            "CHECKPOINT_TOO_OLD",
            f"age_hours={checkpoint_age_hours:.4f}",
        )
    else:
        check(False, "CHECKPOINT_TIMESTAMP_MISSING", str(thread_id))

    topology = ledger.get("worker_topology", {})
    lock = topology.get("program_task_lock", {}) if isinstance(topology, dict) else {}
    check(lock.get("task_count") == 4, "PROGRAM_TASK_LOCK_DRIFT", str(lock.get("task_count")))
    check(lock.get("additional_program_tasks_permitted") is False, "PROGRAM_TASK_WIDENING", "additional tasks must remain false")
    writer_scopes = [entry.get("writer_scope") for entry in entries]
    check(
        len(set(writer_scopes)) == 4 and all(isinstance(scope, str) and scope for scope in writer_scopes),
        "WRITER_SCOPE_COLLISION",
        "four unique writer scopes are required",
    )
    authority = conformance.get("authority_state")
    check(isinstance(authority, dict), "AUTHORITY_STATE_MISSING", "authority_state")
    if isinstance(authority, dict):
        check(authority.get("product_provider_effects_allowed") is False, "AUTHORITY_WIDENING", "product/provider effects")
        check(authority.get("decision_memory_repair_owned_elsewhere") is True, "DECISION_MEMORY_BOUNDARY_MISSING", "00 Questions ownership")

    unknowns = conformance.get("unknowns")
    check(isinstance(unknowns, list) and bool(unknowns), "EXPLICIT_UNKNOWNS_MISSING", "at least one UNKNOWN is required")
    if isinstance(unknowns, list):
        for index, unknown in enumerate(unknowns):
            valid_unknown = (
                isinstance(unknown, dict)
                and unknown.get("status") == "UNKNOWN"
                and isinstance(unknown.get("wake_condition"), str)
                and bool(unknown.get("wake_condition"))
            )
            check(valid_unknown, "UNKNOWN_NOT_ACTIONABLE", str(index))

    coverage = ledger.get("source_coverage", {})
    discovered = coverage.get("cross_source_tasks_discovered")
    indexed = coverage.get("metadata_indexed")
    inaccessible = coverage.get("inaccessible")
    reviewed = coverage.get("content_reviewed_tasks")
    remaining = coverage.get("remaining_content_review_tasks")
    check(
        all(isinstance(value, int) and value >= 0 for value in [discovered, indexed, inaccessible, reviewed, remaining]),
        "SOURCE_DENOMINATOR_INVALID",
        "coverage counts must be nonnegative integers",
    )
    if all(isinstance(value, int) for value in [discovered, indexed, inaccessible]):
        check(discovered == indexed + inaccessible, "SOURCE_DISCOVERY_ARITHMETIC_DRIFT", f"{discovered}!={indexed}+{inaccessible}")
    if all(isinstance(value, int) for value in [indexed, reviewed, remaining]):
        check(indexed == reviewed + remaining, "SOURCE_REVIEW_ARITHMETIC_DRIFT", f"{indexed}!={reviewed}+{remaining}")
    check(coverage.get("coverage_claim") == "partial-denominator-backed", "UNIVERSAL_COVERAGE_OVERCLAIM", str(coverage.get("coverage_claim")))

    return {
        "schema": "atlas.optimization-governance-conformance.v1",
        "recorded_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "valid": not errors,
        "errors": errors,
        "automation_topology": {
            "denominator": 4,
            "observed": len(live_automations),
            "active": sum(item.get("status") == "ACTIVE" for item in live_automations),
            "entries": live_automations,
        },
        "operator_visibility": {
            "task_count": visibility.get("task_count"),
            "thread_id": status_thread_id,
            "excluded_from_learning_program": visibility.get("excluded_from_learning_program"),
            "automation_id": status_automation_id,
            "automation_status": status_live.get("status"),
            "automation_target_thread_id": status_live.get("target_thread_id"),
            "automation_cadence_minutes": _rrule_minutes(str(status_live.get("rrule", ""))) if status_live else None,
            "projection_checks": projection_checks,
            "checkpoint_ref": status_checkpoint_ref,
            "questions_consumer_automation_id": questions_automation_id,
        },
        "bootstrap_baseline": {
            "baseline_ref": BASELINE_REF,
            "baseline_sha256": f"sha256:{_sha256(baseline_path)}" if baseline_path.is_file() else None,
            "manifest_role_denominator": len(roles),
            "roles_with_baseline": len(covered_roles),
            "role_ids": covered_roles,
        },
        "anti_churn": {
            "governance_ref": GOVERNANCE_REF,
            "single_observation_gate": failure_gate,
            "census_identity_gate": census_gate,
            "avoided_amplification": avoided,
            "baseline_markers_present": len(ANTI_CHURN_BASELINE_MARKERS) - len(missing_anti_churn_markers),
            "baseline_markers_required": len(ANTI_CHURN_BASELINE_MARKERS),
        },
        "common_release_safety_controls": {
            "decision_id": common_controls.get("decision_id") if isinstance(common_controls, dict) else None,
            "status": common_controls.get("status") if isinstance(common_controls, dict) else None,
            "local_installation_state": common_controls.get("local_installation_state") if isinstance(common_controls, dict) else None,
            "publication_state": common_controls.get("publication_state") if isinstance(common_controls, dict) else None,
            "pc024_status": pc024.get("status"),
            "pc025_status": pc025.get("status"),
            "provider_effects": pc025.get("provider_effects"),
            "required_artifact_count": len(common_control_refs),
            "present_artifact_count": len(common_control_refs) - len(missing_common_control_refs),
            "engineering_memory_seed_count": len(observed_seed_ids & set(seed_ids)) if isinstance(seed_ids, list) else 0,
            "baseline_markers_present": len(COMMON_RELEASE_BASELINE_MARKERS) - len(missing_common_release_markers),
            "baseline_markers_required": len(COMMON_RELEASE_BASELINE_MARKERS),
        },
        "engineering_memory": {
            "required_refs": len(memory_refs),
            "present_refs": len(memory_refs) - len(missing_memory_refs),
            "missing_refs": missing_memory_refs,
        },
        "job_receipt_seam": {
            "required_refs": len(seam_refs),
            "present_refs": len(seam_refs) - len(missing_seam_refs),
            "latest_receipt_ref": latest_receipt_ref,
            "latest_job_ref": str(latest_job_path.relative_to(atlas_root)).replace("\\", "/") if latest_job_path.is_file() else None,
        },
        "checkpoint": {
            "ref": str(checkpoint_path.relative_to(atlas_root)).replace("\\", "/"),
            "recorded_at": recorded_at,
            "age_hours": round(checkpoint_age_hours, 4) if checkpoint_age_hours is not None else None,
            "max_age_hours": max_checkpoint_age_hours,
            "contains_latest_receipt": contains_latest_receipt,
        },
        "writer_authority": {
            "program_task_count": lock.get("task_count"),
            "additional_program_tasks_permitted": lock.get("additional_program_tasks_permitted"),
            "unique_writer_scopes": len(set(writer_scopes)),
            "product_provider_effects_allowed": authority.get("product_provider_effects_allowed") if isinstance(authority, dict) else None,
            "decision_memory_repair_owned_elsewhere": authority.get("decision_memory_repair_owned_elsewhere") if isinstance(authority, dict) else None,
        },
        "coverage": {
            "discovered": discovered,
            "indexed": indexed,
            "content_reviewed": reviewed,
            "remaining_content_review": remaining,
            "inaccessible": inaccessible,
            "claude_metadata_pending": coverage.get("local_claude_files_pending_metadata_normalization"),
            "vendor_format_pending": coverage.get("vendor_import_files_pending_format_classification"),
            "claim": coverage.get("coverage_claim"),
        },
        "unknowns": unknowns if isinstance(unknowns, list) else [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ATLAS optimization governance conformance.")
    parser.add_argument("--atlas-root", type=Path, default=ROOT)
    parser.add_argument(
        "--automations-root",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "automations",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("runtime/atlas/knowledge-expansion/unified-optimization-integration-r001/integration-ledger.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/registry/ATLAS-WORKFLOW-MANIFEST.v1.json"),
    )
    parser.add_argument("--now", type=str)
    parser.add_argument("--max-checkpoint-age-hours", type=float, default=24.0)
    args = parser.parse_args(argv)

    atlas_root = args.atlas_root.resolve()
    ledger_path = args.ledger if args.ledger.is_absolute() else atlas_root / args.ledger
    manifest_path = args.manifest if args.manifest.is_absolute() else atlas_root / args.manifest
    now = _parse_datetime(args.now) if args.now else datetime.now(timezone.utc)
    try:
        result = validate_conformance(
            atlas_root,
            args.automations_root.resolve(),
            ledger_path.resolve(),
            manifest_path.resolve(),
            now,
            args.max_checkpoint_age_hours,
        )
    except ConformanceError as error:
        result = {
            "schema": "atlas.optimization-governance-conformance.v1",
            "recorded_at": now.isoformat().replace("+00:00", "Z"),
            "valid": False,
            "errors": [{"code": "CONFORMANCE_INPUT_INVALID", "detail": str(error)}],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    sys.exit(main())
