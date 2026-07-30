from __future__ import annotations

import unittest

from ops.atlas.authorization_policy import (
    AuthorizationPolicyError,
    empty_registry,
    evaluate_authorization,
    load_policy,
    record_operator_decision,
)


class AtlasAuthorizationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy()

    def decision(self, event_id: str, outcome: str = "APPROVE", **overrides):
        payload = {
            "event_id": event_id,
            "outcome": outcome,
            "action_class": "CLEAN_GUARDED_MERGE",
            "scope_key": "repo:fawxzzy/example",
            "constraints": {"review": "clean", "deployment": "none"},
            "risk_flags": {},
            "decided_at": "2026-07-29T12:00:00Z",
        }
        payload.update(overrides)
        return payload

    def request(self, **overrides):
        gates = {
            "bounded_scope": True,
            "exact_identity": True,
            "fresh_evidence": True,
            "no_unknown_material_state": True,
            "no_writer_collision": True,
            "reversible": True,
            "clean_worktree": True,
            "exact_head": True,
            "head_parity": True,
            "checks_passed": True,
            "independent_review_clean": True,
            "zero_unresolved_threads": True,
            "zero_deployments": True,
            "merge_policy_allows": True,
        }
        payload = {
            "request_id": "merge-pr-1",
            "action_class": "CLEAN_GUARDED_MERGE",
            "scope_key": "repo:fawxzzy/example",
            "constraints": {"review": "clean", "deployment": "none"},
            "risk_flags": {},
            "gates": gates,
        }
        payload.update(overrides)
        return payload

    def test_two_matching_approvals_activate_reuse(self) -> None:
        registry = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        self.assertEqual("CANDIDATE", registry["entries"][0]["state"])
        registry = record_operator_decision(registry, self.decision("event-2"), self.policy)
        self.assertEqual("ACTIVE", registry["entries"][0]["state"])
        result = evaluate_authorization(self.request(), registry, self.policy)
        self.assertEqual("AUTO_AUTHORIZED", result["decision"])
        self.assertFalse(result["executes_action"])
        self.assertTrue(result["owner_first"])

    def test_exact_retry_is_idempotent(self) -> None:
        first = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        second = record_operator_decision(first, self.decision("event-1"), self.policy)
        self.assertEqual(first, second)
        self.assertEqual(
            first["applied_event_digests"]["event-1"],
            second["applied_event_digests"]["event-1"],
        )

    def test_reused_event_id_with_changed_content_fails_before_mutation(self) -> None:
        registry = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        registry = record_operator_decision(registry, self.decision("event-2"), self.policy)
        original = registry.copy()
        changed = self.decision(
            "event-1",
            "DENY",
            constraints={"review": "clean", "deployment": "preview"},
        )

        with self.assertRaisesRegex(
            AuthorizationPolicyError,
            "reused with different content",
        ):
            record_operator_decision(registry, changed, self.policy)

        self.assertEqual(original, registry)
        self.assertEqual(
            "AUTO_AUTHORIZED",
            evaluate_authorization(self.request(), registry, self.policy)["decision"],
        )

    def test_legacy_applied_event_without_digest_fails_closed(self) -> None:
        registry = empty_registry()
        registry["applied_event_ids"] = ["event-1"]
        with self.assertRaisesRegex(
            AuthorizationPolicyError,
            "cannot be verified",
        ):
            record_operator_decision(registry, self.decision("event-1"), self.policy)

    def test_constraint_drift_does_not_reuse_authority(self) -> None:
        registry = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        registry = record_operator_decision(registry, self.decision("event-2"), self.policy)
        request = self.request(constraints={"review": "clean", "deployment": "preview"})
        self.assertEqual("AUTHORIZATION_REQUIRED", evaluate_authorization(request, registry, self.policy)["decision"])

    def test_denial_revokes_matching_authorization(self) -> None:
        registry = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        registry = record_operator_decision(registry, self.decision("event-2"), self.policy)
        registry = record_operator_decision(registry, self.decision("event-3", "DENY"), self.policy)
        self.assertEqual("REVOKED", registry["entries"][0]["state"])
        self.assertEqual(
            "AUTHORIZATION_REQUIRED",
            evaluate_authorization(self.request(), registry, self.policy)["decision"],
        )

    def test_changed_constraint_modify_revokes_prior_active_lineage(self) -> None:
        registry = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        registry = record_operator_decision(registry, self.decision("event-2"), self.policy)
        modified = self.decision(
            "event-3",
            "MODIFY",
            constraints={"review": "clean", "deployment": "preview"},
        )
        registry = record_operator_decision(registry, modified, self.policy)
        original = next(
            entry
            for entry in registry["entries"]
            if entry.get("last_decision") == "SUPERSEDED_BY_MODIFY"
        )
        self.assertEqual("REVOKED", original["state"])
        self.assertEqual("event-3", original["revoked_by_event_id"])
        self.assertEqual(
            "AUTHORIZATION_REQUIRED",
            evaluate_authorization(self.request(), registry, self.policy)["decision"],
        )

    def test_changed_constraint_deny_revokes_prior_active_lineage(self) -> None:
        registry = record_operator_decision(empty_registry(), self.decision("event-1"), self.policy)
        registry = record_operator_decision(registry, self.decision("event-2"), self.policy)
        denied = self.decision(
            "event-3",
            "DENY",
            constraints={"review": "clean", "deployment": "preview"},
        )
        registry = record_operator_decision(registry, denied, self.policy)
        self.assertTrue(all(entry["state"] == "REVOKED" for entry in registry["entries"]))
        self.assertEqual(
            "AUTHORIZATION_REQUIRED",
            evaluate_authorization(self.request(), registry, self.policy)["decision"],
        )

    def test_production_never_becomes_learned_authority(self) -> None:
        risky = {"production": True}
        registry = record_operator_decision(
            empty_registry(),
            self.decision("event-1", risk_flags=risky),
            self.policy,
        )
        registry = record_operator_decision(
            registry,
            self.decision("event-2", risk_flags=risky),
            self.policy,
        )
        self.assertEqual("INELIGIBLE", registry["entries"][0]["state"])
        result = evaluate_authorization(self.request(risk_flags=risky), registry, self.policy)
        self.assertEqual("AUTHORIZATION_REQUIRED", result["decision"])
        self.assertIn("never_learn_risk:production", result["reasons"])

    def test_supabase_apply_never_becomes_learned_authority(self) -> None:
        result = evaluate_authorization(
            self.request(risk_flags={"supabase_apply": True}),
            empty_registry(),
            self.policy,
        )
        self.assertEqual("AUTHORIZATION_REQUIRED", result["decision"])

    def test_missing_or_unknown_gate_holds(self) -> None:
        request = self.request()
        request["gates"]["no_unknown_material_state"] = False
        result = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("HOLD", result["decision"])
        self.assertIn("gate_not_true:no_unknown_material_state", result["reasons"])

    def test_operator_granted_clean_ready_transition_is_immediately_reusable(self) -> None:
        request = self.request(
            request_id="ready-pr-1",
            action_class="READY_TRANSITION",
            authority_profile="clean-draft-to-ready-transition-v1",
        )
        request["gates"].update(
            {
                "open_draft_clean_mergeable_unmerged": True,
                "exact_base_head_tree": True,
                "repository_policy_allows": True,
            }
        )
        result = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("AUTO_AUTHORIZED", result["decision"])
        self.assertEqual("AUTH-GITHUB-CLEAN-DRAFT-TO-READY-V1", result["operator_rule_id"])
        self.assertIn("merge", result["operator_rule_exclusions"])

    def test_operator_granted_exact_metadata_retirement_is_narrow(self) -> None:
        gates = {
            "bounded_scope": True,
            "exact_identity": True,
            "fresh_evidence": True,
            "no_unknown_material_state": True,
            "no_writer_collision": True,
            "exact_record": True,
            "no_external_execution": True,
            "statusless": True,
            "reviewed_head_binding": True,
            "zero_workflow_execution": True,
            "zero_provider_execution": True,
            "zero_vercel_execution": True,
            "zero_production_execution": True,
            "single_inactive_status_only": True,
            "delete_exact_record_only": True,
            "absence_readback": True,
        }
        request = {
            "request_id": "metadata-record-1",
            "action_class": "EXACT_METADATA_REMEDIATION",
            "authority_profile": "exact-statusless-github-deployment-record-retirement-v1",
            "scope_key": "github:fawxzzy/example:deployment:1",
            "constraints": {"record_id": 1, "record_kind": "accidental_statusless_deployment"},
            "risk_flags": {},
            "gates": gates,
        }
        result = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("AUTO_AUTHORIZED", result["decision"])
        request["gates"]["zero_provider_execution"] = False
        self.assertEqual("HOLD", evaluate_authorization(request, empty_registry(), self.policy)["decision"])


if __name__ == "__main__":
    unittest.main()
