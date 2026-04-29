from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.feedback_artifact import write_feedback_artifact
from ops.cortex.connector_proof_reference_integration import (
    default_integrated_proof_reference_pack_latest_json_path,
)
from ops.cortex.lifeline_receipt_candidate import (
    render_lifeline_candidate_summary,
    validate_lifeline_receipt_candidate,
)
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.proof_reference_pack import write_proof_reference_pack
from ops.cortex.receipt_handoff import write_receipt_handoff
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
        command="python -m unittest tests.test_cortex_lifeline_receipt_candidate",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=(
            "ops/cortex/lifeline_receipt_candidate.py",
            "tests/test_cortex_lifeline_receipt_candidate.py",
        ),
        stdout_summary="Lifeline receipt candidate tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="lifeline-receipt-candidate-targeted",
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
        proof_id="lifeline-receipt-candidate-stack",
    )


class CortexLifelineReceiptCandidateTests(unittest.TestCase):
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

    def _seed_pack(
        self,
        root: Path,
        *,
        targeted: VerificationOutcome | None = None,
        stack: VerificationOutcome | None = None,
    ) -> Path:
        self._seed_run(root)
        result = self._classify_feedback(root, targeted=targeted, stack=stack)
        write_feedback_artifact(result, root=root)
        write_receipt_handoff(root=root)
        artifact = write_proof_reference_pack(root=root)
        return artifact.latest_artifact_path

    def _seed_integrated_pack(self, root: Path, pack_path: Path) -> Path:
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        integrated_path = default_integrated_proof_reference_pack_latest_json_path(root)
        _write_json(integrated_path, payload)
        return integrated_path

    def test_valid_receipt_ready_pack_is_human_review_ready(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)
        summary = render_lifeline_candidate_summary(validation)

        self.assertTrue(validation.candidate_valid)
        self.assertTrue(validation.human_review_ready)
        self.assertTrue(validation.lifeline_write_eligible)
        self.assertFalse(validation.auto_approved)
        self.assertFalse(validation.blocked)
        self.assertIsNone(validation.blocked_reason)
        self.assertIn("Human review may evaluate this Cortex proof-reference pack", validation.required_reviewer_action)
        self.assertIn("Lifeline Receipt Candidate Validation", summary)

    def test_blocked_pack_is_still_a_candidate_artifact_but_not_review_ready(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(
            root,
            targeted=_targeted_outcome(
                exit_code=1,
                failures=(
                    "tests.test_cortex_lifeline_receipt_candidate.CortexLifelineReceiptCandidateTests.test_blocked_pack_is_still_a_candidate_artifact_but_not_review_ready",
                ),
                stderr_summary="1 Lifeline receipt candidate test failed.",
            ),
        )

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertTrue(validation.candidate_valid)
        self.assertFalse(validation.human_review_ready)
        self.assertFalse(validation.lifeline_write_eligible)
        self.assertFalse(validation.auto_approved)
        self.assertTrue(validation.blocked)
        self.assertIn("test_blocked_pack_is_still_a_candidate_artifact_but_not_review_ready", validation.blocked_reason or "")

    def test_warning_only_validation_drift_blocks_lifeline_write_eligibility(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(
            root,
            stack=_stack_outcome(
                exit_code=2,
                observed_debt=VerificationDebtCounts(critical=345, error=14, warning=183),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
            ),
        )

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertTrue(validation.candidate_valid)
        self.assertFalse(validation.lifeline_write_eligible)
        self.assertTrue(validation.blocked)
        self.assertIn("observed critical=345, error=14, warning=183", validation.blocked_reason or "")

    def test_known_ambient_debt_does_not_block_candidate_validation(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        payload["known_ambient_debt"] = ["critical=345, error=14, warning=181"]
        _write_json(pack_path, payload)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertTrue(validation.candidate_valid)
        self.assertTrue(validation.human_review_ready)
        self.assertEqual(("critical=345, error=14, warning=181",), validation.known_ambient_debt)

    def test_missing_run_artifact_reference_fails_clearly(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        payload["references"] = [item for item in payload["references"] if item["kind"] != "cortex_run_artifact"]
        _write_json(pack_path, payload)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertFalse(validation.candidate_valid)
        self.assertIn("run artifact reference", validation.missing_references)
        self.assertIn("Missing required proof references", validation.blocked_reason or "")

    def test_missing_targeted_verification_reference_fails_clearly(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        payload["references"] = [
            item for item in payload["references"] if item["kind"] != "targeted_verification_command"
        ]
        _write_json(pack_path, payload)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertFalse(validation.candidate_valid)
        self.assertIn("targeted verification command reference", validation.missing_references)

    def test_missing_boundary_statement_fails_clearly(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        for item in payload["references"]:
            if item["kind"] == "cortex_receipt_handoff_draft":
                item["notes"] = [note for note in item["notes"] if not note.startswith("Boundary statement=")]
        _write_json(pack_path, payload)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertFalse(validation.candidate_valid)
        self.assertEqual("Missing boundary statement on the receipt handoff reference.", validation.blocked_reason)

    def test_auto_approved_is_always_false(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertFalse(validation.auto_approved)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        json.dumps(validation.to_payload(), sort_keys=True)

    def test_does_not_require_lifeline_connectors_git_or_shell_execution(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        validation = validate_lifeline_receipt_candidate(pack_path, root=root)

        self.assertTrue(Path(validation.proof_reference_pack_path).exists())
        self.assertTrue(validation.candidate_valid)
        self.assertIn("proof-reference-packs", validation.proof_reference_pack_path)

    def test_defaults_to_integrated_pack_when_present(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        integrated_path = self._seed_integrated_pack(root, pack_path)

        validation = validate_lifeline_receipt_candidate(root=root)

        self.assertTrue(validation.candidate_valid)
        self.assertEqual(str(integrated_path).replace("\\", "/"), validation.proof_reference_pack_path)


if __name__ == "__main__":
    unittest.main()
