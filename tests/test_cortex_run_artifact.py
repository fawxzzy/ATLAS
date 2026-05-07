from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.run_artifact import main, persist_cortex_run_artifact


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexRunArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.state_path = cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json"
        cls.rule_path = cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json"
        cls.proof_path = cls.root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json"

    def _state_payload(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _rule_payload(self) -> dict:
        return json.loads(self.rule_path.read_text(encoding="utf-8"))

    def _proof_payload(self) -> dict:
        return json.loads(self.proof_path.read_text(encoding="utf-8"))

    def _seed_temp_root(self, state_payload: dict | None = None) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", state_payload or self._state_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self._rule_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json", self._proof_payload())
        return root

    def test_persisted_run_artifact_writes_valid_json_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = persist_cortex_run_artifact(
                root=self.root,
                output_json_path=root / "runtime" / "cortex" / "runs" / "result.json",
                output_summary_path=root / "runtime" / "cortex" / "runs" / "result.txt",
            )

            payload = json.loads(artifact.artifact_path.read_text(encoding="utf-8"))
            summary = artifact.summary_path.read_text(encoding="utf-8") if artifact.summary_path is not None else ""

        self.assertEqual("pilot-cortex-worker-prompt-stack-consumption-wave7", payload["selected_next_action"]["action_id"])
        self.assertEqual("cortex_stack_consumption_pilot", payload["worker_plan"]["template_id"])
        self.assertTrue(payload["receipt_ready"])
        self.assertTrue(payload["known_ambient_debt"])
        self.assertIn("selected_next_action", json.dumps(payload, sort_keys=True))
        self.assertIn("Worker plan template: cortex_stack_consumption_pilot", summary)
        self.assertIn("Receipt ready: yes", summary)
        self.assertIn("Patterns applied:", summary)
        self.assertIn("implementation_plan", payload["worker_plan"])
        self.assertIn("failure_modes_to_avoid", payload["worker_plan"])

    def test_cli_prints_summary_and_writes_default_artifact_paths(self) -> None:
        root = self._seed_temp_root()
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root)])

        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Cortex Run Result", stdout.getvalue())
        self.assertTrue((root / "runtime" / "cortex" / "runs" / "cortex-run-result.latest.json").exists())
        self.assertTrue((root / "runtime" / "cortex" / "runs" / "cortex-run-result.latest.txt").exists())

    def test_missing_seed_files_fail_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["--root", temp_dir, "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex state model seed not found", stderr.getvalue())

    def test_unsupported_next_action_fails_clearly(self) -> None:
        state_payload = self._state_payload()
        state_payload["posture"]["classification"] = "steady"
        state_payload["posture"]["rail_state"]["next_action"]["action_id"] = "open-connector-work"
        state_payload["posture"]["rail_state"]["next_action"]["owner_layer"] = "connector"
        state_payload["posture"]["rail_state"]["next_action"]["title"] = "Open connector work."
        state_payload["posture"]["rail_state"]["next_action"]["rationale"] = "Connectors stay out of scope for the first run artifact surface."
        state_payload["posture"]["rail_state"]["latest_clean_step"]["owner_layer"] = "connector"
        root = self._seed_temp_root(state_payload)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Unsupported Cortex NextAction", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
