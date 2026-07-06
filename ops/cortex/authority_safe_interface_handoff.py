from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.cortex.authority-safe-interface-handoff.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
SCOPES = {"research", "root"}

DEFAULT_SOURCE_REFS = (
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
    "docs/standards/WORKER-ORCHESTRATION.md",
    "docs/PLAYBOOK_NOTES.md",
    "docs/atlas-book/01-current-state.md",
    "docs/atlas-book/02-lanes-and-markers.md",
    "docs/atlas-book/05-receipt-index.md",
    "docs/atlas-book/12-restart-and-handoff-guide.md",
    "docs/memory/profiles/zachariah_workflow_profile.md",
    "docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json",
    "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-CONTRACT-FREEZE-2026-07-06.md",
    "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md",
    "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-06.md",
    "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-06.md",
    "ops/atlas/playbook_adoption_matrix.py",
    "ops/cortex/worker_prompt.py",
    "runtime/cortex/worker-prompts/latest.json",
    "runtime/receipts/validation/stack-validation.latest.json",
    "stack.lock.yaml",
)

ALLOWED_EXACT_SOURCE_REFS = set(DEFAULT_SOURCE_REFS)
ALLOWED_SOURCE_PREFIXES = (
    "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-",
)
PROTECTED_PREFIXES = (
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "runtime",
    "secrets",
)
AUTHORITY_DENIALS = (
    "execution",
    "approval",
    "owner-truth",
    "final-receipt",
    "deploy",
    "secret-handling",
    "transcript-scraping",
    "automatic-_stack-dispatch",
    "repo-mutation",
    "platform-mutation",
)
FORBIDDEN_SURFACES = (
    "repos/**",
    "archive/**",
    ".vercel/**",
    ".playwright-mcp/**",
    "secrets/**",
    ".env*",
    "deployment outputs",
    "owner-repo receipts",
    "runtime writeback outside explicit later admission",
    "final Lifeline receipts",
)


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


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


def collect_git_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _relative_ref(path: Path, root: Path) -> str | None:
    try:
        return normalize_slashes(str(path.resolve().relative_to(root.resolve())))
    except ValueError:
        return None


