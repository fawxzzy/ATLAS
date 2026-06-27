from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from ops.atlas.sandbox_validator_behavior import evaluate_sandbox_validator_behavior

VALIDATOR_REF = "data/atlas/sandbox/validators/local-only-example-stub/validator.json"
REPORT_REF = (
    "runtime/atlas/sandbox/runs/local-only-example-stub/local-only-example-run-001/validation/report.json"
)
CANDIDATE_OUTPUT_REF = (
    "runtime/atlas/sandbox/runs/local-only-example-stub/local-only-example-run-001/validation/candidate-output.json"
)
ORACLE_REF = (
    "data/atlas/sandbox/fixtures/local-only-example-stub/expected-output/first-expected-output-stub.json"
)


def _read_json(path_ref: str) -> dict[str, Any]:
    return json.loads(Path(path_ref).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return str(path)


def _materialize_temp_validation_pair(
    *,
    report_override: dict[str, Any] | None = None,
    candidate_override: dict[str, Any] | None = None,
    oracle_override: dict[str, Any] | None = None,
) -> tuple[str, str, str]:
    tempdir = Path(tempfile.mkdtemp(prefix="atlas-sandbox-validator-"))

    report_payload = _read_json(REPORT_REF)
    candidate_payload = _read_json(CANDIDATE_OUTPUT_REF)
    oracle_payload = _read_json(ORACLE_REF)

    if report_override:
        report_payload.update(report_override)
    if candidate_override:
        candidate_payload.update(candidate_override)
    if oracle_override:
        oracle_payload.update(oracle_override)

    oracle_path = _write_json(tempdir / "expected-output.json", oracle_payload)
    candidate_payload["oracle_ref"] = oracle_path
    candidate_path = _write_json(tempdir / "candidate-output.json", candidate_payload)
    report_path = _write_json(tempdir / "report.json", report_payload)
    return report_path, candidate_path, oracle_path


class SandboxValidatorBehaviorTests(unittest.TestCase):
    def test_current_admitted_stub_pair_is_equal_on_boundary(self) -> None:
        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            REPORT_REF,
            CANDIDATE_OUTPUT_REF,
            ORACLE_REF,
        )

        self.assertEqual("equal_on_boundary", payload["comparison_outcome"])
        self.assertEqual([], payload["comparison_reasons"])
        self.assertEqual("not_run", payload["report_status"])
        self.assertEqual(
            [
                "payload.mode",
                "payload.status",
                "payload.observations",
            ],
            payload["compared_fields"],
        )

    def test_unequal_payload_is_preserved_as_unequal_on_boundary(self) -> None:
        report_ref, candidate_ref, oracle_ref = _materialize_temp_validation_pair(
            candidate_override={
                "payload": {
                    "mode": "stub",
                    "status": "changed",
                    "observations": [
                        "example output shape recorded",
                        "no validator evaluation has run",
                    ],
                }
            }
        )

        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            report_ref,
            candidate_ref,
            oracle_ref,
        )

        self.assertEqual("unequal_on_boundary", payload["comparison_outcome"])
        self.assertEqual([], payload["comparison_reasons"])

    def test_non_not_run_report_status_is_not_admissible(self) -> None:
        report_ref, candidate_ref, oracle_ref = _materialize_temp_validation_pair(
            report_override={
                "result": {
                    "status": "match",
                    "summary": "Synthetic status drift.",
                }
            }
        )

        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            report_ref,
            candidate_ref,
            oracle_ref,
        )

        self.assertEqual("not_admissible", payload["comparison_outcome"])
        self.assertEqual(["report_status_not_not_run"], payload["comparison_reasons"])

    def test_identity_mismatch_is_not_admissible(self) -> None:
        report_ref, candidate_ref, oracle_ref = _materialize_temp_validation_pair(
            candidate_override={"scenario_id": "other-scenario"}
        )

        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            report_ref,
            candidate_ref,
            oracle_ref,
        )

        self.assertEqual("not_admissible", payload["comparison_outcome"])
        self.assertEqual(["identity_mismatch"], payload["comparison_reasons"])

    def test_missing_boundary_field_is_not_admissible(self) -> None:
        report_ref, candidate_ref, oracle_ref = _materialize_temp_validation_pair(
            candidate_override={
                "payload": {
                    "mode": "stub",
                    "observations": [
                        "example output shape recorded",
                        "no validator evaluation has run",
                    ],
                }
            }
        )

        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            report_ref,
            candidate_ref,
            oracle_ref,
        )

        self.assertEqual("not_admissible", payload["comparison_outcome"])
        self.assertEqual(["missing_boundary_field"], payload["comparison_reasons"])

    def test_oracle_ref_mismatch_is_not_admissible(self) -> None:
        report_ref, candidate_ref, oracle_ref = _materialize_temp_validation_pair()
        candidate_payload = _read_json(candidate_ref)
        candidate_payload["oracle_ref"] = ORACLE_REF
        Path(candidate_ref).write_text(json.dumps(candidate_payload, indent=2) + "\n", encoding="utf-8")

        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            report_ref,
            candidate_ref,
            oracle_ref,
        )

        self.assertEqual("not_admissible", payload["comparison_outcome"])
        self.assertEqual(["oracle_ref_mismatch"], payload["comparison_reasons"])

    def test_no_verdict_and_no_mutation_boundary_is_preserved(self) -> None:
        report_before = Path(REPORT_REF).read_text(encoding="utf-8")
        candidate_before = Path(CANDIDATE_OUTPUT_REF).read_text(encoding="utf-8")

        payload = evaluate_sandbox_validator_behavior(
            VALIDATOR_REF,
            REPORT_REF,
            CANDIDATE_OUTPUT_REF,
            ORACLE_REF,
        )

        self.assertNotIn(payload["comparison_outcome"], {"match", "mismatch", "blocked"})
        self.assertEqual(report_before, Path(REPORT_REF).read_text(encoding="utf-8"))
        self.assertEqual(candidate_before, Path(CANDIDATE_OUTPUT_REF).read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "validator_ref",
                "report_ref",
                "candidate_output_ref",
                "oracle_ref",
                "report_status",
                "compared_fields",
                "comparison_outcome",
                "comparison_reasons",
            },
            set(payload),
        )


if __name__ == "__main__":
    unittest.main()
