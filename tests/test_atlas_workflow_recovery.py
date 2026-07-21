from __future__ import annotations

import contextlib
import copy
import datetime as dt
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/atlas/workflow_recovery.py"
SPEC = importlib.util.spec_from_file_location("atlas_workflow_recovery", MODULE_PATH)
assert SPEC and SPEC.loader
RECOVERY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RECOVERY
SPEC.loader.exec_module(RECOVERY)
FIXTURES = ROOT / "tests/fixtures/atlas-workflow-recovery"
WORKFLOW_PATH = ROOT / ".github/workflows/atlas-workflow-recovery.yml"
CHECKOUT_ACTION = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON_ACTION = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
WORKFLOW_PR_PATHS = [
    ".github/workflows/atlas-workflow-recovery.yml",
    "AGENTS.md",
    "README-STACK.md",
    "docs/architecture/ATLAS-WORKFLOW-RECOVERY.md",
    "docs/memory/profiles/zachariah_workflow_profile.md",
    "docs/ops/ATLAS-WORKFLOW-RECOVERY-RUNBOOK.md",
    "docs/prompts/atlas-workflow/**",
    "docs/registry/ATLAS-WORKFLOW-*.json",
    "ops/atlas/workflow_recovery.py",
    "schemas/atlas.continuity.handoff.v1.json",
    "schemas/atlas.workflow.*.json",
    "tests/fixtures/atlas-workflow-recovery/**",
    "tests/test_atlas_workflow_recovery.py",
]
EXPECTED_WORKFLOW = {
    "name": "ATLAS Workflow Recovery",
    "on": {
        "pull_request": {"paths": WORKFLOW_PR_PATHS},
        "push": {"branches": ["main"]},
    },
    "permissions": {"contents": "read"},
    "jobs": {
        "validate": {
            "name": "validate (${{ matrix.os }}, py${{ matrix.python-version }})",
            "strategy": {
                "fail-fast": False,
                "matrix": {
                    "os": ["ubuntu-latest", "windows-latest"],
                    "python-version": ["3.12"],
                },
            },
            "runs-on": "${{ matrix.os }}",
            "timeout-minutes": 10,
            "steps": [
                {"name": "Check out", "uses": CHECKOUT_ACTION},
                {
                    "name": "Set up Python",
                    "uses": SETUP_PYTHON_ACTION,
                    "with": {"python-version": "${{ matrix.python-version }}"},
                },
                {
                    "name": "Validate canonical recovery contracts",
                    "run": "python ops/atlas/workflow_recovery.py validate --json",
                },
                {
                    "name": "Verify generated architecture",
                    "run": "python ops/atlas/workflow_recovery.py render --check",
                },
                {
                    "name": "Run focused recovery tests",
                    "run": "python -m unittest tests.test_atlas_workflow_recovery -v",
                },
                {
                    "name": "Validate canonical envelope fixture",
                    "run": "python ops/atlas/workflow_recovery.py validate-envelope tests/fixtures/atlas-workflow-recovery/valid-envelope.json",
                },
                {
                    "name": "Exercise deterministic fixture recovery",
                    "run": "python ops/atlas/workflow_recovery.py recover --apply --adapter fixture --fixture tests/fixtures/atlas-workflow-recovery/missing-task.json --acceptance tests/fixtures/atlas-workflow-recovery/fixture-acceptance.json --output-dir runtime/atlas/workflow-recovery-ci --deterministic",
                },
            ],
        }
    },
}


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate workflow key: {key}")
        result[key] = value
    return result


