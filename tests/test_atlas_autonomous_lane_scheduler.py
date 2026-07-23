from __future__ import annotations

import copy
import io
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.atlas import autonomous_lane_scheduler as scheduler
from ops.atlas import marker_aware_next_packet_planner as planner


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _program_payload() -> dict[str, object]:
    return {
        "schema_version": scheduler.PROGRAM_SCHEMA_VERSION,
        "name": "atlas-root-autocomplete",
        "max_docs_only_streak": 2,
        "max_file_overlap_risk": "medium",
        "allow_reselection": True,
        "max_parallel_writers": 4,
        "max_parallel_read_only": 2,
        "allowed_markers": [
            "Cortex Simulation Substrate Readiness",
            "Vercel Platform Observability Governance",
            "Cortex Dual-Mode Replacement Readiness",
            "AI Long-Run Batch Orchestration",
            "AI Repetition-to-Automation Pipeline",
            "Cortex Readiness",
            "Playbook Everywhere + Cortex Interface",
            "AI Work Session Stability & Auto-Sync Loop",
        ],
        "excluded_markers": ["Sandbox Simulation Readiness"],
        "forbidden_owner_lanes": ["fitness", "mazer", "discordos", "foundation", "trove", "playbook", "stream"],
        "phase_priority": [
            "worker_reconciliation",
            "worker_implementation",
            "implementation_readiness",
            "prompt_pack",
            "first_implementation_admission",
            "contract_freeze",
            "selector",
        ],
        "stop_on": ["critical_validation", "error_validation", "owner_repo_required", "secret_required", "deploy_required", "no_safe_candidate"],
    }


def _standing_packet(
    packet_id: str,
    *,
    role_id: str,
    repository: str,
    writer_scope: str,
    dependencies: list[str] | None = None,
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "packet": f"Execute {packet_id}",
        "state": "READY",
        "logical_role_id": role_id,
        "repository": repository,
        "writer_scope": writer_scope,
        "execution_class": "repo_worktree",
        "runtime_thread_id": "019f0000-0000-7000-8000-000000000001",
        "runtime_status": "idle",
        "dependencies": dependencies or [],
        "authority": {
            "event_id": "onv1_" + "a" * 64,
            "payload_digest": "sha256:" + "b" * 64,
        },
    }


def _envelope(
    payload: dict[str, object],
    *,
    idempotency_key: str,
    source_role_id: str | None = None,
) -> dict[str, object]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    envelope = {
        "schema": "atlas.workflow.envelope.v1",
        "kind": "EVENT",
        "event_id": "onv1_" + digest,
        "payload_digest": "sha256:" + digest,
        "idempotency_key": idempotency_key,
        "payload": payload,
    }
    if source_role_id is not None:
        envelope["source_role_id"] = source_role_id
    return envelope


def _standing_local_source_payload() -> dict[str, object]:
    paths = ["src/feature.py", "tests/test_feature.py"]
    return {
        "canonical_lifecycle_state": "READY",
        "packet_id": "owner-local-source-preparation",
        "objective": "Prepare the bounded owner source and tests locally; hold publication.",
        "logical_role_id": "owner.example",
        "repository": "fawxzzy/example",
        "writer_scope": "repo.example.local-preparation",
        "execution_class": "repo_worktree",
        "authority_class": scheduler.STANDING_LOCAL_SOURCE_PREPARATION,
        "source_preparation": {
            "mode": "LOCAL_ONLY_UNSTAGED",
            "publication": "HELD",
            "parent_commit": "1" * 40,
            "path_allowlist": paths,
        },
        "resource_claims": {
            "files": paths,
            "worktrees": ["example-local-preparation"],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        },
    }


def _bindings(*items: tuple[str, str, str]) -> dict[str, object]:
    return {
        "bindings": [
            {
                "role_id": role_id,
                "current_runtime_id": runtime_id,
                "runtime_status": status,
                "host_id": "local",
                "archived": False,
            }
            for role_id, runtime_id, status in items
        ]
    }


def _standardized_envelope(
    payload: dict[str, object],
    *,
    role_id: str,
    runtime_thread_id: str,
    idempotency_key: str,
    source_role_id: str = "atlas.release-control-plane",
    host_id: str = "local",
    owner_role_id: str | None = None,
    owner_runtime_thread_id: str | None = None,
) -> dict[str, object]:
    payload = copy.deepcopy(payload)
    payload["policy_id"] = scheduler.WORKFLOW_STANDARDIZATION_POLICY_ID
    payload["logical_role_id"] = role_id
    envelope = _envelope(
        payload,
        idempotency_key=idempotency_key,
        source_role_id=source_role_id,
    )
    envelope["target_role_id"] = role_id
    envelope["owner_return"] = {
        "logical_role_id": owner_role_id or role_id,
        "thread_id": owner_runtime_thread_id or runtime_thread_id,
        "host_id": host_id,
    }
    return envelope


def _standardized_ready_payload(
    packet_id: str,
    *,
    role_id: str,
    repository: str,
    writer_scope: str,
    worktree: str,
    files: list[str] | None = None,
) -> dict[str, object]:
    return {
        "canonical_lifecycle_state": "READY",
        "packet_id": packet_id,
        "objective": f"Execute {packet_id} through the canonical scheduler.",
        "logical_role_id": role_id,
        "repository": repository,
        "writer_scope": writer_scope,
        "execution_class": "repo_worktree",
        "worktree": worktree,
        "resource_claims": {
            "files": files or ["ops/atlas/**"],
            "worktrees": [worktree],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        },
    }


def _scheduler_report(
    program: dict[str, object],
    *,
    preflight_report: dict[str, object] | None = None,
) -> dict[str, object]:
    with patch.object(scheduler, "_branch_state", return_value=("main", "a" * 40)):
        with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
            return scheduler.build_report(
                root=Path("C:/ATLAS"),
                program=program,
                max_candidates=30,
                preflight_report=preflight_report or _preflight_payload(),
                selector_report=_selector_payload(),
                planner_report=_planner_payload([]),
            )


def _recovery_ready_program() -> dict[str, object]:
    packet = _standing_packet(
        "fitness-source",
        role_id="owner.fitness",
        repository="fawxzzy/fitness",
        writer_scope="repo.fitness.source",
    )
    packet["state"] = scheduler.RECOVERY_READY_STATE
    packet["runtime_thread_id"] = "fitness-thread"
    packet["dispatch_reservation"] = {
        "reservation_id": "rsrv-fitness-source",
        "runtime_thread_id": "fitness-thread",
    }
    packet["resume_authority"] = {
        "event_id": "onv1_" + "d" * 64,
        "payload_digest": "sha256:" + "d" * 64,
        "reservation_id": "rsrv-fitness-source",
        "current_delivered_turn_id": "blocked-turn",
    }
    program = _program_payload()
    program["standing_packets"] = [packet]
    program["active_leases"] = [
        {
            "reservation_id": "rsrv-fitness-source",
            "packet_id": "fitness-source",
            "logical_role_id": "owner.fitness",
            "runtime_thread_id": "fitness-thread",
            "writer_scope": "repo.fitness.source",
            "repository": "fawxzzy/fitness",
            "execution_class": "repo_worktree",
            "resource_claims": {"files": ["src/feature.py"], "worktrees": ["fitness-worktree"]},
            "status": "recovery-required",
        }
    ]
    program["delivery_intents"] = [
        {
            "reservation_id": "rsrv-fitness-source",
            "packet_id": "fitness-source",
            "logical_role_id": "owner.fitness",
            "runtime_thread_id": "fitness-thread",
            "writer_scope": "repo.fitness.source",
            "event_id": packet["resume_authority"]["event_id"],
            "payload_digest": packet["resume_authority"]["payload_digest"],
            "status": "recovery-required",
            "turn_id": None,
            "recovery_superseded_turn_id": "blocked-turn",
        }
    ]
    return program


def _web_release_packet_payload(packet_id: str, *, replaces_packet_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "canonical_lifecycle_state": "READY",
        "packet_id": packet_id,
        "objective": "Review and guard the exact FawxzzyWeb PR source merge.",
        "logical_role_id": "atlas.release-control-plane",
        "repository": "fawxzzy/FawxzzyWeb",
        "writer_scope": "github.fawxzzy.fawxzzyweb.pr30.guarded-source-merge",
        "execution_class": "external_mutation",
        "protected_surface_authorized": True,
        "dependencies": [],
        "resource_claims": {
            "files": [],
            "worktrees": [],
            "ports": [],
            "browsers": [],
            "external_writers": ["github:fawxzzy/FawxzzyWeb#30:merge"],
        },
    }
    if replaces_packet_id is not None:
        payload["replaces_packet_id"] = replaces_packet_id
    return payload


def _orphaned_web_delivery_program() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ready = _envelope(
        _web_release_packet_payload("fawxzzyweb-pr30-guarded-source-merge"),
        idempotency_key="fawxzzyweb-pr30-original",
        source_role_id="owner.fawxzzyweb",
    )
    bindings = _bindings(("atlas.release-control-plane", "release-control-thread", "idle"))
    program, findings = scheduler.reconcile_runtime_program(
        program=_program_payload(),
        bindings_payload=bindings,
        envelopes=[ready],
    )
    if findings:
        raise AssertionError(findings)
    report = scheduler.build_report(
        root=Path("atlas-root-fixture"),
        program=program,
        max_candidates=30,
        preflight_report=_preflight_payload(),
        selector_report=_selector_payload(),
        planner_report=_planner_payload([]),
    )
    program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
    intent = program["delivery_intents"][0]
    program, findings = scheduler.apply_delivery_results(
        program=program,
        results=[
            {
                "reservation_id": reservations[0]["reservation_id"],
                "packet_id": intent["packet_id"],
                "runtime_thread_id": intent["runtime_thread_id"],
                "event_id": intent["event_id"],
                "payload_digest": intent["payload_digest"],
                "status": "RECOVERY_REQUIRED",
            }
        ],
    )
    if findings:
        raise AssertionError(findings)
    return program, bindings, ready


def _web_recovery_absence_envelope(
    *,
    program: dict[str, object],
    successor: dict[str, object],
    evidence_updates: dict[str, object] | None = None,
    payload_updates: dict[str, object] | None = None,
) -> dict[str, object]:
    packet = program["standing_packets"][0]
    intent = program["delivery_intents"][0]
    evidence: dict[str, object] = {
        "schema": scheduler.RECOVERY_ABSENCE_EVIDENCE_SCHEMA,
        "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
        "target_history_receipt_event_id": "onv1_" + "7" * 64,
        "target_history_receipt_payload_digest": "sha256:" + "6" * 64,
        "history_complete": True,
        "original_call_state": scheduler.RECOVERY_ABSENCE_CALL_STATE,
        "reservation_id": intent["reservation_id"],
        "packet_id": intent["packet_id"],
        "writer_scope": intent["writer_scope"],
        "runtime_thread_id": intent["runtime_thread_id"],
        "event_id": intent["event_id"],
        "payload_digest": intent["payload_digest"],
        "matching_turn_ids": [],
        "active_matching_turn_ids": [],
        "effects_match_intent": False,
    }
    if evidence_updates:
        evidence.update(evidence_updates)
    successor_payload = successor["payload"]
    payload: dict[str, object] = {
        "event_class": scheduler.RECOVERY_ABSENCE_EVENT_CLASS,
        "canonical_lifecycle_state": "SUPERSEDED_RECOVERY_ABSENCE_PROVEN",
        "terminal": True,
        "packet_id": packet["packet_id"],
        "writer_scope": packet["writer_scope"],
        "reservation_id": intent["reservation_id"],
        "superseded_by_packet_id": successor_payload["packet_id"],
        "successor_event_id": successor["event_id"],
        "successor_payload_digest": successor["payload_digest"],
        "delivery_recovery_evidence": evidence,
        "delivery_recovery_evidence_digest": scheduler._canonical_payload_digest(evidence),
    }
    if payload_updates:
        payload.update(payload_updates)
    envelope = _envelope(
        payload,
        idempotency_key="fawxzzyweb-pr30-recovery-absence",
        source_role_id="atlas.workflow-architect",
    )
    envelope["kind"] = scheduler.RECOVERY_ABSENCE_ENVELOPE_KIND
    return envelope


def _preflight_payload(*, critical: int = 0, error: int = 0) -> dict[str, object]:
    return {
        "status": "ok" if critical == 0 and error == 0 else "blocker",
        "validation": {"critical": critical, "error": error, "warning": 0, "info": 0},
        "projection_freshness": {"status": "ok", "inventory_matches_live_working_set": True},
        "local_residue": {"root_dirty_paths": []},
        "markers": {"active_lane": "Sandbox Simulation Readiness", "active_lane_is_held": True},
    }


def _selector_payload(*, active_lane_is_held: bool = True, action: str = "hold_current_lane", current_packet: str | None = None) -> dict[str, object]:
    return {
        "selected_marker": "Sandbox Simulation Readiness",
        "active_lane_is_held": active_lane_is_held,
        "operator_action": action,
        "selected_current_packet": current_packet,
        "selected_current_packet_mode": "docs-only root-bounded hold",
    }


def _planner_payload(items: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": planner.SCHEMA_VERSION,
        "status": "ok",
        "selected_marker": items[0]["marker"] if items else None,
        "selected_packet": items[0]["packet"] if items else None,
        "candidate_count": len(items),
        "candidate_scores": items,
    }


