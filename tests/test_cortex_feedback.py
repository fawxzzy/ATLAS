from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.verification_ingest import KNOWN_STACK_VALIDATION_BASELINE, VerificationDebtCounts, VerificationOutcome


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _targeted_outcome(
    *,
    exit_code: int = 0,
    failures: tuple[str, ...] = (),
    stderr_summary: str | None = None,
) -> VerificationOutcome:
    return VerificationOutcome(
        command="python -m unittest tests.test_cortex_feedback",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=("ops/cortex/feedback.py", "tests/test_cortex_feedback.py"),
        stdout_summary="Feedback tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="feedback-targeted",
    )


def _stack_outcome(
    *,
    exit_code: int = 0,
    observed_debt: VerificationDebtCounts | None = None,
    expected_ambient_debt: VerificationDebtCounts | None = None,
) -> VerificationOutcome:
    return VerificationOutcome(
        command="python .\\ops\\validation\\validate_stack.py",
        exit_code=exit_code,
        owner_layer="stack",
        touched_files=("stack.yaml", "ops/validation/validate_stack.py"),
        observed_debt=observed_debt,
        expected_ambient_debt=expected_ambient_debt,
        stdout_summary="Stack validation completed.",
        next_required_layer="cortex",
        proof_id="feedback-stack",
    )


class CortexFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.base_payload = load_and_run_cortex_loop(root=cls.root).to_payload()

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _seed_run(self, root: Path, payload: dict | None = None, *, name: str = "cortex-run-result.latest.json") -> None:
        artifact_path = root / "runtime" / "cortex" / "runs" / name
        _write_json(artifact_path, payload or self.base_payload)

    def test_successful_run_and_targeted_verification_produce_tranche_complete(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(
                root=root,
                verification_outcomes=(
                    _targeted_outcome(),
                    _stack_outcome(exit_code=0, observed_debt=VerificationDebtCounts()),
                ),
            )
        )

        self.assertTrue(result.targeted_verification_passed)
        self.assertEqual("passed", result.stack_validation_status)
        self.assertTrue(result.receipt_ready)
        self.assertTrue(result.tranche_complete)
        self.assertFalse(result.blocked)
        self.assertIsNone(result.blocked_reason)

    def test_failed_targeted_command_blocks_completion(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(
                root=root,
                verification_outcomes=(
                    _targeted_outcome(
                        exit_code=1,
                        failures=("tests.test_cortex_feedback.CortexFeedbackTests.test_failed_targeted_command_blocks_completion",),
                        stderr_summary="1 feedback test failed.",
                    ),
                ),
            )
        )

        self.assertFalse(result.targeted_verification_passed)
        self.assertFalse(result.receipt_ready)
        self.assertFalse(result.tranche_complete)
        self.assertTrue(result.blocked)
        self.assertIn("test_failed_targeted_command_blocks_completion", result.blocked_reason or "")

    def test_known_ambient_stack_debt_does_not_block_current_tranche_completion(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(
                root=root,
                verification_outcomes=(
                    _targeted_outcome(),
                    _stack_outcome(exit_code=2, observed_debt=KNOWN_STACK_VALIDATION_BASELINE),
                ),
            )
        )

        self.assertTrue(result.targeted_verification_passed)
        self.assertEqual("known_ambient_debt", result.stack_validation_status)
        self.assertTrue(result.receipt_ready)
        self.assertTrue(result.tranche_complete)
        self.assertFalse(result.blocked)
        self.assertEqual((), result.current_validation_debt)
        self.assertTrue(any("critical=345" in item for item in result.known_ambient_debt))

    def test_changed_stack_validation_debt_blocks_readiness(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(
                root=root,
                verification_outcomes=(
                    _targeted_outcome(),
                    _stack_outcome(
                        exit_code=2,
                        observed_debt=VerificationDebtCounts(critical=346, error=14, warning=181),
                        expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
                    ),
                ),
            )
        )

        self.assertEqual("changed_debt", result.stack_validation_status)
        self.assertFalse(result.receipt_ready)
        self.assertFalse(result.tranche_complete)
        self.assertTrue(result.blocked)
        self.assertIn("observed critical=346", result.blocked_reason or "")
        self.assertEqual(result.current_validation_debt, result.receipt_draft.known_debt.current_validation_debt)

    def test_feedback_result_carries_receipt_draft_fields(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(root=root, verification_outcomes=(_targeted_outcome(),))
        )

        self.assertEqual("cortex", result.receipt_draft.owner_layer)
        self.assertEqual("cortex", result.receipt_draft.next_required_layer)
        self.assertTrue(result.receipt_draft.passed_commands)
        self.assertTrue(result.receipt_draft.receipt_title.startswith("Cortex proof receipt draft"))

    def test_feedback_result_carries_ledger_summary_fields(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(
                root=root,
                verification_outcomes=(
                    _targeted_outcome(),
                    _stack_outcome(exit_code=2, observed_debt=KNOWN_STACK_VALIDATION_BASELINE),
                ),
            )
        )

        self.assertEqual("cortex-run-result.latest", result.ledger_summary.latest_run_id)
        self.assertEqual("runtime/cortex/runs/cortex-run-result.latest.json", result.ledger_summary.latest_run_path)
        self.assertEqual("completed_with_known_debt", result.ledger_summary.proof_status)
        self.assertFalse(result.ledger_summary.receipt_ready)

    def test_feedback_result_carries_applied_rules_and_failure_modes_avoided(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(root=root, verification_outcomes=(_targeted_outcome(),))
        )

        self.assertTrue(result.applied_rules.rule_ids)
        self.assertTrue(result.applied_rules.pattern_ids)
        self.assertTrue(result.applied_rules.failure_mode_ids)
        self.assertTrue(result.failure_modes_avoided)

    def test_malformed_run_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        payload = copy.deepcopy(self.base_payload)
        del payload["selected_next_action"]
        self._seed_run(root, payload)

        with self.assertRaisesRegex(ValueError, "Expected object for selected_next_action"):
            classify_feedback(CortexFeedbackInput(root=root, verification_outcomes=(_targeted_outcome(),)))

    def test_malformed_verification_outcome_fails_clearly(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        with self.assertRaisesRegex(ValueError, "Expected non-empty string for command"):
            classify_feedback(
                {
                    "root": str(root),
                    "verification_outcomes": [
                        {
                            "command": "",
                            "exit_code": 0,
                            "owner_layer": "cortex",
                            "next_required_layer": "cortex",
                        }
                    ],
                }
            )

    def test_feedback_result_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(root=root, verification_outcomes=(_targeted_outcome(),))
        )

        json.dumps(result.to_payload(), sort_keys=True)

    def test_feedback_loop_does_not_require_connectors_or_lifeline(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        result = classify_feedback(
            CortexFeedbackInput(root=root, verification_outcomes=(_targeted_outcome(),))
        )

        self.assertEqual("cortex", result.owner_layer)
        self.assertEqual("cortex", result.next_required_layer)
        self.assertEqual("not_run", result.stack_validation_status)
        self.assertTrue(result.receipt_ready)


if __name__ == "__main__":
    unittest.main()
