from __future__ import annotations

import json
import unittest

from ops.cortex.kernel import CortexProofSummary, VerificationResult
from ops.cortex.proof_receipt import (
    ProofReceiptDraftBuilder,
    ProofReceiptDraftInput,
    ProofReceiptKnownDebtSummary,
)


def _summary(
    *,
    proof_id: str,
    command: str,
    status: str,
    passed: list[str],
    failed: list[str],
    known_debt: list[str],
    owner_layer: str,
    next_required_layer: str | None,
    receipt_ready: bool,
) -> CortexProofSummary:
    return CortexProofSummary(
        proof_id=proof_id,
        command=command,
        verification=VerificationResult(
            status=status,
            passed=tuple(passed),
            failed=tuple(failed),
            known_debt=tuple(known_debt),
            notes=(),
        ),
        touched_files=(),
        owner_layer=owner_layer,
        next_required_layer=next_required_layer,
        receipt_ready=receipt_ready,
        evidence=(),
    )


def _build_draft(
    *,
    proof_summary: CortexProofSummary,
    touched_files: list[str],
    owner_layer: str,
    next_required_layer: str | None,
    ambient_debt: list[str] | tuple[str, ...] = (),
    current_validation_debt: list[str] | tuple[str, ...] = (),
    boundary_status: str = "clean",
) -> dict[str, object]:
    builder = ProofReceiptDraftBuilder()
    draft = builder.build(
        ProofReceiptDraftInput(
            proof_summary=proof_summary,
            touched_files=tuple(touched_files),
            owner_layer=owner_layer,
            next_required_layer=next_required_layer,
            known_debt_summary=ProofReceiptKnownDebtSummary(
                ambient_debt=tuple(ambient_debt),
                current_validation_debt=tuple(current_validation_debt),
                owner_boundary_status=boundary_status,
            ),
        )
    )
    payload = draft.to_payload()
    json.dumps(payload, sort_keys=True)
    return payload


