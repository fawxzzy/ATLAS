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

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "current-state" / "latest.json", self.current_state_payload)
        _write_json(root / "runtime" / "cortex" / "rail-state" / "latest.json", self.rail_state_payload)
        _write_json(root / "runtime" / "cortex" / "context" / "latest.json", self.context_payload)
        _write_json(root / "runtime" / "cortex" / "operator-surface" / "latest.json", self.operator_surface_payload)
        _write_json(root / "runtime" / "cortex" / "ledger" / "latest.json", self.ledger_payload)
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self.validation_payload)
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
        self.assertEqual("promote-cortex-worker-prompt-contract-wave6", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual("context-promote-cortex-worker-prompt-contract-wave6", payload["context_packet_id"])
        self.assertEqual("cortex_worker_prompt_contract", payload["planner_contract"]["template_id"])
        self.assertIn("implementation_plan", payload["planner_contract"])
        self.assertIn("failure_modes_to_avoid", payload["planner_contract"])
        self.assertEqual("assignment-promote-cortex-worker-prompt-contract-wave6", payload["assignment_id"])
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
        self.assertIn("promote-cortex-worker-prompt-contract-wave6", summary)
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
