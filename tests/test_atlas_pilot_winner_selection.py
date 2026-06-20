from __future__ import annotations

import unittest

from ops.atlas.pilot_winner_selection import evaluate_pilot_winner_selection


def _base_candidate(target_ref: str) -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local pilot winner selection helper.",
        "allowed_write_scope": "ops/atlas/pilot_winner_selection.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_winner_selection -v",
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
        "conversion_status": "winner_selected",
        "pilot_winner": _base_candidate("repos/example/.worktrees/pilot-a"),
        "conversion_reasons": [],
    }


class PilotWinnerSelectionTests(unittest.TestCase):
    def test_winner_selected_with_empty_conversion_reasons_selects_pilot(self) -> None:
        payload = evaluate_pilot_winner_selection(_base_bundle())

        self.assertEqual("pilot_selected", payload["selection_status"])
        self.assertEqual(payload["pilot_winner"], payload["selected_pilot"])
        self.assertEqual([], payload["selection_reasons"])

    def test_no_winner_status_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["conversion_status"] = "no_winner"
        bundle["pilot_winner"] = None

        payload = evaluate_pilot_winner_selection(bundle)

        self.assertEqual("no_selection", payload["selection_status"])
        self.assertIsNone(payload["selected_pilot"])
        self.assertEqual(["conversion_status_not_winner_selected"], payload["selection_reasons"])

    def test_non_empty_conversion_reasons_fail_closed(self) -> None:
        bundle = _base_bundle()
        bundle["conversion_reasons"] = ["comparison_reasons_present"]

        payload = evaluate_pilot_winner_selection(bundle)

        self.assertEqual("no_selection", payload["selection_status"])
        self.assertIsNone(payload["selected_pilot"])
        self.assertEqual(["conversion_reasons_present"], payload["selection_reasons"])
        self.assertEqual(["comparison_reasons_present"], payload["conversion_reasons"])

    def test_missing_or_non_explicit_pilot_winner_fails_closed(self) -> None:
        missing_bundle = _base_bundle()
        del missing_bundle["pilot_winner"]

        missing_payload = evaluate_pilot_winner_selection(missing_bundle)

        self.assertEqual("no_selection", missing_payload["selection_status"])
        self.assertIsNone(missing_payload["selected_pilot"])
        self.assertEqual(["pilot_winner_missing"], missing_payload["selection_reasons"])

        not_explicit_bundle = _base_bundle()
        not_explicit_bundle["pilot_winner"] = "pilot-a"

        not_explicit_payload = evaluate_pilot_winner_selection(not_explicit_bundle)

        self.assertEqual("no_selection", not_explicit_payload["selection_status"])
        self.assertIsNone(not_explicit_payload["selected_pilot"])
        self.assertEqual(["pilot_winner_not_explicit"], not_explicit_payload["selection_reasons"])

    def test_invented_repo_discovery_or_tiebreaks_fail_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]
        repo_payload = evaluate_pilot_winner_selection(repo_bundle)
        self.assertEqual("no_selection", repo_payload["selection_status"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["selection_reasons"])

        readiness_bundle = _base_bundle()
        readiness_bundle["owner_readiness_tiebreak"] = "release-ready"
        readiness_payload = evaluate_pilot_winner_selection(readiness_bundle)
        self.assertEqual("no_selection", readiness_payload["selection_status"])
        self.assertEqual(["owner_readiness_tiebreak_invented"], readiness_payload["selection_reasons"])

        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home_tiebreak"] = "_stack"
        execution_home_payload = evaluate_pilot_winner_selection(execution_home_bundle)
        self.assertEqual("no_selection", execution_home_payload["selection_status"])
        self.assertEqual(["execution_home_tiebreak_invented"], execution_home_payload["selection_reasons"])

    def test_owner_repo_mutation_or_worker_launch_authority_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["worker_launch_authority"] = True

        payload = evaluate_pilot_winner_selection(bundle)

        self.assertEqual("no_selection", payload["selection_status"])
        self.assertIsNone(payload["selected_pilot"])
        self.assertEqual(["owner_repo_mutation_invented"], payload["selection_reasons"])

    def test_protected_surface_violation_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["pilot_winner"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        payload = evaluate_pilot_winner_selection(bundle)

        self.assertEqual("no_selection", payload["selection_status"])
        self.assertIsNone(payload["selected_pilot"])
        self.assertEqual(["protected_surface_violation"], payload["selection_reasons"])


if __name__ == "__main__":
    unittest.main()
