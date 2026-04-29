from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas.ui_proof.fitness import default_schema_path, derive_ui_proof_summary
from ops.cortex.feedback import CortexFeedbackInput, classify_feedback
from ops.cortex.feedback_artifact import write_feedback_artifact
from ops.cortex.lifeline_receipt_payload import (
    build_lifeline_receipt_candidate,
    default_lifeline_receipt_candidate_latest_json_path,
    default_lifeline_receipt_candidate_latest_summary_path,
    default_lifeline_receipt_candidate_run_json_path,
    validate_lifeline_receipt_payload,
    write_lifeline_receipt_candidate,
)
from ops.cortex.lifeline_write_adapter import LifelineReceiptInput, write_lifeline_receipt_with_approval
from ops.cortex.loop import load_and_run_cortex_loop
from ops.cortex.proof_reference_pack import write_proof_reference_pack
from ops.cortex.receipt_handoff import write_receipt_handoff
from ops.cortex.verification_ingest import KNOWN_STACK_VALIDATION_BASELINE, VerificationDebtCounts, VerificationOutcome


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_lifeline_receipt_writer(*, candidate_path: Path, lifeline_root: Path) -> dict[str, object]:
    writer_module_uri = (
        atlas_root()
        / "repos"
        / "fawxzzy-lifeline"
        / "scripts"
        / "write-proof-reference-receipt.mjs"
    ).as_uri()
    completed = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            (
                f"import {{ readFile }} from 'node:fs/promises';\n"
                f"import {{ writeProofReferenceReceipt, validateProofReferenceReceiptCandidate }} from {json.dumps(writer_module_uri)};\n"
                "const [candidatePath, lifelineRoot] = process.argv.slice(1);\n"
                "const result = await writeProofReferenceReceipt({ candidatePath, lifelineRoot });\n"
                "let finalValidation = null;\n"
                "if (result.receipt_written && result.receipt_path) {\n"
                "  const finalReceipt = JSON.parse(await readFile(result.receipt_path, 'utf8'));\n"
                "  finalValidation = await validateProofReferenceReceiptCandidate({ candidate: finalReceipt });\n"
                "}\n"
                "console.log(JSON.stringify({ result, finalValidation }, null, 2));\n"
                "process.exitCode = result.blocked ? 1 : 0;\n"
            ),
            str(candidate_path),
            str(lifeline_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "Lifeline proof-reference writer failed unexpectedly.\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return json.loads(completed.stdout)


def _targeted_outcome(
    *,
    exit_code: int = 0,
    failures: tuple[str, ...] = (),
    stderr_summary: str | None = None,
) -> VerificationOutcome:
    return VerificationOutcome(
        command="python -m unittest tests.test_cortex_lifeline_receipt_payload",
        exit_code=exit_code,
        owner_layer="cortex",
        touched_files=(
            "ops/cortex/lifeline_receipt_payload.py",
            "tests/test_cortex_lifeline_receipt_payload.py",
        ),
        stdout_summary="Lifeline receipt payload tests passed." if exit_code == 0 and not failures else None,
        stderr_summary=stderr_summary,
        failures=failures,
        next_required_layer="cortex",
        proof_id="lifeline-receipt-payload-targeted",
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
        proof_id="lifeline-receipt-payload-stack",
    )


class CortexLifelineReceiptPayloadTests(unittest.TestCase):
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

    def _seed_ui_proof_summary(self, root: Path) -> None:
        _write_json(
            root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness" / "latest.json",
            {
                "contract_version": "atlas.ui.drift.report.v1",
                "report_id": "sha256:" + ("1" * 64),
                "generated_at": "2026-04-28T18:40:00.000Z",
                "owner_repo_id": "fitness",
                "owner_contract_refs": {},
                "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                "summary": {
                    "status": "clean",
                    "expected_capture_count": 46,
                    "observed_capture_count": 46,
                    "finding_count": 0,
                    "mismatch_count": 0,
                    "missing_count": 0,
                    "unexpected_count": 0,
                },
                "findings": [],
                "operator_summary": ["No UI drift detected across 46 captures."],
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "ui-visual-proof" / "fitness" / "latest.json",
            {
                "contract_version": "atlas.ui.visual-proof.report.v1",
                "report_id": "sha256:" + ("2" * 64),
                "generated_at": "2026-04-28T18:41:00.000Z",
                "runner_version": "atlas.ui.visual-proof.fitness.v1",
                "owner_repo_id": "fitness",
                "manifest_ref": "ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json",
                "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
                "summary": {
                    "status": "clean",
                    "capture_count": 2,
                    "passing_count": 2,
                    "failing_count": 0,
                },
                "results": [
                    {"capture_id": "settings-overview-default", "status": "pass"},
                    {"capture_id": "today-overview-default", "status": "pass"},
                ],
                "operator_summary": ["Visual proof passed across 2 captures."],
            },
        )
        derive_ui_proof_summary(
            root=root,
            schema_path=default_schema_path(atlas_root()),
            dry_run=False,
        )

    def _seed_write_ready(self, root: Path) -> None:
        pack_path = self._seed_pack(root)
        self._seed_ui_proof_summary(root)
        write_lifeline_receipt_with_approval(
            pack_path,
            root=root,
            approval={
                "explicit_human_approval": True,
                "approved_at": "2026-04-28T18:42:00.000Z",
                "reviewer_label": "Lane S reviewer",
                "approval_note": "Explicit human approval recorded after compatibility review.",
            },
            lifeline_receipt_input=LifelineReceiptInput(
                source_repo_id="fitness",
                tranche_id="F11",
                proof_summary_ref="runtime/atlas/ui-proof/fitness/latest.json",
            ),
        )

    def test_builds_lifeline_compatible_candidate_payload_from_valid_write_ready_artifact(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = write_lifeline_receipt_candidate(root=root)

        self.assertTrue(default_lifeline_receipt_candidate_latest_json_path(root).exists())
        self.assertTrue(default_lifeline_receipt_candidate_latest_summary_path(root).exists())
        self.assertTrue(default_lifeline_receipt_candidate_run_json_path(artifact.run_id, root).exists())
        self.assertTrue(artifact.schema_validation.valid)

    def test_payload_includes_required_proof_references(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)
        source_refs = set(artifact.candidate_payload["source_refs"])

        self.assertEqual(
            "runtime/atlas/ui-observe/drift/fitness/latest.json",
            artifact.candidate_payload["proof_refs"]["semantic_report_ref"],
        )
        self.assertEqual(
            "runtime/atlas/ui-visual-proof/fitness/latest.json",
            artifact.candidate_payload["proof_refs"]["visual_report_ref"],
        )
        self.assertIn("runtime/atlas/ui-proof/fitness/latest.json", source_refs)

    def test_payload_includes_explicit_human_approval_metadata(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)
        approval = artifact.candidate_payload["approval"]

        self.assertEqual(True, approval["explicit_human_approval"])
        self.assertEqual("2026-04-28T18:42:00.000Z", approval["approved_at"])
        self.assertEqual("Lane S reviewer", approval["reviewer_label"])
        self.assertIn("compatibility review", approval["approval_note"])

    def test_payload_keeps_auto_approved_false(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)

        self.assertFalse(artifact.candidate_payload["approval"]["auto_approved"])

    def test_payload_normalizes_owner_boundary_statement_for_lifeline_writer(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)
        statement = artifact.candidate_payload["boundary"]["statement"]

        self.assertIn("Cortex prepared the proof-reference material", statement)
        self.assertIn("Lifeline owns final receipt truth", statement)
        self.assertIn("Source boundary context:", statement)

    def test_payload_preserves_known_ambient_debt(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)

        self.assertTrue(artifact.candidate_payload["validation_context"]["known_ambient_debt"])
        self.assertIn(
            "outside the active Cortex tranche",
            artifact.candidate_payload["validation_context"]["known_ambient_debt"][0],
        )

    def test_payload_refuses_current_validation_debt(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)
        latest_path = root / "runtime" / "cortex" / "lifeline-write-ready" / "latest.json"
        payload = json.loads(latest_path.read_text(encoding="utf-8"))
        payload["current_validation_debt"] = ["observed critical=345, error=14, warning=183"]
        _write_json(latest_path, payload)

        with self.assertRaisesRegex(ValueError, "current_validation_debt is non-empty"):
            build_lifeline_receipt_candidate(root=root)

    def test_payload_fails_clearly_when_write_ready_artifact_is_missing(self) -> None:
        root = self._temp_root()

        with self.assertRaisesRegex(FileNotFoundError, "Cortex write-ready artifact not found at"):
            build_lifeline_receipt_candidate(root=root)

    def test_payload_fails_clearly_when_write_ready_artifact_is_malformed(self) -> None:
        root = self._temp_root()
        _write_json(
            root / "runtime" / "cortex" / "lifeline-write-ready" / "latest.json",
            {"contract_version": "atlas.cortex.lifeline-write-ready.v1", "run_id": ""},
        )

        with self.assertRaisesRegex(ValueError, "Expected non-empty string for run_id"):
            build_lifeline_receipt_candidate(root=root)

    def test_payload_structurally_matches_lifeline_schema(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)
        validation = validate_lifeline_receipt_payload(artifact.candidate_payload, root=root)

        self.assertTrue(validation.valid)
        self.assertEqual((), validation.errors)

    def test_candidate_payload_is_json_serializable(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = build_lifeline_receipt_candidate(root=root)

        json.dumps(artifact.to_payload(), sort_keys=True)
        json.dumps(artifact.candidate_payload, sort_keys=True)

    def test_no_final_lifeline_receipt_is_written(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)

        artifact = write_lifeline_receipt_candidate(root=root)

        self.assertFalse(artifact.final_receipt_written)
        self.assertFalse((root / "repos" / "fawxzzy-lifeline").exists())

    def test_cortex_candidate_roundtrips_through_lifeline_writer_into_one_isolated_final_receipt(self) -> None:
        root = self._temp_root()
        self._seed_write_ready(root)
        (root / "stack.yaml").write_text("name: ATLAS\n", encoding="utf-8")

        artifact = write_lifeline_receipt_candidate(root=root)
        candidate_payload = artifact.candidate_payload
        candidate_path = root / "runtime" / "cortex" / "lifeline-receipt-candidates" / "lane-u-final-candidate.json"
        _write_json(candidate_path, candidate_payload)
        lifeline_root = root / "repos" / "fawxzzy-lifeline"
        roundtrip = _run_lifeline_receipt_writer(candidate_path=candidate_path, lifeline_root=lifeline_root)
        result = roundtrip["result"]
        final_validation = roundtrip["finalValidation"]

        self.assertFalse(result["blocked"])
        self.assertTrue(result["receipt_written"])
        self.assertTrue(result["schema_valid"])
        self.assertEqual(False, result["auto_approved"])
        self.assertEqual("Lane S reviewer", result["reviewer_label"])
        self.assertEqual(2, result["proof_reference_count"])
        self.assertIsNone(result["blocked_reason"])
        self.assertIsNotNone(final_validation)
        self.assertTrue(final_validation["schemaValid"])
        self.assertEqual([], final_validation["schemaErrors"])
        self.assertEqual([], final_validation["canonicalRefErrors"])
        self.assertEqual([], final_validation["missingRequiredProofRefs"])
        self.assertIsNone(final_validation["blockedReason"])

        receipt_path = Path(result["receipt_path"])
        self.assertTrue(receipt_path.exists())
        self.assertEqual(
            f"{candidate_payload['receipt_id'].replace(':', '-')}.json",
            receipt_path.name,
        )
        self.assertEqual(
            ".lifeline/receipts/proof-reference-accepted/fitness/F11",
            normalize_slashes(str(receipt_path.parent.relative_to(lifeline_root))),
        )
        written_files = sorted(
            normalize_slashes(str(path.relative_to(lifeline_root)))
            for path in (lifeline_root / ".lifeline" / "receipts" / "proof-reference-accepted").rglob("*.json")
        )
        self.assertEqual(
            [
                ".lifeline/receipts/proof-reference-accepted/fitness/F11/"
                f"{candidate_payload['receipt_id'].replace(':', '-')}.json"
            ],
            written_files,
        )

        final_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        structural_validation = validate_lifeline_receipt_payload(final_receipt, root=root)
        self.assertTrue(structural_validation.valid)
        self.assertEqual((), structural_validation.errors)
        self.assertEqual("atlas.lifeline.proof-reference.receipt.v1", final_receipt["contract_version"])
        self.assertEqual("lifeline.proof-reference-receipt.v1", final_receipt["runner_version"])
        self.assertTrue(final_receipt["approval"]["explicit_human_approval"])
        self.assertFalse(final_receipt["approval"]["auto_approved"])
        self.assertEqual([], final_receipt["validation_context"]["current_validation_debt"])
        self.assertEqual(
            candidate_payload["validation_context"]["known_ambient_debt"],
            final_receipt["validation_context"]["known_ambient_debt"],
        )
        self.assertEqual(
            candidate_payload["boundary"]["statement"],
            final_receipt["boundary"]["statement"],
        )
        self.assertFalse(artifact.final_receipt_written)


if __name__ == "__main__":
    unittest.main()
