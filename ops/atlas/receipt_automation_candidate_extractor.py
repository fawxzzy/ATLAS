from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.receipt_automation_candidate_extractor.v1"
STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

ALLOWED_SOURCE_PREFIXES = (
    "docs/ops/",
    "docs/atlas-book/",
    "docs/memory/initiatives/continuity-manifest-",
    "ops/atlas/",
    "ops/cortex/",
    "runtime/receipts/validation/",
)
PROTECTED_PREFIXES = {
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "secrets",
}
HIDDEN_CONTEXT_PREFIXES = {
    ".codex",
    "runtime/sessions",
    "runtime/session",
    "runtime/transcripts",
    "runtime/chats",
    "tmp/transcripts",
    "tmp/chats",
}
DEPLOY_OR_PLATFORM_PREFIXES = {
    "deploy",
    "deployment",
    "platform",
    "vercel",
}
DATE_SUFFIX_RE = re.compile(r"-20\d{2}-\d{2}-\d{2}$")
PASS_SUFFIX_RE = re.compile(r"-PASS-\d+$")

CATEGORY_ORDER = (
    "helper",
    "prompt_pack",
    "selector_or_routing_rule",
    "validation_or_governance_check",
    "read_model_or_manifest_projection",
)

FAMILY_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("worker-cluster-reconciliation", "helper", "WORKER-CLUSTER", "repeated worker-cluster reconciliation receipts"),
    ("first-implementation", "helper", "FIRST-IMPLEMENTATION", "repeated first-implementation admission or proof receipts"),
    ("handoff-helper", "helper", "HANDOFF", "repeated handoff helper or handoff contract receipts"),
    ("prompt-pack", "prompt_pack", "PROMPT-PACK", "repeated prompt-pack and worker handoff receipts"),
    ("selector-routing", "selector_or_routing_rule", "SELECTOR|NEXT-SLICE-SELECTION", "repeated selector or next-slice routing receipts"),
    ("contract-freeze", "selector_or_routing_rule", "CONTRACT-FREEZE", "repeated contract-freeze receipts"),
    ("validation-governance", "validation_or_governance_check", "VALIDATION|GOVERNANCE|READINESS", "repeated validation, governance, or readiness receipts"),
    ("projection-read-model-manifest", "read_model_or_manifest_projection", "PROJECTION|READ-MODEL|MANIFEST", "repeated projection, read-model, or manifest receipts"),
)


