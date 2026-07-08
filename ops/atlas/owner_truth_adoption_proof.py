from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.owner_truth_adoption_proof.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

ADOPTION_ADOPTED = "adopted_advisory_truth"
ADOPTION_BLOCKED = "blocked_root_truth"
ADOPTION_INSUFFICIENT = "insufficient_evidence"
ADOPTION_CONTRACT_VIOLATION = "contract_violation"

MARKER_NO_MOVEMENT = "no_marker_movement"
MARKER_CANDIDATE = "candidate_for_future_ratchet"
MARKER_BLOCKED = "blocked"

PROTECTED_OUTPUT_PREFIXES = {
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "runtime",
    "secrets",
}

ATLAS_BOOK_REFS = (
    "docs/atlas-book/01-current-state.md",
    "docs/atlas-book/02-lanes-and-markers.md",
    "docs/atlas-book/05-receipt-index.md",
    "docs/atlas-book/12-restart-and-handoff-guide.md",
)

REQUIRED_RECEIPTS = (
    "docs/ops/INVENTORY-AND-TRUTH-MAP-OWNER-TRUTH-ADOPTION-PROOF-SELECTION-2026-07-08.md",
    "docs/ops/INVENTORY-AND-TRUTH-MAP-OWNER-TRUTH-ADOPTION-PROOF-CONTRACT-FREEZE-2026-07-08.md",
)

AUTHORITY_DENIALS = OrderedDict(
    [
        ("owner_repo_mutation", True),
        ("owner_repo_source_diff_authority", True),
        ("owner_repo_file_content_authority", True),
        ("deploy_or_platform_api_access", True),
        ("secret_access", True),
        ("protected_surface_access", True),
        ("product_or_game_readiness_claims", True),
        ("marker_movement_without_reconciliation_receipt", True),
    ]
)

VALIDATION_RE = re.compile(
    r"critical=(?P<critical>\d+)\s+error=(?P<error>\d+)\s+warning=(?P<warning>\d+)\s+info=(?P<info>\d+)",
    re.IGNORECASE,
)


