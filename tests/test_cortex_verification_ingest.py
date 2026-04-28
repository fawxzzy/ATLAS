from __future__ import annotations

import unittest

from ops.cortex.proof_receipt import ProofReceiptDraftBuilder, ProofReceiptDraftInput
from ops.cortex.verification_ingest import (
    KNOWN_STACK_VALIDATION_BASELINE,
    VerificationDebtCounts,
    VerificationOutcome,
    ingest_verification_outcome,
)


def _outcome(
    *,
    command: str,
    exit_code: int,
    owner_layer: str,
    touched_files: tuple[str, ...] = (),
    stdout_summary: str | None = None,
    stderr_summary: str | None = None,
    observed_debt: VerificationDebtCounts | None = None,
    expected_ambient_debt: VerificationDebtCounts | None = None,
    current_tranche_failure: bool = False,
    failures: tuple[str, ...] = (),
    proof_id: str | None = None,
) -> VerificationOutcome:
    return VerificationOutcome(
        command=command,
        exit_code=exit_code,
        owner_layer=owner_layer,
        touched_files=touched_files,
        stdout_summary=stdout_summary,
        stderr_summary=stderr_summary,
        observed_debt=observed_debt,
        expected_ambient_debt=expected_ambient_debt,
        current_tranche_failure=current_tranche_failure,
        failures=failures,
        next_required_layer="cortex",
        proof_id=proof_id,
    )


