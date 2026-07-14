from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ops.cortex.read_only_scenario_helper import main, run
from tests.test_cortex_simulation_agent_state_schema import SCHEMA_PATH, validate_contract


DIGEST = "sha256:" + "a" * 64


def fixture() -> dict[str, object]:
    return {
        "scenario_id": "synthetic-scenario-1",
        "agent_id": "synthetic-agent-1",
        "generated_at": "2026-07-14T05:00:00-04:00",
        "objective": "Rehearse a bounded advisory decision.",
        "minimum_confidence": 0.7,
        "scoring": {"recency_weight": 0.3, "importance_weight": 0.3, "relevance_weight": 0.4},
        "observations": [
            {
                "observed_at": "2026-07-14T04:55:00-04:00",
                "content_summary": "Synthetic receipt evidence is available.",
                "source_ref": "data/cortex/simulation-fixtures/scenario.json",
                "source_digest": DIGEST,
                "importance": 0.8,
                "confidence": 0.9,
                "retention_class": "project",
                "rights_class": "synthetic",
                "privacy_class": "internal",
                "injection_state": "trusted",
            }
        ],
    }


class CortexReadOnlyScenarioHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input_ref = "data/cortex/simulation-fixtures/scenario.json"
        input_path = self.root / self.input_ref
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(json.dumps(fixture()) + "\n", encoding="utf-8")
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_builds_deterministic_schema_valid_advisory_state(self) -> None:
        first, first_code = run(root=self.root, input_path=self.input_ref, output_path=None)
        second, second_code = run(root=self.root, input_path=self.input_ref, output_path=None)
        self.assertEqual(0, first_code)
        self.assertEqual(0, second_code)
        self.assertEqual(first, second)
        validate_contract(first["state"], self.schema, self.schema)
        self.assertFalse(first["state"]["authority"]["execution_authorized"])
        self.assertFalse(first["state"]["active_plan"]["execution_authorized"])
        self.assertFalse((self.root / "tmp").exists())

    def test_writes_only_to_explicit_safe_output(self) -> None:
        output_ref = "tmp/atlas/scenario-state.json"
        result, code = run(root=self.root, input_path=self.input_ref, output_path=output_ref)
        self.assertEqual(0, code)
        self.assertTrue((self.root / output_ref).exists())
        self.assertEqual(result["state"], json.loads((self.root / output_ref).read_text(encoding="utf-8")))

    def test_rejects_absolute_traversal_owner_and_secret_paths(self) -> None:
        for unsafe in (str((self.root / self.input_ref).resolve()), "../scenario.json", "repos/mazer/scenario.json", "secrets/scenario.json"):
            result, code = run(root=self.root, input_path=unsafe, output_path=None)
            self.assertEqual(1, code)
            self.assertEqual("blocker", result["status"])

    def test_rejects_unsafe_output_paths_without_writing(self) -> None:
        for unsafe in (str((self.root / "state.json").resolve()), "../state.json", "repos/mazer/state.json", "secrets/state.json"):
            result, code = run(root=self.root, input_path=self.input_ref, output_path=unsafe)
            self.assertEqual(1, code)
            self.assertEqual("blocker", result["status"])
            self.assertFalse((self.root / "state.json").exists())

    def test_rejects_unknown_fixture_fields(self) -> None:
        payload = fixture()
        payload["execute"] = True
        (self.root / self.input_ref).write_text(json.dumps(payload) + "\n", encoding="utf-8")
        result, code = run(root=self.root, input_path=self.input_ref, output_path=None)
        self.assertEqual(1, code)
        self.assertEqual("unknown_fixture_fields", result["blockers"][0]["code"])

    def test_rejects_unsafe_rights_privacy_and_injection(self) -> None:
        for field, value in (
            ("rights_class", "unknown_blocked"),
            ("privacy_class", "sensitive_prohibited"),
            ("injection_state", "rejected"),
        ):
            payload = fixture()
            payload["observations"][0][field] = value
            (self.root / self.input_ref).write_text(json.dumps(payload) + "\n", encoding="utf-8")
            result, code = run(root=self.root, input_path=self.input_ref, output_path=None)
            self.assertEqual(1, code)
            self.assertEqual("blocker", result["status"])

    def test_rejects_unsafe_observation_source_refs(self) -> None:
        for source_ref in ("../secret.json", "repos/mazer/state.json", "secrets/state.json"):
            payload = fixture()
            payload["observations"][0]["source_ref"] = source_ref
            (self.root / self.input_ref).write_text(json.dumps(payload) + "\n", encoding="utf-8")
            result, code = run(root=self.root, input_path=self.input_ref, output_path=None)
            self.assertEqual(1, code)
            self.assertIn("source_ref_not_admitted", [item["code"] for item in result["blockers"]])

    def test_invalid_scoring_returns_blocker_instead_of_raising(self) -> None:
        payload = fixture()
        payload["scoring"]["recency_weight"] = "not-a-number"
        (self.root / self.input_ref).write_text(json.dumps(payload) + "\n", encoding="utf-8")
        result, code = run(root=self.root, input_path=self.input_ref, output_path=None)
        self.assertEqual(1, code)
        self.assertEqual("blocker", result["status"])
        self.assertIn("invalid_score", [item["code"] for item in result["blockers"]])

    def test_strict_mode_returns_nonzero_for_empty_observations(self) -> None:
        payload = fixture()
        payload["observations"] = []
        (self.root / self.input_ref).write_text(json.dumps(payload) + "\n", encoding="utf-8")
        with patch("ops.cortex.read_only_scenario_helper.atlas_root", return_value=self.root):
            self.assertEqual(1, main(["--json", "--strict", "--input", self.input_ref]))


if __name__ == "__main__":
    unittest.main()
