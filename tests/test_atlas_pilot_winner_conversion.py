from __future__ import annotations

import unittest

from ops.atlas.pilot_winner_conversion import evaluate_pilot_winner_conversion


def _base_candidate(target_ref: str) -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local pilot winner conversion helper.",
        "allowed_write_scope": "ops/atlas/pilot_winner_conversion.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_winner_conversion -v",
        "closeout_artifact": "docs/ops/reconciliation.md",
        "park_or_escalation_rule": "stop and escalate if repo discovery or execution-home choice is required",
        "protected_surface_exclusions": [
            "deploy",
            "publication",
            "archive_delete",
            "env_mutation",
            "secret_mutation",
        ],
    }


def _base_bundle() -> dict[str, object]:
    return {
        "candidate_a": _base_candidate("repos/example/.worktrees/pilot-a"),
        "candidate_b": _base_candidate("repos/example/.worktrees/pilot-b"),
        "comparison_outcome": "candidate_a_preferred",
        "comparison_reasons": [],
    }


class PilotWinnerConversionTests(unittest.TestCase):
    def test_candidate_a_preferred_selects_explicit_candidate_a(self) -> None:
        payload = evaluate_pilot_winner_conversion(_base_bundle())

        self.assertEqual("winner_selected", payload["conversion_status"])
        self.assertEqual(payload["candidate_a"], payload["pilot_winner"])
        self.assertEqual([], payload["conversion_reasons"])

    def test_candidate_b_preferred_selects_explicit_candidate_b(self) -> None:
        bundle = _base_bundle()
        bundle["comparison_outcome"] = "candidate_b_preferred"

        payload = evaluate_pilot_winner_conversion(bundle)

        self.assertEqual("winner_selected", payload["conversion_status"])
        self.assertEqual(payload["candidate_b"], payload["pilot_winner"])
        self.assertEqual([], payload["conversion_reasons"])

    def test_tie_fails_closed_without_winner(self) -> None:
        bundle = _base_bundle()
        bundle["comparison_outcome"] = "tie"

        payload = evaluate_pilot_winner_conversion(bundle)

        self.assertEqual("no_winner", payload["conversion_status"])
        self.assertIsNone(payload["pilot_winner"])
        self.assertEqual(["comparison_outcome_not_preferred"], payload["conversion_reasons"])

    def test_not_comparable_fails_closed_without_winner(self) -> None:
        bundle = _base_bundle()
        bundle["comparison_outcome"] = "not_comparable"

        payload = evaluate_pilot_winner_conversion(bundle)

        self.assertEqual("no_winner", payload["conversion_status"])
        self.assertIsNone(payload["pilot_winner"])
        self.assertEqual(["comparison_outcome_not_preferred"], payload["conversion_reasons"])

    def test_non_empty_comparison_reasons_fail_closed(self) -> None:
        bundle = _base_bundle()
        bundle["comparison_reasons"] = ["candidate_fields_hidden"]

        payload = evaluate_pilot_winner_conversion(bundle)

        self.assertEqual("no_winner", payload["conversion_status"])
        self.assertIsNone(payload["pilot_winner"])
        self.assertEqual(["comparison_reasons_present"], payload["conversion_reasons"])
        self.assertEqual(["candidate_fields_hidden"], payload["comparison_reasons"])

    def test_preferred_candidate_missing_or_not_explicit_fails_closed(self) -> None:
        missing_bundle = _base_bundle()
        del missing_bundle["candidate_a"]

        missing_payload = evaluate_pilot_winner_conversion(missing_bundle)

        self.assertEqual("no_winner", missing_payload["conversion_status"])
        self.assertIsNone(missing_payload["pilot_winner"])
        self.assertEqual(["preferred_candidate_missing"], missing_payload["conversion_reasons"])

        not_explicit_bundle = _base_bundle()
        not_explicit_bundle["candidate_a"]["target_ref"] = ""

        not_explicit_payload = evaluate_pilot_winner_conversion(not_explicit_bundle)

        self.assertEqual("no_winner", not_explicit_payload["conversion_status"])
        self.assertIsNone(not_explicit_payload["pilot_winner"])
        self.assertEqual(["preferred_candidate_not_explicit"], not_explicit_payload["conversion_reasons"])

    def test_invented_tiebreaks_fail_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]
        repo_payload = evaluate_pilot_winner_conversion(repo_bundle)
        self.assertEqual("no_winner", repo_payload["conversion_status"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["conversion_reasons"])

        readiness_bundle = _base_bundle()
        readiness_bundle["owner_readiness_tiebreak"] = "release-ready"
        readiness_payload = evaluate_pilot_winner_conversion(readiness_bundle)
        self.assertEqual("no_winner", readiness_payload["conversion_status"])
        self.assertEqual(["owner_readiness_tiebreak_invented"], readiness_payload["conversion_reasons"])

        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home_tiebreak"] = "_stack"
        execution_home_payload = evaluate_pilot_winner_conversion(execution_home_bundle)
        self.assertEqual("no_winner", execution_home_payload["conversion_status"])
        self.assertEqual(["execution_home_tiebreak_invented"], execution_home_payload["conversion_reasons"])

    def test_protected_surface_violation_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["candidate_a"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        payload = evaluate_pilot_winner_conversion(bundle)

        self.assertEqual("no_winner", payload["conversion_status"])
        self.assertIsNone(payload["pilot_winner"])
        self.assertEqual(["protected_surface_violation"], payload["conversion_reasons"])


if __name__ == "__main__":
    unittest.main()
