from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.workflow_resilience_simulator import _state, run


def write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(receipt_id: str, status: str, recorded_at: str) -> dict[str, object]:
    if status in {"succeeded", "failed", "blocked", "awaiting-review"}:
        verification_status = {"succeeded": "passed", "failed": "failed", "blocked": "blocked", "awaiting-review": "skipped"}[status]
        return {"contract_version": "atlas.execution-receipt.v2", "receipt_id": receipt_id, "recorded_at": recorded_at, "status": status, "verification": [{"status": verification_status}], "summary": status}
    return {"contract_version": "atlas.receipt.v1", "receipt_id": receipt_id, "recorded_at": recorded_at, "status": status, "summary": status}


class WorkflowResilienceSimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = "data/cortex/simulation-replays/workflow"
        self.replay_ref = f"{self.base}/replay-manifest.json"
        self.manifest_ref = f"{self.base}/simulator-manifest.json"
        self.first_ref = f"{self.base}/first.json"
        self.second_ref = f"{self.base}/second.json"

    def configure(self, first: dict[str, object], second: dict[str, object] | None = None) -> dict[str, object]:
        entries = [{"ref": self.first_ref, "digest": write_json(self.root / self.first_ref, first), "trust_class": "committed_replay_fixture"}]
        if second is not None:
            entries.append({"ref": self.second_ref, "digest": write_json(self.root / self.second_ref, second), "trust_class": "committed_replay_fixture"})
        replay_manifest = {"contract_version": "atlas.cortex.simulation.receipt-replay-manifest.v1", "scenario_id": "replay", "agent_id": "agent", "generated_at": "2026-07-14T12:00:00Z", "objective": "rehearse", "receipts": entries}
        replay_digest = write_json(self.root / self.replay_ref, replay_manifest)
        manifest = {"contract_version": "atlas.cortex.simulation.workflow-resilience-manifest.v1", "scenario_id": "workflow", "generated_at": "2026-07-14T12:01:00Z", "adapter_id": "atlas-workflow-resilience", "receipt_replay_manifest_ref": self.replay_ref, "receipt_replay_manifest_digest": replay_digest, "max_steps": 4, "scenario_classes": ["observed", "proof_recovery", "blocked_hold"]}
        write_json(self.root / self.manifest_ref, manifest)
        return manifest

    def test_blocked_mixed_replay_is_deterministic_bounded_and_authority_false(self) -> None:
        self.configure(receipt("passed", "passed", "2026-07-14T11:00:00Z"), receipt("blocked", "blocked", "2026-07-14T11:01:00Z"))
        first, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
        second, second_code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
        self.assertEqual((0, 0), (code, second_code))
        self.assertEqual(first, second)
        simulation = first["simulation"]
        self.assertEqual("atlas.cortex.simulation.workflow-resilience.v1", simulation["contract_version"])
        self.assertEqual("blocked", simulation["observed_state"])
        self.assertTrue(simulation["termination"]["terminated"])
        self.assertLessEqual(len(simulation["steps"]), 4)
        self.assertTrue(all(not value for key, value in simulation["authority"].items() if key != "advisory_only"))
        self.assertTrue(all(not step["executed"] for step in simulation["steps"]))
        self.assertFalse((self.root / "tmp").exists())

    def test_state_classification_covers_success_failure_advisory_and_blocked(self) -> None:
        self.assertEqual("healthy", _state({"success": 1, "advisory": 0, "failure": 0, "blocked": 0}))
        self.assertEqual("watch", _state({"success": 1, "advisory": 1, "failure": 0, "blocked": 0}))
        for status, expected in (("failed", "failed"), ("blocked", "blocked")):
            with self.subTest(status=status):
                self.configure(
                    receipt("passed", "passed", "2026-07-14T10:59:00Z"),
                    receipt(status, status, "2026-07-14T11:00:00Z"),
                )
                result, _ = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
                self.assertEqual(expected, result["simulation"]["observed_state"])

    def test_max_steps_and_scenario_class_filter_terminate(self) -> None:
        manifest = self.configure(receipt("passed", "passed", "2026-07-14T11:00:00Z"), receipt("blocked", "blocked", "2026-07-14T11:01:00Z"))
        manifest["max_steps"] = 1
        manifest["scenario_classes"] = ["observed"]
        write_json(self.root / self.manifest_ref, manifest)
        result, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
        self.assertEqual(0, code)
        self.assertEqual(1, len(result["simulation"]["steps"]))
        self.assertEqual("fixed_template_exhausted", result["simulation"]["termination"]["reason"])

    def test_digest_unknown_fields_invalid_steps_and_unsafe_paths_fail_closed(self) -> None:
        manifest = self.configure(receipt("passed", "passed", "2026-07-14T11:00:00Z"), receipt("blocked", "blocked", "2026-07-14T11:01:00Z"))
        variants = []
        bad = copy.deepcopy(manifest); bad["receipt_replay_manifest_digest"] = "sha256:" + "0" * 64; variants.append((bad, "replay_manifest_digest_mismatch"))
        bad = copy.deepcopy(manifest); bad["execute"] = True; variants.append((bad, "unknown_manifest_fields"))
        bad = copy.deepcopy(manifest); bad["max_steps"] = 9; variants.append((bad, "max_steps_invalid"))
        bad = copy.deepcopy(manifest); bad["scenario_classes"] = ["live_mutation"]; variants.append((bad, "scenario_classes_invalid"))
        for payload, code in variants:
            write_json(self.root / self.manifest_ref, payload)
            result, exit_code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
            self.assertEqual(1, exit_code)
            self.assertIn(code, [item["code"] for item in result["blockers"]])
        for unsafe in ("../sim.json", "repos/mazer/sim.json", "secrets/sim.json"):
            self.assertEqual("blocker", run(root=self.root, manifest_path=unsafe, output_path=None)[0]["status"])

    def test_writes_only_to_explicit_safe_output(self) -> None:
        self.configure(receipt("passed", "passed", "2026-07-14T11:00:00Z"), receipt("blocked", "blocked", "2026-07-14T11:01:00Z"))
        output = "tmp/atlas/workflow-resilience.json"
        result, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=output)
        self.assertEqual(0, code)
        self.assertEqual(result["simulation"], json.loads((self.root / output).read_text(encoding="utf-8")))
        self.assertEqual("blocker", run(root=self.root, manifest_path=self.manifest_ref, output_path="../output.json")[0]["status"])


if __name__ == "__main__":
    unittest.main()