class AutonomousLaneSchedulerTests(unittest.TestCase):
    def test_bridge_findings_are_deduplicated_by_complete_identity(self) -> None:
        first = scheduler._finding("one", "same", packet_id="packet")
        second = copy.deepcopy(first)
        distinct = scheduler._finding("one", "same", packet_id="other")

        self.assertEqual([first, distinct], scheduler._dedupe_findings([first, second, distinct]))

    def test_work_program_schema_freezes_delivery_and_lease_state(self) -> None:
        schema = json.loads((scheduler.ROOT / "schemas/atlas.autonomous-work-program.v2.json").read_text(encoding="utf-8"))

        self.assertEqual("atlas.autonomous-work-program.v2", schema["$id"])
        self.assertEqual(
            {
                "schema_version",
                "revision",
                "source_snapshot_digest",
                "scheduler_authority",
                "standing_packets",
                "active_leases",
                "scope_holds",
                "delivery_intents",
                "completed_packets",
                "completed_receipts",
                "released_leases",
                "processed_events",
            },
            set(schema["required"]),
        )
        self.assertEqual(
            ["prepared", "delivered", "host-unavailable", "recovery-required"],
            schema["properties"]["delivery_intents"]["items"]["properties"]["status"]["enum"],
        )
        self.assertEqual(scheduler.CANONICAL_SCHEDULER_AUTHORITY, schema["properties"]["scheduler_authority"]["const"])
        self.assertIn(
            "external_mutation",
            schema["properties"]["standing_packets"]["items"]["properties"]["execution_class"]["enum"],
        )
        standing = schema["properties"]["standing_packets"]["items"]
        self.assertIn("SUPERSEDED", standing["properties"]["state"]["enum"])
        self.assertIn("HOST_UNAVAILABLE", standing["properties"]["state"]["enum"])
        self.assertEqual(
            sorted(scheduler.TERMINAL_SUCCESSORS),
            sorted(schema["$defs"]["terminal_successor"]["enum"]),
        )
        self.assertFalse(schema["$defs"]["owner_return"]["additionalProperties"])
        self.assertFalse(schema["$defs"]["execution_target"]["additionalProperties"])
        self.assertEqual("string", schema["$defs"]["execution_target"]["properties"]["host_id"]["type"])
        self.assertEqual(1, schema["$defs"]["execution_target"]["properties"]["host_id"]["minLength"])
        self.assertIn("transport_digest", schema["properties"]["processed_events"]["items"]["properties"])
        self.assertIn("transport_digest", standing["properties"]["authority"]["properties"])
        self.assertEqual(
            ["target_role_id", "execution_target", "owner_return", "owner_return_state"],
            standing["allOf"][1]["then"]["required"],
        )
        self.assertEqual(
            [scheduler.STANDING_LOCAL_SOURCE_PREPARATION],
            standing["properties"]["authority_class"]["enum"],
        )
        self.assertEqual(32, standing["properties"]["source_preparation"]["properties"]["path_allowlist"]["maxItems"])
        self.assertEqual(
            ["source_role_id", "source_preparation"],
            standing["allOf"][0]["then"]["required"],
        )
        self.assertEqual(
            {
                "reservation_id",
                "packet_id",
                "writer_scope",
                "repository",
                "execution_class",
                "resource_claims",
                "status",
            },
            set(schema["properties"]["active_leases"]["items"]["required"]),
        )

    def test_standardized_ready_packet_normalizes_exact_worktree_and_wakes_once(self) -> None:
        worktree = "worktrees/atlas-discordos-runtime-binding-001"
        payload = _standardized_ready_payload(
            "discordos-wave-c-publication",
            role_id="atlas.workflow-architect",
            repository="fawxzzy/ATLAS",
            writer_scope="repo.fawxzzy.ATLAS.discordos-wave-c",
            worktree=worktree,
            files=["docs/registry/ATLAS-WORKFLOW-LIVE-MAPPING.v1.json"],
        )
        payload["resource_claims"]["worktrees"] = worktree
        payload["reservation_id"] = "rsrv_" + "f" * 64
        envelope = _standardized_envelope(
            payload,
            role_id="atlas.workflow-architect",
            runtime_thread_id="architect-thread",
            idempotency_key="discordos-wave-c-publication",
            source_role_id="atlas.main",
        )
        envelope["consumers"] = ["atlas.inbox", "atlas.main"]

        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("atlas.workflow-architect", "architect-thread", "idle")),
            envelopes=[envelope],
            root=Path("C:/ATLAS"),
        )
        packet = program["standing_packets"][0]
        self.assertEqual([], findings)
        self.assertEqual([worktree], packet["resource_claims"]["worktrees"])
        self.assertEqual("TOP_LEVEL_WORKTREE_BOUND_LEGACY_SCALAR", packet["resource_claim_normalization"])
        self.assertEqual("SUPERSEDED_BEFORE_RESERVE_BY_CANONICAL_SCHEDULER", packet["reservation_reconciliation"])
        self.assertEqual(
            {"logical_role_id": "atlas.workflow-architect", "thread_id": "architect-thread", "host_id": "local"},
            packet["execution_target"],
        )
        self.assertEqual("PENDING", packet["owner_return_state"])
        self.assertRegex(packet["authority"]["transport_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(packet["authority"]["transport_digest"], program["processed_events"][0]["transport_digest"])

        replayed, replay_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("atlas.workflow-architect", "architect-thread", "idle")),
            envelopes=[envelope],
            root=Path("C:/ATLAS"),
        )
        self.assertEqual([], replay_findings)
        self.assertEqual(1, len(replayed["standing_packets"]))
        self.assertEqual(1, len(replayed["processed_events"]))

        report = _scheduler_report(replayed, preflight_report=_preflight_payload(error=1))
        self.assertEqual(["discordos-wave-c-publication"], [job["packet_id"] for job in report["selected_jobs"]])
        reserved, reservations = scheduler.reserve_selected_jobs(program=replayed, report=report)
        expected_reservation = scheduler._deterministic_reservation_id(reserved["standing_packets"][0])
        self.assertEqual(expected_reservation, reservations[0]["reservation_id"])
        self.assertNotEqual(payload["reservation_id"], reservations[0]["reservation_id"])

        second = _scheduler_report(reserved)
        self.assertEqual([], [job for job in second["selected_jobs"] if job.get("source") == "standing_task"])
        self.assertEqual(1, len(reserved["delivery_intents"]))
        self.assertEqual(1, len(reserved["active_leases"]))

    def test_program_loader_rejects_a_second_scheduler_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relative = "tmp/atlas/program.json"
            valid = scheduler._initial_runtime_program()
            _write(root / relative, json.dumps(valid, indent=2) + "\n")
            loaded, errors = scheduler.load_program(root, relative)
            self.assertIsNotNone(loaded)
            self.assertEqual([], errors)

            invalid = copy.deepcopy(valid)
            invalid["scheduler_authority"]["logical_role_id"] = "atlas.release-control-plane"
            _write(root / relative, json.dumps(invalid, indent=2) + "\n")
            _, invalid_errors = scheduler.load_program(root, relative)
            self.assertEqual("scheduler_authority_mismatch", invalid_errors[0]["code"])

    def test_cross_role_execution_targets_preserve_exact_owner_callback(self) -> None:
        routes = [
            ("atlas.release-control-plane", "release-thread"),
            ("manual.messages", "manual-thread"),
            ("component.discordos", "discordos-thread"),
        ]
        for target_role, target_thread in routes:
            with self.subTest(target_role=target_role):
                packet_id = "route-" + target_role.replace(".", "-")
                payload = _standardized_ready_payload(
                    packet_id,
                    role_id=target_role,
                    repository="fawxzzy/ATLAS",
                    writer_scope=f"read.route.{target_role}",
                    worktree=f"isolated-{packet_id}",
                )
                payload["execution_class"] = "read_only"
                envelope = _standardized_envelope(
                    payload,
                    role_id=target_role,
                    runtime_thread_id=target_thread,
                    owner_role_id="atlas.workflow-architect",
                    owner_runtime_thread_id="architect-thread",
                    idempotency_key=packet_id,
                    source_role_id="atlas.workflow-architect",
                )
                program, findings = scheduler.reconcile_runtime_program(
                    program=_program_payload(),
                    bindings_payload=_bindings(
                        (target_role, target_thread, "idle"),
                        ("atlas.workflow-architect", "architect-thread", "idle"),
                    ),
                    envelopes=[envelope],
                )
                self.assertEqual([], findings)
                packet = program["standing_packets"][0]
                self.assertEqual(target_role, packet["execution_target"]["logical_role_id"])
                self.assertEqual(target_thread, packet["execution_target"]["thread_id"])
                self.assertEqual("atlas.workflow-architect", packet["owner_return"]["logical_role_id"])
                self.assertEqual("architect-thread", packet["owner_return"]["thread_id"])

                report = _scheduler_report(program)
                self.assertEqual([packet_id], [job["packet_id"] for job in report["selected_jobs"]])
                reserved, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
                intent = reserved["delivery_intents"][0]
                self.assertEqual(target_thread, reservations[0]["runtime_thread_id"])
                self.assertEqual(packet["execution_target"], intent["execution_target"])
                self.assertEqual(packet["owner_return"], intent["owner_return"])

                result = {
                    "reservation_id": intent["reservation_id"],
                    "packet_id": packet_id,
                    "runtime_thread_id": target_thread,
                    "writer_scope": packet["writer_scope"],
                    "event_id": envelope["event_id"],
                    "payload_digest": envelope["payload_digest"],
                    "transport_digest": packet["authority"]["transport_digest"],
                    "status": "DELIVERED",
                    "turn_id": f"turn-{packet_id}",
                    "owner_return": envelope["owner_return"],
                    "delivery_proof": {
                        "turn_id": f"turn-{packet_id}",
                        "tool_receipt_id": f"tool-{packet_id}",
                        "dedupe_result": "FIRST_DELIVERY",
                    },
                }
                settled, result_findings = scheduler.apply_delivery_results(program=reserved, results=[result])
                self.assertEqual([], result_findings)
                self.assertEqual("DELIVERED", settled["standing_packets"][0]["execution_target_state"])
                self.assertEqual("PENDING", settled["standing_packets"][0]["owner_return_state"])
                self.assertEqual(target_role, settled["standing_packets"][0]["current_tracker_role_id"])

    def test_cross_role_owner_return_must_settle_before_terminal_completion(self) -> None:
        packet_id = "route-release-owner-return"
        payload = _standardized_ready_payload(
            packet_id,
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.release.owner-return",
            worktree="isolated-route-release-owner-return",
        )
        payload["execution_class"] = "read_only"
        envelope = _standardized_envelope(
            payload,
            role_id="atlas.release-control-plane",
            runtime_thread_id="release-thread",
            owner_role_id="atlas.workflow-architect",
            owner_runtime_thread_id="architect-thread",
            idempotency_key=packet_id,
            source_role_id="atlas.workflow-architect",
        )
        bindings = _bindings(
            ("atlas.release-control-plane", "release-thread", "idle"),
            ("atlas.workflow-architect", "architect-thread", "idle"),
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=bindings,
            envelopes=[envelope],
        )
        self.assertEqual([], findings)
        report = _scheduler_report(program)
        reserved, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        reservation_id = reservations[0]["reservation_id"]
        intent = reserved["delivery_intents"][0]
        execution_result = {
            "reservation_id": reservation_id,
            "packet_id": packet_id,
            "runtime_thread_id": "release-thread",
            "writer_scope": payload["writer_scope"],
            "event_id": envelope["event_id"],
            "payload_digest": envelope["payload_digest"],
            "transport_digest": intent["transport_digest"],
            "status": "DELIVERED",
            "turn_id": "release-turn",
            "owner_return": envelope["owner_return"],
            "delivery_proof": {
                "turn_id": "release-turn",
                "tool_receipt_id": "tool-release-turn",
                "dedupe_result": "FIRST_DELIVERY",
            },
        }
        delivered, delivery_findings = scheduler.apply_delivery_results(
            program=reserved,
            results=[execution_result],
        )
        self.assertEqual([], delivery_findings)
        self.assertEqual("PENDING", delivered["standing_packets"][0]["owner_return_state"])

        terminal = _envelope(
            {
                "terminal": True,
                "terminal_successor": "TERMINAL_DOMAIN",
                "canonical_lifecycle_state": "COMPLETED",
                "packet_id": packet_id,
                "writer_scope": payload["writer_scope"],
                "reservation_id": reservation_id,
                "turn_id": "release-turn",
            },
            idempotency_key="route-release-terminal",
            source_role_id="atlas.release-control-plane",
        )
        premature, premature_findings = scheduler.reconcile_runtime_program(
            program=copy.deepcopy(delivered),
            bindings_payload=bindings,
            envelopes=[terminal],
        )
        self.assertIn(
            "terminal_owner_return_delivery_required",
            [finding["code"] for finding in premature_findings],
        )
        self.assertEqual(1, len(premature["standing_packets"]))
        self.assertEqual(0, len(premature["completed_receipts"]))

        callback_result = {
            **execution_result,
            "delivery_phase": "OWNER_RETURN",
            "runtime_thread_id": "architect-thread",
            "turn_id": "architect-owner-turn",
            "delivery_proof": {
                "turn_id": "architect-owner-turn",
                "tool_receipt_id": "tool-architect-owner-turn",
                "dedupe_result": "FIRST_DELIVERY",
            },
        }
        returned, return_findings = scheduler.apply_delivery_results(
            program=premature,
            results=[callback_result],
        )
        self.assertEqual([], return_findings)
        self.assertEqual("DELIVERED", returned["standing_packets"][0]["owner_return_state"])
        self.assertEqual("architect-owner-turn", returned["standing_packets"][0]["owner_return_turn_id"])
        self.assertEqual("atlas.workflow-architect", returned["standing_packets"][0]["current_tracker_role_id"])

        duplicate_callback = copy.deepcopy(callback_result)
        duplicate_callback["delivery_proof"]["dedupe_result"] = "DUPLICATE_SUPPRESSED"
        returned, duplicate_findings = scheduler.apply_delivery_results(
            program=returned,
            results=[duplicate_callback],
        )
        self.assertEqual([], duplicate_findings)
        self.assertEqual(
            "FIRST_DELIVERY",
            returned["standing_packets"][0]["owner_return_proof"]["dedupe_result"],
        )

        completed, completion_findings = scheduler.reconcile_runtime_program(
            program=returned,
            bindings_payload=bindings,
            envelopes=[terminal],
        )
        self.assertEqual([], completion_findings)
        self.assertEqual([], completed["standing_packets"])
        self.assertEqual("architect-owner-turn", completed["completed_receipts"][0]["owner_return_turn_id"])
        self.assertEqual(
            "tool-architect-owner-turn",
            completed["completed_receipts"][0]["owner_return_proof"]["tool_receipt_id"],
        )

    def test_plural_policy_ids_enforce_standardized_successor_and_epoch_binding(self) -> None:
        payload = _standardized_ready_payload(
            "plural-policy",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.release.plural-policy",
            worktree="isolated-plural-policy",
        )
        payload["execution_class"] = "read_only"
        payload["policy_ids"] = [
            scheduler.WORKFLOW_STANDARDIZATION_POLICY_ID,
            "ATLAS-UNIFIED-BLOCKER-MANUAL-ROUTING-20260722-001",
        ]
        envelope = _envelope(
            payload,
            idempotency_key="plural-policy",
            source_role_id="atlas.workflow-architect",
        )
        envelope["target_role_id"] = "atlas.release-control-plane"
        envelope["owner_return"] = {
            "logical_role_id": "atlas.workflow-architect",
            "thread_id": "architect-v1",
            "host_id": "local",
        }
        bindings_v1 = _bindings(
            ("atlas.release-control-plane", "release-v1", "idle"),
            ("atlas.workflow-architect", "architect-v1", "idle"),
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=bindings_v1,
            envelopes=[envelope],
        )
        self.assertEqual([], findings)
        self.assertEqual(sorted(payload["policy_ids"]), program["standing_packets"][0]["policy_ids"])

        terminal_successor, terminal_error = scheduler._resolve_terminal_successor(
            {
                "terminal": True,
                "canonical_lifecycle_state": "COMPLETED",
                "policy_ids": payload["policy_ids"],
            }
        )
        self.assertIsNone(terminal_successor)
        self.assertEqual("terminal_successor_required", terminal_error["code"])

        drifted, drift_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(
                ("atlas.release-control-plane", "release-v2", "idle"),
                ("atlas.workflow-architect", "architect-v2", "idle"),
            ),
            envelopes=[],
        )
        self.assertEqual([], drift_findings)
        self.assertEqual("binding_drift", drifted["standing_packets"][0]["runtime_status"])
        self.assertEqual("UNKNOWN", drifted["standing_packets"][0]["owner_return_state"])
        report = _scheduler_report(drifted)
        self.assertEqual([], report["selected_jobs"])

    def test_standardized_execution_target_requires_current_host_identity(self) -> None:
        payload = _standardized_ready_payload(
            "missing-target-host",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.release.missing-host",
            worktree="isolated-missing-target-host",
        )
        payload["execution_class"] = "read_only"
        envelope = _standardized_envelope(
            payload,
            role_id="atlas.release-control-plane",
            runtime_thread_id="release-thread",
            idempotency_key="missing-target-host",
        )
        bindings = _bindings(("atlas.release-control-plane", "release-thread", "idle"))
        del bindings["bindings"][0]["host_id"]

        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=bindings,
            envelopes=[envelope],
        )
        self.assertIn("execution_target_binding_mismatch", [finding["code"] for finding in findings])
        self.assertIsNone(program["standing_packets"][0]["execution_target"])
        report = _scheduler_report(program)
        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("execution_target_unknown", report["blocked_candidates"][0]["blocked_reason"])

    def test_persisted_callback_binding_host_loss_fails_closed(self) -> None:
        packet_id = "callback-host-loss"
        payload = _standardized_ready_payload(
            packet_id,
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.release.callback-host-loss",
            worktree="isolated-callback-host-loss",
        )
        payload["execution_class"] = "read_only"
        envelope = _standardized_envelope(
            payload,
            role_id="atlas.release-control-plane",
            runtime_thread_id="release-thread",
            owner_role_id="atlas.workflow-architect",
            owner_runtime_thread_id="architect-thread",
            idempotency_key=packet_id,
            source_role_id="atlas.workflow-architect",
        )
        bindings = _bindings(
            ("atlas.release-control-plane", "release-thread", "idle"),
            ("atlas.workflow-architect", "architect-thread", "idle"),
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=bindings,
            envelopes=[envelope],
        )
        self.assertEqual([], findings)

        bindings_without_owner_host = copy.deepcopy(bindings)
        owner_binding = next(
            binding
            for binding in bindings_without_owner_host["bindings"]
            if binding["role_id"] == "atlas.workflow-architect"
        )
        del owner_binding["host_id"]
        reconciled, reconcile_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings_without_owner_host,
            envelopes=[],
        )

        self.assertEqual([], reconcile_findings)
        self.assertEqual("UNKNOWN", reconciled["standing_packets"][0]["owner_return_state"])
        report = _scheduler_report(reconciled)
        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("owner_return_unknown", report["blocked_candidates"][0]["blocked_reason"])

    def test_same_event_replay_cannot_retarget_execution_or_owner_transport(self) -> None:
        payload = _standardized_ready_payload(
            "immutable-transport",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.release.immutable-transport",
            worktree="isolated-immutable-transport",
        )
        payload["execution_class"] = "read_only"
        envelope = _standardized_envelope(
            payload,
            role_id="atlas.release-control-plane",
            runtime_thread_id="release-epoch-1",
            owner_role_id="atlas.workflow-architect",
            owner_runtime_thread_id="architect-epoch-1",
            idempotency_key="immutable-transport",
            source_role_id="atlas.workflow-architect",
        )
        bindings = _bindings(
            ("atlas.release-control-plane", "release-epoch-1", "idle"),
            ("atlas.workflow-architect", "architect-epoch-1", "idle"),
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=bindings,
            envelopes=[envelope],
        )
        self.assertEqual([], findings)
        original_transport = program["standing_packets"][0]["authority"]["transport_digest"]

        cases = []
        owner_epoch = copy.deepcopy(envelope)
        owner_epoch["owner_return"]["thread_id"] = "architect-epoch-2"
        cases.append(
            (
                owner_epoch,
                _bindings(
                    ("atlas.release-control-plane", "release-epoch-1", "idle"),
                    ("atlas.workflow-architect", "architect-epoch-2", "idle"),
                ),
            )
        )
        owner_host = copy.deepcopy(envelope)
        owner_host["owner_return"]["host_id"] = "remote"
        owner_host_bindings = _bindings(
            ("atlas.release-control-plane", "release-epoch-1", "idle"),
            ("atlas.workflow-architect", "architect-epoch-1", "idle"),
        )
        owner_host_bindings["bindings"][1]["host_id"] = "remote"
        cases.append((owner_host, owner_host_bindings))
        cases.append(
            (
                copy.deepcopy(envelope),
                _bindings(
                    ("atlas.release-control-plane", "release-epoch-2", "idle"),
                    ("atlas.workflow-architect", "architect-epoch-1", "idle"),
                ),
            )
        )

        for replay, replay_bindings in cases:
            with self.subTest(replay_owner=replay["owner_return"], replay_bindings=replay_bindings):
                replayed, replay_findings = scheduler.reconcile_runtime_program(
                    program=copy.deepcopy(program),
                    bindings_payload=replay_bindings,
                    envelopes=[replay],
                )
                self.assertIn("event_transport_identity_collision", [item["code"] for item in replay_findings])
                self.assertEqual(original_transport, replayed["standing_packets"][0]["authority"]["transport_digest"])

    def test_tracking_text_cannot_replace_standardized_owner_return(self) -> None:
        payload = _standardized_ready_payload(
            "owner-return-missing",
            role_id="owner.socials-os",
            repository="fawxzzy/socials-os",
            writer_scope="repo.socials-os.source",
            worktree="C:/worktrees/socials-os",
        )
        payload["next_tracking_thread"] = "03 Socials OS — SELF"
        envelope = _standardized_envelope(
            payload,
            role_id="owner.socials-os",
            runtime_thread_id="socials-thread",
            idempotency_key="owner-return-missing",
        )
        envelope.pop("owner_return")

        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("owner.socials-os", "socials-thread", "idle")),
            envelopes=[envelope],
        )
        report = _scheduler_report(program)

        self.assertIn("owner_return_identity_required", [finding["code"] for finding in findings])
        self.assertEqual("UNKNOWN", program["standing_packets"][0]["owner_return_state"])
        self.assertEqual("owner_return_unknown", report["blocked_candidates"][0]["blocked_reason"])
        self.assertIn("OWNER_RETURN_UNKNOWN", [item["code"] for item in report["liveness_watchdogs"]])
        terminal_successor, error = scheduler._resolve_terminal_successor(
            {
                "terminal": True,
                "canonical_lifecycle_state": "COMPLETED",
                "next_tracking_thread": "03 Socials OS — SELF",
            }
        )
        self.assertIsNone(error)
        self.assertEqual("TERMINAL_DOMAIN", terminal_successor)

    def test_standardized_delivery_requires_exact_owner_return_proof_and_dedupes(self) -> None:
        payload = _standardized_ready_payload(
            "owner-return-delivery",
            role_id="owner.fawxzzyweb",
            repository="fawxzzy/fawxzzyweb",
            writer_scope="repo.fawxzzyweb.source",
            worktree="C:/worktrees/fawxzzyweb",
        )
        envelope = _standardized_envelope(
            payload,
            role_id="owner.fawxzzyweb",
            runtime_thread_id="web-thread",
            idempotency_key="owner-return-delivery",
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("owner.fawxzzyweb", "web-thread", "idle")),
            envelopes=[envelope],
        )
        self.assertEqual([], findings)
        report = _scheduler_report(program)
        reserved, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        reservation_id = reservations[0]["reservation_id"]
        intent = reserved["delivery_intents"][0]
        base_result = {
            "reservation_id": reservation_id,
            "packet_id": "owner-return-delivery",
            "runtime_thread_id": "web-thread",
            "writer_scope": "repo.fawxzzyweb.source",
            "event_id": envelope["event_id"],
            "payload_digest": envelope["payload_digest"],
            "transport_digest": intent["transport_digest"],
            "status": "DELIVERED",
            "turn_id": "web-turn",
            "owner_return": envelope["owner_return"],
        }

        rejected, rejected_findings = scheduler.apply_delivery_results(
            program=copy.deepcopy(reserved),
            results=[base_result],
        )
        self.assertIn("owner_return_proof_required", [finding["code"] for finding in rejected_findings])
        self.assertEqual("UNKNOWN", rejected["standing_packets"][0]["owner_return_state"])

        suppressed_first = copy.deepcopy(base_result)
        suppressed_first["delivery_proof"] = {
            "turn_id": "web-turn",
            "tool_receipt_id": "tool-web-turn",
            "dedupe_result": "DUPLICATE_SUPPRESSED",
        }
        _, suppressed_findings = scheduler.apply_delivery_results(
            program=copy.deepcopy(reserved),
            results=[suppressed_first],
        )
        self.assertIn("owner_return_first_delivery_required", [finding["code"] for finding in suppressed_findings])

        delivered_result = copy.deepcopy(base_result)
        delivered_result["delivery_proof"] = {
            "turn_id": "web-turn",
            "tool_receipt_id": "tool-web-turn",
            "dedupe_result": "FIRST_DELIVERY",
        }
        settled, settled_findings = scheduler.apply_delivery_results(
            program=copy.deepcopy(reserved),
            results=[delivered_result, delivered_result],
        )
        self.assertEqual([], settled_findings)
        self.assertEqual("delivered", settled["delivery_intents"][0]["status"])
        self.assertEqual("DELIVERED", settled["standing_packets"][0]["owner_return_state"])
        self.assertEqual("owner.fawxzzyweb", settled["standing_packets"][0]["current_tracker_role_id"])
        self.assertEqual(intent["owner_return"], settled["delivery_intents"][0]["owner_return"])
        self.assertEqual("owner.fawxzzyweb", settled["delivery_intents"][0]["tracker_role_id"])

        duplicate = copy.deepcopy(delivered_result)
        duplicate["delivery_proof"]["dedupe_result"] = "DUPLICATE_SUPPRESSED"
        deduped, dedupe_findings = scheduler.apply_delivery_results(program=settled, results=[duplicate])
        self.assertEqual([], dedupe_findings)
        self.assertEqual("web-turn", deduped["delivery_intents"][0]["turn_id"])

    def test_host_loss_retains_outbox_and_reuses_exact_reservation_after_reconnect(self) -> None:
        payload = _standardized_ready_payload(
            "host-reconnect",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
            worktree="C:/worktrees/fitness",
        )
        envelope = _standardized_envelope(
            payload,
            role_id="owner.fitness",
            runtime_thread_id="fitness-thread",
            idempotency_key="host-reconnect",
        )
        program, _ = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[envelope],
        )
        report = _scheduler_report(program)
        reserved, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        reservation_id = reservations[0]["reservation_id"]
        host_result = {
            "reservation_id": reservation_id,
            "packet_id": "host-reconnect",
            "runtime_thread_id": "fitness-thread",
            "writer_scope": "repo.fitness.source",
            "event_id": envelope["event_id"],
            "payload_digest": envelope["payload_digest"],
            "transport_digest": reserved["delivery_intents"][0]["transport_digest"],
            "status": "HOST_UNAVAILABLE",
            "turn_id": None,
            "owner_return": envelope["owner_return"],
            "delivery_proof": {
                "tool_receipt_id": "tool-host-unavailable",
                "failure_class": "HOST_UNAVAILABLE",
            },
        }
        unavailable, unavailable_findings = scheduler.apply_delivery_results(
            program=reserved,
            results=[host_result],
        )
        self.assertEqual([], unavailable_findings)
        self.assertEqual("HOST_UNAVAILABLE", unavailable["standing_packets"][0]["state"])
        self.assertEqual("host-unavailable", unavailable["delivery_intents"][0]["status"])
        self.assertEqual("recovery-required", unavailable["active_leases"][0]["status"])

        reconnected, reconnect_findings = scheduler.reconcile_runtime_program(
            program=copy.deepcopy(unavailable),
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[envelope],
        )
        self.assertEqual([], reconnect_findings)
        self.assertEqual(scheduler.RECOVERY_READY_STATE, reconnected["standing_packets"][0]["state"])
        reconnect_report = _scheduler_report(reconnected)
        self.assertEqual("HOST_RECONNECT", reconnect_report["selected_jobs"][0]["recovery_mode"])
        resumed, resumed_reservations = scheduler.reserve_selected_jobs(program=reconnected, report=reconnect_report)
        self.assertEqual(reservation_id, resumed_reservations[0]["reservation_id"])
        self.assertEqual(1, len(resumed["delivery_intents"]))
        self.assertEqual(1, len(resumed["active_leases"]))

        drifted, _ = scheduler.reconcile_runtime_program(
            program=copy.deepcopy(unavailable),
            bindings_payload=_bindings(("owner.fitness", "replacement-fitness-thread", "idle")),
            envelopes=[envelope],
        )
        drift_report = _scheduler_report(drifted)
        self.assertEqual([], [job for job in drift_report["selected_jobs"] if job.get("source") == "standing_task"])
        self.assertEqual("UNKNOWN", drifted["standing_packets"][0]["owner_return_state"])

    def test_terminal_successor_is_closed_and_free_form_text_has_no_authority(self) -> None:
        cases = [
            ({"terminal": True, "next_packet_id": "next"}, "NEXT_AUTONOMOUS_PACKET"),
            ({"terminal": True, "question_id": "ATLAS-MAN-1"}, "MANUAL_REQUIRED"),
            ({"terminal": True, "external_wait": True}, "EXTERNAL_WAIT"),
            ({"terminal": True, "canonical_lifecycle_state": "COMPLETED"}, "TERMINAL_DOMAIN"),
            ({"terminal": True, "canonical_lifecycle_state": "BLOCKED_ERROR"}, "ERROR_RECOVERY"),
        ]
        for payload, expected in cases:
            with self.subTest(expected=expected):
                successor, finding = scheduler._resolve_terminal_successor(payload)
                self.assertIsNone(finding)
                self.assertEqual(expected, successor)
        successor, finding = scheduler._resolve_terminal_successor(
            {"terminal": True, "terminal_successor": "KEEP_GOING"}
        )
        self.assertIsNone(successor)
        self.assertEqual("terminal_successor_invalid", finding["code"])

        successor, finding = scheduler._resolve_terminal_successor(
            {
                "terminal": True,
                "policy_id": scheduler.WORKFLOW_STANDARDIZATION_POLICY_ID,
                "canonical_lifecycle_state": "COMPLETED",
            }
        )
        self.assertIsNone(successor)
        self.assertEqual("terminal_successor_required", finding["code"])

        for clean_state in ("MANUALLY_VERIFIED_PASS", "SUCCESS_NO_ERRORS", "UNKNOWN_ITEMS_ZERO"):
            with self.subTest(clean_state=clean_state):
                successor, finding = scheduler._resolve_terminal_successor(
                    {"terminal": True, "canonical_lifecycle_state": clean_state}
                )
                self.assertIsNone(finding)
                self.assertEqual("TERMINAL_DOMAIN", successor)

    def test_portfolio_projection_exposes_named_sections_and_recovery_packets(self) -> None:
        ready = _standing_packet(
            "ready-idle",
            role_id="owner.socials-os",
            repository="fawxzzy/socials-os",
            writer_scope="repo.socials-os.source",
        )
        active = _standing_packet(
            "active-stale",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        active["state"] = "ACTIVE"
        manual = _standing_packet(
            "manual-wait",
            role_id="owner.mazer",
            repository="fawxzzy/mazer",
            writer_scope="repo.mazer.source",
        )
        manual["state"] = "BLOCKED"
        manual["blocking_receipt"] = {"terminal_successor": "MANUAL_REQUIRED"}
        external = _standing_packet(
            "host-wait",
            role_id="owner.fawxzzyweb",
            repository="fawxzzy/fawxzzyweb",
            writer_scope="repo.fawxzzyweb.source",
        )
        external["state"] = "HOST_UNAVAILABLE"
        external["runtime_status"] = "host_unavailable"
        program = _program_payload()
        program["standing_packets"] = [ready, active, manual, external]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv_" + "1" * 64,
                "packet_id": "active-stale",
                "logical_role_id": "owner.fitness",
                "runtime_thread_id": active["runtime_thread_id"],
                "writer_scope": active["writer_scope"],
                "repository": active["repository"],
                "execution_class": "repo_worktree",
                "resource_claims": {"files": [], "worktrees": [], "ports": [], "browsers": [], "external_writers": []},
                "status": "active",
                "heartbeat_at": "2020-01-01T00:00:00Z",
            }
        ]
        program["delivery_intents"] = []
        program["completed_receipts"] = [
            {
                "logical_role_id": "owner.completed",
                "packet_id": "completed",
                "terminal_successor": "TERMINAL_DOMAIN",
            }
        ]
        report: dict[str, object] = {"selected_jobs": [], "observed_at": "2026-07-22T12:00:00Z"}

        scheduler._attach_operational_projection(report=report, program=program)
        portfolio = report["portfolio_status"]
        self.assertEqual(
            [
                "DONE_RECENTLY",
                "ACTIVE_NOW",
                "READY_TO_START",
                "WAITING_ON_ZAC",
                "WAITING_EXTERNAL",
                "BLOCKED_ERROR",
                "NEXT_DISPATCHES",
                "HEALTH",
            ],
            list(portfolio),
        )
        for section in ("DONE_RECENTLY", "ACTIVE_NOW", "READY_TO_START", "WAITING_ON_ZAC", "WAITING_EXTERNAL"):
            self.assertTrue(portfolio[section])
            self.assertEqual(
                {
                    "role",
                    "packet",
                    "resource_claim",
                    "state",
                    "last_receipt",
                    "next_executable_action",
                    "wake_condition",
                    "owner_return_proof",
                    "staleness",
                },
                set(portfolio[section][0]),
            )
        watchdog_codes = {item["code"] for item in report["liveness_watchdogs"]}
        self.assertTrue({"READY_IDLE", "STALE_ACTIVE_LEASE", "BLOCKED_QUEUE", "HOST_UNAVAILABLE"}.issubset(watchdog_codes))
        self.assertEqual("BLOCKED", portfolio["HEALTH"]["scheduler"])
        self.assertIn("STALE_ACTIVE_LEASE", portfolio["HEALTH"]["blocking_watchdog_codes"])
        self.assertGreater(portfolio["HEALTH"]["blocking_watchdog_count"], 0)

    def test_portfolio_health_reflects_each_blocking_watchdog(self) -> None:
        owner_unknown = _standing_packet(
            "owner-unknown",
            role_id="owner.socials-os",
            repository="fawxzzy/socials-os",
            writer_scope="repo.socials-os.source",
        )
        owner_unknown["policy_id"] = scheduler.WORKFLOW_STANDARDIZATION_POLICY_ID
        owner_unknown["owner_return_state"] = "UNKNOWN"

        missing_runtime = _standing_packet(
            "missing-runtime",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        missing_runtime["runtime_thread_id"] = None
        missing_runtime["runtime_status"] = "missing"

        active_without_lease = _standing_packet(
            "active-without-lease",
            role_id="owner.mazer",
            repository="fawxzzy/mazer",
            writer_scope="repo.mazer.source",
        )
        active_without_lease["state"] = "ACTIVE"

        for packet, expected_code in (
            (owner_unknown, "OWNER_RETURN_UNKNOWN"),
            (missing_runtime, "MISSING_RUNTIME"),
            (active_without_lease, "ACTIVE_WITHOUT_LEASE"),
        ):
            with self.subTest(expected_code=expected_code):
                program = _program_payload()
                program["standing_packets"] = [packet]
                program["active_leases"] = []
                program["delivery_intents"] = []
                report: dict[str, object] = {"selected_jobs": [], "observed_at": "2026-07-22T12:00:00Z"}
                scheduler._attach_operational_projection(report=report, program=program)
                health = report["portfolio_status"]["HEALTH"]
                self.assertEqual("BLOCKED", health["scheduler"])
                self.assertIn(expected_code, health["watchdog_codes"])
                self.assertIn(expected_code, health["blocking_watchdog_codes"])
                self.assertEqual(1, health["blocking_watchdog_count"])

        degraded_program = _program_payload()
        degraded_program["standing_packets"] = [
            _standing_packet(
                "ready-idle-health",
                role_id="owner.fawxzzyweb",
                repository="fawxzzy/fawxzzyweb",
                writer_scope="repo.fawxzzyweb.source",
            )
        ]
        degraded_report: dict[str, object] = {"selected_jobs": [], "observed_at": "2026-07-22T12:00:00Z"}
        scheduler._attach_operational_projection(report=degraded_report, program=degraded_program)
        self.assertEqual("DEGRADED", degraded_report["portfolio_status"]["HEALTH"]["scheduler"])

        healthy_report: dict[str, object] = {"selected_jobs": [], "observed_at": "2026-07-22T12:00:00Z"}
        scheduler._attach_operational_projection(report=healthy_report, program=_program_payload())
        self.assertEqual("HEALTHY", healthy_report["portfolio_status"]["HEALTH"]["scheduler"])

    def test_disjoint_owner_repositories_advance_while_colliding_platform_writers_serialize(self) -> None:
        program = _program_payload()
        program["max_parallel_writers"] = 6
        packets = []
        identities = [
            ("web", "owner.fawxzzyweb", "fawxzzy/fawxzzyweb"),
            ("socials", "owner.socials-os", "fawxzzy/socials-os"),
            ("recovery", "owner.recovery-automation", "fawxzzy/recovery-automation"),
            ("hosted-replay", "owner.hosted-replay", "fawxzzy/hosted-replay"),
            ("platform-a", "owner.fawxzzy-platform", "fawxzzy/fawxzzy-platform"),
            ("platform-b", "owner.fawxzzy-platform.secondary", "fawxzzy/fawxzzy-platform"),
        ]
        for packet_id, role_id, repository in identities:
            packet = _standing_packet(
                packet_id,
                role_id=role_id,
                repository=repository,
                writer_scope=f"repo.{packet_id}.source",
            )
            worktree = "worktrees/platform" if packet_id.startswith("platform") else f"worktrees/{packet_id}"
            packet["resource_claims"] = {
                "files": ["src/platform/**"] if packet_id.startswith("platform") else [f"src/{packet_id}/**"],
                "worktrees": [worktree],
                "ports": [],
                "browsers": [],
                "external_writers": [],
            }
            packets.append(packet)
        program["standing_packets"] = packets

        report = _scheduler_report(program)
        selected = {job["packet_id"] for job in report["selected_jobs"]}
        self.assertTrue({"web", "socials", "recovery", "hosted-replay"}.issubset(selected))
        self.assertEqual(1, len(selected.intersection({"platform-a", "platform-b"})))
        deferred_platform = [
            item for item in report["deferred_candidates"] if item["packet_id"] in {"platform-a", "platform-b"}
        ]
        self.assertEqual(1, len(deferred_platform))
        self.assertEqual("resource_conflict", deferred_platform[0]["deferred_reason"])
        deferred_id = deferred_platform[0]["packet_id"]
        deferred_watchdog = next(
            item for item in report["liveness_watchdogs"] if item["packet_id"] == deferred_id
        )
        self.assertEqual("BLOCKED_QUEUE", deferred_watchdog["code"])
        self.assertEqual("CONFLICTING_RESOURCE_RELEASE_OR_CAPACITY", deferred_watchdog["wake_condition"])

    def test_program_lock_excludes_concurrent_scheduler_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            program_path = Path(temp_dir) / "program.json"
            _write(program_path, "{}\n")
            with scheduler._exclusive_program_lock(program_path):
                with self.assertRaises(scheduler.ProgramLockBusy):
                    with scheduler._exclusive_program_lock(program_path):
                        self.fail("second scheduler unexpectedly acquired the program lock")
            self.assertTrue(program_path.with_suffix(".json.lock").exists())

    def test_program_lock_recovers_after_process_death(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            program_path = Path(temp_dir) / "program.json"
            _write(program_path, "{}\n")
            child = (
                "import os,sys; "
                "from pathlib import Path; "
                "from ops.atlas import autonomous_lane_scheduler as s; "
                "c=s._exclusive_program_lock(Path(sys.argv[1])); "
                "c.__enter__(); os._exit(0)"
            )
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [sys.executable, "-c", child, str(program_path)],
                cwd=scheduler.ROOT,
                env=environment,
                check=False,
            )

            self.assertEqual(0, result.returncode)
            self.assertTrue(program_path.with_suffix(".json.lock").exists())
            with scheduler._exclusive_program_lock(program_path):
                pass

    def test_validation_cleanup_takes_precedence(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_VALIDATION_CLEANUP, report["status"])
        self.assertEqual(scheduler.DECISION_VALIDATION_CLEANUP, report["decision"])
        self.assertTrue(report["safe_to_execute"])

    def test_root_validation_does_not_suppress_disjoint_read_only_packet(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "runtime-proof",
            role_id="atlas.runtime",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas-runtime.proof",
        )
        packet["execution_class"] = "read_only"
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["runtime-proof"], [job["packet_id"] for job in report["selected_jobs"]])
        self.assertEqual("read_only", report["selected_jobs"][0]["execution_class"])
        self.assertTrue(
            any(
                candidate.get("blocked_reason") == "root_validation_scope_held"
                for candidate in report["blocked_candidates"]
            )
        )

    def test_root_validation_does_not_suppress_same_root_read_only_packet(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "root-provenance",
            role_id="atlas.clean-resync",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.root.provenance",
        )
        packet["execution_class"] = "read_only"
        packet["resource_claims"] = {
            "files": ["README-STACK.md", "docs/memory/profiles/zachariah_workflow_profile.md"],
            "worktrees": ["C:/ATLAS"],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("C:/ATLAS"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["root-provenance"], [job["packet_id"] for job in report["selected_jobs"]])
        self.assertEqual("read_only", report["selected_jobs"][0]["execution_class"])

    def test_root_validation_does_not_suppress_disjoint_owner_writer(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "web-source-fix",
            role_id="owner.fawxzzyweb",
            repository="fawxzzy/fawxzzyweb",
            writer_scope="repo.fawxzzyweb",
        )
        packet["resource_claims"] = {
            "files": ["apps/web/**"],
            "worktrees": ["fawxzzyweb-source-fix"],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual("web-source-fix", report["selected_jobs"][0]["packet_id"])
        self.assertEqual("repo_worktree", report["selected_jobs"][0]["execution_class"])

    def test_root_validation_does_not_suppress_isolated_same_repository_worktree(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "atlas-corpus-source",
            role_id="playbook.atlas-book",
            repository="fawxzzy/ATLAS",
            writer_scope="source.atlas.text-corpus-inventory.pilot.r2",
        )
        packet["resource_claims"] = {
            "files": ["ops/atlas/text_corpus_inventory.py", "tests/test_atlas_text_corpus_inventory.py"],
            "worktrees": ["C:/w/atci-r2"],
            "ports": [],
            "browsers": [],
            "external_writers": ["git-branch:fawxzzy/ATLAS:codex/text-corpus-inventory-pilot-r2"],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("C:/w/asr"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["atlas-corpus-source"], [job["packet_id"] for job in report["selected_jobs"]])

    def test_root_validation_suppresses_unproven_same_repository_worktree(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "atlas-unbounded-source",
            role_id="playbook.atlas-book",
            repository="fawxzzy/ATLAS",
            writer_scope="source.atlas.unbounded",
        )
        packet["resource_claims"] = {
            "files": [],
            "worktrees": ["C:/w/other"],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("C:/w/asr"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_VALIDATION_CLEANUP, report["status"])
        self.assertEqual(["ATLAS root validation cleanup"], [job["packet_id"] for job in report["selected_jobs"]])

    def test_root_validation_suppresses_same_worktree_repository_writer(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "atlas-root-source",
            role_id="playbook.atlas-book",
            repository="fawxzzy/ATLAS",
            writer_scope="source.atlas.root",
        )
        packet["resource_claims"] = {
            "files": ["ops/atlas/**"],
            "worktrees": ["C:/w/asr"],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("C:/w/asr"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_VALIDATION_CLEANUP, report["status"])
        self.assertEqual(["ATLAS root validation cleanup"], [job["packet_id"] for job in report["selected_jobs"]])

    def test_root_validation_suppresses_wildcard_worktree_claim(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "atlas-wildcard-worktree",
            role_id="playbook.atlas-book",
            repository="fawxzzy/ATLAS",
            writer_scope="source.atlas.wildcard",
        )
        packet["resource_claims"] = {
            "files": ["ops/atlas/text_corpus_inventory.py"],
            "worktrees": ["C:/w/*"],
            "ports": [],
            "browsers": [],
            "external_writers": [],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("C:/w/asr"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_VALIDATION_CLEANUP, report["status"])
        self.assertEqual(["ATLAS root validation cleanup"], [job["packet_id"] for job in report["selected_jobs"]])

    def test_root_validation_does_not_suppress_external_mutation(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "pr-review-request",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="github.fawxzzy.ATLAS.pr146.review",
        )
        packet["execution_class"] = "external_mutation"
        packet["resource_claims"] = {
            "files": [],
            "worktrees": [],
            "ports": [],
            "browsers": [],
            "external_writers": ["github:fawxzzy/ATLAS#146:review"],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["pr-review-request"], [job["packet_id"] for job in report["selected_jobs"]])
        self.assertEqual("external_mutation", report["selected_jobs"][0]["execution_class"])

    def test_external_mutation_requires_exact_writer_claim(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "unclaimed-external-write",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="github.fawxzzy.ATLAS.pr146.review",
        )
        packet["execution_class"] = "external_mutation"
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("external_writer_claim_required", report["blocked_candidates"][0]["blocked_reason"])

    def test_one_segment_repository_identity_is_rejected(self) -> None:
        program = _program_payload()
        malformed = _standing_packet(
            "bare-repository",
            role_id="atlas.main",
            repository="ATLAS",
            writer_scope="repo.atlas.bare",
        )
        qualified = _standing_packet(
            "qualified-repository",
            role_id="atlas.workflow-architect",
            repository="fawxzzy/ATLAS",
            writer_scope="repo.atlas.qualified",
        )
        program["standing_packets"] = [malformed, qualified]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(["qualified-repository"], [job["packet_id"] for job in report["selected_jobs"]])
        blocked = next(item for item in report["blocked_candidates"] if item["packet_id"] == "bare-repository")
        self.assertEqual("standing_packet_scope_required", blocked["blocked_reason"])

    def test_malformed_github_pr_writer_alias_is_rejected(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "malformed-review-writer",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="github.fawxzzy.ATLAS.pr146.review",
        )
        packet["execution_class"] = "external_mutation"
        packet["resource_claims"] = {
            "external_writers": ["github-pr:fawxzzy/ATLAS#not-a-number"],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("external_writer_claim_required", report["blocked_candidates"][0]["blocked_reason"])

    def test_malformed_github_pr_url_aliases_are_rejected(self) -> None:
        for locator, number in (
            ("pulls", "146"),
            ("pr", "146"),
            ("prs", "146"),
            ("pull-request", "146"),
            ("pullx", "146"),
            ("pullx", "not-a-number"),
        ):
            with self.subTest(locator=locator, number=number):
                program = _program_payload()
                packet = _standing_packet(
                    f"malformed-review-url-{locator}",
                    role_id="atlas.release-control-plane",
                    repository="fawxzzy/ATLAS",
                    writer_scope=f"github.fawxzzy.ATLAS.pr146.review.{locator}",
                )
                packet["execution_class"] = "external_mutation"
                packet["resource_claims"] = {
                    "external_writers": [f"https://github.com/fawxzzy/ATLAS/{locator}/{number}"],
                }
                program["standing_packets"] = [packet]

                report = scheduler.build_report(
                    root=Path("atlas-root-fixture"),
                    program=program,
                    max_candidates=30,
                    preflight_report=_preflight_payload(),
                    selector_report=_selector_payload(),
                    planner_report=_planner_payload([]),
                )

                self.assertEqual([], report["selected_jobs"])
                self.assertEqual("external_writer_claim_required", report["blocked_candidates"][0]["blocked_reason"])

    def test_claimless_external_active_lease_is_incomplete(self) -> None:
        program = _program_payload()
        program["active_leases"] = [
            {
                "packet_id": "unknown-external-writer",
                "reservation_id": "rsrv_unknown",
                "repository": "fawxzzy/ATLAS",
                "writer_scope": "github.fawxzzy.ATLAS.unknown",
                "execution_class": "external_mutation",
                "resource_claims": {},
                "status": "active",
            }
        ]
        packet = _standing_packet(
            "review-request",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="github.fawxzzy.ATLAS.pr146.review",
        )
        packet["execution_class"] = "external_mutation"
        packet["resource_claims"] = {
            "external_writers": ["github:fawxzzy/ATLAS#146:review"],
        }
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("active_lease_identity_incomplete", report["blocked_candidates"][0]["blocked_reason"])

    def test_external_mutations_serialize_on_exact_writer_claim(self) -> None:
        program = _program_payload()
        packets = []
        for packet_id in ("review-request", "review-reply"):
            packet = _standing_packet(
                packet_id,
                role_id="atlas.release-control-plane",
                repository="fawxzzy/ATLAS",
                writer_scope=f"github.fawxzzy.ATLAS.pr146.{packet_id}",
            )
            packet["execution_class"] = "external_mutation"
            packet["resource_claims"] = {
                "files": [],
                "worktrees": [],
                "ports": [],
                "browsers": [],
                "external_writers": ["github:fawxzzy/ATLAS#146:review"],
            }
            packets.append(packet)
        program["standing_packets"] = packets

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertTrue(
            any(
                "external_writers" in conflict.get("resource_kinds", [])
                for item in report["deferred_candidates"]
                for conflict in item.get("conflicts_with", [])
            )
        )

    def test_external_writer_repository_case_variants_are_one_resource(self) -> None:
        program = _program_payload()
        packets = []
        for packet_id, repository_case in (("review-request", "ATLAS"), ("review-reply", "atlas")):
            packet = _standing_packet(
                packet_id,
                role_id="atlas.release-control-plane",
                repository="fawxzzy/ATLAS",
                writer_scope=f"github.fawxzzy.ATLAS.pr146.{packet_id}",
            )
            packet["execution_class"] = "external_mutation"
            packet["resource_claims"] = {
                "external_writers": [f"github:fawxzzy/{repository_case}#146:review"],
            }
            packets.append(packet)
        program["standing_packets"] = packets

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertIn("external_writers", report["deferred_candidates"][0]["conflicts_with"][0]["resource_kinds"])
        self.assertEqual(
            ["github-pr:fawxzzy/atlas#146"],
            report["selected_jobs"][0]["resource_claims"]["external_writers"],
        )

    def test_github_pr_url_and_structured_writer_are_one_resource(self) -> None:
        program = _program_payload()
        structured = _standing_packet(
            "structured-review",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="github.fawxzzy.ATLAS.pr146.review",
        )
        structured["execution_class"] = "external_mutation"
        structured["resource_claims"] = {
            "external_writers": ["github:fawxzzy/ATLAS#146:review:head"],
        }
        url = _standing_packet(
            "url-review",
            role_id="atlas.inbox",
            repository="fawxzzy/ATLAS",
            writer_scope="github.fawxzzy.ATLAS.pr146.url",
        )
        url["execution_class"] = "external_mutation"
        url["resource_claims"] = {
            "external_writers": ["https://github.com/fawxzzy/ATLAS/pull/146"],
        }
        program["standing_packets"] = [structured, url]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertIn("external_writers", report["deferred_candidates"][0]["conflicts_with"][0]["resource_kinds"])
        self.assertEqual(
            ["github-pr:fawxzzy/atlas#146"],
            report["selected_jobs"][0]["resource_claims"]["external_writers"],
        )

    def test_worker_reconciliation_selected_before_other_packets(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Simulation Substrate Readiness",
                        "classification": planner.CLASS_IMPLEMENTATION_READY,
                        "score": 100,
                        "packet": "Cortex Simulation Substrate Readiness worker cluster reconciliation",
                        "mode": "root-local implementation worker cluster",
                    },
                    {
                        "marker": "Cortex Dual-Mode Replacement Readiness",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                        "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                    },
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(scheduler.DECISION_WORKER_RECONCILIATION, report["decision"])
        self.assertEqual("Cortex Simulation Substrate Readiness worker cluster reconciliation", report["selected_packet"])

    def test_routed_worker_selected(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Simulation Substrate Readiness",
                        "classification": planner.CLASS_IMPLEMENTATION_READY,
                        "score": 100,
                        "packet": "Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker packet 1",
                        "mode": "implement one bounded helper",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.DECISION_ROUTED_WORKER, report["decision"])
        self.assertEqual("worker_implementation", report["packet_phase"])

    def test_exact_manifest_packet_selected_from_selector(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(active_lane_is_held=False, action="continue_current_lane", current_packet="Exact routed root packet"),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.DECISION_EXACT_MANIFEST_PACKET, report["decision"])
        self.assertEqual("Exact routed root packet", report["selected_packet"])

    def test_operator_program_switch_requires_reselection_receipt(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Dual-Mode Replacement Readiness",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                        "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.DECISION_OPERATOR_PROGRAM_PACKET, report["decision"])
        self.assertTrue(report["requires_reselection_receipt"])
        self.assertIn("CORTEX-DUAL-MODE-REPLACEMENT-READINESS", report["reselection_receipt"])

    def test_owner_lane_candidate_without_scope_metadata_is_blocked(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Fitness cleanup fallback",
                        "mode": "docs-only",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("owner_lane_metadata_required", report["blocked_candidates"][0]["blocked_reason"])

    def test_distinct_standing_writer_scopes_share_one_wave(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness"),
            _standing_packet("mazer-ready", role_id="owner.mazer", repository="fawxzzy/mazer", writer_scope="repo.mazer"),
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(scheduler.DECISION_EXECUTION_WAVE, report["decision"])
        self.assertEqual(["fitness-ready", "mazer-ready"], sorted(job["packet_id"] for job in report["selected_jobs"]))

    def test_same_writer_scope_defers_second_packet(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-a", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness"),
            _standing_packet("fitness-b", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness"),
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertEqual("resource_conflict", report["deferred_candidates"][0]["deferred_reason"])

    def test_same_repository_mutations_require_complete_isolation_claims(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a"),
            _standing_packet("atlas-b", role_id="atlas.workflow-architect", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.b"),
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertEqual("resource_conflict", report["deferred_candidates"][0]["deferred_reason"])
        self.assertEqual(["repository"], report["deferred_candidates"][0]["conflicts_with"][0]["resource_kinds"])

    def test_same_repository_mutations_can_share_wave_with_proven_isolation(self) -> None:
        program = _program_payload()
        left = _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a")
        left["resource_claims"] = {"worktrees": ["worktrees/atlas-a"], "files": ["ops/atlas/a/**"]}
        right = _standing_packet(
            "atlas-b",
            role_id="atlas.workflow-architect",
            repository="fawxzzy/ATLAS",
            writer_scope="repo.atlas.b",
        )
        right["resource_claims"] = {"worktrees": ["worktrees/atlas-b"], "files": ["tests/atlas/b/**"]}
        program["standing_packets"] = [left, right]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["atlas-a", "atlas-b"], sorted(job["packet_id"] for job in report["selected_jobs"]))

    def test_canonical_workspace_never_shares_same_repository_worktree_wave(self) -> None:
        program = _program_payload()
        canonical = _standing_packet(
            "atlas-root",
            role_id="atlas.main",
            repository="fawxzzy/ATLAS",
            writer_scope="atlas.root",
        )
        canonical["execution_class"] = "canonical_workspace"
        canonical["resource_claims"] = {
            "worktrees": ["C:/ATLAS"],
            "files": ["docs/root/**"],
        }
        isolated = _standing_packet(
            "atlas-isolated",
            role_id="atlas.workflow-architect",
            repository="fawxzzy/ATLAS",
            writer_scope="repo.atlas.isolated",
        )
        isolated["resource_claims"] = {
            "worktrees": ["C:/w/atlas-isolated"],
            "files": ["ops/isolated/**"],
        }
        program["standing_packets"] = [canonical, isolated]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertEqual("resource_conflict", report["deferred_candidates"][0]["deferred_reason"])
        self.assertIn(
            "canonical_root",
            report["deferred_candidates"][0]["conflicts_with"][0]["resource_kinds"],
        )

    def test_duplicate_packet_id_is_never_dispatched_twice(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("same-packet", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness"),
            _standing_packet("same-packet", role_id="owner.mazer", repository="fawxzzy/mazer", writer_scope="repo.mazer"),
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertIn("duplicate_packet_id", [item["blocked_reason"] for item in report["blocked_candidates"]])

    def test_active_lease_blocks_only_its_writer_scope(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness"),
            _standing_packet("mazer-ready", role_id="owner.mazer", repository="fawxzzy/mazer", writer_scope="repo.mazer"),
        ]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv_" + "0" * 64,
                "packet_id": "fitness-active",
                "writer_scope": "repo.fitness",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {},
                "status": "active",
            }
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(["mazer-ready"], [job["packet_id"] for job in report["selected_jobs"]])
        self.assertIn("writer_scope_leased", [item["blocked_reason"] for item in report["blocked_candidates"]])

    def test_active_lease_serializes_unproved_same_repository_scope(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a"),
            _standing_packet("atlas-b", role_id="atlas.workflow-architect", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.b"),
        ]
        program["max_parallel_writers"] = 1
        first = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, _ = scheduler.reserve_selected_jobs(program=program, report=first)
        program["max_parallel_writers"] = 2
        second = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual("fawxzzy/atlas", program["active_leases"][0]["repository"])
        self.assertEqual([], second["selected_jobs"])
        blocked = next(item for item in second["blocked_candidates"] if item["packet_id"] == "atlas-b")
        self.assertEqual("active_lease_resource_conflict", blocked["blocked_reason"])
        self.assertEqual(["repository"], blocked["conflicts_with"][0]["resource_kinds"])

    def test_incomplete_legacy_active_lease_blocks_mutating_recovery(self) -> None:
        program = _program_payload()
        read_only = _standing_packet(
            "safe-read",
            role_id="atlas.inbox",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.safe",
        )
        read_only["execution_class"] = "read_only"
        program["standing_packets"] = [
            _standing_packet("atlas-new", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.new"),
            read_only,
        ]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv_" + "1" * 64,
                "packet_id": "legacy-missing-packet",
                "writer_scope": "repo.atlas.legacy",
                "status": "recovery-required",
            }
        ]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(["safe-read"], [item["packet_id"] for item in report["selected_jobs"]])
        blocked = next(item for item in report["blocked_candidates"] if item["packet_id"] == "atlas-new")
        self.assertEqual("active_lease_identity_incomplete", blocked["blocked_reason"])

    def test_repository_identity_is_case_insensitive(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a"),
            _standing_packet("atlas-b", role_id="atlas.workflow-architect", repository="FAWXZZY/atlas", writer_scope="repo.atlas.b"),
        ]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertEqual("resource_conflict", report["deferred_candidates"][0]["deferred_reason"])
        self.assertIn("repository", report["deferred_candidates"][0]["conflicts_with"][0]["resource_kinds"])

    def test_repository_url_alias_cannot_bypass_serialization(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a"),
            _standing_packet(
                "atlas-b",
                role_id="atlas.workflow-architect",
                repository="https://github.com/fawxzzy/ATLAS.git",
                writer_scope="repo.atlas.b",
            ),
        ]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(report["selected_jobs"]))
        self.assertIn("repository", report["deferred_candidates"][0]["conflicts_with"][0]["resource_kinds"])
        self.assertEqual("fawxzzy/atlas", report["selected_jobs"][0]["repository"])

    def test_recovery_lease_serializes_unproved_same_repository_scope(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a"),
            _standing_packet("atlas-b", role_id="atlas.workflow-architect", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.b"),
        ]
        program["max_parallel_writers"] = 1
        first = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, _ = scheduler.reserve_selected_jobs(program=program, report=first)
        program["active_leases"][0]["status"] = "recovery-required"
        program["max_parallel_writers"] = 2
        second = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], second["selected_jobs"])
        blocked = next(item for item in second["blocked_candidates"] if item["packet_id"] == "atlas-b")
        self.assertEqual("active_lease_resource_conflict", blocked["blocked_reason"])

    def test_active_lease_allows_proven_same_repository_isolation(self) -> None:
        program = _program_payload()
        left = _standing_packet("atlas-a", role_id="atlas.main", repository="fawxzzy/ATLAS", writer_scope="repo.atlas.a")
        left["resource_claims"] = {"worktrees": ["worktrees/atlas-a"], "files": ["ops/atlas/a/**"]}
        right = _standing_packet(
            "atlas-b",
            role_id="atlas.workflow-architect",
            repository="fawxzzy/ATLAS",
            writer_scope="repo.atlas.b",
        )
        right["resource_claims"] = {"worktrees": ["worktrees/atlas-b"], "files": ["tests/atlas/b/**"]}
        program["standing_packets"] = [left, right]
        program["max_parallel_writers"] = 1
        first = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, _ = scheduler.reserve_selected_jobs(program=program, report=first)
        program["max_parallel_writers"] = 2
        second = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(["atlas-b"], [job["packet_id"] for job in second["selected_jobs"]])

    def test_zero_read_only_capacity_is_preserved(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "read-only",
            role_id="atlas.runtime",
            repository="fawxzzy/ATLAS",
            writer_scope="atlas.runtime.read-model",
        )
        packet["execution_class"] = "read_only"
        program["standing_packets"] = [packet]
        program["max_parallel_read_only"] = 0

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("read_only_wave_limit", report["deferred_candidates"][0]["deferred_reason"])

    def test_persisted_active_reservations_count_against_parallel_capacity(self) -> None:
        program = _program_payload()
        program["max_parallel_writers"] = 1
        program["max_parallel_read_only"] = 1
        active_read = _standing_packet(
            "active-read",
            role_id="atlas.runtime",
            repository="fawxzzy/ATLAS",
            writer_scope="read.runtime.active",
        )
        active_read["execution_class"] = "read_only"
        active_read["state"] = "ACTIVE"
        active_read["dispatch_reservation"] = {"reservation_id": "rsrv-read"}
        ready_read = _standing_packet(
            "ready-read",
            role_id="atlas.inbox",
            repository="fawxzzy/ATLAS",
            writer_scope="read.inbox.ready",
        )
        ready_read["execution_class"] = "read_only"
        ready_write = _standing_packet(
            "ready-write",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness",
        )
        program["standing_packets"] = [active_read, ready_read, ready_write]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-web",
                "packet_id": "active-web",
                "writer_scope": "repo.web",
                "repository": "fawxzzy/web",
                "execution_class": "repo_worktree",
                "resource_claims": {},
                "status": "active",
            }
        ]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], report["selected_jobs"])
        self.assertEqual(
            {"read_only_wave_limit", "writer_wave_limit"},
            {item["deferred_reason"] for item in report["deferred_candidates"]},
        )

    def test_active_standing_role_is_never_steered(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "active-owner",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness",
        )
        packet["runtime_status"] = "active"
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("standing_role_active", report["blocked_candidates"][0]["blocked_reason"])
        self.assertEqual("QUEUE_UNTIL_OWNER_SAFE_BOUNDARY", report["portfolio_status"]["READY_TO_START"][0]["next_executable_action"])
        self.assertIn("BLOCKED_QUEUE", [item["code"] for item in report["liveness_watchdogs"]])

    def test_bridge_maps_idle_and_notloaded_bindings_but_preserves_active(self) -> None:
        ready_payloads = [
            {
                "canonical_lifecycle_state": "READY",
                "packet_id": "fitness-ready",
                "objective": "Fitness bounded source correction",
                "logical_role_id": "owner.fitness",
                "repository": "fawxzzy/fitness",
                "writer_scope": "repo.fitness",
                "execution_class": "repo_worktree",
            },
            {
                "canonical_lifecycle_state": "READY",
                "packet_id": "mazer-ready",
                "objective": "Mazer bounded source correction",
                "logical_role_id": "owner.mazer",
                "repository": "fawxzzy/mazer",
                "writer_scope": "repo.mazer",
                "execution_class": "repo_worktree",
            },
            {
                "canonical_lifecycle_state": "READY",
                "packet_id": "socials-active",
                "objective": "Socials bounded source correction",
                "logical_role_id": "owner.socials-os",
                "repository": "fawxzzy/socials-os",
                "writer_scope": "repo.socials-os",
                "execution_class": "repo_worktree",
            },
        ]
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(
                ("owner.fitness", "fitness-thread", "idle"),
                ("owner.mazer", "mazer-thread", "notLoaded"),
                ("owner.socials-os", "socials-thread", "active"),
            ),
            envelopes=[_envelope(payload, idempotency_key=f"event-{index}") for index, payload in enumerate(ready_payloads)],
        )
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertEqual(["fitness-ready", "mazer-ready"], sorted(job["packet_id"] for job in report["selected_jobs"]))
        self.assertIn("standing_role_active", [item["blocked_reason"] for item in report["blocked_candidates"]])
        self.assertEqual("repo.socials-os", program["scope_holds"][0]["writer_scope"])
        self.assertEqual("fawxzzy/socials-os", program["scope_holds"][0]["repository"])
        self.assertEqual("repo_worktree", program["scope_holds"][0]["execution_class"])
        self.assertEqual(scheduler._resource_claims({}), program["scope_holds"][0]["resource_claims"])
        self.assertNotIn("forbidden_owner_lanes", program)

    def test_active_runtime_hold_blocks_same_repository_mutation_under_another_scope(self) -> None:
        active = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "active-owner",
            "objective": "Existing active repository mutation",
            "logical_role_id": "owner.active",
            "repository": "fawxzzy/example",
            "writer_scope": "repo.example.active",
            "execution_class": "repo_worktree",
            "resource_claims": scheduler._resource_claims({}),
        }
        candidate = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "idle-owner",
            "objective": "Competing repository mutation",
            "logical_role_id": "owner.idle",
            "repository": "fawxzzy/example",
            "writer_scope": "repo.example.other",
            "execution_class": "repo_worktree",
            "resource_claims": scheduler._resource_claims({}),
        }
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(
                ("owner.active", "active-thread", "active"),
                ("owner.idle", "idle-thread", "idle"),
            ),
            envelopes=[
                _envelope(active, idempotency_key="active-owner"),
                _envelope(candidate, idempotency_key="idle-owner"),
            ],
        )
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertEqual([], report["selected_jobs"])
        blocked = {item["packet_id"]: item for item in report["blocked_candidates"]}
        self.assertEqual("standing_role_active", blocked["active-owner"]["blocked_reason"])
        self.assertEqual("active_runtime_resource_conflict", blocked["idle-owner"]["blocked_reason"])
        self.assertEqual(["repository"], blocked["idle-owner"]["conflicts_with"][0]["resource_kinds"])

    def test_incomplete_active_runtime_hold_blocks_mutating_dispatch(self) -> None:
        candidate = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "idle-owner",
            "objective": "Candidate repository mutation",
            "logical_role_id": "owner.idle",
            "repository": "fawxzzy/example",
            "writer_scope": "repo.example.other",
            "execution_class": "repo_worktree",
            "resource_claims": scheduler._resource_claims({}),
        }
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("owner.idle", "idle-thread", "idle")),
            envelopes=[_envelope(candidate, idempotency_key="idle-owner")],
        )
        program["scope_holds"] = [
            {
                "writer_scope": "repo.legacy.active",
                "status": "active-without-correlated-lease",
                "derived_from_runtime_status": True,
            }
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("active_runtime_hold_identity_incomplete", report["blocked_candidates"][0]["blocked_reason"])

    def test_active_external_runtime_hold_requires_external_writer_identity(self) -> None:
        candidate = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "idle-external-owner",
            "objective": "Independent external mutation",
            "logical_role_id": "owner.idle",
            "repository": "fawxzzy/other",
            "writer_scope": "github.fawxzzy.other.pr1",
            "execution_class": "external_mutation",
            "resource_claims": scheduler._resource_claims(
                {"external_writers": ["github-pr:fawxzzy/other#1"]}
            ),
            "protected_surface_authorized": True,
        }
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("owner.idle", "idle-thread", "idle")),
            envelopes=[_envelope(candidate, idempotency_key="idle-external-owner")],
        )
        program["scope_holds"] = [
            {
                "packet_id": "active-external-owner",
                "repository": "fawxzzy/example",
                "writer_scope": "github.fawxzzy.example.pr1",
                "execution_class": "external_mutation",
                "resource_claims": scheduler._resource_claims({}),
                "status": "active-without-correlated-lease",
                "derived_from_runtime_status": True,
            }
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertEqual([], report["selected_jobs"])
        self.assertEqual(
            "active_runtime_hold_identity_incomplete",
            report["blocked_candidates"][0]["blocked_reason"],
        )

    def test_bridge_admits_bounded_standing_local_source_preparation(self) -> None:
        payload = _standing_local_source_payload()
        with patch.object(scheduler, "_standing_local_worktree_evidence_violation", return_value=None):
            program, findings = scheduler.reconcile_runtime_program(
                program=_program_payload(),
                bindings_payload=_bindings(("owner.example", "example-thread", "notLoaded")),
                envelopes=[
                    _envelope(
                        payload,
                        idempotency_key="owner-local-source-preparation",
                        source_role_id="atlas.main",
                    )
                ],
            )
        with patch.object(scheduler, "_standing_local_worktree_evidence_violation", return_value=None):
            report = scheduler.build_report(
                root=Path("atlas-root-fixture"),
                program=program,
                max_candidates=30,
                preflight_report=_preflight_payload(),
                selector_report=_selector_payload(),
                planner_report=_planner_payload([]),
            )

        self.assertEqual([], findings)
        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["owner-local-source-preparation"], [job["packet_id"] for job in report["selected_jobs"]])
        persisted = program["standing_packets"][0]
        self.assertEqual(scheduler.STANDING_LOCAL_SOURCE_PREPARATION, persisted["authority_class"])
        self.assertEqual("atlas.main", persisted["source_role_id"])
        self.assertEqual("HELD", persisted["source_preparation"]["publication"])
        prompt = scheduler.render_prompt(report)
        self.assertIn("keep every change unstaged and publication held", prompt)
        self.assertIn("Do not stage, commit, push", prompt)

    def test_bridge_rejects_unbounded_standing_local_source_preparation(self) -> None:
        cases: list[tuple[str, dict[str, object], str]] = []

        wrong_role = _standing_local_source_payload()
        wrong_role["logical_role_id"] = "atlas.main"
        cases.append(("standing_owner_role_required", wrong_role, "atlas.main"))

        wrong_execution = _standing_local_source_payload()
        wrong_execution["execution_class"] = "read_only"
        cases.append(("standing_repo_worktree_required", wrong_execution, "atlas.main"))

        unsafe_path = _standing_local_source_payload()
        unsafe_path["source_preparation"] = copy.deepcopy(unsafe_path["source_preparation"])
        unsafe_path["source_preparation"]["path_allowlist"] = [".github/workflows/release.yml"]
        unsafe_path["resource_claims"] = copy.deepcopy(unsafe_path["resource_claims"])
        unsafe_path["resource_claims"]["files"] = [".github/workflows/release.yml"]
        cases.append(("standing_path_allowlist_unsafe", unsafe_path, "atlas.main"))

        mismatched_files = _standing_local_source_payload()
        mismatched_files["resource_claims"] = copy.deepcopy(mismatched_files["resource_claims"])
        mismatched_files["resource_claims"]["files"] = ["src/feature.py"]
        cases.append(("standing_file_claims_must_match_allowlist", mismatched_files, "atlas.main"))

        duplicate_path = _standing_local_source_payload()
        duplicate_path["source_preparation"] = copy.deepcopy(duplicate_path["source_preparation"])
        duplicate_path["source_preparation"]["path_allowlist"] = ["src/feature.py", "src/feature.py"]
        cases.append(("standing_path_allowlist_not_canonical", duplicate_path, "atlas.main"))

        external_claim = _standing_local_source_payload()
        external_claim["resource_claims"] = copy.deepcopy(external_claim["resource_claims"])
        external_claim["resource_claims"]["external_writers"] = ["malformed-external-writer"]
        cases.append(("standing_external_resource_claim_forbidden", external_claim, "atlas.main"))

        unknown_claim = _standing_local_source_payload()
        unknown_claim["resource_claims"] = copy.deepcopy(unknown_claim["resource_claims"])
        unknown_claim["resource_claims"]["gpu"] = ["shared"]
        cases.append(("standing_resource_claims_invalid", unknown_claim, "atlas.main"))

        cases.append(("standing_source_role_forbidden", _standing_local_source_payload(), "manual.messages"))

        for expected_code, payload, source_role_id in cases:
            with self.subTest(expected_code=expected_code):
                program, findings = scheduler.reconcile_runtime_program(
                    program=_program_payload(),
                    bindings_payload=_bindings(("owner.example", "example-thread", "idle")),
                    envelopes=[
                        _envelope(
                            payload,
                            idempotency_key=expected_code,
                            source_role_id=source_role_id,
                        )
                    ],
                )

                self.assertEqual([], program["standing_packets"])
                self.assertEqual(expected_code, findings[0]["code"])

    def test_bridge_rejects_noncanonical_or_escaping_standing_worktree_claims(self) -> None:
        invalid_claims = (
            "foo/../.",
            "../../other-worktree",
            "/absolute/worktree",
            "C:/absolute/worktree",
            "C:outside-worktree",
            "owner\\worktree",
            "owner//worktree",
            " owner/worktree",
            "owner/worktree ",
        )

        for index, worktree_claim in enumerate(invalid_claims):
            with self.subTest(worktree_claim=worktree_claim):
                payload = _standing_local_source_payload()
                payload["resource_claims"] = copy.deepcopy(payload["resource_claims"])
                payload["resource_claims"]["worktrees"] = [worktree_claim]
                program, findings = scheduler.reconcile_runtime_program(
                    program=_program_payload(),
                    bindings_payload=_bindings(("owner.example", "example-thread", "idle")),
                    envelopes=[
                        _envelope(
                            payload,
                            idempotency_key=f"invalid-worktree-{index}",
                            source_role_id="atlas.main",
                        )
                    ],
                )

                self.assertEqual([], program["standing_packets"])
                self.assertEqual("standing_isolated_worktree_required", findings[0]["code"])

        payload = _standing_local_source_payload()
        payload["resource_claims"] = copy.deepcopy(payload["resource_claims"])
        payload["resource_claims"]["worktrees"] = ["owners/example-local-preparation"]
        with patch.object(scheduler, "_standing_local_worktree_evidence_violation", return_value=None):
            program, findings = scheduler.reconcile_runtime_program(
                program=_program_payload(),
                bindings_payload=_bindings(("owner.example", "example-thread", "idle")),
                envelopes=[
                    _envelope(
                        payload,
                        idempotency_key="canonical-nested-worktree",
                        source_role_id="atlas.main",
                    )
                ],
            )

        self.assertEqual([], findings)
        self.assertEqual(["owner-local-source-preparation"], [packet["packet_id"] for packet in program["standing_packets"]])

    def test_bridge_requires_registered_matching_worktree_at_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = root / "primary"
            primary.mkdir()
            subprocess.run(["git", "init", str(primary)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(primary), "config", "user.name", "ATLAS Test"], check=True)
            subprocess.run(["git", "-C", str(primary), "config", "user.email", "atlas-test@example.invalid"], check=True)
            subprocess.run(
                ["git", "-C", str(primary), "remote", "add", "origin", "https://github.com/fawxzzy/example.git"],
                check=True,
            )
            _write(primary / "README.md", "fixture\n")
            subprocess.run(["git", "-C", str(primary), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(primary), "commit", "-m", "fixture"], check=True, capture_output=True)
            parent = subprocess.check_output(["git", "-C", str(primary), "rev-parse", "HEAD"], text=True).strip()
            worktree = root / "example-local-preparation"
            subprocess.run(
                ["git", "-C", str(primary), "worktree", "add", "--detach", str(worktree), parent],
                check=True,
                capture_output=True,
            )

            def violation(payload: dict[str, object]) -> str | None:
                program, findings = scheduler.reconcile_runtime_program(
                    program=_program_payload(),
                    bindings_payload=_bindings(("owner.example", "example-thread", "idle")),
                    envelopes=[
                        _envelope(
                            payload,
                            idempotency_key="registered-worktree-proof",
                            source_role_id="atlas.main",
                        )
                    ],
                    root=root,
                )
                if findings:
                    self.assertEqual([], program["standing_packets"])
                else:
                    self.assertEqual(
                        ["owner-local-source-preparation"],
                        [packet["packet_id"] for packet in program["standing_packets"]],
                    )
                return findings[0]["code"] if findings else None

            valid = _standing_local_source_payload()
            valid["source_preparation"] = copy.deepcopy(valid["source_preparation"])
            valid["source_preparation"]["parent_commit"] = parent
            self.assertIsNone(violation(valid))

            nonexistent = copy.deepcopy(valid)
            nonexistent["resource_claims"]["worktrees"] = ["missing-worktree"]
            self.assertEqual("standing_worktree_evidence_unavailable", violation(nonexistent))

            foreign = copy.deepcopy(valid)
            foreign["repository"] = "fawxzzy/foreign"
            self.assertEqual("standing_worktree_repository_mismatch", violation(foreign))

            wrong_parent = copy.deepcopy(valid)
            wrong_parent["source_preparation"]["parent_commit"] = "f" * 40
            self.assertEqual("standing_worktree_parent_mismatch", violation(wrong_parent))

            clone = root / "unregistered-clone"
            subprocess.run(["git", "clone", "--shared", str(primary), str(clone)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(clone), "remote", "set-url", "origin", "https://github.com/fawxzzy/example.git"],
                check=True,
            )
            unregistered = copy.deepcopy(valid)
            unregistered["resource_claims"]["worktrees"] = ["unregistered-clone"]
            self.assertEqual("standing_registered_worktree_required", violation(unregistered))

            indirection = copy.deepcopy(valid)
            indirection["resource_claims"]["worktrees"] = ["linked-worktree"]
            linked = root / "linked-worktree"
            try:
                linked.symlink_to(worktree, target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    raise
                subprocess.run(["cmd", "/c", "mklink", "/J", str(linked), str(worktree)], check=True, capture_output=True)
            try:
                self.assertEqual("standing_worktree_indirection_forbidden", violation(indirection))
            finally:
                linked.rmdir() if os.name == "nt" and not linked.is_symlink() else linked.unlink()

    def test_persisted_standing_local_source_preparation_revalidates_authority(self) -> None:
        packet = _standing_packet(
            "owner-local-source-preparation",
            role_id="owner.example",
            repository="fawxzzy/example",
            writer_scope="repo.example.local-preparation",
        )
        payload = _standing_local_source_payload()
        packet.update(
            {
                "authority_class": payload["authority_class"],
                "source_preparation": payload["source_preparation"],
                "resource_claims": payload["resource_claims"],
            }
        )
        program = _program_payload()
        program["standing_packets"] = [packet]

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("standing_source_role_forbidden", report["blocked_candidates"][0]["blocked_reason"])

    def test_bridge_preserves_protected_surface_authority_for_external_mutation(self) -> None:
        payload = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "review-request",
            "objective": "Verify deployments zero, then create one review request; no production mutation.",
            "logical_role_id": "atlas.release-control-plane",
            "repository": "fawxzzy/ATLAS",
            "writer_scope": "github.fawxzzy.ATLAS.pr146.review.head",
            "execution_class": "external_mutation",
            "resource_claims": {
                "external_writers": ["github:fawxzzy/ATLAS#146:review:head"],
            },
            "protected_surface_authorized": True,
        }
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("atlas.release-control-plane", "release-thread", "idle")),
            envelopes=[_envelope(payload, idempotency_key="authorized-review-request")],
        )
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertIs(program["standing_packets"][0]["protected_surface_authorized"], True)
        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["review-request"], [job["packet_id"] for job in report["selected_jobs"]])

    def test_bridge_keeps_unadmitted_protected_external_mutation_blocked(self) -> None:
        payload = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "unadmitted-deploy",
            "objective": "Deploy to production.",
            "logical_role_id": "atlas.release-control-plane",
            "repository": "fawxzzy/ATLAS",
            "writer_scope": "github.fawxzzy.ATLAS.deploy",
            "execution_class": "external_mutation",
            "resource_claims": {
                "external_writers": ["github:fawxzzy/ATLAS:deploy"],
            },
        }
        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("atlas.release-control-plane", "release-thread", "idle")),
            envelopes=[_envelope(payload, idempotency_key="unadmitted-deploy")],
        )
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertIs(program["standing_packets"][0]["protected_surface_authorized"], False)
        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("protected_or_platform_mutation_forbidden", report["blocked_candidates"][0]["blocked_reason"])

    def test_reservation_persists_before_duplicate_selection(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        first = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=first)
        second = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(1, len(reservations))
        self.assertTrue(first["program_persisted_before_dispatch"])
        self.assertEqual("ACTIVE", program["standing_packets"][0]["state"])
        self.assertEqual("active", program["active_leases"][0]["status"])
        self.assertEqual(scheduler.STATUS_HOLD, second["status"])
        self.assertEqual("standing_packet_not_ready", second["blocked_candidates"][0]["blocked_reason"])

    def test_terminal_receipt_releases_only_exact_correlated_lease(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        first = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=first)
        intent = program["delivery_intents"][0]
        terminal = _envelope(
            {
                "canonical_lifecycle_state": "COMPLETED",
                "terminal": True,
                "packet_id": "fitness-ready",
                "writer_scope": "repo.fitness",
                "reservation_id": reservations[0]["reservation_id"],
                "turn_id": "turn-fitness-1",
            },
            idempotency_key="fitness-terminal",
        )
        premature, premature_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[terminal],
        )
        program, delivery_findings = scheduler.apply_delivery_results(
            program=premature,
            results=[
                {
                    "reservation_id": reservations[0]["reservation_id"],
                    "packet_id": "fitness-ready",
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "DELIVERED",
                    "turn_id": "turn-fitness-1",
                }
            ],
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[terminal],
        )

        self.assertEqual("terminal_lease_correlation_required", premature_findings[0]["code"])
        self.assertEqual([], premature["processed_events"])
        self.assertEqual([], delivery_findings)
        self.assertEqual([], findings)
        self.assertEqual([], program["active_leases"])
        self.assertEqual(["fitness-ready"], program["completed_packets"])
        self.assertEqual([], program["standing_packets"])
        self.assertEqual("released", program["released_leases"][0]["status"])
        self.assertEqual("turn-fitness-1", program["completed_receipts"][0]["turn_id"])
        self.assertEqual([], program["delivery_intents"])

    def test_terminal_receipt_cannot_release_a_different_reservation(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "fitness-ready",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness",
        )
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-receipt"}
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "packet_id": "fitness-ready",
                "writer_scope": "repo.fitness",
                "status": "active",
                "reservation_id": "rsrv-other",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-receipt",
                "packet_id": "fitness-ready",
                "writer_scope": "repo.fitness",
                "status": "delivered",
                "turn_id": "turn-fitness-2",
            }
        ]
        terminal = _envelope(
            {
                "canonical_lifecycle_state": "COMPLETED",
                "terminal": True,
                "packet_id": "fitness-ready",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv-receipt",
                "turn_id": "turn-fitness-2",
            },
            idempotency_key="fitness-terminal-mismatch",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[terminal],
        )

        self.assertEqual("terminal_lease_correlation_required", findings[0]["code"])
        self.assertEqual("rsrv-other", program["active_leases"][0]["reservation_id"])
        self.assertEqual([], program["completed_packets"])

    def test_terminal_read_only_finding_completes_only_the_exact_delivered_packet(self) -> None:
        packet = _standing_packet(
            "scheduler-review",
            role_id="atlas.release-control-plane",
            repository="fawxzzy/ATLAS",
            writer_scope="read.github.fawxzzy.atlas.scheduler-review",
        )
        packet["execution_class"] = "read_only"
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-review"}
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-review",
                "packet_id": "scheduler-review",
                "runtime_thread_id": "release-thread",
                "writer_scope": "read.github.fawxzzy.atlas.scheduler-review",
                "event_id": "onv1_" + "c" * 64,
                "payload_digest": "sha256:" + "c" * 64,
                "status": "delivered",
                "turn_id": "review-turn",
            }
        ]
        finding = _envelope(
            {
                "canonical_lifecycle_state": "REVIEW_FINDINGS_PENDING",
                "terminal": True,
                "packet_id": "scheduler-review",
                "writer_scope": "read.github.fawxzzy.atlas.scheduler-review",
                "reservation_id": "rsrv-review",
                "turn_id": "review-turn",
            },
            idempotency_key="scheduler-review-finding",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("atlas.release-control-plane", "release-thread", "idle")),
            envelopes=[finding],
        )

        self.assertEqual([], findings)
        self.assertEqual(["scheduler-review"], program["completed_packets"])
        self.assertEqual([], program["standing_packets"])
        self.assertEqual([], program["delivery_intents"])
        self.assertEqual("REVIEW_FINDINGS_PENDING", program["completed_receipts"][0]["terminal_disposition"])

    def test_terminal_mutating_blocker_holds_exact_packet_and_lease_for_resume(self) -> None:
        packet = _standing_packet(
            "fitness-source",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-fitness-source"}
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "status": "active",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "runtime_thread_id": "fitness-thread",
                "writer_scope": "repo.fitness.source",
                "event_id": "onv1_" + "c" * 64,
                "payload_digest": "sha256:" + "c" * 64,
                "status": "delivered",
                "turn_id": "fitness-turn",
            }
        ]
        blocker = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKED_EXACT_MISSING_EVIDENCE",
                "terminal": True,
                "blocking": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "turn_id": "fitness-turn",
            },
            idempotency_key="fitness-source-blocked",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[blocker],
        )
        program, replay_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[blocker],
        )

        self.assertEqual([], findings)
        self.assertEqual([], replay_findings)
        self.assertEqual("BLOCKED", program["standing_packets"][0]["state"])
        self.assertEqual(blocker["event_id"], program["standing_packets"][0]["blocking_receipt"]["event_id"])
        self.assertEqual("active", program["active_leases"][0]["status"])
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual([], program["completed_packets"])

    def test_terminal_mutating_blocker_rejects_packet_reservation_mismatch(self) -> None:
        packet = _standing_packet(
            "fitness-source",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-other"}
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "status": "active",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "runtime_thread_id": "fitness-thread",
                "writer_scope": "repo.fitness.source",
                "event_id": "onv1_" + "c" * 64,
                "payload_digest": "sha256:" + "c" * 64,
                "status": "delivered",
                "turn_id": "fitness-turn",
            }
        ]
        blocker = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKED_EXACT_MISSING_EVIDENCE",
                "terminal": True,
                "blocking": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "turn_id": "fitness-turn",
            },
            idempotency_key="fitness-source-blocked-mismatch",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[blocker],
        )

        self.assertEqual("terminal_mutating_blocker_correlation_required", findings[0]["code"])
        self.assertEqual("ACTIVE", program["standing_packets"][0]["state"])
        self.assertNotIn("blocking_receipt", program["standing_packets"][0])
        self.assertEqual("active", program["active_leases"][0]["status"])
        self.assertEqual([], program["completed_packets"])

    def test_blocker_resume_reuses_the_exact_reservation_lease_and_delivery_intent(self) -> None:
        packet = _standing_packet(
            "fitness-source",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-fitness-source", "runtime_thread_id": "fitness-thread"}
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {"files": ["src/feature.py"], "worktrees": ["fitness-worktree"]},
                "status": "active",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "runtime_thread_id": "fitness-thread",
                "writer_scope": "repo.fitness.source",
                "event_id": packet["authority"]["event_id"],
                "payload_digest": packet["authority"]["payload_digest"],
                "status": "delivered",
                "turn_id": "blocked-turn",
            }
        ]
        blocker = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKED_EXACT_MISSING_EVIDENCE",
                "terminal": True,
                "blocking": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "turn_id": "blocked-turn",
            },
            idempotency_key="fitness-source-blocked-for-resume",
        )
        program, blocker_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[blocker],
        )
        resume = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKER_CLEARED_RESUME_AUTHORITY",
                "resume_authority": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "prior_blocking_receipt_event_id": blocker["event_id"],
                "prior_blocking_receipt_payload_digest": blocker["payload_digest"],
                "current_delivered_turn_id": "blocked-turn",
            },
            idempotency_key="fitness-source-resume",
            source_role_id="atlas.main",
        )
        program, resume_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[resume],
        )
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)

        self.assertEqual([], blocker_findings)
        self.assertEqual([], resume_findings)
        self.assertEqual(["fitness-source"], [job["packet_id"] for job in report["selected_jobs"]])
        self.assertEqual("rsrv-fitness-source", reservations[0]["reservation_id"])
        self.assertTrue(reservations[0]["recovery_resume"])
        self.assertEqual(1, len(program["active_leases"]))
        self.assertEqual("active", program["active_leases"][0]["status"])
        self.assertEqual(1, len(program["delivery_intents"]))
        self.assertEqual("prepared", program["delivery_intents"][0]["status"])
        self.assertIsNone(program["delivery_intents"][0]["turn_id"])
        self.assertEqual("blocked-turn", program["delivery_intents"][0]["recovery_superseded_turn_id"])
        self.assertEqual(resume["event_id"], program["delivery_intents"][0]["event_id"])
        self.assertEqual(resume["payload_digest"], program["delivery_intents"][0]["payload_digest"])
        self.assertEqual(
            packet["authority"],
            program["delivery_intents"][0]["superseded_delivery_authorities"][0],
        )

    def test_blocker_resume_rejects_replacement_runtime_binding(self) -> None:
        packet = _standing_packet(
            "fitness-source",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        packet["state"] = "BLOCKED"
        packet["runtime_thread_id"] = "fitness-thread"
        packet["dispatch_reservation"] = {
            "reservation_id": "rsrv-fitness-source",
            "runtime_thread_id": "fitness-thread",
        }
        packet["blocking_receipt"] = {
            "event_id": "onv1_" + "c" * 64,
            "payload_digest": "sha256:" + "c" * 64,
            "canonical_lifecycle_state": "BLOCKED_EXACT_MISSING_EVIDENCE",
            "turn_id": "blocked-turn",
        }
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {"files": ["src/feature.py"], "worktrees": ["fitness-worktree"]},
                "status": "active",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "runtime_thread_id": "fitness-thread",
                "writer_scope": "repo.fitness.source",
                "event_id": packet["authority"]["event_id"],
                "payload_digest": packet["authority"]["payload_digest"],
                "status": "delivered",
                "turn_id": "blocked-turn",
            }
        ]
        resume = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKER_CLEARED_RESUME_AUTHORITY",
                "resume_authority": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "prior_blocking_receipt_event_id": packet["blocking_receipt"]["event_id"],
                "prior_blocking_receipt_payload_digest": packet["blocking_receipt"]["payload_digest"],
                "current_delivered_turn_id": "blocked-turn",
            },
            idempotency_key="fitness-source-replacement-runtime-resume",
            source_role_id="atlas.main",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "replacement-thread", "idle")),
            envelopes=[resume],
        )

        self.assertEqual("blocker_resume_runtime_binding_drift", findings[0]["code"])
        self.assertEqual("fitness-thread", findings[0]["details"]["expected_runtime_thread_id"])
        self.assertEqual("replacement-thread", findings[0]["details"]["observed_runtime_thread_id"])
        self.assertEqual("BLOCKED", program["standing_packets"][0]["state"])
        self.assertNotIn("resume_authority", program["standing_packets"][0])
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("fitness-thread", program["delivery_intents"][0]["runtime_thread_id"])
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_blocker_resume_can_repeat_after_a_new_exact_blocker(self) -> None:
        packet = _standing_packet(
            "fitness-source",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-fitness-source", "runtime_thread_id": "fitness-thread"}
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {"files": ["src/feature.py"], "worktrees": ["fitness-worktree"]},
                "status": "active",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "runtime_thread_id": "fitness-thread",
                "writer_scope": "repo.fitness.source",
                "event_id": packet["authority"]["event_id"],
                "payload_digest": packet["authority"]["payload_digest"],
                "status": "delivered",
                "turn_id": "first-blocked-turn",
            }
        ]

        first_blocker = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKED_EXACT_MISSING_EVIDENCE",
                "terminal": True,
                "blocking": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "turn_id": "first-blocked-turn",
            },
            idempotency_key="fitness-source-first-repeat-blocker",
        )
        program, first_blocker_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[first_blocker],
        )
        first_resume = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKER_CLEARED_RESUME_AUTHORITY",
                "resume_authority": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "prior_blocking_receipt_event_id": first_blocker["event_id"],
                "prior_blocking_receipt_payload_digest": first_blocker["payload_digest"],
                "current_delivered_turn_id": "first-blocked-turn",
            },
            idempotency_key="fitness-source-first-repeat-resume",
            source_role_id="atlas.main",
        )
        program, first_resume_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[first_resume],
        )
        first_report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, _ = scheduler.reserve_selected_jobs(program=program, report=first_report)
        first_intent = program["delivery_intents"][0]
        program, delivery_findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": "rsrv-fitness-source",
                    "packet_id": "fitness-source",
                    "runtime_thread_id": "fitness-thread",
                    "event_id": first_intent["event_id"],
                    "payload_digest": first_intent["payload_digest"],
                    "status": "DELIVERED",
                    "turn_id": "second-blocked-turn",
                }
            ],
        )
        second_blocker = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKED_EXACT_MISSING_EVIDENCE",
                "terminal": True,
                "blocking": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "turn_id": "second-blocked-turn",
            },
            idempotency_key="fitness-source-second-repeat-blocker",
        )
        program, second_blocker_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[second_blocker],
        )
        second_resume = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKER_CLEARED_RESUME_AUTHORITY",
                "resume_authority": True,
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "reservation_id": "rsrv-fitness-source",
                "prior_blocking_receipt_event_id": second_blocker["event_id"],
                "prior_blocking_receipt_payload_digest": second_blocker["payload_digest"],
                "current_delivered_turn_id": "second-blocked-turn",
            },
            idempotency_key="fitness-source-second-repeat-resume",
            source_role_id="atlas.main",
        )
        program, second_resume_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[second_resume],
        )
        second_report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], first_blocker_findings)
        self.assertEqual([], first_resume_findings)
        self.assertEqual([], delivery_findings)
        self.assertEqual([], second_blocker_findings)
        self.assertEqual([], second_resume_findings)
        self.assertEqual(["fitness-source"], [job["packet_id"] for job in second_report["selected_jobs"]])
        self.assertEqual(second_resume["event_id"], program["delivery_intents"][0]["event_id"])
        self.assertEqual(
            [packet["authority"]["event_id"], first_resume["event_id"]],
            [item["event_id"] for item in program["delivery_intents"][0]["superseded_delivery_authorities"]],
        )
        self.assertEqual(first_resume["event_id"], program["standing_packets"][0]["resume_authority_history"][0]["event_id"])

    def test_blocker_resume_is_blocked_by_a_same_scope_hold(self) -> None:
        program = _recovery_ready_program()
        program["scope_holds"] = [
            {
                "packet_id": "held-peer",
                "writer_scope": "repo.fitness.source",
                "status": "operator-hold",
            }
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("recovery_writer_scope_hold", report["blocked_candidates"][0]["blocked_reason"])

    def test_blocker_resume_revalidates_peer_lease_before_reservation(self) -> None:
        program = _recovery_ready_program()
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program["active_leases"].append(
            {
                "reservation_id": "rsrv-peer",
                "packet_id": "fitness-peer",
                "writer_scope": "repo.fitness.source",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {"files": ["src/peer.py"], "worktrees": ["peer-worktree"]},
                "status": "active",
            }
        )
        before = copy.deepcopy(program)

        with self.assertRaisesRegex(RuntimeError, "recovery peer lease conflict appeared before dispatch"):
            scheduler.reserve_selected_jobs(program=program, report=report)

        self.assertEqual(before, program)
        self.assertEqual(scheduler.RECOVERY_READY_STATE, program["standing_packets"][0]["state"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])

    def test_blocker_resume_revalidates_scope_hold_before_reservation(self) -> None:
        program = _recovery_ready_program()
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program["scope_holds"] = [{"writer_scope": "repo.fitness.source", "status": "operator-hold"}]
        before = copy.deepcopy(program)

        with self.assertRaisesRegex(RuntimeError, "recovery writer scope became held before dispatch"):
            scheduler.reserve_selected_jobs(program=program, report=report)

        self.assertEqual(before, program)
        self.assertEqual(scheduler.RECOVERY_READY_STATE, program["standing_packets"][0]["state"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])

    def test_blocker_resume_rejects_duplicate_peer_lease(self) -> None:
        packet = _standing_packet(
            "fitness-source",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.source",
        )
        packet["state"] = scheduler.RECOVERY_READY_STATE
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-fitness-source"}
        packet["resume_authority"] = {
            "event_id": "onv1_" + "d" * 64,
            "payload_digest": "sha256:" + "d" * 64,
            "reservation_id": "rsrv-fitness-source",
            "current_delivered_turn_id": "blocked-turn",
        }
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "writer_scope": "repo.fitness.source",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {"files": ["src/feature.py"], "worktrees": ["fitness-worktree"]},
                "status": "recovery-required",
            },
            {
                "reservation_id": "rsrv-peer",
                "packet_id": "fitness-peer",
                "writer_scope": "repo.fitness.source",
                "repository": "fawxzzy/fitness",
                "execution_class": "repo_worktree",
                "resource_claims": {"files": ["src/peer.py"], "worktrees": ["peer-worktree"]},
                "status": "active",
            },
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-fitness-source",
                "packet_id": "fitness-source",
                "runtime_thread_id": packet["runtime_thread_id"],
                "writer_scope": "repo.fitness.source",
                "event_id": packet["resume_authority"]["event_id"],
                "payload_digest": packet["resume_authority"]["payload_digest"],
                "status": "recovery-required",
                "turn_id": None,
                "recovery_superseded_turn_id": "blocked-turn",
            }
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], report["selected_jobs"])
        self.assertEqual("recovery_peer_writer_scope_conflict", report["blocked_candidates"][0]["blocked_reason"])

    def test_supersession_cancels_ready_or_exact_prepared_packet_only(self) -> None:
        ready = _standing_packet(
            "ready-stale",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness.ready",
        )
        prepared = _standing_packet(
            "prepared-stale",
            role_id="owner.mazer",
            repository="fawxzzy/mazer",
            writer_scope="repo.mazer.prepared",
        )
        prepared["state"] = "ACTIVE"
        prepared["dispatch_reservation"] = {"reservation_id": "rsrv-prepared"}
        program = _program_payload()
        program["standing_packets"] = [ready, prepared]
        program["active_leases"] = [
            {
                "packet_id": "prepared-stale",
                "writer_scope": "repo.mazer.prepared",
                "status": "active",
                "reservation_id": "rsrv-prepared",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-prepared",
                "packet_id": "prepared-stale",
                "writer_scope": "repo.mazer.prepared",
                "status": "prepared",
            }
        ]
        envelopes = [
            _envelope(
                {
                    "canonical_lifecycle_state": "SUPERSEDED",
                    "terminal": True,
                    "packet_id": "ready-stale",
                    "writer_scope": "repo.fitness.ready",
                    "superseded_by_packet_id": "ready-current",
                },
                idempotency_key="ready-stale-superseded",
                source_role_id="atlas.main",
            ),
            _envelope(
                {
                    "canonical_lifecycle_state": "SUPERSEDED",
                    "terminal": True,
                    "packet_id": "prepared-stale",
                    "writer_scope": "repo.mazer.prepared",
                    "reservation_id": "rsrv-prepared",
                    "superseded_by_packet_id": "prepared-current",
                },
                idempotency_key="prepared-stale-superseded",
                source_role_id="atlas.main",
            ),
        ]

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(
                ("owner.fitness", "fitness-thread", "idle"),
                ("owner.mazer", "mazer-thread", "idle"),
            ),
            envelopes=envelopes,
        )

        self.assertEqual([], findings)
        self.assertEqual([], program["standing_packets"])
        self.assertEqual([], program["active_leases"])
        self.assertEqual([], program["delivery_intents"])
        self.assertEqual(["prepared-stale", "ready-stale"], program["completed_packets"])
        self.assertEqual("cancelled-before-delivery", program["released_leases"][0]["status"])
        self.assertTrue(all(item["turn_id"] is None for item in program["completed_receipts"]))

    def test_supersession_cannot_cancel_delivered_or_uncorrelated_packet(self) -> None:
        packet = _standing_packet(
            "delivered-packet",
            role_id="owner.fitness",
            repository="fawxzzy/fitness",
            writer_scope="repo.fitness",
        )
        packet["state"] = "ACTIVE"
        packet["dispatch_reservation"] = {"reservation_id": "rsrv-delivered"}
        program = _program_payload()
        program["standing_packets"] = [packet]
        program["active_leases"] = [
            {
                "packet_id": "delivered-packet",
                "writer_scope": "repo.fitness",
                "status": "active",
                "reservation_id": "rsrv-delivered",
            }
        ]
        program["delivery_intents"] = [
            {
                "reservation_id": "rsrv-delivered",
                "packet_id": "delivered-packet",
                "writer_scope": "repo.fitness",
                "status": "delivered",
                "turn_id": "turn-delivered",
            }
        ]
        superseded = _envelope(
            {
                "canonical_lifecycle_state": "SUPERSEDED",
                "terminal": True,
                "packet_id": "delivered-packet",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv-delivered",
                "superseded_by_packet_id": "newer-packet",
            },
            idempotency_key="delivered-supersession-rejected",
            source_role_id="atlas.main",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[superseded],
        )

        self.assertEqual("terminal_cancellation_correlation_required", findings[0]["code"])
        self.assertEqual("active", program["active_leases"][0]["status"])
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual([], program["completed_packets"])

    def test_recovery_absence_proof_releases_only_the_orphaned_reservation_for_one_successor(self) -> None:
        program, bindings, _ = _orphaned_web_delivery_program()
        original_reservation = program["delivery_intents"][0]["reservation_id"]
        unrelated_lease = {
            "reservation_id": "rsrv_" + "9" * 64,
            "packet_id": "unrelated-platform-source",
            "logical_role_id": "platform.supabase-migration",
            "runtime_thread_id": "platform-thread",
            "writer_scope": "repo.fawxzzy-platform.unrelated",
            "repository": "fawxzzy/fawxzzy-platform",
            "execution_class": "repo_worktree",
            "resource_claims": {
                "files": ["bootstrap/manifests/namespace-plan.v1.json"],
                "worktrees": ["platform-unrelated"],
                "ports": [],
                "browsers": [],
                "external_writers": [],
            },
            "status": "active",
        }
        preserved_receipt = {"packet_id": "already-complete", "receipt_event_id": "onv1_" + "8" * 64}
        program["active_leases"].append(unrelated_lease)
        program["completed_receipts"].append(preserved_receipt)
        successor = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor",
            source_role_id="owner.fawxzzyweb",
        )
        recovery = _web_recovery_absence_envelope(program=program, successor=successor)

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )

        self.assertEqual([], findings)
        self.assertEqual(["fawxzzyweb-pr30-guarded-source-merge"], program["completed_packets"])
        self.assertEqual("fawxzzyweb-pr30-guarded-source-merge-retry-1", program["standing_packets"][0]["packet_id"])
        self.assertEqual([unrelated_lease], program["active_leases"])
        self.assertEqual([], program["delivery_intents"])
        self.assertEqual("recovery-absence-proven", program["released_leases"][0]["status"])
        self.assertEqual(preserved_receipt, program["completed_receipts"][0])
        recovery_receipt = next(
            item
            for item in program["completed_receipts"]
            if item.get("packet_id") == "fawxzzyweb-pr30-guarded-source-merge"
        )
        self.assertEqual(
            recovery["payload"]["delivery_recovery_evidence_digest"],
            recovery_receipt["recovery_absence_evidence_digest"],
        )

        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        self.assertEqual(["fawxzzyweb-pr30-guarded-source-merge-retry-1"], [item["packet_id"] for item in report["selected_jobs"]])
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)

        self.assertEqual(1, len(reservations))
        self.assertNotEqual(original_reservation, reservations[0]["reservation_id"])
        self.assertEqual("prepared", program["delivery_intents"][0]["status"])
        duplicate = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        self.assertEqual([], duplicate["selected_jobs"])

    def test_recovery_existing_turn_is_bound_and_cannot_be_released_as_absent(self) -> None:
        program, bindings, _ = _orphaned_web_delivery_program()
        intent = program["delivery_intents"][0]
        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": intent["reservation_id"],
                    "packet_id": intent["packet_id"],
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "DELIVERED",
                    "turn_id": "release-control-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": intent["event_id"],
                    "effects_match_intent": True,
                }
            ],
        )
        self.assertEqual([], findings)
        successor = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor-existing-turn",
            source_role_id="owner.fawxzzyweb",
        )
        recovery = _web_recovery_absence_envelope(program=program, successor=successor)

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )

        self.assertEqual("recovery_absence_correlation_required", findings[0]["code"])
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("release-control-turn", program["delivery_intents"][0]["turn_id"])
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_recovery_absence_remains_held_when_complete_history_is_ambiguous(self) -> None:
        program, bindings, _ = _orphaned_web_delivery_program()
        successor = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor-ambiguous",
            source_role_id="owner.fawxzzyweb",
        )
        recovery = _web_recovery_absence_envelope(
            program=program,
            successor=successor,
            evidence_updates={"history_complete": False, "original_call_state": "UNKNOWN"},
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )

        self.assertEqual("recovery_absence_not_proven", findings[0]["code"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])
        self.assertEqual("recovery-required", program["active_leases"][0]["status"])
        self.assertEqual([], program["completed_packets"])

    def test_recovery_absence_rejects_stale_or_mismatched_identity(self) -> None:
        cases = [
            ("stale reservation", {}, {"reservation_id": "rsrv_" + "0" * 64}, "recovery_absence_correlation_required"),
            ("wrong packet", {}, {"packet_id": "different-packet"}, "recovery_absence_correlation_required"),
            ("wrong scope", {}, {"writer_scope": "github.fawxzzy.other.pr30"}, "recovery_absence_correlation_required"),
            ("wrong event", {"event_id": "onv1_" + "1" * 64}, {}, "recovery_absence_evidence_identity_mismatch"),
            ("wrong digest", {"payload_digest": "sha256:" + "2" * 64}, {}, "recovery_absence_evidence_identity_mismatch"),
            ("semantic extra", {"unexpected": True}, {}, "recovery_absence_evidence_shape_invalid"),
            (
                "malformed target history receipt",
                {"target_history_receipt_event_id": "not-an-event-id"},
                {},
                "recovery_absence_history_receipt_invalid",
            ),
            (
                "unbound evidence digest",
                {},
                {"delivery_recovery_evidence_digest": "sha256:" + "3" * 64},
                "recovery_absence_evidence_digest_mismatch",
            ),
        ]
        for label, evidence_updates, payload_updates, expected_code in cases:
            with self.subTest(label=label):
                program, bindings, _ = _orphaned_web_delivery_program()
                successor = _envelope(
                    _web_release_packet_payload(
                        "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                        replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
                    ),
                    idempotency_key=f"fawxzzyweb-pr30-successor-{label}",
                    source_role_id="owner.fawxzzyweb",
                )
                recovery = _web_recovery_absence_envelope(
                    program=program,
                    successor=successor,
                    evidence_updates=evidence_updates,
                    payload_updates=payload_updates,
                )

                program, findings = scheduler.reconcile_runtime_program(
                    program=program,
                    bindings_payload=bindings,
                    envelopes=[successor, recovery],
                )

                self.assertEqual(expected_code, findings[0]["code"])
                self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])
                self.assertEqual("recovery-required", program["active_leases"][0]["status"])

    def test_recovery_absence_rejects_duplicate_successors(self) -> None:
        program, bindings, _ = _orphaned_web_delivery_program()
        first = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor-first",
            source_role_id="owner.fawxzzyweb",
        )
        second = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-2",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor-second",
            source_role_id="owner.fawxzzyweb",
        )
        recovery = _web_recovery_absence_envelope(program=program, successor=first)

        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[first, second, recovery],
        )

        self.assertEqual("recovery_absence_exact_successor_required", findings[0]["code"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])
        self.assertEqual("recovery-required", program["active_leases"][0]["status"])

    def test_recovery_absence_replay_is_idempotent(self) -> None:
        program, bindings, _ = _orphaned_web_delivery_program()
        successor = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor-replay",
            source_role_id="owner.fawxzzyweb",
        )
        recovery = _web_recovery_absence_envelope(program=program, successor=successor)
        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )
        self.assertEqual([], findings)
        frozen = copy.deepcopy(program)

        program, replay_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )

        self.assertEqual([], replay_findings)
        self.assertEqual(frozen, program)

    def test_crash_after_successor_reservation_cannot_replay_the_absent_delivery(self) -> None:
        program, bindings, _ = _orphaned_web_delivery_program()
        original_intent = copy.deepcopy(program["delivery_intents"][0])
        successor = _envelope(
            _web_release_packet_payload(
                "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
            ),
            idempotency_key="fawxzzyweb-pr30-successor-crash",
            source_role_id="owner.fawxzzyweb",
        )
        recovery = _web_recovery_absence_envelope(program=program, successor=successor)
        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )
        self.assertEqual([], findings)
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        successor_reservation = reservations[0]["reservation_id"]

        program, replay_findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": original_intent["reservation_id"],
                    "packet_id": original_intent["packet_id"],
                    "runtime_thread_id": original_intent["runtime_thread_id"],
                    "event_id": original_intent["event_id"],
                    "payload_digest": original_intent["payload_digest"],
                    "status": "RECOVERY_REQUIRED",
                }
            ],
        )
        program, envelope_replay_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=bindings,
            envelopes=[successor, recovery],
        )
        retry = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], replay_findings)
        self.assertEqual([], envelope_replay_findings)
        self.assertEqual([], retry["selected_jobs"])
        self.assertEqual(1, len(program["delivery_intents"]))
        self.assertEqual(successor_reservation, program["delivery_intents"][0]["reservation_id"])
        self.assertEqual("prepared", program["delivery_intents"][0]["status"])

    def test_main_cold_start_retires_proven_absent_delivery_and_dispatches_successor_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            program, bindings, _ = _orphaned_web_delivery_program()
            original_intent = copy.deepcopy(program["delivery_intents"][0])
            successor = _envelope(
                _web_release_packet_payload(
                    "fawxzzyweb-pr30-guarded-source-merge-retry-1",
                    replaces_packet_id="fawxzzyweb-pr30-guarded-source-merge",
                ),
                idempotency_key="fawxzzyweb-pr30-successor-main-cold-start",
                source_role_id="owner.fawxzzyweb",
            )
            recovery = _web_recovery_absence_envelope(program=program, successor=successor)
            delivery_replay = {
                "reservation_id": original_intent["reservation_id"],
                "packet_id": original_intent["packet_id"],
                "runtime_thread_id": original_intent["runtime_thread_id"],
                "event_id": original_intent["event_id"],
                "payload_digest": original_intent["payload_digest"],
                "status": "RECOVERY_REQUIRED",
            }
            _write(root / "tmp/atlas/program.json", json.dumps(program, indent=2) + "\n")
            _write(root / "tmp/atlas/bindings.json", json.dumps(bindings, indent=2) + "\n")
            _write(
                root / "tmp/atlas/envelopes.jsonl",
                json.dumps(successor) + "\n" + json.dumps(recovery) + "\n",
            )
            _write(root / "tmp/atlas/delivery.jsonl", json.dumps(delivery_replay) + "\n")
            args = [
                "--json",
                "--program",
                "tmp/atlas/program.json",
                "--bindings",
                "tmp/atlas/bindings.json",
                "--envelopes",
                "tmp/atlas/envelopes.jsonl",
                "--delivery-results",
                "tmp/atlas/delivery.jsonl",
                "--output",
                "tmp/atlas/report.json",
                "--prompt-output",
                "tmp/atlas/prompt.md",
            ]
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(scheduler.ai_work_session_preflight, "build_report", return_value=_preflight_payload()):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    with redirect_stdout(io.StringIO()):
                                        first_exit = scheduler.main(args)
                                    first_report = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
                                    first_program = json.loads((root / "tmp/atlas/program.json").read_text(encoding="utf-8"))
                                    with redirect_stdout(io.StringIO()):
                                        second_exit = scheduler.main(args)
                                    second_report = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
                                    second_program = json.loads((root / "tmp/atlas/program.json").read_text(encoding="utf-8"))

        self.assertEqual(0, first_exit)
        self.assertEqual([], first_report["bridge_findings"])
        self.assertEqual(
            ["fawxzzyweb-pr30-guarded-source-merge-retry-1"],
            [item["packet_id"] for item in first_report["dispatch_plan"]],
        )
        self.assertEqual(["fawxzzyweb-pr30-guarded-source-merge"], first_program["completed_packets"])
        self.assertEqual(1, len(first_program["delivery_intents"]))
        self.assertEqual("prepared", first_program["delivery_intents"][0]["status"])
        self.assertNotEqual(original_intent["reservation_id"], first_program["delivery_intents"][0]["reservation_id"])
        self.assertEqual(0, second_exit)
        self.assertEqual([], second_report["bridge_findings"])
        self.assertEqual([], second_report["dispatch_plan"])
        self.assertEqual(first_program, second_program)

    def test_cold_start_supersession_accepts_only_the_deterministic_prior_reservation(self) -> None:
        payload = {
            "canonical_lifecycle_state": "READY",
            "packet_id": "cold-stale",
            "objective": "Obsolete exact-head review request.",
            "logical_role_id": "atlas.release-control-plane",
            "repository": "fawxzzy/ATLAS",
            "writer_scope": "github.fawxzzy.ATLAS.pr146.review.stale",
            "execution_class": "external_mutation",
            "protected_surface_authorized": True,
            "dependencies": [],
            "resource_claims": {
                "files": [],
                "worktrees": [],
                "ports": [],
                "browsers": [],
                "external_writers": ["github:fawxzzy/ATLAS#146:review:stale"],
            },
        }
        ready = _envelope(payload, idempotency_key="cold-stale-ready", source_role_id="atlas.main")
        expected_packet = {
            "packet_id": "cold-stale",
            "writer_scope": "github.fawxzzy.ATLAS.pr146.review.stale",
            "runtime_thread_id": "release-thread",
            "authority": {
                "event_id": ready["event_id"],
                "payload_digest": ready["payload_digest"],
            },
        }
        reservation_id = scheduler._deterministic_reservation_id(expected_packet)
        superseded = _envelope(
            {
                "canonical_lifecycle_state": "SUPERSEDED",
                "terminal": True,
                "packet_id": "cold-stale",
                "writer_scope": "github.fawxzzy.ATLAS.pr146.review.stale",
                "reservation_id": reservation_id,
                "superseded_by_packet_id": "cold-current",
            },
            idempotency_key="cold-stale-superseded",
            source_role_id="atlas.main",
        )

        program, findings = scheduler.reconcile_runtime_program(
            program=_program_payload(),
            bindings_payload=_bindings(("atlas.release-control-plane", "release-thread", "idle")),
            envelopes=[ready, superseded],
        )

        self.assertEqual([], findings)
        self.assertEqual([], program["standing_packets"])
        self.assertEqual(["cold-stale"], program["completed_packets"])
        self.assertEqual(reservation_id, program["completed_receipts"][0]["reservation_id"])

    def test_ambiguous_delivery_enters_recovery_without_retry(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        intent = program["delivery_intents"][0]
        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": reservations[0]["reservation_id"],
                    "packet_id": "fitness-ready",
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "RECOVERY_REQUIRED",
                }
            ],
        )
        retry = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual([], findings)
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])
        self.assertEqual("recovery-required", program["active_leases"][0]["status"])
        self.assertEqual(scheduler.STATUS_HOLD, retry["status"])

        program, premature = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": reservations[0]["reservation_id"],
                    "packet_id": "fitness-ready",
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "DELIVERED",
                    "turn_id": "fitness-turn",
                }
            ],
        )

        self.assertEqual("delivery_recovery_evidence_required", premature[0]["code"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])

        program, legacy = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": reservations[0]["reservation_id"],
                    "packet_id": "fitness-ready",
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "DELIVERED",
                    "turn_id": "fitness-turn",
                    "reconciled_from_complete_target_history": True,
                }
            ],
        )

        self.assertEqual("delivery_recovery_evidence_required", legacy[0]["code"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])

        program, recovered = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": reservations[0]["reservation_id"],
                    "packet_id": "fitness-ready",
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "DELIVERED",
                    "turn_id": "fitness-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": intent["event_id"],
                    "effects_match_intent": True,
                }
            ],
        )

        self.assertEqual([], recovered)
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_append_only_recovery_correction_clears_superseded_evidence_finding(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        intent = program["delivery_intents"][0]
        correlation = {
            "reservation_id": reservations[0]["reservation_id"],
            "packet_id": "fitness-ready",
            "runtime_thread_id": intent["runtime_thread_id"],
            "event_id": intent["event_id"],
            "payload_digest": intent["payload_digest"],
        }

        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {**correlation, "status": "RECOVERY_REQUIRED"},
                {**correlation, "status": "DELIVERED", "turn_id": "fitness-turn"},
                {
                    **correlation,
                    "status": "DELIVERED",
                    "turn_id": "fitness-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": intent["event_id"],
                    "effects_match_intent": True,
                },
            ],
        )

        self.assertEqual([], findings)
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("fitness-turn", program["delivery_intents"][0]["turn_id"])
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_recovery_can_supersede_an_interrupted_delivery_turn_with_exact_history_proof(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        intent = program["delivery_intents"][0]
        correlation = {
            "reservation_id": reservations[0]["reservation_id"],
            "packet_id": "fitness-ready",
            "runtime_thread_id": intent["runtime_thread_id"],
            "event_id": intent["event_id"],
            "payload_digest": intent["payload_digest"],
        }
        program, initial = scheduler.apply_delivery_results(
            program=program,
            results=[{**correlation, "status": "DELIVERED", "turn_id": "interrupted-turn"}],
        )
        self.assertEqual([], initial)

        program, recovered = scheduler.apply_delivery_results(
            program=program,
            results=[
                {**correlation, "status": "RECOVERY_REQUIRED", "superseded_turn_id": "interrupted-turn"},
                {
                    **correlation,
                    "status": "DELIVERED",
                    "turn_id": "resumed-turn",
                    "supersedes_turn_id": "interrupted-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": intent["event_id"],
                    "effects_match_intent": True,
                },
            ],
        )

        self.assertEqual([], recovered)
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("resumed-turn", program["delivery_intents"][0]["turn_id"])
        self.assertNotIn("recovery_superseded_turn_id", program["delivery_intents"][0])
        self.assertEqual(["interrupted-turn"], program["delivery_intents"][0]["superseded_turn_ids"])
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_append_only_exact_supersession_clears_prior_turn_collision(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        intent = program["delivery_intents"][0]
        correlation = {
            "reservation_id": reservations[0]["reservation_id"],
            "packet_id": "fitness-ready",
            "runtime_thread_id": intent["runtime_thread_id"],
            "event_id": intent["event_id"],
            "payload_digest": intent["payload_digest"],
        }

        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {**correlation, "status": "DELIVERED", "turn_id": "interrupted-turn"},
                {**correlation, "status": "RECOVERY_REQUIRED"},
                {**correlation, "status": "DELIVERED", "turn_id": "resumed-turn"},
                {
                    **correlation,
                    "status": "RECOVERY_REQUIRED",
                    "superseded_turn_id": "interrupted-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                },
                {
                    **correlation,
                    "status": "DELIVERED",
                    "turn_id": "resumed-turn",
                    "supersedes_turn_id": "interrupted-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": intent["event_id"],
                    "effects_match_intent": True,
                },
            ],
        )

        self.assertEqual([], findings)
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("resumed-turn", program["delivery_intents"][0]["turn_id"])
        self.assertEqual(["interrupted-turn"], program["delivery_intents"][0]["superseded_turn_ids"])
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_full_delivery_journal_replay_is_idempotent_after_turn_supersession(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        intent = program["delivery_intents"][0]
        correlation = {
            "reservation_id": reservations[0]["reservation_id"],
            "packet_id": "fitness-ready",
            "runtime_thread_id": intent["runtime_thread_id"],
            "event_id": intent["event_id"],
            "payload_digest": intent["payload_digest"],
        }
        journal = [
            {**correlation, "status": "DELIVERED", "turn_id": "interrupted-turn"},
            {**correlation, "status": "RECOVERY_REQUIRED"},
            {**correlation, "status": "DELIVERED", "turn_id": "resumed-turn"},
            {**correlation, "status": "RECOVERY_REQUIRED", "superseded_turn_id": "interrupted-turn"},
            {
                **correlation,
                "status": "DELIVERED",
                "turn_id": "resumed-turn",
                "supersedes_turn_id": "interrupted-turn",
                "history_reconciled": True,
                "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                "reconciled_event_id": intent["event_id"],
                "effects_match_intent": True,
            },
        ]
        program, initial_findings = scheduler.apply_delivery_results(program=program, results=journal)
        self.assertEqual([], initial_findings)

        program, replay_findings = scheduler.apply_delivery_results(program=program, results=journal)

        self.assertEqual([], replay_findings)
        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("resumed-turn", program["delivery_intents"][0]["turn_id"])
        self.assertEqual(["interrupted-turn"], program["delivery_intents"][0]["superseded_turn_ids"])

    def test_completed_delivery_journal_replay_is_idempotent(self) -> None:
        program = _program_payload()
        program["completed_receipts"] = [
            {
                "packet_id": "fitness-complete",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv_" + "a" * 64,
                "turn_id": "fitness-turn",
                "runtime_thread_id": "fitness-thread",
                "event_id": "onv1_" + "b" * 64,
                "payload_digest": "sha256:" + "b" * 64,
            }
        ]
        historical = {
            "reservation_id": "rsrv_" + "a" * 64,
            "packet_id": "fitness-complete",
            "runtime_thread_id": "fitness-thread",
            "event_id": "onv1_" + "b" * 64,
            "payload_digest": "sha256:" + "b" * 64,
        }

        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {**historical, "status": "RECOVERY_REQUIRED", "turn_id": None},
                {**historical, "status": "DELIVERED", "turn_id": "fitness-turn"},
            ],
        )

        self.assertEqual([], findings)
        self.assertEqual([], program["delivery_intents"])
        self.assertEqual([], program["active_leases"])

    def test_completed_delivery_journal_replay_accepts_exact_legacy_supersession_history(self) -> None:
        program = _program_payload()
        program["completed_receipts"] = [
            {
                "packet_id": "fitness-complete",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv_" + "a" * 64,
                "turn_id": "resumed-turn",
                "runtime_thread_id": "fitness-thread",
                "event_id": "onv1_" + "b" * 64,
                "payload_digest": "sha256:" + "b" * 64,
            }
        ]
        historical = {
            "reservation_id": "rsrv_" + "a" * 64,
            "packet_id": "fitness-complete",
            "runtime_thread_id": "fitness-thread",
            "event_id": "onv1_" + "b" * 64,
            "payload_digest": "sha256:" + "b" * 64,
        }

        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {**historical, "status": "DELIVERED", "turn_id": "interrupted-turn"},
                {**historical, "status": "RECOVERY_REQUIRED", "superseded_turn_id": "interrupted-turn"},
                {
                    **historical,
                    "status": "DELIVERED",
                    "turn_id": "resumed-turn",
                    "supersedes_turn_id": "interrupted-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": historical["event_id"],
                    "effects_match_intent": True,
                },
            ],
        )

        self.assertEqual([], findings)
        self.assertEqual(["interrupted-turn"], program["completed_receipts"][0]["superseded_turn_ids"])

    def test_completed_delivery_journal_replay_rejects_unproved_old_turn(self) -> None:
        program = _program_payload()
        program["completed_receipts"] = [
            {
                "packet_id": "fitness-complete",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv_" + "a" * 64,
                "turn_id": "resumed-turn",
                "runtime_thread_id": "fitness-thread",
                "event_id": "onv1_" + "b" * 64,
                "payload_digest": "sha256:" + "b" * 64,
            }
        ]
        historical = {
            "reservation_id": "rsrv_" + "a" * 64,
            "packet_id": "fitness-complete",
            "runtime_thread_id": "fitness-thread",
            "event_id": "onv1_" + "b" * 64,
            "payload_digest": "sha256:" + "b" * 64,
        }

        _, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {**historical, "status": "DELIVERED", "turn_id": "interrupted-turn"},
                {**historical, "status": "DELIVERED", "turn_id": "resumed-turn"},
            ],
        )

        self.assertEqual("delivery_result_correlation_mismatch", findings[0]["code"])
        self.assertEqual("interrupted-turn", findings[0]["details"]["turn_id"])

    def test_completed_delivery_journal_replay_rejects_self_supersession(self) -> None:
        program = _program_payload()
        program["completed_receipts"] = [
            {
                "packet_id": "fitness-complete",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv_" + "a" * 64,
                "turn_id": "resumed-turn",
                "runtime_thread_id": "fitness-thread",
                "event_id": "onv1_" + "b" * 64,
                "payload_digest": "sha256:" + "b" * 64,
            }
        ]
        historical = {
            "reservation_id": "rsrv_" + "a" * 64,
            "packet_id": "fitness-complete",
            "runtime_thread_id": "fitness-thread",
            "event_id": "onv1_" + "b" * 64,
            "payload_digest": "sha256:" + "b" * 64,
        }

        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    **historical,
                    "status": "DELIVERED",
                    "turn_id": "resumed-turn",
                    "supersedes_turn_id": "resumed-turn",
                    "history_reconciled": True,
                    "reconciliation_basis": scheduler.RECOVERY_RECONCILIATION_BASIS,
                    "reconciled_event_id": historical["event_id"],
                    "effects_match_intent": True,
                }
            ],
        )

        self.assertEqual("completed_receipt_self_supersession_forbidden", findings[0]["code"])
        self.assertNotIn("superseded_turn_ids", program["completed_receipts"][0])

    def test_completed_delivery_journal_replay_rejects_identity_drift(self) -> None:
        program = _program_payload()
        program["completed_receipts"] = [
            {
                "packet_id": "fitness-complete",
                "writer_scope": "repo.fitness",
                "reservation_id": "rsrv_" + "a" * 64,
                "turn_id": "fitness-turn",
                "runtime_thread_id": "fitness-thread",
                "event_id": "onv1_" + "b" * 64,
                "payload_digest": "sha256:" + "b" * 64,
            }
        ]

        _, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": "rsrv_" + "a" * 64,
                    "packet_id": "fitness-complete",
                    "runtime_thread_id": "other-thread",
                    "event_id": "onv1_" + "b" * 64,
                    "payload_digest": "sha256:" + "b" * 64,
                    "status": "DELIVERED",
                    "turn_id": "fitness-turn",
                }
            ],
        )

        self.assertEqual("delivery_result_correlation_mismatch", findings[0]["code"])

    def test_nonterminal_receipt_cannot_release_a_lease(self) -> None:
        program = _program_payload()
        program["active_leases"] = [
            {"packet_id": "fitness-ready", "writer_scope": "repo.fitness", "status": "active", "reservation_id": "rsrv-1"}
        ]
        blocked = _envelope(
            {
                "canonical_lifecycle_state": "BLOCKED",
                "packet_id": "fitness-ready",
                "writer_scope": "repo.fitness",
            },
            idempotency_key="fitness-blocked",
        )
        program, findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[blocked],
        )

        self.assertEqual([], findings)
        self.assertEqual("active", program["active_leases"][0]["status"])

    def test_terminal_receipt_cannot_replace_delivery_recovery_evidence(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        ]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program, reservations = scheduler.reserve_selected_jobs(program=program, report=report)
        intent = program["delivery_intents"][0]
        program, findings = scheduler.apply_delivery_results(
            program=program,
            results=[
                {
                    "reservation_id": reservations[0]["reservation_id"],
                    "packet_id": "fitness-ready",
                    "runtime_thread_id": intent["runtime_thread_id"],
                    "event_id": intent["event_id"],
                    "payload_digest": intent["payload_digest"],
                    "status": "RECOVERY_REQUIRED",
                    "turn_id": "fitness-turn",
                }
            ],
        )
        terminal = _envelope(
            {
                "canonical_lifecycle_state": "COMPLETED",
                "terminal": True,
                "packet_id": "fitness-ready",
                "writer_scope": "repo.fitness",
                "reservation_id": reservations[0]["reservation_id"],
                "turn_id": "fitness-turn",
                "source_receipt_event_id": "onv1_" + "e" * 64,
            },
            idempotency_key="fitness-terminal-recovery",
        )
        program, receipt_findings = scheduler.reconcile_runtime_program(
            program=program,
            bindings_payload=_bindings(("owner.fitness", "fitness-thread", "idle")),
            envelopes=[terminal],
        )

        self.assertEqual([], findings)
        self.assertEqual("terminal_lease_correlation_required", receipt_findings[0]["code"])
        self.assertEqual("recovery-required", program["active_leases"][0]["status"])
        self.assertEqual("recovery-required", program["delivery_intents"][0]["status"])
        self.assertEqual([], program["completed_packets"])

    def test_standing_dependency_requires_completed_receipt(self) -> None:
        program = _program_payload()
        program["standing_packets"] = [
            _standing_packet(
                "ratchet-ready",
                role_id="platform.supabase-migration",
                repository="fawxzzy/fawxzzy-platform",
                writer_scope="program.fawxzzy-platform",
                dependencies=["source-merge"],
            )
        ]
        blocked = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )
        program["completed_packets"] = ["source-merge"]
        ready = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, blocked["status"])
        self.assertEqual("dependencies_not_complete", blocked["blocked_candidates"][0]["blocked_reason"])
        self.assertEqual(scheduler.STATUS_EXECUTE, ready["status"])

    def test_standing_packet_requires_canonical_authority(self) -> None:
        program = _program_payload()
        packet = _standing_packet("fitness-ready", role_id="owner.fitness", repository="fawxzzy/fitness", writer_scope="repo.fitness")
        packet["authority"] = {"event_id": "not-canonical", "payload_digest": "sha256:bad"}
        program["standing_packets"] = [packet]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("canonical_authority_required", report["blocked_candidates"][0]["blocked_reason"])

    def test_product_name_does_not_imply_provider_mutation(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "platform-source",
            role_id="platform.supabase-migration",
            repository="fawxzzy/fawxzzy-platform",
            writer_scope="program.fawxzzy-platform",
        )
        packet["packet"] = "Fawxzzy Supabase platform source contract correction"
        program["standing_packets"] = [packet]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])

    def test_provider_mutation_still_requires_explicit_surface_authority(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "platform-provider",
            role_id="platform.supabase-migration",
            repository="fawxzzy/fawxzzy-platform",
            writer_scope="program.fawxzzy-platform",
        )
        packet["packet"] = "Supabase provider mutation"
        program["standing_packets"] = [packet]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("protected_or_platform_mutation_forbidden", report["blocked_candidates"][0]["blocked_reason"])

    def test_read_only_standing_packet_can_name_protected_exclusions(self) -> None:
        program = _program_payload()
        packet = _standing_packet(
            "bounded-selector",
            role_id="fawxzzy.questions",
            repository="fawxzzy/ATLAS",
            writer_scope="read.atlas.selector",
        )
        packet["execution_class"] = "read_only"
        packet["packet"] = "Read accepted receipts only; do not deploy production or inspect secrets."
        program["standing_packets"] = [packet]
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=program,
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload([]),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual(["bounded-selector"], [job["packet_id"] for job in report["selected_jobs"]])
        self.assertEqual("read_only", report["selected_jobs"][0]["execution_class"])

    def test_read_only_planner_packet_can_name_protected_exclusions(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(error=1),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_IMMEDIATE,
                        "score": 70,
                        "packet": "Read accepted receipts only; do not deploy production or inspect secrets.",
                        "mode": "worker implementation",
                        "logical_role_id": "fawxzzy.questions",
                        "repository": "fawxzzy/ATLAS",
                        "writer_scope": "read.atlas.selector",
                        "execution_class": "read_only",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual("read_only", report["selected_jobs"][0]["execution_class"])

    def test_protected_packet_is_blocked(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "deploy production and edit .github/workflows/release.yml",
                        "mode": "docs-only",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("protected_or_platform_mutation_forbidden", report["blocked_candidates"][0]["blocked_reason"])

    def test_playbook_everywhere_marker_is_not_blocked_by_name_only(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Playbook Everywhere + Cortex Interface",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Playbook Everywhere + Cortex Interface third consumer-class contract freeze",
                        "mode": "docs-only root-bounded contract freeze",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_EXECUTE, report["status"])
        self.assertEqual("Playbook Everywhere + Cortex Interface", report["selected_marker"])

    def test_completed_packet_is_skipped(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_HELD,
                        "score": 10,
                        "packet": "No immediate AI Long-Run Batch Orchestration same-lane packet",
                        "mode": "held after reconciliation",
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.STATUS_HOLD, report["status"])
        self.assertEqual("held_or_stale_packet", report["skipped_candidates"][0]["stale_reason"])

    def test_cross_marker_signal_selects_cross_marker_decision(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(active_lane_is_held=False, action="continue_current_lane", current_packet=None),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "AI Long-Run Batch Orchestration",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 85,
                        "packet": "AI Long-Run Batch Orchestration planner integration contract freeze",
                        "mode": "docs-only root-bounded contract freeze",
                        "cross_marker_signal_applied": True,
                    }
                ]
            ),
        )

        self.assertEqual(scheduler.DECISION_CROSS_MARKER_OPPORTUNITY, report["decision"])

    def test_docs_only_streak_limit_blocks_docs_candidate(self) -> None:
        report = scheduler.build_report(
            root=Path("atlas-root-fixture"),
            program=_program_payload(),
            max_candidates=30,
            preflight_report=_preflight_payload(),
            selector_report=_selector_payload(),
            planner_report=_planner_payload(
                [
                    {
                        "marker": "Cortex Dual-Mode Replacement Readiness",
                        "classification": planner.CLASS_DOCS_ONLY,
                        "score": 70,
                        "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                        "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                    }
                ]
            ),
            recent_docs_only_streak=2,
        )

        self.assertEqual("docs_only_streak_limit", report["blocked_candidates"][0]["blocked_reason"])
        self.assertEqual(scheduler.STATUS_HOLD, report["status"])

    def test_hold_returns_nonzero_in_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp/atlas/program.json", json.dumps(_program_payload(), indent=2) + "\n")
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(
                                scheduler.ai_work_session_preflight,
                                "build_report",
                                return_value=_preflight_payload(),
                            ):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    stdout = io.StringIO()
                                    with redirect_stdout(stdout):
                                        exit_code = scheduler.main(
                                            [
                                                "--json",
                                                "--program",
                                                "tmp/atlas/program.json",
                                                "--output",
                                                "tmp/atlas/report.json",
                                                "--prompt-output",
                                                "tmp/atlas/prompt.md",
                                                "--strict",
                                            ]
                                        )

        self.assertEqual(2, exit_code)
        self.assertEqual(scheduler.STATUS_HOLD, json.loads(stdout.getvalue())["status"])

    def test_main_writes_outputs_to_tmp_atlas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "tmp/atlas/program.json", json.dumps(_program_payload(), indent=2) + "\n")
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(
                                scheduler.ai_work_session_preflight,
                                "build_report",
                                return_value=_preflight_payload(),
                            ):
                                with patch.object(
                                    scheduler.planner,
                                    "build_report",
                                    return_value=_planner_payload(
                                        [
                                            {
                                                "marker": "Cortex Dual-Mode Replacement Readiness",
                                                "classification": planner.CLASS_DOCS_ONLY,
                                                "score": 70,
                                                "packet": "Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
                                                "mode": "docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
                                            }
                                        ]
                                    ),
                                ):
                                    stdout = io.StringIO()
                                    with redirect_stdout(stdout):
                                        exit_code = scheduler.main(
                                            [
                                                "--json",
                                                "--program",
                                                "tmp/atlas/program.json",
                                                "--output",
                                                "tmp/atlas/report.json",
                                                "--prompt-output",
                                                "tmp/atlas/prompt.md",
                                            ]
                                        )

            payload = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
            prompt_text = (root / "tmp/atlas/prompt.md").read_text(encoding="utf-8")

        self.assertEqual(0, exit_code)
        self.assertEqual(scheduler.SCHEMA_VERSION, payload["schema_version"])
        self.assertIn("Execution wave:", prompt_text)
        self.assertIn("Continuation rule:", prompt_text)

    def test_main_atomically_persists_dispatch_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ready = _envelope(
                {
                    "canonical_lifecycle_state": "READY",
                    "packet_id": "fitness-ready",
                    "objective": "Fitness bounded source correction",
                    "logical_role_id": "owner.fitness",
                    "repository": "fawxzzy/fitness",
                    "writer_scope": "repo.fitness",
                    "execution_class": "repo_worktree",
                },
                idempotency_key="fitness-ready-event",
            )
            _write(root / "tmp/atlas/program.json", json.dumps(_program_payload(), indent=2) + "\n")
            _write(root / "tmp/atlas/bindings.json", json.dumps(_bindings(("owner.fitness", "fitness-thread", "idle")), indent=2) + "\n")
            _write(root / "tmp/atlas/envelopes.jsonl", json.dumps(ready) + "\n")
            common_args = [
                "--json",
                "--program",
                "tmp/atlas/program.json",
                "--bindings",
                "tmp/atlas/bindings.json",
                "--envelopes",
                "tmp/atlas/envelopes.jsonl",
                "--output",
                "tmp/atlas/report.json",
                "--prompt-output",
                "tmp/atlas/prompt.md",
            ]
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(scheduler.ai_work_session_preflight, "build_report", return_value=_preflight_payload()):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    with redirect_stdout(io.StringIO()):
                                        first_exit = scheduler.main(common_args)
                                    first_report = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
                                    persisted = json.loads((root / "tmp/atlas/program.json").read_text(encoding="utf-8"))
                                    with redirect_stdout(io.StringIO()):
                                        second_exit = scheduler.main(common_args)
                                    second_report = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))

        self.assertEqual(0, first_exit)
        self.assertTrue(first_report["program_persisted_before_dispatch"])
        self.assertEqual("fitness-thread", first_report["dispatch_plan"][0]["runtime_thread_id"])
        self.assertEqual("ACTIVE", persisted["standing_packets"][0]["state"])
        self.assertEqual("active", persisted["active_leases"][0]["status"])
        self.assertEqual("prepared", persisted["delivery_intents"][0]["status"])
        self.assertEqual(1, persisted["revision"])
        self.assertRegex(persisted["source_snapshot_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(0, second_exit)
        self.assertEqual(scheduler.STATUS_HOLD, second_report["status"])
        self.assertEqual([], second_report["dispatch_plan"])
        self.assertEqual(1, second_report["program_revision"])

    def test_main_rebuilds_missing_program_and_selects_disjoint_owner_wave(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fitness = _envelope(
                {
                    "canonical_lifecycle_state": "READY",
                    "packet_id": "fitness-local-preparation",
                    "objective": "Prepare bounded Fitness source locally.",
                    "logical_role_id": "owner.fitness",
                    "repository": "fawxzzy/fitness",
                    "writer_scope": "repo.fitness.local-preparation",
                    "execution_class": "repo_worktree",
                    "resource_claims": {"files": ["src/fitness.py"], "worktrees": ["fitness-wt"]},
                },
                idempotency_key="fitness-local-preparation",
            )
            mazer = _envelope(
                {
                    "canonical_lifecycle_state": "READY",
                    "packet_id": "mazer-local-preparation",
                    "objective": "Prepare bounded Mazer source locally.",
                    "logical_role_id": "owner.mazer",
                    "repository": "fawxzzy/mazer",
                    "writer_scope": "repo.mazer.local-preparation",
                    "execution_class": "repo_worktree",
                    "resource_claims": {"files": ["src/mazer.py"], "worktrees": ["mazer-wt"]},
                },
                idempotency_key="mazer-local-preparation",
            )
            _write(
                root / "tmp/atlas/bindings.json",
                json.dumps(
                    _bindings(
                        ("owner.fitness", "fitness-thread", "idle"),
                        ("owner.mazer", "mazer-thread", "notLoaded"),
                    ),
                    indent=2,
                )
                + "\n",
            )
            _write(root / "tmp/atlas/envelopes.jsonl", json.dumps(fitness) + "\n" + json.dumps(mazer) + "\n")
            args = [
                "--json",
                "--program",
                "tmp/atlas/program.json",
                "--bindings",
                "tmp/atlas/bindings.json",
                "--envelopes",
                "tmp/atlas/envelopes.jsonl",
                "--output",
                "tmp/atlas/report.json",
                "--prompt-output",
                "tmp/atlas/prompt.md",
            ]
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(scheduler.ai_work_session_preflight, "build_report", return_value=_preflight_payload()):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    with redirect_stdout(io.StringIO()):
                                        exit_code = scheduler.main(args)

            report = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
            program = json.loads((root / "tmp/atlas/program.json").read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertEqual(
            ["fitness-local-preparation", "mazer-local-preparation"],
            sorted(item["packet_id"] for item in report["dispatch_plan"]),
        )
        self.assertEqual(2, len(program["active_leases"]))
        self.assertEqual(2, len(program["delivery_intents"]))
        self.assertEqual(1, program["revision"])

    def test_main_replays_ready_delivery_and_terminal_when_snapshot_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ready = _envelope(
                {
                    "canonical_lifecycle_state": "READY",
                    "packet_id": "fitness-ready",
                    "objective": "Fitness bounded source correction",
                    "logical_role_id": "owner.fitness",
                    "repository": "fawxzzy/fitness",
                    "writer_scope": "repo.fitness",
                    "execution_class": "repo_worktree",
                },
                idempotency_key="fitness-ready-event",
            )
            reservation_seed = "|".join(
                [
                    "fitness-ready",
                    "repo.fitness",
                    "fitness-thread",
                    str(ready["event_id"]),
                ]
            )
            reservation_id = "rsrv_" + hashlib.sha256(reservation_seed.encode("utf-8")).hexdigest()
            terminal = _envelope(
                {
                    "canonical_lifecycle_state": "COMPLETED",
                    "terminal": True,
                    "packet_id": "fitness-ready",
                    "writer_scope": "repo.fitness",
                    "reservation_id": reservation_id,
                    "turn_id": "fitness-turn",
                },
                idempotency_key="fitness-terminal-event",
            )
            delivery = {
                "reservation_id": reservation_id,
                "packet_id": "fitness-ready",
                "runtime_thread_id": "fitness-thread",
                "event_id": ready["event_id"],
                "payload_digest": ready["payload_digest"],
                "status": "DELIVERED",
                "turn_id": "fitness-turn",
            }
            _write(root / "tmp/atlas/bindings.json", json.dumps(_bindings(("owner.fitness", "fitness-thread", "idle")), indent=2) + "\n")
            _write(root / "tmp/atlas/envelopes.jsonl", json.dumps(ready) + "\n" + json.dumps(terminal) + "\n")
            _write(root / "tmp/atlas/delivery.jsonl", json.dumps(delivery) + "\n")
            args = [
                "--json",
                "--program",
                "tmp/atlas/program.json",
                "--bindings",
                "tmp/atlas/bindings.json",
                "--envelopes",
                "tmp/atlas/envelopes.jsonl",
                "--delivery-results",
                "tmp/atlas/delivery.jsonl",
                "--output",
                "tmp/atlas/report.json",
                "--prompt-output",
                "tmp/atlas/prompt.md",
            ]
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(scheduler.ai_work_session_preflight, "build_report", return_value=_preflight_payload()):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    with redirect_stdout(io.StringIO()):
                                        exit_code = scheduler.main(args)

            program = json.loads((root / "tmp/atlas/program.json").read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertEqual(["fitness-ready"], program["completed_packets"])
        self.assertEqual([], program["standing_packets"])
        self.assertEqual([], program["active_leases"])
        self.assertEqual([], program["delivery_intents"])
        self.assertEqual(reservation_id, program["released_leases"][0]["reservation_id"])

    def test_main_settles_delivery_before_simultaneous_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ready = _envelope(
                {
                    "canonical_lifecycle_state": "READY",
                    "packet_id": "fitness-ready",
                    "objective": "Fitness bounded source correction",
                    "logical_role_id": "owner.fitness",
                    "repository": "fawxzzy/fitness",
                    "writer_scope": "repo.fitness",
                    "execution_class": "repo_worktree",
                },
                idempotency_key="fitness-ready-event",
            )
            reservation_id = "rsrv_" + hashlib.sha256(
                "|".join(["fitness-ready", "repo.fitness", "fitness-thread", ready["event_id"]]).encode("utf-8")
            ).hexdigest()
            cancelled = _envelope(
                {
                    "canonical_lifecycle_state": "SUPERSEDED",
                    "terminal": True,
                    "packet_id": "fitness-ready",
                    "writer_scope": "repo.fitness",
                    "reservation_id": reservation_id,
                    "superseded_by_packet_id": "fitness-next",
                },
                idempotency_key="fitness-cancel-event",
                source_role_id="atlas.main",
            )
            delivery = {
                "reservation_id": reservation_id,
                "packet_id": "fitness-ready",
                "runtime_thread_id": "fitness-thread",
                "event_id": ready["event_id"],
                "payload_digest": ready["payload_digest"],
                "status": "DELIVERED",
                "turn_id": "fitness-turn",
            }
            _write(root / "tmp/atlas/bindings.json", json.dumps(_bindings(("owner.fitness", "fitness-thread", "idle"))))
            _write(root / "tmp/atlas/envelopes.jsonl", json.dumps(ready) + "\n" + json.dumps(cancelled) + "\n")
            _write(root / "tmp/atlas/delivery.jsonl", json.dumps(delivery) + "\n")
            args = [
                "--json", "--program", "tmp/atlas/program.json", "--bindings", "tmp/atlas/bindings.json",
                "--envelopes", "tmp/atlas/envelopes.jsonl", "--delivery-results", "tmp/atlas/delivery.jsonl",
                "--output", "tmp/atlas/report.json", "--prompt-output", "tmp/atlas/prompt.md",
            ]
            with patch.object(scheduler, "atlas_root", return_value=root):
                with patch.object(scheduler, "_branch_state", return_value=("main", "abc123")):
                    with patch.object(scheduler, "_parity_state", return_value={"status": "clean", "behind": 0, "ahead": 0}):
                        with patch.object(scheduler, "_load_selector", return_value=_selector_payload()):
                            with patch.object(scheduler.ai_work_session_preflight, "build_report", return_value=_preflight_payload()):
                                with patch.object(scheduler.planner, "build_report", return_value=_planner_payload([])):
                                    with redirect_stdout(io.StringIO()):
                                        scheduler.main(args)

            program = json.loads((root / "tmp/atlas/program.json").read_text(encoding="utf-8"))

        self.assertEqual("delivered", program["delivery_intents"][0]["status"])
        self.assertEqual("active", program["active_leases"][0]["status"])
        self.assertEqual([], program["completed_packets"])
        self.assertIn("terminal_cancellation_correlation_required", [item["code"] for item in program["bridge_findings"]])
