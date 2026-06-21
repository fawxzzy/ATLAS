from __future__ import annotations

import unittest

from ops.atlas.pilot_selected_owner_repo_implementation import evaluate_pilot_selected_owner_repo_implementation


def _base_implementation_route(target_ref: str) -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local selected-pilot owner-repo implementation helper.",
        "allowed_write_scope": "ops/atlas/pilot_selected_owner_repo_implementation.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_selected_owner_repo_implementation -v",
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
        "implementation_route": _base_implementation_route("repos/example/.worktrees/pilot-a"),
        "routing_reasons": [],
    }


class PilotSelectedOwnerRepoImplementationTests(unittest.TestCase):
    def test_explicit_implementation_route_routes_admissibly(self) -> None:
        payload = evaluate_pilot_selected_owner_repo_implementation(_base_bundle())

        self.assertEqual("pilot_selected", payload["selection_status"])
        self.assertEqual("implementation_route_admissible", payload["routing_status"])
        self.assertEqual("owner_repo_implementation_admissible", payload["implementation_status"])
        self.assertEqual(payload["implementation_route"], payload["owner_repo_implementation"])
        self.assertEqual([], payload["implementation_reasons"])

    def test_non_admissible_routing_status_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["routing_status"] = "no_route"
        bundle["implementation_route"] = None

        payload = evaluate_pilot_selected_owner_repo_implementation(bundle)

        self.assertEqual("no_route", payload["routing_status"])
        self.assertEqual("no_owner_repo_implementation", payload["implementation_status"])
        self.assertIsNone(payload["owner_repo_implementation"])
        self.assertEqual(["routing_status_not_implementation_route_admissible"], payload["implementation_reasons"])

    def test_non_empty_routing_reasons_fail_closed(self) -> None:
        bundle = _base_bundle()
        bundle["routing_reasons"] = ["selection_reasons_present"]

        payload = evaluate_pilot_selected_owner_repo_implementation(bundle)

        self.assertEqual("implementation_route_admissible", payload["routing_status"])
        self.assertEqual("no_owner_repo_implementation", payload["implementation_status"])
        self.assertIsNone(payload["owner_repo_implementation"])
        self.assertEqual(["routing_reasons_present"], payload["implementation_reasons"])
        self.assertEqual(["selection_reasons_present"], payload["routing_reasons"])

    def test_missing_or_non_explicit_implementation_route_fails_closed(self) -> None:
        missing_bundle = _base_bundle()
        del missing_bundle["implementation_route"]

        missing_payload = evaluate_pilot_selected_owner_repo_implementation(missing_bundle)

        self.assertEqual("no_owner_repo_implementation", missing_payload["implementation_status"])
        self.assertIsNone(missing_payload["owner_repo_implementation"])
        self.assertEqual(["implementation_route_missing"], missing_payload["implementation_reasons"])

        not_explicit_bundle = _base_bundle()
        not_explicit_bundle["implementation_route"] = "pilot-a"

        not_explicit_payload = evaluate_pilot_selected_owner_repo_implementation(not_explicit_bundle)

        self.assertEqual("no_owner_repo_implementation", not_explicit_payload["implementation_status"])
        self.assertIsNone(not_explicit_payload["owner_repo_implementation"])
        self.assertEqual(["implementation_route_not_explicit"], not_explicit_payload["implementation_reasons"])

    def test_protected_surface_violation_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["implementation_route"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        payload = evaluate_pilot_selected_owner_repo_implementation(bundle)

        self.assertEqual("no_owner_repo_implementation", payload["implementation_status"])
        self.assertIsNone(payload["owner_repo_implementation"])
        self.assertEqual(["protected_surface_violation"], payload["implementation_reasons"])

    def test_repo_discovery_or_branch_worktree_enumeration_fails_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]

        repo_payload = evaluate_pilot_selected_owner_repo_implementation(repo_bundle)

        self.assertEqual("no_owner_repo_implementation", repo_payload["implementation_status"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["implementation_reasons"])

        branch_bundle = _base_bundle()
        branch_bundle["worktree_inventory"] = ["repos/example/.worktrees/pilot-a"]

        branch_payload = evaluate_pilot_selected_owner_repo_implementation(branch_bundle)

        self.assertEqual("no_owner_repo_implementation", branch_payload["implementation_status"])
        self.assertEqual(["branch_worktree_enumeration_invented"], branch_payload["implementation_reasons"])

    def test_execution_home_or_owner_repo_mutation_fails_closed(self) -> None:
        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home"] = "_stack"

        execution_home_payload = evaluate_pilot_selected_owner_repo_implementation(execution_home_bundle)

        self.assertEqual("no_owner_repo_implementation", execution_home_payload["implementation_status"])
        self.assertEqual(["execution_home_inference_invented"], execution_home_payload["implementation_reasons"])

        mutation_bundle = _base_bundle()
        mutation_bundle["worker_launch_authority"] = True

        mutation_payload = evaluate_pilot_selected_owner_repo_implementation(mutation_bundle)

        self.assertEqual("no_owner_repo_implementation", mutation_payload["implementation_status"])
        self.assertEqual(["owner_repo_mutation_invented"], mutation_payload["implementation_reasons"])

    def test_playbook_doctrine_export_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["playbook_doctrine_export"] = True

        payload = evaluate_pilot_selected_owner_repo_implementation(bundle)

        self.assertEqual("no_owner_repo_implementation", payload["implementation_status"])
        self.assertEqual(["playbook_doctrine_export_invented"], payload["implementation_reasons"])


if __name__ == "__main__":
    unittest.main()
