from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.receipt_interpretation_stack_consumption import (
    build_receipt_interpretation_stack_consumption_payload,
    default_receipt_interpretation_stack_consumption_latest_json_path,
    default_receipt_interpretation_stack_consumption_latest_markdown_path,
    main,
    persist_receipt_interpretation_stack_consumption_artifact,
)
from ops.cortex.receipt_interpreter import persist_receipt_interpretation_artifact
from ops.cortex.stack_consumption_pilot import persist_stack_consumption_pilot_artifact
from ops.cortex.stack_handoff import persist_stack_advisory_handoff_artifact
from ops.cortex.worker_prompt import persist_cortex_worker_prompt_artifact


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexReceiptInterpretationStackConsumptionTests(unittest.TestCase):
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
        cls.schema_payload = json.loads(
            (cls.root / "schemas" / "atlas.cortex.receipt-interpretation-stack-consumption.v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.stack_lock_text = (cls.root / "stack.lock.yaml").read_text(encoding="utf-8")

    def _base_validation_payload(self) -> dict:
        payload = deepcopy(self.validation_payload)
        payload["summary"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["findings"] = []
        return payload

    def _base_current_state_payload(self) -> dict:
        payload = deepcopy(self.current_state_payload)
        payload["branch"] = "codex/cortex-receipt-interpretation-stack-consumption-wave10"
        payload["head"] = "abc123def456"
        payload["worktree_status"] = "clean"
        payload["changed_files"] = []
        payload["untracked_files"] = []
        payload["remote_status"] = {
            "status": "in_sync",
            "upstream": "origin/codex/cortex-receipt-interpretation-stack-consumption-wave10",
            "ahead": 0,
            "behind": 0,
        }
        payload["remote_publication_state"] = {
            "status": "in_sync",
            "branch": "codex/cortex-receipt-interpretation-stack-consumption-wave10",
            "head": "abc123def456",
            "published": True,
            "upstream": "origin/codex/cortex-receipt-interpretation-stack-consumption-wave10",
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/10",
            "notes": [],
        }
        payload["active_blockers"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "docs-adr-or-debt-slice",
            "owner_layer": "atlas",
            "rationale": "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_rail_state_payload(self) -> dict:
        payload = deepcopy(self.rail_state_payload)
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "docs-adr-or-debt-slice",
            "owner_layer": "atlas",
            "rationale": "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation.",
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
        payload["packet_id"] = "context-docs-adr-or-debt-slice"
        payload["context_summary"] = (
            "Cortex context packet for docs-adr-or-debt-slice derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["task_frame"]["lane_id"] = "docs-adr-or-debt-slice"
        payload["task_frame"]["owner_layer"] = "atlas"
        payload["task_frame"]["title"] = "Project the post-catch-up ATLAS systems lane."
        payload["task_frame"]["status"] = "ready"
        payload["task_frame"]["rationale"] = (
            "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation."
        )
        payload["task_frame"]["blocked_by"] = []
        payload["task_frame"]["ready_to_execute"] = True
        return payload

    def _base_operator_surface_payload(self) -> dict:
        payload = deepcopy(self.operator_surface_payload)
        payload["operator_summary"] = (
            "Cortex operator surface for docs-adr-or-debt-slice derived from explicit current-state, "
            "rail-state, context, validation, and seed artifacts."
        )
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "docs-adr-or-debt-slice",
            "owner_layer": "atlas",
            "rationale": "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["context_packet_id"] = "context-docs-adr-or-debt-slice"
        payload["context_summary"] = (
            "Cortex context packet for docs-adr-or-debt-slice derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["task_frame_summary"]["lane_id"] = "docs-adr-or-debt-slice"
        payload["task_frame_summary"]["owner_layer"] = "atlas"
        payload["task_frame_summary"]["title"] = "Project the post-catch-up ATLAS systems lane."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["rationale"] = (
            "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation."
        )
        payload["task_frame_summary"]["blocked_by"] = []
        payload["task_frame_summary"]["ready_to_execute"] = True
        payload["publication_posture"] = {
            "branch": "codex/cortex-receipt-interpretation-stack-consumption-wave10",
            "head": "abc123def456",
            "worktree_status": "clean",
            "remote_status": "in_sync",
            "upstream": "origin/codex/cortex-receipt-interpretation-stack-consumption-wave10",
            "published": True,
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/10",
        }
        return payload

    def _base_ledger_payload(self) -> dict:
        payload = deepcopy(self.ledger_payload)
        payload["ledger_id"] = "ledger-docs-adr-or-debt-slice"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = []
        payload["worktree_status"] = "clean"
        payload["branch"] = "codex/cortex-receipt-interpretation-stack-consumption-wave10"
        payload["head"] = "abc123def456"
        payload["remote_status"] = "in_sync"
        payload["upstream"] = "origin/codex/cortex-receipt-interpretation-stack-consumption-wave10"
        payload["published"] = True
        payload["next_recommended_lane"] = {
            "lane_id": "docs-adr-or-debt-slice",
            "owner_layer": "atlas",
            "rationale": "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation.",
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
        payload["context_packet_id"] = "context-docs-adr-or-debt-slice"
        payload["task_frame_summary"]["lane_id"] = "docs-adr-or-debt-slice"
        payload["task_frame_summary"]["owner_layer"] = "atlas"
        payload["task_frame_summary"]["title"] = "Project the post-catch-up ATLAS systems lane."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["rationale"] = (
            "Wave 11 and the ATLAS catch-up are already complete. The next bounded lane is an ATLAS root projection slice that keeps the live Cortex read model aligned with AI Repetition-to-Automation Pipeline, specifically the bounded receipt skeleton drafts control-plane surface, without reopening Cortex capability implementation."
        )
        payload["task_frame_summary"]["blocked_by"] = []
        payload["task_frame_summary"]["ready_to_execute"] = True
        payload["proof_or_receipt_readiness"] = {
            "status": "unavailable",
            "receipt_ready": None,
            "latest_run_id": None,
            "latest_run_path": None,
            "selected_next_action": None,
            "owner_layer": None,
            "next_required_layer": None,
            "blocked_reason": None,
            "known_ambient_debt": [],
            "current_validation_debt": [],
            "applied_rule_ids": [],
            "summary": "No Cortex run artifacts are available yet.",
        }
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
        _write_json(
            root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json",
            self._base_validation_payload(),
        )
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json", self.proof_payload)
        (root / "stack.lock.yaml").write_text(self.stack_lock_text, encoding="utf-8")
        persist_cortex_worker_prompt_artifact(root=root)
        persist_stack_advisory_handoff_artifact(root=root)
        persist_stack_consumption_pilot_artifact(root=root)
        persist_receipt_interpretation_artifact(root=root)
        return root

    def test_ready_consumption_from_clean_receipt_interpretation(self) -> None:
        root = self._temp_root()

        payload = build_receipt_interpretation_stack_consumption_payload(root=root)

        self.assertEqual("atlas.cortex.receipt-interpretation-stack-consumption.v1", payload["contract_version"])
        self.assertEqual("read_only_advisory", payload["authority_level"])
        self.assertEqual("_stack", payload["consumer"]["consumer_id"])
        self.assertEqual("artifact_refs_only", payload["consumer"]["consumption_mode"])
        self.assertTrue(payload["authority"]["stack_consumption_authorized"])
        self.assertFalse(payload["authority"]["automatic_dispatch_enabled"])
        self.assertFalse(payload["authority"]["final_receipt_authorized"])
        self.assertFalse(payload["authority"]["approval_authorized"])
        self.assertFalse(payload["authority"]["execution_authorized"])
        self.assertFalse(payload["authority"]["dispatch_authorized"])
        self.assertFalse(payload["authority"]["owner_truth_mutation_authorized"])
        self.assertFalse(payload["authority"]["lifeline_truth_mutation_authorized"])
        self.assertFalse(payload["authority"]["transcript_scraping_allowed"])
        self.assertEqual("ready", payload["consumption_result"]["status"])
        self.assertTrue(payload["consumption_result"]["ready_for_stack_consumer"])
        self.assertTrue(all(check["status"] == "passed" for check in payload["consumption_checks"]))
        self.assertIn(
            "Receipt interpretation proof posture is proof_ready.",
            payload["consumption_summary"]["what_proved"],
        )
        json.dumps(payload, sort_keys=True)

    def test_receipt_interpretation_authority_widening_blocks(self) -> None:
        root = self._temp_root()
        interpretation_path = root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json"
        interpretation = json.loads(interpretation_path.read_text(encoding="utf-8"))
        interpretation["authority"]["final_receipt_authorized"] = True
        _write_json(interpretation_path, interpretation)

        payload = build_receipt_interpretation_stack_consumption_payload(root=root)

        self.assertEqual("blocked", payload["consumption_result"]["status"])
        self.assertIn(
            "receipt-interpretation-authority-guard-clean",
            payload["consumption_result"]["failed_checks"],
        )
        self.assertFalse(payload["authority"]["final_receipt_authorized"])

    def test_receipt_interpretation_blocked_blocks_consumption(self) -> None:
        root = self._temp_root()
        interpretation_path = root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json"
        interpretation = json.loads(interpretation_path.read_text(encoding="utf-8"))
        interpretation["interpretation_result"]["status"] = "blocked"
        interpretation["interpretation_result"]["ready_for_stack_consumer"] = False
        interpretation["interpretation_result"]["blocked_reason"] = "Demo interpretation blocker."
        _write_json(interpretation_path, interpretation)

        payload = build_receipt_interpretation_stack_consumption_payload(root=root)

        self.assertEqual("blocked", payload["consumption_result"]["status"])
        self.assertIn("receipt-interpretation-ready", payload["consumption_result"]["failed_checks"])

    def test_validation_critical_or_error_blocks_consumption(self) -> None:
        root = self._temp_root()
        validation_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["summary"]["critical"] = 1
        validation["summary"]["error"] = 1
        validation["findings"] = [
            {
                "severity": "error",
                "category": "demo-validation-error",
                "message": "Demonstration blocker.",
            }
        ]
        _write_json(validation_path, validation)

        payload = build_receipt_interpretation_stack_consumption_payload(root=root)

        self.assertEqual("blocked", payload["consumption_result"]["status"])
        self.assertIn("validation-critical-error-absent", payload["consumption_result"]["failed_checks"])

    def test_transcript_ref_blocks_consumption(self) -> None:
        root = self._temp_root()
        interpretation_path = root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json"
        interpretation = json.loads(interpretation_path.read_text(encoding="utf-8"))
        interpretation["source_refs"].append("runtime/atlas/conversations/demo-transcript.json")
        _write_json(interpretation_path, interpretation)

        payload = build_receipt_interpretation_stack_consumption_payload(root=root)

        self.assertEqual("blocked", payload["consumption_result"]["status"])
        self.assertIn("transcript-scraping-absent", payload["consumption_result"]["failed_checks"])

    def test_markdown_summary_includes_boundary_language(self) -> None:
        root = self._temp_root()

        artifact = persist_receipt_interpretation_stack_consumption_artifact(root=root)
        payload = json.loads(
            default_receipt_interpretation_stack_consumption_latest_json_path(root).read_text(encoding="utf-8")
        )
        summary = default_receipt_interpretation_stack_consumption_latest_markdown_path(root).read_text(
            encoding="utf-8"
        )

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Receipt Interpretation Stack Consumption", summary)
        lowered = summary.lower()
        self.assertIn("artifact_refs_only", lowered)
        self.assertIn("final receipt authorized: `no`", lowered)
        self.assertIn("dispatch authorized: `no`", lowered)
        self.assertIn("no transcript scraping", lowered)
        self.assertIn("lifeline owns final receipt authority", lowered)

    def test_missing_receipt_interpretation_fails_clearly(self) -> None:
        root = self._temp_root()
        (root / "runtime" / "cortex" / "receipt-interpretation" / "latest.json").unlink()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex receipt-interpretation artifact not found", stderr.getvalue())

    def test_schema_declares_emitted_top_level_payload_shape(self) -> None:
        root = self._temp_root()

        payload = build_receipt_interpretation_stack_consumption_payload(root=root)
        schema = self.schema_payload

        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(set(payload.keys()).issubset(set(schema["properties"].keys())))
        for required_key in schema["required"]:
            self.assertIn(required_key, payload)


if __name__ == "__main__":
    unittest.main()
