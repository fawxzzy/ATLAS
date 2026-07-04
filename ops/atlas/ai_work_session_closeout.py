from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_repo_registry, normalize_slashes
from ops.atlas.marker_knockout_selector import build_campaign
from ops.stack.generate_lockfile import git_output

SCHEMA_VERSION = "atlas.ai_work_session_closeout.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_drift"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
SCOPES = {"owner", "platform", "research", "root"}
PROTECTED_OUTPUT_PREFIXES = {
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "runtime",
    "secrets",
}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _git_stdout(repo_root: Path, *args: str) -> tuple[int, str]:
    code, stdout = git_output(repo_root, *args)
    return code, stdout.strip()


def _git_lines(repo_root: Path, *args: str) -> list[str]:
    code, stdout = _git_stdout(repo_root, *args)
    if code != 0 or not stdout:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _protected_path(relative_path: str) -> bool:
    normalized = normalize_slashes(relative_path).strip("/")
    if not normalized:
        return True
    first = normalized.split("/", 1)[0]
    if first in PROTECTED_OUTPUT_PREFIXES:
        return True
    if first.startswith(".env"):
        return True
    filename = normalized.rsplit("/", 1)[-1]
    return filename.startswith(".env")


def validate_output_path(*, root: Path, output_path: str) -> tuple[Path | None, dict[str, Any] | None]:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return None, {
            "code": "absolute_output_path",
            "message": "Output path must be root-relative.",
            "path": normalize_slashes(str(candidate)),
        }
    relative_path = normalize_slashes(str(candidate))
    if _protected_path(relative_path):
        return None, {
            "code": "protected_output_path",
            "message": "Output path targets a protected surface.",
            "path": relative_path,
        }
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, {
            "code": "outside_root_output_path",
            "message": "Output path must stay inside the ATLAS root.",
            "path": relative_path,
        }
    return resolved, None


