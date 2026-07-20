from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/atlas/workflow_recovery.py"
SPEC = importlib.util.spec_from_file_location("atlas_workflow_recovery", MODULE_PATH)
assert SPEC and SPEC.loader
RECOVERY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RECOVERY
SPEC.loader.exec_module(RECOVERY)
FIXTURES = ROOT / "tests/fixtures/atlas-workflow-recovery"


class WorkflowRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = RECOVERY._load_json(ROOT / RECOVERY.MANIFEST_REF)
        cls.registry = RECOVERY._load_json(ROOT / RECOVERY.REGISTRY_REF)

    def adapter(self, name: str) -> object:
        fixture = RECOVERY._load_json(FIXTURES / name)
        return RECOVERY.FixtureAdapter(self.manifest, self.registry, fixture)

    def plan(self, name: str, *, mode: str = "dry-run") -> tuple[dict, object]:
        adapter = self.adapter(name)
        plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode=mode,
            deterministic=True,
        )
        return plan, adapter

    def role(self, plan: dict, role_id: str) -> dict:
        return next(item for item in plan["roles"] if item["role_id"] == role_id)

    def test_repository_contract_and_generated_view_validate(self) -> None:
        result = RECOVERY.validate_repository()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(len(self.manifest["roles"]), result["roles"])
        self.assertEqual(
            set(item["role_id"] for item in self.manifest["roles"]),
            set(item["role_id"] for item in self.registry["bindings"]),
        )
        self.assertEqual(8, result["unbound_runtime_claims"])
        self.assertEqual(3, result["manual_questions"])
        self.assertEqual(3, result["answered_manual_questions"])
        self.assertEqual("ARCHIVED", result["bootstrap_source_lifecycle"])

    def test_answered_manual_questions_are_retained_without_execution(self) -> None:
        registry = RECOVERY._load_json(ROOT / RECOVERY.DECISION_REGISTRY_REF)
        self.assertEqual(3, len(registry["questions"]))
        self.assertTrue(all(item["status"] == "ANSWERED" for item in registry["questions"]))
        self.assertTrue(all(item["transport_state"] == "RETAINED" for item in registry["questions"]))
        self.assertTrue(all(item["execution_state"] == "NOT_STARTED" for item in registry["questions"]))

    def test_unbound_standing_claims_are_inventory_only_and_never_created(self) -> None:
        claims = self.registry["unbound_runtime_claims"]
        self.assertTrue(claims)
        self.assertTrue(all(item["health"] == "HELD" for item in claims))
        self.assertTrue(all(not item["lifecycle_action_authorized"] for item in claims))
        self.assertTrue(all(item["admission_state"] != "DURABLY_ADMITTED" for item in claims))
        plan, _ = self.plan("healthy.json")
        planned_runtime_ids = {item["runtime_id"] for item in plan["roles"]}
        self.assertTrue(planned_runtime_ids.isdisjoint(item["runtime_id"] for item in claims))

    def test_healthy_fixture_is_deterministic_and_idempotent(self) -> None:
        first, _ = self.plan("healthy.json")
        second, _ = self.plan("healthy.json")
        self.assertEqual("HEALTHY", first["terminal_status"])
        self.assertEqual(first, second)
        self.assertEqual(first["plan_digest"], second["plan_digest"])
        self.assertEqual(0, first["summary"]["create_count"])
        self.assertTrue(all(item["decision"] == "REUSE_NO_CHANGE" for item in first["roles"]))

    def test_missing_task_plans_one_create_without_archive(self) -> None:
        plan, _ = self.plan("missing-task.json")
        inbox = self.role(plan, "atlas.inbox")
        self.assertEqual("MISSING", inbox["health"])
        self.assertEqual("CREATE_MISSING_AFTER_ACCEPTANCE", inbox["decision"])
        self.assertIn("CREATE", inbox["actions"])
        self.assertEqual(1, plan["summary"]["create_count"])
        self.assertTrue(plan["no_archive"])

    def test_stale_runtime_id_repairs_binding_without_create(self) -> None:
        plan, _ = self.plan("stale-id.json")
        inbox = self.role(plan, "atlas.inbox")
        self.assertEqual("REPAIR_UNIQUE_STALE_BINDING", inbox["decision"])
        self.assertEqual("fixture-atlas-inbox-successor-001", inbox["runtime_id"])
        self.assertIn("UPDATE_BINDING", inbox["actions"])
        self.assertNotIn("CREATE", inbox["actions"])

    def test_duplicate_task_fails_closed(self) -> None:
        plan, _ = self.plan("duplicate-task.json")
        inbox = self.role(plan, "atlas.inbox")
        self.assertEqual("DUPLICATE", inbox["health"])
        self.assertEqual("FAIL_CLOSED_DUPLICATE", inbox["decision"])
        self.assertEqual("BLOCKED", plan["terminal_status"])

    def test_active_writer_collision_fails_closed(self) -> None:
        plan, _ = self.plan("active-writer.json")
        inbox = self.role(plan, "atlas.inbox")
        self.assertEqual("BLOCKED", inbox["health"])
        self.assertEqual("FAIL_CLOSED_ACTIVE_WRITER_COLLISION", inbox["decision"])
        self.assertEqual(["atlas.inbound-ledger"], plan["summary"]["writer_collision_scopes"])

    def test_partial_create_is_retained_and_retry_reuses_it(self) -> None:
        plan, adapter = self.plan("partial-create.json", mode="apply")
        with self.assertRaises(RECOVERY.PartialCreateFailure) as caught:
            RECOVERY.apply_plan(plan, self.manifest, adapter)
        receipts = caught.exception.mutation_receipts
        self.assertEqual(["CREATE"], [item["action"] for item in receipts])
        created = [item for item in adapter.threads if item.role_marker == "atlas.inbox"]
        self.assertEqual(1, len(created))

        adapter.fail_after_mutations = None
        retry_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="apply",
            deterministic=True,
        )
        inbox = self.role(retry_plan, "atlas.inbox")
        self.assertIn("UPDATE_BINDING", inbox["actions"])
        self.assertNotIn("CREATE", inbox["actions"])
        RECOVERY.apply_plan(retry_plan, self.manifest, adapter)
        final_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="dry-run",
            deterministic=True,
        )
        self.assertEqual("HEALTHY", self.role(final_plan, "atlas.inbox")["health"])
        self.assertEqual(1, len([item for item in adapter.threads if item.role_marker == "atlas.inbox"]))

    def test_retry_fixture_repairs_partial_runtime_without_duplicate(self) -> None:
        plan, _ = self.plan("retry.json")
        inbox = self.role(plan, "atlas.inbox")
        self.assertEqual("REPAIR_UNIQUE_STALE_BINDING", inbox["decision"])
        self.assertIn("SET_TITLE", inbox["actions"])
        self.assertIn("SET_RUNTIME_POLICY", inbox["actions"])
        self.assertIn("SET_PIN", inbox["actions"])
        self.assertNotIn("CREATE", inbox["actions"])

    def test_unknown_discovery_preserves_unknown(self) -> None:
        plan, _ = self.plan("unknown-state.json")
        self.assertEqual("UNKNOWN", plan["terminal_status"])
        self.assertTrue(all(item["health"] == "UNKNOWN" for item in plan["roles"]))
        self.assertTrue(all(item["decision"] == "FAIL_CLOSED_UNKNOWN" for item in plan["roles"]))

    def test_pin_unknown_is_explicit_and_live_apply_would_fail_closed(self) -> None:
        adapter = self.adapter("healthy.json")
        for thread in adapter.threads:
            thread.pinned = None
        adapter.capabilities = {**adapter.capabilities, "read_pin": False, "set_pin": False}
        plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="apply",
            deterministic=True,
        )
        self.assertTrue(all("PROVE_PIN_STATE" in item["actions"] for item in plan["roles"]))
        with self.assertRaises(RECOVERY.WorkflowRecoveryError):
            RECOVERY._preflight_apply(plan, adapter)

    def test_unified_envelope_requires_source_runtime_and_canonical_digest(self) -> None:
        envelope = RECOVERY._load_json(FIXTURES / "valid-envelope.json")
        result = RECOVERY.validate_envelope(envelope)
        self.assertEqual("PASS", result["status"])

        missing_runtime = json.loads(json.dumps(envelope))
        del missing_runtime["source_runtime"]
        with self.assertRaises(RECOVERY.ValidationFailure):
            RECOVERY.validate_envelope(missing_runtime)

        invalid = json.loads(json.dumps(envelope))
        invalid["payload_digest"] = "sha256:" + "a" * 64
        with self.assertRaises(RECOVERY.ValidationFailure):
            RECOVERY.validate_envelope(invalid)

    def test_fixture_apply_creates_exactly_one_missing_role(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        receipts = RECOVERY.apply_plan(plan, self.manifest, adapter)
        self.assertEqual(1, sum(item["action"] == "CREATE" for item in receipts))
        final_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="dry-run",
            deterministic=True,
        )
        self.assertEqual("HEALTHY", self.role(final_plan, "atlas.inbox")["health"])
        self.assertEqual(0, final_plan["summary"]["create_count"])


if __name__ == "__main__":
    unittest.main()
