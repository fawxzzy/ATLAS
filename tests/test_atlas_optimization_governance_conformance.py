from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ops.atlas.validate_optimization_governance_conformance import validate_conformance


class OptimizationGovernanceConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.automations = self.root / "automations"
        self.now = datetime(2026, 8, 27, 22, 0, tzinfo=timezone.utc)
        self.baseline_ref = "docs/prompts/atlas-workflow/STANDING-BASELINE.md"
        (self.root / self.baseline_ref).parent.mkdir(parents=True)
        (self.root / self.baseline_ref).write_text(
            "single non-product-blocking failure observation remains one canonical record\n"
            "ephemeral reviewer and bounded helper identities form an auxiliary denominator\n"
            "ephemeral-only identity change must not trigger a material handoff\n"
            "canonicalize strict same-origin URL paths before exact comparison\n"
            "validate the immutable expected workspace before Vercel\n"
            "a diagnostic must never implicitly link or create a provider project\n",
            encoding="utf-8",
        )
        self.optimization_governance_ref = "docs/registry/ATLAS-WORKFLOW-OPTIMIZATION-GOVERNANCE.v1.json"
        self.common_control_refs = [
            "docs/memory/decisions/decision-atlas-common-release-safety-controls-r001.json",
            "ops/atlas/release_safety_controls.py",
            "tests/test_atlas_release_safety_controls.py",
        ]
        self.optimization_governance = {
            "anti_churn": {
                "single_observation_failure_gate": {
                    "canonical_observation_only": True,
                    "default_state": "recorded-no-fanout-no-promotion-no-implementation",
                    "escalation_any_of": ["matching recurrence", "product blocking", "bounded cause"],
                },
                "census_identity_classes": {
                    "material_denominator": "standing and user-visible task identities",
                    "auxiliary_denominator": "ephemeral reviewer and bounded helper identities",
                    "ephemeral_only_material_delta_handoff": False,
                },
                "avoided_amplification_measurement": {
                    "observed_lower_bound": {
                        "material_downstream_wakes_or_handoffs": 2,
                        "downstream_receipts_or_adoptions": 3,
                    }
                },
            },
            "common_release_safety_controls": {
                "decision_id": "ACCEPT_BOUNDED_COMMON_CONTROL_R001",
                "status": "INSTALLED",
                "local_installation_state": "installed-and-verified-in-canonical-dirty-root",
                "publication_state": "current-main-candidate-unmerged",
                "engineering_memory_ref": self.common_control_refs[0],
                "engineering_memory_seed_ids": ["seed.pc024.rule", "seed.fa027.failure", "seed.pc025.rule", "seed.fa028.failure"],
                "implementation_ref": self.common_control_refs[1],
                "focused_test_ref": self.common_control_refs[2],
                "pc024": {"status": "INSTALLED"},
                "pc025": {"status": "INSTALLED", "provider_effects": 0},
            },
        }
        optimization_governance_path = self.root / self.optimization_governance_ref
        optimization_governance_path.parent.mkdir(parents=True, exist_ok=True)
        optimization_governance_path.write_text(json.dumps(self.optimization_governance), encoding="utf-8")
        for ref in self.common_control_refs:
            path = self.root / ref
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")

        self.memory_refs = [
            "docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json",
            "ops/atlas/engineering_memory_gate.mjs",
        ]
        self.seam_refs = [
            "packages/atlas-contracts/schemas/atlas.job-envelope.v2.schema.json",
            "packages/atlas-contracts/schemas/atlas.execution-receipt.v2.schema.json",
        ]
        for ref in [*self.memory_refs, *self.seam_refs]:
            path = self.root / ref
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
        (self.root / self.memory_refs[0]).write_text(
            json.dumps(
                {
                    "knowledge_seeds": [
                        {"id": seed_id, "status": "accepted-atlas-root", "playbook_promotion": "installed-common-control"}
                        for seed_id in self.optimization_governance["common_release_safety_controls"]["engineering_memory_seed_ids"]
                    ]
                }
            ),
            encoding="utf-8",
        )

        self.manifest_path = self.root / "manifest.json"
        self.manifest = {
            "roles": [
                {"role_id": "role.one", "prompt_template": {"fragments": [self.baseline_ref]}},
                {"role_id": "role.two", "prompt_template": {"fragments": [self.baseline_ref]}},
            ]
        }
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

        self.receipt_ref = "runtime/successor/execution-receipt.json"
        receipt_path = self.root / self.receipt_ref
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(json.dumps({"contract_version": "atlas.execution-receipt.v2"}), encoding="utf-8")
        receipt_path.with_name("job-envelope.json").write_text(
            json.dumps({"contract_version": "atlas.job-envelope.v2"}), encoding="utf-8"
        )
        checkpoint_path = self.root / "runtime/atlas/thread-context/thread-integrator/latest.json"
        checkpoint_path.parent.mkdir(parents=True)
        checkpoint_path.write_text(
            json.dumps(
                {
                    "payload": {
                        "recorded_at": "2026-08-27T21:30:00Z",
                        "receipts": [self.receipt_ref],
                    }
                }
            ),
            encoding="utf-8",
        )

        entries = [
            ("integrator", "Integrator", "thread-integrator", 60, "scope.integrator"),
            ("census", "Census", "thread-census", 120, "scope.census"),
            ("failure", "Failure", "thread-failure", 90, "scope.failure"),
            ("master", "Master", "thread-master", 120, "scope.master"),
        ]
        for automation_id, name, thread_id, cadence, _scope in entries:
            path = self.automations / automation_id / "automation.toml"
            path.parent.mkdir(parents=True)
            if cadence % 60 == 0:
                rrule = f"FREQ=HOURLY;INTERVAL={cadence // 60}"
            else:
                rrule = f"FREQ=MINUTELY;INTERVAL={cadence}"
            path.write_text(
                "\n".join(
                    [
                        f'id = "{automation_id}"',
                        'kind = "heartbeat"',
                        f'name = "{name}"',
                        'prompt = "Do not create any additional task."',
                        'status = "ACTIVE"',
                        f'rrule = "{rrule}"',
                        f'target_thread_id = "{thread_id}"',
                    ]
                ),
                encoding="utf-8",
            )

        self.status_thread_id = "thread-status"
        self.status_automation_id = "status-refresh"
        status_automation_path = self.automations / self.status_automation_id / "automation.toml"
        status_automation_path.parent.mkdir(parents=True)
        status_automation_path.write_text(
            "\n".join(
                [
                    f'id = "{self.status_automation_id}"',
                    'kind = "heartbeat"',
                    'name = "Status Refresh"',
                    'prompt = "Maintain the single read-only human ATLAS dashboard. Use direct material handoffs as the primary trigger. First perform a cheap identity gate; if none changed, stop without task-listing calls, full checkpoint reads, projection rewrites, or a new checkpoint. Do not dispatch work."',
                    'status = "ACTIVE"',
                    'rrule = "FREQ=MINUTELY;INTERVAL=30"',
                    f'target_thread_id = "{self.status_thread_id}"',
                ]
            ),
            encoding="utf-8",
        )
        self.questions_automation_id = "questions"
        questions_path = self.automations / self.questions_automation_id / "automation.toml"
        questions_path.parent.mkdir(parents=True)
        questions_path.write_text(
            "\n".join(
                [
                    f'id = "{self.questions_automation_id}"',
                    'kind = "heartbeat"',
                    'name = "Questions"',
                    'prompt = "Questions is not a scheduler, product owner, status renderer, verifier, or duplicate. First perform a cheap delta gate only and do not call task-listing tools on no delta. Route one compact delta-only message to 00 ATLAS Status when its projection is stale."',
                    'status = "ACTIVE"',
                    'rrule = "FREQ=HOURLY;INTERVAL=1"',
                    'target_thread_id = "thread-questions"',
                ]
            ),
            encoding="utf-8",
        )

        status_root = self.root / "runtime/atlas/status"
        status_root.mkdir(parents=True)
        self.status_json_ref = "runtime/atlas/status/active-task-status.json"
        self.status_markdown_ref = "runtime/atlas/status/active-task-status.md"
        (self.root / self.status_json_ref).write_text("{}\n", encoding="utf-8")
        (self.root / self.status_markdown_ref).write_text("status\n", encoding="utf-8")
        self.status_json_sha = "sha256:" + hashlib.sha256((self.root / self.status_json_ref).read_bytes()).hexdigest()
        self.status_markdown_sha = "sha256:" + hashlib.sha256((self.root / self.status_markdown_ref).read_bytes()).hexdigest()
        self.status_checkpoint_ref = f"runtime/atlas/thread-context/{self.status_thread_id}/latest.json"
        status_checkpoint_path = self.root / self.status_checkpoint_ref
        status_checkpoint_path.parent.mkdir(parents=True)
        status_checkpoint_path.write_text(
            json.dumps(
                {
                    "payload": {
                        "thread_id": self.status_thread_id,
                        "logical_role_id": "atlas.status-projection",
                        "receipts": [
                            f"{self.status_json_ref}#sha256={self.status_json_sha.removeprefix('sha256:')}",
                            f"{self.status_markdown_ref}#sha256={self.status_markdown_sha.removeprefix('sha256:')}",
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )

        def topology_entry(values: tuple[str, str, str, int, str]) -> dict:
            automation_id, name, thread_id, cadence, scope = values
            return {
                "title": name,
                "automation_name": name,
                "thread_id": thread_id,
                "automation_id": automation_id,
                "cadence_minutes": cadence,
                "schedule_status": "ACTIVE",
                "writer_scope": scope,
            }

        self.ledger_path = self.root / "ledger.json"
        self.ledger = {
            "worker_topology": {
                "program_task_lock": {
                    "task_count": 4,
                    "additional_program_tasks_permitted": False,
                },
                "integrator": topology_entry(entries[0]),
                "bounded_workers": [topology_entry(entry) for entry in entries[1:]],
            },
            "operator_visibility_topology": {
                "task_count": 1,
                "excluded_from_learning_program": True,
                "thread_id": self.status_thread_id,
                "automation": {
                    "automation_id": self.status_automation_id,
                    "automation_name": "Status Refresh",
                    "schedule_status": "ACTIVE",
                    "cadence_minutes": 30,
                    "toml_sha256": "sha256:" + hashlib.sha256(status_automation_path.read_bytes()).hexdigest(),
                    "identity_first_delta_gate": True,
                },
                "scope": {
                    "read_only_projection": True,
                    "dispatch_allowed": False,
                    "approval_evaluation_allowed": False,
                    "state_mutation_allowed": False,
                },
                "projection": {
                    "json_ref": self.status_json_ref,
                    "json_sha256": self.status_json_sha,
                    "markdown_ref": self.status_markdown_ref,
                    "markdown_sha256": self.status_markdown_sha,
                },
                "checkpoint": {"ref": self.status_checkpoint_ref},
                "questions_consumer": {
                    "automation_id": self.questions_automation_id,
                    "thread_id": "thread-questions",
                    "schedule_status": "ACTIVE",
                    "cadence_minutes": 60,
                    "toml_sha256": "sha256:" + hashlib.sha256(questions_path.read_bytes()).hexdigest(),
                    "identity_first_delta_gate": True,
                    "routes_compact_material_delta_to_status": True,
                },
            },
            "automation": {"latest_active_successor_ref": self.receipt_ref},
            "active_task_governance_conformance": {
                "manifest_role_denominator": 2,
                "engineering_memory_gate_refs": self.memory_refs,
                "job_receipt_seam_refs": self.seam_refs,
                "authority_state": {
                    "product_provider_effects_allowed": False,
                    "decision_memory_repair_owned_elsewhere": True,
                },
                "unknowns": [
                    {
                        "status": "UNKNOWN",
                        "wake_condition": "EXACT_EXTERNAL_READBACK",
                    }
                ],
            },
            "source_coverage": {
                "cross_source_tasks_discovered": 10,
                "metadata_indexed": 9,
                "inaccessible": 1,
                "content_reviewed_tasks": 2,
                "remaining_content_review_tasks": 7,
                "local_claude_files_pending_metadata_normalization": 3,
                "vendor_import_files_pending_format_classification": 4,
                "coverage_claim": "partial-denominator-backed",
            },
        }
        self._write_ledger()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_ledger(self) -> None:
        self.ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")

    def validate(self) -> dict:
        return validate_conformance(
            self.root,
            self.automations,
            self.ledger_path,
            self.manifest_path,
            self.now,
            24,
        )

    def test_accepts_exact_four_task_topology_and_baseline(self) -> None:
        result = self.validate()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(4, result["automation_topology"]["active"])
        self.assertEqual(1, result["operator_visibility"]["task_count"])
        self.assertTrue(result["operator_visibility"]["excluded_from_learning_program"])
        self.assertEqual(2, result["bootstrap_baseline"]["roles_with_baseline"])
        self.assertEqual(3, result["anti_churn"]["baseline_markers_present"])
        self.assertEqual("INSTALLED", result["common_release_safety_controls"]["status"])
        self.assertEqual(
            "current-main-candidate-unmerged",
            result["common_release_safety_controls"]["publication_state"],
        )
        self.assertEqual(3, result["common_release_safety_controls"]["present_artifact_count"])
        self.assertEqual(4, result["common_release_safety_controls"]["engineering_memory_seed_count"])

    def test_fails_when_single_observation_fanout_gate_is_removed(self) -> None:
        self.optimization_governance["anti_churn"]["single_observation_failure_gate"][
            "canonical_observation_only"
        ] = False
        (self.root / self.optimization_governance_ref).write_text(
            json.dumps(self.optimization_governance), encoding="utf-8"
        )
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("SINGLE_OBSERVATION_FANOUT_GATE_DRIFT", {error["code"] for error in result["errors"]})

    def test_fails_when_ephemeral_identity_can_trigger_material_handoff(self) -> None:
        self.optimization_governance["anti_churn"]["census_identity_classes"][
            "ephemeral_only_material_delta_handoff"
        ] = True
        (self.root / self.optimization_governance_ref).write_text(
            json.dumps(self.optimization_governance), encoding="utf-8"
        )
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("EPHEMERAL_IDENTITY_HANDOFF_GATE_DRIFT", {error["code"] for error in result["errors"]})

    def test_fails_when_anti_churn_baseline_is_removed(self) -> None:
        (self.root / self.baseline_ref).write_text("baseline\n", encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("ANTI_CHURN_BASELINE_MISSING", {error["code"] for error in result["errors"]})

    def test_fails_when_common_release_control_is_not_installed(self) -> None:
        self.optimization_governance["common_release_safety_controls"]["pc025"]["status"] = "PROPOSED"
        (self.root / self.optimization_governance_ref).write_text(
            json.dumps(self.optimization_governance), encoding="utf-8"
        )
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("PC025_COMMON_CONTROL_NOT_INSTALLED", {error["code"] for error in result["errors"]})

    def test_fails_when_common_release_publication_state_overclaims_current_main(self) -> None:
        self.optimization_governance["common_release_safety_controls"]["publication_state"] = "installed-current-main"
        (self.root / self.optimization_governance_ref).write_text(
            json.dumps(self.optimization_governance), encoding="utf-8"
        )
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn(
            "COMMON_RELEASE_CONTROL_PUBLICATION_STATE_DRIFT",
            {error["code"] for error in result["errors"]},
        )

    def test_fails_when_common_release_control_artifact_is_missing(self) -> None:
        (self.root / self.common_control_refs[1]).unlink()
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("COMMON_RELEASE_CONTROL_ARTIFACT_MISSING", {error["code"] for error in result["errors"]})

    def test_fails_when_any_manifest_role_loses_baseline(self) -> None:
        self.manifest["roles"][1]["prompt_template"]["fragments"] = []
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("ROLE_BASELINE_MISSING", {error["code"] for error in result["errors"]})

    def test_fails_when_live_topology_drifts_from_ledger(self) -> None:
        path = self.automations / "failure" / "automation.toml"
        text = path.read_text(encoding="utf-8").replace('status = "ACTIVE"', 'status = "PAUSED"')
        path.write_text(text, encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("AUTOMATION_STATUS_DRIFT", {error["code"] for error in result["errors"]})

    def test_fails_when_checkpoint_does_not_reference_latest_receipt(self) -> None:
        checkpoint_path = self.root / "runtime/atlas/thread-context/thread-integrator/latest.json"
        checkpoint_path.write_text(
            json.dumps({"payload": {"recorded_at": "2026-08-27T21:30:00Z", "receipts": []}}),
            encoding="utf-8",
        )
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("CHECKPOINT_RECEIPT_STALE", {error["code"] for error in result["errors"]})

    def test_accepts_content_addressed_latest_receipt_anchor(self) -> None:
        receipt_path = self.root / self.receipt_ref
        receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        checkpoint_path = self.root / "runtime/atlas/thread-context/thread-integrator/latest.json"
        checkpoint_path.write_text(
            json.dumps(
                {
                    "payload": {
                        "recorded_at": "2026-08-27T21:30:00Z",
                        "receipts": [f"{self.receipt_ref}#sha256={receipt_sha}"],
                    }
                }
            ),
            encoding="utf-8",
        )
        result = self.validate()
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["checkpoint"]["contains_latest_receipt"])

    def test_fails_when_status_automation_is_missing(self) -> None:
        (self.automations / self.status_automation_id / "automation.toml").unlink()
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("STATUS_AUTOMATION_MISSING", {error["code"] for error in result["errors"]})

    def test_fails_when_status_automation_target_drifts(self) -> None:
        path = self.automations / self.status_automation_id / "automation.toml"
        text = path.read_text(encoding="utf-8").replace(
            f'target_thread_id = "{self.status_thread_id}"', 'target_thread_id = "other-thread"'
        )
        path.write_text(text, encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("STATUS_AUTOMATION_TARGET_DRIFT", {error["code"] for error in result["errors"]})

    def test_fails_when_status_identity_gate_is_removed(self) -> None:
        path = self.automations / self.status_automation_id / "automation.toml"
        text = path.read_text(encoding="utf-8").replace("cheap identity gate", "bounded comparison")
        path.write_text(text, encoding="utf-8")
        self.ledger["operator_visibility_topology"]["automation"]["toml_sha256"] = (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
        self._write_ledger()
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("STATUS_IDENTITY_GATE_MISSING", {error["code"] for error in result["errors"]})

    def test_fails_when_questions_cadence_drifts(self) -> None:
        path = self.automations / self.questions_automation_id / "automation.toml"
        text = path.read_text(encoding="utf-8").replace(
            'rrule = "FREQ=HOURLY;INTERVAL=1"', 'rrule = "FREQ=MINUTELY;INTERVAL=15"'
        )
        path.write_text(text, encoding="utf-8")
        self.ledger["operator_visibility_topology"]["questions_consumer"]["toml_sha256"] = (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
        self._write_ledger()
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("QUESTIONS_AUTOMATION_CADENCE_DRIFT", {error["code"] for error in result["errors"]})

    def test_fails_when_status_projection_hash_drifts(self) -> None:
        (self.root / self.status_markdown_ref).write_text("changed\n", encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("STATUS_PROJECTION_HASH_DRIFT", {error["code"] for error in result["errors"]})

    def test_fails_when_status_checkpoint_receipt_hash_drifts(self) -> None:
        checkpoint_path = self.root / self.status_checkpoint_ref
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        checkpoint["payload"]["receipts"][1] = f"{self.status_markdown_ref}#sha256=wrong"
        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertIn("STATUS_CHECKPOINT_RECEIPT_HASH_DRIFT", {error["code"] for error in result["errors"]})


if __name__ == "__main__":
    unittest.main()