def _normalized_source_ref(source: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    candidate = Path(source)
    if candidate.is_absolute():
        try:
            ref = normalize_slashes(str(candidate.resolve().relative_to(root.resolve())))
        except ValueError:
            return None, _finding("source_outside_root", "Source path must stay inside the ATLAS root.", path=normalize_slashes(str(candidate)))
    else:
        ref = normalize_slashes(str(candidate)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("source_parent_traversal", "Source path must not use parent traversal.", path=ref)
    if ref.startswith("repos/"):
        return None, _finding("owner_repo_source_forbidden", "Owner repo paths are not admitted source surfaces.", path=ref)
    if "transcript" in ref.lower() or "runtime/atlas/conversations" in ref.lower() or "runtime/atlas/sessions" in ref.lower():
        return None, _finding("transcript_source_forbidden", "Transcript or hidden chat/session state is not an admitted source.", path=ref)
    if not is_allowed_source_ref(ref):
        return None, _finding("source_not_admitted", "Source path is outside the admitted authority-safe interface source set.", path=ref)
    return ref, None


def is_allowed_source_ref(ref: str) -> bool:
    if ref in ALLOWED_EXACT_SOURCE_REFS:
        return True
    return ref.startswith(ALLOWED_SOURCE_PREFIXES) and ref.endswith(".md")


def resolve_sources(root: Path, requested_sources: list[str]) -> tuple[list[str], list[OrderedDict[str, Any]]]:
    errors: list[OrderedDict[str, Any]] = []
    refs: list[str] = []
    seen: set[str] = set()
    candidates = requested_sources or list(DEFAULT_SOURCE_REFS)
    for source in candidates:
        ref, error = _normalized_source_ref(source, root)
        if error is not None:
            errors.append(error)
            continue
        if ref is not None and ref not in seen:
            refs.append(ref)
            seen.add(ref)
    return refs, errors


def consume_surfaces(root: Path, source_refs: list[str]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    consumed: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []
    for ref in source_refs:
        path = (root / ref).resolve()
        if not path.exists() or not path.is_file():
            warnings.append(_finding("source_missing", "Admitted source path is missing.", path=ref))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        consumed.append(
            OrderedDict(
                [
                    ("ref", ref),
                    ("byte_count", len(text.encode("utf-8"))),
                    ("read_only", True),
                ]
            )
        )
    return consumed, warnings


def read_validation(root: Path) -> tuple[OrderedDict[str, int], OrderedDict[str, Any] | None]:
    path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    counts = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    if not path.exists():
        return counts, _finding("validation_missing", "Stack validation receipt is unavailable.", path=atlas_relative(path, root=root))
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return counts, _finding("validation_summary_missing", "Stack validation summary is unavailable.", path=atlas_relative(path, root=root))
    for key in counts:
        counts[key] = int(summary.get(key, 0) or 0)
    return counts, None


def validate_output_path(root: Path, output: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(output)
    if candidate.is_absolute():
        return None, _finding("absolute_output_path", "Output path must be root-relative.", path=normalize_slashes(str(candidate)))
    ref = normalize_slashes(str(candidate)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", path=ref)
    first = ref.split("/", 1)[0]
    filename = ref.rsplit("/", 1)[-1]
    if first in PROTECTED_PREFIXES or first.startswith(".env") or filename.startswith(".env"):
        return None, _finding("protected_output_path", "Output path targets a protected or forbidden surface.", path=ref)
    if not ref.startswith("tmp/"):
        return None, _finding("non_tmp_output_path", "Output path must be under tmp/** for this helper.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", path=ref)
    return resolved, None


def build_handoff_report(*, root: Path | None = None, scope: str = "root", sources: list[str] | None = None) -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []

    if scope not in SCOPES:
        blockers.append(_finding("invalid_scope", "Scope must be root or research.", scope=scope))

    branch, head = collect_git_state(base)
    source_refs, source_errors = resolve_sources(base, list(sources or []))
    blockers.extend(source_errors)
    consumed_surfaces, source_warnings = consume_surfaces(base, source_refs)
    warnings.extend(source_warnings)
    validation_counts, validation_error = read_validation(base)
    if validation_error is not None:
        warnings.append(validation_error)

    if validation_counts["critical"] or validation_counts["error"]:
        blockers.append(
            _finding(
                "validation_not_safe",
                "Stack validation has critical or error findings; advisory handoff is not safe to use.",
                critical=validation_counts["critical"],
                error=validation_counts["error"],
            )
        )

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY

    safe_to_use = status == STATUS_OK
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(base))),
            ("branch", branch),
            ("head", head),
            ("source_refs", source_refs),
            ("consumed_surfaces", consumed_surfaces),
            (
                "handoff_payload",
                OrderedDict(
                    [
                        ("scope", scope),
                        ("contract", "authority_safe_cortex_interface_widening.v1"),
                        ("recommended_next_packet", "Playbook Everywhere + Cortex Interface authority-safe Cortex interface widening first-implementation worker cluster reconciliation"),
                        ("advisory_only", True),
                        ("execution_authorized", False),
                        ("owner_repo_mutation_authorized", False),
                        ("final_receipt_authorized", False),
                        ("validation", validation_counts),
                    ]
                ),
            ),
            ("authority_denials", list(AUTHORITY_DENIALS)),
            ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", safe_to_use),
        ]
    )


def render_summary(report: OrderedDict[str, Any]) -> str:
    return "\n".join(
        [
            "Authority-Safe Cortex Interface Handoff",
            f"Status: {report['status']}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Sources consumed: {len(report.get('consumed_surfaces', []))}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
            "Authority: advisory only; no execution, owner-truth, deploy, secret, _stack dispatch, or final-receipt authority.",
        ]
    ) + "\n"


def exit_code(status: str, *, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only authority-safe Cortex interface handoff.")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument("--scope", choices=sorted(SCOPES), default="root")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    root = atlas_root().resolve()
    try:
        report = build_handoff_report(root=root, scope=args.scope, sources=list(args.source or []))
        if args.output:
            resolved_output, output_error = validate_output_path(root, args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(render_summary(report), end="")
        return exit_code(str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("source_refs", []),
                ("consumed_surfaces", []),
                ("handoff_payload", OrderedDict()),
                ("authority_denials", list(AUTHORITY_DENIALS)),
                ("forbidden_surfaces", list(FORBIDDEN_SURFACES)),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Authority-safe handoff failed before completion.", exception=str(exc))]),
                ("safe_to_use", False),
            ]
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(render_summary(report), end="")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
