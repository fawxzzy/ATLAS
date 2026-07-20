from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import sys
import tempfile
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

    def observation(self) -> dict:
        return RECOVERY._load_json(FIXTURES / "valid-desktop-observation.json")

    def observation_now(self) -> dt.datetime:
        return RECOVERY._parse_utc_timestamp(
            self.observation()["payload"]["captured_at"],
            "test observation captured_at",
        )

    def resign_observation(self, observation: dict) -> dict:
        digest = RECOVERY._sha256_bytes(RECOVERY._canonical_bytes(observation["payload"]))
        observation["payload_digest"] = digest
        observation["observation_id"] = "onv1_" + digest.removeprefix("sha256:")
        return observation

    def validate_observation(
        self,
        observation: dict,
        *,
        current: dict | None = None,
        now: dt.datetime | None = None,
    ) -> dict:
        return RECOVERY.validate_desktop_observation(
            observation,
            current or observation,
            self.manifest,
            self.registry,
            now=now or self.observation_now(),
        )

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
        self.assertEqual("ATLAS_ROOT", inbox["cwd_locator"])
        self.assertEqual("ATLAS_ROOT", inbox["resolved_cwd"])
        self.assertNotIn("SET_RUNTIME_POLICY", inbox["actions"])

    def test_live_create_and_bootstrap_use_admitted_cwd_and_modern_permissions(self) -> None:
        role = next(item for item in self.manifest["roles"] if item["role_id"] == "owner.socials-os")
        locator = role["runtime"]["cwd_locator"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            admitted_cwd = Path(temporary_directory).resolve()
            adapter = RECOVERY.LiveAppServerAdapter(
                cwd_bindings={locator: admitted_cwd},
            )

            create_params = adapter._thread_start_params(role)
            bootstrap_params = adapter._bootstrap_params(role, "thread-owner-socials-os-001")
            self.assertEqual(str(admitted_cwd), create_params["cwd"])
            self.assertEqual(str(admitted_cwd), bootstrap_params["cwd"])
            self.assertEqual(":danger-full-access", create_params["permissions"])
            self.assertNotIn("sandbox", create_params)

            legacy_role = json.loads(json.dumps(role))
            legacy_role["runtime"]["permissions"] = "danger-full-access"
            with self.assertRaisesRegex(RECOVERY.WorkflowRecoveryError, "legacy sandbox tokens"):
                adapter._thread_start_params(legacy_role)

            legacy_manifest = json.loads(json.dumps(self.manifest))
            next(
                item for item in legacy_manifest["roles"] if item["role_id"] == role["role_id"]
            )["runtime"]["permissions"] = "danger-full-access"
            with self.assertRaises(RECOVERY.ValidationFailure):
                RECOVERY._assert_schema(
                    legacy_manifest,
                    RECOVERY.MANIFEST_SCHEMA_REF,
                    "legacy permission manifest",
                )

            role_plan = {
                "role_id": role["role_id"],
                "cwd_locator": locator,
                "resolved_cwd": str(admitted_cwd),
            }
            adapter.validate_planned_cwd(role_plan)
            role_plan["resolved_cwd"] = str(ROOT)
            with self.assertRaisesRegex(RECOVERY.WorkflowRecoveryError, "accepted cwd binding drifted"):
                adapter.validate_planned_cwd(role_plan)

    def test_live_non_root_cwd_requires_an_explicit_absolute_binding(self) -> None:
        role = next(item for item in self.manifest["roles"] if item["role_id"] == "owner.fawxzzyweb")
        adapter = RECOVERY.LiveAppServerAdapter()
        with self.assertRaisesRegex(RECOVERY.WorkflowRecoveryError, "no admitted absolute binding"):
            adapter.resolve_role_cwd(role)

        with self.assertRaisesRegex(RECOVERY.ValidationFailure, "must be absolute"):
            RECOVERY._parse_cwd_bindings([f"{role['runtime']['cwd_locator']}=relative/path"])

    def test_live_existing_runtime_policy_repair_fails_preflight(self) -> None:
        adapter = RECOVERY.LiveAppServerAdapter()
        self.assertFalse(adapter.capabilities["set_runtime"])
        plan = {
            "roles": [
                {
                    "role_id": "atlas.inbox",
                    "decision": "REPAIR_RUNTIME_POLICY",
                    "active": False,
                    "actions": ["SET_RUNTIME_POLICY"],
                }
            ]
        }
        with self.assertRaisesRegex(
            RECOVERY.WorkflowRecoveryError,
            "adapter capability set_runtime is unavailable",
        ):
            RECOVERY._preflight_apply(plan, adapter)

    def test_live_apply_requires_canonical_durable_runtime_output(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary_directory:
            with contextlib.redirect_stderr(stderr):
                exit_code = RECOVERY.main(
                    [
                        "recover",
                        "--apply",
                        "--adapter",
                        "live",
                        "--output-dir",
                        temporary_directory,
                    ]
                )
        self.assertEqual(2, exit_code)
        self.assertIn("canonical runtime output directory", stderr.getvalue())

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
        self.assertEqual(
            created[0].thread_id,
            adapter.binding_overrides["atlas.inbox"],
        )
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

    def test_partial_create_journal_blocks_duplicate_in_a_fresh_process(self) -> None:
        plan, adapter = self.plan("partial-create.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            journal_path = Path(temporary_directory) / "creation-journal.json"
            journal = RECOVERY.CreationJournal(
                journal_path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            with self.assertRaises(RECOVERY.PartialCreateFailure) as caught:
                RECOVERY.apply_plan(
                    plan,
                    self.manifest,
                    adapter,
                    creation_journal=journal,
                )
            create_receipt = next(
                item for item in caught.exception.mutation_receipts if item["action"] == "CREATE"
            )
            created_runtime_id = create_receipt["after_runtime_id"]
            self.assertTrue(journal_path.is_file())

            # Discard all process-local adapter and journal state. A fresh
            # process that cannot discover the exact retained ID must block,
            # never schedule another CREATE.
            retained = RECOVERY.CreationJournal(
                journal_path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            missing_adapter = self.adapter("missing-task.json")
            retained.apply_to(missing_adapter, self.registry)
            blocked_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                missing_adapter,
                mode="dry-run",
                deterministic=True,
            )
            blocked_inbox = self.role(blocked_plan, "atlas.inbox")
            self.assertEqual(created_runtime_id, blocked_inbox["runtime_id"])
            self.assertEqual(
                "FAIL_CLOSED_RETAINED_CREATION_NOT_DISCOVERED",
                blocked_inbox["decision"],
            )
            self.assertNotIn("CREATE", blocked_inbox["actions"])

            # If complete discovery returns the exact ID, the same fresh
            # journal binding reuses and repairs it without duplication.
            discoverable_fixture = RECOVERY._load_json(FIXTURES / "missing-task.json")
            discoverable_fixture["operations"].append(
                {
                    "op": "partial_runtime",
                    "role_id": "atlas.inbox",
                    "runtime_id": created_runtime_id,
                    "title": None,
                    "status": "idle",
                    "cwd": "ATLAS_ROOT",
                    "archived": False,
                    "pinned": False,
                }
            )
            discoverable_adapter = RECOVERY.FixtureAdapter(
                self.manifest,
                self.registry,
                discoverable_fixture,
            )
            retained.apply_to(discoverable_adapter, self.registry)
            repair_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                discoverable_adapter,
                mode="dry-run",
                deterministic=True,
            )
            repair_inbox = self.role(repair_plan, "atlas.inbox")
            self.assertEqual(created_runtime_id, repair_inbox["runtime_id"])
            self.assertNotIn("CREATE", repair_inbox["actions"])

    def test_partial_create_cli_restart_loads_journal_before_planning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                first_exit = RECOVERY.main(
                    [
                        "recover",
                        "--apply",
                        "--adapter",
                        "fixture",
                        "--fixture",
                        str(FIXTURES / "partial-create.json"),
                        "--acceptance",
                        str(FIXTURES / "fixture-acceptance.json"),
                        "--output-dir",
                        temporary_directory,
                        "--deterministic",
                    ]
                )
            self.assertEqual(4, first_exit)
            partial_receipt = json.loads(stderr.getvalue())
            journal_receipt = partial_receipt["creation_journal"]
            self.assertEqual(
                "fixture-created-atlas.inbox-1",
                journal_receipt["bindings"]["atlas.inbox"],
            )
            self.assertTrue((Path(temporary_directory) / "creation-journal.json").is_file())

            # A second CLI invocation constructs a new fixture adapter. The
            # only identity carried across invocations is the durable journal.
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                second_exit = RECOVERY.main(
                    [
                        "recover",
                        "--dry-run",
                        "--adapter",
                        "fixture",
                        "--fixture",
                        str(FIXTURES / "missing-task.json"),
                        "--output-dir",
                        temporary_directory,
                        "--deterministic",
                    ]
                )
            self.assertEqual(0, second_exit)
            restarted = json.loads(stdout.getvalue())
            self.assertEqual("BLOCKED", restarted["status"])
            self.assertEqual(0, restarted["summary"]["create_count"])
            restarted_plan = RECOVERY._load_json(Path(temporary_directory) / "plan.json")
            restarted_inbox = self.role(restarted_plan, "atlas.inbox")
            self.assertEqual(
                "fixture-created-atlas.inbox-1",
                restarted_inbox["runtime_id"],
            )
            self.assertEqual(
                "FAIL_CLOSED_RETAINED_CREATION_NOT_DISCOVERED",
                restarted_inbox["decision"],
            )
            self.assertNotIn("CREATE", restarted_inbox["actions"])

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
        accepted_digest = plan["plan_digest"]
        self.assertIsNone(self.role(plan, "atlas.inbox")["runtime_id"])
        receipts = RECOVERY.apply_plan(plan, self.manifest, adapter)
        self.assertEqual(1, sum(item["action"] == "CREATE" for item in receipts))
        self.assertEqual(accepted_digest, plan["plan_digest"])
        self.assertIsNone(self.role(plan, "atlas.inbox")["runtime_id"])

        post_apply_plan, refreshed, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="dry-run",
            deterministic=True,
        )
        runtime_registry = RECOVERY.build_runtime_registry(
            self.manifest,
            self.registry,
            post_apply_plan,
            refreshed,
            runtime_id_overrides=adapter.binding_overrides,
        )
        inbox_binding = next(
            item for item in runtime_registry["bindings"] if item["role_id"] == "atlas.inbox"
        )
        self.assertEqual("fixture-created-atlas.inbox-1", inbox_binding["current_runtime_id"])
        self.assertEqual("idle", inbox_binding["runtime_status"])
        self.assertEqual("HEALTHY", inbox_binding["health"])

        without_created_runtime = [
            item for item in refreshed if item.thread_id != inbox_binding["current_runtime_id"]
        ]
        with self.assertRaisesRegex(
            RECOVERY.WorkflowRecoveryError,
            "was not returned by readback",
        ):
            RECOVERY.build_runtime_registry(
                self.manifest,
                self.registry,
                plan,
                without_created_runtime,
                runtime_id_overrides=adapter.binding_overrides,
            )

        final_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="dry-run",
            deterministic=True,
        )
        self.assertEqual("HEALTHY", self.role(final_plan, "atlas.inbox")["health"])
        self.assertEqual(0, final_plan["summary"]["create_count"])

    def test_fixture_cli_writes_immutable_accepted_and_healthy_post_apply_plans(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = RECOVERY.main(
                    [
                        "recover",
                        "--apply",
                        "--adapter",
                        "fixture",
                        "--fixture",
                        str(FIXTURES / "missing-task.json"),
                        "--acceptance",
                        str(FIXTURES / "fixture-acceptance.json"),
                        "--output-dir",
                        temporary_directory,
                        "--deterministic",
                    ]
                )
            self.assertEqual(0, exit_code)
            result = json.loads(stdout.getvalue())
            self.assertEqual("HEALTHY", result["status"])
            self.assertEqual(0, result["summary"]["create_count"])

            output_dir = Path(temporary_directory)
            accepted_plan = RECOVERY._load_json(output_dir / "plan.json")
            post_apply_plan = RECOVERY._load_json(output_dir / "post-apply-plan.json")
            runtime_registry = RECOVERY._load_json(output_dir / "live-registry.json")
            receipt = RECOVERY._load_json(output_dir / "RECEIPT.json")
            creation_journal = RECOVERY._load_json(output_dir / "creation-journal.json")
            accepted_inbox = self.role(accepted_plan, "atlas.inbox")
            post_apply_inbox = self.role(post_apply_plan, "atlas.inbox")
            registry_inbox = next(
                item for item in runtime_registry["bindings"] if item["role_id"] == "atlas.inbox"
            )

            self.assertIsNone(accepted_inbox["runtime_id"])
            self.assertEqual("fixture-created-atlas.inbox-1", post_apply_inbox["runtime_id"])
            self.assertEqual("HEALTHY", post_apply_inbox["health"])
            self.assertEqual(post_apply_inbox["runtime_id"], registry_inbox["current_runtime_id"])
            self.assertEqual("HEALTHY", receipt["terminal_status"])
            self.assertEqual(accepted_plan["plan_digest"], receipt["accepted_plan_digest"])
            self.assertEqual(post_apply_plan["plan_digest"], receipt["post_apply_plan_digest"])
            self.assertNotEqual(receipt["accepted_plan_digest"], receipt["post_apply_plan_digest"])
            RECOVERY._assert_schema(
                creation_journal,
                RECOVERY.CREATION_JOURNAL_SCHEMA_REF,
                "test creation journal",
            )
            journal_entry = creation_journal["payload"]["entries"][0]
            self.assertEqual(post_apply_inbox["runtime_id"], journal_entry["runtime_id"])
            self.assertEqual("READBACK_CONFIRMED", journal_entry["state"])
            self.assertEqual(post_apply_plan["plan_digest"], journal_entry["post_apply_plan_digest"])
            self.assertEqual(creation_journal["event_id"], receipt["creation_journal"]["event_id"])
            self.assertEqual(
                creation_journal["payload_digest"],
                receipt["creation_journal"]["payload_digest"],
            )

    def test_created_runtime_missing_from_post_apply_readback_is_not_confirmed(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            journal = RECOVERY.CreationJournal(
                Path(temporary_directory) / "creation-journal.json",
                self.manifest,
                self.registry,
                manifest_digest,
            )
            receipts = RECOVERY.apply_plan(
                plan,
                self.manifest,
                adapter,
                creation_journal=journal,
            )
            created_runtime_id = next(
                item["after_runtime_id"] for item in receipts if item["action"] == "CREATE"
            )
            adapter.threads = [
                item for item in adapter.threads if item.thread_id != created_runtime_id
            ]

            post_apply_plan, returned_threads, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                adapter,
                mode="dry-run",
                deterministic=True,
            )
            post_apply_inbox = self.role(post_apply_plan, "atlas.inbox")
            self.assertEqual(
                "FAIL_CLOSED_RETAINED_CREATION_NOT_DISCOVERED",
                post_apply_inbox["decision"],
            )
            self.assertNotIn("CREATE", post_apply_inbox["actions"])
            with self.assertRaisesRegex(
                RECOVERY.WorkflowRecoveryError,
                "was not returned and bound",
            ):
                journal.confirm_readback(post_apply_plan, returned_threads)

            persisted = RECOVERY._load_json(journal.path)
            entry = persisted["payload"]["entries"][0]
            self.assertEqual("CREATED_PENDING_READBACK", entry["state"])
            self.assertIsNone(entry["post_apply_plan_id"])
            self.assertIsNone(entry["post_apply_plan_digest"])

    def test_valid_desktop_observation_is_complete_content_addressed_and_pin_unknown(self) -> None:
        observation = self.observation()
        result = self.validate_observation(observation)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(len(self.manifest["roles"]), result["role_count"])
        self.assertEqual("UNKNOWN", result["pin_state"])
        self.assertEqual("UNSUPPORTED", result["pin_capability"])
        self.assertEqual(observation["observation_id"], result["current_observation_id"])
        with self.assertRaises(RECOVERY.ValidationFailure):
            RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                self.adapter("healthy.json"),
                mode="dry-run",
                deterministic=True,
                desktop_observation=observation,
                observation_now=self.observation_now(),
            )

    def test_desktop_observation_rejects_malformed_identity_denominator_and_digest(self) -> None:
        cases: list[tuple[str, dict, str, bool]] = []

        pin = self.observation()
        pin["payload"]["entries"][0]["pin_state"] = "PINNED"
        cases.append(("pin", pin, "expected const 'UNKNOWN'", True))

        missing = self.observation()
        missing["payload"]["entries"].pop()
        cases.append(("missing-role", missing, "missing required roles", True))

        partial = self.observation()
        partial["payload"]["entries"].pop()
        partial["payload"]["required_role_count"] = 12
        cases.append(("partial-denominator", partial, "partial or over-complete role denominator", True))

        duplicate_role = self.observation()
        duplicate_role["payload"]["entries"].append(
            json.loads(json.dumps(duplicate_role["payload"]["entries"][0]))
        )
        cases.append(("duplicate-role", duplicate_role, "duplicate role entries", True))

        duplicate_runtime = self.observation()
        duplicate_runtime["payload"]["entries"][1]["runtime_thread_id"] = (
            duplicate_runtime["payload"]["entries"][0]["runtime_thread_id"]
        )
        cases.append(("duplicate-runtime", duplicate_runtime, "duplicate runtime entries", True))

        wrong_thread = self.observation()
        wrong_thread["payload"]["entries"][0]["runtime_thread_id"] = "wrong-thread-id"
        cases.append(("wrong-thread", wrong_thread, "runtime binding mismatch", True))

        wrong_host = self.observation()
        wrong_host["payload"]["source_host_id"] = "wrong-host"
        for entry in wrong_host["payload"]["entries"]:
            entry["source_host_id"] = "wrong-host"
        cases.append(("wrong-host", wrong_host, "expected const 'local'", True))

        wrong_title = self.observation()
        wrong_title["payload"]["entries"][0]["source_title"] = "Wrong Title"
        cases.append(("wrong-title", wrong_title, "source title mismatch", True))

        malformed_status = self.observation()
        malformed_status["payload"]["entries"][0]["activity"] = "completed"
        cases.append(("malformed-status", malformed_status, "value is not in enum", True))

        unknown_role = self.observation()
        unknown_role["payload"]["entries"][0]["role_id"] = "unknown.required-role"
        cases.append(("unknown-role", unknown_role, "unknown required roles", True))

        bad_digest = self.observation()
        bad_digest["payload_digest"] = "sha256:" + "a" * 64
        cases.append(("digest-mismatch", bad_digest, "payload digest mismatch", False))

        for name, observation, expected, resign in cases:
            with self.subTest(name=name):
                if resign:
                    self.resign_observation(observation)
                with self.assertRaises(RECOVERY.ValidationFailure) as caught:
                    self.validate_observation(observation)
                self.assertIn(expected, str(caught.exception))

    def test_desktop_observation_rejects_stale_and_future_timestamps(self) -> None:
        for name, offset, expected in (
            ("stale", -301, "is stale"),
            ("future", 31, "is in the future"),
        ):
            with self.subTest(name=name):
                observation = self.observation()
                timestamp = self.observation_now() + dt.timedelta(seconds=offset)
                rendered = timestamp.isoformat().replace("+00:00", "Z")
                observation["payload"]["captured_at"] = rendered
                for entry in observation["payload"]["entries"]:
                    entry["observed_at"] = rendered
                self.resign_observation(observation)
                with self.assertRaises(RECOVERY.ValidationFailure) as caught:
                    self.validate_observation(observation)
                self.assertIn(expected, str(caught.exception))

    def test_newer_current_receipt_rejects_older_superseded_candidate(self) -> None:
        older = self.observation()
        newer = self.observation()
        later_now = self.observation_now() + dt.timedelta(seconds=1)
        later_timestamp = later_now.isoformat().replace("+00:00", "Z")
        newer["payload"]["captured_at"] = later_timestamp
        newer["payload"]["supersession"]["supersedes_observation_ids"] = [
            older["observation_id"]
        ]
        for entry in newer["payload"]["entries"]:
            entry["observed_at"] = later_timestamp
        self.resign_observation(newer)

        current = self.validate_observation(newer, current=newer, now=later_now)
        self.assertEqual(newer["observation_id"], current["current_observation_id"])
        with self.assertRaises(RECOVERY.ValidationFailure) as caught:
            self.validate_observation(older, current=newer, now=later_now)
        self.assertIn("has been superseded by trusted current observation", str(caught.exception))

    def test_desktop_observation_changes_activity_only_and_cannot_satisfy_pin_apply(self) -> None:
        observation = self.observation()
        adapter = self.adapter("healthy.json")
        for thread in adapter.threads:
            thread.pinned = None
        adapter.capabilities = {**adapter.capabilities, "read_pin": False, "set_pin": False}
        first, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="apply",
            deterministic=True,
            desktop_observation=observation,
            desktop_observation_current=observation,
            observation_now=self.observation_now(),
        )
        second, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="apply",
            deterministic=True,
            desktop_observation=observation,
            desktop_observation_current=observation,
            observation_now=self.observation_now(),
        )
        self.assertEqual(first, second)
        self.assertEqual("UNKNOWN", first["summary"]["desktop_observation"]["pin_state"])
        self.assertEqual(
            observation["observation_id"],
            first["summary"]["desktop_observation"]["current_observation_id"],
        )
        self.assertTrue(all(item["pinned"] is None for item in first["roles"]))
        self.assertTrue(all("SET_PIN" not in item["actions"] for item in first["roles"]))
        self.assertTrue(all("PROVE_PIN_STATE" in item["actions"] for item in first["roles"]))
        with self.assertRaises(RECOVERY.WorkflowRecoveryError):
            RECOVERY._preflight_apply(first, adapter)

        later = self.observation()
        later_now = self.observation_now() + dt.timedelta(seconds=1)
        later_timestamp = later_now.isoformat().replace("+00:00", "Z")
        later["payload"]["captured_at"] = later_timestamp
        for entry in later["payload"]["entries"]:
            entry["observed_at"] = later_timestamp
        self.resign_observation(later)
        later_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="apply",
            deterministic=True,
            desktop_observation=later,
            desktop_observation_current=later,
            observation_now=later_now,
        )
        self.assertNotEqual(
            first["summary"]["desktop_observation"]["payload_digest"],
            later_plan["summary"]["desktop_observation"]["payload_digest"],
        )
        self.assertEqual(first["plan_digest"], later_plan["plan_digest"])

    def test_observed_active_writer_and_discovery_mismatch_fail_closed(self) -> None:
        active = self.observation()
        next(item for item in active["payload"]["entries"] if item["role_id"] == "atlas.main")[
            "activity"
        ] = "active"
        self.resign_observation(active)
        adapter = self.adapter("healthy.json")
        active_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            adapter,
            mode="apply",
            deterministic=True,
            desktop_observation=active,
            desktop_observation_current=active,
            observation_now=self.observation_now(),
        )
        main = self.role(active_plan, "atlas.main")
        self.assertEqual("BLOCKED", main["health"])
        self.assertEqual("FAIL_CLOSED_OBSERVED_ACTIVE_WRITER", main["decision"])
        self.assertEqual([], main["actions"])
        with self.assertRaises(RECOVERY.WorkflowRecoveryError):
            RECOVERY._preflight_apply(active_plan, adapter)

        missing_adapter = self.adapter("missing-task.json")
        mismatch_observation = self.observation()
        mismatch_plan, _, _ = RECOVERY.build_recovery_plan(
            self.manifest,
            self.registry,
            missing_adapter,
            mode="dry-run",
            deterministic=True,
            desktop_observation=mismatch_observation,
            desktop_observation_current=mismatch_observation,
            observation_now=self.observation_now(),
        )
        inbox = self.role(mismatch_plan, "atlas.inbox")
        self.assertEqual("UNKNOWN", inbox["health"])
        self.assertEqual("FAIL_CLOSED_OBSERVATION_DISCOVERY_MISMATCH", inbox["decision"])
        self.assertNotIn("CREATE", inbox["actions"])
        with self.assertRaises(RECOVERY.WorkflowRecoveryError):
            RECOVERY._preflight_apply(mismatch_plan, missing_adapter)

    def test_cli_rejects_desktop_observation_apply(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = RECOVERY.main(
                [
                    "recover",
                    "--apply",
                    "--adapter",
                    "fixture",
                    "--fixture",
                    str(FIXTURES / "healthy.json"),
                    "--desktop-observation",
                    str(FIXTURES / "valid-desktop-observation.json"),
                    "--desktop-observation-current",
                    str(FIXTURES / "valid-desktop-observation.json"),
                    "--no-write-runtime",
                    "--deterministic",
                ]
            )
        self.assertEqual(2, exit_code)
        self.assertIn("read-only dry-run input", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