def _read_text(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _read_json(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _finding(code: str, message: str, *, severity: str = "advisory", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
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


def parse_owner_status_inputs(values: list[str] | None) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    rows: list[OrderedDict[str, Any]] = []
    findings: list[OrderedDict[str, Any]] = []
    for raw in values or []:
        value = raw.strip()
        parts = [part.strip() for part in value.split(":")]
        if len(parts) != 3:
            findings.append(
                _finding(
                    "invalid_owner_status_input",
                    "Owner status input must use repo_id:dirty|clean:advisory|root_blocking|clean.",
                    severity="blocker",
                    value=value,
                )
            )
            continue
        repo_id, cleanliness, classification = parts
        if not repo_id or "/" in repo_id or "\\" in repo_id:
            findings.append(_finding("invalid_owner_status_repo", "Owner status repo id must be a simple id.", severity="blocker", value=value))
            continue
        if cleanliness not in {"dirty", "clean"} or classification not in {"advisory", "root_blocking", "clean"}:
            findings.append(_finding("invalid_owner_status_classification", "Owner status classification is unsupported.", severity="blocker", value=value))
            continue
        dirty = cleanliness == "dirty"
        dirty_blocks_root = classification == "root_blocking"
        if not dirty and classification != "clean":
            findings.append(_finding("owner_status_clean_classification_mismatch", "Clean owner status must use clean classification.", severity="blocker", value=value))
            continue
        rows.append(
            OrderedDict(
                [
                    ("repo_id", repo_id),
                    ("dirty", dirty),
                    ("classification", classification),
                    ("dirty_blocks_root", dirty_blocks_root),
                    ("source", "operator_inline_summary"),
                ]
            )
        )
    return rows, findings


def collect_root_validation_summary(root: Path) -> OrderedDict[str, Any]:
    preferred_refs = (
        "docs/atlas-book/01-current-state.md",
        "docs/atlas-book/02-lanes-and-markers.md",
        "docs/atlas-book/12-restart-and-handoff-guide.md",
        "docs/atlas-book/05-receipt-index.md",
    )
    selected_ref = None
    selected_match = None
    for ref in preferred_refs:
        text = _read_text(root / ref) or ""
        matches = list(VALIDATION_RE.finditer(text))
        if not matches:
            continue
        selected_ref = ref
        selected_match = matches[0]
        break
    if selected_match is None:
        return OrderedDict(
            [
                ("source", "atlas_book_mirror"),
                ("source_ref", None),
                ("available", False),
                ("critical", None),
                ("error", None),
                ("warning", None),
                ("info", None),
                ("clean", False),
            ]
        )
    counts = {key: int(selected_match.group(key)) for key in ("critical", "error", "warning", "info")}
    return OrderedDict(
        [
            ("source", "atlas_book_mirror"),
            ("source_ref", selected_ref),
            ("available", True),
            ("critical", counts["critical"]),
            ("error", counts["error"]),
            ("warning", counts["warning"]),
            ("info", counts["info"]),
            ("clean", counts["critical"] == 0 and counts["error"] == 0),
        ]
    )


def collect_inventory(root: Path) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]]]:
    findings: list[OrderedDict[str, Any]] = []
    inventory_ref = "docs/registry/STACK-REPO-INVENTORY.json"
    audit_ref = "docs/audits/STACK-REPO-INVENTORY.md"
    inventory = _read_json(root / inventory_ref)
    audit = _read_text(root / audit_ref)
    if inventory is None:
        return (
            OrderedDict(
                [
                    ("source_ref", inventory_ref),
                    ("available", False),
                    ("markdown_ref", audit_ref),
                    ("markdown_available", audit is not None),
                    ("repo_count", None),
                    ("dirty_repo_count", None),
                    ("visible_dirty_repo_count", None),
                    ("advisory_dirty_repo_count", None),
                    ("advisory_owner_repos", []),
                    ("root_blocking_owner_repos", []),
                    ("count_mismatches", []),
                ]
            ),
            [_finding("inventory_unavailable", "Inventory JSON is missing or invalid.", severity="blocker")],
        )

    repos = inventory.get("repos", []) if isinstance(inventory.get("repos"), list) else []
    advisory_repos: list[str] = []
    root_blocking_repos: list[str] = []
    visible_dirty_count = 0
    for item in repos:
        if not isinstance(item, dict):
            continue
        repo_id = str(item.get("logical_id") or item.get("repo_id") or item.get("id") or "").strip()
        if not repo_id or not item.get("dirty"):
            continue
        visible_dirty_count += 1
        if item.get("dirty_blocks_root"):
            root_blocking_repos.append(repo_id)
        else:
            advisory_repos.append(repo_id)

    count_mismatches: list[OrderedDict[str, Any]] = []
    expected_counts = {
        "dirty_repo_count": len(root_blocking_repos),
        "visible_dirty_repo_count": visible_dirty_count,
        "advisory_dirty_repo_count": len(advisory_repos),
    }
    for key, expected in expected_counts.items():
        actual = inventory.get(key)
        if actual != expected:
            count_mismatches.append(OrderedDict([("field", key), ("expected", expected), ("actual", actual)]))
    if count_mismatches:
        findings.append(_finding("inventory_count_mismatch", "Inventory dirty counts do not match repo rows.", severity="blocker", mismatches=count_mismatches))
    if root_blocking_repos:
        findings.append(_finding("root_blocking_owner_dirt", "Inventory contains root-blocking dirty repos.", severity="blocker", repos=root_blocking_repos))

    markdown_mirrors_counts = False
    if audit is not None:
        markdown_mirrors_counts = all(f"{label}: `{value}`" in audit for label, value in {
            "Root-blocking dirty repo count": inventory.get("dirty_repo_count"),
            "Visible dirty repo count": inventory.get("visible_dirty_repo_count"),
            "Advisory dirty repo count": inventory.get("advisory_dirty_repo_count"),
        }.items())
    else:
        findings.append(_finding("inventory_markdown_unavailable", "Inventory markdown mirror is missing."))

    if audit is not None and not markdown_mirrors_counts:
        findings.append(_finding("inventory_markdown_count_drift", "Inventory markdown does not mirror JSON dirty counts."))

    return (
        OrderedDict(
            [
                ("source_ref", inventory_ref),
                ("available", True),
                ("markdown_ref", audit_ref),
                ("markdown_available", audit is not None),
                ("markdown_mirrors_counts", markdown_mirrors_counts),
                ("repo_count", inventory.get("repo_count")),
                ("dirty_repo_count", inventory.get("dirty_repo_count")),
                ("visible_dirty_repo_count", inventory.get("visible_dirty_repo_count")),
                ("advisory_dirty_repo_count", inventory.get("advisory_dirty_repo_count")),
                ("advisory_owner_repos", advisory_repos),
                ("root_blocking_owner_repos", root_blocking_repos),
                ("count_mismatches", count_mismatches),
            ]
        ),
        findings,
    )


