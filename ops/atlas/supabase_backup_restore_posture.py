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

SCHEMA_VERSION = "atlas.supabase_backup_restore_posture.v1"

STATUS_OK = "ok"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

AUDIT_RECEIPT = "docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md"
CONTRACT_RECEIPT = "docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md"
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

REQUIRED_INVENTORY_IDS = ("fitness", "discordos", "mazer", "nat1-games")

CONFIRMED_PROJECTS = (
    OrderedDict(
        [
            ("project_name", "FawxzzyFitness"),
            ("project_ref", "lpswxoyfniocuhljgzbc"),
            (
                "posture_classes",
                [
                    "daily_backup_covered",
                    "daily_backup_unverified",
                    "restore_process_unverified",
                    "pitr_candidate",
                    "pitr_not_approved",
                    "manual_dump_plan_needed",
                    "storage_restore_gap",
                    "custom_role_password_gap",
                    "operator_decision_required",
                ],
            ),
            ("pitr_candidate", True),
            ("notes", ["mature app data plane with direct DB operational surfaces and no governed backup inventory proof yet"]),
        ]
    ),
    OrderedDict(
        [
            ("project_name", "DiscordOS"),
            ("project_ref", "nwexsktuuenfdegzrbut"),
            (
                "posture_classes",
                [
                    "daily_backup_covered",
                    "daily_backup_unverified",
                    "restore_process_unverified",
                    "pitr_candidate",
                    "pitr_not_approved",
                    "manual_dump_plan_needed",
                    "storage_restore_gap",
                    "custom_role_password_gap",
                    "operator_decision_required",
                ],
            ),
            ("pitr_candidate", True),
            ("notes", ["active workflow and Edge Function data plane with no governed backup inventory proof yet"]),
        ]
    ),
    OrderedDict(
        [
            ("project_name", "Mazer"),
            ("project_ref", "geknvnrmktchljnyddwp"),
            (
                "posture_classes",
                [
                    "daily_backup_covered",
                    "daily_backup_unverified",
                    "restore_process_unverified",
                    "pitr_not_approved",
                    "manual_dump_plan_needed",
                    "storage_restore_gap",
                    "custom_role_password_gap",
                    "operator_decision_required",
                ],
            ),
            ("pitr_candidate", False),
            ("notes", ["newer project surface with conservative backup posture and no governed inventory proof yet"]),
        ]
    ),
)

DEPENDENCY_ONLY_SURFACES = (
    OrderedDict(
        [
            ("surface_name", "Nat1-Games"),
            ("posture_classes", ["no_project_identity"]),
            ("notes", ["real supabase-js dependency exists, but no confirmed visible project identity is governed at ATLAS root yet"]),
        ]
    ),
)