def _git_stdout(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normalized_relative(value: str) -> str:
    return normalize_slashes(value).strip("/")


def _path_contains_env(relative_path: str) -> bool:
    return any(part.startswith(".env") for part in _normalized_relative(relative_path).split("/"))


def _is_forbidden_source_ref(relative_path: str) -> tuple[bool, str | None]:
    normalized = _normalized_relative(relative_path)
    first = normalized.split("/", 1)[0] if normalized else ""
    if not normalized:
        return True, "empty_source_ref"
    if first in PROTECTED_PREFIXES or _path_contains_env(normalized):
        return True, "protected_source_ref"
    if any(normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in HIDDEN_CONTEXT_PREFIXES):
        return True, "hidden_context_source_ref"
    if first in DEPLOY_OR_PLATFORM_PREFIXES:
        return True, "deploy_or_platform_source_ref"
    if normalized.startswith("runtime/") and not normalized.startswith("runtime/receipts/validation/"):
        return True, "unadmitted_runtime_source_ref"
    if not any(normalized.startswith(prefix) for prefix in ALLOWED_SOURCE_PREFIXES):
        return True, "unadmitted_source_ref"
    return False, None


def validate_source_ref(*, root: Path, source_ref: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(source_ref)
    if candidate.is_absolute():
        return None, _finding("absolute_source_ref", "Source ref must be root-relative.", severity="blocker", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if ".." in Path(relative_path).parts:
        return None, _finding("parent_traversal_source_ref", "Source ref must not use parent traversal.", severity="blocker", path=relative_path)
    forbidden, code = _is_forbidden_source_ref(relative_path)
    if forbidden:
        return None, _finding(code or "forbidden_source_ref", "Source ref is outside the admitted extractor inputs.", severity="blocker", path=relative_path)
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_source_ref", "Source ref must stay inside the ATLAS root.", severity="blocker", path=relative_path)
    if not resolved.exists():
        return None, _finding("missing_source_ref", "Source ref does not exist.", severity="blocker", path=relative_path)
    return resolved, None


def validate_output_path(*, root: Path, output_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return None, _finding("absolute_output_path", "Output path must be root-relative.", severity="blocker", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if ".." in Path(relative_path).parts:
        return None, _finding("parent_traversal_output_path", "Output path must not use parent traversal.", severity="blocker", path=relative_path)
    if not relative_path.startswith("tmp/"):
        return None, _finding("protected_output_path", "Output writes are admitted only under tmp/**.", severity="blocker", path=relative_path)
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", severity="blocker", path=relative_path)
    return resolved, None


def _branch_state(root: Path) -> tuple[str | None, str | None]:
    branch = _git_stdout(root, "branch", "--show-current")
    head = _git_stdout(root, "rev-parse", "HEAD")
    return branch or None, head or None


def _default_receipt_paths(root: Path) -> list[Path]:
    tracked = _git_stdout(root, "ls-files", "--", "docs/ops/*.md")
    if tracked is not None:
        return sorted((root / line).resolve() for line in tracked.splitlines() if line.strip())
    ops_dir = root / "docs" / "ops"
    if not ops_dir.exists():
        return []
    return sorted(path for path in ops_dir.glob("*.md") if path.is_file())


def _resolve_source_paths(root: Path, source_refs: list[str]) -> tuple[list[Path], list[OrderedDict[str, Any]]]:
    if not source_refs:
        return _default_receipt_paths(root), []
    paths: list[Path] = []
    blockers: list[OrderedDict[str, Any]] = []
    for source_ref in source_refs:
        resolved, error = validate_source_ref(root=root, source_ref=source_ref)
        if error is not None:
            blockers.append(error)
            continue
        if resolved is not None:
            paths.append(resolved)
    return sorted(paths), blockers


def _receipt_key(path: Path) -> str:
    stem = path.stem.upper()
    stem = DATE_SUFFIX_RE.sub("", stem)
    stem = PASS_SUFFIX_RE.sub("", stem)
    return stem


def _pattern_matches(pattern: str, key: str) -> bool:
    return re.search(pattern, key) is not None


def _candidate_title(family: str) -> str:
    return family.replace("-", " ").title()


def _recommended_next_packet(family: str) -> str:
    readable = family.replace("-", " ")
    return f"AI Repetition-to-Automation Pipeline {readable} automation candidate review"


def _candidate_boundaries() -> list[str]:
    return [
        "read_only",
        "root_owned_sources_only",
        "no_owner_repo_mutation",
        "no_hidden_transcript_inference",
        "no_secret_or_deploy_access",
        "no_stack_dispatch",
        "no_marker_movement",
    ]


def extract_candidates(root: Path, paths: list[Path]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[str]]:
    receipt_paths = [path for path in paths if atlas_relative(path, root=root).startswith("docs/ops/") and path.suffix.lower() == ".md"]
    source_refs = [atlas_relative(path, root=root) for path in receipt_paths]
    grouped: dict[str, OrderedDict[str, Any]] = {}
    for path in receipt_paths:
        key = _receipt_key(path)
        ref = atlas_relative(path, root=root)
        for family, category, pattern, summary in FAMILY_RULES:
            if not _pattern_matches(pattern, key):
                continue
            if family not in grouped:
                grouped[family] = OrderedDict(
                    [
                        ("id", family),
                        ("title", _candidate_title(family)),
                        ("category", category),
                        ("supporting_receipts", []),
                        ("pattern_summary", summary),
                    ]
                )
            grouped[family]["supporting_receipts"].append(ref)

    candidates: list[OrderedDict[str, Any]] = []
    rejected: list[OrderedDict[str, Any]] = []
    for family in sorted(grouped):
        row = grouped[family]
        supporting_receipts = sorted(set(row["supporting_receipts"]))
        repeat_count = len(supporting_receipts)
        base = OrderedDict(
            [
                ("id", row["id"]),
                ("title", row["title"]),
                ("category", row["category"]),
                ("status", "admitted" if repeat_count >= 2 else "rejected"),
                ("supporting_receipts", supporting_receipts),
                ("pattern_summary", row["pattern_summary"]),
                ("repeat_count", repeat_count),
                ("recommended_next_packet", _recommended_next_packet(family) if repeat_count >= 2 else None),
                ("boundaries", _candidate_boundaries()),
                ("rejection_reason", None if repeat_count >= 2 else "fewer_than_two_committed_receipts"),
            ]
        )
        if repeat_count >= 2:
            candidates.append(base)
        else:
            rejected.append(base)

    candidates.sort(key=lambda item: (CATEGORY_ORDER.index(str(item["category"])), str(item["id"])))
    rejected.sort(key=lambda item: (str(item["category"]), str(item["id"])))
    return candidates, rejected, source_refs


def build_report(*, root: Path, source_refs: list[str] | None = None) -> OrderedDict[str, Any]:
    branch, head = _branch_state(root)
    paths, blockers = _resolve_source_paths(root, source_refs or [])
    candidates: list[OrderedDict[str, Any]] = []
    rejected: list[OrderedDict[str, Any]] = []
    source_ref_output: list[str] = []
    warnings: list[OrderedDict[str, Any]] = []
    if not blockers:
        candidates, rejected, source_ref_output = extract_candidates(root, paths)
        if not candidates:
            warnings.append(_finding("no_repeated_candidates", "No repeated committed receipt-backed automation candidates were admitted."))
    else:
        source_ref_output = [_normalized_relative(ref) for ref in source_refs or []]

    status = STATUS_BLOCKER if blockers else (STATUS_OK if candidates else STATUS_ADVISORY_GAP)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch),
            ("head", head),
            ("source_refs", source_ref_output if source_refs else ["docs/ops"]),
            ("candidate_count", len(candidates)),
            ("candidates", candidates),
            ("rejected_candidates", rejected),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", not blockers),
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
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Candidates: {report.get('candidate_count')}",
            f"Rejected candidates: {len(report.get('rejected_candidates') or [])}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only receipt-derived automation candidate extractor.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--source-ref", action="append", default=[], help="Root-relative admitted source ref to inspect.")
    parser.add_argument("--output", help="Optional root-relative tmp/** JSON output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, source_refs=args.source_ref)
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
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
                ("source_refs", []),
                ("candidate_count", 0),
                ("candidates", []),
                ("rejected_candidates", []),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Extractor failed before classification.", severity="blocker", exception=str(exc))]),
                ("safe_to_use", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
