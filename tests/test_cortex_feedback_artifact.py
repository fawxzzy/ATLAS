from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.feedback_artifact import (
    default_feedback_run_json_path,
    default_feedback_run_summary_path,
    render_feedback_summary,
    write_feedback_artifact,
)
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
        command="python -m unittest tests.test_cortex_feedback_artifact",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=("ops/cortex/feedback_artifact.py", "tests/test_cortex_feedback_artifact.py"),
        stdout_summary="Feedback artifact tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="feedback-artifact-targeted",
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
        proof_id="feedback-artifact-stack",
    )


class CortexFeedbackArtifactTests(unittest.TestCase):
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

    def test_writes_json_feedback_artifact(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)

        artifact = write_feedback_artifact(result, root=root)
        latest_payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))
        run_payload = json.loads(artifact.run_artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(result.to_payload(), latest_payload)
        self.assertEqual(latest_payload, run_payload)
        self.assertEqual(result.run_id, latest_payload["run_id"])

    def test_writes_human_readable_summary(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)

        artifact = write_feedback_artifact(result, root=root)
        summary = artifact.latest_summary_path.read_text(encoding="utf-8") if artifact.latest_summary_path is not None else ""

        self.assertEqual(artifact.summary, summary)
        self.assertIn("Cortex Feedback Result", summary)
        self.assertIn(f"Run id: {result.run_id}", summary)
        self.assertIn("Receipt draft title:", summary)

    def test_writes_latest_json_and_latest_text(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        artifact = write_feedback_artifact(self._classify_feedback(root), root=root)

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertTrue(artifact.latest_summary_path.exists() if artifact.latest_summary_path is not None else False)
        self.assertEqual("latest.json", artifact.latest_artifact_path.name)
        self.assertEqual("latest.txt", artifact.latest_summary_path.name if artifact.latest_summary_path is not None else "")

    def test_writes_run_specific_artifact_paths_deterministically(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)

        artifact = write_feedback_artifact(result, root=root)

        self.assertEqual(default_feedback_run_json_path(result.run_id, root), artifact.run_artifact_path)
        self.assertEqual(default_feedback_run_summary_path(result.run_id, root), artifact.run_summary_path)
        self.assertEqual("runtime/cortex/feedback/runs/cortex-run-result.latest.json", artifact.to_payload(root=root)["run_artifact_path"])

    def test_preserves_known_ambient_debt(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(
            root,
            stack=_stack_outcome(exit_code=2, observed_debt=KNOWN_STACK_VALIDATION_BASELINE),
        )

        artifact = write_feedback_artifact(result, root=root)
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))
        summary = artifact.latest_summary_path.read_text(encoding="utf-8") if artifact.latest_summary_path is not None else ""

        self.assertEqual(list(result.known_ambient_debt), payload["known_ambient_debt"])
        self.assertEqual([], payload["current_validation_debt"])
        self.assertIn("critical=345", summary)
        self.assertIn("Current validation debt: none", summary)

    def test_preserves_changed_validation_debt_separately(self) -> None:
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

        artifact = write_feedback_artifact(result, root=root)
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))
        summary = artifact.latest_summary_path.read_text(encoding="utf-8") if artifact.latest_summary_path is not None else ""

        self.assertTrue(any("observed critical=346" in item for item in payload["current_validation_debt"]))
        self.assertFalse(any("observed critical=346" in item for item in payload["known_ambient_debt"]))
        self.assertIn("Known ambient debt:", summary)
        self.assertIn("Current validation debt:", summary)
        self.assertIn("observed critical=346", summary)

    def test_blocked_feedback_summary_includes_blocked_reason(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(
            root,
            targeted=_targeted_outcome(
                exit_code=1,
                failures=("tests.test_cortex_feedback_artifact.CortexFeedbackArtifactTests.test_blocked_feedback_summary_includes_blocked_reason",),
                stderr_summary="1 feedback artifact test failed.",
            ),
        )

        summary = render_feedback_summary(result)

        self.assertIn("Blocked: yes", summary)
        self.assertIn("Blocked reason:", summary)
        self.assertIn("test_blocked_feedback_summary_includes_blocked_reason", summary)

    def test_receipt_ready_feedback_summary_includes_receipt_draft_fields(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)

        summary = render_feedback_summary(result)

        self.assertIn(f"Receipt draft title: {result.receipt_draft.receipt_title}", summary)
        self.assertIn("Receipt draft status: ready", summary)
        self.assertIn("Receipt draft next action:", summary)

    def test_malformed_feedback_result_fails_clearly(self) -> None:
        root = self._temp_root()

        with self.assertRaisesRegex(ValueError, "Expected non-empty string for run_id"):
            write_feedback_artifact(
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
                root=root,
            )

    def test_artifact_writer_does_not_require_connectors_or_lifeline(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result = self._classify_feedback(root)

        artifact = write_feedback_artifact(result.to_payload(), root=root)

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertEqual("cortex", result.owner_layer)
        self.assertEqual("cortex", result.next_required_layer)
        self.assertEqual("runtime/cortex/feedback/latest.json", artifact.to_payload(root=root)["latest_artifact_path"])


if __name__ == "__main__":
    unittest.main()
