from __future__ import annotations

import unittest

from ops.atlas.pilot_selection_criteria import evaluate_pilot_selection_criteria


def _base_card() -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": "repos/example/.worktrees/pilot-a",
        "objective_summary": "Land one bounded root-local pilot criteria validator.",
        "allowed_write_scope": "ops/atlas/pilot_selection_criteria.py and tests/test_atlas_pilot_selection_criteria.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_selection_criteria -v",
        "closeout_artifact": "docs/ops/reconciliation.md",
        "park_or_escalation_rule": "stop if repo discovery or candidate comparison is required",
        "protected_surface_exclusions": [
            "deploy",
            "publication",
            "archive_delete",
            "env_mutation",
            "secret_mutation",
        ],
    }


class PilotSelectionCriteriaTests(unittest.TestCase):
    def test_complete_bounded_single_owner_card_is_admissible(self) -> None:
        payload = evaluate_pilot_selection_criteria(_base_card())

        self.assertEqual("admissible", payload["status"])
        self.assertEqual([], payload["rejection_reasons"])

    def test_owner_repo_count_not_one_is_rejected(self) -> None:
        card = _base_card()
        card["owner_repo_count"] = 2

        payload = evaluate_pilot_selection_criteria(card)

        self.assertEqual("not_admissible", payload["status"])
        self.assertEqual(["owner_repo_count_not_one"], payload["rejection_reasons"])

    def test_target_must_be_explicit(self) -> None:
        card = _base_card()
        card["target_ref"] = "   "

        payload = evaluate_pilot_selection_criteria(card)

        self.assertEqual("not_admissible", payload["status"])
        self.assertIn("target_not_explicit", payload["rejection_reasons"])

    def test_missing_control_fields_fail_closed(self) -> None:
        card = _base_card()
        card["verification_gate"] = ""

        payload = evaluate_pilot_selection_criteria(card)

        self.assertEqual("not_admissible", payload["status"])
        self.assertEqual(["verification_gate_missing"], payload["rejection_reasons"])

    def test_missing_or_violated_protected_surface_boundary_is_rejected(self) -> None:
        missing_card = _base_card()
        missing_card["protected_surface_exclusions"] = ["deploy", "publication"]

        missing_payload = evaluate_pilot_selection_criteria(missing_card)

        self.assertEqual("not_admissible", missing_payload["status"])
        self.assertEqual(["protected_surface_exclusions_missing"], missing_payload["rejection_reasons"])

        violated_card = _base_card()
        violated_card["allowed_write_scope"] = "docs-only plus deploy preparation"

        violated_payload = evaluate_pilot_selection_criteria(violated_card)

        self.assertEqual("not_admissible", violated_payload["status"])
        self.assertEqual(["protected_surface_violation"], violated_payload["rejection_reasons"])

    def test_extra_candidate_comparison_fields_do_not_widen_output(self) -> None:
        card = _base_card()
        card["candidate_options"] = ["repo-a", "repo-b"]

        payload = evaluate_pilot_selection_criteria(card)

        self.assertEqual("admissible", payload["status"])
        self.assertNotIn("candidate_options", payload)


if __name__ == "__main__":
    unittest.main()
