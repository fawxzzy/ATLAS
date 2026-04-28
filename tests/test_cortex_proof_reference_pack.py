from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.feedback_artifact import write_feedback_artifact
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.proof_reference_pack import (
    build_proof_reference_pack,
    default_proof_reference_pack_run_json_path,
    default_proof_reference_pack_run_summary_path,
    render_proof_reference_pack_summary,
    write_proof_reference_pack,
)
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
        command="python -m unittest tests.test_cortex_proof_reference_pack",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=("ops/cortex/proof_reference_pack.py", "tests/test_cortex_proof_reference_pack.py"),
        stdout_summary="Proof reference pack tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="proof-reference-pack-targeted",
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
        proof_id="proof-reference-pack-stack",
    )


class CortexProofReferencePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.base_payload = load_and_run_cortex_loop(root=cls.root).to_payload()

    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _seed_run(self, root: Path, payload: dict | None = None, *, name: str = "cortex-run-result.latest.json") -> Path:
        artifact_path = root / "runtime" / "cortex" / "runs" / name
        _write_json(artifact_path, payload or self.base_payload)
        return artifact_path

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

    def _seed_feedback_and_handoff(
        self,
        root: Path,
        *,
        targeted: VerificationOutcome | None = None,
        stack: VerificationOutcome | None = None,
    ):
        result = self._classify_feedback(root, targeted=targeted, stack=stack)
        feedback_artifact = write_feedback_artifact(result, root=root)
        handoff_artifact = write_receipt_handoff(root=root)
        return result, feedback_artifact, handoff_artifact

    def test_builds_proof_reference_pack_from_receipt_ready_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result, feedback_artifact, handoff_artifact = self._seed_feedback_and_handoff(root)

        pack = build_proof_reference_pack(root=root)

        self.assertEqual(result.run_id, pack.run_id)
        self.assertEqual("cortex", pack.owner_layer)
        self.assertEqual(result.selected_next_action, pack.selected_next_action)
        self.assertFalse(pack.blocked)
        self.assertEqual("review_ready", pack.pack_status)
        self.assertEqual(feedback_artifact.latest_artifact_path, pack.feedback_artifact_path)
        self.assertEqual(handoff_artifact.latest_artifact_path, pack.handoff_artifact_path)
        self.assertIn("python -m unittest tests.test_cortex_proof_reference_pack", pack.targeted_verification_commands)

    def test_builds_blocked_proof_reference_pack_from_blocked_handoff(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(
            root,
            targeted=_targeted_outcome(
                exit_code=1,
                failures=(
                    "tests.test_cortex_proof_reference_pack.CortexProofReferencePackTests.test_builds_blocked_proof_reference_pack_from_blocked_handoff",
                ),
                stderr_summary="1 proof reference pack test failed.",
            ),
        )

        pack = build_proof_reference_pack(root=root)

        self.assertTrue(pack.blocked)
        self.assertEqual("blocked", pack.pack_status)
        self.assertEqual("blocked", pack.review_status)
        self.assertIn("test_builds_blocked_proof_reference_pack_from_blocked_handoff", pack.blocked_reason or "")

    def test_writes_latest_json_and_latest_text(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(root)

        artifact = write_proof_reference_pack(root=root)
        summary = artifact.latest_summary_path.read_text(encoding="utf-8") if artifact.latest_summary_path is not None else ""

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertTrue(artifact.latest_summary_path.exists() if artifact.latest_summary_path is not None else False)
        self.assertEqual("latest.json", artifact.latest_artifact_path.name)
        self.assertEqual("latest.txt", artifact.latest_summary_path.name if artifact.latest_summary_path is not None else "")
        self.assertIn("Cortex Proof Reference Pack", summary)
        self.assertIn("Rule: Cortex may assemble proof-reference packs", summary)

    def test_writes_run_scoped_json_and_text_artifacts(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        result, _, _ = self._seed_feedback_and_handoff(root)

        artifact = write_proof_reference_pack(root=root)

        self.assertEqual(default_proof_reference_pack_run_json_path(result.run_id, root), artifact.run_artifact_path)
        self.assertEqual(default_proof_reference_pack_run_summary_path(result.run_id, root), artifact.run_summary_path)
        self.assertEqual(
            "runtime/cortex/proof-reference-packs/runs/cortex-run-result.latest.json",
            artifact.to_payload(root=root)["run_artifact_path"],
        )

    def test_preserves_known_ambient_debt_separately_from_current_validation_debt(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(
            root,
            stack=_stack_outcome(
                exit_code=2,
                observed_debt=VerificationDebtCounts(critical=346, error=14, warning=181),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
            ),
        )

        artifact = write_proof_reference_pack(root=root)
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(KNOWN_STACK_VALIDATION_BASELINE.to_payload(), payload["stack_validation"]["known_ambient_baseline"])
        self.assertTrue(any("observed critical=346" in item for item in payload["current_validation_debt"]))
        self.assertFalse(any("observed critical=346" in item for item in payload["known_ambient_debt"]))

    def test_includes_expected_reference_kinds(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(root)

        pack = build_proof_reference_pack(root=root)
        kinds = {reference.kind for reference in pack.references}
        summary = render_proof_reference_pack_summary(pack)

        self.assertTrue(
            {
                "cortex_run_artifact",
                "cortex_feedback_artifact",
                "cortex_receipt_handoff_draft",
                "targeted_verification_command",
                "stack_validation_command",
                "applied_rules",
                "failure_modes_avoided",
            }.issubset(kinds)
        )
        self.assertIn("Failure modes avoided:", summary)
        self.assertIn("Applied rules:", summary)

    def test_missing_run_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        run_path = self._seed_run(root)
        result, _, _ = self._seed_feedback_and_handoff(root)
        run_path.unlink()

        with self.assertRaisesRegex(FileNotFoundError, "Cortex run artifact not found at"):
            build_proof_reference_pack(feedback_artifact=result, root=root)

    def test_missing_feedback_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        self._seed_run(root)

        with self.assertRaisesRegex(FileNotFoundError, "Feedback artifact not found at"):
            build_proof_reference_pack(root=root)

    def test_malformed_handoff_artifact_fails_clearly(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(root)
        artifact_path = root / "runtime" / "cortex" / "receipt-drafts" / "latest.json"
        _write_json(
            artifact_path,
            {
                "run_id": "cortex-run-result.latest",
                "receipt_title": "",
                "owner_layer": "cortex",
                "selected_next_action": "review",
                "next_required_layer": "cortex",
                "tranche_complete": True,
                "receipt_ready": True,
                "blocked": False,
                "blocked_reason": None,
                "passed_commands": [],
                "failed_commands": [],
                "known_ambient_debt": [],
                "current_validation_debt": [],
                "touched_files": [],
                "applied_rules": {},
                "failure_modes_avoided": [],
                "boundary_statement": "cortex boundary is clean for cortex.",
                "reviewer_action_required": "Human review is required.",
                "review_status": "review_ready",
            },
        )

        with self.assertRaisesRegex(
            ValueError,
            "Malformed Cortex receipt handoff draft at .*Expected non-empty string for receipt_title",
        ):
            build_proof_reference_pack(root=root)

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(root)

        pack = build_proof_reference_pack(root=root)

        json.dumps(pack.to_payload(root=root), sort_keys=True)

    def test_does_not_require_lifeline_or_connectors(self) -> None:
        root = self._temp_root()
        self._seed_run(root)
        self._seed_feedback_and_handoff(root)

        artifact = write_proof_reference_pack(root=root)
        payload = json.loads(artifact.latest_artifact_path.read_text(encoding="utf-8"))

        self.assertTrue(artifact.latest_artifact_path.exists())
        self.assertEqual("cortex", payload["owner_layer"])
        self.assertEqual("lifeline", payload["final_receipt_owner"])
        self.assertEqual("cortex", payload["next_required_layer"])


if __name__ == "__main__":
    unittest.main()
