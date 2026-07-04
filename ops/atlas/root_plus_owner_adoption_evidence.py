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
from ops.stack.generate_lockfile import git_output

SCHEMA_VERSION = "atlas.root_plus_owner_adoption_evidence.v1"
STATUS_OK = "ok"
STATUS_NEEDS_EVIDENCE = "needs_owner_evidence"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
REQUIRED_OWNER_COUNT = 2
PROTECTED_OUTPUT_PREFIXES = {
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "runtime",
    "secrets",
}
CONTRACT_RECEIPTS = (
    "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-ROOT-PLUS-OWNER-ADOPTION-ADMISSION-2026-07-04.md",
    "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-ROOT-PLUS-OWNER-ADOPTION-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-04.md",
    "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-ROOT-PLUS-OWNER-ADOPTION-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-04.md",
)
REQUIRED_EVIDENCE_FIELDS = OrderedDict(
    [
        ("owner-lane adoption proof", "true"),
        ("owner repo", None),
        ("ai work-session loop used", "true"),
        ("separate owner-lane authorization", "true"),
        ("root mutated owner repo", "false"),
        ("platform mutation from root", "false"),
        ("protected-surface mutation", "false"),
        ("secrets touched", "false"),
    ]
)
FIELD_RE = re.compile(r"^\s*(?:[-*]\s*)?`?([^:`\n]+):\s*([^`\n]+?)`?\s*$")


def _git_stdout(repo_root: Path, *args: str) -> tuple[int, str]:
    code, stdout = git_output(repo_root, *args)
    return code, stdout.strip()


def _git_lines(repo_root: Path, *args: str) -> list[str]:
    code, stdout = _git_stdout(repo_root, *args)
    if code != 0 or not stdout:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _finding(code: str, message: str, *, severity: str = "advisory", **details: Any) -> OrderedDict[str, Any]:
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


def _root_relative(path: Path, root: Path) -> str:
    return normalize_slashes(str(path.resolve().relative_to(root.resolve())))


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


