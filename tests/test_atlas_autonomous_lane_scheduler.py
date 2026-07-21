from __future__ import annotations

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


def _envelope(payload: dict[str, object], *, idempotency_key: str) -> dict[str, object]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {
        "schema": "atlas.workflow.envelope.v1",
        "kind": "EVENT",
        "event_id": "onv1_" + digest,
        "payload_digest": "sha256:" + digest,
        "idempotency_key": idempotency_key,
        "payload": payload,
    }


def _bindings(*items: tuple[str, str, str]) -> dict[str, object]:
    return {
        "bindings": [
            {
                "role_id": role_id,
                "current_runtime_id": runtime_id,
                "runtime_status": status,
                "archived": False,
            }
            for role_id, runtime_id, status in items
        ]
    }


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
    def test_work_program_schema_freezes_delivery_and_lease_state(self) -> None:
        schema = json.loads((scheduler.ROOT / "schemas/atlas.autonomous-work-program.v2.json").read_text(encoding="utf-8"))

        self.assertEqual("atlas.autonomous-work-program.v2", schema["$id"])
        self.assertEqual(
            {
                "schema_version",
                "revision",
                "source_snapshot_digest",
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
            ["prepared", "delivered", "recovery-required"],
            schema["properties"]["delivery_intents"]["items"]["properties"]["status"]["enum"],
        )
        self.assertIn(
            "external_mutation",
            schema["properties"]["standing_packets"]["items"]["properties"]["execution_class"]["enum"],
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
            ["github:fawxzzy/atlas#146:review"],
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
        self.assertNotIn("forbidden_owner_lanes", program)

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
