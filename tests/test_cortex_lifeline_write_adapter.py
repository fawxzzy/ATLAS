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
from ops.cortex.lifeline_write_adapter import (
    LifelineWriteAdapter,
    default_lifeline_write_ready_latest_json_path,
    default_lifeline_write_ready_run_json_path,
    prepare_lifeline_receipt_payload,
    write_lifeline_receipt_with_approval,
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
        command="python -m unittest tests.test_cortex_lifeline_write_adapter",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=(
            "ops/cortex/lifeline_write_adapter.py",
            "tests/test_cortex_lifeline_write_adapter.py",
        ),
        stdout_summary="Lifeline write adapter tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="lifeline-write-adapter-targeted",
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
        proof_id="lifeline-write-adapter-stack",
    )


class CortexLifelineWriteAdapterTests(unittest.TestCase):
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

    def _approved_result(self, pack_path: Path, *, root: Path):
        return write_lifeline_receipt_with_approval(
            pack_path,
            root=root,
            approval={
                "explicit_human_approval": True,
                "reviewer_label": "Lane Q reviewer",
                "approval_note": "Human-approved gated Lifeline write adapter review.",
            },
        )

    def test_valid_candidate_without_explicit_human_approval_is_blocked(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        result = write_lifeline_receipt_with_approval(
            pack_path,
            root=root,
            approval={
                "explicit_human_approval": False,
                "reviewer_label": "Lane Q reviewer",
            },
        )

        self.assertTrue(result.candidate_valid)
        self.assertTrue(result.human_review_ready)
        self.assertTrue(result.lifeline_write_eligible)
        self.assertFalse(result.explicit_human_approval)
        self.assertFalse(result.auto_approved)
        self.assertTrue(result.blocked)
        self.assertIn("Explicit human approval is required", result.blocked_reason or "")
        self.assertFalse(result.receipt_written)
        self.assertFalse(result.write_ready_artifact_written)
        self.assertFalse(default_lifeline_write_ready_run_json_path(result.run_id, root).exists())

    def test_valid_candidate_with_explicit_human_approval_produces_a_write_ready_result(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        result = self._approved_result(pack_path, root=root)

        self.assertTrue(result.candidate_valid)
        self.assertTrue(result.human_review_ready)
        self.assertTrue(result.lifeline_write_eligible)
        self.assertTrue(result.explicit_human_approval)
        self.assertFalse(result.auto_approved)
        self.assertFalse(result.blocked)
        self.assertFalse(result.receipt_written)
        self.assertTrue(result.write_ready_artifact_written)
        self.assertEqual(
            "runtime/cortex/lifeline-write-ready/runs/cortex-run-result.latest.json",
            result.write_ready_artifact_path,
        )
        self.assertTrue(default_lifeline_write_ready_latest_json_path(root).exists())
        self.assertTrue(default_lifeline_write_ready_run_json_path(result.run_id, root).exists())

    def test_candidate_with_current_validation_debt_is_blocked(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(
            root,
            stack=_stack_outcome(
                exit_code=2,
                observed_debt=VerificationDebtCounts(critical=345, error=14, warning=183),
                expected_ambient_debt=KNOWN_STACK_VALIDATION_BASELINE,
            ),
        )

        result = self._approved_result(pack_path, root=root)

        self.assertTrue(result.candidate_valid)
        self.assertTrue(result.blocked)
        self.assertIn("observed critical=345, error=14, warning=183", result.blocked_reason or "")
        self.assertFalse(result.write_ready_artifact_written)
        self.assertFalse(default_lifeline_write_ready_run_json_path(result.run_id, root).exists())

    def test_candidate_missing_required_references_is_blocked(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        payload = json.loads(pack_path.read_text(encoding="utf-8"))
        payload["references"] = [item for item in payload["references"] if item["kind"] != "cortex_run_artifact"]
        _write_json(pack_path, payload)

        result = self._approved_result(pack_path, root=root)

        self.assertTrue(result.blocked)
        self.assertIn("run artifact reference", result.blocked_reason or "")
        self.assertFalse(result.write_ready_artifact_written)

    def test_blocked_candidate_is_never_written(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(
            root,
            targeted=_targeted_outcome(
                exit_code=1,
                failures=(
                    "tests.test_cortex_lifeline_write_adapter.CortexLifelineWriteAdapterTests.test_blocked_candidate_is_never_written",
                ),
                stderr_summary="1 Lifeline write adapter test failed.",
            ),
        )

        result = self._approved_result(pack_path, root=root)

        self.assertTrue(result.blocked)
        self.assertFalse(result.receipt_written)
        self.assertFalse(result.write_ready_artifact_written)
        self.assertFalse(default_lifeline_write_ready_run_json_path(result.run_id, root).exists())

    def test_auto_approved_is_always_false(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        adapter = LifelineWriteAdapter()

        prepared = adapter.prepare(
            pack_path,
            root=root,
            approval={
                "explicit_human_approval": True,
                "reviewer_id": "reviewer-1",
                "approval_note": "Safe write-ready preparation only.",
            },
        )
        written = self._approved_result(pack_path, root=root)

        self.assertFalse(prepared.auto_approved)
        self.assertFalse(written.auto_approved)

    def test_adapter_does_not_require_connectors(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        payload = prepare_lifeline_receipt_payload(
            pack_path,
            root=root,
            approval={
                "explicit_human_approval": True,
                "reviewer_id": "reviewer-1",
                "approval_note": "Prepare locally without external connectors.",
            },
        )

        self.assertEqual("atlas.cortex.lifeline-write-ready.v1", payload["contract_version"])
        self.assertEqual("cortex_write_ready_artifact_only", payload["write_scope"])
        self.assertEqual(False, payload["auto_approved"])

    def test_adapter_does_not_mutate_unrelated_owner_repos(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        lifeline_repo = root / "repos" / "fawxzzy-lifeline"
        fitness_repo = root / "repos" / "fawxzzy-fitness"
        sentinel_paths = (
            lifeline_repo / "sentinel.txt",
            fitness_repo / "sentinel.txt",
        )
        for path in sentinel_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("unchanged\n", encoding="utf-8")
        before_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())

        result = self._approved_result(pack_path, root=root)

        after_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        self.assertTrue(result.write_ready_artifact_written)
        self.assertEqual("unchanged\n", sentinel_paths[0].read_text(encoding="utf-8"))
        self.assertEqual("unchanged\n", sentinel_paths[1].read_text(encoding="utf-8"))
        new_files = [path for path in after_files if path not in before_files]
        self.assertEqual(
            [
                "runtime/cortex/lifeline-write-ready/latest.json",
                "runtime/cortex/lifeline-write-ready/runs/cortex-run-result.latest.json",
            ],
            [item.replace("\\", "/") for item in new_files],
        )

    def test_output_is_json_serializable(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        result = self._approved_result(pack_path, root=root)
        payload = prepare_lifeline_receipt_payload(
            pack_path,
            root=root,
            approval={
                "explicit_human_approval": True,
                "reviewer_label": "Lane Q reviewer",
                "approval_note": "Serialize the write-ready payload.",
            },
        )

        json.dumps(result.to_payload(), sort_keys=True)
        json.dumps(payload, sort_keys=True)

    def test_ambiguous_lifeline_format_stops_at_write_ready_artifact_instead_of_guessing(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)

        result = self._approved_result(pack_path, root=root)
        written_payload = json.loads(
            default_lifeline_write_ready_run_json_path(result.run_id, root).read_text(encoding="utf-8")
        )

        self.assertFalse(result.final_receipt_ready)
        self.assertFalse(result.receipt_written)
        self.assertIsNone(result.receipt_path)
        self.assertIn("missing mapped inputs", result.final_receipt_blocked_reason or "")
        self.assertEqual("cortex_write_ready_artifact_only", written_payload["write_scope"])
        self.assertEqual(False, written_payload["final_receipt_ready"])
        self.assertTrue(any(item == "source_repo_id" for item in written_payload["required_lifeline_inputs_missing"]))

    def test_defaults_to_integrated_pack_when_present(self) -> None:
        root = self._temp_root()
        pack_path = self._seed_pack(root)
        integrated_path = self._seed_integrated_pack(root, pack_path)

        result = write_lifeline_receipt_with_approval(
            root=root,
            approval={
                "explicit_human_approval": True,
                "reviewer_label": "Lane Q reviewer",
                "approval_note": "Use the integrated proof-reference pack.",
            },
        )

        self.assertTrue(result.write_ready_artifact_written)
        self.assertEqual("runtime/cortex/proof-reference-packs/integrated/latest.json", result.proof_reference_pack_path)
        self.assertEqual(
            "runtime/cortex/proof-reference-packs/integrated/latest.json",
            result.prepared_receipt_payload["proof_reference_pack_path"],
        )
        self.assertTrue(integrated_path.exists())


if __name__ == "__main__":
    unittest.main()