def collect_contract_receipts(root: Path) -> tuple[list[OrderedDict[str, Any]], list[dict[str, Any]]]:
    rows: list[OrderedDict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for ref in CONTRACT_RECEIPTS:
        path = root / ref
        text = _read_text(path)
        exists = text is not None
        rows.append(OrderedDict([("path", ref), ("exists", exists)]))
        if not exists:
            findings.append(_finding("contract_receipt_missing", "Required root contract receipt is missing.", severity="blocker", path=ref))
    return rows, findings


def _parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().strip("`").lower()
        value = match.group(2).strip().strip("`")
        fields[key] = value
    return fields


def _looks_like_owner_evidence(fields: dict[str, str]) -> bool:
    return "owner-lane adoption proof" in fields or "ai work-session loop used" in fields or "owner repo" in fields


def classify_owner_evidence(path: Path, *, root: Path) -> OrderedDict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    fields = _parse_fields(text)
    if not _looks_like_owner_evidence(fields):
        return None

    reasons: list[str] = []
    for field, expected in REQUIRED_EVIDENCE_FIELDS.items():
        actual = fields.get(field)
        if actual is None or not actual.strip():
            reasons.append(f"missing:{field}")
            continue
        if expected is not None and actual.strip().lower() != expected:
            reasons.append(f"expected:{field}={expected}")
    owner_repo = fields.get("owner repo", "").strip()
    if not owner_repo or "<" in owner_repo or ">" in owner_repo:
        reasons.append("invalid:owner repo")
    if owner_repo.lower() in {"atlas", "root", "atlas-root"}:
        reasons.append("invalid:root-owned-owner")

    eligible = not reasons
    return OrderedDict(
        [
            ("path", _root_relative(path, root)),
            ("owner_repo", owner_repo or None),
            ("eligible", eligible),
            ("reasons", reasons),
            ("fields", OrderedDict((field, fields.get(field)) for field in REQUIRED_EVIDENCE_FIELDS.keys())),
        ]
    )


def collect_owner_evidence(root: Path) -> list[OrderedDict[str, Any]]:
    ops_dir = root / "docs" / "ops"
    if not ops_dir.exists():
        return []
    contract_paths = {normalize_slashes(ref) for ref in CONTRACT_RECEIPTS}
    rows: list[OrderedDict[str, Any]] = []
    for path in sorted(ops_dir.glob("*.md"), key=lambda item: normalize_slashes(str(item))):
        if _root_relative(path, root) in contract_paths:
            continue
        row = classify_owner_evidence(path, root=root)
        if row is not None:
            rows.append(row)
    return rows


def _eligible_owner_repos(rows: list[dict[str, Any]]) -> list[str]:
    owners: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not row.get("eligible"):
            continue
        owner = str(row.get("owner_repo") or "").strip()
        key = owner.lower()
        if not owner or key in seen:
            continue
        seen.add(key)
        owners.append(owner)
    return owners


def _split_findings(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = [item for item in findings if item.get("severity") == "blocker"]
    warnings = [item for item in findings if item.get("severity") != "blocker"]
    return blockers, warnings


def build_report(*, root: Path) -> OrderedDict[str, Any]:
    findings: list[dict[str, Any]] = []
    branch_state = collect_branch_state(root)
    if branch_state["parity"]["status"] == "unavailable":
        findings.append(_finding("parity_unavailable", "Remote parity truth is unavailable.", severity="blocker"))
    elif branch_state["parity"]["status"] == "drift":
        findings.append(_finding("parity_drift", "Root branch parity is not clean.", severity="blocker", parity=branch_state["parity"]))
    if branch_state["staged"]:
        findings.append(_finding("staged_files_present", "Staged files block adoption claims.", severity="blocker", paths=branch_state["staged"]))
    if branch_state["unstaged"] or branch_state["untracked"]:
        findings.append(
            _finding(
                "local_residue_present",
                "Local residue is present; evidence classification remains advisory.",
                unstaged=branch_state["unstaged"],
                untracked=branch_state["untracked"],
            )
        )

    contract_receipts, contract_findings = collect_contract_receipts(root)
    findings.extend(contract_findings)
    owner_evidence = collect_owner_evidence(root)
    eligible_owners = _eligible_owner_repos(owner_evidence)
    if len(eligible_owners) < REQUIRED_OWNER_COUNT:
        findings.append(
            _finding(
                "owner_evidence_below_threshold",
                "Fewer than two eligible owner-lane adoption proofs exist.",
                eligible_owner_count=len(eligible_owners),
                required_owner_count=REQUIRED_OWNER_COUNT,
            )
        )
    duplicate_count = len([row for row in owner_evidence if row.get("eligible")]) - len(eligible_owners)
    if duplicate_count > 0:
        findings.append(_finding("duplicate_owner_evidence", "Duplicate owner-lane evidence does not increase adoption count.", duplicate_count=duplicate_count))

    blockers, warnings = _split_findings(findings)
    threshold_met = len(eligible_owners) >= REQUIRED_OWNER_COUNT and not blockers
    status = STATUS_OK if threshold_met else STATUS_NEEDS_EVIDENCE
    if blockers:
        status = STATUS_BLOCKER
    required_followups = []
    if not threshold_met and not blockers:
        required_followups.append(
            OrderedDict(
                [
                    ("code", "supply_owner_lane_evidence"),
                    ("target", "Provide at least two separately authorized owner-lane adoption proof receipts."),
                ]
            )
        )
    for blocker in blockers:
        required_followups.append(OrderedDict([("code", blocker.get("code")), ("target", blocker.get("message"))]))

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch_state.get("branch")),
            ("head", branch_state.get("head")),
            ("parity", branch_state.get("parity")),
            ("contract_receipts", contract_receipts),
            ("owner_evidence", owner_evidence),
            ("eligible_owner_count", len(eligible_owners)),
            ("required_owner_count", REQUIRED_OWNER_COUNT),
            ("threshold_met", threshold_met),
            ("blockers", blockers),
            ("warnings", warnings),
            ("required_followups", required_followups),
            ("safe_to_continue", not blockers),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_NEEDS_EVIDENCE:
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
            f"Eligible owner evidence: {report.get('eligible_owner_count')}/{report.get('required_owner_count')}",
            f"Threshold met: {str(report.get('threshold_met')).lower()}",
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only ATLAS root-plus-owner adoption evidence classifier.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output")
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
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_continue"] = False
                report["required_followups"] = list(report.get("required_followups", [])) + [
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
                ("contract_receipts", []),
                ("owner_evidence", []),
                ("eligible_owner_count", 0),
                ("required_owner_count", REQUIRED_OWNER_COUNT),
                ("threshold_met", False),
                ("blockers", [_finding("internal_error", "Root-plus-owner evidence worker failed before classification.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
                ("required_followups", [OrderedDict([("code", "internal_error"), ("target", "debug root-plus-owner evidence worker")])]),
                ("safe_to_continue", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
