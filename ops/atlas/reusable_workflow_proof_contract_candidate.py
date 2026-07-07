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

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.reusable_workflow_proof_contract_candidate.v1"
STATUS_OK = "ok"
STATUS_ADVISORY_CANDIDATE = "advisory_candidate"
STATUS_DOCTRINE_GAP = "doctrine_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

DEFAULT_SOURCE_REFS = [
    "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-REUSABLE-WORKFLOW-PROOF-CONTRACT-CANDIDATE-CONTRACT-FREEZE-2026-07-07.md",
    "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-REUSABLE-WORKFLOW-PROOF-CONTRACT-CANDIDATE-FIRST-IMPLEMENTATION-ADMISSION-2026-07-07.md",
    "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-REUSABLE-WORKFLOW-PROOF-CONTRACT-CANDIDATE-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-07.md",
    "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-REUSABLE-WORKFLOW-PROOF-CONTRACT-CANDIDATE-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-07.md",
    "docs/PLAYBOOK_NOTES.md",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
    "docs/standards/WORKER-ORCHESTRATION.md",
]

ALLOWED_SOURCE_PREFIXES = (
    "docs/ops/",
    "docs/atlas-book/",
    "docs/memory/initiatives/",
    "docs/architecture/",
    "docs/standards/",
    "docs/PLAYBOOK_NOTES.md",
    "runtime/receipts/validation/",
)
PROTECTED_PREFIXES = (
    ".github/workflows/",
    ".playwright-mcp/",
    ".vercel/",
    "archive/",
    "repos/",
    "secrets/",
)
HIDDEN_CONTEXT_PREFIXES = (
    ".codex/",
    "runtime/sessions/",
    "runtime/session/",
    "runtime/transcripts/",
    "runtime/chats/",
    "tmp/transcripts/",
    "tmp/chats/",
)
DEPLOY_OR_PLATFORM_PREFIXES = (
    "deploy/",
    "deployment/",
    "platform/",
    "vercel/",
)

PLAYBOOK_RULE_REFS = [
    "docs/PLAYBOOK_NOTES.md#2026-06-04---close-receipt-package-implementation-readiness-before-worker-routing",
    "docs/PLAYBOOK_NOTES.md#2026-06-04---implementation-readiness-before-worker-routing",
    "docs/PLAYBOOK_NOTES.md#rule-do-not-promote-a-repeated-workflow-into-automation-candidacy-until-its-trigger-inputs-proof-artifact-and-fallback-path-are-all-explicit-and-stable",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md#explicit-artifact-ref-handoff",
    "docs/standards/WORKER-ORCHESTRATION.md#handoff-artifacts",
]
PATTERN_REFS = [
    "freeze first slice -> freeze proof matrix -> freeze prompt-pack -> close implementation-readiness -> route one bounded worker",
    "model workflow_call-style reuse as typed contract design before workflow implementation",
    "model workflow_dispatch-style manual proof as typed dispatch/input contract before execution",
    "require artifact-backed or receipt-backed proof instead of green-CI-only claims",
]
FAILURE_MODE_REFS = [
    "worker routing before readiness widens authority beyond the frozen slice",
    "green CI is mistaken for protected release proof without artifact or receipt evidence",
    "workflow contract design drifts into live workflow edit or dispatch authority",
    "owner repo evidence is treated as root-owned truth",
]
PROOF_REQUIREMENTS = [
    "deterministic JSON ordering",
    "workflow-style candidate classification",
    "manual-dispatch-style candidate classification",
    "artifact-backed proof candidate classification",
    "owner/protected/hidden/secret/deploy source rejection",
    "explicit tmp/** JSON output-path guard",
    "no marker authority",
]


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


def _source_ref_error(relative_path: str) -> str | None:
    normalized = _normalized_relative(relative_path)
    if not normalized:
        return "empty_source_ref"
    if _path_contains_env(normalized):
        return "secret_source_ref"
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return "protected_source_ref"
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in HIDDEN_CONTEXT_PREFIXES):
        return "hidden_context_source_ref"
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in DEPLOY_OR_PLATFORM_PREFIXES):
        return "deploy_or_platform_source_ref"
    if normalized.startswith("runtime/") and not normalized.startswith("runtime/receipts/validation/"):
        return "unadmitted_runtime_source_ref"
    if not any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in ALLOWED_SOURCE_PREFIXES):
        return "unadmitted_source_ref"
    return None


