from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.vercel_deployment_freshness_inventory.v1"
EXPORT_SCHEMA_VERSION = "atlas.vercel.observability.project_inventory_export.v1"
REPORT_SCHEMA_VERSION = "atlas.vercel_observability_project_inventory.v1"

STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

AUDIT_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md"
PROJECT_CONTRACT_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-CONTRACT-FREEZE-2026-07-09.md"
)
PROJECT_EXECUTION_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-READ-ONLY-PROJECT-INVENTORY-FIRST-OPERATOR-EXPORT-CAPTURE-EXECUTION-2026-07-09.md"
)
PROJECT_COVERAGE_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-PROJECT-INVENTORY-COVERAGE-RECONCILIATION-CONTRACT-FREEZE-2026-07-09.md"
)
CONTRACT_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-DEPLOYMENT-FRESHNESS-INVENTORY-CONTRACT-FREEZE-2026-07-09.md"
)
ADMISSION_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-DEPLOYMENT-FRESHNESS-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md"
)
PROMPT_PACK_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-DEPLOYMENT-FRESHNESS-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md"
)
READINESS_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-DEPLOYMENT-FRESHNESS-INVENTORY-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-09.md"
)
CURRENT_STATE = "docs/atlas-book/01-current-state.md"
RECEIPT_INDEX = "docs/atlas-book/05-receipt-index.md"
RESTART_GUIDE = "docs/atlas-book/12-restart-and-handoff-guide.md"
STACK_REPO_INVENTORY = "docs/registry/STACK-REPO-INVENTORY.json"

REQUIRED_TEXT_REFS = (
    AUDIT_RECEIPT,
    PROJECT_CONTRACT_RECEIPT,
    PROJECT_EXECUTION_RECEIPT,
    PROJECT_COVERAGE_RECEIPT,
    CONTRACT_RECEIPT,
    ADMISSION_RECEIPT,
    PROMPT_PACK_RECEIPT,
    READINESS_RECEIPT,
    CURRENT_STATE,
    RECEIPT_INDEX,
    RESTART_GUIDE,
)

GOVERNED_PROJECTS = OrderedDict(
    [
        (
            "prj_C2RSEa34OblHfhuEpVChRQQZSjuG",
            OrderedDict([("project_name", "fawxzzy-discordos"), ("repo_logical_id", "discordos")]),
        ),
        (
            "prj_rtlFVOMFAWCRoJ3SQjHloi89881K",
            OrderedDict([("project_name", "fawxzzy-fitness"), ("repo_logical_id", "fitness")]),
        ),
        (
            "prj_t3zothbtj9DExrh3FjMsH98hwwSZ",
            OrderedDict([("project_name", "fawxzzy-mazer"), ("repo_logical_id", "mazer")]),
        ),
        (
            "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV",
            OrderedDict([("project_name", "fawxzzy-trove"), ("repo_logical_id", "trove")]),
        ),
        (
            "prj_o37CPLlESB6Zybe8GB74BX3wrkpy",
            OrderedDict([("project_name", "fawxzzy-foundation"), ("repo_logical_id", "foundation")]),
        ),
    ]
)

