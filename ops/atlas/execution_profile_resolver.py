#!/usr/bin/env python3
"""Pure deterministic ATLAS execution-profile resolver.

This module validates an explicitly selected logical profile against a standing
role floor and an effective runtime observation. It performs no dispatch,
network access, provider call, configuration mutation, or runtime activation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "docs/registry/ATLAS-EXECUTION-PROFILES.v1.json"
OBSERVATION_SCHEMA = ROOT / "schemas/atlas.execution-observation.v1.json"
REGISTRY_SCHEMA = ROOT / "schemas/atlas.execution-profile.registry.v1.json"
UNKNOWN = "UNKNOWN"
PROFILE_IDS = ("FAST", "STANDARD", "DEEP", "CRITICAL")
REASONING_EFFORTS = ("low", "medium", "high", "xhigh", "max")
EVIDENCE_TIERS = ("E1", "E2", "E3", "E4")
REQUIRED_REQUESTED_FIELDS = (
    "benchmark_exception_id",
    "execution_binding",
    "profile_id",
    "profile_version",
    "model",
    "reasoning_effort",
    "selection_reason",
    "workload_class",
    "context_budget",
    "token_budget",
    "turn_budget",
    "retry_budget",
    "evidence_tier",
    "fallback_policy",
    "escalation_policy",
)
REQUIRED_EFFECTIVE_FIELDS = (
    "model",
    "reasoning_effort",
    "provider",
    "execution_binding",
    "adapter_id",
    "adapter_version",
    "runtime_version",
    "readback_source",
    "fallback_reason",
)
USAGE_PROXY_FIELDS = (
    "input_bundle_bytes",
    "repeated_evidence_bytes",
    "unique_evidence_refs",
    "files_read",
    "turns",
    "tool_calls",
    "child_workers",
    "retry_attempts",
    "correction_loops",
    "elapsed_to_material_state_ms",
)
CANONICAL_PROFILE_MAPPING = {
    "FAST": {
        "model": "gpt-5.6-luna",
        "provider": "openai",
        "reasoning_allowed": ["low", "medium"],
        "reasoning_default": "low",
        "reasoning_elevation_rule": (
            "MEDIUM_ONLY_FOR_CLEAR_REPEATABLE_WORK_REQUIRING_MODEST_SYNTHESIS"
        ),
        "workload_classes": [
            "EXTRACTION",
            "CLASSIFICATION",
            "TRANSFORMATION",
            "STRUCTURED_SUMMARY",
            "STATUS_PROJECTION",
            "DEDUPE_RENDERING",
        ],
    },
    "STANDARD": {
        "model": "gpt-5.6-terra",
        "provider": "openai",
        "reasoning_allowed": ["medium", "high"],
        "reasoning_default": "medium",
        "reasoning_elevation_rule": (
            "HIGH_FOR_BOUNDED_IMPLEMENTATION_CI_CORRECTION_OR_ORDINARY_REVIEW_WITH_EDGE_CASES"
        ),
        "workload_classes": [
            "ROUTINE_BOUNDED_IMPLEMENTATION",
            "NONCRITICAL_REVIEW",
            "EVERYDAY_TOOL_WORK",
        ],
    },
    "DEEP": {
        "model": "gpt-5.6-sol",
        "provider": "openai",
        "reasoning_allowed": ["high", "xhigh"],
        "reasoning_default": "high",
        "reasoning_elevation_rule": (
            "XHIGH_FOR_MIGRATION_SECURITY_ARCHITECTURE_OR_FAILED_HIGH_CANARY"
        ),
        "workload_classes": [
            "COMPLEX_ANALYSIS",
            "SCHEDULER_RECOVERY",
            "MIGRATION_PLANNING",
            "SECURITY_REVIEW",
            "ARCHITECTURE",
        ],
    },
    "CRITICAL": {
        "model": "gpt-5.6-sol",
        "provider": "openai",
        "reasoning_allowed": ["xhigh", "max"],
        "reasoning_default": "xhigh",
        "reasoning_elevation_rule": (
            "MAX_REQUIRES_EXPLICIT_BENCHMARKED_EXCEPTION"
        ),
        "workload_classes": ["HIGHEST_RISK_QUALITY_FIRST_WORK"],
    },
}
CANONICAL_ROLE_POLICIES = {
    "atlas.main": {
        "default_profile": "DEEP",
        "floor_profile": "DEEP",
        "minimum_reasoning_effort": "high",
    },
    "atlas.release-control-plane": {
        "default_profile": "STANDARD",
        "floor_profile": "STANDARD",
        "minimum_reasoning_effort": "high",
    },
    "atlas.workflow-architect": {
        "default_profile": "DEEP",
        "floor_profile": "DEEP",
        "minimum_reasoning_effort": "high",
    },
    "owner.fitness": {
        "default_profile": "DEEP",
        "floor_profile": "STANDARD",
        "minimum_reasoning_effort": "high",
    },
    "owner.mazer": {
        "default_profile": "DEEP",
        "floor_profile": "STANDARD",
        "minimum_reasoning_effort": "high",
    },
}
CANONICAL_CANARY_CLASSES = [
    {
        "allowed_profiles": ["FAST"],
        "class": "STATUS_PROJECTION",
        "evidence_tier": "E1",
    },
    {
        "allowed_profiles": ["STANDARD"],
        "class": "ROUTINE_SOURCE_CORRECTION",
        "evidence_tier": "E2",
    },
    {
        "allowed_profiles": ["STANDARD", "DEEP"],
        "class": "INDEPENDENT_REVIEW",
        "evidence_tier": "E3",
    },
    {
        "allowed_profiles": ["DEEP"],
        "class": "SCHEDULER_RECOVERY",
        "evidence_tier": "E3",
    },
    {
        "allowed_profiles": ["DEEP"],
        "class": "MIGRATION_PLANNING",
        "evidence_tier": "E3",
    },
]
CANARY_COMPARE_DIMENSIONS = (
    "QUALITY",
    "COMPLETENESS",
    "TOOL_CORRECTNESS",
    "LATENCY",
    "TURNS",
    "TOKEN_PROXIES",
)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        .encode("utf-8")
    )


def load_registry(path: Path | str = DEFAULT_REGISTRY) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _append(findings: list[str], condition: bool, code: str) -> None:
    if condition:
        findings.append(code)


def _resolve_local_ref(
    root_schema: Mapping[str, Any], reference: str
) -> Mapping[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported non-local schema reference: {reference}")
    current: Any = root_schema
    for raw in reference[2:].split("/"):
        segment = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or segment not in current:
            raise ValueError(f"unresolvable schema reference: {reference}")
        current = current[segment]
    if not isinstance(current, Mapping):
        raise ValueError(f"schema reference is not an object: {reference}")
    return current


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return _is_finite_number(value)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected}")


def schema_errors(
    value: Any,
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any] | None = None,
    at: str = "$",
) -> list[str]:
    """Validate the closed dependency-free JSON-Schema subset used here."""

    root_schema = root_schema or schema
    if "$ref" in schema:
        return schema_errors(
            value,
            _resolve_local_ref(root_schema, str(schema["$ref"])),
            root_schema,
            at,
        )
    if "anyOf" in schema:
        branches = [
            schema_errors(value, item, root_schema, at)
            for item in schema["anyOf"]
        ]
        if any(not branch for branch in branches):
            return []
        return [f"{at}: value does not match anyOf"]

    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{at}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: value is not in enum")

    expected = schema.get("type")
    if expected is not None:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, item) for item in allowed):
            errors.append(f"{at}: expected type {' | '.join(allowed)}")
            return errors

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{at}: string shorter than minimum")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            errors.append(f"{at}: string does not match pattern")
        if schema.get("format") == "date" and re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", value
        ) is None:
            errors.append(f"{at}: invalid date format")
        if schema.get("format") == "uri" and re.match(
            r"^https?://[^\s]+$", value
        ) is None:
            errors.append(f"{at}: invalid URI format")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{at}: number below minimum")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{at}: fewer than minimum items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{at}: more than maximum items")
        if schema.get("uniqueItems") and len(
            {canonical_bytes(item) for item in value}
        ) != len(value):
            errors.append(f"{at}: array items are not unique")
        child = schema.get("items")
        if isinstance(child, Mapping):
            for index, item in enumerate(value):
                errors.extend(
                    schema_errors(item, child, root_schema, f"{at}[{index}]")
                )
        contains = schema.get("contains")
        if isinstance(contains, Mapping) and not any(
            not schema_errors(item, contains, root_schema, f"{at}[{index}]")
            for index, item in enumerate(value)
        ):
            errors.append(f"{at}: no array item satisfies contains")

    if isinstance(value, Mapping):
        if len(value) < schema.get("minProperties", 0):
            errors.append(f"{at}: fewer than minimum properties")
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{at}.{key}: required property missing")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key in value:
            if key not in properties:
                if additional is False:
                    errors.append(f"{at}.{key}: property is not allowed")
                elif isinstance(additional, Mapping):
                    errors.extend(
                        schema_errors(
                            value[key],
                            additional,
                            root_schema,
                            f"{at}.{key}",
                        )
                    )
        for key, child in properties.items():
            if key in value and isinstance(child, Mapping):
                errors.extend(
                    schema_errors(
                        value[key], child, root_schema, f"{at}.{key}"
                    )
                )
        property_names = schema.get("propertyNames")
        if isinstance(property_names, Mapping):
            for key in value:
                errors.extend(
                    schema_errors(
                        key,
                        property_names,
                        root_schema,
                        f"{at}.<property-name>",
                    )
                )
    return errors


def validate_schema_document(
    schema: Mapping[str, Any], *, expected_id: str
) -> list[str]:
    findings: list[str] = []
    _append(
        findings,
        schema.get("$schema")
        != "https://json-schema.org/draft/2020-12/schema",
        "schema_draft_mismatch",
    )
    _append(findings, schema.get("$id") != expected_id, "schema_id_mismatch")
    _append(findings, schema.get("type") != "object", "schema_root_type_invalid")
    _append(
        findings,
        schema.get("additionalProperties") is not False,
        "schema_root_not_closed",
    )
    _append(
        findings,
        not isinstance(schema.get("properties"), Mapping),
        "schema_properties_missing",
    )
    _append(
        findings,
        not isinstance(schema.get("required"), list),
        "schema_required_missing",
    )
    return findings


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    registry_schema = load_registry(REGISTRY_SCHEMA)
    findings = [
        f"registry_schema_invalid:{item}"
        for item in schema_errors(registry, registry_schema)
    ]
    if findings:
        return sorted(set(findings))
    _append(
        findings,
        registry.get("contract_version") != "atlas.execution-profile.registry.v1",
        "registry_contract_version_mismatch",
    )
    _append(
        findings,
        registry.get("profile_version") != "atlas.execution-profiles.v1",
        "profile_version_mismatch",
    )
    _append(
        findings,
        tuple(registry.get("profile_order", ())) != PROFILE_IDS,
        "profile_order_mismatch",
    )
    _append(
        findings,
        tuple(registry.get("reasoning_order", ())) != REASONING_EFFORTS,
        "reasoning_order_mismatch",
    )

    profiles = registry.get("profiles")
    if not isinstance(profiles, Mapping):
        findings.append("profiles_missing")
        profiles = {}
    _append(findings, set(profiles) != set(PROFILE_IDS), "profile_set_mismatch")

    workload_owners: dict[str, str] = {}
    for profile_id in PROFILE_IDS:
        profile = profiles.get(profile_id, {})
        if not isinstance(profile, Mapping):
            findings.append(f"profile_invalid:{profile_id}")
            profile = {}
        expected_profile = CANONICAL_PROFILE_MAPPING[profile_id]
        _append(
            findings,
            profile.get("model") != expected_profile["model"],
            f"profile_model_mismatch:{profile_id}",
        )
        _append(
            findings,
            profile.get("provider") != expected_profile["provider"],
            f"profile_provider_mismatch:{profile_id}",
        )
        _append(
            findings,
            profile.get("reasoning_allowed")
            != expected_profile["reasoning_allowed"],
            f"profile_reasoning_allowed_mismatch:{profile_id}",
        )
        _append(
            findings,
            profile.get("reasoning_default")
            != expected_profile["reasoning_default"],
            f"profile_reasoning_default_mismatch:{profile_id}",
        )
        _append(
            findings,
            profile.get("reasoning_elevation_rule")
            != expected_profile["reasoning_elevation_rule"],
            f"profile_reasoning_elevation_rule_mismatch:{profile_id}",
        )
        _append(
            findings,
            profile.get("workload_classes")
            != expected_profile["workload_classes"],
            f"profile_workload_classes_mismatch:{profile_id}",
        )
        workload_classes = profile.get("workload_classes")
        for workload in workload_classes if isinstance(workload_classes, list) else []:
            if workload in workload_owners:
                findings.append(f"workload_class_duplicate:{workload}")
            workload_owners[workload] = profile_id

    role_policies = registry.get("role_policies")
    if not isinstance(role_policies, Mapping) or not role_policies:
        findings.append("role_policies_missing")
        role_policies = {}
    _append(
        findings,
        set(role_policies) != set(CANONICAL_ROLE_POLICIES),
        "role_policy_set_mismatch",
    )
    for role_id, expected_policy in CANONICAL_ROLE_POLICIES.items():
        _append(
            findings,
            role_policies.get(role_id) != expected_policy,
            f"role_policy_mapping_mismatch:{role_id}",
        )
    for role_id, policy in role_policies.items():
        if not isinstance(policy, Mapping):
            findings.append(f"role_policy_invalid:{role_id}")
            continue
        _append(
            findings,
            not _is_nonempty_string(role_id),
            "role_policy_role_id_invalid",
        )
        default_profile = policy.get("default_profile")
        floor_profile = policy.get("floor_profile")
        minimum_effort = policy.get("minimum_reasoning_effort")
        _append(
            findings,
            default_profile not in PROFILE_IDS,
            f"role_default_profile_invalid:{role_id}",
        )
        _append(
            findings,
            floor_profile not in PROFILE_IDS,
            f"role_floor_profile_invalid:{role_id}",
        )
        if default_profile in PROFILE_IDS and floor_profile in PROFILE_IDS:
            _append(
                findings,
                PROFILE_IDS.index(default_profile) < PROFILE_IDS.index(floor_profile),
                f"role_default_below_floor:{role_id}",
            )
        _append(
            findings,
            minimum_effort not in REASONING_EFFORTS,
            f"role_reasoning_floor_invalid:{role_id}",
        )

    boundary = registry.get("worker_adapter_boundary")
    if not isinstance(boundary, Mapping):
        findings.append("worker_adapter_boundary_invalid")
        boundary = {}
    _append(
        findings,
        boundary.get("canonical_scheduler") != "ATLAS_MAIN_ONLY",
        "canonical_scheduler_boundary_invalid",
    )
    _append(
        findings,
        boundary.get("resolver_authority") != "PURE_DETERMINISTIC_NO_DISPATCH",
        "resolver_authority_invalid",
    )
    _append(
        findings,
        boundary.get("first_canary_adapter") != "codex",
        "first_canary_adapter_invalid",
    )
    held_adapters = boundary.get("held_adapters")
    held = set(held_adapters) if isinstance(held_adapters, list) else set()
    _append(
        findings,
        not {"claude", "litellm"}.issubset(held),
        "external_adapter_hold_missing",
    )

    canaries = registry.get("canaries")
    if not isinstance(canaries, Mapping):
        findings.append("canaries_invalid")
        canaries = {}
    classes = canaries.get("classes")
    _append(
        findings,
        classes != CANONICAL_CANARY_CLASSES,
        "five_canary_contract_mismatch",
    )
    _append(
        findings,
        canaries.get("compare") != list(CANARY_COMPARE_DIMENSIONS),
        "canary_compare_dimensions_mismatch",
    )
    _append(
        findings,
        canaries.get("baseline_event_id")
        != "onv1_f2c164eb892f46fa66ea834c6bba96206a3109a9e6817b765d1546690e900502",
        "canary_baseline_identity_mismatch",
    )
    _append(
        findings,
        canaries.get("baseline_repeated_evidence_bytes") != 3543,
        "canary_baseline_bytes_mismatch",
    )
    _append(
        findings,
        canaries.get("minimum_completed_canaries") != 5,
        "canary_minimum_completed_mismatch",
    )
    _append(
        findings,
        canaries.get("minimum_repeated_context_reduction_percent") != 30,
        "canary_reduction_target_mismatch",
    )
    _append(
        findings,
        canaries.get("maximum_repeated_evidence_bytes") != 2480,
        "canary_repeated_evidence_ceiling_mismatch",
    )
    _append(
        findings,
        canaries.get("dropped_acceptance_criteria") != 0,
        "canary_registry_dropped_acceptance_mismatch",
    )
    _append(
        findings,
        canaries.get("dropped_required_evidence_refs") != 0,
        "canary_registry_dropped_evidence_mismatch",
    )
    _append(
        findings,
        canaries.get("savings_success_rule")
        != "RESOURCE_REDUCTION_COUNTS_ONLY_WHEN_ACCEPTANCE_AND_REQUIRED_EVIDENCE_DO_NOT_REGRESS",
        "canary_savings_rule_mismatch",
    )
    return sorted(set(findings))


def _validate_budget_fields(requested: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    context = requested.get("context_budget")
    if not isinstance(context, Mapping):
        findings.append("context_budget_invalid")
    else:
        for field in (
            "max_bundle_bytes",
            "maximum_repeated_evidence_bytes",
            "immutable_ref_count",
        ):
            value = context.get(field)
            _append(
                findings,
                not isinstance(value, int) or value < 0,
                f"context_budget_field_invalid:{field}",
            )
        _append(
            findings,
            not _is_nonempty_string(context.get("freshness_rule")),
            "context_budget_freshness_rule_invalid",
        )
        _append(
            findings,
            not isinstance(context.get("compaction_checkpoint_required"), bool),
            "context_budget_compaction_rule_invalid",
        )

    token = requested.get("token_budget")
    if not isinstance(token, Mapping):
        findings.append("token_budget_invalid")
    else:
        for field in ("max_total_tokens", "max_output_tokens"):
            value = token.get(field)
            _append(
                findings,
                value is not None and (not isinstance(value, int) or value <= 0),
                f"token_budget_field_invalid:{field}",
            )
        _append(
            findings,
            token.get("enforcement") not in {"HARD_LIMIT", "OBSERVE_ONLY"},
            "token_budget_enforcement_invalid",
        )

    turn = requested.get("turn_budget")
    if not isinstance(turn, Mapping):
        findings.append("turn_budget_invalid")
    else:
        maximum = turn.get("max_turns")
        escalation = turn.get("escalation_at_turn")
        _append(
            findings,
            not isinstance(maximum, int) or maximum <= 0,
            "turn_budget_max_invalid",
        )
        _append(
            findings,
            not isinstance(escalation, int)
            or escalation <= 0
            or (isinstance(maximum, int) and escalation > maximum),
            "turn_budget_escalation_invalid",
        )

    retry = requested.get("retry_budget")
    if not isinstance(retry, Mapping):
        findings.append("retry_budget_invalid")
    else:
        _append(
            findings,
            not isinstance(retry.get("max_attempts"), int)
            or retry.get("max_attempts", -1) < 0,
            "retry_budget_max_attempts_invalid",
        )
        for field in ("retryable_classes", "terminal_classes"):
            value = retry.get(field)
            _append(
                findings,
                not isinstance(value, list)
                or any(not _is_nonempty_string(item) for item in value),
                f"retry_budget_field_invalid:{field}",
            )
    return findings


def _default_usage() -> dict[str, Any]:
    return {
        "cached_input_tokens": None,
        "child_workers": 0,
        "correction_loops": 0,
        "elapsed_to_material_state_ms": 0,
        "escalation_checkpoint_observed": False,
        "files_read": 0,
        "input_bundle_bytes": 0,
        "input_tokens": None,
        "output_tokens": None,
        "provider_cost": None,
        "reasoning_tokens": None,
        "repeated_evidence_bytes": 0,
        "retry_attempts": 0,
        "tool_calls": 0,
        "turns": 0,
        "unique_evidence_refs": 0,
    }


def validate_usage(usage: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    _append(
        findings,
        not isinstance(usage.get("escalation_checkpoint_observed"), bool),
        "usage_escalation_checkpoint_invalid",
    )
    for field in (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_tokens",
    ):
        value = usage.get(field)
        _append(
            findings,
            value is not None and (not isinstance(value, int) or value < 0),
            f"usage_exact_invalid:{field}",
        )
    provider_cost = usage.get("provider_cost")
    _append(
        findings,
        provider_cost is not None
        and (
            not _is_finite_number(provider_cost)
            or provider_cost < 0
        ),
        "usage_exact_invalid:provider_cost",
    )
    for field in USAGE_PROXY_FIELDS:
        value = usage.get(field)
        _append(
            findings,
            not isinstance(value, int) or value < 0,
            f"usage_proxy_invalid:{field}",
        )
    return findings


def _validate_execution_bindings(
    logical_role_id: str,
    requested: Mapping[str, Any],
    effective: Mapping[str, Any],
    admitted_execution_binding: Mapping[str, Any],
) -> list[str]:
    findings: list[str] = []
    requested_binding = requested.get("execution_binding")
    effective_binding = effective.get("execution_binding")
    admitted_binding: Mapping[str, Any] = admitted_execution_binding
    if not isinstance(requested_binding, Mapping):
        findings.append("requested_execution_binding_invalid")
        requested_binding = {}
    if not isinstance(effective_binding, Mapping):
        findings.append("effective_execution_binding_invalid")
        effective_binding = {}
    if not isinstance(admitted_binding, Mapping):
        findings.append("admitted_execution_binding_invalid")
        admitted_binding = {}

    requested_fields = (
        "logical_role_id",
        "host_id",
        "runtime_thread_id",
        "runtime_epoch_id",
    )
    admitted_fields = requested_fields + ("turn_id",)
    effective_fields = admitted_fields
    for field in admitted_fields:
        admitted_value = admitted_binding.get(field)
        _append(
            findings,
            not _is_nonempty_string(admitted_value)
            or str(admitted_value).strip().upper() == UNKNOWN,
            f"admitted_execution_binding_unproven:{field}",
        )
    for field in requested_fields:
        value = requested_binding.get(field)
        _append(
            findings,
            not _is_nonempty_string(value)
            or str(value).strip().upper() == UNKNOWN,
            f"requested_execution_binding_unproven:{field}",
        )
    for field in effective_fields:
        value = effective_binding.get(field)
        _append(
            findings,
            not _is_nonempty_string(value)
            or str(value).strip().upper() == UNKNOWN,
            f"effective_execution_binding_unproven:{field}",
        )

    _append(
        findings,
        requested_binding.get("logical_role_id") != logical_role_id,
        "requested_execution_role_mismatch",
    )
    for field in requested_fields:
        _append(
            findings,
            requested_binding.get(field) != admitted_binding.get(field),
            f"requested_execution_binding_not_admitted:{field}",
        )
        _append(
            findings,
            requested_binding.get(field) != effective_binding.get(field),
            f"effective_execution_binding_mismatch:{field}",
        )
    _append(
        findings,
        effective_binding.get("turn_id") != admitted_binding.get("turn_id"),
        "effective_execution_binding_mismatch:turn_id",
    )
    return findings


def _enforce_budget_limits(
    requested: Mapping[str, Any], usage: Mapping[str, Any]
) -> list[str]:
    findings: list[str] = []
    context = requested.get("context_budget")
    if isinstance(context, Mapping):
        context_limits = (
            ("input_bundle_bytes", "max_bundle_bytes"),
            (
                "repeated_evidence_bytes",
                "maximum_repeated_evidence_bytes",
            ),
        )
        for usage_field, budget_field in context_limits:
            actual = usage.get(usage_field)
            maximum = context.get(budget_field)
            if isinstance(actual, int) and isinstance(maximum, int):
                _append(
                    findings,
                    actual > maximum,
                    f"context_budget_exceeded:{usage_field}",
                )
        actual_refs = usage.get("unique_evidence_refs")
        minimum_refs = context.get("immutable_ref_count")
        if isinstance(actual_refs, int) and isinstance(minimum_refs, int):
            _append(
                findings,
                actual_refs < minimum_refs,
                "context_budget_immutable_refs_missing",
            )

    turn = requested.get("turn_budget")
    if isinstance(turn, Mapping):
        turns = usage.get("turns")
        maximum = turn.get("max_turns")
        escalation = turn.get("escalation_at_turn")
        if isinstance(turns, int) and isinstance(maximum, int):
            _append(
                findings,
                turns > maximum,
                "turn_budget_exceeded",
            )
        if isinstance(turns, int) and isinstance(escalation, int):
            _append(
                findings,
                turns >= escalation
                and usage.get("escalation_checkpoint_observed") is not True,
                "turn_budget_escalation_checkpoint_missing",
            )

    retry = requested.get("retry_budget")
    if isinstance(retry, Mapping):
        attempts = usage.get("retry_attempts")
        maximum_attempts = retry.get("max_attempts")
        if isinstance(attempts, int) and isinstance(maximum_attempts, int):
            _append(
                findings,
                attempts > maximum_attempts,
                "retry_budget_exceeded",
            )

    token = requested.get("token_budget")
    if isinstance(token, Mapping) and token.get("enforcement") == "HARD_LIMIT":
        output_tokens = usage.get("output_tokens")
        max_output = token.get("max_output_tokens")
        if isinstance(max_output, int):
            _append(
                findings,
                not isinstance(output_tokens, int),
                "hard_limit_output_tokens_unproven",
            )
            if isinstance(output_tokens, int):
                _append(
                    findings,
                    output_tokens > max_output,
                    "hard_limit_output_tokens_exceeded",
                )

        max_total = token.get("max_total_tokens")
        if isinstance(max_total, int):
            total_fields = (
                usage.get("input_tokens"),
                usage.get("output_tokens"),
                usage.get("reasoning_tokens"),
            )
            _append(
                findings,
                any(not isinstance(item, int) for item in total_fields),
                "hard_limit_total_tokens_unproven",
            )
            if all(isinstance(item, int) for item in total_fields):
                _append(
                    findings,
                    sum(total_fields) > max_total,
                    "hard_limit_total_tokens_exceeded",
                )
    return findings


def _build_observation(
    *,
    admitted_execution_binding: Mapping[str, Any],
    effective: Mapping[str, Any],
    findings: Sequence[str],
    logical_role_id: str,
    packet_id: str,
    requested: Mapping[str, Any],
    usage_value: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_findings = sorted(set(findings))
    admitted_binding_value = (
        copy.deepcopy(dict(admitted_execution_binding))
        if isinstance(admitted_execution_binding, Mapping)
        else {}
    )
    effective_value = (
        copy.deepcopy(dict(effective)) if isinstance(effective, Mapping) else {}
    )
    requested_value = (
        copy.deepcopy(dict(requested)) if isinstance(requested, Mapping) else {}
    )
    normalized_usage = copy.deepcopy(dict(usage_value))
    identity_payload = {
        "admitted_execution_binding": admitted_binding_value,
        "effective": effective_value,
        "logical_role_id": logical_role_id,
        "packet_id": packet_id,
        "requested": requested_value,
        "usage": normalized_usage,
    }
    observation_id = "onv1_" + hashlib.sha256(
        canonical_bytes(identity_payload)
    ).hexdigest()
    observation = {
        "admitted_execution_binding": admitted_binding_value,
        "contract_version": "atlas.execution-observation.v1",
        "decision": {
            "canary_eligible": not normalized_findings,
            "findings": normalized_findings,
            "state": "ADMITTED" if not normalized_findings else "BLOCKED",
        },
        "effective": effective_value,
        "logical_role_id": logical_role_id,
        "observation_id": observation_id,
        "packet_id": packet_id,
        "requested": requested_value,
        "usage": normalized_usage,
    }
    observation_schema = load_registry(OBSERVATION_SCHEMA)
    schema_findings = [
        f"observation_schema_invalid:{item}"
        for item in schema_errors(observation, observation_schema)
    ]
    if schema_findings:
        normalized_findings = sorted(
            set(normalized_findings + schema_findings)
        )
        observation["decision"] = {
            "canary_eligible": False,
            "findings": normalized_findings,
            "state": "BLOCKED",
        }
    return observation


def resolve_execution(
    registry: Mapping[str, Any],
    *,
    packet_id: str,
    logical_role_id: str,
    admitted_execution_binding: Mapping[str, Any],
    requested: Mapping[str, Any],
    effective: Mapping[str, Any],
    usage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a closed deterministic observation without dispatching work."""

    findings = validate_registry(registry)
    if findings and all(
        finding.startswith("registry_schema_invalid:") for finding in findings
    ):
        usage_value = copy.deepcopy(
            dict(usage) if isinstance(usage, Mapping) else _default_usage()
        )
        provider_cost = usage_value.get("provider_cost")
        if provider_cost is not None and (
            not _is_finite_number(provider_cost) or provider_cost < 0
        ):
            usage_value["provider_cost"] = None
        return _build_observation(
            admitted_execution_binding=admitted_execution_binding,
            effective=effective,
            findings=findings,
            logical_role_id=logical_role_id,
            packet_id=packet_id,
            requested=requested,
            usage_value=usage_value,
        )
    registry_view: Mapping[str, Any] = (
        registry if isinstance(registry, Mapping) else {}
    )
    for field in REQUIRED_REQUESTED_FIELDS:
        _append(
            findings,
            field not in requested,
            f"requested_field_missing:{field}",
        )
    for field in REQUIRED_EFFECTIVE_FIELDS:
        _append(
            findings,
            field not in effective,
            f"effective_field_missing:{field}",
        )
    _append(findings, not _is_nonempty_string(packet_id), "packet_id_invalid")
    _append(
        findings,
        not _is_nonempty_string(logical_role_id),
        "logical_role_id_invalid",
    )
    findings.extend(
        _validate_execution_bindings(
            logical_role_id,
            requested,
            effective,
            admitted_execution_binding,
        )
    )

    profile_id = requested.get("profile_id")
    profiles = registry_view.get("profiles")
    profile = profiles.get(profile_id) if isinstance(profiles, Mapping) else None
    if not isinstance(profile, Mapping):
        profile = None
    _append(findings, profile is None, "requested_profile_unknown")
    _append(
        findings,
        requested.get("profile_version") != registry_view.get("profile_version"),
        "requested_profile_version_mismatch",
    )
    if profile is not None:
        _append(
            findings,
            requested.get("model") != profile.get("model"),
            "requested_model_profile_mismatch",
        )
        _append(
            findings,
            requested.get("reasoning_effort")
            not in profile.get("reasoning_allowed", []),
            "requested_reasoning_not_allowed",
        )
        _append(
            findings,
            requested.get("workload_class")
            not in profile.get("workload_classes", []),
            "requested_workload_profile_mismatch",
        )

    role_policies = registry_view.get("role_policies")
    role_policy = (
        role_policies.get(logical_role_id)
        if isinstance(role_policies, Mapping)
        else None
    )
    if not isinstance(role_policy, Mapping):
        role_policy = None
    _append(findings, role_policy is None, "role_policy_missing")
    if role_policy is not None and profile_id in PROFILE_IDS:
        floor_profile = role_policy.get("floor_profile")
        if floor_profile in PROFILE_IDS:
            _append(
                findings,
                PROFILE_IDS.index(profile_id) < PROFILE_IDS.index(floor_profile),
                "requested_profile_below_role_floor",
            )
        minimum_effort = role_policy.get("minimum_reasoning_effort")
        effort = requested.get("reasoning_effort")
        if minimum_effort in REASONING_EFFORTS and effort in REASONING_EFFORTS:
            _append(
                findings,
                REASONING_EFFORTS.index(effort)
                < REASONING_EFFORTS.index(minimum_effort),
                "requested_reasoning_below_role_floor",
            )

    _append(
        findings,
        not _is_nonempty_string(requested.get("selection_reason")),
        "selection_reason_invalid",
    )
    _append(
        findings,
        requested.get("evidence_tier") not in EVIDENCE_TIERS,
        "evidence_tier_invalid",
    )
    _append(
        findings,
        requested.get("fallback_policy") != "NO_SILENT_FALLBACK",
        "fallback_policy_invalid",
    )
    _append(
        findings,
        requested.get("escalation_policy")
        != "FAIL_CLOSED_AND_RETURN_CONTENT_ADDRESSED_HOLD",
        "escalation_policy_invalid",
    )
    findings.extend(_validate_budget_fields(requested))

    if requested.get("reasoning_effort") == "max":
        _append(
            findings,
            profile_id != "CRITICAL",
            "max_reasoning_requires_critical_profile",
        )
        _append(
            findings,
            not _is_nonempty_string(requested.get("benchmark_exception_id")),
            "max_reasoning_benchmark_exception_missing",
        )

    for field in (
        "model",
        "reasoning_effort",
        "provider",
        "adapter_id",
        "adapter_version",
        "runtime_version",
        "readback_source",
    ):
        value = effective.get(field)
        _append(
            findings,
            not _is_nonempty_string(value) or str(value).strip().upper() == UNKNOWN,
            f"effective_identity_unproven:{field}",
        )
    if profile is not None:
        _append(
            findings,
            effective.get("model") != requested.get("model"),
            "effective_model_mismatch",
        )
        _append(
            findings,
            effective.get("reasoning_effort") != requested.get("reasoning_effort"),
            "effective_reasoning_mismatch",
        )
        _append(
            findings,
            effective.get("provider") != profile.get("provider"),
            "effective_provider_mismatch",
        )
    boundary = registry_view.get("worker_adapter_boundary")
    if not isinstance(boundary, Mapping):
        boundary = {}
    _append(
        findings,
        effective.get("adapter_id") != boundary.get("first_canary_adapter"),
        "effective_adapter_not_admitted",
    )
    _append(
        findings,
        effective.get("fallback_reason") not in (None, ""),
        "silent_or_unapproved_fallback_detected",
    )

    raw_usage = copy.deepcopy(dict(usage or _default_usage()))
    findings.extend(validate_usage(raw_usage))
    findings.extend(_enforce_budget_limits(requested, raw_usage))
    usage_value = raw_usage
    if (
        usage_value.get("provider_cost") is not None
        and (
            not _is_finite_number(usage_value.get("provider_cost"))
            or usage_value.get("provider_cost") < 0
        )
    ):
        usage_value["provider_cost"] = None
    return _build_observation(
        admitted_execution_binding=admitted_execution_binding,
        effective=effective,
        findings=findings,
        logical_role_id=logical_role_id,
        packet_id=packet_id,
        requested=requested,
        usage_value=usage_value,
    )


