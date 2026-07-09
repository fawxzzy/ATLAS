from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.vercel_observability_project_inventory.v1"
EXPORT_SCHEMA_VERSION = "atlas.vercel.observability.project_inventory_export.v1"
EXPORT_SOURCE = "vercel.read_only.observability.project_inventory.v1"

STATUS_OK = "ok"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

AUDIT_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md"
CONTRACT_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-CONTRACT-FREEZE-2026-07-09.md"
)
CURRENT_STATE = "docs/atlas-book/01-current-state.md"
RECEIPT_INDEX = "docs/atlas-book/05-receipt-index.md"
RESTART_GUIDE = "docs/atlas-book/12-restart-and-handoff-guide.md"
STACK_REPO_INVENTORY = "docs/registry/STACK-REPO-INVENTORY.json"

REQUIRED_TEXT_REFS = (
    AUDIT_RECEIPT,
    CONTRACT_RECEIPT,
    CURRENT_STATE,
    RECEIPT_INDEX,
    RESTART_GUIDE,
)

REQUIRED_INVENTORY_IDS = ("discordos", "fitness", "mazer", "trove", "foundation")

EXPECTED_TEAM_ID = "team_CMJn7MvzFZZBnhNnjVUZF2RD"
EXPECTED_TEAM_NAME = "fawxzzy"

ALLOWED_POSTURE_CLASSES = {
    "vercel_observability_discordos_only",
    "vercel_observability_atlas_visible",
    "vercel_observability_connector_visible",
    "vercel_observability_partial",
    "vercel_observability_full_read_only",
    "vercel_observability_mutation_risk",
    "vercel_observability_unknown",
}

ALLOWED_INVENTORY_SCOPES = {
    "in_scope_governed_repo",
    "inventory_only_governed_repo",
    "adjacent_owner_lane_surface",
    "unknown_mapping",
}

ALLOWED_OBSERVABILITY_STATES = {"visible", "unproven", "forbidden", "unknown"}

FORBIDDEN_KEYS = {
    "env_value",
    "env_values",
    "secret_value",
    "secret_values",
    "token_value",
    "token_values",
    "authorization_header",
    "headers",
    "request_body",
}

GOVERNED_PROJECTS = OrderedDict(
    [
        (
            "prj_C2RSEa34OblHfhuEpVChRQQZSjuG",
            OrderedDict(
                [
                    ("project_name", "fawxzzy-discordos"),
                    ("repo_logical_id", "discordos"),
                ]
            ),
        ),
        (
            "prj_rtlFVOMFAWCRoJ3SQjHloi89881K",
            OrderedDict(
                [
                    ("project_name", "fawxzzy-fitness"),
                    ("repo_logical_id", "fitness"),
                ]
            ),
        ),
        (
            "prj_t3zothbtj9DExrh3FjMsH98hwwSZ",
            OrderedDict(
                [
                    ("project_name", "fawxzzy-mazer"),
                    ("repo_logical_id", "mazer"),
                ]
            ),
        ),
        (
            "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV",
            OrderedDict(
                [
                    ("project_name", "fawxzzy-trove"),
                    ("repo_logical_id", "trove"),
                ]
            ),
        ),
        (
            "prj_o37CPLlESB6Zybe8GB74BX3wrkpy",
            OrderedDict(
                [
                    ("project_name", "fawxzzy-foundation"),
                    ("repo_logical_id", "foundation"),
                ]
            ),
        ),
    ]
)


