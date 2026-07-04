from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, parse_simple_yaml
from ops.atlas.marker_knockout_selector import build_campaign
from ops.cortex._artifacts import stable_json_digest
from ops.stack.generate_lockfile import git_output

SCHEMA_VERSION = "atlas.projection_freshness.v1"
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
PROJECTION_RECEIPT = (
    "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-ROOT-PLUS-OWNER-ADOPTION-"
    "EVIDENCE-INTAKE-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-04.md"
)
PROJECTION_PACKET = "No immediate AI Work Session Stability & Auto-Sync Loop same-lane packet; wait for at least two separately authorized owner-lane adoption proof receipts"
AI_WORK_SESSION_MARKER_PERCENT = 70
NO_IMMEDIATE_OPERATOR_ACTION = "no_immediate_root_packet"


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    payload = json.loads(text)
    return payload if isinstance(payload, dict) else None


def _read_yaml(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text)
        return payload if isinstance(payload, dict) else None
    except ModuleNotFoundError:
        return parse_simple_yaml(text)


def _sha256_text(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _sha256_file(path: Path) -> str | None:
    text = _read_text(path)
    return _sha256_text(text) if text is not None else None


def _git_stdout(repo_root: Path, *args: str) -> tuple[int, str]:
    code, stdout = git_output(repo_root, *args)
    return code, stdout.strip()


def _git_lines(repo_root: Path, *args: str) -> list[str]:
    code, stdout = _git_stdout(repo_root, *args)
    if code != 0 or not stdout:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _git_commit_relation(repo_root: Path, older_commit: str | None, newer_commit: str | None) -> str:
    if not older_commit or not newer_commit:
        return "unavailable"
    if older_commit == newer_commit:
        return "matches"
    code, _stdout = _git_stdout(repo_root, "merge-base", "--is-ancestor", older_commit, newer_commit)
    if code == 0:
        return "ancestor"
    return "diverged"


def _finding(code: str, message: str, *, severity: str = "advisory", **details: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    if details:
        payload["details"] = details
    return payload


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
        return None, _finding(
            "absolute_output_path",
            "Output path must be root-relative.",
            severity="blocker",
            path=normalize_slashes(str(candidate)),
        )
    relative_path = normalize_slashes(str(candidate))
    if _protected_path(relative_path):
        return None, _finding(
            "protected_output_path",
            "Output path targets a protected surface.",
            severity="blocker",
            path=relative_path,
        )
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding(
            "outside_root_output_path",
            "Output path must stay inside the ATLAS root.",
            severity="blocker",
            path=relative_path,
        )
    return resolved, None


def collect_branch_state(root: Path) -> OrderedDict[str, Any]:
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
    return OrderedDict(
        [
            ("branch", branch_name),
            ("head", head if head_code == 0 and head else None),
            ("parity", OrderedDict([("status", parity_status), ("behind", behind), ("ahead", ahead)])),
            ("staged", _git_lines(root, "diff", "--cached", "--name-only")),
            ("unstaged", _git_lines(root, "diff", "--name-only")),
            ("untracked", _git_lines(root, "ls-files", "--others", "--exclude-standard")),
        ]
    )


def collect_stack_lock(root: Path, inventory: dict[str, Any] | None) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    lock_path = root / "stack.lock.yaml"
    payload = _read_yaml(lock_path)
    digest = _sha256_file(lock_path)
    if payload is None:
        return OrderedDict([("source_ref", "stack.lock.yaml"), ("available", False), ("digest", None), ("component_count", 0), ("drift", [])]), [
            _finding("stack_lock_unavailable", "stack.lock.yaml could not be read.", severity="blocker")
        ]

    components = payload.get("components", {}) if isinstance(payload, dict) else {}
    component_count = len(components) if isinstance(components, dict) else 0
    inventory_repos = {}
    if inventory and isinstance(inventory.get("repos"), list):
        inventory_repos = {item.get("logical_id"): item for item in inventory["repos"] if isinstance(item, dict)}

    drift: list[dict[str, Any]] = []
    if isinstance(components, dict):
        for repo_id, component in components.items():
            if not isinstance(component, dict):
                continue
            inventory_repo = inventory_repos.get(repo_id)
            if not inventory_repo:
                drift.append({"repo": repo_id, "kind": "missing_from_inventory"})
                continue
            lock_commit = component.get("commit")
            inventory_commit = inventory_repo.get("current_commit")
            if lock_commit and inventory_commit and lock_commit != inventory_commit:
                drift.append(
                    {
                        "repo": repo_id,
                        "kind": "lock_inventory_commit_mismatch",
                        "lock": lock_commit,
                        "inventory": inventory_commit,
                    }
                )
    if drift:
        warnings.append(
            _finding("stack_lock_inventory_drift", "stack.lock.yaml and inventory disagree.", drift=drift)
        )
    return OrderedDict(
        [
            ("source_ref", "stack.lock.yaml"),
            ("available", True),
            ("digest", digest),
            ("component_count", component_count),
            ("drift", drift),
        ]
    ), warnings


def collect_inventory(root: Path, branch_state: dict[str, Any]) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    inventory_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
    markdown_path = root / "docs" / "audits" / "STACK-REPO-INVENTORY.md"
    payload = _read_json(inventory_path)
    if payload is None:
        return OrderedDict([("source_ref", atlas_relative(inventory_path, root=root)), ("available", False)]), [
            _finding("inventory_unavailable", "Inventory JSON could not be read.", severity="blocker")
        ]

    json_payload_without_digest = dict(payload)
    reported_digest = str(json_payload_without_digest.pop("content_digest", ""))
    actual_digest = stable_json_digest(json_payload_without_digest)
    digest_drift = bool(reported_digest and actual_digest != reported_digest)
    if digest_drift:
        warnings.append(
            _finding(
                "inventory_digest_drift",
                "Inventory content_digest does not match inventory content.",
                reported=reported_digest,
                actual=actual_digest,
            )
        )

    repos = payload.get("repos", [])
    stack_repo = next((item for item in repos if isinstance(item, dict) and item.get("logical_id") == "stack"), None)
    root_head = branch_state.get("head")
    stack_commit = stack_repo.get("current_commit") if stack_repo else None
    root_head_relation = _git_commit_relation(root, stack_commit, root_head)
    root_head_drift = bool(stack_repo and root_head and stack_commit != root_head)
    if root_head_drift:
        code = "inventory_root_head_self_reference_lag" if root_head_relation == "ancestor" else "inventory_root_head_drift"
        message = (
            "Inventory stack entry points at an ancestor of current root HEAD; this is expected after committing root-only changes."
            if root_head_relation == "ancestor"
            else "Inventory stack entry does not match current root HEAD."
        )
        warnings.append(
            _finding(
                code,
                message,
                inventory=stack_commit,
                head=root_head,
                relation=root_head_relation,
            )
        )

    markdown_text = _read_text(markdown_path)
    markdown_digest_match = None
    if markdown_text is None:
        warnings.append(_finding("inventory_markdown_unavailable", "Inventory markdown could not be read."))
    else:
        markdown_digest_match = reported_digest in markdown_text if reported_digest else False
        if not markdown_digest_match:
            warnings.append(
                _finding(
                    "inventory_markdown_digest_drift",
                    "Inventory markdown does not mirror the JSON content digest.",
                    digest=reported_digest,
                )
            )

    root_blocking_dirty = []
    advisory_dirty = []
    if isinstance(repos, list):
        for item in repos:
            if not isinstance(item, dict) or not item.get("dirty"):
                continue
            repo_id = item.get("logical_id")
            if item.get("dirty_blocks_root"):
                root_blocking_dirty.append(repo_id)
            else:
                advisory_dirty.append(repo_id)

    return OrderedDict(
        [
            ("source_ref", atlas_relative(inventory_path, root=root)),
            ("available", True),
            ("reported_digest", reported_digest),
            ("actual_digest", actual_digest),
            ("digest_matches", not digest_drift),
            ("markdown_ref", atlas_relative(markdown_path, root=root)),
            ("markdown_digest_matches", markdown_digest_match),
            ("repo_count", payload.get("repo_count")),
            ("dirty_repo_count", payload.get("dirty_repo_count")),
            ("visible_dirty_repo_count", payload.get("visible_dirty_repo_count")),
            ("advisory_dirty_repo_count", payload.get("advisory_dirty_repo_count")),
            ("root_head_matches", not root_head_drift),
            ("root_head_relation", root_head_relation),
            ("root_blocking_dirty_repos", root_blocking_dirty),
            ("advisory_dirty_repos", advisory_dirty),
            ("payload", payload),
        ]
    ), warnings


def collect_atlas_book(root: Path, markers: dict[str, Any]) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    current_state = _read_text(root / "docs" / "atlas-book" / "01-current-state.md") or ""
    lanes = _read_text(root / "docs" / "atlas-book" / "02-lanes-and-markers.md") or ""
    receipt_index = _read_text(root / "docs" / "atlas-book" / "05-receipt-index.md") or ""
    restart = _read_text(root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md") or ""
    joined = "\n".join([current_state, lanes, receipt_index, restart])
    expected_bits = {
        "marker_current": f"AI Work Session Stability & Auto-Sync Loop: {AI_WORK_SESSION_MARKER_PERCENT}%" in joined
        or (
            "AI Work Session Stability & Auto-Sync Loop` now sits at "
            f"`{AI_WORK_SESSION_MARKER_PERCENT}%"
        )
        in joined,
        "projection_packet": PROJECTION_PACKET in joined,
        "routing_receipt": PROJECTION_RECEIPT in joined or Path(PROJECTION_RECEIPT).name in joined,
    }
    for key, present in expected_bits.items():
        if not present:
            warnings.append(_finding(f"atlas_book_{key}_missing", "ATLAS Book mirror is missing expected projection freshness truth."))
    return OrderedDict(
        [
            ("current_state_ref", "docs/atlas-book/01-current-state.md"),
            ("marker_board_ref", "docs/atlas-book/02-lanes-and-markers.md"),
            ("receipt_index_ref", "docs/atlas-book/05-receipt-index.md"),
            ("restart_ref", "docs/atlas-book/12-restart-and-handoff-guide.md"),
            ("expected_truth_present", expected_bits),
            ("selector_next_packet", markers.get("next_after_current_packet")),
        ]
    ), warnings


def collect_manifests(root: Path) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    manifest_path = root / "docs" / "memory" / "initiatives" / "continuity-manifest-ai-work-session-stability-auto-sync-loop.json"
    payload = _read_json(manifest_path)
    if payload is None:
        return OrderedDict([("source_ref", atlas_relative(manifest_path, root=root)), ("available", False)]), [
            _finding("ai_work_session_manifest_unavailable", "AI Work Session continuity manifest could not be read.", severity="blocker")
        ]
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
    marker_posture = metadata.get("marker_posture", [])
    percent = None
    if isinstance(marker_posture, list) and marker_posture:
        first = marker_posture[0]
        if isinstance(first, dict):
            percent = first.get("percent")
    next_package_ladder = metadata.get("next_package_ladder", [])
    next_package = None
    if isinstance(next_package_ladder, list) and next_package_ladder:
        first = next_package_ladder[0]
        if isinstance(first, dict):
            next_package = first.get("package")
    checkpoint = metadata.get("current_checkpoint_receipt")
    if percent != AI_WORK_SESSION_MARKER_PERCENT:
        warnings.append(_finding("manifest_marker_percent_drift", "AI Work Session manifest marker percent is stale.", percent=percent))
    if next_package != PROJECTION_PACKET:
        warnings.append(_finding("manifest_next_packet_drift", "AI Work Session manifest next package is stale.", package=next_package))
    if checkpoint != PROJECTION_RECEIPT:
        warnings.append(_finding("manifest_checkpoint_drift", "AI Work Session manifest checkpoint receipt is stale.", checkpoint=checkpoint))
    return OrderedDict(
        [
            ("source_ref", atlas_relative(manifest_path, root=root)),
            ("available", True),
            ("marker_percent", percent),
            ("next_package", next_package),
            ("current_checkpoint_receipt", checkpoint),
        ]
    ), warnings


def collect_markers(root: Path, manifests: dict[str, Any] | None = None) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    payload = build_campaign(root=root)
    next_packet = payload.get("next_after_current_packet")
    next_basis = payload.get("next_after_current_packet_basis_ref")
    next_percent = payload.get("next_after_current_percentage")
    operator_action = payload.get("operator_action")
    no_immediate = operator_action == NO_IMMEDIATE_OPERATOR_ACTION
    if no_immediate:
        manifest_package = manifests.get("next_package") if manifests else None
        manifest_checkpoint = manifests.get("current_checkpoint_receipt") if manifests else None
        if manifest_package != PROJECTION_PACKET:
            warnings.append(
                _finding(
                    "selector_no_immediate_manifest_packet_drift",
                    "Marker selector reports no immediate root packet, but the AI Work Session manifest does not hold the expected package.",
                    package=manifest_package,
                )
            )
        if manifest_checkpoint != PROJECTION_RECEIPT:
            warnings.append(
                _finding(
                    "selector_no_immediate_manifest_basis_drift",
                    "Marker selector reports no immediate root packet, but the AI Work Session manifest checkpoint is stale.",
                    basis=manifest_checkpoint,
                )
            )
    else:
        if next_packet != PROJECTION_PACKET:
            warnings.append(_finding("selector_next_packet_drift", "Marker selector does not route the expected AI Work Session next packet.", packet=next_packet))
        if next_basis != PROJECTION_RECEIPT:
            warnings.append(_finding("selector_basis_drift", "Marker selector basis receipt is stale.", basis=next_basis))
    if manifests and not no_immediate and manifests.get("marker_percent") != next_percent:
        warnings.append(
            _finding(
                "marker_manifest_percent_drift",
                "Marker selector and AI Work Session manifest disagree on percent.",
                selector=next_percent,
                manifest=manifests.get("marker_percent"),
            )
        )
    return OrderedDict(
        [
            ("source_ref", "docs/atlas-book/02-lanes-and-markers.md"),
            ("active_lane", payload.get("active_lane")),
            ("operator_action", payload.get("operator_action")),
            ("next_after_current_marker", payload.get("next_after_current_marker")),
            ("next_after_current_percentage", next_percent),
            ("next_after_current_packet", next_packet),
            ("next_after_current_packet_basis_ref", next_basis),
            ("next_after_current_packet_mode", payload.get("next_after_current_packet_mode")),
        ]
    ), warnings


def collect_receipts(root: Path) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    refs = [
        "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PROJECTION-FRESHNESS-CHECKER-FIRST-IMPLEMENTATION-ADMISSION-2026-07-02.md",
        "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PROJECTION-FRESHNESS-CHECKER-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-02.md",
        PROJECTION_RECEIPT,
    ]
    missing = [ref for ref in refs if not (root / ref).exists()]
    if missing:
        warnings.append(_finding("projection_receipts_missing", "Projection freshness receipt chain is incomplete.", missing=missing, severity="blocker"))
    return OrderedDict([("required_refs", refs), ("missing", missing), ("complete", not missing)]), warnings


def collect_pull_requests(root: Path, pr_body_file: str | None, pr_head: str | None, skip_pr: bool) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    if skip_pr or not pr_body_file:
        return OrderedDict([("checked", False), ("reason", "not_requested"), ("stale_refs", [])]), warnings
    body_path = root / pr_body_file
    body = _read_text(body_path)
    if body is None:
        return OrderedDict([("checked", True), ("body_ref", pr_body_file), ("stale_refs", [])]), [
            _finding("pr_body_unavailable", "Requested PR body fixture could not be read.", severity="blocker", body_ref=pr_body_file)
        ]
    short_sha_pattern = re.compile(r"\b[0-9a-f]{8,40}\b")
    refs = sorted(set(short_sha_pattern.findall(body)))
    stale = []
    if pr_head:
        for ref in refs:
            if not pr_head.startswith(ref) and not ref.startswith(pr_head):
                stale.append(ref)
    if stale:
        warnings.append(_finding("pr_body_stale_head_refs", "PR body contains stale head references.", severity="blocker", stale_refs=stale, expected_head=pr_head))
    return OrderedDict([("checked", True), ("body_ref", pr_body_file), ("expected_head", pr_head), ("stale_refs", stale)]), warnings


def collect_owner_lanes(owners: list[str], inventory: dict[str, Any]) -> OrderedDict[str, Any]:
    repos = inventory.get("payload", {}).get("repos", []) if isinstance(inventory.get("payload"), dict) else []
    by_id = {item.get("logical_id"): item for item in repos if isinstance(item, dict)}
    requested = []
    for owner in owners:
        item = by_id.get(owner)
        requested.append(
            OrderedDict(
                [
                    ("owner", owner),
                    ("known", item is not None),
                    ("dirty", bool(item.get("dirty")) if item else None),
                    ("dirty_blocks_root", bool(item.get("dirty_blocks_root")) if item else None),
                    ("classification", "root_blocking" if item and item.get("dirty_blocks_root") else "advisory_or_clean"),
                ]
            )
        )
    return OrderedDict([("requested", requested), ("mode", "read_only" if owners else "none")])


def collect_proof_state(root: Path) -> tuple[OrderedDict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    readiness = _read_json(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
    dry_run_markers = []
    protected_markers = []
    if readiness:
        text = json.dumps(readiness, sort_keys=True).lower()
        if "dry-run" in text or "dry_run" in text:
            dry_run_markers.append("release-readiness.latest.json")
        if "protected" in text and "dry-run" not in text and "dry_run" not in text:
            protected_markers.append("release-readiness.latest.json")
    protected_claim_without_evidence = bool(dry_run_markers and not protected_markers)
    if protected_claim_without_evidence:
        warnings.append(_finding("dry_run_not_protected_proof", "Dry-run proof is present without protected proof evidence."))
    return OrderedDict(
        [
            ("release_readiness_available", readiness is not None),
            ("dry_run_refs", dry_run_markers),
            ("protected_refs", protected_markers),
            ("protected_proof_explicit", bool(protected_markers)),
        ]
    ), warnings


def collect_protected_surfaces(branch_state: dict[str, Any]) -> OrderedDict[str, Any]:
    touched = []
    for key in ("staged", "unstaged", "untracked"):
        for relative_path in branch_state.get(key, []):
            if _protected_path(str(relative_path)):
                touched.append(OrderedDict([("path", relative_path), ("source", key)]))
    return OrderedDict([("touched", touched), ("blocked", touched)])


def _split_findings(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = [item for item in findings if item.get("severity") == "blocker"]
    warnings = [item for item in findings if item.get("severity") != "blocker"]
    return blockers, warnings


def build_report(
    *,
    root: Path,
    scope: str,
    owners: list[str] | None = None,
    pr_body_file: str | None = None,
    pr_head: str | None = None,
    skip_pr: bool = False,
) -> OrderedDict[str, Any]:
    owners = owners or []
    all_findings: list[dict[str, Any]] = []
    branch_state = collect_branch_state(root)
    if branch_state["parity"]["status"] == "unavailable":
        all_findings.append(_finding("parity_unavailable", "Remote parity truth is unavailable.", severity="blocker"))
    if branch_state["parity"]["status"] == "drift":
        all_findings.append(_finding("parity_drift", "Root branch parity is not clean.", severity="blocker", parity=branch_state["parity"]))
    if branch_state["staged"]:
        all_findings.append(_finding("staged_files_present", "Staged files block projection freshness claims.", severity="blocker", paths=branch_state["staged"]))
    if branch_state["unstaged"] or branch_state["untracked"]:
        all_findings.append(_finding("local_residue_present", "Local residue can make projections stale.", unstaged=branch_state["unstaged"], untracked=branch_state["untracked"]))

    inventory, inventory_findings = collect_inventory(root, branch_state)
    all_findings.extend(inventory_findings)
    stack_lock, lock_findings = collect_stack_lock(root, inventory.get("payload") if inventory else None)
    all_findings.extend(lock_findings)
    manifests, manifest_findings = collect_manifests(root)
    all_findings.extend(manifest_findings)
    markers, marker_findings = collect_markers(root, manifests)
    all_findings.extend(marker_findings)
    atlas_book, book_findings = collect_atlas_book(root, markers)
    all_findings.extend(book_findings)
    receipts, receipt_findings = collect_receipts(root)
    all_findings.extend(receipt_findings)
    pull_requests, pr_findings = collect_pull_requests(root, pr_body_file, pr_head, skip_pr)
    all_findings.extend(pr_findings)
    owner_lanes = collect_owner_lanes(owners, inventory)
    proof_state, proof_findings = collect_proof_state(root)
    all_findings.extend(proof_findings)
    protected_surfaces = collect_protected_surfaces(branch_state)
    if protected_surfaces["blocked"]:
        all_findings.append(_finding("protected_surface_touched", "Protected surfaces are touched.", severity="blocker", touched=protected_surfaces["blocked"]))
    if inventory.get("root_blocking_dirty_repos"):
        all_findings.append(_finding("root_blocking_dirty_repos", "Inventory reports root-blocking dirty repositories.", severity="blocker", repos=inventory.get("root_blocking_dirty_repos")))
    if inventory.get("advisory_dirty_repos"):
        all_findings.append(_finding("advisory_owner_lane_dirty", "Inventory reports advisory owner-lane dirt.", repos=inventory.get("advisory_dirty_repos")))

    blockers, warnings = _split_findings(all_findings)
    required_refreshes = []
    for item in all_findings:
        code = str(item.get("code", "unknown"))
        if code.endswith("_drift") or "stale" in code or "missing" in code or "unavailable" in code:
            required_refreshes.append(OrderedDict([("code", code), ("target", item.get("message"))]))

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch_state.get("branch")),
            ("head", branch_state.get("head")),
            ("parity", branch_state.get("parity")),
            ("stack_lock", stack_lock),
            ("inventory", OrderedDict((key, value) for key, value in inventory.items() if key != "payload")),
            ("atlas_book", atlas_book),
            ("receipts", receipts),
            ("manifests", manifests),
            ("markers", markers),
            ("pull_requests", pull_requests),
            ("owner_lanes", owner_lanes),
            ("proof_state", proof_state),
            ("protected_surfaces", protected_surfaces),
            ("blockers", blockers),
            ("warnings", warnings),
            ("required_refreshes", required_refreshes),
            ("safe_to_continue", not blockers),
        ]
    )


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
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Parity: {parity.get('status', 'unknown')} (behind={parity.get('behind')}, ahead={parity.get('ahead')})",
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
            f"Required refreshes: {len(report.get('required_refreshes', []))}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only ATLAS projection freshness checker.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--scope", choices=sorted(SCOPES), default="root")
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--pr-body-file")
    parser.add_argument("--pr-head")
    parser.add_argument("--skip-pr", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(
            root=root,
            scope=args.scope,
            owners=list(args.owner or []),
            pr_body_file=args.pr_body_file,
            pr_head=args.pr_head,
            skip_pr=bool(args.skip_pr),
        )
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_continue"] = False
                report["required_refreshes"] = list(report.get("required_refreshes", [])) + [
                    OrderedDict([("code", output_error["code"]), ("target", output_error["message"])])
                ]
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("parity", OrderedDict([("status", "unavailable"), ("behind", None), ("ahead", None)])),
                ("stack_lock", OrderedDict()),
                ("inventory", OrderedDict()),
                ("atlas_book", OrderedDict()),
                ("receipts", OrderedDict()),
                ("manifests", OrderedDict()),
                ("markers", OrderedDict()),
                ("pull_requests", OrderedDict()),
                ("owner_lanes", OrderedDict()),
                ("proof_state", OrderedDict()),
                ("protected_surfaces", OrderedDict()),
                ("blockers", [_finding("internal_error", "Projection freshness failed before classification.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
                ("required_refreshes", [OrderedDict([("code", "internal_error"), ("target", "debug projection freshness worker")])]),
                ("safe_to_continue", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
