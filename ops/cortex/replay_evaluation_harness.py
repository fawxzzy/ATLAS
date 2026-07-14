from __future__ import annotations

"""Deterministic, offline, advisory comparison of explicit Cortex artifacts.

This module intentionally has no execution, network, model, queue, Git, or
platform client.  It only reads named local JSON and writes an explicitly
requested temporary JSON report.
"""

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

REPORT_SCHEMA = "atlas.cortex.replay_evaluation_report.v1"
CASE_SCHEMA = "atlas.cortex.replay_case.v1"
ADAPTER_SCHEMA = "atlas.cortex.external_adapter_candidate.v1"
SYNTHESIS_SCHEMA = "atlas.cortex.chat_style_synthesis_packet.v1"
PLAN_SCHEMA = "atlas.cortex.execution_plan.v1"
RUBRIC_SCHEMA = "atlas.cortex.replay_evaluation_rubric.v1"
CONTRACT_VERSION = "atlas.cortex.replay_evaluation_harness_contract.v1"
COMPARATOR_VERSION = "atlas.cortex.replay_evaluation_harness.v1"
NO_EXECUTION_AUTHORITY = "no_execution_authority"

RESULT_CLASSES = (
    "equivalent", "cortex_stricter", "adapter_stricter", "complementary",
    "regression", "incomparable", "blocked",
)
DIMENSIONS = (
    "schema_compatibility", "source_digest_parity", "objective_and_selected_scope",
    "project_component_repository_owner", "execution_class", "scope_lock",
    "dependency_graph", "resource_claims", "runtime_recommendation",
    "permission_capability_separation", "external_action_authority_and_approvals",
    "verification_proof_commit_and_receipt_requirements", "rollback_and_recovery_requirements",
    "blocker_conflict_warning_and_admission_posture", "repeated_output_stability",
)
REPORT_FIELDS = (
    "schema_version", "report_id", "case_id", "source_digests", "source_trust_classes",
    "comparator_version", "rubric_version", "adapter_projection", "cortex_projection",
    "field_comparisons", "matched_constraints", "adapter_only_constraints",
    "cortex_only_constraints", "omissions", "contradictions", "authority_regressions",
    "dependency_and_collision_differences", "verification_and_receipt_differences", "metrics",
    "prior_report_comparison", "result_class", "explanation_codes", "blocked_reasons",
    "warnings", "skipped_reasons", "safe_to_use", "next_recommended_packet",
    "authority_denials",
)
AUTHORITY_DENIALS = (
    NO_EXECUTION_AUTHORITY, "no_model_call_authority", "no_final_receipt_authority",
    "no_marker_authority", "no_routing_authority", "no_codex_launch", "no_stack_invocation",
    "no_git_authority", "no_deploy_authority", "no_discord_or_card_authority",
    "no_database_authority", "no_external_mutation_authority", "no_queue_or_scheduler_creation",
    "no_owner_repository_mutation", "no_live_platform_query",
    "no_hidden_transcript_or_private_reasoning_access",
)
NEXT_PACKET = "Cortex Dual-Mode Replacement Readiness replay/evaluation harness first-implementation worker-cluster reconciliation"
PROTECTED_PARTS = {"repos", "runtime", "secrets", ".codex", ".vercel", "archive", "archives"}
FORBIDDEN_TERMS = (
    "transcript", "conversation", "private-reasoning", "chain-of-thought", "browser-profile",
    "account", "health", "payment", "personal-data", "customer", "live-platform", "github",
    "vercel", "supabase", "discord", "network", "api", "cookie", "credential", "token",
)


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return OrderedDict((str(key), _canonical(value[key])) for key in sorted(value, key=str))
    if isinstance(value, list):
        values = [_canonical(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, ensure_ascii=False, separators=(",", ":")))
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _finding(code: str, detail: str, **extra: Any) -> OrderedDict[str, Any]:
    return OrderedDict((("code", code), ("detail", detail), *sorted(extra.items())))


def _path_error(argument: str, *, output: bool = False) -> str | None:
    normalized = argument.replace("\\", "/")
    candidate = Path(argument)
    parts = [part.lower() for part in normalized.split("/") if part not in ("", ".")]
    if candidate.is_absolute() or (len(argument) > 1 and argument[1] == ":"):
        return "absolute_output_path" if output else "absolute_input_path"
    if ".." in parts:
        return "parent_traversal"
    if any(part in PROTECTED_PARTS or part.startswith(".") or part.startswith(".env") for part in parts):
        return "protected_path"
    if any(term in normalized.lower() for term in FORBIDDEN_TERMS):
        return "forbidden_source_class"
    return None