def _finding(code: str, message: str, *, severity: str = "blocker", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _read_text(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="ignore")


def _load_json(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _normal(value: str | Path) -> str:
    return normalize_slashes(str(value)).strip("/")


def _protected_path(relative_path: str) -> bool:
    normalized = _normal(relative_path)
    if not normalized:
        return True
    if normalized.startswith(("repos/", "secrets/", "runtime/", ".vercel/", ".playwright-mcp/", "archive/")):
        return True
    return any(part.startswith(".env") for part in normalized.split("/"))


def validate_runtime_json_path(*, root: Path, relative_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return None, _finding("absolute_path", "Path must be root-relative.", path=normalize_slashes(str(candidate)))
    normalized = _normal(candidate)
    if ".." in Path(normalized).parts:
        return None, _finding("parent_traversal_path", "Path must not use parent traversal.", path=normalized)
    if _protected_path(normalized) or not normalized.startswith("tmp/") or not normalized.endswith(".json"):
        return None, _finding("protected_path", "Paths are admitted only under root-relative tmp/**.json.", path=normalized)
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=normalized)
    return resolved, None


def _inventory_ids(payload: dict[str, Any]) -> set[str]:
    repos = payload.get("repos")
    if not isinstance(repos, list):
        return set()
    ids: set[str] = set()
    for item in repos:
        if isinstance(item, dict) and isinstance(item.get("logical_id"), str):
            ids.add(str(item["logical_id"]))
    return ids


def _ensure_required_files(root: Path) -> tuple[dict[str, str], list[OrderedDict[str, Any]]]:
    texts: dict[str, str] = {}
    blockers: list[OrderedDict[str, Any]] = []
    for ref in REQUIRED_TEXT_REFS:
        text = _read_text(root / ref)
        if text is None:
            blockers.append(_finding("required_receipt_missing", "Required root-owned Vercel governance input is missing.", path=ref))
            continue
        texts[ref] = text
    inventory = _load_json(root / STACK_REPO_INVENTORY)
    if inventory is None:
        blockers.append(_finding("stack_repo_inventory_missing", "Required stack repo inventory JSON is missing or malformed.", path=STACK_REPO_INVENTORY))
    else:
        texts[STACK_REPO_INVENTORY] = json.dumps(inventory)
        inventory_ids = _inventory_ids(inventory)
        missing_ids = [repo_id for repo_id in REQUIRED_INVENTORY_IDS if repo_id not in inventory_ids]
        if missing_ids:
            blockers.append(
                _finding(
                    "stack_repo_inventory_incomplete",
                    "Stack repo inventory is missing one or more required logical ids.",
                    missing_ids=missing_ids,
                )
            )
    return texts, blockers


def _validate_contract_texts(texts: dict[str, str], blockers: list[OrderedDict[str, Any]]) -> None:
    audit_text = texts.get(AUDIT_RECEIPT, "")
    for project_id, meta in GOVERNED_PROJECTS.items():
        if project_id not in audit_text or meta["project_name"] not in audit_text:
            blockers.append(
                _finding(
                    "audit_project_missing",
                    "Vercel audit receipt does not contain the expected governed project entry.",
                    project_name=meta["project_name"],
                    project_id=project_id,
                )
            )
    contract_text = texts.get(CONTRACT_RECEIPT, "")
    for needle in ("ops/atlas/vercel_observability_project_inventory.py", "env-name-only", "vercel_observability_mutation_risk"):
        if needle not in contract_text:
            blockers.append(
                _finding(
                    "contract_missing_required_reference",
                    "Vercel project inventory contract is missing a required boundary reference.",
                    required_reference=needle,
                )
            )


def _ensure_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _ensure_bool(payload: dict[str, Any], key: str) -> bool | None:
    value = payload.get(key)
    return value if isinstance(value, bool) else None


def _scan_forbidden_keys(value: Any, *, path: str = "") -> list[OrderedDict[str, Any]]:
    blockers: list[OrderedDict[str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str) and key in FORBIDDEN_KEYS:
                blockers.append(_finding("forbidden_sensitive_key", "Wrapper includes a forbidden sensitive field.", path=f"{path}.{key}".strip(".")))
            blockers.extend(_scan_forbidden_keys(nested, path=f"{path}.{key}".strip(".")))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            blockers.extend(_scan_forbidden_keys(nested, path=f"{path}[{index}]"))
    return blockers


def _deployment_sort_key(item: dict[str, Any]) -> tuple[str, str]:
    created_at = item.get("created_at")
    deployment_id = item.get("id")
    return (created_at if isinstance(created_at, str) else "", deployment_id if isinstance(deployment_id, str) else "")


def _validate_project_wrapper(*, wrapper: dict[str, Any]) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []

    if wrapper.get("schema_version") != EXPORT_SCHEMA_VERSION:
        blockers.append(
            _finding(
                "unexpected_wrapper_schema",
                "Input wrapper does not use the admitted Vercel inventory export schema.",
                expected=EXPORT_SCHEMA_VERSION,
                actual=wrapper.get("schema_version"),
            )
        )
        return None, blockers, warnings

    blockers.extend(_scan_forbidden_keys(wrapper))

    captured_at = _ensure_string(wrapper, "captured_at")
    source = _ensure_string(wrapper, "source")
    team = wrapper.get("team")
    project = wrapper.get("project")
    deployments = wrapper.get("deployments")
    log_surfaces = wrapper.get("log_surfaces")
    runtime_errors = wrapper.get("runtime_error_observations")
    observability_surfaces = wrapper.get("observability_surfaces")
    posture_classes = wrapper.get("posture_classes")

    if captured_at is None:
        blockers.append(_finding("captured_at_missing", "Input wrapper must include a string captured_at field."))
    if source != EXPORT_SOURCE:
        blockers.append(
            _finding(
                "unexpected_source",
                "Input wrapper must use the admitted exported source value.",
                expected=EXPORT_SOURCE,
                actual=source,
            )
        )
    if not isinstance(team, dict):
        blockers.append(_finding("team_missing", "Input wrapper must include an object team field."))
    if not isinstance(project, dict):
        blockers.append(_finding("project_missing", "Input wrapper must include an object project field."))
    if not isinstance(deployments, list):
        blockers.append(_finding("deployments_missing", "Input wrapper must include a deployments array."))
        deployments = []
    if not isinstance(log_surfaces, dict):
        blockers.append(_finding("log_surfaces_missing", "Input wrapper must include an object log_surfaces field."))
    if not isinstance(runtime_errors, list):
        blockers.append(_finding("runtime_error_observations_missing", "Input wrapper must include a runtime_error_observations array."))
        runtime_errors = []
    if not isinstance(observability_surfaces, dict):
        blockers.append(_finding("observability_surfaces_missing", "Input wrapper must include an object observability_surfaces field."))
    if not isinstance(posture_classes, list):
        blockers.append(_finding("posture_classes_missing", "Input wrapper must include a posture_classes array."))
        posture_classes = []

    if blockers or not isinstance(team, dict) or not isinstance(project, dict) or not isinstance(log_surfaces, dict) or not isinstance(observability_surfaces, dict):
        return None, blockers, warnings

    team_id = _ensure_string(team, "id")
    team_name = _ensure_string(team, "name")
    if team_id is None:
        blockers.append(_finding("team_id_missing", "Team object must include string id."))
    if team_name is None:
        blockers.append(_finding("team_name_missing", "Team object must include string name."))
    if team_id is not None and team_id != EXPECTED_TEAM_ID:
        blockers.append(_finding("unexpected_team_id", "Team id does not match the governed Vercel team.", expected=EXPECTED_TEAM_ID, actual=team_id))
    if team_name is not None and team_name != EXPECTED_TEAM_NAME:
        blockers.append(
            _finding("unexpected_team_name", "Team name does not match the governed Vercel team.", expected=EXPECTED_TEAM_NAME, actual=team_name)
        )

    project_id = _ensure_string(project, "id")
    project_name = _ensure_string(project, "name")
    repo_logical_id = _ensure_string(project, "repo_logical_id")
    inventory_scope = _ensure_string(project, "inventory_scope")
    framework = project.get("framework")
    node_version = project.get("node_version")
    domains = project.get("domains")

    if project_id is None:
        blockers.append(_finding("project_id_missing", "Project object must include string id."))
    if project_name is None:
        blockers.append(_finding("project_name_missing", "Project object must include string name."))
    if repo_logical_id is None:
        blockers.append(_finding("repo_logical_id_missing", "Project object must include string repo_logical_id."))
    if inventory_scope is None:
        blockers.append(_finding("inventory_scope_missing", "Project object must include string inventory_scope."))
    elif inventory_scope not in ALLOWED_INVENTORY_SCOPES:
        blockers.append(
            _finding(
                "invalid_inventory_scope",
                "Project inventory_scope is outside the admitted bounded vocabulary.",
                inventory_scope=inventory_scope,
            )
        )
    if framework is not None and not isinstance(framework, str):
        blockers.append(_finding("framework_malformed", "Project framework must be a string or null."))
    if node_version is not None and not isinstance(node_version, str):
        blockers.append(_finding("node_version_malformed", "Project node_version must be a string or null."))
    if not isinstance(domains, list) or any(not isinstance(item, str) for item in domains):
        blockers.append(_finding("domains_malformed", "Project domains must be an array of strings."))
        domains = []

    expected_project = GOVERNED_PROJECTS.get(project_id or "")
    if expected_project is None and project_id is not None:
        blockers.append(_finding("unknown_project_id", "Project id is not part of the governed Vercel project set.", project_id=project_id))
    if expected_project is not None:
        if project_name != expected_project["project_name"]:
            blockers.append(
                _finding(
                    "project_name_mismatch",
                    "Project name does not match the governed Vercel project mapping.",
                    expected=expected_project["project_name"],
                    actual=project_name,
                )
            )
        if repo_logical_id != expected_project["repo_logical_id"]:
            blockers.append(
                _finding(
                    "repo_logical_id_mismatch",
                    "repo_logical_id does not match the governed Vercel project mapping.",
                    expected=expected_project["repo_logical_id"],
                    actual=repo_logical_id,
                )
            )

    normalized_posture_classes: list[str] = []
    for item in posture_classes:
        if not isinstance(item, str):
            blockers.append(_finding("posture_class_malformed", "Each posture class must be a string."))
            continue
        if item not in ALLOWED_POSTURE_CLASSES:
            blockers.append(
                _finding(
                    "invalid_posture_class",
                    "Posture class is outside the admitted bounded vocabulary.",
                    posture_class=item,
                )
            )
            continue
        normalized_posture_classes.append(item)

    if blockers:
        return None, blockers, warnings

    validated_deployments: list[dict[str, Any]] = []
    for deployment in deployments:
        if not isinstance(deployment, dict):
            blockers.append(_finding("deployment_malformed", "Each deployment entry must be an object.", project_id=project_id))
            continue
        if not isinstance(deployment.get("id"), str):
            blockers.append(_finding("deployment_id_missing", "Each deployment entry must include string id.", project_id=project_id))
        if not isinstance(deployment.get("created_at"), str):
            blockers.append(_finding("deployment_created_at_missing", "Each deployment entry must include string created_at.", project_id=project_id))
        if not isinstance(deployment.get("state"), str):
            blockers.append(_finding("deployment_state_missing", "Each deployment entry must include string state.", project_id=project_id))
        if not isinstance(deployment.get("target"), str):
            blockers.append(_finding("deployment_target_missing", "Each deployment entry must include string target.", project_id=project_id))
        if not isinstance(deployment.get("commit_sha"), str):
            blockers.append(_finding("deployment_commit_sha_missing", "Each deployment entry must include string commit_sha.", project_id=project_id))
        validated_deployments.append(deployment)

    if blockers:
        return None, blockers, warnings

    build_logs_queryable = _ensure_bool(log_surfaces, "build_logs_queryable")
    runtime_logs_queryable = _ensure_bool(log_surfaces, "runtime_logs_queryable")
    runtime_errors_queryable = _ensure_bool(log_surfaces, "runtime_errors_queryable")
    if build_logs_queryable is None:
        blockers.append(_finding("build_logs_queryable_missing", "log_surfaces must include boolean build_logs_queryable.", project_id=project_id))
    if runtime_logs_queryable is None:
        blockers.append(_finding("runtime_logs_queryable_missing", "log_surfaces must include boolean runtime_logs_queryable.", project_id=project_id))
    if runtime_errors_queryable is None:
        blockers.append(_finding("runtime_errors_queryable_missing", "log_surfaces must include boolean runtime_errors_queryable.", project_id=project_id))

    normalized_runtime_errors: list[OrderedDict[str, Any]] = []
    for item in runtime_errors:
        if not isinstance(item, dict):
            blockers.append(_finding("runtime_error_malformed", "Each runtime error observation must be an object.", project_id=project_id))
            continue
        error_group = _ensure_string(item, "error_group")
        route = _ensure_string(item, "route")
        first_seen = _ensure_string(item, "first_seen")
        last_seen = _ensure_string(item, "last_seen")
        last_deployment_id = _ensure_string(item, "last_deployment_id")
        count = item.get("count")
        if error_group is None:
            blockers.append(_finding("runtime_error_group_missing", "Runtime error observations must include string error_group.", project_id=project_id))
        if route is None:
            blockers.append(_finding("runtime_error_route_missing", "Runtime error observations must include string route.", project_id=project_id))
        if first_seen is None:
            blockers.append(_finding("runtime_error_first_seen_missing", "Runtime error observations must include string first_seen.", project_id=project_id))
        if last_seen is None:
            blockers.append(_finding("runtime_error_last_seen_missing", "Runtime error observations must include string last_seen.", project_id=project_id))
        if last_deployment_id is None:
            blockers.append(
                _finding("runtime_error_last_deployment_missing", "Runtime error observations must include string last_deployment_id.", project_id=project_id)
            )
        if not isinstance(count, int):
            blockers.append(_finding("runtime_error_count_missing", "Runtime error observations must include integer count.", project_id=project_id))
        if error_group is None or route is None or first_seen is None or last_seen is None or last_deployment_id is None or not isinstance(count, int):
            continue
        normalized_runtime_errors.append(
            OrderedDict(
                [
                    ("error_group", error_group),
                    ("count", count),
                    ("route", route),
                    ("first_seen", first_seen),
                    ("last_seen", last_seen),
                    ("last_deployment_id", last_deployment_id),
                ]
            )
        )

    normalized_observability: OrderedDict[str, str] = OrderedDict()
    for key in ("web_analytics", "speed_insights", "drains", "alerts", "env_name_only"):
        value = _ensure_string(observability_surfaces, key)
        if value is None or value not in ALLOWED_OBSERVABILITY_STATES:
            blockers.append(
                _finding(
                    "invalid_observability_surface_state",
                    "Observability surface state must use the admitted bounded vocabulary.",
                    project_id=project_id,
                    surface=key,
                    actual=value,
                )
            )
            continue
        normalized_observability[key] = value

    if blockers:
        return None, blockers, warnings

    production_deployments = [item for item in validated_deployments if item.get("target") == "production"]
    latest_production = max(production_deployments, key=_deployment_sort_key) if production_deployments else {}
    if not production_deployments:
        warnings.append(
            OrderedDict(
                [
                    ("code", "no_production_deployments"),
                    ("severity", "warning"),
                    ("message", "Capture contained no production deployments."),
                    ("details", {"project_id": project_id}),
                ]
            )
        )

    summary = OrderedDict(
        [
            ("project_name", project_name),
            ("project_id", project_id),
            ("repo_logical_id", repo_logical_id),
            ("inventory_scope", inventory_scope),
            ("framework", framework),
            ("node_version", node_version),
            ("domain_count", len(domains)),
            ("domains", sorted(domains)),
            ("latest_production_deployment_id", latest_production.get("id") if production_deployments else None),
            ("latest_production_deployment_created_at", latest_production.get("created_at") if production_deployments else None),
            ("latest_production_commit_sha", latest_production.get("commit_sha") if production_deployments else None),
            ("build_logs_queryable", build_logs_queryable),
            ("runtime_logs_queryable", runtime_logs_queryable),
            ("runtime_errors_queryable", runtime_errors_queryable),
            ("runtime_error_group_count", len(normalized_runtime_errors)),
            ("runtime_error_observations", normalized_runtime_errors),
        ]
    )

    team_summary = OrderedDict([("id", team_id), ("name", team_name)])
    team_slug = _ensure_string(team, "slug")
    if team_slug is not None:
        team_summary["slug"] = team_slug

    payload = OrderedDict(
        [
            ("team", team_summary),
            ("posture_classes", sorted(set(normalized_posture_classes))),
            ("project", summary),
        ]
    )
    return payload, blockers, warnings


def build_report(*, root: Path, inputs: list[str]) -> OrderedDict[str, Any]:
    texts, blockers = _ensure_required_files(root)
    _validate_contract_texts(texts, blockers)

    warnings: list[OrderedDict[str, Any]] = []
    if not inputs:
        blockers.append(_finding("input_required", "At least one --input tmp/**.json capture path is required."))

    projects_by_id: dict[str, OrderedDict[str, Any]] = {}
    captured_team: OrderedDict[str, Any] | None = None
    posture_classes_union: set[str] = set()

    for input_path in inputs:
        resolved, path_error = validate_runtime_json_path(root=root, relative_path=input_path)
        if path_error is not None:
            blockers.append(path_error)
            continue
        if resolved is None:
            continue
        payload = _load_json(resolved)
        if payload is None:
            blockers.append(_finding("input_json_missing_or_malformed", "Input capture JSON is missing or malformed.", path=input_path))
            continue
        summary, capture_blockers, capture_warnings = _validate_project_wrapper(wrapper=payload)
        blockers.extend(capture_blockers)
        warnings.extend(capture_warnings)
        if summary is None:
            continue
        team = summary["team"]
        if captured_team is None:
            captured_team = team
        elif team != captured_team:
            blockers.append(
                _finding(
                    "inconsistent_team_identity",
                    "A single run may not include wrappers for inconsistent team identity.",
                    expected=captured_team,
                    actual=team,
                )
            )
            continue

        project = summary["project"]
        project_id = str(project["project_id"])
        if project_id in projects_by_id:
            blockers.append(
                _finding(
                    "duplicate_project_capture",
                    "A single run may not include duplicate captures for the same project_id.",
                    project_id=project_id,
                )
            )
            continue
        projects_by_id[project_id] = project
        for posture_class in summary["posture_classes"]:
            posture_classes_union.add(str(posture_class))

    captured_projects: list[OrderedDict[str, Any]] = []
    missing_projects: list[OrderedDict[str, Any]] = []
    for project_id, meta in GOVERNED_PROJECTS.items():
        summary = projects_by_id.get(project_id)
        if summary is not None:
            captured_projects.append(summary)
        else:
            missing_projects.append(
                OrderedDict(
                    [
                        ("project_name", meta["project_name"]),
                        ("project_id", project_id),
                        ("repo_logical_id", meta["repo_logical_id"]),
                        ("detail", "no admitted Vercel project inventory capture was supplied for this governed project"),
                    ]
                )
            )
    if missing_projects:
        warnings.append(
            OrderedDict(
                [
                    ("code", "partial_capture_coverage"),
                    ("severity", "warning"),
                    ("message", "One or more governed Vercel projects still lack admitted inventory capture."),
                    ("details", {"missing_project_ids": [item["project_id"] for item in missing_projects]}),
                ]
            )
        )

    status = STATUS_BLOCKER if blockers else STATUS_OK
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", not blockers),
            (
                "basis_receipts",
                [
                    AUDIT_RECEIPT,
                    CONTRACT_RECEIPT,
                    CURRENT_STATE,
                    RECEIPT_INDEX,
                    RESTART_GUIDE,
                    STACK_REPO_INVENTORY,
                ],
            ),
            ("input_count", len(inputs)),
            ("team", captured_team),
            ("posture_classes", sorted(posture_classes_union)),
            ("captured_project_count", len(captured_projects)),
            ("projects", captured_projects),
            ("missing_projects", missing_projects),
            ("blockers", blockers),
            ("warnings", warnings),
        ]
    )


def report_exit_code(*, status: str) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Inputs: {report.get('input_count')}",
            f"Captured projects: {report.get('captured_project_count')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Vercel project inventory validator for ATLAS root governance.")
    parser.add_argument("--input", action="append", default=[], help="Root-relative tmp/**.json Vercel project inventory wrapper input.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, inputs=list(args.input))
        if args.output:
            resolved_output, output_error = validate_runtime_json_path(root=root, relative_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["safe_to_use"] = False
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR))
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("safe_to_use", False),
                ("basis_receipts", [AUDIT_RECEIPT, CONTRACT_RECEIPT, CURRENT_STATE, RECEIPT_INDEX, RESTART_GUIDE, STACK_REPO_INVENTORY]),
                ("input_count", len(getattr(args, "input", []) or [])),
                ("team", None),
                ("posture_classes", []),
                ("captured_project_count", 0),
                ("projects", []),
                ("missing_projects", []),
                ("blockers", [_finding("internal_error", "Vercel project inventory helper failed before summary output.", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
