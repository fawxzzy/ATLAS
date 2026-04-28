from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.rail_state import (
    FOOTER_CATCH_UP_PATTERN_ID,
    KNOWN_DEBT_VERIFICATION_STATUS,
    KNOWN_DEBT_RULE_ID,
    PIVOT_OVERRIDE_RULE_ID,
    load_and_classify_rail_state,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexRailStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()

    def test_priority_pivot_keeps_next_action_in_cortex(self) -> None:
        assessment = load_and_classify_rail_state(root=self.root)
        self.assertEqual("cortex", assessment.priority_owner_layer)
        self.assertEqual("cortex", assessment.next_layer)
        self.assertEqual("cortex", assessment.next_action.owner_layer)
        self.assertIn(PIVOT_OVERRIDE_RULE_ID, assessment.matched_rule_ids)
        self.assertIn(KNOWN_DEBT_RULE_ID, assessment.matched_rule_ids)

    def test_known_stack_validation_debt_is_preserved_without_blocking_progress(self) -> None:
        assessment = load_and_classify_rail_state(root=self.root)
        self.assertEqual(KNOWN_DEBT_VERIFICATION_STATUS, assessment.verification_status)
        self.assertTrue(assessment.known_validation_debt)
        self.assertTrue(assessment.safe_to_proceed)

    def test_non_pivoted_rail_returns_to_fitness_after_atlas_catch_up(self) -> None:
        state_payload = json.loads(
            (self.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        state_payload["posture"]["classification"] = "steady"
        state_payload["posture"]["summary"] = "The Cortex priority pivot is inactive."
        state_payload["posture"]["rail_state"]["latest_clean_step"]["step_id"] = "footer-owner-atlas-cortex-catch-up"
        state_payload["posture"]["rail_state"]["latest_clean_step"]["owner_layer"] = "atlas"
        state_payload["posture"]["rail_state"]["next_action"]["owner_layer"] = "atlas"

        rule_payload = json.loads(
            (self.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", state_payload)
            _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", rule_payload)

            assessment = load_and_classify_rail_state(root=root)

        self.assertEqual("fitness", assessment.priority_owner_layer)
        self.assertEqual("fitness", assessment.next_layer)
        self.assertEqual("fitness", assessment.next_action.owner_layer)
        self.assertEqual("resume-fitness-owner-adoption", assessment.next_action.action_id)
        self.assertIn(PIVOT_OVERRIDE_RULE_ID, assessment.matched_rule_ids)

    def test_non_pivoted_rail_returns_to_atlas_after_fitness_step(self) -> None:
        state_payload = json.loads(
            (self.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        state_payload["posture"]["classification"] = "steady"
        state_payload["posture"]["summary"] = "The Cortex priority pivot is inactive."
        state_payload["posture"]["rail_state"]["owner_layer"] = "atlas"
        state_payload["posture"]["rail_state"]["latest_clean_step"]["step_id"] = "fitness-owner-adoption"
        state_payload["posture"]["rail_state"]["latest_clean_step"]["owner_layer"] = "fitness"
        state_payload["posture"]["rail_state"]["next_action"]["owner_layer"] = "fitness"

        rule_payload = json.loads(
            (self.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", state_payload)
            _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", rule_payload)

            assessment = load_and_classify_rail_state(root=root)

        self.assertEqual("atlas", assessment.priority_owner_layer)
        self.assertEqual("atlas", assessment.next_layer)
        self.assertEqual("atlas", assessment.next_action.owner_layer)
        self.assertEqual("atlas-cortex-catch-up", assessment.next_action.action_id)
        self.assertIn(FOOTER_CATCH_UP_PATTERN_ID, assessment.matched_rule_ids)

    def test_missing_state_seed_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(FileNotFoundError, "Cortex state model seed not found"):
                load_and_classify_rail_state(root=root)

    def test_invalid_rule_registry_fails_clearly(self) -> None:
        state_payload = json.loads(
            (self.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        invalid_rules = {
            "contract_version": "atlas.cortex.rule-registry.v1",
            "rules": [{"id": "broken-rule", "kind": "unsupported"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", state_payload)
            _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", invalid_rules)

            with self.assertRaisesRegex(ValueError, "Invalid Cortex rule registry seed"):
                load_and_classify_rail_state(root=root)


if __name__ == "__main__":
    unittest.main()
