from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas import sandbox_validator_runner as runner


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class SandboxValidatorRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self._seed()

    def _seed(self) -> None:
        _write(self.root / runner.SCENARIO_REF, {
            "scenario_id": runner.SCENARIO_ID,
            "status": "active",
            "fixture_refs": [runner.FIXTURE_PACK_REF],
            "guards": {key: False for key in runner.AUTHORITY_GUARD_KEYS},
        })
        _write(self.root / runner.FIXTURE_PACK_REF, {
            "scenario_id": runner.SCENARIO_ID,
            "status": "active",
            "guards": {key: False for key in runner.AUTHORITY_GUARD_KEYS},
            "items": [
                {"fixture_id": "local-only-example-stub-note-001", "kind": "note", "path": runner.NOTE_REF},
                {"fixture_id": "local-only-example-stub-input-001", "kind": "input", "path": runner.INPUT_REF},
                {"fixture_id": "local-only-example-stub-expected-output-001", "kind": "expected_output", "path": runner.ORACLE_REF},
            ],
        })
        _write(self.root / runner.VALIDATOR_REF, {
            "validator_id": runner.VALIDATOR_ID,
            "scenario_id": runner.SCENARIO_ID,
            "status": "active",
            "reads": {
                "scenario_ref": runner.SCENARIO_REF,
                "fixture_pack_ref": runner.FIXTURE_PACK_REF,
                "allowed_kinds": ["note", "input", "expected_output"],
            },
            "guards": {
                "owner_repo_mutation": False,
                "deploy_mutation": False,
                "secret_use": False,
                "live_data_mutation": False,
                "_stack_execution": False,
            },
        })
        note_path = self.root / runner.NOTE_REF
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("Fixture note for the deterministic local-only validator.\n", encoding="utf-8")
        _write(self.root / runner.INPUT_REF, {
            "fixture_id": "local-only-example-stub-input-001",
            "scenario_id": runner.SCENARIO_ID,
            "payload": {
                "mode": "stub",
                "constraints": list(runner.REQUIRED_CONSTRAINTS),
            },
        })
        _write(self.root / runner.ORACLE_REF, {
            "fixture_id": "local-only-example-stub-expected-output-001",
            "scenario_id": runner.SCENARIO_ID,
            "payload": {
                "mode": "local_only",
                "status": "validated",
                "observations": [
                    "local-only sandbox input accepted",
                    "all no-mutation constraints preserved",
                ],
            },
        })
        runner_path = self.root / runner.RUNNER_REF
        runner_path.parent.mkdir(parents=True, exist_ok=True)
        runner_path.write_text(Path(runner.__file__).read_text(encoding="utf-8"), encoding="utf-8")

    def test_writes_source_bound_terminal_pair(self) -> None:
        report = runner.run_sandbox_validator(root=self.root, run_id="proof-run-001")

        self.assertEqual("passed", report["result"]["status"])
        self.assertEqual("equal_on_boundary", report["comparison_outcome"])
        self.assertEqual([], report["authority_actions"])
        self.assertTrue(all(value is False for value in report["guards"].values()))
        self.assertRegex(report["receipt_id"], r"^asv_[0-9a-f]{24}$")
        self.assertRegex(report["source_digests"]["runner"], r"^sha256:[0-9a-f]{64}$")
        validation_dir = self.root / runner.RUNTIME_PREFIX / "proof-run-001" / "validation"
        self.assertTrue((validation_dir / "report.json").is_file())
        self.assertTrue((validation_dir / "candidate-output.json").is_file())

    def test_same_run_is_idempotent(self) -> None:
        first = runner.run_sandbox_validator(root=self.root, run_id="proof-run-001")
        second = runner.run_sandbox_validator(root=self.root, run_id="proof-run-001")
        self.assertEqual(first, second)

    def test_oracle_mismatch_finishes_failed_without_authority(self) -> None:
        oracle = json.loads((self.root / runner.ORACLE_REF).read_text(encoding="utf-8"))
        oracle["payload"]["status"] = "different"
        _write(self.root / runner.ORACLE_REF, oracle)

        report = runner.run_sandbox_validator(root=self.root, run_id="proof-run-002")

        self.assertEqual("failed", report["result"]["status"])
        self.assertEqual("unequal_on_boundary", report["comparison_outcome"])
        self.assertEqual([], report["authority_actions"])

    def test_rejects_guard_drift(self) -> None:
        descriptor = json.loads((self.root / runner.VALIDATOR_REF).read_text(encoding="utf-8"))
        descriptor["guards"]["owner_repo_mutation"] = True
        _write(self.root / runner.VALIDATOR_REF, descriptor)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "validator_guard_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-003")

    def test_rejects_scenario_guard_drift(self) -> None:
        scenario = json.loads((self.root / runner.SCENARIO_REF).read_text(encoding="utf-8"))
        scenario["guards"]["owner_repo_mutation"] = True
        _write(self.root / runner.SCENARIO_REF, scenario)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "scenario_guard_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-012")

    def test_rejects_missing_scenario_guard(self) -> None:
        scenario = json.loads((self.root / runner.SCENARIO_REF).read_text(encoding="utf-8"))
        del scenario["guards"]["secret_use"]
        _write(self.root / runner.SCENARIO_REF, scenario)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "scenario_guard_shape_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-013")

    def test_rejects_fixture_pack_guard_drift(self) -> None:
        pack = json.loads((self.root / runner.FIXTURE_PACK_REF).read_text(encoding="utf-8"))
        pack["guards"]["owner_repo_mutation"] = True
        _write(self.root / runner.FIXTURE_PACK_REF, pack)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "fixture_pack_guard_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-014")

    def test_rejects_non_object_fixture_pack_member(self) -> None:
        pack = json.loads((self.root / runner.FIXTURE_PACK_REF).read_text(encoding="utf-8"))
        pack["items"].append("unexpected")
        _write(self.root / runner.FIXTURE_PACK_REF, pack)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "fixture_pack_member_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-016")

    def test_rejects_input_fixture_identity_drift(self) -> None:
        fixture = json.loads((self.root / runner.INPUT_REF).read_text(encoding="utf-8"))
        fixture["fixture_id"] = "wrong-input"
        _write(self.root / runner.INPUT_REF, fixture)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "input_fixture_identity_mismatch"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-017")

    def test_rejects_oracle_fixture_identity_drift(self) -> None:
        fixture = json.loads((self.root / runner.ORACLE_REF).read_text(encoding="utf-8"))
        fixture["fixture_id"] = "wrong-oracle"
        _write(self.root / runner.ORACLE_REF, fixture)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "oracle_fixture_identity_mismatch"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-018")

    def test_rejects_missing_fixture_pack_guard(self) -> None:
        pack = json.loads((self.root / runner.FIXTURE_PACK_REF).read_text(encoding="utf-8"))
        del pack["guards"]["secret_use"]
        _write(self.root / runner.FIXTURE_PACK_REF, pack)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "fixture_pack_guard_shape_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-015")

    def test_rejects_inactive_validator(self) -> None:
        descriptor = json.loads((self.root / runner.VALIDATOR_REF).read_text(encoding="utf-8"))
        descriptor["status"] = "draft"
        _write(self.root / runner.VALIDATOR_REF, descriptor)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "validator_not_active"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-004")

    def test_rejects_constraint_drift(self) -> None:
        input_fixture = json.loads((self.root / runner.INPUT_REF).read_text(encoding="utf-8"))
        input_fixture["payload"]["constraints"] = ["no owner-repo mutation"]
        _write(self.root / runner.INPUT_REF, input_fixture)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "input_constraint_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-005")

    def test_rejects_missing_scenario(self) -> None:
        (self.root / runner.SCENARIO_REF).unlink()
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "missing_source"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-007")

    def test_rejects_draft_scenario(self) -> None:
        scenario = json.loads((self.root / runner.SCENARIO_REF).read_text(encoding="utf-8"))
        scenario["status"] = "draft"
        _write(self.root / runner.SCENARIO_REF, scenario)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "scenario_not_active"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-008")

    def test_rejects_fixture_member_drift(self) -> None:
        pack = json.loads((self.root / runner.FIXTURE_PACK_REF).read_text(encoding="utf-8"))
        pack["items"] = pack["items"][:-1]
        _write(self.root / runner.FIXTURE_PACK_REF, pack)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "fixture_pack_member_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-009")

    def test_rejects_validator_read_graph_drift(self) -> None:
        descriptor = json.loads((self.root / runner.VALIDATOR_REF).read_text(encoding="utf-8"))
        descriptor["reads"]["fixture_pack_ref"] = "data/other.json"
        _write(self.root / runner.VALIDATOR_REF, descriptor)
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "validator_read_graph_drift"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-010")

    def test_rejects_stale_note(self) -> None:
        (self.root / runner.NOTE_REF).write_text("No runtime exists.\n", encoding="utf-8")
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "fixture_note_stale"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-011")

    def test_rejects_unsafe_run_id(self) -> None:
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "invalid_run_id"):
            runner.run_sandbox_validator(root=self.root, run_id="../escape")

    def test_existing_artifact_conflict_fails_closed(self) -> None:
        runner.run_sandbox_validator(root=self.root, run_id="proof-run-006")
        report_path = self.root / runner.RUNTIME_PREFIX / "proof-run-006" / "validation" / "report.json"
        report_path.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(runner.SandboxValidatorRunError, "existing_artifact_conflict"):
            runner.run_sandbox_validator(root=self.root, run_id="proof-run-006")


if __name__ == "__main__":
    unittest.main()
