from __future__ import annotations

"""Deterministic, advisory-only Cortex execution planning.

This module deliberately only reads explicit local JSON/doc sources and can
write an explicitly requested ``tmp/atlas/**/*.json`` result.  It neither
executes work nor grants authority to execute work.
"""

import argparse
import fnmatch
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SCHEMA_VERSION = "atlas.cortex.execution_plan.v1"
SYNTHESIS_SCHEMA_VERSION = "atlas.cortex.chat_style_synthesis_packet.v1"
BRIDGE_SCHEMA_VERSION = "atlas.cortex.synthesis_execution_bridge_packet.v1"
CONTRACT_VERSION = "atlas.cortex.execution_planner_contract_registry.v1"
NO_EXECUTION_AUTHORITY = "no_execution_authority"

EXECUTION_CLASSES = ("read_only", "repo_worktree", "canonical_workspace")
MUTATING_EXECUTION_CLASSES = {"repo_worktree", "canonical_workspace"}
TOP_LEVEL_FIELDS = (
    "schema_version", "plan_id", "source_packet", "source_digests", "source_trust_classes",
    "selected_lane", "selected_marker", "selected_packet", "objective", "plan_status",
    "dependency_graph", "execution_waves", "job_candidates", "project_component_ownership",
    "runtime_recommendation", "permission_posture", "external_action_authority", "scope_lock",
    "resource_leases", "verification_requirements", "proof_requirements", "commit_requirements",
    "receipt_requirements", "rollback_requirements", "recovery_requirements", "collision_risks",
    "dependency_risks", "required_approvals", "blocked_reasons", "skipped_reasons",
    "next_recommended_packet", "safe_to_admit", "warnings",
)
AUTHORITY_DENIALS = (
    NO_EXECUTION_AUTHORITY,
    "no_final_receipt_authority",
    "no_marker_authority",
    "no_external_mutation_authority",
    "no_codex_launch",
    "no_queue_or_scheduler_creation",
    "no_owner_repository_mutation",
    "no_live_platform_query",
    "no_git_authority",
    "no_deploy_authority",
    "no_discord_or_card_authority",
    "no_database_authority",
)
RESOURCE_KINDS = (
    "files", "generated_artifacts", "schemas", "canonical_root", "worktrees", "ports",
    "browsers", "external_writers", "writer_scopes",
)
PROTECTED_PARTS = {"repos", "secrets", "runtime", ".vercel", ".codex", "archive", "archives"}
FORBIDDEN_PATH_TERMS = ("transcript", "conversation", "private-reasoning", "browser-profile", "account", "health", "payment", "live-platform", "network")
NEXT_PACKET = "Cortex Dual-Mode Replacement Readiness execution planner first-implementation worker-cluster reconciliation"


def atlas_root() -> Path:
    """Return the repository root without consulting environment or platform state."""
    return Path(__file__).resolve().parents[2]


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return OrderedDict((str(key), _canonical(value[key])) for key in sorted(value, key=str))
    if isinstance(value, list):
        normalized = [_canonical(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, separators=(",", ":"), ensure_ascii=False))
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _finding(code: str, detail: str, **extra: Any) -> OrderedDict[str, Any]:
    return OrderedDict((("code", code), ("detail", detail), *sorted(extra.items())))


def _path_error(argument: str, *, output: bool = False) -> str | None:
    path = Path(argument)
    normalized = argument.replace("\\", "/")
    parts = [part.lower() for part in normalized.split("/") if part not in ("", ".")]
    if path.is_absolute() or (len(argument) > 1 and argument[1] == ":"):
        return "absolute_output_path" if output else "absolute_input_path"
    if ".." in parts:
        return "parent_traversal"
    if any(part in PROTECTED_PARTS or part.startswith(".env") for part in parts):
        return "protected_path"
    lowered = normalized.lower()
    if any(term in lowered for term in FORBIDDEN_PATH_TERMS):
        return "forbidden_source_class"
    return None


