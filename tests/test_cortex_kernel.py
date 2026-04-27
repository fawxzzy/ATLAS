from __future__ import annotations

import unittest

from ops._atlas import atlas_root
from ops.cortex._artifacts import read_json
from ops.cortex.kernel import (
    CortexProofSummary,
    KERNEL_STATE_CONTRACT_VERSION,
    PROOF_SUMMARY_EXAMPLES_CONTRACT_VERSION,
    RULE_KINDS,
    RULE_REGISTRY_CONTRACT_VERSION,
    default_proof_summary_examples_path,
    default_rule_registry_path,
    default_state_model_path,
    load_kernel_state_model,
    load_proof_summary_examples,
    load_rule_registry,
)


class CortexKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()

    def test_state_model_seed_round_trips_through_loader(self) -> None:
        path = default_state_model_path(self.root)
        payload = read_json(path)
        self.assertEqual(KERNEL_STATE_CONTRACT_VERSION, payload["contract_version"])
        posture = load_kernel_state_model(root=self.root)
        self.assertEqual("pivoted", posture.classification)
        self.assertEqual("cortex-mvp", posture.rail_state.rail_id)
        self.assertEqual(
            "footer-owner-atlas-cortex-catch-up",
            posture.rail_state.latest_clean_step.step_id,
        )
        self.assertIn(
            "handoff summaries",
            posture.rail_state.next_action.required_inputs,
        )
        self.assertEqual(posture, load_kernel_state_model(path=path))

    def test_rule_registry_seed_uses_supported_compact_kinds(self) -> None:
        path = default_rule_registry_path(self.root)
        payload = read_json(path)
        self.assertEqual(RULE_REGISTRY_CONTRACT_VERSION, payload["contract_version"])
        rules = load_rule_registry(root=self.root)
        self.assertGreaterEqual(len(rules), 8)
        self.assertEqual(len(rules), len({item.rule_id for item in rules}))
        self.assertTrue({item.kind for item in rules}.issubset(RULE_KINDS))
        self.assertEqual(RULE_KINDS, {item.kind for item in rules})

    def test_proof_examples_preserve_known_debt_without_marking_failure(self) -> None:
        path = default_proof_summary_examples_path(self.root)
        payload = read_json(path)
        self.assertEqual(
            PROOF_SUMMARY_EXAMPLES_CONTRACT_VERSION,
            payload["contract_version"],
        )
        examples = load_proof_summary_examples(root=self.root)
        by_id = {item.proof_id: item for item in examples}
        stack_validation = by_id["stack-validation-known-debt"]
        self.assertEqual(
            "completed_with_known_debt",
            stack_validation.verification.status,
        )
        self.assertEqual((), stack_validation.verification.failed)
        self.assertTrue(stack_validation.verification.known_debt)
        self.assertFalse(stack_validation.receipt_ready)

    def test_proof_example_round_trip_keeps_flattened_shape(self) -> None:
        example = load_proof_summary_examples(root=self.root)[1]
        payload = example.to_payload()
        reloaded = CortexProofSummary.from_payload(payload)
        self.assertEqual(example, reloaded)


if __name__ == "__main__":
    unittest.main()
