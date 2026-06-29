from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_repo_registry, load_stack_config, normalize_slashes
from ops.atlas.continuity import (
    build_continuity_status_slices,
    build_initiative_continuity_manifest_health,
    build_open_marker_restart_index,
)
from ops.atlas.marker_knockout_selector import build_campaign
from ops.stack.export_repo_inventory import build_repo_inventory
from ops.stack.generate_lockfile import (
    build_canonical_lockfile_artifacts,
    default_lockfile_path,
    describe_lock_payload_drift,
    git_output,
    git_status_lines,
    load_lockfile,
    parse_porcelain_path,
)

SCHEMA_VERSION = "atlas.ai_work_session_preflight.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_drift"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
STATUSES = {STATUS_OK, STATUS_ADVISORY, STATUS_BLOCKER, STATUS_INTERNAL_ERROR}
SCOPES = {"root", "owner", "platform", "research"}
PROTECTED_OUTPUT_PREFIXES = {
    "archive",
    "repos",
    "runtime",
    "secrets",
    ".playwright-mcp",
    ".vercel",
}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _git_stdout(repo_root: Path, *args: str) -> tuple[int, str]:
    code, stdout = git_output(repo_root, *args)
    return code, stdout.strip()


def _status_paths(repo_root: Path) -> list[str]:
    paths: list[str] = []
    for line in git_status_lines(repo_root):
        path = parse_porcelain_path(line)
        if path:
            paths.append(path)
    return paths


def _protected_output_path(relative_path: str) -> bool:
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
    if _protected_output_path(relative_path):
        return None, {
            "code": "protected_output_path",
            "message": "Output path targets a protected surface.",
            "path": relative_path,
        }
    return (root / candidate).resolve(), None