PROJECT_NAME_TO_ID = {meta["project_name"]: project_id for project_id, meta in GOVERNED_PROJECTS.items()}
REQUIRED_INVENTORY_IDS = tuple(meta["repo_logical_id"] for meta in GOVERNED_PROJECTS.values())
FRESHNESS_BUCKETS = ("same_day", "age_1_to_7_days", "age_8_to_30_days", "age_over_30_days", "missing_production_timestamp")
NEXT_RECOMMENDED_PACKET = (
    "Vercel Platform Observability Governance deployment freshness inventory first-implementation worker-cluster reconciliation"
)
FORBIDDEN_KEYS = {
    "env",
    "env_value",
    "env_values",
    "token",
    "token_value",
    "token_values",
    "secret",
    "secret_value",
    "secret_values",
    "authorization",
    "authorization_header",
    "headers",
    "request_body",
}


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
        if project_id not in audit_text and meta["project_name"] not in audit_text:
            blockers.append(
                _finding(
                    "audit_project_missing",
                    "Vercel observability audit is missing an expected governed project reference.",
                    project_id=project_id,
                    project_name=meta["project_name"],
                )
            )
    coverage_text = texts.get(PROJECT_COVERAGE_RECEIPT, "")
    for needle in ("5/5", "deployment freshness", "fawxzzy-foundation", "fawxzzy-trove"):
        if needle not in coverage_text:
            blockers.append(_finding("coverage_reference_missing", "Project coverage receipt is missing a required deployment-freshness reference.", required_reference=needle))
    contract_text = texts.get(CONTRACT_RECEIPT, "")
    for needle in ("latest_production_deployment_created_at", "deployment_age_days", "age_over_30_days"):
        if needle not in contract_text:
            blockers.append(_finding("contract_reference_missing", "Deployment freshness contract is missing a required reference.", required_reference=needle))
    admission_text = texts.get(ADMISSION_RECEIPT, "")
    for needle in ("ops/atlas/vercel_deployment_freshness_inventory.py", "tests/test_atlas_vercel_deployment_freshness_inventory.py", "--strict"):
        if needle not in admission_text:
            blockers.append(_finding("admission_reference_missing", "Deployment freshness admission is missing a required worker reference.", required_reference=needle))
    prompt_text = texts.get(PROMPT_PACK_RECEIPT, "")
    for needle in (SCHEMA_VERSION, EXPORT_SCHEMA_VERSION, REPORT_SCHEMA_VERSION, "same_day", "age_over_30_days"):
        if needle not in prompt_text:
            blockers.append(_finding("prompt_pack_reference_missing", "Prompt-pack contract is missing a required helper reference.", required_reference=needle))
    readiness_text = texts.get(READINESS_RECEIPT, "")
    for needle in ("implementation_ready", "worker-cluster reconciliation", "ops/atlas/vercel_deployment_freshness_inventory.py"):
        if needle not in readiness_text:
            blockers.append(_finding("readiness_reference_missing", "Implementation-readiness closeout is missing a required routing reference.", required_reference=needle))