def collect_book_mirror_status(root: Path, inventory: dict[str, Any]) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]], str]:
    findings: list[OrderedDict[str, Any]] = []
    refs: list[OrderedDict[str, Any]] = []
    texts: list[str] = []
    for ref in ATLAS_BOOK_REFS:
        text = _read_text(root / ref)
        available = text is not None
        refs.append(OrderedDict([("ref", ref), ("available", available)]))
        if text is None:
            findings.append(_finding("book_surface_missing", "Required ATLAS Book mirror surface is missing.", ref=ref))
            continue
        texts.append(text)
    joined = "\n".join(texts)
    expected = OrderedDict(
        [
            ("dirty_repo_count", f"dirty_repo_count: {inventory.get('dirty_repo_count')}"),
            ("visible_dirty_repo_count", f"visible_dirty_repo_count: {inventory.get('visible_dirty_repo_count')}"),
            ("advisory_dirty_repo_count", f"advisory_dirty_repo_count: {inventory.get('advisory_dirty_repo_count')}"),
            ("next_package", "No immediate Inventory & Truth Map follow-on packet"),
            ("contract_receipt", Path(REQUIRED_RECEIPTS[1]).name),
        ]
    )
    present = OrderedDict((key, needle in joined) for key, needle in expected.items())
    missing_keys = [key for key, value in present.items() if not value]
    if missing_keys:
        findings.append(_finding("book_mirror_drift", "ATLAS Book mirror is missing owner-truth adoption posture.", missing=missing_keys))
    return (
        OrderedDict(
            [
                ("refs", refs),
                ("expected_truth_present", present),
                ("status", "ok" if not missing_keys and all(item["available"] for item in refs) else "advisory_gap"),
            ]
        ),
        findings,
        joined,
    )


