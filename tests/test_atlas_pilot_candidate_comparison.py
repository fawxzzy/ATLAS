from __future__ import annotations

import unittest

from ops.atlas.pilot_candidate_comparison import evaluate_pilot_candidate_comparison


def _base_candidate() -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": "repos/example/.worktrees/pilot-a",
        "objective_summary": "Land one bounded root-local pilot comparison helper.",
        "allowed_write_scope": "ops/atlas/pilot_candidate_comparison.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_candidate_comparison -v",
        "closeout_artifact": "docs/ops/reconciliation.md",
        "park_or_escalation_rule": "stop and escalate if execution-home or repo discovery is required",
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
        "candidate_a": _base_candidate(),
        "candidate_b": _base_candidate(),
    }


class PilotCandidateComparisonTests(unittest.TestCase):
    def test_candidate_a_preferred_when_scope_is_narrower(self) -> None:
        bundle = _base_bundle()
        bundle["candidate_b"]["allowed_write_scope"] = (
            "ops/atlas/pilot_candidate_comparison.py and tests/test_atlas_pilot_candidate_comparison.py"
        )

        payload = evaluate_pilot_candidate_comparison(bundle)

        self.assertEqual("candidate_a_preferred", payload["comparison_outcome"])
        self.assertEqual([], payload["comparison_reasons"])

    def test_candidate_b_preferred_when_proof_surfaces_are_cleaner(self) -> None:
        bundle = _base_bundle()
        bundle["candidate_a"]["checkpoint_surface"] = "manual note later"
        bundle["candidate_a"]["verification_gate"] = "review manually when available"
        bundle["candidate_b"]["checkpoint_surface"] = "docs/ops/checkpoint.md"
        bundle["candidate_b"]["verification_gate"] = (
            "python -m unittest tests.test_atlas_pilot_candidate_comparison -v"
        )

        payload = evaluate_pilot_candidate_comparison(bundle)

        self.assertEqual("candidate_b_preferred", payload["comparison_outcome"])
        self.assertEqual([], payload["comparison_reasons"])

    def test_materially_equal_candidates_tie(self) -> None:
        payload = evaluate_pilot_candidate_comparison(_base_bundle())

        self.assertEqual("tie", payload["comparison_outcome"])
        self.assertEqual([], payload["comparison_reasons"])

    def test_candidate_specific_criteria_failure_is_not_comparable(self) -> None:
        bundle = _base_bundle()
        bundle["candidate_a"]["owner_repo_count"] = 2

        payload = evaluate_pilot_candidate_comparison(bundle)

        self.assertEqual("not_comparable", payload["comparison_outcome"])
        self.assertEqual(["candidate_a_not_criteria_admissible"], payload["comparison_reasons"])
        self.assertEqual("not_admissible", payload["candidate_a"]["criteria_status"])

    def test_hidden_fields_and_protected_surface_violation_fail_closed(self) -> None:
        hidden_bundle = _base_bundle()
        del hidden_bundle["candidate_a"]["checkpoint_surface"]

        hidden_payload = evaluate_pilot_candidate_comparison(hidden_bundle)

        self.assertEqual("not_comparable", hidden_payload["comparison_outcome"])
        self.assertEqual(["candidate_fields_hidden"], hidden_payload["comparison_reasons"])

        protected_bundle = _base_bundle()
        protected_bundle["candidate_b"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        protected_payload = evaluate_pilot_candidate_comparison(protected_bundle)

        self.assertEqual("not_comparable", protected_payload["comparison_outcome"])
        self.assertEqual(["protected_surface_violation"], protected_payload["comparison_reasons"])

    def test_repo_discovery_and_execution_home_tiebreak_fail_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]

        repo_payload = evaluate_pilot_candidate_comparison(repo_bundle)

        self.assertEqual("not_comparable", repo_payload["comparison_outcome"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["comparison_reasons"])

        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home_tiebreak"] = "_stack"

        execution_home_payload = evaluate_pilot_candidate_comparison(execution_home_bundle)

        self.assertEqual("not_comparable", execution_home_payload["comparison_outcome"])
        self.assertEqual(["execution_home_tiebreak_invented"], execution_home_payload["comparison_reasons"])

    def test_no_winner_conversion_boundary_is_preserved(self) -> None:
        bundle = _base_bundle()
        bundle["candidate_b"]["allowed_write_scope"] = (
            "ops/atlas/pilot_candidate_comparison.py and tests/test_atlas_pilot_candidate_comparison.py"
        )
        bundle["pilot_winner"] = "candidate_b"

        payload = evaluate_pilot_candidate_comparison(bundle)

        self.assertEqual("candidate_a_preferred", payload["comparison_outcome"])
        self.assertNotIn("pilot_winner", payload)
        self.assertEqual(
            {
                "candidate_a",
                "candidate_b",
                "comparison_outcome",
                "comparison_reasons",
            },
            set(payload),
        )
        self.assertEqual(
            {
                "criteria_status",
                "allowed_write_scope",
                "checkpoint_surface",
                "verification_gate",
                "closeout_artifact",
                "park_or_escalation_rule",
                "protected_surface_exclusions",
            },
            set(payload["candidate_a"]),
        )


if __name__ == "__main__":
    unittest.main()