def _ensure_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _scan_forbidden_keys(value: Any, *, path: str = "") -> list[OrderedDict[str, Any]]:
    blockers: list[OrderedDict[str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str) and key in FORBIDDEN_KEYS:
                blockers.append(_finding("forbidden_sensitive_key", "Input includes a forbidden sensitive or out-of-scope field.", path=f"{path}.{key}".strip(".")))
            blockers.extend(_scan_forbidden_keys(nested, path=f"{path}.{key}".strip(".")))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            blockers.extend(_scan_forbidden_keys(nested, path=f"{path}[{index}]"))
    return blockers


def _utc_date_today() -> date:
    return datetime.now(UTC).date()


def _parse_iso_date(value: str) -> date | None:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


def _freshness_bucket(age_days: int) -> str:
    if age_days <= 0:
        return "same_day"
    if age_days <= 7:
        return "age_1_to_7_days"
    if age_days <= 30:
        return "age_8_to_30_days"
    return "age_over_30_days"


def _summary_from_export(payload: dict[str, Any], *, path: str) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers = _scan_forbidden_keys(payload, path=path)
    if payload.get("schema_version") != EXPORT_SCHEMA_VERSION:
        return [], [
            _finding(
                "unexpected_export_schema",
                "Input export does not use the admitted Vercel project inventory export schema.",
                path=path,
                expected=EXPORT_SCHEMA_VERSION,
                actual=payload.get("schema_version"),
            )
        ]
    project = payload.get("project")
    deployments = payload.get("deployments")
    if not isinstance(project, dict):
        blockers.append(_finding("project_missing", "Input export must include an object project field.", path=path))
        return [], blockers
    if not isinstance(deployments, list):
        blockers.append(_finding("deployments_missing", "Input export must include a deployments array.", path=path))
        return [], blockers

    project_id = _ensure_string(project, "id")
    project_name = _ensure_string(project, "name")
    repo_logical_id = _ensure_string(project, "repo_logical_id")
    if project_id is None or project_name is None or repo_logical_id is None:
        blockers.append(_finding("project_identity_missing", "Input export project object must include string id, name, and repo_logical_id fields.", path=path))
        return [], blockers

    expected = GOVERNED_PROJECTS.get(project_id)
    if expected is None:
        blockers.append(_finding("unknown_project_id", "Input export project_id is outside the governed Vercel set.", path=path, project_id=project_id))
        return [], blockers
    if project_name != expected["project_name"] or repo_logical_id != expected["repo_logical_id"]:
        blockers.append(
            _finding(
                "project_mapping_mismatch",
                "Input export project mapping does not match the governed Vercel mapping.",
                path=path,
                expected_project_name=expected["project_name"],
                actual_project_name=project_name,
                expected_repo_logical_id=expected["repo_logical_id"],
                actual_repo_logical_id=repo_logical_id,
            )
        )
        return [], blockers

    production = [item for item in deployments if isinstance(item, dict) and item.get("target") == "production"]
    latest: dict[str, Any] | None = None
    latest_key: tuple[str, str] = ("", "")
    for item in production:
        created_at = _ensure_string(item, "created_at")
        deployment_id = _ensure_string(item, "id")
        commit_sha = _ensure_string(item, "commit_sha")
        if created_at is None or deployment_id is None or commit_sha is None:
            blockers.append(_finding("production_deployment_fields_missing", "Production deployment entries must include string id, created_at, and commit_sha fields.", path=path, project_id=project_id))
            continue
        key = (created_at, deployment_id)
        if latest is None or key > latest_key:
            latest = item
            latest_key = key

    if not blockers and latest is None:
        blockers.append(_finding("missing_production_timestamp", "Input export does not contain an admitted production deployment timestamp.", path=path, project_id=project_id))

    if blockers or latest is None:
        return [], blockers

    return (
        [
            OrderedDict(
                [
                    ("project_name", project_name),
                    ("project_id", project_id),
                    ("repo_logical_id", repo_logical_id),
                    ("latest_production_deployment_id", str(latest["id"])),
                    ("latest_production_deployment_created_at", str(latest["created_at"])),
                    ("latest_production_commit_sha", str(latest["commit_sha"])),
                ]
            )
        ],
        blockers,
    )


def _summary_from_report(payload: dict[str, Any], *, path: str) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers = _scan_forbidden_keys(payload, path=path)
    if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
        return [], [
            _finding(
                "unexpected_report_schema",
                "Input report does not use the admitted Vercel project inventory helper schema.",
                path=path,
                expected=REPORT_SCHEMA_VERSION,
                actual=payload.get("schema_version"),
            )
        ]
    projects = payload.get("projects")
    if not isinstance(projects, list):
        return [], [_finding("projects_missing", "Input report must include a projects array.", path=path)]
    summaries: list[OrderedDict[str, Any]] = []
    for index, item in enumerate(projects):
        item_path = f"{path}.projects[{index}]"
        if not isinstance(item, dict):
            blockers.append(_finding("project_summary_malformed", "Each input report project summary must be an object.", path=item_path))
            continue
        project_name = _ensure_string(item, "project_name")
        project_id = _ensure_string(item, "project_id")
        repo_logical_id = _ensure_string(item, "repo_logical_id")
        deployment_id = _ensure_string(item, "latest_production_deployment_id")
        created_at = _ensure_string(item, "latest_production_deployment_created_at")
        commit_sha = _ensure_string(item, "latest_production_commit_sha")
        if None in (project_name, project_id, repo_logical_id, deployment_id, created_at, commit_sha):
            blockers.append(_finding("project_summary_fields_missing", "Each input report project summary must include governed production deployment freshness fields.", path=item_path))
            continue
        expected = GOVERNED_PROJECTS.get(project_id)
        if expected is None:
            blockers.append(_finding("unknown_project_id", "Input report project_id is outside the governed Vercel set.", path=item_path, project_id=project_id))
            continue
        if project_name != expected["project_name"] or repo_logical_id != expected["repo_logical_id"]:
            blockers.append(
                _finding(
                    "project_mapping_mismatch",
                    "Input report project mapping does not match the governed Vercel mapping.",
                    path=item_path,
                    expected_project_name=expected["project_name"],
                    actual_project_name=project_name,
                    expected_repo_logical_id=expected["repo_logical_id"],
                    actual_repo_logical_id=repo_logical_id,
                )
            )
            continue
        summaries.append(
            OrderedDict(
                [
                    ("project_name", project_name),
                    ("project_id", project_id),
                    ("repo_logical_id", repo_logical_id),
                    ("latest_production_deployment_id", deployment_id),
                    ("latest_production_deployment_created_at", created_at),
                    ("latest_production_commit_sha", commit_sha),
                ]
            )
        )
    return summaries, blockers


def _load_input_summaries(*, root: Path, relative_path: str) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    resolved, path_error = validate_runtime_json_path(root=root, relative_path=relative_path)
    if path_error is not None:
        return [], [path_error]
    if resolved is None:
        return [], []
    payload = _load_json(resolved)
    if payload is None:
        return [], [_finding("input_json_missing_or_malformed", "Input JSON is missing or malformed.", path=relative_path)]
    schema_version = payload.get("schema_version")
    if schema_version == EXPORT_SCHEMA_VERSION:
        return _summary_from_export(payload, path=relative_path)
    if schema_version == REPORT_SCHEMA_VERSION:
        return _summary_from_report(payload, path=relative_path)
    return [], [
        _finding(
            "unexpected_schema",
            "Input JSON does not use an admitted Vercel project-inventory evidence schema.",
            path=relative_path,
            actual=schema_version,
        )
    ]


def build_report(*, root: Path, inputs: list[str]) -> OrderedDict[str, Any]:
    texts, blockers = _ensure_required_files(root)
    _validate_contract_texts(texts, blockers)

    warnings: list[OrderedDict[str, Any]] = []
    if not inputs:
        blockers.append(_finding("input_required", "At least one --input tmp/**.json capture path is required."))

    by_project_id: dict[str, OrderedDict[str, Any]] = {}
    for input_path in inputs:
        summaries, input_blockers = _load_input_summaries(root=root, relative_path=input_path)
        blockers.extend(input_blockers)
        for summary in summaries:
            project_id = str(summary["project_id"])
            if project_id in by_project_id:
                blockers.append(_finding("duplicate_project_capture", "A single run may not include duplicate captures for the same project_id.", project_id=project_id))
                continue
            by_project_id[project_id] = summary

    as_of_date = _utc_date_today()
    projects: list[OrderedDict[str, Any]] = []
    missing_projects: list[OrderedDict[str, Any]] = []
    freshness_counts = OrderedDict((bucket, 0) for bucket in FRESHNESS_BUCKETS)

    for project_id, meta in GOVERNED_PROJECTS.items():
        summary = by_project_id.get(project_id)
        if summary is None:
            missing_projects.append(
                OrderedDict(
                    [
                        ("project_name", meta["project_name"]),
                        ("project_id", project_id),
                        ("repo_logical_id", meta["repo_logical_id"]),
                        ("detail", "no admitted deployment freshness evidence was supplied for this governed project"),
                    ]
                )
            )
            continue
        created_at = str(summary["latest_production_deployment_created_at"])
        deployment_date = _parse_iso_date(created_at)
        if deployment_date is None:
            blockers.append(_finding("malformed_production_timestamp", "Production deployment timestamp is malformed.", project_id=project_id, created_at=created_at))
            continue
        age_days = (as_of_date - deployment_date).days
        bucket = _freshness_bucket(age_days)
        freshness_counts[bucket] += 1
        projects.append(
            OrderedDict(
                [
                    ("project_name", str(summary["project_name"])),
                    ("project_id", project_id),
                    ("repo_logical_id", str(summary["repo_logical_id"])),
                    ("latest_production_deployment_id", str(summary["latest_production_deployment_id"])),
                    ("latest_production_deployment_created_at", created_at),
                    ("latest_production_commit_sha", str(summary["latest_production_commit_sha"])),
                    ("deployment_age_days", age_days),
                    ("freshness_bucket", bucket),
                ]
            )
        )

    if missing_projects:
        warnings.append(
            OrderedDict(
                [
                    ("code", "partial_capture_coverage"),
                    ("severity", "warning"),
                    ("message", "One or more governed Vercel projects still lack admitted deployment freshness evidence."),
                    ("details", {"missing_project_ids": [item["project_id"] for item in missing_projects]}),
                ]
            )
        )

    status = STATUS_BLOCKER if blockers else (STATUS_ADVISORY_GAP if warnings else STATUS_OK)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", not blockers),
            (
                "basis_receipts",
                [
                    AUDIT_RECEIPT,
                    PROJECT_CONTRACT_RECEIPT,
                    PROJECT_EXECUTION_RECEIPT,
                    PROJECT_COVERAGE_RECEIPT,
                    CONTRACT_RECEIPT,
                    ADMISSION_RECEIPT,
                    PROMPT_PACK_RECEIPT,
                    READINESS_RECEIPT,
                    CURRENT_STATE,
                    RECEIPT_INDEX,
                    RESTART_GUIDE,
                    STACK_REPO_INVENTORY,
                ],
            ),
            ("input_count", len(inputs)),
            ("captured_project_count", len(projects)),
            ("project_count", len(GOVERNED_PROJECTS)),
            ("as_of_date", as_of_date.isoformat()),
            ("freshness_counts", freshness_counts),
            ("projects", sorted(projects, key=lambda item: str(item["project_name"]))),
            ("missing_projects", missing_projects),
            ("warnings", warnings),
            ("blockers", blockers),
            ("next_recommended_packet", NEXT_RECOMMENDED_PACKET),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_GAP:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Inputs: {report.get('input_count')}",
            f"Captured projects: {report.get('captured_project_count')}/{report.get('project_count')}",
            f"As of date: {report.get('as_of_date')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Vercel deployment freshness inventory helper for ATLAS root governance.")
    parser.add_argument("--input", action="append", default=[], help="Root-relative tmp/**.json project-inventory evidence input.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for advisory-gap and blocker statuses.")
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
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=bool(args.strict))
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("safe_to_use", False),
                ("basis_receipts", [AUDIT_RECEIPT, PROJECT_CONTRACT_RECEIPT, PROJECT_EXECUTION_RECEIPT, PROJECT_COVERAGE_RECEIPT, CONTRACT_RECEIPT, ADMISSION_RECEIPT, PROMPT_PACK_RECEIPT, READINESS_RECEIPT, CURRENT_STATE, RECEIPT_INDEX, RESTART_GUIDE, STACK_REPO_INVENTORY]),
                ("input_count", len(getattr(args, "input", []) or [])),
                ("captured_project_count", 0),
                ("project_count", len(GOVERNED_PROJECTS)),
                ("as_of_date", _utc_date_today().isoformat()),
                ("freshness_counts", OrderedDict((bucket, 0) for bucket in FRESHNESS_BUCKETS)),
                ("projects", []),
                ("missing_projects", []),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Vercel deployment freshness helper failed before summary output.", exception=str(exc))]),
                ("next_recommended_packet", NEXT_RECOMMENDED_PACKET),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