def collect_branch_state(root: Path) -> dict[str, Any]:
    branch_code, branch = _git_stdout(root, "branch", "--show-current")
    head_code, head = _git_stdout(root, "rev-parse", "HEAD")
    dirty_paths = _status_paths(root)
    remote_tracking = f"origin/{branch}" if branch_code == 0 and branch else None
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
    return {
        "branch": branch if branch_code == 0 and branch else None,
        "head": head if head_code == 0 and head else None,
        "remote_tracking": remote_tracking,
        "parity": {
            "status": parity_status,
            "behind": behind,
            "ahead": ahead,
        },
        "dirty_paths": dirty_paths,
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
    return {
        "status": STATUS_OK,
        "active_lane": payload.get("active_lane"),
        "active_lane_is_held": bool(payload.get("active_lane_is_held")),
        "operator_action": payload.get("operator_action"),
        "current_packet": payload.get("selected_current_packet"),
        "next_packet": payload.get("next_after_current_packet"),
        "current_basis_ref": payload.get("selected_current_packet_basis_ref"),
        "next_basis_ref": payload.get("next_after_current_packet_basis_ref"),
    }


def collect_continuity(root: Path) -> dict[str, Any]:
    _, slices = build_continuity_status_slices(root=root)
    manifest_health = build_initiative_continuity_manifest_health(root=root)
    restart_index = build_open_marker_restart_index(root=root)
    coverage = slices.get("continuity_coverage", {}) if isinstance(slices, dict) else {}
    return {
        "status": STATUS_OK,
        "manifest_health": {
            "status": manifest_health.get("status"),
            "ok_count": manifest_health.get("ok_count"),
            "warning_count": manifest_health.get("warning_count"),
            "error_count": manifest_health.get("error_count"),
        },
        "restart_index": {
            "status": restart_index.get("status"),
            "eligible_open_marker_count": restart_index.get("eligible_open_marker_count"),
            "restart_ready_count": restart_index.get("restart_ready_count"),
            "restart_ready_percent": restart_index.get("restart_ready_percent"),
            "items": restart_index.get("items", []),
        },
        "coverage": {
            "status": coverage.get("status"),
            "pending_review_count": coverage.get("pending_review_count"),
            "initiative_manifest_status": coverage.get("initiative_manifest_status"),
            "open_marker_restart_index_status": coverage.get("open_marker_restart_index_status"),
        },
    }


def collect_stack_state(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_stack_config(root / "stack.yaml")
    lockfile_path = default_lockfile_path(config, root)
    live_lock = build_canonical_lockfile_artifacts(config=config, root=root)
    locked_payload = load_lockfile(lockfile_path)
    lock_drift = describe_lock_payload_drift(locked_payload, live_lock["payload"])
    live_inventory = build_repo_inventory(root=root, config=config, lock_payload=locked_payload)
    published_inventory_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
    published_inventory = _read_json(published_inventory_path)
    published_digest = (
        str(published_inventory.get("content_digest"))
        if isinstance(published_inventory, dict) and published_inventory.get("content_digest")
        else None
    )
    live_digest = str(live_inventory.get("content_digest") or "")
    inventory_matches_live = published_digest == live_digest if published_digest else False
    projection_status = STATUS_OK
    if lock_drift.get("has_drift") or not inventory_matches_live:
        projection_status = STATUS_ADVISORY
    stack_inventory = {
        "status": STATUS_OK,
        "published_ref": atlas_relative(published_inventory_path, root=root),
        "published_digest": published_digest,
        "live_digest": live_digest,
        "repo_count": live_inventory.get("repo_count"),
        "dirty_repo_count": live_inventory.get("dirty_repo_count"),
        "release_eligible_count": live_inventory.get("release_eligible_count"),
    }
    projection_freshness = {
        "status": projection_status,
        "lockfile_matches_live_working_set": not bool(lock_drift.get("has_drift")),
        "lockfile_drift": {
            "metadata_fields": lock_drift.get("metadata_fields", []),
            "components": lock_drift.get("components", {}),
            "excluded_surfaces": lock_drift.get("excluded_surfaces", {}),
        },
        "inventory_matches_live_working_set": inventory_matches_live,
        "published_inventory_ref": atlas_relative(published_inventory_path, root=root),
    }
    return stack_inventory, projection_freshness


def collect_qa_release_readiness(root: Path) -> dict[str, Any]:
    secret_path = root / "runtime" / "atlas" / "qa" / "github-secret-readiness.latest.json"
    payload = _read_json(secret_path)
    if payload is None:
        return {
            "status": "unavailable",
            "source_ref": atlas_relative(secret_path, root=root),
            "missing_required_secret_names": [],
        }
    return {
        "status": payload.get("status"),
        "source_ref": atlas_relative(secret_path, root=root),
        "available_secret_count": payload.get("available_secret_count"),
        "missing_required_secret_names": payload.get("missing_required_secret_names", []),
    }


def collect_playbook(root: Path, stack_inventory: dict[str, Any]) -> dict[str, Any]:
    inventory = _read_json(root / "docs" / "registry" / "STACK-REPO-INVENTORY.json")
    repos = inventory.get("repos", []) if isinstance(inventory, dict) else []
    playbook_repo = next(
        (
            item for item in repos
            if isinstance(item, dict) and str(item.get("logical_id", "")).strip() == "playbook"
        ),
        None,
    )
    return {
        "status": STATUS_OK,
        "repo_present": playbook_repo is not None,
        "branch": playbook_repo.get("branch") if isinstance(playbook_repo, dict) else None,
        "dirty": playbook_repo.get("dirty") if isinstance(playbook_repo, dict) else None,
        "adoption_signal": "playbook_repo_visible" if playbook_repo else "playbook_repo_not_visible",
        "stack_inventory_digest": stack_inventory.get("live_digest"),
    }


def collect_platform(root: Path, scope: str, qa_release_readiness: dict[str, Any]) -> dict[str, Any]:
    if scope != "platform":
        return {
            "status": "not_requested",
            "requested": False,
        }
    return {
        "status": qa_release_readiness.get("status", "unavailable"),
        "requested": True,
        "source_ref": qa_release_readiness.get("source_ref"),
        "missing_required_secret_names": qa_release_readiness.get("missing_required_secret_names", []),
    }


def collect_protected_surfaces(root: Path) -> dict[str, Any]:
    entries = []
    for relative_path in ["archive", ".playwright-mcp", ".vercel", "secrets", "repos"]:
        target = root / relative_path
        entries.append(
            {
                "path": normalize_slashes(relative_path),
                "present": target.exists(),
            }
        )
    env_files = sorted(path.name for path in root.glob(".env*") if path.is_file())
    return {
        "status": STATUS_OK,
        "entries": entries,
        "env_files": env_files,
    }


def resolve_owner_scope(root: Path, owner: str | None) -> dict[str, Any]:
    if not owner:
        return {
            "status": STATUS_BLOCKER,
            "owner": None,
            "repo_path": None,
            "branch": None,
            "head": None,
            "dirty_paths": [],
        }
    registry = load_repo_registry(root=root)
    entry = registry.get(owner)
    if entry is None:
        return {
            "status": STATUS_BLOCKER,
            "owner": owner,
            "repo_path": None,
            "branch": None,
            "head": None,
            "dirty_paths": [],
        }
    branch_code, branch = _git_stdout(entry.root, "branch", "--show-current")
    head_code, head = _git_stdout(entry.root, "rev-parse", "HEAD")
    return {
        "status": STATUS_OK,
        "owner": owner,
        "repo_path": atlas_relative(entry.root, root=root),
        "branch": branch if branch_code == 0 and branch else None,
        "head": head if head_code == 0 and head else None,
        "dirty_paths": _status_paths(entry.root),
    }


def build_local_residue(
    *,
    branch_state: dict[str, Any],
    owner_scope: dict[str, Any] | None,
) -> dict[str, Any]:
    residue = {
        "status": STATUS_OK,
        "root_dirty_paths": branch_state.get("dirty_paths", []),
        "owner_dirty_paths": [],
    }
    if owner_scope:
        residue["owner_dirty_paths"] = owner_scope.get("dirty_paths", [])
    return residue


def _blocker(code: str, message: str, **details: Any) -> dict[str, Any]:
    payload = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return payload


def _warning(code: str, message: str, **details: Any) -> dict[str, Any]:
    payload = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return payload


def build_required_followups(
    *,
    markers: dict[str, Any],
    projection_freshness: dict[str, Any],
    qa_release_readiness: dict[str, Any],
    scope: str,
    owner_scope: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    followups: list[dict[str, Any]] = []
    next_packet = markers.get("next_packet")
    if isinstance(next_packet, str) and next_packet:
        followups.append(
            {
                "kind": "packet",
                "scope": scope,
                "action": "execute",
                "target": next_packet,
            }
        )
    if projection_freshness.get("status") == STATUS_ADVISORY:
        followups.append(
            {
                "kind": "projection_refresh",
                "scope": "root",
                "action": "reconcile_authoritative_and_projected_truth",
                "target": "stack.lock.yaml and published stack inventory",
            }
        )
    if qa_release_readiness.get("status") == "blocked":
        followups.append(
            {
                "kind": "qa_release_gate",
                "scope": "platform",
                "action": "supply_missing_github_actions_secrets",
                "target": qa_release_readiness.get("missing_required_secret_names", []),
            }
        )
    if owner_scope and owner_scope.get("owner") and owner_scope.get("dirty_paths"):
        followups.append(
            {
                "kind": "owner_repo",
                "scope": "owner",
                "action": "resolve_owner_repo_dirty_state",
                "target": owner_scope.get("owner"),
            }
        )
    if not followups:
        followups.append(
            {
                "kind": "hold",
                "scope": scope,
                "action": "no_immediate_followup",
                "target": "current root posture remains stable",
            }
        )
    return followups


def build_report(*, root: Path, scope: str, owner: str | None = None) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    branch_state = collect_branch_state(root)
    if not branch_state.get("branch") or not branch_state.get("head"):
        blockers.append(_blocker("branch_truth_unavailable", "Authoritative branch or HEAD truth is unavailable."))
    parity = branch_state.get("parity", {})
    if parity.get("status") == "unavailable":
        blockers.append(_blocker("parity_truth_unavailable", "Authoritative parity truth is unavailable."))

    validation = collect_validation(root)
    if not validation.get("available"):
        blockers.append(_blocker("validation_unavailable", "Required validation receipt is unavailable."))
    elif int(validation.get("critical", 0) or 0) > 0 or int(validation.get("error", 0) or 0) > 0:
        blockers.append(
            _blocker(
                "validation_blocking",
                "Validation has blocking findings.",
                critical=validation.get("critical"),
                error=validation.get("error"),
                report_ref=validation.get("report_ref"),
            )
        )

    markers = collect_markers(root)
    continuity = collect_continuity(root)
    restart_items = continuity.get("restart_index", {}).get("items", [])
    active_lane = markers.get("active_lane")
    if active_lane and not any(
        isinstance(item, dict) and str(item.get("marker") or "").strip() == str(active_lane)
        for item in restart_items
    ):
        blockers.append(
            _blocker(
                "contradictory_authoritative_inputs",
                "Active marker truth is missing from the restart-ready open-marker index.",
                active_lane=active_lane,
            )
        )

    stack_inventory, projection_freshness = collect_stack_state(root)
    if projection_freshness.get("status") == STATUS_ADVISORY:
        warnings.append(
            _warning(
                "projection_freshness_drift",
                "Projected stack truth differs from live authoritative state.",
                published_inventory_ref=projection_freshness.get("published_inventory_ref"),
            )
        )

    qa_release_readiness = collect_qa_release_readiness(root)
    if qa_release_readiness.get("status") == "blocked":
        warnings.append(
            _warning(
                "qa_release_gate_blocked",
                "Existing QA release-readiness blockers are still present.",
                source_ref=qa_release_readiness.get("source_ref"),
            )
        )

    playbook = collect_playbook(root, stack_inventory)
    platform = collect_platform(root, scope, qa_release_readiness)
    protected_surfaces = collect_protected_surfaces(root)

    owner_scope: dict[str, Any] | None = None
    if scope == "owner":
        owner_scope = resolve_owner_scope(root, owner)
        if owner_scope.get("status") != STATUS_OK:
            blockers.append(
                _blocker(
                    "owner_scope_unavailable",
                    "Owner scope requires a known owner repo.",
                    owner=owner,
                )
            )
    local_residue = build_local_residue(branch_state=branch_state, owner_scope=owner_scope)

    required_followups = build_required_followups(
        markers=markers,
        projection_freshness=projection_freshness,
        qa_release_readiness=qa_release_readiness,
        scope=scope,
        owner_scope=owner_scope,
    )

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "scope": scope,
        "root": normalize_slashes(str(root)),
        "branch": branch_state.get("branch"),
        "head": branch_state.get("head"),
        "remote_tracking": branch_state.get("remote_tracking"),
        "parity": parity,
        "validation": validation,
        "markers": markers,
        "continuity": continuity,
        "stack_inventory": stack_inventory,
        "projection_freshness": projection_freshness,
        "qa_release_readiness": qa_release_readiness,
        "playbook": playbook,
        "platform": platform,
        "protected_surfaces": protected_surfaces,
        "local_residue": local_residue,
        "required_followups": required_followups,
        "blockers": blockers,
        "warnings": warnings,
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
    lines = [
        f"Status: {report['status']}",
        f"Scope: {report['scope']}",
        f"Branch: {report.get('branch') or 'unknown'}",
        f"Head: {report.get('head') or 'unknown'}",
    ]
    parity = report.get("parity", {})
    lines.append(
        "Parity: "
        + f"{parity.get('status', 'unknown')} "
        + f"(behind={parity.get('behind')}, ahead={parity.get('ahead')})"
    )
    validation = report.get("validation", {})
    lines.append(
        "Validation: "
        + f"critical={validation.get('critical')} "
        + f"error={validation.get('error')} "
        + f"warning={validation.get('warning')} "
        + f"info={validation.get('info')}"
    )
    markers = report.get("markers", {})
    lines.append(f"Next packet: {markers.get('next_packet') or 'none'}")
    return "\n".join(lines)


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only ATLAS AI work-session preflight aggregator."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--scope", choices=sorted(SCOPES), default="root")
    parser.add_argument("--owner")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, scope=args.scope, owner=args.owner)
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_INTERNAL_ERROR,
            "scope": args.scope,
            "root": normalize_slashes(str(root)),
            "branch": None,
            "head": None,
            "remote_tracking": None,
            "parity": {"status": "unavailable", "behind": None, "ahead": None},
            "validation": {"available": False, "critical": 0, "error": 0, "warning": 0, "info": 0},
            "markers": {},
            "continuity": {},
            "stack_inventory": {},
            "projection_freshness": {},
            "qa_release_readiness": {},
            "playbook": {},
            "platform": {},
            "protected_surfaces": {},
            "local_residue": {},
            "required_followups": [],
            "blockers": [
                _blocker(
                    "internal_error",
                    "Preflight failed before completion.",
                    exception=str(exc),
                )
            ],
            "warnings": [],
        }
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
