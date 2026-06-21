from __future__ import annotations

import unittest

from ops.atlas.pilot_selected_owner_repo_mutation import evaluate_pilot_selected_owner_repo_mutation


def _base_owner_repo_implementation(target_ref: str) -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local selected-pilot owner-repo mutation helper.",
        "allowed_write_scope": "ops/atlas/pilot_selected_owner_repo_mutation.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_selected_owner_repo_mutation -v",
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
        "selection_status": "pilot_selected",
        "selection_reasons": [],
        "routing_status": "implementation_route_admissible",
        "implementation_route": _base_owner_repo_implementation("repos/example/.worktrees/pilot-a"),
        "routing_reasons": [],
        "implementation_status": "owner_repo_implementation_admissible",
        "owner_repo_implementation": _base_owner_repo_implementation("repos/example/.worktrees/pilot-a"),
        "implementation_reasons": [],
    }


class PilotSelectedOwnerRepoMutationTests(unittest.TestCase):
    def test_explicit_owner_repo_implementation_routes_admissibly(self) -> None:
        payload = evaluate_pilot_selected_owner_repo_mutation(_base_bundle())

        self.assertEqual("pilot_selected", payload["selection_status"])
        self.assertEqual("owner_repo_implementation_admissible", payload["implementation_status"])
        self.assertEqual("owner_repo_mutation_admissible", payload["mutation_status"])
        self.assertEqual(payload["owner_repo_implementation"], payload["owner_repo_mutation"])
        self.assertEqual([], payload["mutation_reasons"])

    def test_non_admissible_implementation_status_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["implementation_status"] = "no_owner_repo_implementation"
        bundle["owner_repo_implementation"] = None

        payload = evaluate_pilot_selected_owner_repo_mutation(bundle)

        self.assertEqual("no_owner_repo_implementation", payload["implementation_status"])
        self.assertEqual("no_owner_repo_mutation", payload["mutation_status"])
        self.assertIsNone(payload["owner_repo_mutation"])
        self.assertEqual(
            ["implementation_status_not_owner_repo_implementation_admissible"],
            payload["mutation_reasons"],
        )

    def test_non_empty_implementation_reasons_fail_closed(self) -> None:
        bundle = _base_bundle()
        bundle["implementation_reasons"] = ["routing_reasons_present"]

        payload = evaluate_pilot_selected_owner_repo_mutation(bundle)

        self.assertEqual("owner_repo_implementation_admissible", payload["implementation_status"])
        self.assertEqual("no_owner_repo_mutation", payload["mutation_status"])
        self.assertIsNone(payload["owner_repo_mutation"])
        self.assertEqual(["implementation_reasons_present"], payload["mutation_reasons"])
        self.assertEqual(["routing_reasons_present"], payload["implementation_reasons"])

    def test_missing_or_non_explicit_owner_repo_implementation_fails_closed(self) -> None:
        missing_bundle = _base_bundle()
        del missing_bundle["owner_repo_implementation"]

        missing_payload = evaluate_pilot_selected_owner_repo_mutation(missing_bundle)

        self.assertEqual("no_owner_repo_mutation", missing_payload["mutation_status"])
        self.assertIsNone(missing_payload["owner_repo_mutation"])
        self.assertEqual(["owner_repo_implementation_missing"], missing_payload["mutation_reasons"])

        not_explicit_bundle = _base_bundle()
        not_explicit_bundle["owner_repo_implementation"] = "pilot-a"

        not_explicit_payload = evaluate_pilot_selected_owner_repo_mutation(not_explicit_bundle)

        self.assertEqual("no_owner_repo_mutation", not_explicit_payload["mutation_status"])
        self.assertIsNone(not_explicit_payload["owner_repo_mutation"])
        self.assertEqual(
            ["owner_repo_implementation_not_explicit"],
            not_explicit_payload["mutation_reasons"],
        )

    def test_protected_surface_violation_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["owner_repo_implementation"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        payload = evaluate_pilot_selected_owner_repo_mutation(bundle)

        self.assertEqual("no_owner_repo_mutation", payload["mutation_status"])
        self.assertIsNone(payload["owner_repo_mutation"])
        self.assertEqual(["protected_surface_violation"], payload["mutation_reasons"])

    def test_repo_discovery_or_branch_worktree_enumeration_fails_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]

        repo_payload = evaluate_pilot_selected_owner_repo_mutation(repo_bundle)

        self.assertEqual("no_owner_repo_mutation", repo_payload["mutation_status"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["mutation_reasons"])

        branch_bundle = _base_bundle()
        branch_bundle["worktree_inventory"] = ["repos/example/.worktrees/pilot-a"]

        branch_payload = evaluate_pilot_selected_owner_repo_mutation(branch_bundle)

        self.assertEqual("no_owner_repo_mutation", branch_payload["mutation_status"])
        self.assertEqual(["branch_worktree_enumeration_invented"], branch_payload["mutation_reasons"])

    def test_execution_home_or_actual_owner_repo_mutation_fails_closed(self) -> None:
        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home"] = "_stack"

        execution_home_payload = evaluate_pilot_selected_owner_repo_mutation(execution_home_bundle)

        self.assertEqual("no_owner_repo_mutation", execution_home_payload["mutation_status"])
        self.assertEqual(["execution_home_inference_invented"], execution_home_payload["mutation_reasons"])

        mutation_bundle = _base_bundle()
        mutation_bundle["worker_launch_authority"] = True

        mutation_payload = evaluate_pilot_selected_owner_repo_mutation(mutation_bundle)

        self.assertEqual("no_owner_repo_mutation", mutation_payload["mutation_status"])
        self.assertEqual(["actual_owner_repo_mutation_invented"], mutation_payload["mutation_reasons"])

    def test_playbook_doctrine_export_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["playbook_doctrine_export"] = True

        payload = evaluate_pilot_selected_owner_repo_mutation(bundle)

        self.assertEqual("no_owner_repo_mutation", payload["mutation_status"])
        self.assertEqual(["playbook_doctrine_export_invented"], payload["mutation_reasons"])


if __name__ == "__main__":
    unittest.main()
