from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.feedback_artifact import write_feedback_artifact
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.receipt_handoff import (
    build_receipt_handoff,
    default_receipt_handoff_run_json_path,
    default_receipt_handoff_run_summary_path,
    render_receipt_handoff_summary,
    write_receipt_handoff,
)
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
        command="python -m unittest tests.test_cortex_receipt_handoff",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=("ops/cortex/receipt_handoff.py", "tests/test_cortex_receipt_handoff.py"),
        stdout_summary="Receipt handoff tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="receipt-handoff-targeted",
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
        proof_id="receipt-handoff-stack",
    )


class CortexReceiptHandoffTests(unittest.TestCase):
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

    def test_builds_receipt_handoff_from_receipt_ready_feedback_artifact(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        feedback_artifact = write_feedback_artifact(result, root=root)

        draft = build_receipt_handoff(feedback_artifact.latest_artifact_path, root=root)

        self.assertEqual(result.run_id, draft.run_id)
        self.assertEqual("cortex", draft.owner_layer)
        self.assertEqual(result.selected_next_action, draft.selected_next_action)
        self.assertTrue(draft.receipt_ready)
        self.assertFalse(draft.blocked)
        self.assertEqual("review_ready", draft.review_status)
        self.assertIn("Human review is required", draft.reviewer_action_required)
        self.assertIn("not auto-approved", draft.reviewer_action_required)

    def test_builds_blocked_handoff_from_blocked_feedback_artifact(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(
            root,
            targeted=_targeted_outcome(
                exit_code=1,
                failures=("tests.test_cortex_receipt_handoff.CortexReceiptHandoffTests.test_builds_blocked_handoff_from_blocked_feedback_artifact",),
                stderr_summary="1 receipt handoff test failed.",
            ),
        )
        feedback_artifact = write_feedback_artifact(result, root=root)

        draft = build_receipt_handoff(feedback_artifact.latest_artifact_path, root=root)

        self.assertFalse(draft.receipt_ready)
        self.assertTrue(draft.blocked)
        self.assertEqual("blocked", draft.review_status)
        self.assertIn("test_builds_blocked_handoff_from_blocked_feedback_artifact", draft.blocked_reason or "")
        self.assertIn("must not be treated as approval", draft.reviewer_action_required)

    def test_writes_latest_json_and_latest_text(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        write_feedback_artifact(result, root=root)

        artifact = write_receipt_handoff(root=root)
        summary = artifact.latest_summary_path.read_text(encoding="utf-8") if artifact.latest_summary_path is not None else ""

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertTrue(artifact.latest_summary_path.exists() if artifact.latest_summary_path is not None else False)
        self.assertEqual("latest.json", artifact.latest_artifact_path.name)
        self.assertEqual("latest.txt", artifact.latest_summary_path.name if artifact.latest_summary_path is not None else "")
        self.assertIn("Cortex Receipt Handoff Draft", summary)
        self.assertIn("Reviewer action required:", summary)

    def test_writes_run_specific_json_and_text_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        write_feedback_artifact(result, root=root)

        artifact = write_receipt_handoff(root=root)

        self.assertEqual(default_receipt_handoff_run_json_path(result.run_id, root), artifact.run_artifact_path)
        self.assertEqual(default_receipt_handoff_run_summary_path(result.run_id, root), artifact.run_summary_path)
        self.assertEqual(
            "runtime/cortex/receipt-drafts/runs/cortex-run-result.latest.json",
            artifact.to_payload(root=root)["run_artifact_path"],
        )

    def test_preserves_ambient_debt_separately_from_changed_validation_debt(self) -> None:
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
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(list(result.known_ambient_debt), payload["known_ambient_debt"])
        self.assertTrue(any("observed critical=346" in item for item in payload["current_validation_debt"]))
        self.assertFalse(any("observed critical=346" in item for item in payload["known_ambient_debt"]))

    def test_includes_reviewer_action_required(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        feedback_artifact = write_feedback_artifact(result, root=root)

        draft = build_receipt_handoff(feedback_artifact.latest_artifact_path, root=root)
        summary = render_receipt_handoff_summary(draft)

        self.assertTrue(draft.reviewer_action_required)
        self.assertIn("Human review is required", draft.reviewer_action_required)
        self.assertIn("Reviewer action required:", summary)

    def test_does_not_require_lifeline_or_connector_scope(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        write_feedback_artifact(result.to_payload(), root=root)

        artifact = write_receipt_handoff(root=root)
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertEqual("cortex", payload["owner_layer"])
        self.assertEqual("cortex", payload["next_required_layer"])
        self.assertEqual("review_ready", payload["review_status"])

    def test_missing_feedback_artifact_fails_clearly(self) -> None:
        root = self._temp_root()

        with self.assertRaisesRegex(FileNotFoundError, "Feedback artifact not found at"):
            build_receipt_handoff(root=root)

    def test_malformed_feedback_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        artifact_path = root / "runtime" / "cortex" / "feedback" / "latest.json"
        _write_json(
            artifact_path,
            {
                "run_id": "",
                "selected_next_action": "next-action",
                "owner_layer": "cortex",
                "next_required_layer": "cortex",
                "targeted_verification_passed": True,
                "stack_validation_status": "not_run",
                "known_ambient_debt": [],
                "current_validation_debt": [],
                "receipt_ready": True,
                "tranche_complete": True,
                "blocked": False,
                "blocked_reason": None,
                "proof_summary": {},
                "receipt_draft": {},
                "ledger_summary": {},
                "applied_rules": {},
                "failure_modes_avoided": [],
            },
        )

        with self.assertRaisesRegex(ValueError, "Malformed Cortex feedback artifact at .*Expected non-empty string for run_id"):
            build_receipt_handoff(artifact_path, root=root)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)
        feedback_artifact = write_feedback_artifact(result, root=root)

        draft = build_receipt_handoff(feedback_artifact.latest_artifact_path, root=root)

        json.dumps(draft.to_payload(), sort_keys=True)


if __name__ == "__main__":
    unittest.main()
