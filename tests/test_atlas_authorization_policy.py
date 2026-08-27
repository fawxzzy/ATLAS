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

    def test_operator_granted_clean_guarded_merge_is_immediately_reusable(self) -> None:
        request = self.request(authority_profile="clean-guarded-merge-v1")
        request["gates"].update(
            {
                "open_ready_clean_mergeable_unmerged": True,
                "exact_base_head_tree": True,
                "normal_merge_commit_only": True,
                "branch_preserved": True,
                "postmerge_ci_defined": True,
            }
        )
        result = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("AUTO_AUTHORIZED", result["decision"])
        self.assertEqual("AUTH-GITHUB-CLEAN-GUARDED-MERGE-V1", result["operator_rule_id"])
        self.assertIn("deployment", result["operator_rule_exclusions"])

    def test_verified_release_production_continuation_is_narrowly_auto_authorized(self) -> None:
        gate_names = {
            "bounded_scope", "exact_identity", "fresh_evidence",
            "no_unknown_material_state", "no_writer_collision",
            "exact_reviewed_merge_commit", "reviewed_tree_equals_merge_tree",
            "postmerge_ci_success", "exact_named_production_project",
            "production_binding_exact", "zero_unresolved_review_threads",
            "zero_deployment_writer_collision", "known_good_rollback_target_retained",
            "automatic_rollback_on_failed_acceptance",
            "production_acceptance_checks_defined", "single_production_deployment",
            "terminal_production_readback_defined", "cost_verified_zero",
            "production_target_and_project_exact", "production_writer_collision_free",
            "rollback_obligation_reserved_before_effect", "terminal_proof_before_cleanup",
            "no_source_or_configuration_drift",
            "no_dns_auth_data_billing_or_destructive_effect",
        }
        request = {
            "request_id": "verified-release-production-1",
            "action_class": "VERIFIED_RELEASE_PRODUCTION_CONTINUATION",
            "authority_profile": "verified-release-production-continuation-v1",
            "scope_key": "vercel:fawxzzy:FawxzzyWeb:production:merge-abc",
            "constraints": {
                "deployments": 1,
                "retries": 0,
                "cost_usd": 0,
                "unreviewed_promotions": 0,
                "dns_mutations": 0,
                "environment_mutations": 0,
                "secret_mutations": 0,
                "auth_mutations": 0,
                "live_data_mutations": 0,
                "provider_configuration_mutations": 0,
                "billing_actions": 0,
                "destructive_actions": 0,
                "deletions": 0,
                "ownership_or_retention_changes": 0,
                "unrelated_provider_effects": 0,
            },
            "risk_flags": {"production": True, "provider_mutation": True},
            "gates": {name: True for name in gate_names},
        }
        result = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("AUTO_AUTHORIZED", result["decision"])
        self.assertEqual(
            "AUTH-VERIFIED-RELEASE-PRODUCTION-CONTINUATION-V1",
            result["operator_rule_id"],
        )
        self.assertEqual(
            ["production", "provider_mutation"],
            result["operator_rule_risk_flag_exceptions"],
        )
        self.assertEqual(
            [
                "exact_deployment_identity",
                "exact_named_project_production_binding_readback",
                "production_acceptance_observation_complete",
                "automatic_rollback_or_terminal_success_receipt",
                "terminal_production_readback",
            ],
            result["required_post_action_proof"],
        )

        request["gates"]["known_good_rollback_target_retained"] = False
        held = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("HOLD", held["decision"])
        self.assertIn(
            "gate_not_true:known_good_rollback_target_retained",
            held["reasons"],
        )

    def test_verified_release_profile_does_not_override_auth_or_live_data_risk(self) -> None:
        request = self.request(
            action_class="VERIFIED_RELEASE_PRODUCTION_CONTINUATION",
            authority_profile="verified-release-production-continuation-v1",
            risk_flags={"production": True, "auth_mutation": True},
        )
        result = evaluate_authorization(request, empty_registry(), self.policy)
        self.assertEqual("AUTHORIZATION_REQUIRED", result["decision"])
        self.assertIn("never_learn_risk:auth_mutation", result["reasons"])

    def test_verified_release_profile_enforces_every_declared_risk_exclusion(self) -> None:
        gate_names = {
            "bounded_scope", "exact_identity", "fresh_evidence",
            "no_unknown_material_state", "no_writer_collision",
            "exact_reviewed_merge_commit", "reviewed_tree_equals_merge_tree",
            "postmerge_ci_success", "exact_named_production_project",
            "production_binding_exact", "zero_unresolved_review_threads",
            "zero_deployment_writer_collision", "known_good_rollback_target_retained",
            "automatic_rollback_on_failed_acceptance",
            "production_acceptance_checks_defined", "single_production_deployment",
            "terminal_production_readback_defined", "cost_verified_zero",
            "production_target_and_project_exact", "production_writer_collision_free",
            "rollback_obligation_reserved_before_effect", "terminal_proof_before_cleanup",
            "no_source_or_configuration_drift",
            "no_dns_auth_data_billing_or_destructive_effect",
        }
        constraints = {
            "deployments": 1, "retries": 0, "cost_usd": 0,
            "unreviewed_promotions": 0, "dns_mutations": 0,
            "environment_mutations": 0, "secret_mutations": 0,
            "auth_mutations": 0, "live_data_mutations": 0,
            "provider_configuration_mutations": 0, "billing_actions": 0,
            "destructive_actions": 0, "deletions": 0,
            "ownership_or_retention_changes": 0, "unrelated_provider_effects": 0,
        }
        base = {
            "request_id": "verified-release-adversarial",
            "action_class": "VERIFIED_RELEASE_PRODUCTION_CONTINUATION",
            "authority_profile": "verified-release-production-continuation-v1",
            "scope_key": "vercel:fawxzzy:FawxzzyWeb:production:merge-abc",
            "constraints": constraints,
            "risk_flags": {"production": True, "provider_mutation": True},
            "gates": {name: True for name in gate_names},
        }
        forbidden = [
            "unreviewed_promotion", "dns", "environment_variable_mutation",
            "secret_or_credential_access", "auth_mutation", "live_data_mutation",
            "provider_configuration_mutation", "billing_or_purchase",
            "destructive_or_irreversible", "source_retirement_or_deletion",
            "ownership_or_retention_change", "unrelated_provider_effect",
        ]
        for risk in forbidden:
            with self.subTest(risk=risk):
                request = {**base, "risk_flags": {**base["risk_flags"], risk: True}}
                result = evaluate_authorization(request, empty_registry(), self.policy)
                self.assertEqual("AUTHORIZATION_REQUIRED", result["decision"])

    def test_verified_release_profile_rejects_nonexact_effect_constraints(self) -> None:
        gate_names = {
            "bounded_scope", "exact_identity", "fresh_evidence",
            "no_unknown_material_state", "no_writer_collision",
            "exact_reviewed_merge_commit", "reviewed_tree_equals_merge_tree",
            "postmerge_ci_success", "exact_named_production_project",
            "production_binding_exact", "zero_unresolved_review_threads",
            "zero_deployment_writer_collision", "known_good_rollback_target_retained",
            "automatic_rollback_on_failed_acceptance",
            "production_acceptance_checks_defined", "single_production_deployment",
            "terminal_production_readback_defined", "cost_verified_zero",
            "production_target_and_project_exact", "production_writer_collision_free",
            "rollback_obligation_reserved_before_effect", "terminal_proof_before_cleanup",
            "no_source_or_configuration_drift",
            "no_dns_auth_data_billing_or_destructive_effect",
        }
        constraints = {
            "deployments": 1, "retries": 0, "cost_usd": 0,
            "unreviewed_promotions": 0, "dns_mutations": 0,
            "environment_mutations": 0, "secret_mutations": 0,
            "auth_mutations": 0, "live_data_mutations": 0,
            "provider_configuration_mutations": 0, "billing_actions": 0,
            "destructive_actions": 0, "deletions": 0,
            "ownership_or_retention_changes": 0, "unrelated_provider_effects": 0,
        }
        for name in constraints:
            if name == "cost_usd":
                continue
            with self.subTest(constraint=name):
                changed = dict(constraints)
                changed[name] = 2 if name == "deployments" else 1
                request = {
                    "request_id": f"verified-release-constraint-{name.replace('_', '-')}",
                    "action_class": "VERIFIED_RELEASE_PRODUCTION_CONTINUATION",
                    "authority_profile": "verified-release-production-continuation-v1",
                    "scope_key": "vercel:fawxzzy:FawxzzyWeb:production:merge-abc",
                    "constraints": changed,
                    "risk_flags": {"production": True, "provider_mutation": True},
                    "gates": {gate: True for gate in gate_names},
                }
                result = evaluate_authorization(request, empty_registry(), self.policy)
                self.assertEqual("HOLD", result["decision"])
                self.assertIn(f"constraint_not_exact:{name}", result["reasons"])


if __name__ == "__main__":
    unittest.main()