class CortexVerificationIngestTests(unittest.TestCase):
    def test_clean_targeted_unittest_command_ingests_as_passed(self) -> None:
        result = ingest_verification_outcome(
            _outcome(
                command="python -m unittest tests.test_cortex_kernel",
                exit_code=0,
                owner_layer="cortex",
                touched_files=("ops/cortex/kernel.py", "tests/test_cortex_kernel.py"),
                stdout_summary="Cortex kernel tests passed.",
                proof_id="cortex-kernel-clean",
            )
        )

        self.assertEqual("targeted_passed", result.classification)
        self.assertFalse(result.current_tranche_failure)
        self.assertEqual("passed", result.proof_summary.verification.status)
        self.assertEqual(("Cortex kernel tests passed.",), result.proof_summary.verification.passed)
        self.assertEqual((), result.proof_summary.verification.failed)
        self.assertTrue(result.proof_summary.receipt_ready)

    def test_clean_npm_verify_command_ingests_as_passed(self) -> None:
        result = ingest_verification_outcome(
            _outcome(
                command="npm run verify",
                exit_code=0,
                owner_layer="fitness",
                touched_files=("repos/fitness/package.json",),
                stdout_summary="npm verify completed cleanly.",
            )
        )

        self.assertEqual("targeted_passed", result.classification)
        self.assertEqual("passed", result.proof_summary.verification.status)
        self.assertTrue(result.proof_summary.receipt_ready)
        self.assertIn("npm run verify", result.proof_summary.command)

    def test_failed_targeted_command_ingests_as_current_tranche_failure(self) -> None:
        result = ingest_verification_outcome(
            _outcome(
                command="python -m unittest tests.test_cortex_kernel",
                exit_code=1,
                owner_layer="cortex",
                stderr_summary="1 test failed.",
                failures=("tests.test_cortex_kernel.CortexKernelTests.test_proof_example_round_trip_keeps_flattened_shape",),
            )
        )

        self.assertEqual("targeted_failed", result.classification)
        self.assertTrue(result.current_tranche_failure)
        self.assertEqual("failed", result.proof_summary.verification.status)
        self.assertEqual((), result.proof_summary.verification.passed)
        self.assertEqual(
            ("tests.test_cortex_kernel.CortexKernelTests.test_proof_example_round_trip_keeps_flattened_shape",),
            result.proof_summary.verification.failed,
        )
        self.assertFalse(result.proof_summary.receipt_ready)

    def test_stack_validation_nonzero_with_known_ambient_baseline_is_classified_as_ambient_debt(self) -> None:
        result = ingest_verification_outcome(
            _outcome(
                command="python .\\ops\\validation\\validate_stack.py",
                exit_code=2,
                owner_layer="stack",
                observed_debt=KNOWN_STACK_VALIDATION_BASELINE,
                stdout_summary="Stack validation completed against stack.yaml.",
                proof_id="stack-validation-known-ambient",
            )
        )

        self.assertEqual("stack_validation_known_ambient_debt", result.classification)
        self.assertFalse(result.current_tranche_failure)
        self.assertEqual("completed_with_known_debt", result.proof_summary.verification.status)
        self.assertEqual((), result.proof_summary.verification.failed)
        self.assertEqual(result.ambient_debt, result.proof_summary.verification.known_debt)
        self.assertEqual((), result.current_validation_debt)
        self.assertFalse(result.proof_summary.receipt_ready)
        self.assertIn("critical=345", result.ambient_debt[0])

    def test_stack_validation_changed_debt_is_not_treated_as_ambient(self) -> None:
        result = ingest_verification_outcome(
            _outcome(
                command="python .\\ops\\validation\\validate_stack.py",
                exit_code=2,
                owner_layer="stack",
                observed_debt=VerificationDebtCounts(critical=346, error=14, warning=181),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
                proof_id="stack-validation-changed-debt",
            )
        )

        self.assertEqual("stack_validation_changed_debt", result.classification)
        self.assertFalse(result.current_tranche_failure)
        self.assertEqual("completed_with_changed_debt", result.proof_summary.verification.status)
        self.assertEqual((), result.ambient_debt)
        self.assertEqual(result.current_validation_debt, result.proof_summary.verification.known_debt)
        self.assertIn("expected critical=345", result.current_validation_debt[0])
        self.assertIn("observed critical=346", result.current_validation_debt[0])

    def test_stack_validation_warning_only_drift_stays_in_current_validation_debt(self) -> None:
        result = ingest_verification_outcome(
            _outcome(
                command="python .\\ops\\validation\\validate_stack.py",
                exit_code=2,
                owner_layer="stack",
                observed_debt=VerificationDebtCounts(critical=345, error=14, warning=183),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
                proof_id="stack-validation-warning-drift",
            )
        )

        self.assertEqual("stack_validation_changed_debt", result.classification)
        self.assertFalse(result.current_tranche_failure)
        self.assertEqual("completed_with_changed_debt", result.proof_summary.verification.status)
        self.assertEqual((), result.ambient_debt)
        self.assertEqual(result.current_validation_debt, result.proof_summary.verification.known_debt)
        self.assertIn("expected critical=345, error=14, warning=181", result.current_validation_debt[0])
        self.assertIn("observed critical=345, error=14, warning=183", result.current_validation_debt[0])

    def test_malformed_verification_outcome_fails_clearly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected non-empty string for command"):
            ingest_verification_outcome(
                {
                    "command": "",
                    "exit_code": 0,
                    "owner_layer": "cortex",
                }
            )

        with self.assertRaisesRegex(ValueError, "Expected object for observed_debt"):
            ingest_verification_outcome(
                {
                    "command": "python .\\ops\\validation\\validate_stack.py",
                    "exit_code": 2,
                    "owner_layer": "stack",
                    "observed_debt": ["critical", 345],
                }
            )

    def test_output_feeds_proof_receipt_builder_without_changing_ambient_or_current_debt_semantics(self) -> None:
        ambient_result = ingest_verification_outcome(
            _outcome(
                command="python .\\ops\\validation\\validate_stack.py",
                exit_code=2,
                owner_layer="stack",
                touched_files=("stack.yaml", "ops/validation/validate_stack.py"),
                observed_debt=KNOWN_STACK_VALIDATION_BASELINE,
                proof_id="stack-validation-ambient",
            )
        )
        changed_result = ingest_verification_outcome(
            _outcome(
                command="python .\\ops\\validation\\validate_stack.py",
                exit_code=2,
                owner_layer="stack",
                touched_files=("stack.yaml", "ops/validation/validate_stack.py"),
                observed_debt=VerificationDebtCounts(critical=345, error=15, warning=181),
                proof_id="stack-validation-changed",
            )
        )

        builder = ProofReceiptDraftBuilder()
        ambient_draft = builder.build(
            ProofReceiptDraftInput(
                proof_summary=ambient_result.proof_summary,
                touched_files=ambient_result.proof_summary.touched_files,
                owner_layer=ambient_result.proof_summary.owner_layer,
                next_required_layer=ambient_result.proof_summary.next_required_layer,
                known_debt_summary=ambient_result.to_known_debt_summary(owner_boundary_status="clean"),
            )
        )
        changed_draft = builder.build(
            ProofReceiptDraftInput(
                proof_summary=changed_result.proof_summary,
                touched_files=changed_result.proof_summary.touched_files,
                owner_layer=changed_result.proof_summary.owner_layer,
                next_required_layer=changed_result.proof_summary.next_required_layer,
                known_debt_summary=changed_result.to_known_debt_summary(owner_boundary_status="clean"),
            )
        )

        self.assertEqual(list(ambient_result.ambient_debt), ambient_draft.to_payload()["known_debt"]["ambient_debt"])
        self.assertEqual([], ambient_draft.to_payload()["known_debt"]["current_validation_debt"])
        self.assertEqual([], changed_draft.to_payload()["known_debt"]["ambient_debt"])
        self.assertEqual(
            list(changed_result.current_validation_debt),
            changed_draft.to_payload()["known_debt"]["current_validation_debt"],
        )


if __name__ == "__main__":
    unittest.main()
