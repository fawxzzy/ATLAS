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

SCHEMA_VERSION = "atlas.supabase_backup_metadata_intake.v1"
EXPORT_SCHEMA_VERSION = "atlas.supabase.backup-management-export.v1"
EXPORT_SOURCE = "management_api.v1.projects.database.backups"

STATUS_OK = "ok"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

AUDIT_RECEIPT = "docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md"
POSTURE_CONTRACT = "docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md"
INTAKE_CONTRACT = "docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-METADATA-READ-ONLY-INTAKE-CONTRACT-FREEZE-2026-07-09.md"
CURRENT_STATE = "docs/atlas-book/01-current-state.md"
RECEIPT_INDEX = "docs/atlas-book/05-receipt-index.md"
RESTART_GUIDE = "docs/atlas-book/12-restart-and-handoff-guide.md"
STACK_REPO_INVENTORY = "docs/registry/STACK-REPO-INVENTORY.json"

REQUIRED_TEXT_REFS = (
    AUDIT_RECEIPT,
    POSTURE_CONTRACT,
    INTAKE_CONTRACT,
    CURRENT_STATE,
    RECEIPT_INDEX,
    RESTART_GUIDE,
)

REQUIRED_INVENTORY_IDS = ("fitness", "discordos", "mazer", "nat1-games")

