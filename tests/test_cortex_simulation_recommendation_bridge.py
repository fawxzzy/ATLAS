from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.simulation_recommendation_bridge import PLAYBOOK_ADOPTION_REF, run
from tests.test_cortex_workflow_resilience_simulator import WorkflowResilienceSimulatorTests, receipt, write_json


class SimulationRecommendationBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture = WorkflowResilienceSimulatorTests(methodName="runTest")
        fixture.root = self.root
        fixture.base = "data/cortex/simulation-replays/workflow"
        fixture.replay_ref = f"{fixture.base}/replay-manifest.json"
        fixture.manifest_ref = f"{fixture.base}/simulator-manifest.json"
        fixture.first_ref = f"{fixture.base}/first.json"
        fixture.second_ref = f"{fixture.base}/second.json"
        fixture.configure(receipt("passed", "passed", "2026-07-14T11:00:00Z"), receipt("blocked", "blocked", "2026-07-14T11:01:00Z"))
        self.manifest_ref = fixture.manifest_ref
        self.adoption = {
            "contract_version": "atlas.playbook_doctrine_adoption.v1",
            "source": {"repository_path": "repos/playbook", "accepted_commit": "a" * 40, "artifacts": {"registry": {"path": "docs/doctrine/registry.json", "sha256": "b" * 64}}},
            "registry": {"adopted_record_ids": {"promoted": ["rule-proof"]}},
        }
        write_json(self.root / PLAYBOOK_ADOPTION_REF, self.adoption)

    def test_projects_deterministic_playbook_candidates_and_cortex_recommendations(self) -> None:
        first, code = run(root=self.root, simulator_manifest_path=self.manifest_ref, output_path=None)
        second, second_code = run(root=self.root, simulator_manifest_path=self.manifest_ref, output_path=None)
        self.assertEqual((0, 0), (code, second_code))
        self.assertEqual(first, second)
        envelope = first["envelope"]
        self.assertEqual("atlas.cortex.simulation.recommendation-envelope.v1", envelope["contract_version"])
        candidates = envelope["playbook_projection"]["candidates"]
        self.assertEqual({"rule_candidate", "pattern_candidate", "failure_mode_candidate"}, {item["record_type"] for item in candidates})
        self.assertTrue(all(item["promotion_state"] == "candidate_only" and not item["promotion_authorized"] for item in candidates))
        self.assertEqual(len(envelope["cortex_projection"]["recommendations"]), 2)
        self.assertTrue(all(not item["execution_authorized"] and not item["dispatch_authorized"] for item in envelope["cortex_projection"]["recommendations"]))
        self.assertTrue(all(not value for key, value in envelope["authority"].items() if key != "advisory_only"))
        self.assertFalse((self.root / "tmp").exists())

    def test_doctrine_contract_drift_and_simulator_blocker_fail_closed(self) -> None:
        bad = dict(self.adoption)
        bad["contract_version"] = "atlas.unknown.v1"
        write_json(self.root / PLAYBOOK_ADOPTION_REF, bad)
        result, code = run(root=self.root, simulator_manifest_path=self.manifest_ref, output_path=None)
        self.assertEqual(1, code)
        self.assertIn("playbook_adoption_contract_invalid", [item["code"] for item in result["blockers"]])
        write_json(self.root / PLAYBOOK_ADOPTION_REF, self.adoption)
        result, code = run(root=self.root, simulator_manifest_path="../unsafe.json", output_path=None)
        self.assertEqual(1, code)
        self.assertIn("simulation_not_eligible", [item["code"] for item in result["blockers"]])

    def test_writes_only_to_explicit_safe_output(self) -> None:
        output = "tmp/atlas/recommendations.json"
        result, code = run(root=self.root, simulator_manifest_path=self.manifest_ref, output_path=output)
        self.assertEqual(0, code)
        self.assertEqual(result["envelope"], json.loads((self.root / output).read_text(encoding="utf-8")))
        self.assertEqual("blocker", run(root=self.root, simulator_manifest_path=self.manifest_ref, output_path="../recommendations.json")[0]["status"])


if __name__ == "__main__":
    unittest.main()
