from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.kernel import CortexProofSummary, VerificationResult
from ops.cortex.loop import CORTEX_RUN_RESULT_CONTRACT_VERSION, load_and_run_cortex_loop


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _failing_proof_summary() -> CortexProofSummary:
    return CortexProofSummary(
        proof_id="cortex-runtime-regression",
        command="python -m unittest tests.test_cortex_loop",
        verification=VerificationResult(
            status="failed",
            passed=(),
            failed=("tests.test_cortex_loop.CortexLoopTests.test_current_tranche_failure_blocks_receipt_ready",),
            known_debt=(),
            notes=(),
        ),
        touched_files=("ops/cortex/loop.py", "tests/test_cortex_loop.py"),
        owner_layer="cortex",
        next_required_layer="cortex",
        receipt_ready=False,
        evidence=("tests/test_cortex_loop.py",),
    )


class CortexLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.state_path = cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json"
        cls.rule_path = cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json"
        cls.proof_path = cls.root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json"

    def _state_payload(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _rule_payload(self) -> dict:
        return json.loads(self.rule_path.read_text(encoding="utf-8"))

    def _proof_payload(self) -> dict:
        return json.loads(self.proof_path.read_text(encoding="utf-8"))

    def _temp_root(self, state_payload: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self._rule_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.proof-summary.examples.v1.json", self._proof_payload())
        return root

    def test_priority_pivot_produces_cortex_runtime_run_result(self) -> None:
        result = load_and_run_cortex_loop(root=self.root)
        payload = result.to_payload()
        trace = payload["applied_rule_trace"]

        self.assertEqual(CORTEX_RUN_RESULT_CONTRACT_VERSION, payload["contract_version"])
        self.assertEqual("cortex", result.rail_state.next_layer)
        self.assertEqual("cortex", result.selected_next_action["owner_layer"])
        self.assertEqual("cortex", result.worker_plan.owner_layer)
        self.assertTrue(result.receipt_ready)
        self.assertEqual("cortex", result.next_required_layer)
        self.assertTrue(result.known_ambient_debt)
        self.assertIn("Rule", result.worker_plan.prompt)
        self.assertIn("Pattern", result.worker_plan.prompt)
        self.assertIn("Failure Mode", result.worker_plan.prompt)
        self.assertTrue(any(rule.kind == "failure_mode" for rule in result.rules_applied))
        self.assertEqual("promote-cortex-operator-surface-wave4", trace["selected_next_action_id"])
        self.assertIn("fitness-owner-adoption-resumes-unless-pivot", trace["pattern_ids"])
        self.assertIn("known-validation-debt-stays-ambient-unless-regression", trace["rule_ids"])
        self.assertIn("cortex-observes-interprets-proves-only", trace["failure_mode_ids"])
        self.assertIn(result.selected_next_action["rationale"], trace["why_selected"])
        json.dumps(payload, sort_keys=True)

    def test_fitness_and_atlas_alternation_still_work_when_pivot_is_inactive(self) -> None:
        atlas_to_fitness = self._state_payload()
        atlas_to_fitness["posture"]["classification"] = "steady"
        atlas_to_fitness["posture"]["summary"] = "The Cortex priority pivot is inactive."
        atlas_to_fitness["posture"]["rail_state"]["latest_clean_step"]["step_id"] = "atlas-cortex-catch-up"
        atlas_to_fitness["posture"]["rail_state"]["latest_clean_step"]["owner_layer"] = "atlas"
        atlas_to_fitness["posture"]["rail_state"]["next_action"]["owner_layer"] = "atlas"

        atlas_to_fitness_result = load_and_run_cortex_loop(root=self._temp_root(atlas_to_fitness))

        self.assertEqual("fitness", atlas_to_fitness_result.selected_next_action["owner_layer"])
        self.assertEqual("resume-fitness-owner-adoption", atlas_to_fitness_result.selected_next_action["action_id"])
        self.assertEqual("fitness_owner_adoption", atlas_to_fitness_result.worker_plan.template_id)
        self.assertEqual("fitness", atlas_to_fitness_result.proof_receipt_draft.owner_layer)
        self.assertIn(
            "fitness-owner-adoption-resumes-unless-pivot",
            atlas_to_fitness_result.applied_rule_trace.pattern_ids,
        )

        fitness_to_atlas = self._state_payload()
        fitness_to_atlas["posture"]["classification"] = "steady"
        fitness_to_atlas["posture"]["summary"] = "The Cortex priority pivot is inactive."
        fitness_to_atlas["posture"]["rail_state"]["owner_layer"] = "atlas"
        fitness_to_atlas["posture"]["rail_state"]["latest_clean_step"]["step_id"] = "fitness-owner-adoption"
        fitness_to_atlas["posture"]["rail_state"]["latest_clean_step"]["owner_layer"] = "fitness"
        fitness_to_atlas["posture"]["rail_state"]["next_action"]["owner_layer"] = "fitness"

        fitness_to_atlas_result = load_and_run_cortex_loop(root=self._temp_root(fitness_to_atlas))

        self.assertEqual("atlas", fitness_to_atlas_result.selected_next_action["owner_layer"])
        self.assertEqual("atlas-cortex-catch-up", fitness_to_atlas_result.selected_next_action["action_id"])
        self.assertEqual("atlas_cortex_catch_up", fitness_to_atlas_result.worker_plan.template_id)
        self.assertEqual("atlas", fitness_to_atlas_result.proof_receipt_draft.owner_layer)
        self.assertIn("footer-catch-up-precedes-pivot", fitness_to_atlas_result.applied_rule_trace.pattern_ids)

    def test_known_ambient_debt_does_not_block_receipt_readiness_when_targeted_verification_passes(self) -> None:
        result = load_and_run_cortex_loop(root=self.root)

        self.assertTrue(result.known_ambient_debt)
        self.assertTrue(result.receipt_ready)
        self.assertTrue(result.proof_receipt_draft.receipt_ready)
        self.assertEqual((), result.proof_receipt_draft.known_debt.ambient_debt)
        self.assertIn("known-validation-debt-stays-ambient-unless-regression", result.applied_rule_trace.rule_ids)

    def test_current_tranche_failure_blocks_receipt_ready(self) -> None:
        result = load_and_run_cortex_loop(root=self.root, proof_summary=_failing_proof_summary())

        self.assertFalse(result.receipt_ready)
        self.assertFalse(result.proof_receipt_draft.receipt_ready)
        self.assertEqual(
            ["tests.test_cortex_loop.CortexLoopTests.test_current_tranche_failure_blocks_receipt_ready"],
            list(result.proof_receipt_draft.failed_commands),
        )

    def test_unsupported_next_action_fails_clearly(self) -> None:
        state_payload = self._state_payload()
        state_payload["posture"]["classification"] = "steady"
        state_payload["posture"]["rail_state"]["next_action"]["action_id"] = "open-connector-work"
        state_payload["posture"]["rail_state"]["next_action"]["owner_layer"] = "connector"
        state_payload["posture"]["rail_state"]["next_action"]["title"] = "Open connector work."
        state_payload["posture"]["rail_state"]["next_action"]["rationale"] = "Connectors are intentionally out of scope."
        state_payload["posture"]["rail_state"]["latest_clean_step"]["owner_layer"] = "connector"

        with self.assertRaisesRegex(ValueError, "Unsupported Cortex NextAction"):
            load_and_run_cortex_loop(root=self._temp_root(state_payload))


if __name__ == "__main__":
    unittest.main()