CONFIRMED_PROJECTS = OrderedDict(
    [
        ("lpswxoyfniocuhljgzbc", "FawxzzyFitness"),
        ("nwexsktuuenfdegzrbut", "DiscordOS"),
        ("geknvnrmktchljnyddwp", "Mazer"),
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
            blockers.append(_finding("required_receipt_missing", "Required root-owned Supabase governance input is missing.", path=ref))
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
    for project_ref, project_name in CONFIRMED_PROJECTS.items():
        if project_ref not in audit_text or project_name not in audit_text:
            blockers.append(
                _finding(
                    "audit_project_missing",
                    "Supabase audit receipt does not contain the expected confirmed project entry.",
                    project_name=project_name,
                    project_ref=project_ref,
                )
            )
    contract_text = texts.get(INTAKE_CONTRACT, "")
    for needle in ("/v1/projects/{ref}/database/backups", EXPORT_SCHEMA_VERSION, "tmp/atlas/supabase-backup-metadata"):
        if needle not in contract_text:
            blockers.append(
                _finding(
                    "intake_contract_missing_required_reference",
                    "Supabase backup metadata intake contract is missing a required boundary reference.",
                    required_reference=needle,
                )
            )


def _ensure_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _ensure_bool(payload: dict[str, Any], key: str) -> bool | None:
    value = payload.get(key)
    return value if isinstance(value, bool) else None


def _backup_sort_key(item: dict[str, Any]) -> tuple[str, int]:
    inserted_at = item.get("inserted_at")
    backup_id = item.get("id")
    key = inserted_at if isinstance(inserted_at, str) else ""
    numeric = backup_id if isinstance(backup_id, int) else -1
    return (key, numeric)


def _project_summary(*, wrapper: dict[str, Any]) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []

    if wrapper.get("schema_version") != EXPORT_SCHEMA_VERSION:
        blockers.append(
            _finding(
                "unexpected_wrapper_schema",
                "Input wrapper does not use the admitted Supabase backup export schema.",
                expected=EXPORT_SCHEMA_VERSION,
                actual=wrapper.get("schema_version"),
            )
        )
        return None, blockers, warnings

    captured_at = _ensure_string(wrapper, "captured_at")
    project_ref = _ensure_string(wrapper, "project_ref")
    source = _ensure_string(wrapper, "source")
    payload = wrapper.get("payload")

    if captured_at is None:
        blockers.append(_finding("captured_at_missing", "Input wrapper must include a string captured_at field."))
    if project_ref is None:
        blockers.append(_finding("project_ref_missing", "Input wrapper must include a string project_ref field."))
    if source != EXPORT_SOURCE:
        blockers.append(
            _finding(
                "unexpected_source",
                "Input wrapper must use the admitted exported source value.",
                expected=EXPORT_SOURCE,
                actual=source,
            )
        )
    if not isinstance(payload, dict):
        blockers.append(_finding("payload_missing", "Input wrapper must include an object payload field."))

    if blockers or project_ref is None or not isinstance(payload, dict):
        return None, blockers, warnings

    if project_ref not in CONFIRMED_PROJECTS:
        blockers.append(
            _finding(
                "unknown_project_ref",
                "Input wrapper project_ref is not part of the currently governed confirmed project set.",
                project_ref=project_ref,
            )
        )
        return None, blockers, warnings

    region = _ensure_string(payload, "region")
    walg_enabled = _ensure_bool(payload, "walg_enabled")
    pitr_enabled = _ensure_bool(payload, "pitr_enabled")
    backups = payload.get("backups")
    physical_backup_data = payload.get("physical_backup_data")

    if region is None:
        blockers.append(_finding("region_missing", "Payload must include string region metadata.", project_ref=project_ref))
    if walg_enabled is None:
        blockers.append(_finding("walg_enabled_missing", "Payload must include boolean walg_enabled metadata.", project_ref=project_ref))
    if pitr_enabled is None:
        blockers.append(_finding("pitr_enabled_missing", "Payload must include boolean pitr_enabled metadata.", project_ref=project_ref))
    if not isinstance(backups, list):
        blockers.append(_finding("backups_missing", "Payload must include a backups array.", project_ref=project_ref))
        backups = []
    if physical_backup_data is not None and not isinstance(physical_backup_data, dict):
        blockers.append(
            _finding("physical_backup_data_malformed", "physical_backup_data must be an object when present.", project_ref=project_ref)
        )
        physical_backup_data = {}

    if blockers:
        return None, blockers, warnings

    validated_backups: list[dict[str, Any]] = []
    for item in backups:
        if not isinstance(item, dict):
            blockers.append(_finding("backup_item_malformed", "Each backup entry must be an object.", project_ref=project_ref))
            continue
        if not isinstance(item.get("id"), int):
            blockers.append(_finding("backup_id_missing", "Each backup entry must include integer id.", project_ref=project_ref))
        if not isinstance(item.get("is_physical_backup"), bool):
            blockers.append(
                _finding("backup_is_physical_missing", "Each backup entry must include boolean is_physical_backup.", project_ref=project_ref)
            )
        if not isinstance(item.get("status"), str):
            blockers.append(_finding("backup_status_missing", "Each backup entry must include string status.", project_ref=project_ref))
        if not isinstance(item.get("inserted_at"), str):
            blockers.append(
                _finding("backup_inserted_at_missing", "Each backup entry must include string inserted_at.", project_ref=project_ref)
            )
        validated_backups.append(item)

    if blockers:
        return None, blockers, warnings

    if not validated_backups:
        warnings.append(
            OrderedDict(
                [
                    ("code", "no_backup_rows"),
                    ("severity", "warning"),
                    ("message", "Capture contained no backup rows."),
                    ("details", {"project_ref": project_ref}),
                ]
            )
        )

    latest = max(validated_backups, key=_backup_sort_key) if validated_backups else {}
    physical = physical_backup_data if isinstance(physical_backup_data, dict) else {}

    summary = OrderedDict(
        [
            ("project_name", CONFIRMED_PROJECTS[project_ref]),
            ("project_ref", project_ref),
            ("source", EXPORT_SOURCE),
            ("captured_at", captured_at),
            ("region", region),
            ("walg_enabled", walg_enabled),
            ("pitr_enabled", pitr_enabled),
            ("backup_count", len(validated_backups)),
            ("latest_backup_id", latest.get("id") if validated_backups else None),
            ("latest_backup_status", latest.get("status") if validated_backups else None),
            ("latest_backup_inserted_at", latest.get("inserted_at") if validated_backups else None),
            ("latest_backup_is_physical", latest.get("is_physical_backup") if validated_backups else None),
            ("earliest_physical_backup_date_unix", physical.get("earliest_physical_backup_date_unix")),
            ("latest_physical_backup_date_unix", physical.get("latest_physical_backup_date_unix")),
        ]
    )
    return summary, blockers, warnings


def build_report(*, root: Path, inputs: list[str]) -> OrderedDict[str, Any]:
    texts, blockers = _ensure_required_files(root)
    _validate_contract_texts(texts, blockers)

    warnings: list[OrderedDict[str, Any]] = []
    if not inputs:
        blockers.append(_finding("input_required", "At least one --input tmp/**.json capture path is required."))

    projects_by_ref: dict[str, OrderedDict[str, Any]] = {}
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
        summary, capture_blockers, capture_warnings = _project_summary(wrapper=payload)
        blockers.extend(capture_blockers)
        warnings.extend(capture_warnings)
        if summary is None:
            continue
        project_ref = str(summary["project_ref"])
        if project_ref in projects_by_ref:
            blockers.append(
                _finding(
                    "duplicate_project_capture",
                    "A single run may not include duplicate captures for the same project_ref.",
                    project_ref=project_ref,
                )
            )
            continue
        projects_by_ref[project_ref] = summary

    captured_projects: list[OrderedDict[str, Any]] = []
    missing_projects: list[OrderedDict[str, Any]] = []
    for project_ref, project_name in CONFIRMED_PROJECTS.items():
        summary = projects_by_ref.get(project_ref)
        if summary is not None:
            captured_projects.append(summary)
        else:
            missing_projects.append(
                OrderedDict(
                    [
                        ("project_name", project_name),
                        ("project_ref", project_ref),
                        ("detail", "no admitted backup metadata capture was supplied for this confirmed project"),
                    ]
                )
            )
    if missing_projects:
        warnings.append(
            OrderedDict(
                [
                    ("code", "partial_capture_coverage"),
                    ("severity", "warning"),
                    ("message", "One or more confirmed projects still lack admitted backup metadata capture."),
                    ("details", {"missing_project_refs": [item["project_ref"] for item in missing_projects]}),
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
                    POSTURE_CONTRACT,
                    INTAKE_CONTRACT,
                    CURRENT_STATE,
                    RECEIPT_INDEX,
                    RESTART_GUIDE,
                    STACK_REPO_INVENTORY,
                ],
            ),
            ("input_count", len(inputs)),
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
    parser = argparse.ArgumentParser(description="Read-only Supabase backup metadata intake validator for ATLAS root governance.")
    parser.add_argument("--input", action="append", default=[], help="Root-relative tmp/**.json backup metadata wrapper input.")
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
                ("basis_receipts", [AUDIT_RECEIPT, POSTURE_CONTRACT, INTAKE_CONTRACT, CURRENT_STATE, RECEIPT_INDEX, RESTART_GUIDE, STACK_REPO_INVENTORY]),
                ("input_count", len(getattr(args, "input", []) or [])),
                ("captured_project_count", 0),
                ("projects", []),
                ("missing_projects", []),
                ("blockers", [_finding("internal_error", "Supabase backup metadata intake helper failed before summary output.", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