def collect_scope_lock_status(root: Path, inventory: dict[str, Any]) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]]]:
    findings: list[OrderedDict[str, Any]] = []
    agents_text = _read_text(root / "AGENTS.md") or ""
    stack_text = _read_text(root / "stack.yaml") or ""
    repos = []
    payload = _read_json(root / "docs/registry/STACK-REPO-INVENTORY.json") or {}
    for item in payload.get("repos", []) if isinstance(payload.get("repos"), list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "unmanaged" or item.get("root_blocking") is False:
            repos.append(
                OrderedDict(
                    [
                        ("repo_id", item.get("logical_id")),
                        ("status", item.get("status")),
                        ("root_blocking", bool(item.get("root_blocking"))),
                        ("dirty_blocks_root", bool(item.get("dirty_blocks_root"))),
                    ]
                )
            )
    checks = OrderedDict(
        [
            ("root_session_default_governance", "root-governance sessions by default" in agents_text),
            ("owner_repos_excluded_fallback_lanes", "owner repos are excluded fallback lanes" in agents_text),
            ("no_fitness_mazer_fallback", "Do not switch into Fitness, Mazer" in agents_text),
            ("unmanaged_owner_repos_non_root_blocking", all(not row["root_blocking"] for row in repos)),
            ("stack_manifest_available", bool(stack_text.strip())),
        ]
    )
    missing = [key for key, value in checks.items() if not value]
    if missing:
        findings.append(_finding("scope_lock_drift", "Root scope-lock policy is missing expected owner-lane boundaries.", severity="blocker", missing=missing))
    return (
        OrderedDict(
            [
                ("agents_ref", "AGENTS.md"),
                ("stack_manifest_ref", "stack.yaml"),
                ("checks", checks),
                ("owner_lane_rows", repos),
                ("status", "ok" if not missing else "contract_violation"),
            ]
        ),
        findings,
    )


def collect_receipt_status(root: Path) -> tuple[OrderedDict[str, Any], list[OrderedDict[str, Any]]]:
    rows: list[OrderedDict[str, Any]] = []
    findings: list[OrderedDict[str, Any]] = []
    for ref in REQUIRED_RECEIPTS:
        exists = (root / ref).exists()
        rows.append(OrderedDict([("ref", ref), ("exists", exists)]))
        if not exists:
            findings.append(_finding("required_receipt_missing", "Required owner-truth adoption proof receipt is missing.", severity="blocker", ref=ref))
    return OrderedDict([("required_receipts", rows), ("status", "ok" if all(row["exists"] for row in rows) else "blocked")]), findings


def reconcile_owner_status_inputs(
    owner_status_inputs: list[dict[str, Any]],
    inventory_advisory: list[str],
    inventory_root_blocking: list[str],
) -> list[OrderedDict[str, Any]]:
    findings: list[OrderedDict[str, Any]] = []
    advisory = {repo.lower() for repo in inventory_advisory}
    root_blocking = {repo.lower() for repo in inventory_root_blocking}
    for row in owner_status_inputs:
        repo_id = str(row.get("repo_id") or "")
        key = repo_id.lower()
        classification = row.get("classification")
        if classification == "advisory" and key not in advisory:
            findings.append(_finding("owner_status_not_adopted", "Operator owner-status summary is not represented as advisory inventory truth.", repo_id=repo_id))
        if classification == "root_blocking" and key not in root_blocking:
            findings.append(_finding("owner_status_root_blocking_not_adopted", "Operator root-blocking owner-status summary is not represented in inventory.", severity="blocker", repo_id=repo_id))
        if classification == "clean" and (key in advisory or key in root_blocking):
            findings.append(_finding("owner_status_clean_inventory_dirty", "Operator clean owner-status summary conflicts with dirty inventory truth.", severity="blocker", repo_id=repo_id))
    return findings


def _split_findings(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = [item for item in findings if item.get("severity") == "blocker"]
    warnings = [item for item in findings if item.get("severity") != "blocker"]
    return blockers, warnings


def build_report(*, root: Path, owner_status_values: list[str] | None = None) -> OrderedDict[str, Any]:
    all_findings: list[OrderedDict[str, Any]] = []
    owner_status_inputs, owner_status_findings = parse_owner_status_inputs(owner_status_values)
    all_findings.extend(owner_status_findings)

    inventory, inventory_findings = collect_inventory(root)
    all_findings.extend(inventory_findings)
    book_mirror_status, book_findings, _joined_book_text = collect_book_mirror_status(root, inventory)
    all_findings.extend(book_findings)
    root_validation_summary = collect_root_validation_summary(root)
    if not root_validation_summary["available"]:
        all_findings.append(_finding("root_validation_summary_missing", "ATLAS Book does not mirror a root validation summary."))
    elif not root_validation_summary["clean"]:
        all_findings.append(_finding("root_validation_not_clean", "Root validation summary has critical or error findings.", severity="blocker", summary=root_validation_summary))
    scope_lock_status, scope_findings = collect_scope_lock_status(root, inventory)
    all_findings.extend(scope_findings)
    receipt_status, receipt_findings = collect_receipt_status(root)
    all_findings.extend(receipt_findings)
    all_findings.extend(
        reconcile_owner_status_inputs(
            owner_status_inputs,
            list(inventory.get("advisory_owner_repos") or []),
            list(inventory.get("root_blocking_owner_repos") or []),
        )
    )

    blockers, warnings = _split_findings(all_findings)
    has_root_blocking = bool(inventory.get("root_blocking_owner_repos"))
    if blockers:
        adoption_result = ADOPTION_BLOCKED if has_root_blocking else ADOPTION_CONTRACT_VIOLATION
    elif warnings:
        adoption_result = ADOPTION_INSUFFICIENT
    else:
        adoption_result = ADOPTION_ADOPTED

    if blockers:
        marker_implication = MARKER_BLOCKED
    elif adoption_result == ADOPTION_ADOPTED:
        marker_implication = MARKER_CANDIDATE
    else:
        marker_implication = MARKER_NO_MOVEMENT

    status = STATUS_BLOCKER if blockers else (STATUS_OK if adoption_result == ADOPTION_ADOPTED else STATUS_ADVISORY)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", not blockers),
            ("root_validation_summary", root_validation_summary),
            ("inventory_dirty_repo_count", inventory.get("dirty_repo_count")),
            ("inventory_visible_dirty_repo_count", inventory.get("visible_dirty_repo_count")),
            ("inventory_advisory_dirty_repo_count", inventory.get("advisory_dirty_repo_count")),
            ("advisory_owner_repos", inventory.get("advisory_owner_repos")),
            ("root_blocking_owner_repos", inventory.get("root_blocking_owner_repos")),
            ("owner_status_inputs", owner_status_inputs),
            ("book_mirror_status", book_mirror_status),
            ("scope_lock_status", scope_lock_status),
            ("receipt_status", receipt_status),
            ("adoption_result", adoption_result),
            ("marker_implication", marker_implication),
            ("blockers", blockers),
            ("warnings", warnings),
            ("authority_denials", AUTHORITY_DENIALS),
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
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Adoption result: {report.get('adoption_result')}",
            f"Advisory owner repos: {', '.join(report.get('advisory_owner_repos') or []) or 'none'}",
            f"Root-blocking owner repos: {', '.join(report.get('root_blocking_owner_repos') or []) or 'none'}",
            f"Marker implication: {report.get('marker_implication')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only ATLAS owner-truth adoption proof classifier.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument(
        "--owner-status",
        action="append",
        default=[],
        help="Optional inline read-only owner status summary: repo_id:dirty|clean:advisory|root_blocking|clean.",
    )
    parser.add_argument("--output", help="Optional root-relative JSON output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, owner_status_values=list(args.owner_status or []))
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["safe_to_use"] = False
                report["adoption_result"] = ADOPTION_CONTRACT_VIOLATION
                report["marker_implication"] = MARKER_BLOCKED
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
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
                ("safe_to_use", False),
                ("root_validation_summary", OrderedDict()),
                ("inventory_dirty_repo_count", None),
                ("inventory_visible_dirty_repo_count", None),
                ("inventory_advisory_dirty_repo_count", None),
                ("advisory_owner_repos", []),
                ("root_blocking_owner_repos", []),
                ("owner_status_inputs", []),
                ("book_mirror_status", OrderedDict()),
                ("scope_lock_status", OrderedDict()),
                ("receipt_status", OrderedDict()),
                ("adoption_result", ADOPTION_CONTRACT_VIOLATION),
                ("marker_implication", MARKER_BLOCKED),
                ("blockers", [_finding("internal_error", "Owner-truth adoption proof failed before classification.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
                ("authority_denials", AUTHORITY_DENIALS),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