def _load_github_workflow(text: str | None = None) -> dict[str, object]:
    # JSON is a strict YAML subset. Keeping the workflow in JSON form makes the
    # parsed key semantics deterministic without adding a CI-only YAML package.
    payload = json.loads(
        WORKFLOW_PATH.read_text(encoding="utf-8") if text is None else text,
        object_pairs_hook=_reject_duplicate_json_keys,
    )
    if not isinstance(payload, dict):
        raise ValueError("workflow root must be an object")
    return payload


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

    def journal_record_created(
        self,
        journal: object,
        plan: dict,
        role_id: str,
        runtime_id: str,
        adapter_name: str = "fixture",
    ) -> str:
        operation_key = journal.record_intent(
            plan,
            role_id,
            adapter_name,
            provider_idempotency_key_supported=(adapter_name == "fixture"),
        )
        journal.record_created(
            plan,
            role_id,
            runtime_id,
            adapter_name,
            operation_key,
        )
        return operation_key

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

    def test_github_workflow_is_read_only_cross_platform_and_main_complete(self) -> None:
        workflow = _load_github_workflow()
        self.assertEqual(EXPECTED_WORKFLOW, workflow)

        uses = [
            step["uses"]
            for step in workflow["jobs"]["validate"]["steps"]
            if "uses" in step
        ]
        self.assertEqual([CHECKOUT_ACTION, SETUP_PYTHON_ACTION], uses)
        self.assertTrue(all(len(item.rsplit("@", 1)[1]) == 40 for item in uses))

    def test_github_workflow_rejects_authority_expansion_counterexamples(
        self,
    ) -> None:
        counterexamples: list[tuple[str, dict[str, object]]] = []

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["on"]["schedule"] = [{"cron": "0 * * * *"}]
        counterexamples.append(("extra schedule event", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["on"]["workflow_dispatch"] = {}
        counterexamples.append(("manual dispatch", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["on"]["push"]["branches"].append("*")
        counterexamples.append(("widened push branches", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["on"]["pull_request"]["paths"].append("**")
        counterexamples.append(("widened pull-request paths", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["permissions"]["issues"] = "write"
        counterexamples.append(("write permission", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["network"] = {
            "runs-on": "ubuntu-latest",
            "steps": [{"run": "curl https://example.invalid"}],
        }
        counterexamples.append(("extra network job", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["steps"].append({"run": "python -V"})
        counterexamples.append(("extra step", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["strategy"]["matrix"]["os"].append(
            "macos-latest"
        )
        counterexamples.append(("altered matrix", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["steps"][0]["uses"] = "actions/checkout@v4"
        counterexamples.append(("mutable action ref", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["steps"][2]["run"] = "python -V"
        counterexamples.append(("changed command", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["steps"].append(
            {"uses": "actions/upload-artifact@v4"}
        )
        counterexamples.append(("artifact upload", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["steps"].append(
            {"run": "vercel deploy --prod"}
        )
        counterexamples.append(("provider deployment", candidate))

        candidate = copy.deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["validate"]["environment"] = "production"
        counterexamples.append(("production environment", candidate))

        for label, counterexample in counterexamples:
            with self.subTest(label=label), self.assertRaises(AssertionError):
                self.assertEqual(EXPECTED_WORKFLOW, counterexample)

    def test_github_workflow_parser_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate workflow key: on"):
            _load_github_workflow('{"on": {}, "on": {}}')

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

    def test_apply_time_claimant_race_fails_before_create(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        role = next(item for item in self.manifest["roles"] if item["role_id"] == "atlas.inbox")
        adapter.threads.append(
            RECOVERY.ThreadRecord(
                thread_id="fixture-late-atlas-inbox-claimant",
                title=role["human_title"],
                status="idle",
                cwd="ATLAS_ROOT",
                archived=False,
                pinned=True,
                preview="late claimant",
                role_marker="atlas.inbox",
                created_at=4000,
                updated_at=4000,
            )
        )

        with self.assertRaisesRegex(
            RECOVERY.WorkflowRecoveryError,
            "apply-time discovery changed the accepted CREATE decision",
        ):
            RECOVERY.apply_plan(plan, self.manifest, self.registry, adapter)

        self.assertEqual(0, adapter.mutations)
        self.assertEqual(
            ["fixture-late-atlas-inbox-claimant"],
            [item.thread_id for item in adapter.threads if item.role_marker == "atlas.inbox"],
        )

    def test_apply_time_discovery_failure_fails_before_create(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        adapter.fixture["discovery_error"] = "injected apply-time discovery failure"

        with self.assertRaisesRegex(
            RECOVERY.WorkflowRecoveryError,
            "complete apply-time discovery failed before mutation",
        ):
            RECOVERY.apply_plan(plan, self.manifest, self.registry, adapter)

        self.assertEqual(0, adapter.mutations)
        self.assertFalse(any(item.role_marker == "atlas.inbox" for item in adapter.threads))

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
            self.assertFalse(adapter.create_operation_key_supported)
            self.assertFalse(
                any("idempot" in key.lower() or "operation" in key.lower() for key in create_params)
            )

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

    def test_posix_durable_replace_orders_rename_before_parent_fsync(self) -> None:
        events: list[tuple[str, object]] = []

        def record_replace(source: Path, target: Path) -> None:
            events.append(("replace", (source, target)))

        def record_open(path: Path, flags: int) -> int:
            events.append(("open_parent", (path, flags)))
            return 71

        def record_fsync(file_descriptor: int) -> None:
            events.append(("fsync_parent", file_descriptor))

        def record_close(file_descriptor: int) -> None:
            events.append(("close_parent", file_descriptor))

        with (
            mock.patch.object(RECOVERY.os, "replace", side_effect=record_replace),
            mock.patch.object(RECOVERY.os, "open", side_effect=record_open),
            mock.patch.object(RECOVERY.os, "fsync", side_effect=record_fsync),
            mock.patch.object(RECOVERY.os, "close", side_effect=record_close),
        ):
            RECOVERY._durable_replace(
                Path("journal.tmp"),
                Path("runtime/journal.json"),
                platform_name="posix",
            )

        self.assertEqual(
            ["replace", "open_parent", "fsync_parent", "close_parent"],
            [item[0] for item in events],
        )
        self.assertEqual(71, events[2][1])
        self.assertEqual(71, events[3][1])

    def test_atomic_write_fsyncs_file_before_durable_replace(self) -> None:
        events: list[str] = []
        real_fsync = RECOVERY.os.fsync
        real_durable_replace = RECOVERY._durable_replace

        def record_fsync(file_descriptor: int) -> None:
            events.append("fsync")
            real_fsync(file_descriptor)

        def record_durable_replace(source: Path, target: Path) -> None:
            events.append("durable_replace")
            real_durable_replace(source, target)

        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "journal.json"
            with (
                mock.patch.object(RECOVERY.os, "fsync", side_effect=record_fsync),
                mock.patch.object(
                    RECOVERY,
                    "_durable_replace",
                    side_effect=record_durable_replace,
                ),
            ):
                RECOVERY._atomic_write_bytes(target, b"first")
            self.assertEqual(b"first", target.read_bytes())

        self.assertEqual(["fsync", "durable_replace"], events[:2])

    def test_durable_replace_fails_closed_on_an_unsupported_platform(self) -> None:
        with mock.patch.object(RECOVERY.os, "replace") as replace:
            with self.assertRaisesRegex(OSError, "does not expose"):
                RECOVERY._durable_replace(
                    Path("journal.tmp"),
                    Path("journal.json"),
                    platform_name="unsupported",
                )
        replace.assert_not_called()

    def test_creation_journal_lock_times_out_and_keeps_stable_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lock_path = Path(temporary_directory) / "creation-journal.json.lock"
            with RECOVERY._CrossProcessFileLock(
                lock_path,
                timeout_seconds=0.2,
                poll_seconds=0.005,
            ):
                with self.assertRaisesRegex(
                    RECOVERY.WorkflowRecoveryError,
                    "lock timed out",
                ):
                    with RECOVERY._CrossProcessFileLock(
                        lock_path,
                        timeout_seconds=0.02,
                        poll_seconds=0.005,
                    ):
                        self.fail("a second native lock unexpectedly acquired")
                self.assertTrue(lock_path.is_file())
            self.assertTrue(lock_path.is_file())

    def test_creation_journal_lock_acquisition_failure_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lock_path = Path(temporary_directory) / "creation-journal.json.lock"
            with (
                mock.patch.object(
                    RECOVERY,
                    "_acquire_native_file_lock",
                    side_effect=OSError(RECOVERY.errno.EIO, "injected lock failure"),
                ),
                self.assertRaisesRegex(
                    RECOVERY.WorkflowRecoveryError,
                    "lock acquisition failed",
                ),
            ):
                with RECOVERY._CrossProcessFileLock(lock_path, timeout_seconds=0.01):
                    self.fail("failed lock acquisition entered its body")
            self.assertTrue(lock_path.is_file())

    def test_creation_journal_lock_rejects_unsupported_platform(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lock_path = Path(temporary_directory) / "creation-journal.json.lock"
            with self.assertRaisesRegex(
                RECOVERY.WorkflowRecoveryError,
                "platform 'unsupported' is unsupported",
            ):
                with RECOVERY._CrossProcessFileLock(
                    lock_path,
                    timeout_seconds=0.01,
                    platform_name="unsupported",
                ):
                    self.fail("unsupported lock platform entered its body")
            self.assertFalse(lock_path.exists())

    def test_creation_journal_lock_excludes_another_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            lock_path = temporary_path / "creation-journal.json.lock"
            ready_path = temporary_path / "ready"
            child_source = (
                "import importlib.util, pathlib, sys, time\n"
                "spec = importlib.util.spec_from_file_location('child_recovery', sys.argv[1])\n"
                "module = importlib.util.module_from_spec(spec)\n"
                "sys.modules[spec.name] = module\n"
                "spec.loader.exec_module(module)\n"
                "with module._CrossProcessFileLock(pathlib.Path(sys.argv[2]), timeout_seconds=2):\n"
                "    pathlib.Path(sys.argv[3]).write_text('ready', encoding='utf-8')\n"
                "    time.sleep(0.5)\n"
            )
            child = subprocess.Popen(
                [sys.executable, "-c", child_source, str(MODULE_PATH), str(lock_path), str(ready_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 2
                while not ready_path.is_file() and time.monotonic() < deadline:
                    if child.poll() is not None:
                        break
                    time.sleep(0.01)
                if not ready_path.is_file():
                    stdout, stderr = child.communicate(timeout=1)
                    self.fail(f"lock holder failed before readiness: {stdout!r} {stderr!r}")
                with self.assertRaisesRegex(
                    RECOVERY.WorkflowRecoveryError,
                    "lock timed out",
                ):
                    with RECOVERY._CrossProcessFileLock(
                        lock_path,
                        timeout_seconds=0.05,
                        poll_seconds=0.005,
                    ):
                        self.fail("a second process lock unexpectedly acquired")
                self.assertEqual(0, child.wait(timeout=2))
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=2)
                if child.stdout is not None:
                    child.stdout.close()
                if child.stderr is not None:
                    child.stderr.close()
            self.assertTrue(lock_path.is_file())

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
            RECOVERY.apply_plan(plan, self.manifest, self.registry, adapter)
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
        RECOVERY.apply_plan(retry_plan, self.manifest, self.registry, adapter)
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
                    self.registry,
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

    def test_independent_journals_reload_and_merge_without_lost_binding(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            first = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            stale_second = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )

            self.journal_record_created(first, plan, "atlas.inbox", "runtime-inbox")
            self.journal_record_created(stale_second, plan, "ai.questions", "runtime-ai")

            merged = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.assertEqual(
                {
                    "ai.questions": "runtime-ai",
                    "atlas.inbox": "runtime-inbox",
                },
                merged.bindings,
            )

    def test_journal_same_role_different_runtime_collision_fails_closed(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            first = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            stale_second = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.journal_record_created(first, plan, "atlas.inbox", "runtime-inbox-a")
            with self.assertRaisesRegex(
                RECOVERY.WorkflowRecoveryError,
                "creation intent collision",
            ):
                self.journal_record_created(
                    stale_second,
                    plan,
                    "atlas.inbox",
                    "runtime-inbox-b",
                )
            self.assertEqual(
                {"atlas.inbox": "runtime-inbox-a"},
                RECOVERY.CreationJournal(
                    path,
                    self.manifest,
                    self.registry,
                    manifest_digest,
                ).bindings,
            )

    def test_journal_same_runtime_different_role_collision_fails_closed(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            first = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            stale_second = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.journal_record_created(first, plan, "atlas.inbox", "runtime-shared")
            with self.assertRaisesRegex(
                RECOVERY.WorkflowRecoveryError,
                "already retained for another logical role atlas.inbox",
            ):
                self.journal_record_created(
                    stale_second,
                    plan,
                    "ai.questions",
                    "runtime-shared",
                )
            self.assertEqual(
                {"atlas.inbox": "runtime-shared"},
                RECOVERY.CreationJournal(
                    path,
                    self.manifest,
                    self.registry,
                    manifest_digest,
                ).bindings,
            )

    def test_stale_journal_merge_preserves_confirmed_state(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            first = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.journal_record_created(first, plan, "atlas.inbox", "runtime-inbox")
            stale_second = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            post_digest = "sha256:" + "1" * 64
            post_apply_plan = {
                "plan_id": "awrp1_" + "1" * 64,
                "plan_digest": post_digest,
                "roles": [{"role_id": "atlas.inbox", "runtime_id": "runtime-inbox"}],
            }
            first.confirm_readback(
                post_apply_plan,
                [
                    RECOVERY.ThreadRecord(
                        thread_id="runtime-inbox",
                        title="ATLAS INBOX",
                        status="idle",
                        cwd="ATLAS_ROOT",
                        archived=False,
                        pinned=True,
                    )
                ],
            )

            self.journal_record_created(stale_second, plan, "ai.questions", "runtime-ai")
            persisted = RECOVERY._load_json(path)
            entries = {item["role_id"]: item for item in persisted["payload"]["entries"]}
            self.assertEqual("READBACK_CONFIRMED", entries["atlas.inbox"]["state"])
            self.assertEqual(post_digest, entries["atlas.inbox"]["post_apply_plan_digest"])
            self.assertEqual("CREATED_PENDING_READBACK", entries["ai.questions"]["state"])

    def test_locked_journal_reload_rejects_invalid_committed_state(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            journal = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.journal_record_created(journal, plan, "atlas.inbox", "runtime-inbox")
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                RECOVERY.WorkflowRecoveryError,
                "locked reload failed",
            ):
                self.journal_record_created(journal, plan, "ai.questions", "runtime-ai")

    def test_intent_lock_release_failure_stops_before_create(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            journal = RECOVERY.CreationJournal(
                Path(temporary_directory) / "creation-journal.json",
                self.manifest,
                self.registry,
                manifest_digest,
            )
            real_release = RECOVERY._release_native_file_lock
            release_calls = 0

            def fail_record_release(handle: object, platform_name: str) -> None:
                nonlocal release_calls
                release_calls += 1
                if release_calls == 2:
                    raise OSError("injected lock release failure")
                real_release(handle, platform_name)

            with (
                mock.patch.object(
                    RECOVERY,
                    "_release_native_file_lock",
                    side_effect=fail_record_release,
                ),
                self.assertRaises(RECOVERY.WorkflowRecoveryError) as caught,
            ):
                RECOVERY.apply_plan(
                    plan,
                    self.manifest,
                    self.registry,
                    adapter,
                    creation_journal=journal,
                )

            self.assertIn("lock release failed", str(caught.exception))
            self.assertNotIsInstance(caught.exception, RECOVERY.PartialCreateFailure)
            self.assertEqual(0, adapter.mutations)
            self.assertFalse(
                any(item.role_marker == "atlas.inbox" for item in adapter.threads)
            )

    def test_create_transaction_lock_timeout_stops_before_create(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            holder = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            contender = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
                lock_timeout_seconds=0.02,
            )
            with holder.create_transaction_lock():
                with self.assertRaisesRegex(
                    RECOVERY.WorkflowRecoveryError,
                    "lock timed out",
                ):
                    RECOVERY.apply_plan(
                        plan,
                        self.manifest,
                        self.registry,
                        adapter,
                        creation_journal=contender,
                    )

            self.assertEqual(0, adapter.mutations)
            self.assertFalse(path.exists())
            self.assertTrue(holder.create_lock_path.exists())

    def test_create_failure_retains_intent_and_blocks_retry(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        create_attempts = 0
        original_mutate = adapter.mutate

        def fail_create(
            action: str,
            role: dict,
            thread: object | None,
            *,
            operation_key: str | None = None,
        ) -> object | None:
            nonlocal create_attempts
            if action == "CREATE":
                create_attempts += 1
                raise RECOVERY.WorkflowRecoveryError("injected remote create failure")
            return original_mutate(
                action,
                role,
                thread,
                operation_key=operation_key,
            )

        adapter.mutate = fail_create
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            journal = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            with self.assertRaisesRegex(
                RECOVERY.WorkflowRecoveryError,
                "injected remote create failure",
            ):
                RECOVERY.apply_plan(
                    plan,
                    self.manifest,
                    self.registry,
                    adapter,
                    creation_journal=journal,
                )

            self.assertEqual(1, create_attempts)
            self.assertEqual(0, adapter.mutations)
            self.assertTrue(path.exists())
            retained = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.assertEqual({}, retained.bindings)
            self.assertIn("atlas.inbox", retained.intents)
            restarted_adapter = self.adapter("missing-task.json")
            retained.apply_to(restarted_adapter, self.registry)
            restarted_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                restarted_adapter,
                mode="dry-run",
                deterministic=True,
            )
            restarted_inbox = self.role(restarted_plan, "atlas.inbox")
            self.assertEqual(
                "FAIL_CLOSED_UNRESOLVED_CREATE_INTENT",
                restarted_inbox["decision"],
            )
            self.assertNotIn("CREATE", restarted_inbox["actions"])
            self.assertTrue(journal.create_lock_path.exists())

    def test_process_death_after_remote_create_retains_intent_and_blocks_restart(
        self,
    ) -> None:
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        child_source = """
import importlib.util
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
journal_path = Path(sys.argv[2])
module_path = root / "ops/atlas/workflow_recovery.py"
spec = importlib.util.spec_from_file_location("atlas_workflow_recovery_child", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
manifest = module._load_json(root / module.MANIFEST_REF)
registry = module._load_json(root / module.REGISTRY_REF)
fixture = module._load_json(root / "tests/fixtures/atlas-workflow-recovery/missing-task.json")
adapter = module.FixtureAdapter(manifest, registry, fixture)
plan, _, _ = module.build_recovery_plan(
    manifest,
    registry,
    adapter,
    mode="apply",
    deterministic=True,
)
journal = module.CreationJournal(
    journal_path,
    manifest,
    registry,
    module._sha256_file(root / module.MANIFEST_REF),
)
def crash_before_binding(*args, **kwargs):
    os._exit(79)
journal.record_created = crash_before_binding
module.apply_plan(
    plan,
    manifest,
    registry,
    adapter,
    creation_journal=journal,
)
os._exit(97)
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            child = subprocess.run(
                [sys.executable, "-c", child_source, str(ROOT), str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(79, child.returncode, child.stderr)

            persisted = RECOVERY._load_json(path)
            entry = persisted["payload"]["entries"][0]
            self.assertEqual("atlas.inbox", entry["role_id"])
            self.assertEqual("CREATE_INTENT", entry["state"])
            self.assertIsNone(entry["runtime_id"])
            self.assertRegex(entry["operation_key"], r"^awci1_[0-9a-f]{64}$")

            retained = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            # The operating system releases the persistent lock handle when
            # the crashed process exits; retained intent, not a stale lock,
            # governs the next decision.
            with retained.create_transaction_lock():
                pass
            restarted_adapter = self.adapter("missing-task.json")
            retained.apply_to(restarted_adapter, self.registry)
            restarted_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                restarted_adapter,
                mode="apply",
                deterministic=True,
            )
            restarted_inbox = self.role(restarted_plan, "atlas.inbox")
            self.assertEqual(
                "FAIL_CLOSED_UNRESOLVED_CREATE_INTENT",
                restarted_inbox["decision"],
            )
            self.assertEqual([], restarted_inbox["actions"])
            self.assertEqual(0, restarted_plan["summary"]["create_count"])

    def test_exact_provider_operation_key_reconciles_without_second_create(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            journal = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            operation_key = journal.record_intent(
                plan,
                "atlas.inbox",
                "fixture",
                provider_idempotency_key_supported=True,
            )
            adapter = self.adapter("missing-task.json")
            adapter.threads.append(
                RECOVERY.ThreadRecord(
                    thread_id="fixture-provider-recovered-atlas-inbox",
                    title=None,
                    status="idle",
                    cwd="ATLAS_ROOT",
                    archived=False,
                    pinned=False,
                    preview="",
                    role_marker="atlas.inbox",
                    created_at=5000,
                    updated_at=5000,
                    raw={"atlas_create_operation_key": operation_key},
                )
            )
            journal.apply_to(adapter, self.registry)
            reconcile_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                adapter,
                mode="apply",
                deterministic=True,
            )
            reconcile_inbox = self.role(reconcile_plan, "atlas.inbox")
            self.assertEqual(
                "RECONCILE_EXACT_CREATE_INTENT",
                reconcile_inbox["decision"],
            )
            self.assertEqual("COMMIT_CREATE_INTENT", reconcile_inbox["actions"][0])
            self.assertNotIn("CREATE", reconcile_inbox["actions"])

            receipts = RECOVERY.apply_plan(
                reconcile_plan,
                self.manifest,
                self.registry,
                adapter,
                creation_journal=journal,
            )
            self.assertNotIn("CREATE", [item["action"] for item in receipts])
            self.assertEqual("COMMIT_CREATE_INTENT", receipts[0]["action"])
            committed = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.assertEqual(
                "fixture-provider-recovered-atlas-inbox",
                committed.bindings["atlas.inbox"],
            )
            self.assertEqual({}, committed.intents)
            self.assertEqual(
                1,
                sum(item.role_marker == "atlas.inbox" for item in adapter.threads),
            )

    def test_unsupported_provider_operation_key_match_remains_blocked(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            journal = RECOVERY.CreationJournal(
                Path(temporary_directory) / "creation-journal.json",
                self.manifest,
                self.registry,
                manifest_digest,
            )
            operation_key = journal.record_intent(
                plan,
                "atlas.inbox",
                "fixture",
                provider_idempotency_key_supported=False,
            )
            adapter = self.adapter("missing-task.json")
            adapter.threads.append(
                RECOVERY.ThreadRecord(
                    thread_id="fixture-untrusted-operation-key-match",
                    title=None,
                    status="idle",
                    cwd="ATLAS_ROOT",
                    archived=False,
                    pinned=False,
                    preview="",
                    role_marker="atlas.inbox",
                    created_at=5050,
                    updated_at=5050,
                    raw={"atlas_create_operation_key": operation_key},
                )
            )
            journal.apply_to(adapter, self.registry)

            blocked_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                adapter,
                mode="apply",
                deterministic=True,
            )
            blocked_inbox = self.role(blocked_plan, "atlas.inbox")
            self.assertEqual("BLOCKED", blocked_inbox["health"])
            self.assertEqual(
                "FAIL_CLOSED_UNRESOLVED_CREATE_INTENT",
                blocked_inbox["decision"],
            )
            self.assertEqual([], blocked_inbox["actions"])
            self.assertEqual(0, blocked_plan["summary"]["create_count"])

    def test_intent_reconciliation_requires_current_adapter_support_and_identity(
        self,
    ) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        cases = [
            (False, "fixture", "current adapter support is false"),
            (True, "live-app-server", "current adapter identity changed"),
        ]
        for current_support, current_name, label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary_directory:
                journal = RECOVERY.CreationJournal(
                    Path(temporary_directory) / "creation-journal.json",
                    self.manifest,
                    self.registry,
                    manifest_digest,
                )
                operation_key = journal.record_intent(
                    plan,
                    "atlas.inbox",
                    "fixture",
                    provider_idempotency_key_supported=True,
                )
                adapter = self.adapter("missing-task.json")
                adapter.create_operation_key_supported = current_support
                adapter.name = current_name
                adapter.threads.append(
                    RECOVERY.ThreadRecord(
                        thread_id=f"fixture-untrusted-{current_name}",
                        title=None,
                        status="idle",
                        cwd="ATLAS_ROOT",
                        archived=False,
                        pinned=False,
                        preview="",
                        role_marker="atlas.inbox",
                        created_at=5075,
                        updated_at=5075,
                        raw={"atlas_create_operation_key": operation_key},
                    )
                )
                journal.apply_to(adapter, self.registry)
                blocked_plan, _, _ = RECOVERY.build_recovery_plan(
                    self.manifest,
                    self.registry,
                    adapter,
                    mode="apply",
                    deterministic=True,
                )
                blocked_inbox = self.role(blocked_plan, "atlas.inbox")
                self.assertEqual(
                    "FAIL_CLOSED_UNRESOLVED_CREATE_INTENT",
                    blocked_inbox["decision"],
                )
                self.assertEqual([], blocked_inbox["actions"])

    def test_duplicate_provider_operation_key_matches_fail_closed(self) -> None:
        plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            journal = RECOVERY.CreationJournal(
                Path(temporary_directory) / "creation-journal.json",
                self.manifest,
                self.registry,
                manifest_digest,
            )
            operation_key = journal.record_intent(
                plan,
                "atlas.inbox",
                "fixture",
                provider_idempotency_key_supported=True,
            )
            adapter = self.adapter("missing-task.json")
            for index in range(2):
                adapter.threads.append(
                    RECOVERY.ThreadRecord(
                        thread_id=f"fixture-provider-duplicate-{index}",
                        title=None,
                        status="idle",
                        cwd="ATLAS_ROOT",
                        archived=False,
                        pinned=False,
                        preview="",
                        role_marker="atlas.inbox",
                        created_at=5100 + index,
                        updated_at=5100 + index,
                        raw={"atlas_create_operation_key": operation_key},
                    )
                )
            journal.apply_to(adapter, self.registry)
            duplicate_plan, _, _ = RECOVERY.build_recovery_plan(
                self.manifest,
                self.registry,
                adapter,
                mode="dry-run",
                deterministic=True,
            )
            duplicate_inbox = self.role(duplicate_plan, "atlas.inbox")
            self.assertEqual("DUPLICATE", duplicate_inbox["health"])
            self.assertEqual(
                "FAIL_CLOSED_DUPLICATE_CREATE_INTENT",
                duplicate_inbox["decision"],
            )
            self.assertEqual([], duplicate_inbox["actions"])

    def test_concurrent_missing_role_apply_creates_exactly_one_runtime(self) -> None:
        accepted_plan, _ = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        adapters = [self.adapter("missing-task.json") for _ in range(2)]
        shared_threads = adapters[0].threads
        adapters[1].threads = shared_threads
        start_barrier = threading.Barrier(2)
        counter_lock = threading.Lock()
        create_attempts = 0

        def instrument(adapter: object) -> None:
            original_discover = adapter.discover
            original_mutate = adapter.mutate
            discovery_calls = 0

            def discover() -> tuple[list[object], list[dict]]:
                nonlocal discovery_calls
                discovery_calls += 1
                if discovery_calls == 1:
                    start_barrier.wait(timeout=2)
                return original_discover()

            def mutate(
                action: str,
                role: dict,
                thread: object | None,
                *,
                operation_key: str | None = None,
            ) -> object | None:
                nonlocal create_attempts
                if action == "CREATE":
                    with counter_lock:
                        create_attempts += 1
                return original_mutate(
                    action,
                    role,
                    thread,
                    operation_key=operation_key,
                )

            adapter.discover = discover
            adapter.mutate = mutate

        for adapter in adapters:
            instrument(adapter)

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "creation-journal.json"
            journals = [
                RECOVERY.CreationJournal(
                    path,
                    self.manifest,
                    self.registry,
                    manifest_digest,
                )
                for _ in range(2)
            ]
            results: list[tuple[str, object]] = []
            results_lock = threading.Lock()

            def apply(index: int) -> None:
                try:
                    value: object = RECOVERY.apply_plan(
                        accepted_plan,
                        self.manifest,
                        self.registry,
                        adapters[index],
                        creation_journal=journals[index],
                    )
                    outcome = ("success", value)
                except BaseException as exc:  # test captures contender failure
                    outcome = ("failure", exc)
                with results_lock:
                    results.append(outcome)

            workers = [threading.Thread(target=apply, args=(index,)) for index in range(2)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=5)

            self.assertTrue(all(not worker.is_alive() for worker in workers))
            self.assertEqual(1, create_attempts)
            self.assertEqual(
                1,
                sum(item.role_marker == "atlas.inbox" for item in shared_threads),
            )
            self.assertEqual(1, sum(kind == "success" for kind, _ in results))
            failures = [value for kind, value in results if kind == "failure"]
            self.assertEqual(1, len(failures))
            self.assertIn("apply-time discovery changed", str(failures[0]))
            committed = RECOVERY.CreationJournal(
                path,
                self.manifest,
                self.registry,
                manifest_digest,
            )
            self.assertEqual(
                "fixture-created-atlas.inbox-1",
                committed.bindings["atlas.inbox"],
            )
            self.assertTrue(committed.create_lock_path.exists())

    def test_intent_committed_readback_failure_stops_before_create(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)
        with tempfile.TemporaryDirectory() as temporary_directory:
            journal = RECOVERY.CreationJournal(
                Path(temporary_directory) / "creation-journal.json",
                self.manifest,
                self.registry,
                manifest_digest,
            )
            with (
                mock.patch.object(
                    journal,
                    "_load",
                    side_effect=ValueError("injected committed readback failure"),
                ),
                self.assertRaises(RECOVERY.WorkflowRecoveryError) as caught,
            ):
                RECOVERY.apply_plan(
                    plan,
                    self.manifest,
                    self.registry,
                    adapter,
                    creation_journal=journal,
                )

            self.assertIn("committed readback failed", str(caught.exception))
            self.assertNotIsInstance(caught.exception, RECOVERY.PartialCreateFailure)
            self.assertEqual(0, adapter.mutations)
            self.assertFalse(
                any(item.role_marker == "atlas.inbox" for item in adapter.threads)
            )

    def test_intent_metadata_durability_failure_stops_before_create(self) -> None:
        plan, adapter = self.plan("missing-task.json", mode="apply")
        manifest_digest = RECOVERY._sha256_file(ROOT / RECOVERY.MANIFEST_REF)

        def fail_after_replace(source: Path, target: Path) -> None:
            RECOVERY.os.replace(source, target)
            raise OSError("injected replacement metadata durability failure")

        with tempfile.TemporaryDirectory() as temporary_directory:
            journal = RECOVERY.CreationJournal(
                Path(temporary_directory) / "creation-journal.json",
                self.manifest,
                self.registry,
                manifest_digest,
            )
            with (
                mock.patch.object(
                    RECOVERY,
                    "_durable_replace",
                    side_effect=fail_after_replace,
                ),
                self.assertRaises(RECOVERY.WorkflowRecoveryError) as caught,
            ):
                RECOVERY.apply_plan(
                    plan,
                    self.manifest,
                    self.registry,
                    adapter,
                    creation_journal=journal,
                )

            self.assertNotIsInstance(caught.exception, RECOVERY.PartialCreateFailure)
            self.assertEqual(0, adapter.mutations)
            self.assertFalse(
                any(item.role_marker == "atlas.inbox" for item in adapter.threads)
            )
            self.assertTrue(journal.path.is_file())
            self.assertIsNone(journal.event_id)
            self.assertIsNone(journal.payload_digest)

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
        receipts = RECOVERY.apply_plan(plan, self.manifest, self.registry, adapter)
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
                self.registry,
                adapter,
                creation_journal=journal,
            )
            self.assertEqual(
                ["CREATE_INTENT", "CREATE"],
                [item["action"] for item in receipts[:2]],
            )
            created_runtime_id = next(
                item["after_runtime_id"] for item in receipts if item["action"] == "CREATE"
            )
            created_thread = next(
                item for item in adapter.threads if item.thread_id == created_runtime_id
            )
            self.assertEqual(
                receipts[0]["operation_key"],
                created_thread.raw["atlas_create_operation_key"],
            )
            self.assertTrue(receipts[0]["provider_idempotency_key_supported"])
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