def _finding(code: str, message: str, **details: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return payload


def collect_branch_state(root: Path) -> dict[str, Any]:
    branch_code, branch = _git_stdout(root, "branch", "--show-current")
    head_code, head = _git_stdout(root, "rev-parse", "HEAD")
    branch_name = branch if branch_code == 0 and branch else None
    remote_tracking = f"origin/{branch_name}" if branch_name else None
    behind = ahead = None
    parity_status = "unavailable"
    if remote_tracking:
        parity_code, parity_text = _git_stdout(root, "rev-list", "--left-right", "--count", f"{remote_tracking}...HEAD")
        if parity_code == 0 and parity_text:
            parts = parity_text.split()
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                behind = int(parts[0])
                ahead = int(parts[1])
                parity_status = "clean" if behind == 0 and ahead == 0 else "drift"

    staged = _git_lines(root, "diff", "--cached", "--name-only")
    unstaged = _git_lines(root, "diff", "--name-only")
    untracked = _git_lines(root, "ls-files", "--others", "--exclude-standard")
    return {
        "branch": branch_name,
        "head": head if head_code == 0 and head else None,
        "remote_tracking": remote_tracking,
        "parity": {"status": parity_status, "behind": behind, "ahead": ahead},
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }


def collect_validation(root: Path) -> dict[str, Any]:
    report_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    payload = _read_json(report_path)
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    return {
        "report_ref": atlas_relative(report_path, root=root),
        "available": payload is not None,
        "critical": int(summary.get("critical", 0) or 0),
        "error": int(summary.get("error", 0) or 0),
        "warning": int(summary.get("warning", 0) or 0),
        "info": int(summary.get("info", 0) or 0),
    }


def collect_markers(root: Path) -> dict[str, Any]:
    payload = build_campaign(root=root)
    current_board = [
        {
            "marker": item.get("marker"),
            "percentage": item.get("percentage"),
            "category": item.get("category"),
        }
        for item in payload.get("open_markers", [])
        if isinstance(item, dict)
    ]
    return {
        "changed": [],
        "current_board": current_board,
        "active_lane": payload.get("active_lane"),
        "operator_action": payload.get("operator_action"),
        "current_packet": payload.get("selected_current_packet"),
        "next_packet": payload.get("next_after_current_packet"),
        "current_basis_ref": payload.get("selected_current_packet_basis_ref"),
        "next_basis_ref": payload.get("next_after_current_packet_basis_ref"),
    }


def collect_inventory(root: Path) -> dict[str, Any]:
    inventory_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
    payload = _read_json(inventory_path) or {}
    repositories = payload.get("repos")
    if not isinstance(repositories, list):
        repositories = payload.get("repositories", [])
    root_blocking_dirty = []
    advisory_dirty = []
    if isinstance(repositories, list):
        for item in repositories:
            if not isinstance(item, dict) or not item.get("dirty"):
                continue
            repo_id = item.get("logical_id")
            if item.get("dirty_blocks_root"):
                root_blocking_dirty.append(repo_id)
            else:
                advisory_dirty.append(repo_id)
    return {
        "source_ref": atlas_relative(inventory_path, root=root),
        "repo_count": payload.get("repo_count"),
        "dirty_repo_count": payload.get("dirty_repo_count"),
        "visible_dirty_repo_count": payload.get("visible_dirty_repo_count"),
        "advisory_dirty_repo_count": payload.get("advisory_dirty_repo_count"),
        "root_blocking_dirty_repos": root_blocking_dirty,
        "advisory_dirty_repos": advisory_dirty,
    }


def collect_protected_surfaces(changes: dict[str, Any]) -> dict[str, Any]:
    touched = []
    for key in ("staged", "unstaged", "untracked"):
        for relative_path in changes.get(key, []):
            if _protected_path(str(relative_path)):
                touched.append({"path": relative_path, "source": key})
    return {
        "touched": touched,
        "blocked": touched,
    }


def collect_owner_scope(root: Path, touched_repos: list[str]) -> dict[str, Any]:
    registry = load_repo_registry(root=root)
    repos = []
    for name in touched_repos:
        entry = registry.get(name)
        repos.append(
            {
                "name": name,
                "known": entry is not None,
                "repo_path": atlas_relative(entry.root, root=root) if entry else None,
            }
        )
    return {
        "mode": "read_only" if touched_repos else "none",
        "repos": repos,
    }


def build_next_actions(markers: dict[str, Any], blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if blockers:
        return [
            {
                "kind": "resolve_blocker",
                "target": blockers[0]["code"],
            }
        ]
    next_packet = markers.get("next_packet")
    if isinstance(next_packet, str) and next_packet:
        return [{"kind": "packet", "target": next_packet}]
    return [{"kind": "hold", "target": "no immediate next packet"}]


def build_report(
    *,
    root: Path,
    scope: str,
    session_label: str,
    touched_repos: list[str],
    commands_run: list[str],
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    branch_state = collect_branch_state(root)
    if not branch_state.get("branch") or not branch_state.get("head"):
        blockers.append(_finding("branch_truth_unavailable", "Branch or HEAD truth is unavailable."))
    if branch_state.get("parity", {}).get("status") == "unavailable":
        blockers.append(_finding("parity_truth_unavailable", "Remote parity truth is unavailable."))
    if branch_state.get("staged"):
        blockers.append(
            _finding(
                "staged_files_present",
                "Staged files block safe closeout unless they are committed or explicitly unstaged.",
                paths=branch_state.get("staged", []),
            )
        )
    if branch_state.get("unstaged") or branch_state.get("untracked"):
        warnings.append(
            _finding(
                "local_residue_present",
                "Local residue exists and must be reported before closeout.",
                unstaged=branch_state.get("unstaged", []),
                untracked=branch_state.get("untracked", []),
            )
        )

    validation = collect_validation(root)
    if not validation.get("available"):
        blockers.append(_finding("validation_unavailable", "Latest stack validation receipt is unavailable."))
    if int(validation.get("critical", 0) or 0) > 0 or int(validation.get("error", 0) or 0) > 0:
        blockers.append(
            _finding(
                "validation_blocking",
                "Validation has blocking findings.",
                critical=validation.get("critical"),
                error=validation.get("error"),
            )
        )

    markers = collect_markers(root)
    inventory = collect_inventory(root)
    if inventory.get("root_blocking_dirty_repos"):
        blockers.append(
            _finding(
                "root_blocking_dirty_repos",
                "Inventory reports root-blocking dirty repositories.",
                repos=inventory.get("root_blocking_dirty_repos"),
            )
        )
    elif inventory.get("advisory_dirty_repos"):
        warnings.append(
            _finding(
                "advisory_dirty_repos",
                "Inventory reports advisory dirty repositories.",
                repos=inventory.get("advisory_dirty_repos"),
            )
        )

    protected_surfaces = collect_protected_surfaces(branch_state)
    if protected_surfaces["blocked"]:
        blockers.append(
            _finding(
                "protected_surface_touched",
                "Protected surfaces are touched in local residue.",
                touched=protected_surfaces["blocked"],
            )
        )

    owner_scope = collect_owner_scope(root, touched_repos)
    platform_scope = "read_only" if scope == "platform" else "none"
    if scope == "owner" and not touched_repos:
        warnings.append(_finding("owner_scope_without_touched_repo", "Owner scope was requested without --touched-repo."))

    proof = {
        "commands_run": commands_run,
        "validation_summary": validation,
        "selector_next_packet": markers.get("next_packet"),
    }
    local_residue = {
        "staged": branch_state.get("staged", []),
        "unstaged": branch_state.get("unstaged", []),
        "untracked": branch_state.get("untracked", []),
    }

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY
    warning_codes = {str(item.get("code", "")) for item in warnings if isinstance(item, dict)}
    safe_to_close = not blockers and "local_residue_present" not in warning_codes
    next_actions = build_next_actions(markers, blockers)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "session_label": session_label,
        "scope": scope,
        "root": normalize_slashes(str(root)),
        "branch": branch_state.get("branch"),
        "head": branch_state.get("head"),
        "parity": branch_state.get("parity"),
        "repos_touched": touched_repos,
        "commands_run": commands_run,
        "validation": validation,
        "markers": markers,
        "proof": proof,
        "protected_surfaces": protected_surfaces,
        "local_residue": local_residue,
        "blockers": blockers,
        "warnings": warnings,
        "next_actions": next_actions,
        "safe_to_close": safe_to_close,
        "inventory": inventory,
        "owner_repo_scope": owner_scope,
        "platform_scope": platform_scope,
    }


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    parity = report.get("parity", {})
    validation = report.get("validation", {})
    lines = [
        f"Status: {report.get('status')}",
        f"Session: {report.get('session_label')}",
        f"Scope: {report.get('scope')}",
        f"Branch: {report.get('branch') or 'unknown'}",
        f"Head: {report.get('head') or 'unknown'}",
        f"Parity: {parity.get('status', 'unknown')} (behind={parity.get('behind')}, ahead={parity.get('ahead')})",
        (
            "Validation: "
            f"critical={validation.get('critical')} "
            f"error={validation.get('error')} "
            f"warning={validation.get('warning')} "
            f"info={validation.get('info')}"
        ),
        f"Safe to close: {str(report.get('safe_to_close')).lower()}",
    ]
    next_actions = report.get("next_actions", [])
    if next_actions:
        lines.append(f"Next action: {next_actions[0].get('target')}")
    return "\n".join(lines)


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only ATLAS AI work-session closeout aggregator.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--scope", choices=sorted(SCOPES), default="root")
    parser.add_argument("--session-label", default="unspecified")
    parser.add_argument("--touched-repo", action="append", default=[])
    parser.add_argument("--command-run", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(
            root=root,
            scope=args.scope,
            session_label=args.session_label,
            touched_repos=list(args.touched_repo or []),
            commands_run=list(args.command_run or []),
        )
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_close"] = False
                report["next_actions"] = build_next_actions(report.get("markers", {}), report["blockers"])
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_INTERNAL_ERROR,
            "session_label": getattr(args, "session_label", "unspecified"),
            "scope": getattr(args, "scope", "root"),
            "root": normalize_slashes(str(root)),
            "branch": None,
            "head": None,
            "parity": {"status": "unavailable", "behind": None, "ahead": None},
            "repos_touched": list(getattr(args, "touched_repo", []) or []),
            "commands_run": list(getattr(args, "command_run", []) or []),
            "validation": {"available": False, "critical": 0, "error": 0, "warning": 0, "info": 0},
            "markers": {},
            "proof": {},
            "protected_surfaces": {},
            "local_residue": {},
            "blockers": [_finding("internal_error", "Closeout failed before completion.", exception=str(exc))],
            "warnings": [],
            "next_actions": [{"kind": "resolve_blocker", "target": "internal_error"}],
            "safe_to_close": False,
            "inventory": {},
            "owner_repo_scope": {"mode": "none", "repos": []},
            "platform_scope": "none",
        }
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
