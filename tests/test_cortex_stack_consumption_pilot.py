from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.stack_consumption_pilot import (
    build_stack_consumption_pilot_payload,
    default_stack_consumption_pilot_latest_json_path,
    default_stack_consumption_pilot_latest_markdown_path,
    main,
    persist_stack_consumption_pilot_artifact,
)
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
        persist_cortex_worker_prompt_artifact(root=root)
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
            "promote-cortex-stack-consumer-default-routing-wave8",
            payload["next_recommended_lane"]["lane_id"],
        )
        self.assertEqual("runtime/cortex/worker-prompts/latest.json", payload["stack_handoff"]["worker_prompt_ref"])
        self.assertEqual("runtime/cortex/context/latest.json", payload["stack_handoff"]["context_ref"])
        self.assertFalse(payload["stack_handoff"]["execution_authorized"])
        self.assertFalse(payload["stack_handoff"]["receipt_authorized"])
        self.assertFalse(payload["stack_handoff"]["owner_truth_mutation_authorized"])
        self.assertFalse(payload["stack_handoff"]["default_routing_enabled"])
        self.assertFalse(payload["stack_handoff"]["transcript_scraping_allowed"])
        self.assertFalse(payload["transcript_scraping"]["detected"])
        self.assertEqual([], payload["transcript_scraping"]["detected_refs"])
        self.assertIsNone(payload["stack_handoff"]["final_receipt_ref"])
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
        self.assertIn("promote-cortex-stack-consumer-default-routing-wave8", summary)
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
