from __future__ import annotations

import unittest

from ops.atlas.pilot_selected_actual_owner_side_mutation import (
    evaluate_pilot_selected_actual_owner_side_mutation,
)


def _base_owner_repo_mutation(target_ref: str) -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local selected-pilot actual owner-side mutation helper.",
        "allowed_write_scope": "ops/atlas/pilot_selected_actual_owner_side_mutation.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_selected_actual_owner_side_mutation -v",
        "closeout_artifact": "docs/ops/reconciliation.md",
        "park_or_escalation_rule": "stop and escalate if actual owner-side mutation authority is required",
        "protected_surface_exclusions": [
            "deploy",
            "publication",
            "archive_delete",
            "env_mutation",
            "secret_mutation",
        ],
    }


def _base_bundle() -> dict[str, object]:
    mutation_card = _base_owner_repo_mutation("repos/example/.worktrees/pilot-a")
    return {
        "selection_status": "pilot_selected",
        "selection_reasons": [],
        "routing_status": "implementation_route_admissible",
        "implementation_route": mutation_card,
        "routing_reasons": [],
        "implementation_status": "owner_repo_implementation_admissible",
        "owner_repo_implementation": mutation_card,
        "implementation_reasons": [],
        "mutation_status": "owner_repo_mutation_admissible",
        "owner_repo_mutation": mutation_card,
        "mutation_reasons": [],
    }


class PilotSelectedActualOwnerSideMutationTests(unittest.TestCase):
    def test_explicit_owner_repo_mutation_routes_admissibly(self) -> None:
        payload = evaluate_pilot_selected_actual_owner_side_mutation(_base_bundle())

        self.assertEqual("pilot_selected", payload["selection_status"])
        self.assertEqual("owner_repo_mutation_admissible", payload["mutation_status"])
        self.assertEqual("actual_owner_side_mutation_admissible", payload["actual_mutation_status"])
        self.assertEqual(payload["owner_repo_mutation"], payload["actual_owner_side_mutation"])
        self.assertEqual([], payload["actual_mutation_reasons"])

    def test_non_admissible_mutation_status_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["mutation_status"] = "no_owner_repo_mutation"
        bundle["owner_repo_mutation"] = None

        payload = evaluate_pilot_selected_actual_owner_side_mutation(bundle)

        self.assertEqual("no_owner_repo_mutation", payload["mutation_status"])
        self.assertEqual("no_actual_owner_side_mutation", payload["actual_mutation_status"])
        self.assertIsNone(payload["actual_owner_side_mutation"])
        self.assertEqual(
            ["mutation_status_not_owner_repo_mutation_admissible"],
            payload["actual_mutation_reasons"],
        )

    def test_non_empty_mutation_reasons_fail_closed(self) -> None:
        bundle = _base_bundle()
        bundle["mutation_reasons"] = ["implementation_reasons_present"]

        payload = evaluate_pilot_selected_actual_owner_side_mutation(bundle)

        self.assertEqual("owner_repo_mutation_admissible", payload["mutation_status"])
        self.assertEqual("no_actual_owner_side_mutation", payload["actual_mutation_status"])
        self.assertIsNone(payload["actual_owner_side_mutation"])
        self.assertEqual(["mutation_reasons_present"], payload["actual_mutation_reasons"])
        self.assertEqual(["implementation_reasons_present"], payload["mutation_reasons"])

    def test_missing_or_non_explicit_owner_repo_mutation_fails_closed(self) -> None:
        missing_bundle = _base_bundle()
        del missing_bundle["owner_repo_mutation"]

        missing_payload = evaluate_pilot_selected_actual_owner_side_mutation(missing_bundle)

        self.assertEqual("no_actual_owner_side_mutation", missing_payload["actual_mutation_status"])
        self.assertIsNone(missing_payload["actual_owner_side_mutation"])
        self.assertEqual(["owner_repo_mutation_missing"], missing_payload["actual_mutation_reasons"])

        not_explicit_bundle = _base_bundle()
        not_explicit_bundle["owner_repo_mutation"] = "pilot-a"

        not_explicit_payload = evaluate_pilot_selected_actual_owner_side_mutation(not_explicit_bundle)

        self.assertEqual("no_actual_owner_side_mutation", not_explicit_payload["actual_mutation_status"])
        self.assertIsNone(not_explicit_payload["actual_owner_side_mutation"])
        self.assertEqual(
            ["owner_repo_mutation_not_explicit"],
            not_explicit_payload["actual_mutation_reasons"],
        )

    def test_protected_surface_violation_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["owner_repo_mutation"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        payload = evaluate_pilot_selected_actual_owner_side_mutation(bundle)

        self.assertEqual("no_actual_owner_side_mutation", payload["actual_mutation_status"])
        self.assertIsNone(payload["actual_owner_side_mutation"])
        self.assertEqual(["protected_surface_violation"], payload["actual_mutation_reasons"])

    def test_repo_discovery_or_branch_worktree_enumeration_fails_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]

        repo_payload = evaluate_pilot_selected_actual_owner_side_mutation(repo_bundle)

        self.assertEqual("no_actual_owner_side_mutation", repo_payload["actual_mutation_status"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["actual_mutation_reasons"])

        branch_bundle = _base_bundle()
        branch_bundle["worktree_inventory"] = ["repos/example/.worktrees/pilot-a"]

        branch_payload = evaluate_pilot_selected_actual_owner_side_mutation(branch_bundle)

        self.assertEqual("no_actual_owner_side_mutation", branch_payload["actual_mutation_status"])
        self.assertEqual(["branch_worktree_enumeration_invented"], branch_payload["actual_mutation_reasons"])

    def test_execution_home_or_actual_mutation_authority_fails_closed(self) -> None:
        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home"] = "_stack"

        execution_home_payload = evaluate_pilot_selected_actual_owner_side_mutation(execution_home_bundle)

        self.assertEqual("no_actual_owner_side_mutation", execution_home_payload["actual_mutation_status"])
        self.assertEqual(["execution_home_inference_invented"], execution_home_payload["actual_mutation_reasons"])

        mutation_bundle = _base_bundle()
        mutation_bundle["actual_owner_side_mutation_authority"] = True

        mutation_payload = evaluate_pilot_selected_actual_owner_side_mutation(mutation_bundle)

        self.assertEqual("no_actual_owner_side_mutation", mutation_payload["actual_mutation_status"])
        self.assertEqual(
            ["actual_owner_side_mutation_authority_invented"],
            mutation_payload["actual_mutation_reasons"],
        )

    def test_playbook_doctrine_export_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["playbook_doctrine_export"] = True

        payload = evaluate_pilot_selected_actual_owner_side_mutation(bundle)

        self.assertEqual("no_actual_owner_side_mutation", payload["actual_mutation_status"])
        self.assertEqual(["playbook_doctrine_export_invented"], payload["actual_mutation_reasons"])


if __name__ == "__main__":
    unittest.main()