def validate_canary_result(
    registry: Mapping[str, Any], result: Mapping[str, Any]
) -> list[str]:
    findings = validate_registry(registry)
    if findings and all(
        finding.startswith("registry_schema_invalid:") for finding in findings
    ):
        return findings
    registry_view: Mapping[str, Any] = (
        registry if isinstance(registry, Mapping) else {}
    )
    canaries = registry_view.get("canaries")
    if not isinstance(canaries, Mapping):
        canaries = {}
    classes = canaries.get("classes")
    if not isinstance(classes, list):
        classes = []
    definitions = {
        item.get("class"): item for item in classes if isinstance(item, Mapping)
    }
    canary_class = result.get("canary_class")
    definition = definitions.get(canary_class)
    _append(findings, definition is None, "canary_class_unknown")
    if definition is not None:
        _append(
            findings,
            result.get("profile_id") not in definition.get("allowed_profiles", []),
            "canary_profile_not_allowed",
        )
        _append(
            findings,
            result.get("evidence_tier") != definition.get("evidence_tier"),
            "canary_evidence_tier_mismatch",
        )
    required_fields = {
        "accepted",
        "baseline_event_id",
        "baseline_repeated_evidence_bytes",
        "canary_class",
        "completed_canary_classes",
        "comparison",
        "dropped_acceptance_criteria",
        "dropped_required_evidence_refs",
        "evidence_tier",
        "profile_id",
        "repeated_context_reduction_percent",
        "repeated_evidence_bytes",
    }
    _append(
        findings,
        set(result) != required_fields,
        "canary_result_fields_mismatch",
    )
    _append(findings, result.get("accepted") is not True, "canary_not_accepted")
    _append(
        findings,
        result.get("dropped_acceptance_criteria") != 0,
        "canary_dropped_acceptance_criteria",
    )
    _append(
        findings,
        result.get("dropped_required_evidence_refs") != 0,
        "canary_dropped_required_evidence_refs",
    )

    _append(
        findings,
        result.get("baseline_event_id") != canaries.get("baseline_event_id"),
        "canary_result_baseline_identity_mismatch",
    )
    baseline = result.get("baseline_repeated_evidence_bytes")
    _append(
        findings,
        baseline != canaries.get("baseline_repeated_evidence_bytes"),
        "canary_result_baseline_bytes_mismatch",
    )

    completed = result.get("completed_canary_classes")
    exact_classes = {item["class"] for item in CANONICAL_CANARY_CLASSES}
    completed_valid = isinstance(completed, list) and all(
        isinstance(item, str) for item in completed
    )
    _append(
        findings,
        not completed_valid
        or len(completed) != canaries.get("minimum_completed_canaries")
        or len(set(completed)) != len(completed)
        or set(completed) != exact_classes,
        "canary_completed_set_mismatch",
    )

    comparison = result.get("comparison")
    _append(
        findings,
        not isinstance(comparison, Mapping)
        or set(comparison) != set(CANARY_COMPARE_DIMENSIONS),
        "canary_comparison_dimensions_mismatch",
    )
    if isinstance(comparison, Mapping):
        quality_dimensions = {
            "QUALITY",
            "COMPLETENESS",
            "TOOL_CORRECTNESS",
        }
        for dimension in CANARY_COMPARE_DIMENSIONS:
            record = comparison.get(dimension)
            if not isinstance(record, Mapping):
                findings.append(f"canary_comparison_invalid:{dimension}")
                continue
            _append(
                findings,
                set(record) != {"baseline", "candidate", "passed"},
                f"canary_comparison_fields_mismatch:{dimension}",
            )
            baseline_value = record.get("baseline")
            candidate_value = record.get("candidate")
            numeric = (
                isinstance(baseline_value, (int, float))
                and not isinstance(baseline_value, bool)
                and baseline_value >= 0
                and isinstance(candidate_value, (int, float))
                and not isinstance(candidate_value, bool)
                and candidate_value >= 0
            )
            _append(
                findings,
                not numeric,
                f"canary_comparison_values_invalid:{dimension}",
            )
            _append(
                findings,
                record.get("passed") is not True,
                f"canary_comparison_not_passed:{dimension}",
            )
            if numeric:
                regressed = (
                    candidate_value < baseline_value
                    if dimension in quality_dimensions
                    else candidate_value > baseline_value
                )
                _append(
                    findings,
                    regressed,
                    f"canary_comparison_regressed:{dimension}",
                )

    repeated = result.get("repeated_evidence_bytes")
    _append(
        findings,
        not isinstance(repeated, int)
        or repeated < 0
        or repeated > canaries.get("maximum_repeated_evidence_bytes", -1),
        "canary_repeated_evidence_ceiling_exceeded",
    )
    reported_reduction = result.get("repeated_context_reduction_percent")
    if (
        isinstance(baseline, int)
        and baseline > 0
        and isinstance(repeated, int)
        and repeated >= 0
    ):
        computed_reduction = (baseline - repeated) * 100 / baseline
        _append(
            findings,
            not isinstance(reported_reduction, (int, float))
            or isinstance(reported_reduction, bool)
            or not math.isclose(
                reported_reduction,
                computed_reduction,
                abs_tol=0.01,
            ),
            "canary_reduction_calculation_mismatch",
        )
        _append(
            findings,
            computed_reduction
            < canaries.get("minimum_repeated_context_reduction_percent", 101),
            "canary_reduction_target_not_met",
        )
    else:
        findings.append("canary_reduction_evidence_invalid")
    return sorted(set(findings))


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the non-dispatching ATLAS execution profile registry."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to atlas.execution-profile.registry.v1 JSON.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)
    registry = load_registry(args.registry)
    findings = validate_registry(registry)
    result = {
        "findings": findings,
        "registry": args.registry.as_posix(),
        "status": "PASS" if not findings else "BLOCKED",
    }
    if args.json:
        print(
            json.dumps(
                result,
                allow_nan=False,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        print(result["status"])
        for finding in findings:
            print(f"- {finding}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(_main())
