from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.feedback_artifact import write_feedback_artifact
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.receipt_handoff import write_receipt_handoff
from ops.cortex.receipt_handoff_review import review_receipt_handoff
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
        command="python -m unittest tests.test_cortex_receipt_handoff_review",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=(
            "ops/cortex/receipt_handoff_review.py",
            "tests/test_cortex_receipt_handoff_review.py",
        ),
        stdout_summary="Receipt handoff review tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="receipt-handoff-review-targeted",
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
        proof_id="receipt-handoff-review-stack",
    )


class CortexReceiptHandoffReviewTests(unittest.TestCase):
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

    def _classify_feedback(
        self,
        root: Path,
        *,
        targeted: VerificationOutcome | None = None,
        stack: VerificationOutcome | None = None,
    ):
        outcomes = [targeted or _targeted_outcome()]
        if stack is not None:
            outcomes.append(stack)
        return classify_feedback(CortexFeedbackInput(root=root, verification_outcomes=tuple(outcomes)))

    def test_marks_clean_handoff_as_human_review_ready_and_lifeline_candidate(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        write_feedback_artifact(result, root=root)
        artifact = write_receipt_handoff(root=root)

        decision = review_receipt_handoff(artifact.latest_artifact_path, root=root)

        self.assertTrue(decision.handoff_valid)
        self.assertTrue(decision.human_review_ready)
        self.assertTrue(decision.lifeline_candidate)
        self.assertFalse(decision.auto_approved)
        self.assertFalse(decision.blocked)
        self.assertIsNone(decision.blocked_reason)
        self.assertIn("never auto-approved", decision.required_reviewer_action)

    def test_keeps_blocked_handoff_reviewable_without_making_it_a_lifeline_candidate(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(
            root,
            targeted=_targeted_outcome(
                exit_code=1,
                failures=(
                    "tests.test_cortex_receipt_handoff_review.CortexReceiptHandoffReviewTests.test_keeps_blocked_handoff_reviewable_without_making_it_a_lifeline_candidate",
                ),
                stderr_summary="1 receipt handoff review test failed.",
            ),
        )
        write_feedback_artifact(result, root=root)
        artifact = write_receipt_handoff(root=root)

        decision = review_receipt_handoff(artifact.latest_artifact_path, root=root)

        self.assertTrue(decision.handoff_valid)
        self.assertTrue(decision.human_review_ready)
        self.assertFalse(decision.lifeline_candidate)
        self.assertFalse(decision.auto_approved)
        self.assertTrue(decision.blocked)
        self.assertIn("test_keeps_blocked_handoff_reviewable", decision.blocked_reason or "")
        self.assertIn("must not be treated as approval", decision.required_reviewer_action)

    def test_current_validation_debt_blocks_lifeline_candidacy(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(
            root,
            stack=_stack_outcome(
                exit_code=2,
                observed_debt=VerificationDebtCounts(critical=346, error=14, warning=181),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
            ),
        )
        write_feedback_artifact(result, root=root)
        artifact = write_receipt_handoff(root=root)

        decision = review_receipt_handoff(artifact.latest_artifact_path, root=root)

        self.assertTrue(decision.handoff_valid)
        self.assertTrue(decision.human_review_ready)
        self.assertFalse(decision.lifeline_candidate)
        self.assertTrue(decision.blocked)
        self.assertIn("observed critical=346", decision.blocked_reason or "")

    def test_missing_required_field_fails_clearly(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "receipt-drafts" / "latest.json"
        _write_json(
            artifact_path,
            {
                "run_id": "run-001",
                "receipt_title": "",
                "owner_layer": "cortex",
                "selected_next_action": "review",
                "next_required_layer": "cortex",
                "tranche_complete": True,
                "receipt_ready": True,
                "blocked": False,
                "blocked_reason": None,
                "known_ambient_debt": [],
                "current_validation_debt": [],
                "applied_rules": {},
                "failure_modes_avoided": [],
                "reviewer_action_required": "Human review is required.",
            },
        )

        with self.assertRaisesRegex(
            ValueError,
            "Malformed Cortex receipt handoff draft at .*Expected non-empty string for receipt_title",
        ):
            review_receipt_handoff(artifact_path, root=root)

    def test_internally_inconsistent_handoff_is_invalid(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        write_feedback_artifact(result, root=root)
        artifact = write_receipt_handoff(root=root)
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))
        payload["current_validation_debt"] = ["observed critical=346, expected critical=345"]
        payload["blocked"] = False
        payload["blocked_reason"] = None
        _write_json(artifact.latest_artifact_path, payload)

        decision = review_receipt_handoff(artifact.latest_artifact_path, root=root)

        self.assertFalse(decision.handoff_valid)
        self.assertFalse(decision.human_review_ready)
        self.assertFalse(decision.lifeline_candidate)
        self.assertFalse(decision.auto_approved)
        self.assertTrue(decision.blocked)
        self.assertEqual(
            "blocked must be true when current_validation_debt is present.",
            decision.blocked_reason,
        )
        self.assertIn("Fix the Cortex handoff contract before review", decision.required_reviewer_action)

    def test_review_decision_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        write_feedback_artifact(result, root=root)
        artifact = write_receipt_handoff(root=root)

        decision = review_receipt_handoff(artifact.latest_artifact_path, root=root)

        json.dumps(decision.to_payload(), sort_keys=True)


if __name__ == "__main__":
    unittest.main()
