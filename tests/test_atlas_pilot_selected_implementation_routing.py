from __future__ import annotations

import unittest

from ops.atlas.pilot_selected_implementation_routing import evaluate_pilot_selected_implementation_routing


def _base_selected_pilot(target_ref: str) -> dict[str, object]:
    return {
        "owner_repo_count": 1,
        "target_kind": "worktree",
        "target_ref": target_ref,
        "objective_summary": "Land one bounded root-local selected-pilot implementation-routing helper.",
        "allowed_write_scope": "ops/atlas/pilot_selected_implementation_routing.py",
        "checkpoint_surface": "docs/ops/checkpoint.md",
        "verification_gate": "python -m unittest tests.test_atlas_pilot_selected_implementation_routing -v",
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
        "selected_pilot": _base_selected_pilot("repos/example/.worktrees/pilot-a"),
        "selection_reasons": [],
    }


class PilotSelectedImplementationRoutingTests(unittest.TestCase):
    def test_explicit_selected_pilot_routes_admissibly(self) -> None:
        payload = evaluate_pilot_selected_implementation_routing(_base_bundle())

        self.assertEqual("pilot_selected", payload["selection_status"])
        self.assertEqual("implementation_route_admissible", payload["routing_status"])
        self.assertEqual(payload["selected_pilot"], payload["implementation_route"])
        self.assertEqual([], payload["routing_reasons"])

    def test_no_selection_status_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["selection_status"] = "no_selection"
        bundle["selected_pilot"] = None

        payload = evaluate_pilot_selected_implementation_routing(bundle)

        self.assertEqual("no_selection", payload["selection_status"])
        self.assertEqual("no_route", payload["routing_status"])
        self.assertIsNone(payload["implementation_route"])
        self.assertEqual(["selection_status_not_pilot_selected"], payload["routing_reasons"])

    def test_non_empty_selection_reasons_fail_closed(self) -> None:
        bundle = _base_bundle()
        bundle["selection_reasons"] = ["comparison_reasons_present"]

        payload = evaluate_pilot_selected_implementation_routing(bundle)

        self.assertEqual("pilot_selected", payload["selection_status"])
        self.assertEqual("no_route", payload["routing_status"])
        self.assertIsNone(payload["implementation_route"])
        self.assertEqual(["selection_reasons_present"], payload["routing_reasons"])
        self.assertEqual(["comparison_reasons_present"], payload["selection_reasons"])

    def test_missing_or_non_explicit_selected_pilot_fails_closed(self) -> None:
        missing_bundle = _base_bundle()
        del missing_bundle["selected_pilot"]

        missing_payload = evaluate_pilot_selected_implementation_routing(missing_bundle)

        self.assertEqual("no_route", missing_payload["routing_status"])
        self.assertIsNone(missing_payload["implementation_route"])
        self.assertEqual(["selected_pilot_missing"], missing_payload["routing_reasons"])

        not_explicit_bundle = _base_bundle()
        not_explicit_bundle["selected_pilot"] = "pilot-a"

        not_explicit_payload = evaluate_pilot_selected_implementation_routing(not_explicit_bundle)

        self.assertEqual("no_route", not_explicit_payload["routing_status"])
        self.assertIsNone(not_explicit_payload["implementation_route"])
        self.assertEqual(["selected_pilot_not_explicit"], not_explicit_payload["routing_reasons"])

    def test_protected_surface_violation_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["selected_pilot"]["allowed_write_scope"] = "docs-only plus deploy preparation"

        payload = evaluate_pilot_selected_implementation_routing(bundle)

        self.assertEqual("no_route", payload["routing_status"])
        self.assertIsNone(payload["implementation_route"])
        self.assertEqual(["protected_surface_violation"], payload["routing_reasons"])

    def test_repo_discovery_or_branch_worktree_enumeration_fails_closed(self) -> None:
        repo_bundle = _base_bundle()
        repo_bundle["repo_inventory"] = ["repos/example", "repos/other"]

        repo_payload = evaluate_pilot_selected_implementation_routing(repo_bundle)

        self.assertEqual("no_route", repo_payload["routing_status"])
        self.assertEqual(["repo_discovery_invented"], repo_payload["routing_reasons"])

        branch_bundle = _base_bundle()
        branch_bundle["worktree_inventory"] = ["repos/example/.worktrees/pilot-a"]

        branch_payload = evaluate_pilot_selected_implementation_routing(branch_bundle)

        self.assertEqual("no_route", branch_payload["routing_status"])
        self.assertEqual(["branch_worktree_enumeration_invented"], branch_payload["routing_reasons"])

    def test_execution_home_or_owner_repo_mutation_fails_closed(self) -> None:
        execution_home_bundle = _base_bundle()
        execution_home_bundle["execution_home"] = "_stack"

        execution_home_payload = evaluate_pilot_selected_implementation_routing(execution_home_bundle)

        self.assertEqual("no_route", execution_home_payload["routing_status"])
        self.assertEqual(["execution_home_inference_invented"], execution_home_payload["routing_reasons"])

        mutation_bundle = _base_bundle()
        mutation_bundle["worker_launch_authority"] = True

        mutation_payload = evaluate_pilot_selected_implementation_routing(mutation_bundle)

        self.assertEqual("no_route", mutation_payload["routing_status"])
        self.assertEqual(["owner_repo_mutation_invented"], mutation_payload["routing_reasons"])

    def test_playbook_doctrine_export_fails_closed(self) -> None:
        bundle = _base_bundle()
        bundle["playbook_doctrine_export"] = True

        payload = evaluate_pilot_selected_implementation_routing(bundle)

        self.assertEqual("no_route", payload["routing_status"])
        self.assertEqual(["playbook_doctrine_export_invented"], payload["routing_reasons"])


if __name__ == "__main__":
    unittest.main()
