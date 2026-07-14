from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.simulation_recommendation_evaluator import run
from ops.cortex.simulation_recommendation_bridge import PLAYBOOK_ADOPTION_REF
from tests.test_cortex_workflow_resilience_simulator import WorkflowResilienceSimulatorTests, receipt, write_json


class SimulationRecommendationEvaluatorTests(unittest.TestCase):
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
        self.simulator_ref = fixture.manifest_ref
        adoption = {"contract_version": "atlas.playbook_doctrine_adoption.v1", "source": {"repository_path": "repos/playbook", "accepted_commit": "a" * 40, "artifacts": {"registry": {"path": "docs/doctrine/registry.json", "sha256": "b" * 64}}}, "registry": {"adopted_record_ids": {"promoted": ["rule-proof"]}}}
        write_json(self.root / PLAYBOOK_ADOPTION_REF, adoption)
        from ops.cortex.simulation_recommendation_bridge import run as run_bridge
        bridge, _ = run_bridge(root=self.root, simulator_manifest_path=self.simulator_ref, output_path=None)
        envelope_id = bridge["envelope"]["envelope_id"]
        digest = "sha256:" + __import__("hashlib").sha256((self.root / self.simulator_ref).read_bytes()).hexdigest()
        self.manifest_ref = "data/cortex/simulation-evaluations/test/manifest.json"
        self.manifest = {"contract_version": "atlas.cortex.simulation.recommendation-evaluation-manifest.v1", "evaluation_id": "test-loop", "generated_at": "2026-07-14T14:00:00Z", "cases": [
            {"case_id": "match", "simulator_manifest_ref": self.simulator_ref, "simulator_manifest_digest": digest, "expected_envelope_id": envelope_id, "expected_classification": "match"},
            {"case_id": "changed", "simulator_manifest_ref": self.simulator_ref, "simulator_manifest_digest": digest, "expected_envelope_id": "sha256:" + "0" * 64, "expected_classification": "changed"},
            {"case_id": "invalid", "simulator_manifest_ref": "data/cortex/simulation-replays/workflow/missing.json", "simulator_manifest_digest": "sha256:" + "0" * 64, "expected_envelope_id": None, "expected_classification": "invalid"},
        ]}
        write_json(self.root / self.manifest_ref, self.manifest)

    def test_three_class_loop_is_deterministic_terminating_and_authority_false(self) -> None:
        first, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
        second, second_code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
        self.assertEqual((0, 0), (code, second_code))
        self.assertEqual(first, second)
        evaluation = first["evaluation"]
        self.assertEqual({"match": 1, "changed": 1, "invalid": 1}, evaluation["classification_counts"])
        self.assertTrue(evaluation["threshold_eligible"])
        self.assertTrue(evaluation["termination"]["terminated"])
        self.assertTrue(all(item["expectation_met"] and not item["mutation_authorized"] for item in evaluation["case_results"]))
        self.assertTrue(all(not value for key, value in evaluation["authority"].items() if key != "advisory_only"))

    def test_duplicate_ids_unknown_fields_and_invalid_classification_fail_closed(self) -> None:
        variants = []
        bad = copy.deepcopy(self.manifest); bad["cases"][1]["case_id"] = "match"; variants.append((bad, "case_id_invalid"))
        bad = copy.deepcopy(self.manifest); bad["execute"] = True; variants.append((bad, "manifest_invalid"))
        bad = copy.deepcopy(self.manifest); bad["cases"][0]["expected_classification"] = "approved"; variants.append((bad, "case_invalid"))
        for payload, expected in variants:
            write_json(self.root / self.manifest_ref, payload)
            result, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=None)
            self.assertEqual(1, code)
            self.assertIn(expected, [item["code"] for item in result["blockers"]])

    def test_safe_output_and_unsafe_manifest_paths(self) -> None:
        output = "tmp/atlas/evaluation.json"
        result, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=output)
        self.assertEqual(0, code)
        self.assertEqual(result["evaluation"], json.loads((self.root / output).read_text(encoding="utf-8")))
        self.assertEqual("blocker", run(root=self.root, manifest_path="../manifest.json", output_path=None)[0]["status"])
        self.assertEqual("blocker", run(root=self.root, manifest_path=self.manifest_ref, output_path="../output.json")[0]["status"])


if __name__ == "__main__":
    unittest.main()