class CortexProofReceiptTests(unittest.TestCase):
    def test_clean_cortex_kernel_tranche_is_receipt_ready(self) -> None:
        payload = _build_draft(
            proof_summary=_summary(
                proof_id="cortex-kernel-schema-clean",
                command="python -m unittest tests.test_cortex_kernel",
                status="passed",
                passed=["Cortex kernel state, rule registry, and proof summary examples load from explicit runtime artifacts."],
                failed=[],
                known_debt=[],
                owner_layer="cortex",
                next_required_layer="cortex",
                receipt_ready=True,
            ),
            touched_files=[
                "ops/cortex/kernel.py",
                "tests/test_cortex_kernel.py",
            ],
            owner_layer="cortex",
            next_required_layer="cortex",
            boundary_status="clean",
        )

        self.assertEqual("Cortex proof receipt draft: cortex-kernel-schema-clean", payload["receipt_title"])
        self.assertEqual("cortex", payload["owner_layer"])
        self.assertTrue(payload["receipt_ready"])
        self.assertEqual([], payload["known_debt"]["ambient_debt"])
        self.assertEqual("Promote this draft into the cortex receipt handoff.", payload["next_action"])

    def test_fitness_verification_passed_is_receipt_ready_only_when_boundary_is_clean(self) -> None:
        clean_payload = _build_draft(
            proof_summary=_summary(
                proof_id="fitness-verify-clean",
                command="python -m unittest tests.test_atlas_ui_proof_summary",
                status="passed",
                passed=["Fitness proof summary classification stays completion-ready when semantic and visual proof are both clean."],
                failed=[],
                known_debt=[],
                owner_layer="fitness",
                next_required_layer="cortex",
                receipt_ready=True,
            ),
            touched_files=[
                "tests/test_atlas_ui_proof_summary.py",
                "ops/atlas/ui_proof/fitness.py",
            ],
            owner_layer="fitness",
            next_required_layer="cortex",
            boundary_status="clean",
        )
        dirty_payload = _build_draft(
            proof_summary=_summary(
                proof_id="fitness-verify-dirty",
                command="python -m unittest tests.test_atlas_ui_proof_summary",
                status="passed",
                passed=["Fitness proof summary classification stays completion-ready when semantic and visual proof are both clean."],
                failed=[],
                known_debt=[],
                owner_layer="fitness",
                next_required_layer="cortex",
                receipt_ready=True,
            ),
            touched_files=[
                "tests/test_atlas_ui_proof_summary.py",
                "ops/atlas/ui_proof/fitness.py",
            ],
            owner_layer="fitness",
            next_required_layer="cortex",
            boundary_status="dirty",
        )

        self.assertTrue(clean_payload["receipt_ready"])
        self.assertFalse(dirty_payload["receipt_ready"])
        self.assertIn("dirty", str(dirty_payload["boundary_statement"]))

    def test_atlas_cortex_unittest_proof_passed_is_receipt_ready(self) -> None:
        payload = _build_draft(
            proof_summary=_summary(
                proof_id="atlas-cortex-unittest-proof",
                command="python -m unittest tests.test_atlas_ui_proof_summary",
                status="passed",
                passed=["ATLAS/Cortex proof surface passed its unittest proof."],
                failed=[],
                known_debt=[],
                owner_layer="atlas",
                next_required_layer="cortex",
                receipt_ready=True,
            ),
            touched_files=[
                "tests/test_atlas_ui_proof_summary.py",
                "ops/atlas/ui_proof/fitness.py",
            ],
            owner_layer="atlas",
            next_required_layer="cortex",
            boundary_status="clean",
        )

        self.assertTrue(payload["receipt_ready"])
        self.assertEqual("atlas", payload["owner_layer"])
        self.assertIn("Promote this draft", str(payload["next_action"]))

    def test_stack_validation_known_ambient_debt_is_not_treated_as_current_regression(self) -> None:
        payload = _build_draft(
            proof_summary=_summary(
                proof_id="stack-validation-known-debt",
                command="python .\\ops\\validation\\validate_stack.py",
                status="completed_with_known_debt",
                passed=["Stack validation completed and exercised the stack-level path policy."],
                failed=[],
                known_debt=["Existing stack debt remained present before and after the Cortex tranche."],
                owner_layer="stack",
                next_required_layer="cortex",
                receipt_ready=False,
            ),
            touched_files=[
                "stack.yaml",
                "ops/validation/validate_stack.py",
            ],
            owner_layer="stack",
            next_required_layer="cortex",
            ambient_debt=["Existing stack debt remained present before and after the Cortex tranche."],
            boundary_status="clean",
        )

        self.assertFalse(payload["receipt_ready"])
        self.assertEqual([], payload["known_debt"]["current_validation_debt"])
        self.assertEqual(
            ["Existing stack debt remained present before and after the Cortex tranche."],
            payload["known_debt"]["ambient_debt"],
        )
        self.assertIn("ambient debt", str(payload["boundary_statement"]))

    def test_current_tranche_command_failure_blocks_receipt_ready(self) -> None:
        payload = _build_draft(
            proof_summary=_summary(
                proof_id="cortex-runtime-regression",
                command="python -m unittest tests.test_cortex_kernel",
                status="failed",
                passed=[],
                failed=["tests.test_cortex_kernel.CortexKernelTests.test_proof_example_round_trip_keeps_flattened_shape"],
                known_debt=[],
                owner_layer="cortex",
                next_required_layer="cortex",
                receipt_ready=False,
            ),
            touched_files=[
                "ops/cortex/kernel.py",
                "tests/test_cortex_kernel.py",
            ],
            owner_layer="cortex",
            next_required_layer="cortex",
            boundary_status="clean",
        )

        self.assertFalse(payload["receipt_ready"])
        self.assertEqual(
            ["tests.test_cortex_kernel.CortexKernelTests.test_proof_example_round_trip_keeps_flattened_shape"],
            payload["failed_commands"],
        )
        self.assertIn("command failure", str(payload["next_action"]))

    def test_unknown_validation_debt_is_represented_separately_from_ambient_debt(self) -> None:
        payload = _build_draft(
            proof_summary=_summary(
                proof_id="mixed-known-and-new-validation-debt",
                command="python -m unittest tests.test_cortex_proof_receipt",
                status="completed_with_known_debt",
                passed=["Proof receipt draft builder stayed deterministic."],
                failed=[],
                known_debt=[
                    "Existing stack debt remained present before and after the Cortex tranche.",
                    "New owner-boundary validation gap introduced by this tranche.",
                ],
                owner_layer="cortex",
                next_required_layer="cortex",
                receipt_ready=False,
            ),
            touched_files=[
                "ops/cortex/proof_receipt.py",
                "tests/test_cortex_proof_receipt.py",
            ],
            owner_layer="cortex",
            next_required_layer="cortex",
            ambient_debt=["Existing stack debt remained present before and after the Cortex tranche."],
            current_validation_debt=["New owner-boundary validation gap introduced by this tranche."],
            boundary_status="clean",
        )

        self.assertEqual(
            ["Existing stack debt remained present before and after the Cortex tranche."],
            payload["known_debt"]["ambient_debt"],
        )
        self.assertEqual(
            ["New owner-boundary validation gap introduced by this tranche."],
            payload["known_debt"]["current_validation_debt"],
        )
        self.assertFalse(payload["receipt_ready"])


if __name__ == "__main__":
    unittest.main()