def validate_input_path(root: Path, argument: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    error = _path_error(argument)
    normalized = argument.replace("\\", "/")
    if error:
        return None, _finding(error, "Input path is not admitted.", path=argument)
    if not normalized.endswith(".json") or not (normalized.startswith("docs/") or normalized.startswith("tmp/atlas/")):
        return None, _finding("unadmitted_input_path", "Inputs must be explicit docs or tmp/atlas JSON files.", path=argument)
    candidate = root / Path(argument)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None, _finding("parent_traversal", "Input escapes the Atlas root.", path=argument)
    if not candidate.is_file():
        return None, _finding("missing_input", "Explicit input does not exist.", path=argument)
    return candidate, None


def validate_output_path(root: Path, argument: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    error = _path_error(argument, output=True)
    normalized = argument.replace("\\", "/")
    if error:
        return None, _finding(error, "Output path is not admitted.", path=argument)
    if not normalized.startswith("tmp/atlas/") or not normalized.endswith(".json"):
        return None, _finding("unadmitted_output_path", "Output must be an explicit tmp/atlas JSON file.", path=argument)
    candidate = root / Path(argument)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None, _finding("parent_traversal", "Output escapes the Atlas root.", path=argument)
    return candidate, None


def _read_json(root: Path, argument: str) -> tuple[dict[str, Any] | None, OrderedDict[str, Any] | None, str | None]:
    path, error = validate_input_path(root, argument)
    if error:
        return None, error, None
    assert path is not None
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _finding("invalid_json", "Input must be valid UTF-8 JSON.", path=argument, exception=str(exc)), None
    if not isinstance(value, dict):
        return None, _finding("invalid_json_shape", "Input JSON must be an object.", path=argument), None
    return value, None, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _get(packet: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in packet:
            return packet[name]
    nested = packet.get("synthesis_packet")
    if isinstance(nested, dict):
        for name in names:
            if name in nested:
                return nested[name]
    return None


def _constraint_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_constraint_set(item))
        return result
    if isinstance(value, dict):
        return {json.dumps(_canonical(value), ensure_ascii=False, separators=(",", ":"))}
    return {json.dumps(value, ensure_ascii=False, separators=(",", ":"))}


def _dimension_value(packet: dict[str, Any], dimension: str) -> set[str]:
    # Schema compatibility is established by the admitted-schema gate rather
    # than by requiring distinct artifact schema identifiers to be equal.
    if dimension == "schema_compatibility":
        return {"admitted_schema"} if isinstance(packet.get("schema_version"), str) else set()
    explicit = packet.get("constraints")
    if isinstance(explicit, dict) and dimension in explicit:
        return _constraint_set(explicit[dimension])
    aliases = {
        "schema_compatibility": ("schema_version",),
        "source_digest_parity": ("source_digests",),
        "objective_and_selected_scope": ("objective", "selected_lane", "selected_marker", "selected_packet"),
        "project_component_repository_owner": ("project", "component", "repository", "owner", "project_component_ownership"),
        "execution_class": ("execution_class",), "scope_lock": ("scope_lock", "allowed_files", "forbidden_files"),
        "dependency_graph": ("dependency_graph", "dependencies"), "resource_claims": ("resource_claims", "resource_leases"),
        "runtime_recommendation": ("runtime_recommendation",), "permission_capability_separation": ("permission_posture", "local_capability"),
        "external_action_authority_and_approvals": ("external_action_authority", "authority_denials", "required_approvals"),
        "verification_proof_commit_and_receipt_requirements": ("verification_requirements", "proof_requirements", "commit_requirements", "receipt_requirements"),
        "rollback_and_recovery_requirements": ("rollback_requirements", "recovery_requirements"),
        "blocker_conflict_warning_and_admission_posture": ("blocked_reasons", "conflicts", "warnings", "admission_posture", "safe_to_admit", "safe_to_use"),
        "repeated_output_stability": ("deterministic", "stable_for_identical_admitted_inputs"),
    }
    values: set[str] = set()
    for alias in aliases[dimension]:
        value = _get(packet, alias)
        if value is not None:
            values.add(alias + "=" + json.dumps(_canonical(value), ensure_ascii=False, separators=(",", ":")))
    return values


def _projection(packet: dict[str, Any], dimensions: tuple[str, ...]) -> OrderedDict[str, list[str]]:
    return OrderedDict((dimension, sorted(_dimension_value(packet, dimension))) for dimension in dimensions)


def _declared_digests(packet: dict[str, Any]) -> list[tuple[str, str]]:
    raw = _get(packet, "source_digests")
    if not isinstance(raw, list):
        return []
    pairs: list[tuple[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            path, digest = item.get("path") or item.get("source"), item.get("sha256") or item.get("digest")
            if isinstance(path, str) and isinstance(digest, str):
                pairs.append((path.replace("\\", "/"), digest))
    return sorted(pairs)


def _authority_widening(packet: dict[str, Any]) -> bool:
    value = _get(packet, "external_action_authority", "execution_authority")
    if value is None:
        return False
    encoded = json.dumps(_canonical(value), ensure_ascii=False).lower()
    safe = ("no_execution_authority", "no_external_mutation_authority", "denied", "false", "advisory_only")
    return not any(token in encoded for token in safe)


def _rubric_dimensions(rubric: dict[str, Any]) -> tuple[tuple[str, ...] | None, bool]:
    raw = rubric.get("comparison_dimensions", rubric.get("dimensions"))
    if not isinstance(raw, list):
        return None, False
    values = tuple(str(item) for item in raw)
    if not values or any(value not in DIMENSIONS for value in values):
        return None, False
    return tuple(sorted(set(values), key=DIMENSIONS.index)), bool(rubric.get("allow_complementary") or rubric.get("admit_complementary"))


def _report_template() -> OrderedDict[str, Any]:
    return OrderedDict((field, [] if field in {"source_digests", "source_trust_classes", "field_comparisons", "matched_constraints", "adapter_only_constraints", "cortex_only_constraints", "omissions", "contradictions", "authority_regressions", "dependency_and_collision_differences", "verification_and_receipt_differences", "explanation_codes", "blocked_reasons", "warnings", "skipped_reasons", "authority_denials"} else OrderedDict() if field in {"adapter_projection", "cortex_projection", "metrics", "prior_report_comparison"} else None) for field in REPORT_FIELDS)


def build_schema_only_payload() -> OrderedDict[str, Any]:
    report = _report_template()
    report.update(OrderedDict((("schema_version", REPORT_SCHEMA), ("report_id", "replay-evaluation-schema-only"), ("case_id", "schema_only"),
        ("source_trust_classes", ["schema_only", "non_authoritative"]), ("comparator_version", COMPARATOR_VERSION), ("rubric_version", "schema_only"),
        ("metrics", OrderedDict((("compared_dimensions", 0), ("deterministic", True)))), ("result_class", "blocked"),
        ("explanation_codes", ["schema_only"]), ("blocked_reasons", [_finding("schema_only", "Schema-only mode makes no comparison recommendation.")]),
        ("safe_to_use", False), ("next_recommended_packet", NEXT_PACKET), ("authority_denials", list(AUTHORITY_DENIALS)))))
    return report


def build_report(*, root: Path, case_path: str | None, adapter_path: str | None, synthesis_path: str | None, plan_path: str | None, rubric_path: str | None, prior_report_path: str | None = None) -> tuple[OrderedDict[str, Any], str]:
    report = _report_template()
    blockers: list[OrderedDict[str, Any]] = []
    inputs: dict[str, dict[str, Any]] = {}
    source_digests: list[OrderedDict[str, str]] = []
    expected = {"case": CASE_SCHEMA, "adapter": ADAPTER_SCHEMA, "synthesis": SYNTHESIS_SCHEMA, "plan": PLAN_SCHEMA, "rubric": RUBRIC_SCHEMA}
    arguments = {"case": case_path, "adapter": adapter_path, "synthesis": synthesis_path, "plan": plan_path, "rubric": rubric_path}
    for name, argument in arguments.items():
        if not argument:
            blockers.append(_finding("missing_required_input", "Required input is missing.", input=name))
            continue
        packet, error, digest = _read_json(root, argument)
        if error:
            blockers.append(error); continue
        assert packet is not None and digest is not None
        inputs[name] = packet
        source_digests.append(OrderedDict((("path", argument.replace("\\", "/")), ("sha256", digest))))
        if packet.get("schema_version") != expected[name]:
            blockers.append(_finding("invalid_schema", "Input schema is not admitted.", input=name, expected=expected[name], actual=packet.get("schema_version")))
    prior: dict[str, Any] | None = None
    if prior_report_path:
        prior, error, digest = _read_json(root, prior_report_path)
        if error:
            blockers.append(error)
        elif prior is not None:
            source_digests.append(OrderedDict((("path", prior_report_path.replace("\\", "/")), ("sha256", digest or ""))))
            if prior.get("schema_version") != REPORT_SCHEMA:
                blockers.append(_finding("invalid_prior_report_schema", "Prior report schema is not admitted."))
    if len(inputs) == len(expected):
        case = inputs["case"]
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            blockers.append(_finding("missing_case_identity", "Case needs a non-empty case_id."))
        for name in ("adapter", "synthesis", "plan"):
            found = _get(inputs[name], "case_id")
            if found is not None and found != case_id:
                blockers.append(_finding("source_identity_mismatch", "Artifact case identity differs from replay case.", input=name))
        claims: dict[str, str] = {}
        for packet in inputs.values():
            for path, digest in _declared_digests(packet):
                if path in claims and claims[path] != digest:
                    blockers.append(_finding("digest_conflict", "A source path has conflicting digests.", path=path))
                claims[path] = digest
        dimensions, allows_complementary = _rubric_dimensions(inputs["rubric"])
        version = inputs["rubric"].get("rubric_version", inputs["rubric"].get("version"))
        if not isinstance(version, str) or not version or dimensions is None:
            blockers.append(_finding("unknown_rubric_version", "Rubric version or comparison dimensions are not admitted."))
        for name in ("adapter", "synthesis", "plan"):
            if _authority_widening(inputs[name]):
                blockers.append(_finding("self_granted_authority", "Candidate artifact claims execution or external authority.", input=name))
        if blockers:
            dimensions = dimensions or DIMENSIONS
            adapter_projection = _projection(inputs["adapter"], dimensions)
            cortex_packet = dict(inputs["synthesis"]); cortex_packet.update(inputs["plan"])
            cortex_projection = _projection(cortex_packet, dimensions)
            result = "blocked"
        else:
            assert dimensions is not None
            adapter_projection = _projection(inputs["adapter"], dimensions)
            cortex_packet = dict(inputs["synthesis"]); cortex_packet.update(inputs["plan"])
            cortex_projection = _projection(cortex_packet, dimensions)
            comparisons: list[OrderedDict[str, Any]] = []
            matched: list[OrderedDict[str, Any]] = []; adapter_only: list[OrderedDict[str, Any]] = []; cortex_only: list[OrderedDict[str, Any]] = []
            omissions: list[OrderedDict[str, Any]] = []; contradictions: list[OrderedDict[str, Any]] = []
            for dimension in dimensions:
                adapter_values, cortex_values = set(adapter_projection[dimension]), set(cortex_projection[dimension])
                common = sorted(adapter_values & cortex_values); left = sorted(adapter_values - cortex_values); right = sorted(cortex_values - adapter_values)
                relation = "equivalent" if not left and not right else "cortex_stricter" if not left else "adapter_stricter" if not right else "complementary" if allows_complementary else "incomparable"
                comparisons.append(OrderedDict((("dimension", dimension), ("relation", relation), ("matched", common), ("adapter_only", left), ("cortex_only", right))))
                matched.extend(OrderedDict((("dimension", dimension), ("constraint", item))) for item in common)
                adapter_only.extend(OrderedDict((("dimension", dimension), ("constraint", item))) for item in left)
                cortex_only.extend(OrderedDict((("dimension", dimension), ("constraint", item))) for item in right)
                required = _dimension_value(case, dimension)
                for candidate, values in (("adapter", adapter_values), ("cortex", cortex_values)):
                    for missing in sorted(required - values):
                        omissions.append(OrderedDict((("dimension", dimension), ("candidate", candidate), ("constraint", missing))))
            result = "equivalent"
            relations = {item["relation"] for item in comparisons}
            if omissions:
                result = "regression"
            elif "incomparable" in relations:
                result = "incomparable"
            elif "complementary" in relations:
                result = "complementary"
            elif "cortex_stricter" in relations and "adapter_stricter" not in relations:
                result = "cortex_stricter"
            elif "adapter_stricter" in relations and "cortex_stricter" not in relations:
                result = "adapter_stricter"
            elif "cortex_stricter" in relations and "adapter_stricter" in relations:
                result = "complementary" if allows_complementary else "incomparable"
            if prior and prior.get("result_class") in {"equivalent", "cortex_stricter", "adapter_stricter", "complementary"} and result in {"regression", "incomparable"}:
                result = "regression"; contradictions.append(_finding("prior_report_regression", "Current report regressed from an admitted prior report."))
            report["field_comparisons"] = comparisons; report["matched_constraints"] = matched
            report["adapter_only_constraints"] = adapter_only; report["cortex_only_constraints"] = cortex_only
            report["omissions"] = omissions; report["contradictions"] = contradictions
    else:
        case_id = None; dimensions = DIMENSIONS; version = "unavailable"; adapter_projection = OrderedDict(); cortex_projection = OrderedDict(); result = "blocked"; allows_complementary = False
    case = inputs.get("case", {})
    source_digests.sort(key=lambda item: item["path"])
    identity = OrderedDict((("contract_version", CONTRACT_VERSION), ("case", case), ("rubric", inputs.get("rubric", {})), ("source_digests", source_digests)))
    report.update(OrderedDict((("schema_version", REPORT_SCHEMA), ("report_id", "replay-" + _digest(identity)[:24]), ("case_id", case.get("case_id", case_id)),
        ("source_digests", source_digests), ("source_trust_classes", ["explicit_local_json", "validated_advisory"]),
        ("comparator_version", COMPARATOR_VERSION), ("rubric_version", version), ("adapter_projection", adapter_projection), ("cortex_projection", cortex_projection),
        ("authority_regressions", [item for item in blockers if item["code"] == "self_granted_authority"]),
        ("dependency_and_collision_differences", [item for item in report["field_comparisons"] if item["dimension"] in {"dependency_graph", "resource_claims"}]),
        ("verification_and_receipt_differences", [item for item in report["field_comparisons"] if item["dimension"] == "verification_proof_commit_and_receipt_requirements"]),
        ("metrics", OrderedDict((("compared_dimensions", len(dimensions)), ("deterministic", True), ("adapter_constraint_count", sum(map(len, adapter_projection.values()))), ("cortex_constraint_count", sum(map(len, cortex_projection.values())))))),
        ("prior_report_comparison", OrderedDict((("provided", prior is not None), ("prior_result_class", prior.get("result_class") if prior else None)))),
        ("result_class", result), ("explanation_codes", sorted({item["relation"] for item in report["field_comparisons"]} | {item["code"] for item in blockers} | {item["code"] for item in report["contradictions"]})),
        ("blocked_reasons", sorted(blockers, key=lambda item: (item["code"], item["detail"]))), ("warnings", []), ("skipped_reasons", []),
        ("safe_to_use", result in {"equivalent", "cortex_stricter", "adapter_stricter", "complementary"} and not blockers),
        ("next_recommended_packet", NEXT_PACKET), ("authority_denials", list(AUTHORITY_DENIALS)))))
    return report, result


def exit_code(result_class: str, *, strict: bool, schema_only: bool = False) -> int:
    if schema_only or result_class in {"equivalent", "cortex_stricter", "adapter_stricter", "complementary"}:
        return 0
    if result_class == "blocked" or (strict and result_class in {"regression", "incomparable"}):
        return 2
    return 0 if result_class in {"regression", "incomparable"} else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare explicit Cortex replay artifacts without execution authority.")
    parser.add_argument("--json", action="store_true"); parser.add_argument("--schema-only", action="store_true")
    parser.add_argument("--case"); parser.add_argument("--adapter"); parser.add_argument("--synthesis"); parser.add_argument("--plan"); parser.add_argument("--rubric")
    parser.add_argument("--prior-report"); parser.add_argument("--output"); parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        report, result = (build_schema_only_payload(), "blocked") if args.schema_only else build_report(root=atlas_root(), case_path=args.case, adapter_path=args.adapter, synthesis_path=args.synthesis, plan_path=args.plan, rubric_path=args.rubric, prior_report_path=args.prior_report)
        if args.output:
            output, error = validate_output_path(atlas_root(), args.output)
            if error:
                report["blocked_reasons"] = sorted(list(report["blocked_reasons"]) + [error], key=lambda item: (item["code"], item["detail"])); report["result_class"] = "blocked"; report["safe_to_use"] = False; result = "blocked"
            else:
                assert output is not None
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return exit_code(result, strict=args.strict, schema_only=args.schema_only)
    except Exception as exc:
        report = build_schema_only_payload(); report["blocked_reasons"] = [_finding("internal_error", "Comparison failed before completion.", exception=str(exc))]
        print(json.dumps(report, indent=2, ensure_ascii=False)); return 3


if __name__ == "__main__":
    raise SystemExit(main())