def validate_input_path(root: Path, argument: str, *, packet: bool = False) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    error = _path_error(argument)
    normalized = argument.replace("\\", "/")
    allowed = normalized.startswith("docs/") or normalized.startswith("tmp/atlas/")
    if error:
        return None, _finding(error, "Input path is not admitted.", path=argument)
    if not allowed or (not packet and normalized.startswith("tmp/atlas/") and not normalized.endswith(".json")):
        return None, _finding("unadmitted_input_path", "Inputs must be explicit docs or tmp/atlas JSON sources.", path=argument)
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
        return None, _finding("unadmitted_output_path", "Output must be an explicit tmp/atlas JSON path.", path=argument)
    candidate = root / Path(argument)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None, _finding("parent_traversal", "Output escapes the Atlas root.", path=argument)
    return candidate, None


def _read_json(root: Path, argument: str) -> tuple[Any | None, OrderedDict[str, Any] | None, str | None]:
    path, error = validate_input_path(root, argument, packet=True)
    if error:
        return None, error, None
    assert path is not None
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text), None, hashlib.sha256(text.encode("utf-8")).hexdigest()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _finding("invalid_json", "Input must be valid UTF-8 JSON.", path=argument, exception=str(exc)), None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).replace("\\", "/") for item in value if isinstance(item, (str, int, float))})


