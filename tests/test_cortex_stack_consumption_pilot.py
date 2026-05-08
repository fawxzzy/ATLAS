from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.stack_consumption_pilot import (
    build_stack_consumption_pilot_payload,
    default_stack_consumption_pilot_latest_json_path,
    default_stack_consumption_pilot_latest_markdown_path,
    main,
    persist_stack_consumption_pilot_artifact,
)
from ops.cortex.stack_handoff import persist_stack_advisory_handoff_artifact
from ops.cortex.worker_prompt import persist_cortex_worker_prompt_artifact


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexStackConsumptionPilotTests(unittest.TestCase):
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
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
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
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-contract-v0-1"]
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
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
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
        payload["packet_id"] = "context-promote-cortex-receipt-interpretation-contract-wave9"
        payload["task_frame"]["lane_id"] = "promote-cortex-receipt-interpretation-contract-wave9"
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
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-contract-v0-1"]
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
            "owner_layer": "cortex",
            "rationale": "Cortex should promote one canonical advisory handoff envelope for _stack consumption.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["context_packet_id"] = "context-promote-cortex-receipt-interpretation-contract-wave9"
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-receipt-interpretation-contract-wave9"
        payload["task_frame_summary"]["owner_layer"] = "cortex"
        payload["task_frame_summary"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["blocked_by"] = []
        return payload

    def _base_ledger_payload(self) -> dict:
        payload = deepcopy(self.ledger_payload)
        payload["generated_at"] = "2026-05-07T17:05:00+00:00"
        payload["ledger_id"] = "ledger-promote-cortex-receipt-interpretation-contract-wave9"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-contract-v0-1"]
        payload["worktree_status"] = "clean"
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
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
        payload["context_packet_id"] = "context-promote-cortex-receipt-interpretation-contract-wave9"
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-receipt-interpretation-contract-wave9"
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
        persist_stack_advisory_handoff_artifact(root=root)
        return root

    def test_clean_ready_posture_emits_stack_consumption_pilot(self) -> None:
        root = self._temp_root()

        payload = build_stack_consumption_pilot_payload(root=root)

        self.assertEqual("atlas.cortex.stack-consumption-pilot.v1", payload["contract_version"])
        self.assertEqual("read_only_advisory", payload["authority_level"])
        self.assertEqual("_stack", payload["consumer_id"])
        self.assertEqual("artifact_refs_only", payload["stack_handoff"]["consumption_mode"])
        self.assertEqual("ready", payload["pilot_result"]["status"])
        self.assertTrue(payload["pilot_result"]["ready_for_stack_consumer"])
        self.assertEqual(
            "promote-cortex-receipt-interpretation-contract-wave9",
            payload["next_recommended_lane"]["lane_id"],
        )
        self.assertEqual(
            "runtime/cortex/stack-advisory-handoff/latest.json",
            payload["canonical_handoff"]["ref"],
        )
        self.assertEqual("runtime/cortex/worker-prompts/latest.json", payload["stack_handoff"]["worker_prompt_ref"])
        self.assertEqual("runtime/cortex/context/latest.json", payload["stack_handoff"]["context_ref"])
        self.assertEqual(
            "atlas.cortex.stack-advisory-handoff.v2",
            payload["canonical_handoff"]["contract_version"],
        )
        self.assertFalse(payload["stack_handoff"]["execution_authorized"])
        self.assertFalse(payload["stack_handoff"]["receipt_authorized"])
        self.assertFalse(payload["stack_handoff"]["owner_truth_mutation_authorized"])
        self.assertFalse(payload["stack_handoff"]["default_routing_enabled"])
        self.assertFalse(payload["stack_handoff"]["transcript_scraping_allowed"])
        self.assertFalse(payload["transcript_scraping"]["detected"])
        self.assertEqual([], payload["transcript_scraping"]["detected_refs"])
        self.assertIsNone(payload["stack_handoff"]["final_receipt_ref"])
        self.assertIn("runtime/cortex/stack-advisory-handoff/latest.json", payload["source_refs"])
        self.assertIn("runtime/cortex/worker-prompts/latest.json", payload["source_refs"])
        self.assertIn("runtime/cortex/context/latest.json", payload["source_refs"])
        self.assertTrue(all(check["status"] == "passed" for check in payload["pilot_checks"]))
        json.dumps(payload, sort_keys=True)

    def test_markdown_summary_includes_pilot_checks_and_guards(self) -> None:
        root = self._temp_root()

        artifact = persist_stack_consumption_pilot_artifact(root=root)
        payload = json.loads(default_stack_consumption_pilot_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_stack_consumption_pilot_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Stack Consumption Pilot", summary)
        self.assertIn("promote-cortex-receipt-interpretation-contract-wave9", summary)
        self.assertIn("Canonical handoff", summary)
        self.assertIn("Pilot Checks", summary)
        self.assertIn("Transcript scraping", summary)
        self.assertIn("Execution authorized", summary)
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


if __name__ == "__main__":
    unittest.main()