REQUIRED_POSTURE_CLASSES = {
    "daily_backup_covered",
    "daily_backup_unverified",
    "restore_process_unverified",
    "pitr_candidate",
    "pitr_not_approved",
    "manual_dump_plan_needed",
    "storage_restore_gap",
    "custom_role_password_gap",
    "operator_decision_required",
    "no_project_identity",
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
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


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


def validate_output_path(*, root: Path, output_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return None, _finding("absolute_output_path", "Output path must be root-relative.", path=normalize_slashes(str(candidate)))
    normalized = _normal(candidate)
    if ".." in Path(normalized).parts:
        return None, _finding("parent_traversal_output_path", "Output path must not use parent traversal.", path=normalized)
    if _protected_path(normalized) or not normalized.startswith("tmp/") or not normalized.endswith(".json"):
        return None, _finding(
            "protected_output_path",
            "Output writes are admitted only to root-relative tmp/**.json.",
            path=normalized,
        )
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", path=normalized)
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


def _audit_project_present(audit_text: str, project_name: str, project_ref: str) -> bool:
    return project_name in audit_text and project_ref in audit_text


def _contract_classes_present(contract_text: str) -> list[str]:
    return sorted(posture for posture in REQUIRED_POSTURE_CLASSES if posture not in contract_text)


def _project_report(project: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("project_name", project["project_name"]),
            ("project_ref", project["project_ref"]),
            ("posture_classes", list(project["posture_classes"])),
            ("pitr_candidate", bool(project["pitr_candidate"])),
            ("restore_readiness", "restore_process_unverified"),
            ("backup_inventory_status", "daily_backup_unverified"),
            ("storage_restore_gap", True),
            ("custom_role_password_gap", True),
            ("notes", list(project["notes"])),
        ]
    )


def _missing_evidence() -> list[OrderedDict[str, Any]]:
    items: list[OrderedDict[str, Any]] = []
    for project in CONFIRMED_PROJECTS:
        project_name = str(project["project_name"])
        items.extend(
            [
                OrderedDict(
                    [
                        ("project_name", project_name),
                        ("code", "backup_inventory_metadata_missing"),
                        ("detail", "project-specific backup timestamps or metadata are not yet recorded at ATLAS root"),
                    ]
                ),
                OrderedDict(
                    [
                        ("project_name", project_name),
                        ("code", "restore_dependency_checklist_missing"),
                        ("detail", "no governed restore dependency checklist or downtime estimate is recorded yet"),
                    ]
                ),
                OrderedDict(
                    [
                        ("project_name", project_name),
                        ("code", "custom_role_inventory_missing"),
                        ("detail", "custom-role usage and password-reset requirements are not yet inventoried"),
                    ]
                ),
            ]
        )
    return items


def _operator_decisions() -> list[OrderedDict[str, Any]]:
    return [
        OrderedDict(
            [
                ("project_name", "FawxzzyFitness"),
                ("code", "pitr_cost_and_compute_approval_required"),
                ("detail", "PITR remains a candidate only after explicit operator approval of add-on cost and compute requirements"),
            ]
        ),
        OrderedDict(
            [
                ("project_name", "DiscordOS"),
                ("code", "pitr_cost_and_compute_approval_required"),
                ("detail", "PITR remains a candidate only after explicit operator approval of add-on cost and compute requirements"),
            ]
        ),
        OrderedDict(
            [
                ("project_name", "all_confirmed_projects"),
                ("code", "restore_execution_approval_required"),
                ("detail", "any live restore or restore drill requires explicit operator approval before execution"),
            ]
        ),
    ]


def build_report(*, root: Path) -> OrderedDict[str, Any]:
    texts, blockers = _ensure_required_files(root)
    audit_text = texts.get(AUDIT_RECEIPT, "")
    contract_text = texts.get(CONTRACT_RECEIPT, "")

    for project in CONFIRMED_PROJECTS:
        name = str(project["project_name"])
        project_ref = str(project["project_ref"])
        if not _audit_project_present(audit_text, name, project_ref):
            blockers.append(
                _finding(
                    "audit_project_missing",
                    "Supabase audit receipt does not contain the expected confirmed project entry.",
                    project_name=name,
                    project_ref=project_ref,
                )
            )

    if "Nat1-Games" not in audit_text:
        blockers.append(
            _finding(
                "audit_dependency_surface_missing",
                "Supabase audit receipt does not record the Nat1-Games dependency-only surface.",
                surface_name="Nat1-Games",
            )
        )

    missing_classes = _contract_classes_present(contract_text)
    if missing_classes:
        blockers.append(
            _finding(
                "contract_posture_class_missing",
                "Supabase backup posture contract freeze is missing one or more required posture classes.",
                missing_classes=missing_classes,
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
            ("project_count", len(CONFIRMED_PROJECTS)),
            ("projects", [_project_report(project) for project in CONFIRMED_PROJECTS]),
            ("dependency_only_surfaces", [OrderedDict(surface) for surface in DEPENDENCY_ONLY_SURFACES]),
            ("missing_evidence", _missing_evidence()),
            ("operator_decisions_required", _operator_decisions()),
            ("blockers", blockers),
            ("warnings", []),
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
            f"Project count: {report.get('project_count')}",
            f"Dependency-only surfaces: {len(report.get('dependency_only_surfaces') or [])}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Supabase backup and restore posture classifier for ATLAS root governance.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root)
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
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
                ("project_count", 0),
                ("projects", []),
                ("dependency_only_surfaces", []),
                ("missing_evidence", []),
                ("operator_decisions_required", []),
                ("blockers", [_finding("internal_error", "Supabase backup restore posture helper failed before classification.", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