def _repository_identity(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("\\", "/")
    lowered = raw.casefold()
    if lowered.startswith("git@github.com:"):
        path = raw.split(":", 1)[1]
    elif "://" in raw:
        parsed = urlsplit(raw)
        if parsed.hostname is None or parsed.hostname.casefold() != "github.com" or parsed.query or parsed.fragment:
            return None
        path = parsed.path
    elif lowered.startswith("github.com/"):
        path = raw[len("github.com/") :]
    else:
        path = raw
    path = path.strip("/")
    if path.casefold().endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return "/".join(part.casefold() for part in parts)


def _external_writer_identity(value: str) -> str:
    raw = value.strip()
    if "://" in raw:
        parsed = urlsplit(raw)
        parts = parsed.path.strip("/").split("/")
        if parsed.hostname and parsed.hostname.casefold() == "github.com" and len(parts) >= 3 and parts[2].casefold() == "pull":
            if len(parts) < 4 or not parts[3].isdigit():
                return ""
            repository = _repository_identity("/".join(parts[:2]))
            if repository:
                return f"github-pr:{repository}#{int(parts[3])}"
        return raw.casefold()
    prefix, separator, remainder = raw.partition(":")
    normalized_prefix = prefix.casefold()
    if not separator or normalized_prefix not in {"github", "github-pr", "git-branch"}:
        return value.strip()
    repository_token, suffix_separator, suffix = remainder.partition(":")
    repository, pr_separator, pr_number = repository_token.partition("#")
    normalized_repository = _repository_identity(repository)
    if not normalized_repository:
        return ""
    if pr_separator:
        if not pr_number.isdigit():
            return ""
        return f"github-pr:{normalized_repository}#{int(pr_number)}"
    if normalized_prefix == "github-pr":
        return ""
    normalized = f"{normalized_prefix}:{normalized_repository}"
    if suffix_separator:
        normalized += f":{suffix}"
    return normalized


def _writer_scope(job: dict[str, Any]) -> str | None:
    declared = job.get("writer_scope")
    if isinstance(declared, str) and declared.strip():
        return declared.strip()
    execution_class = job.get("execution_class")
    if execution_class == "canonical_workspace":
        return "atlas.root"
    repository = _repository_identity(job.get("repository"))
    if execution_class == "repo_worktree" and repository:
        return f"repo.{repository}"
    return None


def _normalized_claims(job: dict[str, Any]) -> OrderedDict[str, list[str]]:
    raw = job.get("resource_claims") if isinstance(job.get("resource_claims"), dict) else {}
    claims: OrderedDict[str, list[str]] = OrderedDict()
    for kind in RESOURCE_KINDS:
        value = raw.get(kind, [])
        if kind == "files":
            value = list(value) if isinstance(value, list) else value
            if isinstance(value, list):
                value += job.get("allowed_files", []) if isinstance(job.get("allowed_files"), list) else []
        if value is True and kind == "canonical_root":
            value = ["canonical_root"]
        if kind == "canonical_root" and job.get("execution_class") == "canonical_workspace":
            value = list(value) if isinstance(value, list) else []
            value.append("atlas")
        if kind == "writer_scopes":
            value = list(value) if isinstance(value, list) else []
            writer_scope = _writer_scope(job)
            if writer_scope:
                value.append(writer_scope)
        claims[kind] = _string_list(value)
        if kind == "external_writers":
            claims[kind] = sorted(
                identity
                for identity in {_external_writer_identity(item) for item in claims[kind]}
                if identity
            )
    return claims


def _candidate_id(job: dict[str, Any]) -> str:
    return "job-" + _digest(OrderedDict((("contract_version", CONTRACT_VERSION), ("job", job))))[:16]


def _normalize_job(raw: Any) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    if not isinstance(raw, dict):
        return None, [_finding("invalid_job_shape", "Each execution job must be an object.")]
    for field in ("objective", "project", "component", "repository", "owner"):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            blockers.append(_finding("missing_ownership" if field == "owner" else "invalid_job_shape", "Required job field is missing.", field=field))
    execution_class = raw.get("execution_class")
    if execution_class not in EXECUTION_CLASSES:
        blockers.append(_finding("invalid_execution_class", "Execution class is unavailable.", value=execution_class))
    if not isinstance(raw.get("dependencies", []), list):
        blockers.append(_finding("invalid_job_shape", "Dependencies must be an array.", field="dependencies"))
    for field in ("allowed_files", "forbidden_files", "external_actions", "required_approvals"):
        if field in raw and not isinstance(raw[field], list):
            blockers.append(_finding("invalid_job_shape", "Job collection field must be an array.", field=field))
    if "resource_claims" in raw and not isinstance(raw["resource_claims"], dict):
        blockers.append(_finding("invalid_job_shape", "resource_claims must be an object."))
    raw_claims = raw.get("resource_claims") if isinstance(raw.get("resource_claims"), dict) else {}
    external_writers = raw_claims.get("external_writers", [])
    if not isinstance(external_writers, list) or any(
        not isinstance(item, str) or not item.strip() or not _external_writer_identity(item)
        for item in external_writers
    ):
        blockers.append(
            _finding(
                "invalid_resource_claim",
                "External writer claims must use a recognized, complete resource identity.",
                field="resource_claims.external_writers",
            )
        )
    if "writer_scope" in raw and (not isinstance(raw["writer_scope"], str) or not raw["writer_scope"].strip()):
        blockers.append(_finding("invalid_job_shape", "writer_scope must be a non-empty string when supplied."))
    repository = _repository_identity(raw.get("repository"))
    if repository is None:
        blockers.append(
            _finding(
                "invalid_job_shape",
                "Repository identity must be an owner/repo value or recognized GitHub alias.",
                field="repository",
            )
        )
    candidate_id = _candidate_id(raw)
    candidate = OrderedDict(
        (("job_id", candidate_id), ("source_job_id", raw.get("job_id")), ("objective", raw.get("objective")),
         ("project", raw.get("project")), ("component", raw.get("component")), ("repository", repository),
         ("owner", raw.get("owner")), ("execution_class", execution_class),
         ("writer_scope", _writer_scope(raw)),
         ("allowed_files", _string_list(raw.get("allowed_files", []))), ("forbidden_files", _string_list(raw.get("forbidden_files", []))),
         ("dependencies", _string_list(raw.get("dependencies", []))), ("resource_claims", _normalized_claims(raw)),
         ("runtime", _canonical(raw.get("runtime", {})) if isinstance(raw.get("runtime", {}), dict) else OrderedDict()),
         ("external_actions", _string_list(raw.get("external_actions", []))),
         ("required_approvals", _canonical(raw.get("required_approvals", [])) if isinstance(raw.get("required_approvals", []), list) else []),
         ("verification_requirements", _canonical(raw.get("verification_requirements", []))),
         ("proof_requirements", _canonical(raw.get("proof_requirements", []))),
         ("commit_requirements", _canonical(raw.get("commit_requirements", []))),
         ("receipt_requirements", _canonical(raw.get("receipt_requirements", []))),
         ("rollback_requirements", _canonical(raw.get("rollback_requirements", []))),
         ("recovery_requirements", _canonical(raw.get("recovery_requirements", [])))))
    return candidate, blockers


def _patterns_overlap(left: str, right: str) -> bool:
    if left == right or fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    left_prefix, right_prefix = left.split("**", 1)[0], right.split("**", 1)[0]
    return bool(left_prefix and right_prefix and (left.startswith(right_prefix) or right.startswith(left_prefix)))


def _collision_kinds(left: OrderedDict[str, Any], right: OrderedDict[str, Any]) -> list[str]:
    kinds: list[str] = []
    left_claims, right_claims = left["resource_claims"], right["resource_claims"]
    for kind in RESOURCE_KINDS:
        values_left, values_right = left_claims[kind], right_claims[kind]
        if kind == "files":
            if left.get("repository") == right.get("repository") and any(
                _patterns_overlap(a, b) for a in values_left for b in values_right
            ):
                kinds.append(kind)
        elif set(values_left).intersection(values_right):
            kinds.append(kind)
    same_repository_mutation = (
        left.get("execution_class") in MUTATING_EXECUTION_CLASSES
        and right.get("execution_class") in MUTATING_EXECUTION_CLASSES
        and bool(left.get("repository"))
        and left.get("repository") == right.get("repository")
    )
    if same_repository_mutation:
        if "canonical_workspace" in {left.get("execution_class"), right.get("execution_class")}:
            kinds.append("canonical_root")
        else:
            complete_isolation_claims = all(
                claims.get(kind)
                for claims in (left_claims, right_claims)
                for kind in ("worktrees", "files")
            )
            worktrees_overlap = any(
                _patterns_overlap(a, b)
                for a in left_claims["worktrees"]
                for b in right_claims["worktrees"]
            )
            if not complete_isolation_claims:
                kinds.append("repository")
            elif worktrees_overlap:
                kinds.append("worktrees")
    return sorted(kinds)


def _runtime_recommendation(candidates: list[OrderedDict[str, Any]], blockers: list[OrderedDict[str, Any]], warnings: list[OrderedDict[str, Any]]) -> OrderedDict[str, Any]:
    requested = next((candidate["runtime"] for candidate in candidates if candidate["runtime"]), OrderedDict())
    speed = requested.get("speed", "standard")
    supports_fast = requested.get("fast_supported") is True or requested.get("supported_model_capability") == "fast"
    fallback = requested.get("fallback", "standard_with_warning")
    if speed == "fast" and not supports_fast:
        if fallback == "blocked":
            blockers.append(_finding("unsupported_runtime_without_fallback", "Fast runtime lacks an explicit supported-model capability."))
        else:
            speed = "standard"
            warnings.append(_finding("fast_fallback", "Fast requested without supported-model capability; standard is recommended."))
    return OrderedDict(
        (("advisory_only", True), ("provider", requested.get("provider", "unresolved")),
         ("model", requested.get("model", "unresolved")), ("reasoning", requested.get("reasoning", "unresolved")),
         ("speed", speed), ("fallback", fallback), ("effective_runtime_must_be_resolved_by_stack", True)))


def _source_claim_conflicts(packet: dict[str, Any]) -> list[OrderedDict[str, Any]]:
    seen: dict[str, str] = {}
    findings: list[OrderedDict[str, Any]] = []
    digests = packet.get("source_digests", [])
    if not isinstance(digests, list):
        return [_finding("invalid_source_schema", "source_digests must be an array when supplied.")]
    for item in digests:
        if not isinstance(item, dict):
            continue
        path, digest = item.get("path") or item.get("source"), item.get("sha256") or item.get("digest")
        if isinstance(path, str) and isinstance(digest, str):
            if path in seen and seen[path] != digest:
                findings.append(_finding("digest_conflict", "A source path has conflicting digests.", path=path))
            seen[path] = digest
    return findings


def _empty_plan() -> OrderedDict[str, Any]:
    return OrderedDict((field, [] if field in {"source_digests", "source_trust_classes", "dependency_graph", "execution_waves", "job_candidates", "project_component_ownership", "scope_lock", "resource_leases", "verification_requirements", "proof_requirements", "commit_requirements", "receipt_requirements", "rollback_requirements", "recovery_requirements", "collision_risks", "dependency_risks", "required_approvals", "blocked_reasons", "skipped_reasons", "warnings"} else None) for field in TOP_LEVEL_FIELDS)


def build_schema_only_payload() -> OrderedDict[str, Any]:
    plan = _empty_plan()
    plan.update(OrderedDict(
        (("schema_version", SCHEMA_VERSION), ("plan_id", "execution-plan-schema-only"),
         ("source_packet", OrderedDict()), ("source_trust_classes", ["validated_advisory", "durable_root_truth", "explicit_task_local"]),
         ("selected_lane", "schema_only"), ("selected_marker", "schema_only"), ("selected_packet", "schema_only"),
         ("objective", "Describe the deterministic advisory execution-plan schema without planning work."), ("plan_status", "draft"),
         ("runtime_recommendation", OrderedDict((("advisory_only", True), ("allowed_speeds", ["standard", "fast"]), ("fast_fallback", ["standard_with_warning", "blocked"])))),
         ("permission_posture", OrderedDict((("full_local_access_is_capability_only", True), ("external_mutation_authority", False)))),
         ("external_action_authority", OrderedDict((("planner_authority", NO_EXECUTION_AUTHORITY), ("denials", list(AUTHORITY_DENIALS))))),
         ("next_recommended_packet", NEXT_PACKET), ("safe_to_admit", False),
         ("warnings", [_finding("schema_only", "No real plan or admission recommendation exists in schema-only mode.")]))))
    return plan


def build_plan(*, root: Path, synthesis_path: str | None, bridge_path: str | None, sources: list[str]) -> tuple[OrderedDict[str, Any], str]:
    blockers: list[OrderedDict[str, Any]] = []
    conflicts: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []
    if not synthesis_path or not bridge_path:
        blockers.append(_finding("missing_required_input", "Both synthesis and bridge packets are required."))
        return _finalize_error_plan(blockers, warnings), "blocker"
    synthesis, synthesis_error, synthesis_digest = _read_json(root, synthesis_path)
    bridge, bridge_error, bridge_digest = _read_json(root, bridge_path)
    if synthesis_error:
        blockers.append(synthesis_error)
    if bridge_error:
        blockers.append(bridge_error)
    if not isinstance(synthesis, dict) or synthesis.get("schema_version") != SYNTHESIS_SCHEMA_VERSION:
        blockers.append(_finding("invalid_synthesis_schema", "Synthesis packet schema is not admitted."))
    if not isinstance(bridge, dict) or bridge.get("schema_version") != BRIDGE_SCHEMA_VERSION:
        blockers.append(_finding("invalid_bridge_schema", "Bridge packet schema is not admitted."))
    source_digests: list[OrderedDict[str, Any]] = []
    for name, digest in ((synthesis_path, synthesis_digest), (bridge_path, bridge_digest)):
        if digest:
            source_digests.append(OrderedDict((("path", name.replace("\\", "/")), ("sha256", digest))))
    for source in sorted(set(sources)):
        path, error = validate_input_path(root, source)
        if error:
            blockers.append(error)
            continue
        assert path is not None
        source_digests.append(OrderedDict((("path", source.replace("\\", "/")), ("sha256", hashlib.sha256(path.read_bytes()).hexdigest()))))
    if blockers:
        return _finalize_error_plan(blockers, warnings, source_digests=source_digests), "blocker"
    assert isinstance(synthesis, dict) and isinstance(bridge, dict)
    for packet in (synthesis, bridge):
        blockers.extend(_source_claim_conflicts(packet))
        if packet.get("stale") is True or packet.get("source_truth") == "stale":
            blockers.append(_finding("stale_source_truth", "Packet declares stale truth."))
        if packet.get("marker_conflict") is True:
            blockers.append(_finding("marker_conflict", "Packet declares conflicting marker truth."))
    if synthesis.get("status") == "conflict" or bridge.get("status") == "conflict":
        conflicts.append(_finding("source_conflict", "An admitted advisory packet reports a conflict."))
    if synthesis.get("status") == "blocker" or bridge.get("status") == "blocker":
        blockers.append(_finding("source_blocker", "An admitted advisory packet reports a blocker."))
    contract = bridge.get("execution_contract")
    if not isinstance(contract, dict):
        blockers.append(_finding("invalid_bridge_schema", "Bridge needs an execution_contract object."))
        return _finalize_error_plan(blockers, warnings, source_digests=source_digests), "blocker"
    for field in ("selected_lane", "selected_marker", "selected_packet", "objective"):
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            blockers.append(_finding("missing_scope_truth", "Execution contract must name one admitted scope.", field=field))
    raw_jobs = contract.get("jobs", [contract])
    if not isinstance(raw_jobs, list) or not raw_jobs:
        blockers.append(_finding("invalid_job_shape", "execution_contract must contain one or more jobs."))
        return _finalize_error_plan(blockers, warnings, source_digests=source_digests), "blocker"
    candidates: list[OrderedDict[str, Any]] = []
    source_ids: dict[str, str] = {}
    for raw in raw_jobs:
        candidate, job_blockers = _normalize_job(raw)
        blockers.extend(job_blockers)
        if candidate:
            candidates.append(candidate)
            if isinstance(candidate["source_job_id"], str):
                if candidate["source_job_id"] in source_ids:
                    blockers.append(_finding("duplicate_job_id", "Source job IDs must be unique.", job_id=candidate["source_job_id"]))
                source_ids[candidate["source_job_id"]] = candidate["job_id"]
    candidates.sort(key=lambda item: item["job_id"])
    ids = {candidate["job_id"] for candidate in candidates}
    edges: list[OrderedDict[str, str]] = []
    for candidate in candidates:
        resolved: list[str] = []
        for dependency in candidate["dependencies"]:
            dependency_id = source_ids.get(dependency, dependency)
            if dependency_id not in ids:
                blockers.append(_finding("unknown_dependency", "Dependency does not name an admitted job.", dependency=dependency, job_id=candidate["job_id"]))
            else:
                resolved.append(dependency_id)
                edges.append(OrderedDict((("from", dependency_id), ("to", candidate["job_id"]))))
        candidate["dependencies"] = sorted(set(resolved))
    edges.sort(key=lambda edge: (edge["to"], edge["from"]))
    cycle = _has_cycle(candidates)
    if cycle:
        blockers.append(_finding("dependency_cycle", "Dependency graph contains a cycle.", jobs=cycle))
    external_actions = sorted({action for candidate in candidates for action in candidate["external_actions"]})
    authority = contract.get("external_action_authority", NO_EXECUTION_AUTHORITY)
    approval_items = list(contract.get("required_approvals", [])) if isinstance(contract.get("required_approvals", []), list) else []
    for candidate in candidates:
        approval_items.extend(candidate["required_approvals"])
    approvals = _canonical(approval_items)
    if external_actions and authority != "explicit_task_local_authority":
        blockers.append(_finding("unknown_external_authority", "External actions require explicit task-local authority."))
    if external_actions and not approvals:
        blockers.append(_finding("missing_required_approvals", "External actions require explicit approvals."))
    runtime = _runtime_recommendation(candidates, blockers, warnings)
    waves, collision_risks = _assign_waves(candidates) if not cycle else ([], [])
    status = "blocker" if blockers else "conflict" if conflicts else "advisory_gap" if warnings else "ok"
    plan_status = "blocked" if status in {"blocker", "conflict"} else "ready_for_admission"
    seed = OrderedDict((("contract_version", CONTRACT_VERSION), ("source_digests", source_digests), ("candidates", candidates), ("edges", edges)))
    plan = _empty_plan()
    plan.update(OrderedDict(
        (("schema_version", SCHEMA_VERSION), ("plan_id", "plan-" + _digest(seed)[:20]),
         ("source_packet", OrderedDict((("synthesis", synthesis.get("packet_id", synthesis_path)), ("bridge", bridge.get("packet_id", bridge_path))))),
         ("source_digests", sorted(source_digests, key=lambda item: item["path"])),
         ("source_trust_classes", ["validated_advisory"] + (["durable_root_truth"] if sources else [])),
         ("selected_lane", contract.get("selected_lane")), ("selected_marker", contract.get("selected_marker")),
         ("selected_packet", contract.get("selected_packet")), ("objective", contract.get("objective")),
         ("plan_status", plan_status), ("dependency_graph", edges), ("execution_waves", waves),
         ("job_candidates", candidates),
         ("project_component_ownership", [OrderedDict((("job_id", c["job_id"]), ("project", c["project"]), ("component", c["component"]), ("repository", c["repository"]), ("owner", c["owner"]), ("writer_scope", c["writer_scope"]))) for c in candidates]),
         ("runtime_recommendation", runtime),
         ("permission_posture", OrderedDict((("full_local_access_is_capability_only", True), ("requested_capability", contract.get("local_capability", "unresolved")), ("planner_cannot_apply_permissions", True)))),
         ("external_action_authority", OrderedDict((("planner_authority", NO_EXECUTION_AUTHORITY), ("requested_authority", authority), ("requested_actions", external_actions), ("denials", list(AUTHORITY_DENIALS))))),
         ("scope_lock", [OrderedDict((("job_id", c["job_id"]), ("allowed_files", c["allowed_files"]), ("forbidden_files", c["forbidden_files"]))) for c in candidates]),
         ("resource_leases", [OrderedDict((("job_id", c["job_id"]), ("writer_scope", c["writer_scope"]), ("claims", c["resource_claims"]), ("advisory_only", True))) for c in candidates]),
         ("verification_requirements", [OrderedDict((("job_id", c["job_id"]), ("requirements", c["verification_requirements"]))) for c in candidates]),
         ("proof_requirements", [OrderedDict((("job_id", c["job_id"]), ("requirements", c["proof_requirements"]))) for c in candidates]),
         ("commit_requirements", [OrderedDict((("job_id", c["job_id"]), ("requirements", c["commit_requirements"]))) for c in candidates]),
         ("receipt_requirements", [OrderedDict((("job_id", c["job_id"]), ("requirements", c["receipt_requirements"]))) for c in candidates]),
         ("rollback_requirements", [OrderedDict((("job_id", c["job_id"]), ("requirements", c["rollback_requirements"]))) for c in candidates]),
         ("recovery_requirements", [OrderedDict((("job_id", c["job_id"]), ("requirements", c["recovery_requirements"]))) for c in candidates]),
         ("collision_risks", collision_risks), ("dependency_risks", [_finding("dependency_cycle", "Dependency graph blocks wave assignment.")] if cycle else []),
         ("required_approvals", approvals), ("blocked_reasons", sorted(blockers, key=lambda item: (item["code"], item["detail"]))),
         ("skipped_reasons", []), ("next_recommended_packet", NEXT_PACKET),
         ("safe_to_admit", plan_status == "ready_for_admission" and not blockers and not conflicts),
         ("warnings", sorted(warnings, key=lambda item: (item["code"], item["detail"]))))))
    return plan, status


def _has_cycle(candidates: list[OrderedDict[str, Any]]) -> list[str]:
    graph = {candidate["job_id"]: candidate["dependencies"] for candidate in candidates}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    def visit(job_id: str) -> list[str]:
        if job_id in visiting:
            return stack[stack.index(job_id):] + [job_id]
        if job_id in visited:
            return []
        visiting.add(job_id); stack.append(job_id)
        for dependency in graph[job_id]:
            found = visit(dependency)
            if found:
                return found
        stack.pop(); visiting.remove(job_id); visited.add(job_id)
        return []
    for job_id in sorted(graph):
        found = visit(job_id)
        if found:
            return found
    return []


def _assign_waves(candidates: list[OrderedDict[str, Any]]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    by_id = {candidate["job_id"]: candidate for candidate in candidates}
    pending = set(by_id)
    assigned: dict[str, int] = {}
    waves: dict[int, list[str]] = {}
    risks: list[OrderedDict[str, Any]] = []
    while pending:
        available = sorted(job_id for job_id in pending if all(dependency in assigned for dependency in by_id[job_id]["dependencies"]))
        if not available:
            break
        for job_id in available:
            candidate = by_id[job_id]
            wave = max([assigned[dependency] + 1 for dependency in candidate["dependencies"]] or [1])
            while True:
                occupants = [by_id[item] for item in waves.get(wave, [])]
                collisions = [(occupant, _collision_kinds(candidate, occupant)) for occupant in occupants]
                collisions = [(occupant, kinds) for occupant, kinds in collisions if kinds]
                if not collisions:
                    break
                for occupant, kinds in collisions:
                    risks.append(OrderedDict((("jobs", sorted([job_id, occupant["job_id"]])), ("resource_kinds", kinds), ("serialized", True))))
                wave += 1
            assigned[job_id] = wave
            waves.setdefault(wave, []).append(job_id)
            pending.remove(job_id)
    result = [OrderedDict((("wave", number), ("job_ids", sorted(job_ids)))) for number, job_ids in sorted(waves.items())]
    unique_risks = OrderedDict((json.dumps(risk, separators=(",", ":")), risk) for risk in risks)
    return result, [unique_risks[key] for key in sorted(unique_risks)]


def _finalize_error_plan(blockers: list[OrderedDict[str, Any]], warnings: list[OrderedDict[str, Any]], *, source_digests: list[OrderedDict[str, Any]] | None = None) -> OrderedDict[str, Any]:
    plan = build_schema_only_payload()
    plan["plan_id"] = "plan-" + _digest(OrderedDict((("contract_version", CONTRACT_VERSION), ("blockers", blockers))))[:20]
    plan["plan_status"] = "blocked"
    plan["source_digests"] = sorted(source_digests or [], key=lambda item: item["path"])
    plan["blocked_reasons"] = sorted(blockers, key=lambda item: (item["code"], item["detail"]))
    plan["warnings"] = sorted(warnings, key=lambda item: (item["code"], item["detail"]))
    plan["safe_to_admit"] = False
    return plan


def exit_code(status: str, *, strict: bool) -> int:
    if status in {"ok", "advisory_gap"}:
        return 0
    if status == "conflict":
        return 2 if strict else 0
    return 2 if status == "blocker" else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic advisory Cortex execution plan.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--synthesis-packet")
    parser.add_argument("--bridge-packet")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args(argv)
    root = atlas_root()
    try:
        if args.schema_only:
            plan, status = build_schema_only_payload(), "ok"
        else:
            plan, status = build_plan(root=root, synthesis_path=args.synthesis_packet, bridge_path=args.bridge_packet, sources=list(args.source))
        if args.output:
            output, error = validate_output_path(root, args.output)
            if error:
                plan["plan_status"] = "blocked"
                plan["blocked_reasons"] = sorted(list(plan["blocked_reasons"]) + [error], key=lambda item: (item["code"], item["detail"]))
                plan["safe_to_admit"] = False
                status = "blocker"
            else:
                assert output is not None
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(plan, indent=2, ensure_ascii=False) if args.json else json.dumps(plan, indent=2, ensure_ascii=False))
        return exit_code(status, strict=args.strict)
    except Exception as exc:
        plan = _finalize_error_plan([_finding("internal_error", "Planning failed before completion.", exception=str(exc))], [])
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