def validate_source_ref(*, root: Path, source_ref: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(source_ref)
    if candidate.is_absolute():
        return None, _finding("absolute_source_ref", "Source ref must be root-relative.", severity="blocker", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if ".." in Path(relative_path).parts:
        return None, _finding("parent_traversal_source_ref", "Source ref must not use parent traversal.", severity="blocker", path=relative_path)
    source_error = _source_ref_error(relative_path)
    if source_error is not None:
        return None, _finding(source_error, "Source ref is outside admitted reusable proof-contract inputs.", severity="blocker", path=relative_path)
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
    if not relative_path.startswith("tmp/") or not relative_path.endswith(".json"):
        return None, _finding("protected_output_path", "Output writes are admitted only to root-relative tmp/**.json.", severity="blocker", path=relative_path)
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", severity="blocker", path=relative_path)
    return resolved, None


def _branch_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current") or None, _git_stdout(root, "rev-parse", "HEAD") or None


def _load_sources(*, root: Path, source_refs: list[str]) -> tuple[list[tuple[str, str]], list[OrderedDict[str, Any]]]:
    refs = source_refs or DEFAULT_SOURCE_REFS
    loaded: list[tuple[str, str]] = []
    blockers: list[OrderedDict[str, Any]] = []
    for source_ref in refs:
        resolved, error = validate_source_ref(root=root, source_ref=source_ref)
        if error is not None:
            blockers.append(error)
            continue
        assert resolved is not None
        loaded.append((_normalized_relative(source_ref), resolved.read_text(encoding="utf-8", errors="replace")))
    return loaded, blockers


def _refs_containing(sources: list[tuple[str, str]], *needles: str) -> list[str]:
    matched: list[str] = []
    lowered_needles = [needle.lower() for needle in needles]
    for source_ref, text in sources:
        lowered = text.lower()
        if any(needle in lowered for needle in lowered_needles):
            matched.append(source_ref)
    return sorted(set(matched))


def _candidate(candidate_id: str, candidate_type: str, source_refs: list[str], proof_kind: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("candidate_id", candidate_id),
            ("classification", candidate_type),
            ("status", "implementation_ready_candidate"),
            ("source_refs", source_refs),
            ("proof_kind", proof_kind),
            ("required_contract_fields", ["typed_inputs", "secret_names_only", "permissions", "proof_artifacts_or_receipts", "stop_conditions", "authority_denials"]),
            ("authority", "advisory_contract_only"),
        ]
    )


def _build_candidates(sources: list[tuple[str, str]]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    workflow_refs = _refs_containing(sources, "workflow_call", "reusable workflow", "reusable-workflow", "reusable workflow-style")
    manual_refs = _refs_containing(sources, "workflow_dispatch", "manual dispatch", "manual/protected", "manual proof", "typed input")
    artifact_refs = _refs_containing(sources, "artifact", "receipt-backed", "artifact-backed", "proof artifact")

    workflow_candidates = [_candidate("reusable-workflow-proof-contract", "reusable_workflow_style_candidate", workflow_refs, "workflow_call_style_contract")] if workflow_refs else []
    manual_candidates = [_candidate("manual-protected-proof-contract", "workflow_dispatch_style_manual_proof_candidate", manual_refs, "workflow_dispatch_style_contract")] if manual_refs else []
    artifact_candidates = [_candidate("artifact-backed-proof-contract", "artifact_backed_proof_candidate", artifact_refs, "artifact_or_receipt_backed_proof")] if artifact_refs else []

    rejected: list[OrderedDict[str, Any]] = []
    green_ci_refs = _refs_containing(sources, "green ci", "ci is green", "current-head ci")
    for source_ref in green_ci_refs:
        source_text = next(text.lower() for ref, text in sources if ref == source_ref)
        if "artifact" not in source_text and "receipt" not in source_text and "protected proof" not in source_text:
            rejected.append(
                OrderedDict(
                    [
                        ("candidate_id", "green-ci-only-proof"),
                        ("classification", "rejected_unsafe_candidate"),
                        ("source_ref", source_ref),
                        ("rejection_reason", "green_ci_without_artifact_or_receipt_proof"),
                    ]
                )
            )

    authority_risks = [
        OrderedDict([("risk", "workflow_edit_or_dispatch"), ("mitigation", "helper emits advisory candidates only and rejects .github/workflows/** as source input")]),
        OrderedDict([("risk", "owner_truth_or_owner_mutation"), ("mitigation", "helper rejects repos/** and emits no owner truth")]),
        OrderedDict([("risk", "secret_or_deploy_authority"), ("mitigation", "helper rejects secrets, .env*, deploy, platform, and Vercel inputs")]),
        OrderedDict([("risk", "final_receipt_or_marker_claim"), ("mitigation", "helper emits no final receipt or marker authority")]),
    ]
    return workflow_candidates, manual_candidates, artifact_candidates, rejected, authority_risks


def build_report(*, root: Path, scope: str = "root", source_refs: list[str] | None = None) -> OrderedDict[str, Any]:
    branch, head = _branch_state(root)
    normalized_scope = scope.strip() or "root"
    blockers: list[OrderedDict[str, Any]] = []
    warnings: list[OrderedDict[str, Any]] = []
    if normalized_scope not in {"root", "research"}:
        blockers.append(_finding("unsupported_scope", "Scope must be root or research.", severity="blocker", scope=normalized_scope))

    sources, source_blockers = _load_sources(root=root, source_refs=source_refs or [])
    blockers.extend(source_blockers)

    workflow_candidates, manual_candidates, artifact_candidates, rejected_candidates, authority_risks = _build_candidates(sources)
    candidate_count = len(workflow_candidates) + len(manual_candidates) + len(artifact_candidates)

    doctrine_gaps: list[OrderedDict[str, Any]] = []
    loaded_refs = {source_ref for source_ref, _ in sources}
    missing_doctrine = [ref for ref in DEFAULT_SOURCE_REFS[-3:] if ref not in loaded_refs and not source_refs]
    if missing_doctrine:
        doctrine_gaps.append(_finding("missing_playbook_doctrine_refs", "One or more default Playbook doctrine refs are missing.", missing_refs=missing_doctrine))
    if not candidate_count and not blockers:
        doctrine_gaps.append(_finding("no_candidate_evidence", "No reusable workflow proof-contract candidate evidence was found."))

    if blockers:
        status = STATUS_BLOCKER
    elif doctrine_gaps:
        status = STATUS_DOCTRINE_GAP
    elif candidate_count == 3:
        status = STATUS_OK
    else:
        status = STATUS_ADVISORY_CANDIDATE

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("candidate_count", candidate_count),
            ("workflow_contract_candidates", workflow_candidates),
            ("manual_dispatch_candidates", manual_candidates),
            ("artifact_proof_candidates", artifact_candidates),
            ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
            ("pattern_refs", PATTERN_REFS),
            ("failure_mode_refs", FAILURE_MODE_REFS),
            ("doctrine_gaps", doctrine_gaps),
            ("authority_risks", authority_risks),
            ("rejected_candidates", rejected_candidates),
            ("proof_requirements", PROOF_REQUIREMENTS),
            ("safe_to_continue", not blockers),
            ("scope", normalized_scope),
            ("root", normalize_slashes(str(root))),
            ("branch", branch),
            ("head", head),
            ("source_refs", [source_ref for source_ref, _ in sources]),
            ("blockers", blockers),
            ("warnings", warnings),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status in {STATUS_OK, STATUS_ADVISORY_CANDIDATE, STATUS_DOCTRINE_GAP}:
        return 1 if strict and status != STATUS_OK else 0
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
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify reusable workflow proof-contract candidates from durable ATLAS root evidence.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--scope", choices=["root", "research"], default="root")
    parser.add_argument("--source", action="append", default=[], help="Root-relative admitted source ref. May be repeated.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, scope=args.scope, source_refs=list(args.source or []))
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_continue"] = False
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
                ("candidate_count", 0),
                ("workflow_contract_candidates", []),
                ("manual_dispatch_candidates", []),
                ("artifact_proof_candidates", []),
                ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
                ("pattern_refs", PATTERN_REFS),
                ("failure_mode_refs", FAILURE_MODE_REFS),
                ("doctrine_gaps", []),
                ("authority_risks", []),
                ("rejected_candidates", []),
                ("proof_requirements", PROOF_REQUIREMENTS),
                ("safe_to_continue", False),
                ("scope", getattr(args, "scope", "root")),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("source_refs", []),
                ("blockers", [_finding("internal_error", "Reusable workflow proof-contract candidate classification failed.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
