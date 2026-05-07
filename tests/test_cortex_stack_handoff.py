from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.stack_handoff import (
    build_stack_advisory_handoff_payload,
    default_stack_advisory_handoff_latest_json_path,
    default_stack_advisory_handoff_latest_markdown_path,
    main,
    persist_stack_advisory_handoff_artifact,
)
from ops.cortex.worker_prompt import persist_cortex_worker_prompt_artifact


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexStackAdvisoryHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.current_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "current-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.rail_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "rail-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.context_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "context" / "latest.json").read_text(encoding="utf-8")
        )
        cls.operator_surface_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "operator-surface" / "latest.json").read_text(encoding="utf-8")
        )
        cls.ledger_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "ledger" / "latest.json").read_text(encoding="utf-8")
        )
        cls.validation_payload = json.loads(
            (cls.root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json").read_text(encoding="utf-8")
        )
        cls.state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.rule_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.proof_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json").read_text(encoding="utf-8")
        )
        cls.stack_lock_text = (cls.root / "stack.lock.yaml").read_text(encoding="utf-8")

    def _base_validation_payload(self) -> dict:
        return {
            "generated_at": "2026-05-07T17:00:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "stack_lock_file": "stack.lock.yaml",
            "summary": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
            "repo_ids": ["stack", "fitness", "lifeline"],
            "findings": [],
        }

    def _base_current_state_payload(self) -> dict:
        payload = deepcopy(self.current_state_payload)
        payload["generated_at"] = "2026-05-07T17:01:00+00:00"
        payload["worktree_status"] = "clean"
        payload["active_blockers"] = []
        payload["validation_receipt"] = {
            "generated_at": "2026-05-07T17:00:00+00:00",
            "path": "runtime/receipts/validation/stack-validation.latest.json",
            "counts": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
        }
        payload["validation_counts"] = dict(payload["validation_receipt"]["counts"])
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-stack-consumer-default-routing-wave8",
            "owner_layer": "cortex",
            "rationale": "Cortex should promote one canonical advisory handoff envelope for _stack consumption.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_rail_state_payload(self) -> dict:
        payload = deepcopy(self.rail_state_payload)
        payload["generated_at"] = "2026-05-07T17:02:00+00:00"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-stack-consumer-default-routing-v0-1"]
        payload["validation_posture"] = {
            "status": "ambient-debt-only",
            "counts": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
            "receipt_generated_at": "2026-05-07T17:00:00+00:00",
            "receipt_path": "runtime/receipts/validation/stack-validation.latest.json",
        }
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-stack-consumer-default-routing-wave8",
            "owner_layer": "cortex",
            "rationale": "Cortex should promote one canonical advisory handoff envelope for _stack consumption.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_context_payload(self) -> dict:
        payload = deepcopy(self.context_payload)
        payload["generated_at"] = "2026-05-07T17:03:00+00:00"
        payload["packet_id"] = "context-promote-cortex-stack-consumer-default-routing-wave8"
        payload["task_frame"]["lane_id"] = "promote-cortex-stack-consumer-default-routing-wave8"
        payload["task_frame"]["owner_layer"] = "cortex"
        payload["task_frame"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame"]["status"] = "ready"
        payload["task_frame"]["blocked_by"] = []
        return payload

    def _base_operator_surface_payload(self) -> dict:
        payload = deepcopy(self.operator_surface_payload)
        payload["generated_at"] = "2026-05-07T17:04:00+00:00"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-stack-consumer-default-routing-v0-1"]
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-stack-consumer-default-routing-wave8",
            "owner_layer": "cortex",
            "rationale": "Cortex should promote one canonical advisory handoff envelope for _stack consumption.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["context_packet_id"] = "context-promote-cortex-stack-consumer-default-routing-wave8"
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-stack-consumer-default-routing-wave8"
        payload["task_frame_summary"]["owner_layer"] = "cortex"
        payload["task_frame_summary"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["blocked_by"] = []
        return payload

    def _base_ledger_payload(self) -> dict:
        payload = deepcopy(self.ledger_payload)
        payload["generated_at"] = "2026-05-07T17:05:00+00:00"
        payload["ledger_id"] = "ledger-promote-cortex-stack-consumer-default-routing-wave8"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-stack-consumer-default-routing-v0-1"]
        payload["worktree_status"] = "clean"
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-stack-consumer-default-routing-wave8",
            "owner_layer": "cortex",
            "rationale": "Cortex should promote one canonical advisory handoff envelope for _stack consumption.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/rail-state/latest.json",
                "runtime/cortex/context/latest.json",
                "runtime/cortex/operator-surface/latest.json",
                "runtime/receipts/validation/stack-validation.latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["context_packet_id"] = "context-promote-cortex-stack-consumer-default-routing-wave8"
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-stack-consumer-default-routing-wave8"
        payload["task_frame_summary"]["owner_layer"] = "cortex"
        payload["task_frame_summary"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["blocked_by"] = []
        return payload

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "current-state" / "latest.json", self._base_current_state_payload())
        _write_json(root / "runtime" / "cortex" / "rail-state" / "latest.json", self._base_rail_state_payload())
        _write_json(root / "runtime" / "cortex" / "context" / "latest.json", self._base_context_payload())
        _write_json(root / "runtime" / "cortex" / "operator-surface" / "latest.json", self._base_operator_surface_payload())
        _write_json(root / "runtime" / "cortex" / "ledger" / "latest.json", self._base_ledger_payload())
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self._base_validation_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json", self.proof_payload)
        (root / "stack.lock.yaml").write_text(self.stack_lock_text, encoding="utf-8")
        persist_cortex_worker_prompt_artifact(root=root)
        return root

    def test_clean_ready_posture_emits_canonical_handoff(self) -> None:
        root = self._temp_root()

        payload = build_stack_advisory_handoff_payload(root=root)

        self.assertEqual("atlas.cortex.stack-advisory-handoff.v2", payload["contract_version"])
        self.assertEqual("read_only_advisory", payload["authority_level"])
        self.assertEqual("_stack", payload["consumer"]["consumer_id"])
        self.assertEqual("artifact_refs_only", payload["consumer"]["consumption_mode"])
        self.assertTrue(payload["routing_contract"]["routing_contract_promoted"])
        self.assertEqual("explicit_artifact_ref_handoff", payload["routing_contract"]["routing_mode"])
        self.assertFalse(payload["routing_contract"]["automatic_dispatch_enabled"])
        self.assertFalse(payload["routing_contract"]["execution_authorized"])
        self.assertFalse(payload["routing_contract"]["receipt_authorized"])
        self.assertFalse(payload["routing_contract"]["owner_truth_mutation_authorized"])
        self.assertFalse(payload["routing_contract"]["transcript_scraping_allowed"])
        self.assertEqual(
            "promote-cortex-stack-consumer-default-routing-wave8",
            payload["next_recommended_lane"]["lane_id"],
        )
        self.assertEqual("ready", payload["handoff_result"]["status"])
        self.assertTrue(payload["handoff_result"]["ready_for_stack_consumer"])
        self.assertTrue(all(check["status"] == "passed" for check in payload["handoff_checks"]))
        self.assertEqual(
            "runtime/cortex/stack-consumption-pilot/latest.json",
            payload["canonical_refs"]["stack_consumption_pilot"],
        )
        json.dumps(payload, sort_keys=True)

    def test_markdown_summary_includes_boundary_language(self) -> None:
        root = self._temp_root()

        artifact = persist_stack_advisory_handoff_artifact(root=root)
        payload = json.loads(default_stack_advisory_handoff_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_stack_advisory_handoff_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Stack Advisory Handoff", summary)
        self.assertIn("promote-cortex-stack-consumer-default-routing-wave8", summary)
        self.assertIn("_stack", summary)
        self.assertIn("artifact_refs_only", summary)
        self.assertIn("automatic dispatch", summary.lower())
        self.assertIn("execution authorized", summary.lower())
        self.assertIn("receipt authorized", summary.lower())
        self.assertIn("Authority Guards", summary)

    def test_missing_worker_prompt_fails_clearly(self) -> None:
        root = self._temp_root()
        (root / "runtime" / "cortex" / "worker-prompts" / "latest.json").unlink()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex worker-prompt artifact not found", stderr.getvalue())

    def test_transcript_refs_block_readiness(self) -> None:
        root = self._temp_root()
        worker_prompt_path = root / "runtime" / "cortex" / "worker-prompts" / "latest.json"
        payload = json.loads(worker_prompt_path.read_text(encoding="utf-8"))
        payload["source_refs"] = list(payload.get("source_refs", [])) + [
            "runtime/atlas/conversations/example-transcript.json"
        ]
        worker_prompt_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        handoff_payload = build_stack_advisory_handoff_payload(root=root)

        self.assertEqual("blocked", handoff_payload["handoff_result"]["status"])
        self.assertFalse(handoff_payload["handoff_result"]["ready_for_stack_consumer"])
        self.assertTrue(handoff_payload["transcript_scraping"]["detected"])
        self.assertIn("transcript-scraping-absent", handoff_payload["handoff_result"]["failed_checks"])


if __name__ == "__main__":
    unittest.main()
