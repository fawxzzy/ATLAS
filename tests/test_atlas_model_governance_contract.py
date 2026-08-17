from __future__ import annotations

import copy
import hashlib
import io
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/atlas/execution_profile_resolver.py"
REGISTRY_PATH = ROOT / "docs/registry/ATLAS-EXECUTION-PROFILES.v1.json"
REGISTRY_SCHEMA_PATH = (
    ROOT / "schemas/atlas.execution-profile.registry.v1.json"
)
OBSERVATION_SCHEMA_PATH = ROOT / "schemas/atlas.execution-observation.v1.json"
FIXTURE_PATH = (
    ROOT / "tests/fixtures/atlas-model-governance/valid-profile-registry.json"
)
DOC_PATH = (
    ROOT / "docs/ops/ATLAS-MODEL-USAGE-AND-BOUNDED-WORKER-CONTRACT.md"
)
EXACT_PATHS = (
    "docs/ops/ATLAS-MODEL-USAGE-AND-BOUNDED-WORKER-CONTRACT.md",
    "docs/registry/ATLAS-EXECUTION-PROFILES.v1.json",
    "ops/atlas/execution_profile_resolver.py",
    "schemas/atlas.execution-observation.v1.json",
    "schemas/atlas.execution-profile.registry.v1.json",
    "tests/fixtures/atlas-model-governance/valid-profile-registry.json",
    "tests/test_atlas_model_governance_contract.py",
)
SPEC = importlib.util.spec_from_file_location(
    "atlas_execution_profile_resolver", MODULE_PATH
)
assert SPEC and SPEC.loader
RESOLVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESOLVER)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class AtlasModelGovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(REGISTRY_PATH)
        cls.registry_schema = load_json(REGISTRY_SCHEMA_PATH)
        cls.observation_schema = load_json(OBSERVATION_SCHEMA_PATH)

    def requested(
        self,
        profile_id: str,
        reasoning_effort: str | None = None,
        workload_class: str | None = None,
    ) -> dict:
        profile = self.registry["profiles"][profile_id]
        return {
            "benchmark_exception_id": None,
            "context_budget": {
                "compaction_checkpoint_required": True,
                "freshness_rule": "CONTENT_ADDRESSED_REFS_AND_ACTION_TIME_READBACK",
                "immutable_ref_count": 3,
                "max_bundle_bytes": 65536,
                "maximum_repeated_evidence_bytes": 2480,
            },
            "escalation_policy": "FAIL_CLOSED_AND_RETURN_CONTENT_ADDRESSED_HOLD",
            "evidence_tier": "E3",
            "execution_binding": {
                "host_id": "local",
                "logical_role_id": "atlas.workflow-architect",
                "runtime_epoch_id": "runtime-epoch-001",
                "runtime_thread_id": "runtime-thread-001",
            },
            "fallback_policy": "NO_SILENT_FALLBACK",
            "model": profile["model"],
            "profile_id": profile_id,
            "profile_version": self.registry["profile_version"],
            "reasoning_effort": reasoning_effort
            or profile["reasoning_default"],
            "retry_budget": {
                "max_attempts": 1,
                "retryable_classes": ["TRANSIENT_TRANSPORT"],
                "terminal_classes": ["IDENTITY_MISMATCH", "ACCEPTANCE_FAILURE"],
            },
            "selection_reason": "REPRESENTATIVE_EVAL_AND_ROLE_RISK",
            "token_budget": {
                "enforcement": "OBSERVE_ONLY",
                "max_output_tokens": None,
                "max_total_tokens": None,
            },
            "turn_budget": {
                "escalation_at_turn": 3,
                "max_turns": 4,
            },
            "workload_class": workload_class
            or profile["workload_classes"][0],
        }

    @staticmethod
    def effective(
        model: str, reasoning_effort: str, execution_binding: dict
    ) -> dict:
        return {
            "adapter_id": "codex",
            "adapter_version": "desktop-current",
            "execution_binding": {
                **copy.deepcopy(execution_binding),
                "turn_id": "turn-001",
            },
            "fallback_reason": None,
            "model": model,
            "provider": "openai",
            "readback_source": "LIVE_CODEX_THREAD_STATUS",
            "reasoning_effort": reasoning_effort,
            "runtime_version": "current",
        }

    @staticmethod
    def usage() -> dict:
        return {
            "cached_input_tokens": None,
            "child_workers": 0,
            "correction_loops": 0,
            "elapsed_to_material_state_ms": 100,
            "escalation_checkpoint_observed": False,
            "files_read": 2,
            "input_bundle_bytes": 1024,
            "input_tokens": None,
            "output_tokens": None,
            "provider_cost": None,
            "reasoning_tokens": None,
            "repeated_evidence_bytes": 512,
            "retry_attempts": 0,
            "tool_calls": 1,
            "turns": 1,
            "unique_evidence_refs": 3,
        }

    def canary_result(
        self, definition: dict, *, repeated_evidence_bytes: int = 2480
    ) -> dict:
        canaries = self.registry["canaries"]
        baseline = canaries["baseline_repeated_evidence_bytes"]
        return {
            "accepted": True,
            "baseline_event_id": canaries["baseline_event_id"],
            "baseline_repeated_evidence_bytes": baseline,
            "canary_class": definition["class"],
            "comparison": {
                "QUALITY": {
                    "baseline": 100,
                    "candidate": 100,
                    "passed": True,
                },
                "COMPLETENESS": {
                    "baseline": 100,
                    "candidate": 100,
                    "passed": True,
                },
                "TOOL_CORRECTNESS": {
                    "baseline": 100,
                    "candidate": 100,
                    "passed": True,
                },
                "LATENCY": {
                    "baseline": 1000,
                    "candidate": 900,
                    "passed": True,
                },
                "TURNS": {
                    "baseline": 3,
                    "candidate": 2,
                    "passed": True,
                },
                "TOKEN_PROXIES": {
                    "baseline": 3000,
                    "candidate": 2000,
                    "passed": True,
                },
            },
            "dropped_acceptance_criteria": 0,
            "dropped_required_evidence_refs": 0,
            "evidence_tier": definition["evidence_tier"],
            "profile_id": definition["allowed_profiles"][0],
            "repeated_context_reduction_percent": (
                baseline - repeated_evidence_bytes
            )
            * 100
            / baseline,
            "repeated_evidence_bytes": repeated_evidence_bytes,
        }

    def canary_campaign(self) -> dict:
        results = [
            self.canary_result(definition)
            for definition in self.registry["canaries"]["classes"]
        ]
        digests = [RESOLVER._canary_result_digest(result) for result in results]
        return {
            "canary_result_digests": digests,
            "canary_results": results,
        }

    def resolve(
        self,
        role_id: str,
        requested: dict,
        effective: dict | None = None,
        usage: dict | None = None,
        admitted_execution_binding: dict | None = None,
        registry: dict | None = None,
    ) -> dict:
        requested = copy.deepcopy(requested)
        requested["execution_binding"]["logical_role_id"] = role_id
        admitted_binding = copy.deepcopy(
            admitted_execution_binding or requested["execution_binding"]
        )
        if admitted_execution_binding is None:
            admitted_binding["turn_id"] = "turn-001"
        return RESOLVER.resolve_execution(
            registry or self.registry,
            packet_id="packet-001",
            logical_role_id=role_id,
            admitted_execution_binding=admitted_binding,
            requested=requested,
            effective=effective
            or self.effective(
                requested["model"],
                requested["reasoning_effort"],
                requested["execution_binding"],
            ),
            usage=copy.deepcopy(usage) if usage is not None else self.usage(),
        )

    def test_registry_and_fixture_validate_against_closed_schema(self) -> None:
        self.assertEqual(
            [],
            RESOLVER.validate_schema_document(
                self.registry_schema,
                expected_id="atlas://schemas/atlas.execution-profile.registry.v1.json",
            ),
        )
        self.assertEqual(
            [], RESOLVER.schema_errors(self.registry, self.registry_schema)
        )
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual(
            [], RESOLVER.schema_errors(fixture, self.registry_schema)
        )
        self.assertEqual(self.registry, fixture)
        self.assertEqual([], RESOLVER.validate_registry(self.registry))

    def test_invalid_registry_matrix_fails_closed(self) -> None:
        cases = []
        extra = copy.deepcopy(self.registry)
        extra["unexpected"] = True
        cases.append(extra)
        missing = copy.deepcopy(self.registry)
        del missing["profiles"]["FAST"]
        cases.append(missing)
        invalid_model = copy.deepcopy(self.registry)
        invalid_model["profiles"]["FAST"]["model"] = "gpt-5.6-sol"
        cases.append(invalid_model)
        for index, candidate in enumerate(cases):
            with self.subTest(case=index):
                schema_findings = RESOLVER.schema_errors(
                    candidate, self.registry_schema
                )
                semantic_findings = RESOLVER.validate_registry(candidate)
                self.assertTrue(schema_findings or semantic_findings)

    def test_profile_matrix_all_four_classes(self) -> None:
        expected = {
            "FAST": ("gpt-5.6-luna", "low", ("low", "medium")),
            "STANDARD": (
                "gpt-5.6-terra",
                "medium",
                ("medium", "high"),
            ),
            "DEEP": ("gpt-5.6-sol", "high", ("high", "xhigh")),
            "CRITICAL": ("gpt-5.6-sol", "xhigh", ("xhigh", "max")),
        }
        for profile_id, (model, default, allowed) in expected.items():
            with self.subTest(profile=profile_id):
                profile = self.registry["profiles"][profile_id]
                self.assertEqual(model, profile["model"])
                self.assertEqual(default, profile["reasoning_default"])
                self.assertEqual(allowed, tuple(profile["reasoning_allowed"]))

    def test_packet_selection_and_role_floor_fail_closed(self) -> None:
        requested = self.requested("STANDARD", "high")
        allowed = self.resolve("atlas.release-control-plane", requested)
        self.assertEqual("ADMITTED", allowed["decision"]["state"])

        below_floor = self.resolve(
            "atlas.workflow-architect", self.requested("STANDARD", "high")
        )
        self.assertIn(
            "requested_profile_below_role_floor",
            below_floor["decision"]["findings"],
        )
        self.assertEqual("BLOCKED", below_floor["decision"]["state"])

        missing_role = self.resolve("owner.unregistered", requested)
        self.assertIn("role_policy_missing", missing_role["decision"]["findings"])

    def test_fitness_high_floor_accepts_terra_high_and_sol(self) -> None:
        valid = (
            self.requested("STANDARD", "high"),
            self.requested("DEEP", "high"),
            self.requested("DEEP", "xhigh"),
            self.requested("CRITICAL", "xhigh"),
        )
        for requested in valid:
            with self.subTest(
                profile=requested["profile_id"],
                effort=requested["reasoning_effort"],
            ):
                result = self.resolve("owner.fitness", requested)
                self.assertEqual([], result["decision"]["findings"])
                self.assertEqual("ADMITTED", result["decision"]["state"])

    def test_fitness_rejects_fast_and_standard_medium(self) -> None:
        fast = self.resolve("owner.fitness", self.requested("FAST", "low"))
        self.assertIn(
            "requested_profile_below_role_floor", fast["decision"]["findings"]
        )
        self.assertIn(
            "requested_reasoning_below_role_floor",
            fast["decision"]["findings"],
        )

        standard_medium = self.resolve(
            "owner.fitness", self.requested("STANDARD", "medium")
        )
        self.assertIn(
            "requested_reasoning_below_role_floor",
            standard_medium["decision"]["findings"],
        )

    def test_requested_effective_match_validates_observation_schema(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        result = self.resolve("atlas.workflow-architect", requested)
        self.assertEqual("ADMITTED", result["decision"]["state"])
        self.assertEqual(
            [],
            RESOLVER.validate_schema_document(
                self.observation_schema,
                expected_id="atlas://schemas/atlas.execution-observation.v1.json",
            ),
        )
        self.assertEqual(
            [], RESOLVER.schema_errors(result, self.observation_schema)
        )

    def test_execution_binding_requires_exact_current_runtime_epoch(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        cases = (
            ("host_id", "", "effective_execution_binding_unproven:host_id"),
            (
                "host_id",
                "UNKNOWN",
                "effective_execution_binding_unproven:host_id",
            ),
            (
                "runtime_thread_id",
                "runtime-thread-stale",
                "effective_execution_binding_mismatch:runtime_thread_id",
            ),
            (
                "runtime_epoch_id",
                "runtime-epoch-stale",
                "effective_execution_binding_mismatch:runtime_epoch_id",
            ),
            (
                "turn_id",
                " ",
                "effective_execution_binding_unproven:turn_id",
            ),
            (
                "turn_id",
                "UNKNOWN",
                "effective_execution_binding_unproven:turn_id",
            ),
            (
                "turn_id",
                "turn-drifted-not-admitted",
                "effective_execution_binding_mismatch:turn_id",
            ),
        )
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                effective = self.effective(
                    requested["model"],
                    requested["reasoning_effort"],
                    requested["execution_binding"],
                )
                effective["execution_binding"][field] = value
                result = self.resolve(
                    "atlas.workflow-architect", requested, effective
                )
                self.assertEqual("BLOCKED", result["decision"]["state"])
                self.assertIn(expected, result["decision"]["findings"])

        requested_blank = self.requested(
            "DEEP", "xhigh", "ARCHITECTURE"
        )
        requested_blank["execution_binding"]["host_id"] = " "
        blocked = self.resolve(
            "atlas.workflow-architect", requested_blank
        )
        self.assertIn(
            "requested_execution_binding_unproven:host_id",
            blocked["decision"]["findings"],
        )

        requested_stale = self.requested(
            "DEEP", "xhigh", "ARCHITECTURE"
        )
        admitted_current = copy.deepcopy(
            requested_stale["execution_binding"]
        )
        admitted_current["runtime_epoch_id"] = "runtime-epoch-002"
        drifted = self.resolve(
            "atlas.workflow-architect",
            requested_stale,
            admitted_execution_binding=admitted_current,
        )
        self.assertIn(
            "requested_execution_binding_not_admitted:runtime_epoch_id",
            drifted["decision"]["findings"],
        )

    def test_effective_turn_requires_exact_scheduler_admission(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        exact_admitted = copy.deepcopy(requested["execution_binding"])
        exact_admitted["turn_id"] = "turn-001"

        admitted_cases = (
            (
                lambda value: value.pop("turn_id"),
                "admitted_execution_binding_unproven:turn_id",
            ),
            (
                lambda value: value.update(turn_id=" "),
                "admitted_execution_binding_unproven:turn_id",
            ),
            (
                lambda value: value.update(turn_id="UNKNOWN"),
                "admitted_execution_binding_unproven:turn_id",
            ),
        )
        for mutate, expected in admitted_cases:
            with self.subTest(admitted=expected):
                admitted = copy.deepcopy(exact_admitted)
                mutate(admitted)
                result = self.resolve(
                    "atlas.workflow-architect",
                    requested,
                    admitted_execution_binding=admitted,
                )
                self.assertEqual("BLOCKED", result["decision"]["state"])
                self.assertIn(expected, result["decision"]["findings"])

        effective = self.effective(
            requested["model"],
            requested["reasoning_effort"],
            requested["execution_binding"],
        )
        effective["execution_binding"]["turn_id"] = "turn-drifted-not-admitted"
        drifted = self.resolve(
            "atlas.workflow-architect",
            requested,
            effective,
            admitted_execution_binding=exact_admitted,
        )
        self.assertEqual("BLOCKED", drifted["decision"]["state"])
        self.assertIn(
            "effective_execution_binding_mismatch:turn_id",
            drifted["decision"]["findings"],
        )

    def test_resolver_blocks_schema_invalid_requested_observations(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        del requested["benchmark_exception_id"]
        missing = self.resolve("atlas.workflow-architect", requested)
        self.assertEqual("BLOCKED", missing["decision"]["state"])
        self.assertIn(
            "requested_field_missing:benchmark_exception_id",
            missing["decision"]["findings"],
        )
        self.assertTrue(
            any(
                item.startswith("observation_schema_invalid:")
                for item in missing["decision"]["findings"]
            )
        )

        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        requested["unexpected"] = "not-closed"
        extra = self.resolve("atlas.workflow-architect", requested)
        self.assertEqual("BLOCKED", extra["decision"]["state"])
        self.assertTrue(
            any(
                "requested.unexpected: property is not allowed" in item
                for item in extra["decision"]["findings"]
            )
        )

    def test_unknown_effective_identity_fails_closed(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        effective = self.effective(
            requested["model"],
            requested["reasoning_effort"],
            requested["execution_binding"],
        )
        effective["model"] = "UNKNOWN"
        result = self.resolve("atlas.workflow-architect", requested, effective)
        self.assertEqual("BLOCKED", result["decision"]["state"])
        self.assertIn(
            "effective_identity_unproven:model", result["decision"]["findings"]
        )

    def test_silent_model_reasoning_and_provider_downgrades_rejected(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        cases = (
            ("model", "gpt-5.6-terra", "effective_model_mismatch"),
            ("reasoning_effort", "high", "effective_reasoning_mismatch"),
            ("provider", "other", "effective_provider_mismatch"),
            ("fallback_reason", "automatic_cost_route", "silent_or_unapproved_fallback_detected"),
        )
        for field, value, finding in cases:
            with self.subTest(field=field):
                effective = self.effective(
                    requested["model"],
                    requested["reasoning_effort"],
                    requested["execution_binding"],
                )
                effective[field] = value
                result = self.resolve(
                    "atlas.workflow-architect", requested, effective
                )
                self.assertIn(finding, result["decision"]["findings"])
                self.assertEqual("BLOCKED", result["decision"]["state"])

    def test_max_requires_critical_profile_and_benchmark_exception(self) -> None:
        critical = self.requested("CRITICAL", "max")
        blocked = self.resolve("atlas.main", critical)
        self.assertIn(
            "max_reasoning_benchmark_exception_missing",
            blocked["decision"]["findings"],
        )
        critical["benchmark_exception_id"] = "bench-critical-001"
        allowed = self.resolve("atlas.main", critical)
        self.assertEqual("ADMITTED", allowed["decision"]["state"])

        deep = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        deep["reasoning_effort"] = "max"
        deep["benchmark_exception_id"] = "bench-invalid-001"
        effective = self.effective(
            deep["model"], "max", deep["execution_binding"]
        )
        invalid = self.resolve("atlas.workflow-architect", deep, effective)
        self.assertIn(
            "requested_reasoning_not_allowed", invalid["decision"]["findings"]
        )
        self.assertIn(
            "max_reasoning_requires_critical_profile",
            invalid["decision"]["findings"],
        )

    def test_budgets_and_evidence_tiers_are_closed(self) -> None:
        requested = self.requested("DEEP", "high", "ARCHITECTURE")
        requested["turn_budget"]["escalation_at_turn"] = 5
        result = self.resolve("atlas.workflow-architect", requested)
        self.assertIn(
            "turn_budget_escalation_invalid", result["decision"]["findings"]
        )
        requested = self.requested("DEEP", "high", "ARCHITECTURE")
        requested["evidence_tier"] = "E5"
        result = self.resolve("atlas.workflow-architect", requested)
        self.assertIn("evidence_tier_invalid", result["decision"]["findings"])

    def test_budget_limits_enforce_equality_one_over_and_checkpoint(self) -> None:
        requested = self.requested("DEEP", "high", "ARCHITECTURE")
        requested["context_budget"].update(
            {
                "immutable_ref_count": 2,
                "max_bundle_bytes": 100,
                "maximum_repeated_evidence_bytes": 50,
            }
        )
        requested["token_budget"] = {
            "enforcement": "HARD_LIMIT",
            "max_output_tokens": 100,
            "max_total_tokens": 300,
        }
        usage = self.usage()
        usage.update(
            {
                "input_bundle_bytes": 100,
                "input_tokens": 150,
                "output_tokens": 100,
                "reasoning_tokens": 50,
                "repeated_evidence_bytes": 50,
                "retry_attempts": 1,
                "turns": 2,
                "unique_evidence_refs": 2,
            }
        )
        equal = self.resolve(
            "atlas.workflow-architect", requested, usage=usage
        )
        self.assertEqual([], equal["decision"]["findings"])

        cases = (
            (
                "input_bundle_bytes",
                101,
                "context_budget_exceeded:input_bundle_bytes",
            ),
            (
                "repeated_evidence_bytes",
                51,
                "context_budget_exceeded:repeated_evidence_bytes",
            ),
            (
                "unique_evidence_refs",
                1,
                "context_budget_immutable_refs_missing",
            ),
            ("turns", 5, "turn_budget_exceeded"),
            ("retry_attempts", 2, "retry_budget_exceeded"),
            ("output_tokens", 101, "hard_limit_output_tokens_exceeded"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field):
                over = copy.deepcopy(usage)
                over[field] = value
                result = self.resolve(
                    "atlas.workflow-architect", requested, usage=over
                )
                self.assertIn(expected, result["decision"]["findings"])
                self.assertEqual("BLOCKED", result["decision"]["state"])

        total_over = copy.deepcopy(usage)
        total_over["input_tokens"] = 151
        result = self.resolve(
            "atlas.workflow-architect", requested, usage=total_over
        )
        self.assertIn(
            "hard_limit_total_tokens_exceeded",
            result["decision"]["findings"],
        )

        checkpoint = copy.deepcopy(usage)
        checkpoint["turns"] = requested["turn_budget"]["escalation_at_turn"]
        result = self.resolve(
            "atlas.workflow-architect", requested, usage=checkpoint
        )
        self.assertIn(
            "turn_budget_escalation_checkpoint_missing",
            result["decision"]["findings"],
        )
        checkpoint["escalation_checkpoint_observed"] = True
        admitted = self.resolve(
            "atlas.workflow-architect", requested, usage=checkpoint
        )
        self.assertEqual([], admitted["decision"]["findings"])

        observe_only = self.requested("DEEP", "high", "ARCHITECTURE")
        nullable = self.resolve(
            "atlas.workflow-architect", observe_only, usage=self.usage()
        )
        self.assertEqual([], nullable["decision"]["findings"])

    def test_registry_rejects_same_version_profile_mapping_drift(self) -> None:
        cases = (
            ("reasoning_allowed", ["high"]),
            ("reasoning_default", "medium"),
            ("reasoning_elevation_rule", "UNREVIEWED_RULE"),
            ("workload_classes", ["UNREVIEWED_WORKLOAD"]),
        )
        for field, value in cases:
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.registry)
                candidate["profiles"]["FAST"][field] = value
                schema_findings = RESOLVER.schema_errors(
                    candidate, self.registry_schema
                )
                self.assertTrue(schema_findings)
                self.assertTrue(
                    all(
                        item.startswith("registry_schema_invalid:")
                        for item in RESOLVER.validate_registry(candidate)
                    )
                )

    def test_registry_freezes_exact_standing_role_policy_mapping(self) -> None:
        downgrade = copy.deepcopy(self.registry)
        downgrade["role_policies"]["atlas.main"] = {
            "default_profile": "FAST",
            "floor_profile": "FAST",
            "minimum_reasoning_effort": "low",
        }
        removed = copy.deepcopy(self.registry)
        del removed["role_policies"]["atlas.main"]
        extra = copy.deepcopy(self.registry)
        extra["role_policies"]["owner.unreviewed"] = {
            "default_profile": "FAST",
            "floor_profile": "FAST",
            "minimum_reasoning_effort": "low",
        }
        for label, candidate in (
            ("downgrade", downgrade),
            ("removed", removed),
            ("extra", extra),
        ):
            with self.subTest(case=label):
                self.assertTrue(
                    RESOLVER.schema_errors(candidate, self.registry_schema)
                )
                findings = RESOLVER.validate_registry(candidate)
                self.assertTrue(findings)
                self.assertTrue(
                    all(
                        item.startswith("registry_schema_invalid:")
                        for item in findings
                    )
                )

    def test_resolver_and_cli_enforce_closed_registry_schema(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        extra = copy.deepcopy(self.registry)
        extra["unexpected"] = True
        missing = copy.deepcopy(self.registry)
        del missing["source_evidence"]
        for label, candidate in (("extra", extra), ("missing", missing)):
            with self.subTest(boundary="resolver", case=label):
                result = self.resolve(
                    "atlas.workflow-architect",
                    requested,
                    registry=candidate,
                )
                self.assertEqual("BLOCKED", result["decision"]["state"])
                self.assertTrue(
                    any(
                        item.startswith("registry_schema_invalid:")
                        for item in result["decision"]["findings"]
                    )
                )

            with self.subTest(boundary="cli", case=label):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "invalid-registry.json"
                    path.write_text(
                        json.dumps(
                            candidate,
                            allow_nan=False,
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(MODULE_PATH),
                            "--registry",
                            str(path),
                            "--json",
                        ],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(1, completed.returncode)
                cli_result = json.loads(completed.stdout)
                self.assertEqual("BLOCKED", cli_result["status"])
                self.assertTrue(
                    any(
                        item.startswith("registry_schema_invalid:")
                        for item in cli_result["findings"]
                    )
                )

    def test_nested_schema_invalid_registry_fails_closed_without_traceback(
        self,
    ) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        cases = []
        for label, path, value in (
            ("profile_null", ("profiles", "FAST"), None),
            ("profile_scalar", ("profiles", "FAST"), "invalid"),
            ("boundary_null", ("worker_adapter_boundary",), None),
            ("boundary_scalar", ("worker_adapter_boundary",), 7),
            ("canaries_null", ("canaries",), None),
            ("canaries_scalar", ("canaries",), "invalid"),
        ):
            candidate = copy.deepcopy(self.registry)
            target = candidate
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            cases.append((label, candidate))

        canary_result = self.canary_result(self.registry["canaries"]["classes"][0])
        for label, candidate in cases:
            with self.subTest(boundary="resolver", case=label):
                result = self.resolve(
                    "atlas.workflow-architect",
                    requested,
                    registry=candidate,
                )
                self.assertEqual("BLOCKED", result["decision"]["state"])
                self.assertTrue(
                    any(
                        item.startswith("registry_schema_invalid:")
                        for item in result["decision"]["findings"]
                    )
                )
                json.dumps(result, allow_nan=False, sort_keys=True)

            with self.subTest(boundary="canary", case=label):
                findings = RESOLVER.validate_canary_result(
                    candidate, canary_result
                )
                self.assertTrue(
                    any(
                        item.startswith("registry_schema_invalid:")
                        for item in findings
                    )
                )

            with self.subTest(boundary="cli", case=label):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "invalid-registry.json"
                    path.write_text(
                        json.dumps(
                            candidate,
                            allow_nan=False,
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(MODULE_PATH),
                            "--registry",
                            str(path),
                            "--json",
                        ],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(1, completed.returncode)
                self.assertNotIn("Traceback", completed.stdout)
                self.assertNotIn("Traceback", completed.stderr)
                cli_result = json.loads(completed.stdout)
                self.assertEqual("BLOCKED", cli_result["status"])
                self.assertTrue(
                    any(
                        item.startswith("registry_schema_invalid:")
                        for item in cli_result["findings"]
                    )
                )

    def test_complete_registry_property_matrix_short_circuits_structurally(
        self,
    ) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        canary_result = self.canary_result(self.registry["canaries"]["classes"][0])

        def property_paths(value: object, prefix: tuple = ()) -> list[tuple]:
            paths = []
            if isinstance(value, dict):
                for key, child in value.items():
                    path = prefix + (key,)
                    paths.append(path)
                    paths.extend(property_paths(child, path))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    path = prefix + (index,)
                    paths.append(path)
                    paths.extend(property_paths(child, path))
            return paths

        def replace_path(candidate: object, path: tuple, value: object) -> None:
            target = candidate
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value

        def invalid_values(value: object) -> tuple:
            if isinstance(value, dict):
                return (None, "invalid", [])
            if isinstance(value, list):
                return (None, "invalid", {})
            if isinstance(value, str):
                return (None, 7, {})
            return (None, "invalid", {})

        property_matrix = []
        for path in property_paths(self.registry):
            target = self.registry
            for key in path:
                target = target[key]
            for invalid in invalid_values(target):
                candidate = copy.deepcopy(self.registry)
                replace_path(candidate, path, invalid)
                property_matrix.append((path, invalid, candidate))

        with tempfile.TemporaryDirectory() as temporary:
            registry_path = Path(temporary) / "invalid-registry.json"
            for path, invalid, candidate in property_matrix:
                case = f"{path}={invalid!r}"
                with self.subTest(boundary="schema", case=case):
                    self.assertTrue(
                        RESOLVER.schema_errors(candidate, self.registry_schema)
                    )
                    findings = RESOLVER.validate_registry(candidate)
                    self.assertTrue(findings)
                    self.assertTrue(
                        all(
                            item.startswith("registry_schema_invalid:")
                            for item in findings
                        )
                    )

                with self.subTest(boundary="resolver", case=case):
                    result = self.resolve(
                        "atlas.workflow-architect",
                        requested,
                        registry=candidate,
                    )
                    self.assertEqual("BLOCKED", result["decision"]["state"])
                    self.assertTrue(
                        all(
                            item.startswith("registry_schema_invalid:")
                            for item in result["decision"]["findings"]
                        )
                    )
                    json.dumps(result, allow_nan=False, sort_keys=True)

                with self.subTest(boundary="canary", case=case):
                    findings = RESOLVER.validate_canary_result(
                        candidate, canary_result
                    )
                    self.assertTrue(findings)
                    self.assertTrue(
                        all(
                            item.startswith("registry_schema_invalid:")
                            for item in findings
                        )
                    )

                with self.subTest(boundary="cli", case=case):
                    registry_path.write_text(
                        json.dumps(
                            candidate,
                            allow_nan=False,
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        exit_code = RESOLVER._main(
                            [
                                "--registry",
                                str(registry_path),
                                "--json",
                            ]
                        )
                    self.assertEqual(1, exit_code)
                    cli_result = json.loads(stdout.getvalue())
                    self.assertEqual("BLOCKED", cli_result["status"])
                    self.assertTrue(
                        all(
                            item.startswith("registry_schema_invalid:")
                            for item in cli_result["findings"]
                        )
                    )

        self.assertGreater(len(property_matrix), 0)

    def test_provider_cost_rejects_nonfinite_and_boolean_values(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        cases = (True, float("nan"), float("inf"), float("-inf"))
        for value in cases:
            with self.subTest(value=repr(value)):
                usage = self.usage()
                usage["provider_cost"] = value
                result = self.resolve(
                    "atlas.workflow-architect",
                    requested,
                    usage=usage,
                )
                self.assertEqual("BLOCKED", result["decision"]["state"])
                self.assertIn(
                    "usage_exact_invalid:provider_cost",
                    result["decision"]["findings"],
                )
                self.assertIsNone(result["usage"]["provider_cost"])
                json.dumps(result, allow_nan=False, sort_keys=True)

                schema_invalid = copy.deepcopy(result)
                schema_invalid["usage"]["provider_cost"] = value
                self.assertTrue(
                    RESOLVER.schema_errors(
                        schema_invalid,
                        self.observation_schema,
                    )
                )

        for value in (0, 0.25):
            with self.subTest(valid=repr(value)):
                usage = self.usage()
                usage["provider_cost"] = value
                result = self.resolve(
                    "atlas.workflow-architect",
                    requested,
                    usage=usage,
                )
                self.assertEqual("ADMITTED", result["decision"]["state"])
                self.assertEqual(value, result["usage"]["provider_cost"])

    def test_observation_id_addresses_final_decision_and_findings(self) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        admitted = self.resolve("atlas.workflow-architect", requested)
        drifted_registry = copy.deepcopy(self.registry)
        drifted_registry["profiles"]["DEEP"]["reasoning_default"] = "xhigh"
        blocked = self.resolve(
            "atlas.workflow-architect",
            requested,
            registry=drifted_registry,
        )

        self.assertEqual("ADMITTED", admitted["decision"]["state"])
        self.assertEqual("BLOCKED", blocked["decision"]["state"])
        self.assertNotEqual(admitted["observation_id"], blocked["observation_id"])
        for observation in (admitted, blocked):
            identity_payload = {
                key: value
                for key, value in observation.items()
                if key != "observation_id"
            }
            expected = (
                "onv1_"
                + hashlib.sha256(
                    RESOLVER.canonical_bytes(identity_payload)
                ).hexdigest()
            )
            self.assertEqual(expected, observation["observation_id"])

    def test_canary_comparison_rejects_nonfinite_values(self) -> None:
        definition = self.registry["canaries"]["classes"][0]
        for value in (float("nan"), float("inf"), float("-inf")):
            for field in ("baseline", "candidate"):
                with self.subTest(value=repr(value), field=field):
                    result = self.canary_result(definition)
                    result["comparison"]["QUALITY"][field] = value
                    self.assertIn(
                        "canary_comparison_values_invalid:QUALITY",
                        RESOLVER.validate_canary_result(self.registry, result),
                    )

    def test_nonfinite_unique_items_fail_closed_in_schema_and_cli(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=repr(value)):
                candidate = copy.deepcopy(self.registry)
                candidate["policy_ids"] = [value]
                findings = RESOLVER.validate_registry(candidate)
                self.assertTrue(findings)
                self.assertTrue(
                    all(
                        item.startswith("registry_schema_invalid:")
                        for item in findings
                    )
                )

                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "nonfinite-registry.json"
                    path.write_text(
                        json.dumps(
                            candidate,
                            allow_nan=True,
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(MODULE_PATH),
                            "--registry",
                            str(path),
                            "--json",
                        ],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(1, completed.returncode)
                self.assertNotIn("Traceback", completed.stdout)
                self.assertNotIn("Traceback", completed.stderr)
                cli_result = json.loads(completed.stdout)
                self.assertEqual("BLOCKED", cli_result["status"])

    def test_public_boundaries_block_malformed_roots_without_traceback(
        self,
    ) -> None:
        requested = self.requested("DEEP", "xhigh", "ARCHITECTURE")
        admitted_binding = copy.deepcopy(requested["execution_binding"])
        admitted_binding["turn_id"] = "turn-001"
        effective = self.effective(
            requested["model"],
            requested["reasoning_effort"],
            requested["execution_binding"],
        )
        for root_name, malformed in (
            ("requested", None),
            ("requested", []),
            ("requested", "invalid"),
            ("effective", None),
            ("effective", []),
            ("effective", "invalid"),
        ):
            with self.subTest(root=root_name, value=repr(malformed)):
                kwargs = {
                    "registry": self.registry,
                    "packet_id": "packet-001",
                    "logical_role_id": "atlas.workflow-architect",
                    "admitted_execution_binding": admitted_binding,
                    "requested": requested,
                    "effective": effective,
                    "usage": self.usage(),
                }
                kwargs[root_name] = malformed
                observation = RESOLVER.resolve_execution(**kwargs)
                self.assertEqual("BLOCKED", observation["decision"]["state"])
                self.assertIn(
                    f"{root_name}_root_invalid",
                    observation["decision"]["findings"],
                )
                json.dumps(observation, allow_nan=False, sort_keys=True)

        for malformed in (None, [], "invalid"):
            with self.subTest(root="canary", value=repr(malformed)):
                findings = RESOLVER.validate_canary_result(
                    self.registry, malformed
                )
                self.assertIn("canary_result_root_invalid", findings)

    def test_five_canaries_bind_baseline_and_acceptance(self) -> None:
        canaries = self.registry["canaries"]
        self.assertEqual(5, len(canaries["classes"]))
        self.assertEqual(
            "onv1_f2c164eb892f46fa66ea834c6bba96206a3109a9e6817b765d1546690e900502",
            canaries["baseline_event_id"],
        )
        for definition in canaries["classes"]:
            result = self.canary_result(definition)
            with self.subTest(canary=definition["class"]):
                self.assertEqual(
                    [], RESOLVER.validate_canary_result(self.registry, result)
                )

        regressed = self.canary_result(canaries["classes"][0])
        regressed["dropped_acceptance_criteria"] = 1
        self.assertIn(
            "canary_dropped_acceptance_criteria",
            RESOLVER.validate_canary_result(self.registry, regressed),
        )

    def test_canary_result_field_and_regression_matrix_fails_closed(self) -> None:
        duplicate = copy.deepcopy(self.registry)
        duplicate["canaries"]["classes"] = [
            copy.deepcopy(self.registry["canaries"]["classes"][0])
            for _ in range(5)
        ]
        self.assertTrue(
            RESOLVER.schema_errors(duplicate, self.registry_schema)
        )
        self.assertTrue(
            all(
                item.startswith("registry_schema_invalid:")
                for item in RESOLVER.validate_registry(duplicate)
            )
        )

        definition = self.registry["canaries"]["classes"][0]
        complete = self.canary_result(definition)
        cases = []
        minimal = {
            "accepted": True,
            "canary_class": definition["class"],
            "dropped_acceptance_criteria": 0,
            "dropped_required_evidence_refs": 0,
            "evidence_tier": definition["evidence_tier"],
            "profile_id": definition["allowed_profiles"][0],
            "repeated_evidence_bytes": 2480,
        }
        cases.append((minimal, "canary_result_fields_mismatch"))

        missing_dimension = copy.deepcopy(complete)
        del missing_dimension["comparison"]["TOKEN_PROXIES"]
        cases.append(
            (
                missing_dimension,
                "canary_comparison_dimensions_mismatch",
            )
        )

        regressed = copy.deepcopy(complete)
        regressed["comparison"]["QUALITY"]["candidate"] = 99
        cases.append((regressed, "canary_comparison_regressed:QUALITY"))

        inconsistent = copy.deepcopy(complete)
        inconsistent["repeated_context_reduction_percent"] = 99
        cases.append(
            (inconsistent, "canary_reduction_calculation_mismatch")
        )

        below_target = self.canary_result(
            definition, repeated_evidence_bytes=3000
        )
        cases.append((below_target, "canary_reduction_target_not_met"))

        for index, (candidate, expected) in enumerate(cases):
            with self.subTest(case=index):
                findings = RESOLVER.validate_canary_result(
                    self.registry, candidate
                )
                self.assertIn(expected, findings)

    def test_five_canary_campaign_requires_five_unique_content_addressed_results(
        self,
    ) -> None:
        campaign = self.canary_campaign()
        self.assertEqual(
            [], RESOLVER.validate_canary_campaign(self.registry, campaign)
        )

        # Too few results: a caller cannot claim completion evidence for
        # canaries whose result payloads were never actually submitted.
        too_few = copy.deepcopy(campaign)
        too_few["canary_results"] = too_few["canary_results"][:4]
        too_few["canary_result_digests"] = too_few["canary_result_digests"][:4]
        findings = RESOLVER.validate_canary_campaign(self.registry, too_few)
        self.assertIn("canary_campaign_result_count_invalid", findings)
        self.assertIn("canary_campaign_classes_incomplete", findings)

        # A result standing in twice for two different classes (instead of
        # five distinct classes each appearing once) must fail closed, even
        # though it is still five well-formed results.
        duplicated_class = copy.deepcopy(campaign)
        duplicated_class["canary_results"][1] = copy.deepcopy(
            duplicated_class["canary_results"][0]
        )
        duplicated_class["canary_result_digests"] = [
            RESOLVER._canary_result_digest(result)
            for result in duplicated_class["canary_results"]
        ]
        findings = RESOLVER.validate_canary_campaign(
            self.registry, duplicated_class
        )
        self.assertIn("canary_campaign_classes_incomplete", findings)
        self.assertIn("canary_campaign_digests_not_unique", findings)

        # A result that itself would not independently validate (e.g. not
        # accepted) must not be laundered into campaign completion just
        # because a name for its class appears somewhere in the campaign.
        unaccepted = copy.deepcopy(campaign)
        unaccepted["canary_results"][2]["accepted"] = False
        findings = RESOLVER.validate_canary_campaign(self.registry, unaccepted)
        self.assertIn("canary_campaign_result_invalid:2", findings)

        # The declared digest list is evidence too: it must match what the
        # actual result content hashes to, not an independently asserted
        # value that could reference a result that was never submitted.
        tampered_digests = copy.deepcopy(campaign)
        tampered_digests["canary_result_digests"][0] = (
            "canres1_" + ("0" * 64)
        )
        findings = RESOLVER.validate_canary_campaign(
            self.registry, tampered_digests
        )
        self.assertIn("canary_campaign_declared_digests_mismatch", findings)

        # A structurally malformed campaign (not a mapping, or missing/
        # non-list canary_results) must fail closed without raising.
        try:
            findings = RESOLVER.validate_canary_campaign(self.registry, [])
        except TypeError:
            self.fail(
                "validate_canary_campaign raised on a non-mapping campaign"
            )
        self.assertIn("canary_campaign_root_invalid", findings)

        try:
            findings = RESOLVER.validate_canary_campaign(
                self.registry, {"canary_results": "not-a-list"}
            )
        except TypeError:
            self.fail(
                "validate_canary_campaign raised on malformed canary_results"
            )
        self.assertIn("canary_campaign_results_invalid", findings)

    def test_malformed_nested_discriminators_fail_closed_without_raising(
        self,
    ) -> None:
        # profile_id, logical_role_id, and canary_class are all untrusted
        # nested discriminators that used to be passed straight into a
        # dict.get() call. A malformed shape (e.g. a list where a string
        # is expected) must produce a structured BLOCKED/failed-closed
        # result, never an unhandled TypeError: unhashable type.
        requested = self.requested("DEEP", "high", "ARCHITECTURE")

        malformed_profile = copy.deepcopy(requested)
        malformed_profile["profile_id"] = ["DEEP"]
        try:
            result = self.resolve(
                "atlas.workflow-architect", malformed_profile
            )
        except TypeError:
            self.fail(
                "resolve_execution raised on a malformed nested profile_id"
            )
        self.assertEqual("BLOCKED", result["decision"]["state"])
        self.assertIn(
            "requested_profile_id_type_invalid", result["decision"]["findings"]
        )

        try:
            result = RESOLVER.resolve_execution(
                self.registry,
                packet_id="packet-001",
                logical_role_id=["atlas.workflow-architect"],
                admitted_execution_binding={
                    **copy.deepcopy(requested["execution_binding"]),
                    "turn_id": "turn-001",
                },
                requested=requested,
                effective=self.effective(
                    requested["model"],
                    requested["reasoning_effort"],
                    requested["execution_binding"],
                ),
                usage=self.usage(),
            )
        except TypeError:
            self.fail(
                "resolve_execution raised on a malformed nested "
                "logical_role_id"
            )
        self.assertEqual("BLOCKED", result["decision"]["state"])
        self.assertIn(
            "logical_role_id_type_invalid", result["decision"]["findings"]
        )

        definition = self.registry["canaries"]["classes"][0]
        malformed_canary = self.canary_result(definition)
        malformed_canary["canary_class"] = {"class": "STATUS_PROJECTION"}
        try:
            findings = RESOLVER.validate_canary_result(
                self.registry, malformed_canary
            )
        except TypeError:
            self.fail(
                "validate_canary_result raised on a malformed nested "
                "canary_class"
            )
        self.assertIn("canary_class_type_invalid", findings)
        self.assertIn("canary_class_unknown", findings)

    def test_explicit_empty_usage_is_rejected_not_defaulted(self) -> None:
        requested = self.requested("DEEP", "high", "ARCHITECTURE")
        result = self.resolve("atlas.workflow-architect", requested, usage={})
        self.assertEqual("BLOCKED", result["decision"]["state"])
        # An explicitly empty usage object must not be silently replaced by
        # _default_usage(): it must instead fail per-field validation as an
        # incomplete usage record, and the observation must keep recording
        # what was actually sent ({}), not a backfilled default.
        self.assertEqual({}, result["usage"])
        findings = set(result["decision"]["findings"])
        for field in RESOLVER.USAGE_PROXY_FIELDS:
            self.assertIn(f"usage_proxy_invalid:{field}", findings)
        self.assertIn("usage_escalation_checkpoint_invalid", findings)

        # Confirm omission (None) still defaults, as before -- only an
        # explicitly supplied usage object skips the default.
        omitted = self.resolve(
            "atlas.workflow-architect", requested, usage=None
        )
        self.assertNotEqual({}, omitted["usage"])

    def test_hard_limit_token_budget_requires_concrete_positive_ceilings(
        self,
    ) -> None:
        token_budget_schema = self.observation_schema["$defs"]["token_budget"]

        valid_hard_limit = {
            "enforcement": "HARD_LIMIT",
            "max_output_tokens": 100,
            "max_total_tokens": 300,
        }
        self.assertEqual(
            [],
            RESOLVER.schema_errors(
                valid_hard_limit, token_budget_schema, self.observation_schema
            ),
        )
        valid_observe_only = {
            "enforcement": "OBSERVE_ONLY",
            "max_output_tokens": None,
            "max_total_tokens": None,
        }
        self.assertEqual(
            [],
            RESOLVER.schema_errors(
                valid_observe_only,
                token_budget_schema,
                self.observation_schema,
            ),
        )

        # Schema-level: HARD_LIMIT with either ceiling null must not match
        # either anyOf branch (OBSERVE_ONLY requires the OBSERVE_ONLY
        # const; HARD_LIMIT's own branch requires concrete integers).
        for missing_field in ("max_output_tokens", "max_total_tokens"):
            with self.subTest(schema_missing=missing_field):
                invalid = copy.deepcopy(valid_hard_limit)
                invalid[missing_field] = None
                self.assertTrue(
                    RESOLVER.schema_errors(
                        invalid, token_budget_schema, self.observation_schema
                    )
                )

        # Code-level: the same fail-open shape must independently be
        # blocked by _validate_budget_fields inside resolve_execution, not
        # only by the schema check above.
        requested = self.requested("DEEP", "high", "ARCHITECTURE")
        for missing_field in ("max_output_tokens", "max_total_tokens"):
            with self.subTest(code_missing=missing_field):
                requested_case = copy.deepcopy(requested)
                requested_case["token_budget"] = copy.deepcopy(
                    valid_hard_limit
                )
                requested_case["token_budget"][missing_field] = None
                result = self.resolve(
                    "atlas.workflow-architect", requested_case
                )
                self.assertIn(
                    f"hard_limit_ceiling_missing:{missing_field}",
                    result["decision"]["findings"],
                )
                self.assertEqual("BLOCKED", result["decision"]["state"])

    def test_provider_neutral_boundary_is_non_dispatching(self) -> None:
        boundary = self.registry["worker_adapter_boundary"]
        self.assertEqual("ATLAS_MAIN_ONLY", boundary["canonical_scheduler"])
        self.assertEqual(
            "PURE_DETERMINISTIC_NO_DISPATCH", boundary["resolver_authority"]
        )
        self.assertEqual("codex", boundary["first_canary_adapter"])
        self.assertEqual({"claude", "litellm"}, set(boundary["held_adapters"]))
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "subprocess.",
            "requests.",
            "urllib.",
            "socket.",
            "send_message",
            "create_thread",
        ):
            self.assertNotIn(forbidden, source)

    def test_cli_validation_is_deterministic(self) -> None:
        command = [
            sys.executable,
            str(MODULE_PATH),
            "--registry",
            str(REGISTRY_PATH),
            "--json",
        ]
        first = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        second = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual("PASS", json.loads(first.stdout)["status"])

    def test_canonical_json_portable_paths_and_official_evidence(self) -> None:
        self.assertEqual(7, len(EXACT_PATHS))
        for relative in EXACT_PATHS:
            path = PurePosixPath(relative)
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)
            self.assertTrue((ROOT / Path(*path.parts)).is_file())

        self.assertEqual(
            REGISTRY_PATH.read_bytes(),
            FIXTURE_PATH.read_bytes(),
            "the valid fixture must be byte-identical to canonical registry",
        )
        for path in (REGISTRY_PATH, FIXTURE_PATH):
            data = path.read_bytes()
            self.assertTrue(data.endswith(b"\n"))
            self.assertFalse(data.endswith(b"\n\n"))
            self.assertNotIn(b"\r\n", data)

        docs = DOC_PATH.read_text(encoding="utf-8")
        for url in self.registry["source_evidence"].values():
            if isinstance(url, str) and url.startswith("https://"):
                self.assertIn(url, docs)
        for path in EXACT_PATHS:
            machine_prefix = "C:" + chr(92)
            self.assertNotIn(
                machine_prefix, (ROOT / path).read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
