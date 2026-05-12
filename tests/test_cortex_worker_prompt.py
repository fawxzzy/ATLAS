from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.worker_prompt import (
    build_cortex_worker_prompt_payload,
    default_worker_prompt_latest_json_path,
    default_worker_prompt_latest_markdown_path,
    main,
    persist_cortex_worker_prompt_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexWorkerPromptTests(unittest.TestCase):
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
            "generated_at": "2026-05-06T22:00:00+00:00",
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
        payload = json.loads(json.dumps(self.current_state_payload))
        payload["generated_at"] = "2026-05-06T22:01:00+00:00"
        payload["branch"] = "codex/cortex-worker-prompt-contract-wave6"
        payload["head"] = "abc123def456"
        payload["worktree_status"] = "clean"
        payload["changed_files"] = []
        payload["untracked_files"] = []
        payload["remote_status"] = {
            "status": "in_sync",
            "upstream": "origin/codex/cortex-worker-prompt-contract-wave6",
            "ahead": 0,
            "behind": 0,
        }
        payload["remote_publication_state"] = {
            "status": "in_sync",
            "branch": "codex/cortex-worker-prompt-contract-wave6",
            "head": "abc123def456",
            "published": True,
            "upstream": "origin/codex/cortex-worker-prompt-contract-wave6",
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/12",
            "notes": [],
        }
        payload["validation_receipt"] = {
            "generated_at": "2026-05-06T22:00:00+00:00",
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
        payload["active_blockers"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_rail_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.rail_state_payload))
        payload["generated_at"] = "2026-05-06T22:02:00+00:00"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-consumption-feedback-v0-1"]
        payload["validation_posture"] = {
            "status": "ambient-debt-only",
            "counts": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
            "receipt_generated_at": "2026-05-06T22:00:00+00:00",
            "receipt_path": "runtime/receipts/validation/stack-validation.latest.json",
        }
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_context_payload(self) -> dict:
        payload = json.loads(json.dumps(self.context_payload))
        payload["generated_at"] = "2026-05-06T22:03:00+00:00"
        payload["packet_id"] = "context-promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["context_summary"] = (
            "Cortex context packet for promote-cortex-receipt-interpretation-consumption-feedback-wave11 derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["task_frame"]["lane_id"] = "promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["task_frame"]["owner_layer"] = "cortex"
        payload["task_frame"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame"]["status"] = "ready"
        payload["task_frame"]["rationale"] = (
            "The worker-prompt contract is landed, but Cortex still needs one bounded _stack pilot that consumes current "
            "context and planning artifacts without transcript scraping while planner, context, proof, receipt-draft, "
            "and final receipt stay separate and linked by refs and digests."
        )
        payload["task_frame"]["blocked_by"] = []
        payload["task_frame"]["required_inputs"] = [
            "runtime/cortex/current-state/latest.json",
            "runtime/cortex/rail-state/latest.json",
            "runtime/cortex/context/latest.json",
            "runtime/cortex/operator-surface/latest.json",
            "runtime/cortex/ledger/latest.json",
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/kernel.state-model.seed.v1.json",
            "runtime/cortex/kernel.rule-registry.seed.v1.json",
            "docs/atlas/notes/cortex-surface-reconciliation-2026-05-06.md",
        ]
        payload["task_frame"]["ready_to_execute"] = True
        return payload

    def _base_operator_surface_payload(self) -> dict:
        payload = json.loads(json.dumps(self.operator_surface_payload))
        payload["generated_at"] = "2026-05-06T22:04:00+00:00"
        payload["operator_summary"] = (
            "Cortex operator surface for promote-cortex-receipt-interpretation-consumption-feedback-wave11 derived from explicit current-state, "
            "rail-state, context, validation, and seed artifacts."
        )
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-consumption-feedback-v0-1"]
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["context_packet_id"] = "context-promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["context_summary"] = (
            "Cortex context packet for promote-cortex-receipt-interpretation-consumption-feedback-wave11 derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["task_frame_summary"]["owner_layer"] = "cortex"
        payload["task_frame_summary"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["rationale"] = (
            "The worker-prompt contract is landed, but Cortex still needs one bounded _stack pilot that consumes current "
            "context and planning artifacts without transcript scraping while planner, context, proof, receipt-draft, "
            "and final receipt stay separate and linked by refs and digests."
        )
        payload["task_frame_summary"]["blocked_by"] = []
        payload["task_frame_summary"]["required_inputs"] = [
            "runtime/cortex/current-state/latest.json",
            "runtime/cortex/rail-state/latest.json",
            "runtime/cortex/context/latest.json",
            "runtime/cortex/operator-surface/latest.json",
            "runtime/cortex/ledger/latest.json",
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/kernel.state-model.seed.v1.json",
            "runtime/cortex/kernel.rule-registry.seed.v1.json",
            "docs/atlas/notes/cortex-surface-reconciliation-2026-05-06.md",
        ]
        payload["task_frame_summary"]["ready_to_execute"] = True
        payload["publication_posture"] = {
            "branch": "codex/cortex-worker-prompt-contract-wave6",
            "head": "abc123def456",
            "worktree_status": "clean",
            "remote_status": "in_sync",
            "upstream": "origin/codex/cortex-worker-prompt-contract-wave6",
            "published": True,
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/12",
        }
        return payload

    def _base_ledger_payload(self) -> dict:
        payload = json.loads(json.dumps(self.ledger_payload))
        payload["generated_at"] = "2026-05-06T22:05:00+00:00"
        payload["ledger_id"] = "ledger-promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-consumption-feedback-v0-1"]
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["worktree_status"] = "clean"
        payload["branch"] = "codex/cortex-worker-prompt-contract-wave6"
        payload["head"] = "abc123def456"
        payload["remote_status"] = "in_sync"
        payload["upstream"] = "origin/codex/cortex-worker-prompt-contract-wave6"
        payload["published"] = True
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-consumption-feedback-wave11",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
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
        payload["context_packet_id"] = "context-promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-receipt-interpretation-consumption-feedback-wave11"
        payload["task_frame_summary"]["owner_layer"] = "cortex"
        payload["task_frame_summary"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["rationale"] = (
            "The worker-prompt contract is landed, but Cortex still needs one bounded _stack pilot that consumes current "
            "context and planning artifacts without transcript scraping while planner, context, proof, receipt-draft, "
            "and final receipt stay separate and linked by refs and digests."
        )
        payload["task_frame_summary"]["blocked_by"] = []
        payload["task_frame_summary"]["required_inputs"] = [
            "runtime/cortex/current-state/latest.json",
            "runtime/cortex/rail-state/latest.json",
            "runtime/cortex/context/latest.json",
            "runtime/cortex/operator-surface/latest.json",
            "runtime/cortex/ledger/latest.json",
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/kernel.state-model.seed.v1.json",
            "runtime/cortex/kernel.rule-registry.seed.v1.json",
            "docs/atlas/notes/cortex-surface-reconciliation-2026-05-06.md",
        ]
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
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self._base_validation_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json", self.proof_payload)
        (root / "stack.lock.yaml").write_text(self.stack_lock_text, encoding="utf-8")
        return root

    def test_clean_ready_posture_emits_worker_prompt_contract(self) -> None:
        root = self._temp_root()

        payload = build_cortex_worker_prompt_payload(root=root)

        self.assertEqual("atlas.cortex.worker-prompt.v1", payload["contract_version"])
        self.assertEqual("read_only_advisory", payload["authority_level"])
        self.assertEqual("promote-cortex-receipt-interpretation-consumption-feedback-wave11", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual("context-promote-cortex-receipt-interpretation-consumption-feedback-wave11", payload["context_packet_id"])
        self.assertEqual(
            "cortex_receipt_interpretation_stack_consumption_contract",
            payload["planner_contract"]["template_id"],
        )
        self.assertIn("implementation_plan", payload["planner_contract"])
        self.assertIn("failure_modes_to_avoid", payload["planner_contract"])
        self.assertEqual("assignment-promote-cortex-receipt-interpretation-consumption-feedback-wave11", payload["assignment_id"])
        self.assertTrue(str(payload["stack_lock_digest"]).startswith("sha256:"))
        self.assertIn(
            "runtime/cortex/kernel.proof-summary.examples.v1.json",
            payload["source_refs"],
        )
        self.assertEqual(
            "runtime/cortex/context/latest.json",
            payload["source_artifact_refs"]["context"],
        )
        self.assertEqual("embedded_preview", payload["separation_refs"]["planner"]["status"])
        self.assertEqual("source_artifact", payload["separation_refs"]["proof"]["status"])
        self.assertEqual("not_emitted_by_cortex", payload["separation_refs"]["final_receipt"]["status"])
        self.assertEqual([], payload["task_frame_summary"]["blocked_by"])
        self.assertTrue(payload["non_execution_guards"])
        json.dumps(payload, sort_keys=True)

    def test_markdown_summary_includes_lane_verification_and_guards(self) -> None:
        root = self._temp_root()

        artifact = persist_cortex_worker_prompt_artifact(root=root)
        payload = json.loads(default_worker_prompt_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_worker_prompt_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Worker Prompt", summary)
        self.assertIn("promote-cortex-receipt-interpretation-consumption-feedback-wave11", summary)
        self.assertIn("Verification Steps", summary)
        self.assertIn("Non-Execution Guards", summary)
        self.assertIn("Stack lock digest", summary)

    def test_missing_required_current_state_fails_clearly(self) -> None:
        root = self._temp_root()
        (root / "runtime" / "cortex" / "current-state" / "latest.json").unlink()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex current-state artifact not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

