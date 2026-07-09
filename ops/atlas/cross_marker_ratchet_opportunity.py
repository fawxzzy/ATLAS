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

SCHEMA_VERSION = "atlas.cross_marker_ratchet_opportunity.v1"

STATUS_OK = "ok"
STATUS_NO_OPPORTUNITIES = "no_opportunities"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

BLOCKER_DOCS_ONLY = "docs_only_receipt"
BLOCKER_OWNER_LANE = "owner_lane_evidence_only"
BLOCKER_PROTECTED = "protected_surface_required"
BLOCKER_UNCOMMITTED = "uncommitted_evidence"
BLOCKER_MISSING_RECEIPT = "missing_receipt"
BLOCKER_MISSING_MANIFEST = "missing_manifest"
BLOCKER_CONFLICTING_MARKER = "conflicting_marker_truth"
BLOCKER_OWNER_MUTATION = "requires_owner_mutation"
BLOCKER_DEPLOY_SECRET = "requires_deploy_or_secret"
BLOCKER_WORKFLOW = "requires_workflow_authority"

DOCS_ONLY_FILENAME_TOKENS = (
    "NEXT-SLICE-SELECTION",
    "CONTRACT-FREEZE",
    "FIRST-IMPLEMENTATION-ADMISSION",
    "PROMPT-PACK",
    "HANDOFF-CONTRACT",
    "IMPLEMENTATION-READINESS",
    "WORKER-ROUTING",
)

IMPLEMENTATION_BACKED_TOKENS = (
    "WORKER-CLUSTER-RECONCILIATION",
    "FIRST-IMPLEMENTATION-WORKER",
)

ALLOWED_SOURCE_PREFIXES = (
    "docs/ops/",
    "docs/atlas-book/",
    "docs/memory/initiatives/",
    "docs/architecture/",
    "docs/standards/",
    "docs/PLAYBOOK_NOTES.md",
)

OWNER_LANE_PREFIXES = (
    "repos/",
)

PROTECTED_PREFIXES = (
    ".playwright-mcp/",
    ".vercel/",
    "archive/",
    "secrets/",
)

WORKFLOW_PREFIXES = (
    ".github/workflows/",
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

OWNER_LANE_EXCLUSIONS = [
    "Fitness app work stays in the Fitness owner lane.",
    "Mazer game work stays in the Mazer owner lane.",
    "Playbook owner-repo work requires a separate owner-side packet.",
    "Owner-repo receipts are advisory only unless committed into ATLAS root governance receipts.",
]

PROTECTED_SURFACE_EXCLUSIONS = [
    "repos/**",
    "secrets/**",
    ".env*",
    ".vercel/**",
    ".playwright-mcp/**",
    "archive/**",
    ".github/workflows/**",
    "deploy/platform outputs",
    "hidden transcript/chat/session state",
]

AUTHORITY_DENIALS = [
    "marker_write_authority_denied",
    "final_receipt_authority_denied",
    "owner_repo_mutation_denied",
    "workflow_edit_or_dispatch_denied",
    "secret_or_deploy_authority_denied",
    "protected_surface_access_denied",
    "cortex_execution_authority_denied",
    "playbook_owner_truth_authority_denied",
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


def _normal(value: str | Path) -> str:
    return normalize_slashes(str(value)).strip("/")


def _path_contains_env(relative_path: str) -> bool:
    return any(part.startswith(".env") for part in _normal(relative_path).split("/"))


def _blocked_candidate(
    source_receipt: str,
    candidate_marker: str,
    blocker_class: str,
    reason: str,
    required_unblock: str,
) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("source_receipt", source_receipt),
            ("candidate_marker", candidate_marker),
            ("blocker_class", blocker_class),
            ("reason", reason),
            ("required_unblock", required_unblock),
        ]
    )


def _source_ref_blocker(relative_path: str) -> tuple[str, str, str] | None:
    normalized = _normal(relative_path)
    if not normalized:
        return (BLOCKER_MISSING_RECEIPT, "Source ref is empty.", "Provide a root-relative admitted source ref.")
    if _path_contains_env(normalized) or normalized.startswith("secrets/"):
        return (BLOCKER_DEPLOY_SECRET, "Source ref would require secret handling.", "Use committed non-secret ATLAS governance receipts only.")
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in OWNER_LANE_PREFIXES):
        return (BLOCKER_OWNER_LANE, "Owner-lane source refs are not admitted as direct proof.", "Commit a bounded ATLAS root governance receipt or run a separate owner-lane packet.")
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in WORKFLOW_PREFIXES):
        return (BLOCKER_WORKFLOW, "Workflow source refs imply workflow authority.", "Use a committed governance receipt that records workflow proof without editing or dispatching workflows.")
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return (BLOCKER_PROTECTED, "Source ref points at a protected surface.", "Use a committed ATLAS root governance receipt.")
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in HIDDEN_CONTEXT_PREFIXES):
        return (BLOCKER_PROTECTED, "Hidden transcript or session state is not admitted.", "Use durable committed receipts only.")
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in DEPLOY_OR_PLATFORM_PREFIXES):
        return (BLOCKER_DEPLOY_SECRET, "Deploy or platform surfaces are not admitted.", "Use a committed receipt that records bounded proof.")
    if normalized.startswith("runtime/"):
        return (BLOCKER_UNCOMMITTED, "Runtime latest files are not committed proof.", "Record durable receipt-backed proof first.")
    if not any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in ALLOWED_SOURCE_PREFIXES):
        return (BLOCKER_MISSING_RECEIPT, "Source ref is outside admitted ATLAS root inputs.", "Use docs/ops, docs/atlas-book, or continuity manifest inputs.")
    return None


def validate_source_ref(*, root: Path, source_ref: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(source_ref)
    if candidate.is_absolute():
        return None, _blocked_candidate(
            normalize_slashes(str(candidate)),
            "unknown",
            BLOCKER_PROTECTED,
            "Absolute source paths are not admitted.",
            "Use a root-relative committed ATLAS governance source.",
        )
    normalized = _normal(candidate)
    if ".." in Path(normalized).parts:
        return None, _blocked_candidate(
            normalized,
            "unknown",
            BLOCKER_PROTECTED,
            "Parent traversal is not admitted.",
            "Use a root-relative committed ATLAS governance source.",
        )
    source_blocker = _source_ref_blocker(normalized)
    if source_blocker is not None:
        blocker_class, reason, required_unblock = source_blocker
        return None, _blocked_candidate(normalized, "unknown", blocker_class, reason, required_unblock)
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _blocked_candidate(
            normalized,
            "unknown",
            BLOCKER_PROTECTED,
            "Resolved source path escapes the ATLAS root.",
            "Use an admitted root-relative source.",
        )
    if not resolved.exists():
        blocker_class = BLOCKER_MISSING_MANIFEST if normalized.endswith(".json") and "continuity-manifest-" in normalized else BLOCKER_MISSING_RECEIPT
        return None, _blocked_candidate(
            normalized,
            "unknown",
            blocker_class,
            "Source ref does not exist.",
            "Create or cite the durable committed source before using it as proof.",
        )
    return resolved, None


def validate_output_path(*, root: Path, output_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return None, _blocked_candidate(
            normalize_slashes(str(candidate)),
            "unknown",
            BLOCKER_PROTECTED,
            "Output path must be root-relative.",
            "Write only to an explicit tmp/**.json output path.",
        )
    normalized = _normal(candidate)
    if ".." in Path(normalized).parts:
        return None, _blocked_candidate(
            normalized,
            "unknown",
            BLOCKER_PROTECTED,
            "Output path must not use parent traversal.",
            "Write only to an explicit tmp/**.json output path.",
        )
    if not normalized.startswith("tmp/") or not normalized.endswith(".json"):
        return None, _blocked_candidate(
            normalized,
            "unknown",
            BLOCKER_PROTECTED,
            "Output writes are admitted only to root-relative tmp/**.json.",
            "Use a tmp/**.json output path or omit --output.",
        )
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _blocked_candidate(
            normalized,
            "unknown",
            BLOCKER_PROTECTED,
            "Resolved output path escapes the ATLAS root.",
            "Use a tmp/**.json output path inside ATLAS.",
        )
    return resolved, None


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _manifest_marker(manifest: dict[str, Any]) -> tuple[str, int | None]:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    posture = metadata.get("marker_posture") if isinstance(metadata.get("marker_posture"), list) else []
    for item in posture:
        if isinstance(item, dict) and item.get("marker"):
            percent = item.get("percent")
            return str(item["marker"]), int(percent) if isinstance(percent, int) else None
    return str(manifest.get("title") or manifest.get("id") or "unknown"), None


def _next_packet(metadata: dict[str, Any]) -> str:
    ladder = metadata.get("next_package_ladder") if isinstance(metadata.get("next_package_ladder"), list) else []
    if ladder and isinstance(ladder[0], dict):
        return str(ladder[0].get("package") or "")
    return ""


def _surface_paths(value: Any) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                refs.append((item, "manifest reference"))
            elif isinstance(item, dict):
                path = item.get("path")
                if isinstance(path, str):
                    refs.append((path, str(item.get("role") or "manifest surface")))
    return refs


def _manifest_refs(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    refs: list[tuple[str, str]] = []
    current = metadata.get("current_checkpoint_receipt")
    if isinstance(current, str):
        refs.append((current, "current checkpoint receipt"))
    refs.extend(_surface_paths(manifest.get("evidence_refs")))
    refs.extend(_surface_paths(metadata.get("governing_receipts")))
    refs.extend(_surface_paths(metadata.get("owner_truth_surfaces")))
    refs.extend(_surface_paths(metadata.get("verification_adoption_surfaces")))
    seen: set[str] = set()
    ordered: list[tuple[str, str]] = []
    for path, role in refs:
        normalized = _normal(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append((normalized, role))
    return ordered


def _is_docs_only_receipt(path: str, role: str = "") -> bool:
    basename = Path(path).name.upper()
    role_lower = role.lower()
    return any(token in basename for token in DOCS_ONLY_FILENAME_TOKENS) or any(
        token in role_lower
        for token in (
            "docs-only",
            "selector",
            "contract freeze",
            "first-implementation admission",
            "prompt-pack",
            "implementation-readiness",
        )
    )


def _is_implementation_backed(path: str, role: str = "") -> bool:
    basename = Path(path).name.upper()
    role_lower = role.lower()
    return any(token in basename for token in IMPLEMENTATION_BACKED_TOKENS) or "implementation-backed" in role_lower


def _receipt_authority_blocker(path: str, text: str) -> tuple[str, str, str] | None:
    combined = f"{path} {text}".lower()
    filename = Path(path).name.upper()
    if "OWNER-REPO-MUTATION" in filename or "requires owner mutation" in combined:
        return (BLOCKER_OWNER_MUTATION, "Proof would require owner-repo mutation.", "Route a separate owner-side packet or cite a root receipt proving no owner mutation.")
    if "requires workflow" in combined or "workflow dispatch required" in combined:
        return (BLOCKER_WORKFLOW, "Proof would require workflow authority.", "Use a committed receipt that records proof without workflow edit or dispatch authority.")
    if "requires secret" in combined or "requires deploy" in combined or "deploy required" in combined:
        return (BLOCKER_DEPLOY_SECRET, "Proof would require deploy or secret authority.", "Use an admitted receipt that does not require deploy, platform, or secret handling.")
    return None


def _load_manifests(root: Path, source_refs: list[str]) -> tuple[list[dict[str, Any]], list[OrderedDict[str, Any]], set[str] | None]:
    blockers: list[OrderedDict[str, Any]] = []
    selected_manifest_refs: set[str] | None = None
    if source_refs:
        selected_manifest_refs = set()
        for source_ref in source_refs:
            normalized = _normal(source_ref)
            resolved, error = validate_source_ref(root=root, source_ref=source_ref)
            if error is not None:
                blockers.append(error)
                continue
            if resolved is not None and resolved.suffix.lower() == ".json" and "continuity-manifest-" in resolved.name:
                selected_manifest_refs.add(normalized)
    manifest_paths = sorted((root / "docs" / "memory" / "initiatives").glob("continuity-manifest-*.json"))
    manifests: list[dict[str, Any]] = []
    for path in manifest_paths:
        relative = _normal(path.relative_to(root))
        if selected_manifest_refs is not None and selected_manifest_refs and relative not in selected_manifest_refs:
            continue
        payload = _load_json(path)
        if payload is None:
            blockers.append(
                _blocked_candidate(
                    relative,
                    "unknown",
                    BLOCKER_MISSING_MANIFEST,
                    "Continuity manifest is missing or malformed.",
                    "Repair the manifest before using it as cross-marker proof input.",
                )
            )
            continue
        manifests.append(payload)
    return manifests, blockers, selected_manifest_refs


def _manifest_marker_conflicts(manifest: dict[str, Any]) -> list[OrderedDict[str, Any]]:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    posture = metadata.get("marker_posture") if isinstance(metadata.get("marker_posture"), list) else []
    seen: dict[str, int] = {}
    blockers: list[OrderedDict[str, Any]] = []
    for item in posture:
        if not isinstance(item, dict):
            continue
        marker = item.get("marker")
        percent = item.get("percent")
        if not isinstance(marker, str) or not isinstance(percent, int):
            continue
        if marker in seen and seen[marker] != percent:
            blockers.append(
                _blocked_candidate(
                    str(metadata.get("current_checkpoint_receipt") or manifest.get("id") or "unknown"),
                    marker,
                    BLOCKER_CONFLICTING_MARKER,
                    "Manifest contains conflicting marker posture values.",
                    "Reconcile marker posture before using this manifest for ratchet opportunity detection.",
                )
            )
        seen[marker] = percent
    return blockers


def _build_receipt_index(manifests: list[dict[str, Any]]) -> dict[str, list[OrderedDict[str, Any]]]:
    index: dict[str, list[OrderedDict[str, Any]]] = {}
    for manifest in manifests:
        marker, percent = _manifest_marker(manifest)
        metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
        next_packet = _next_packet(metadata)
        for path, role in _manifest_refs(manifest):
            if not path.startswith("docs/ops/"):
                continue
            index.setdefault(path, []).append(
                OrderedDict(
                    [
                        ("marker", marker),
                        ("percent", percent),
                        ("manifest_id", str(manifest.get("id") or "")),
                        ("role", role),
                        ("current_checkpoint", metadata.get("current_checkpoint_receipt")),
                        ("next_packet", next_packet),
                    ]
                )
            )
    return index


def _marker_contexts(manifests: list[dict[str, Any]]) -> dict[str, OrderedDict[str, Any]]:
    contexts: dict[str, OrderedDict[str, Any]] = {}
    for manifest in manifests:
        marker, percent = _manifest_marker(manifest)
        metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
        contexts[marker] = OrderedDict(
            [
                ("marker", marker),
                ("percent", percent),
                ("manifest_id", str(manifest.get("id") or "")),
                ("role", "marker continuity manifest"),
                ("current_checkpoint", metadata.get("current_checkpoint_receipt")),
                ("next_packet", _next_packet(metadata)),
            ]
        )
    return contexts


def _source_manifest_for(path: str, entries: list[OrderedDict[str, Any]]) -> OrderedDict[str, Any]:
    for entry in entries:
        if entry.get("current_checkpoint") == path:
            return entry
    for entry in entries:
        if "worker-cluster reconciliation" in str(entry.get("role") or "").lower():
            return entry
    return entries[0]


def _receipt_reference_opportunities(
    *,
    root: Path,
    path: str,
    source_entry: OrderedDict[str, Any],
    marker_contexts: dict[str, OrderedDict[str, Any]],
) -> list[OrderedDict[str, Any]]:
    opportunities: list[OrderedDict[str, Any]] = []
    playbook_context = marker_contexts.get("Playbook Everywhere + Cortex Interface")
    if playbook_context is None:
        return opportunities
    for receipt_path in sorted((root / "docs" / "ops").glob("PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-*.md")):
        relative = _normal(receipt_path.relative_to(root))
        try:
            text = receipt_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lowered = text.lower()
        if path not in text:
            continue
        if "PROOF-RECONCILIATION" not in receipt_path.name.upper():
            continue
        if "second implementation-backed consumer class" not in lowered:
            continue
        candidate_entry = OrderedDict(playbook_context)
        candidate_entry["role"] = f"referenced by {relative}: second implementation-backed consumer class proof"
        opportunities.append(_opportunity(path, source_entry, candidate_entry))
    return opportunities


def _opportunity(path: str, source_entry: OrderedDict[str, Any], candidate_entry: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
    required_packet = str(candidate_entry.get("next_packet") or "No immediate same-lane packet")
    return OrderedDict(
        [
            ("source_receipt", path),
            ("source_marker", source_entry.get("marker")),
            ("candidate_marker", candidate_entry.get("marker")),
            ("candidate_marker_percent", candidate_entry.get("percent")),
            ("evidence_class", "implementation_backed_cross_marker_proof"),
            (
                "ratchet_condition_refs",
                [
                    str(candidate_entry.get("current_checkpoint") or path),
                    "docs/PLAYBOOK_NOTES.md#marker-ratchet-threshold",
                ],
            ),
            ("reuse_basis", candidate_entry.get("role")),
            (
                "limits",
                [
                    "advisory_only",
                    "does_not_move_markers",
                    "does_not_emit_final_receipts",
                    "does_not_grant_owner_truth_or_execution_authority",
                ],
            ),
            ("required_follow_up_packet", required_packet),
            ("safe_to_use", True),
        ]
    )


def _blocked_for_receipt(path: str, marker: str, role: str, text: str) -> OrderedDict[str, Any] | None:
    if _is_docs_only_receipt(path, role):
        return _blocked_candidate(
            path,
            marker,
            BLOCKER_DOCS_ONLY,
            "Receipt is selector, contract, admission, prompt-pack, readiness, or wording evidence only.",
            "Land implementation-backed proof before treating this as cross-marker ratchet evidence.",
        )
    authority_blocker = _receipt_authority_blocker(path, text)
    if authority_blocker is not None:
        blocker_class, reason, required_unblock = authority_blocker
        return _blocked_candidate(path, marker, blocker_class, reason, required_unblock)
    return None


def _selected_receipts_from_sources(root: Path, source_refs: list[str]) -> tuple[set[str] | None, list[OrderedDict[str, Any]]]:
    if not source_refs:
        return None, []
    blockers: list[OrderedDict[str, Any]] = []
    selected: set[str] = set()
    for source_ref in source_refs:
        normalized = _normal(source_ref)
        resolved, error = validate_source_ref(root=root, source_ref=source_ref)
        if error is not None:
            blockers.append(error)
            continue
        if resolved is None:
            continue
        if resolved.suffix.lower() == ".md" and normalized.startswith("docs/ops/"):
            selected.add(normalized)
    return selected, blockers


def _default_receipt_paths(receipt_index: dict[str, list[OrderedDict[str, Any]]]) -> list[str]:
    paths: list[str] = []
    for path, entries in receipt_index.items():
        if "CROSS-MARKER-RATCHET-OPPORTUNITY" in path:
            paths.append(path)
            continue
        if any(entry.get("current_checkpoint") == path and _is_implementation_backed(path, str(entry.get("role") or "")) for entry in entries):
            paths.append(path)
    return sorted(paths)


def build_report(*, root: Path, source_refs: list[str] | None = None) -> OrderedDict[str, Any]:
    refs = list(source_refs or [])
    basis_commit = _git_stdout(root, "rev-parse", "HEAD")
    manifests, manifest_blockers, selected_manifest_refs = _load_manifests(root, refs)
    selected_receipts, source_blockers = _selected_receipts_from_sources(root, refs)
    hard_blockers: list[OrderedDict[str, Any]] = manifest_blockers + source_blockers

    for manifest in manifests:
        hard_blockers.extend(_manifest_marker_conflicts(manifest))

    receipt_index = _build_receipt_index(manifests)
    marker_contexts = _marker_contexts(manifests)
    receipt_paths = _default_receipt_paths(receipt_index)
    if selected_receipts is not None:
        receipt_paths = sorted(path for path in selected_receipts if path in receipt_index)

    source_receipts: list[str] = []
    opportunities: list[OrderedDict[str, Any]] = []
    blocked_candidates: list[OrderedDict[str, Any]] = []

    for path in receipt_paths:
        entries = receipt_index[path]
        source_receipts.append(path)
        source_entry = _source_manifest_for(path, entries)
        receipt_path = root / path
        receipt_text = receipt_path.read_text(encoding="utf-8", errors="replace") if receipt_path.exists() else ""
        blocked = _blocked_for_receipt(path, str(source_entry.get("marker") or "unknown"), str(source_entry.get("role") or ""), receipt_text)
        if blocked is not None:
            blocked_candidates.append(blocked)
            continue
        if not _is_implementation_backed(path, str(source_entry.get("role") or "")):
            continue
        for candidate_entry in entries:
            if candidate_entry.get("marker") == source_entry.get("marker"):
                continue
            candidate_marker = str(candidate_entry.get("marker") or "")
            role = str(candidate_entry.get("role") or "")
            if candidate_marker == "Playbook Everywhere + Cortex Interface" and "second" in role.lower():
                opportunities.append(_opportunity(path, source_entry, candidate_entry))
        opportunities.extend(
            _receipt_reference_opportunities(
                root=root,
                path=path,
                source_entry=source_entry,
                marker_contexts=marker_contexts,
            )
        )

    blocked_candidates.extend(hard_blockers)
    blocked_candidates = sorted(blocked_candidates, key=lambda item: (str(item.get("source_receipt")), str(item.get("candidate_marker")), str(item.get("blocker_class"))))
    opportunities = sorted(opportunities, key=lambda item: (str(item.get("source_receipt")), str(item.get("candidate_marker"))))
    source_receipts = sorted(set(source_receipts))

    explicit_receipt_mode = selected_receipts is not None
    if hard_blockers:
        status = STATUS_BLOCKED
    elif explicit_receipt_mode and blocked_candidates and not opportunities:
        status = STATUS_BLOCKED
    elif opportunities:
        status = STATUS_OK
    else:
        status = STATUS_NO_OPPORTUNITIES

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", status in {STATUS_OK, STATUS_NO_OPPORTUNITIES}),
            ("basis_commit", basis_commit),
            ("source_receipts", source_receipts),
            ("candidate_count", len(source_receipts) + len(blocked_candidates)),
            ("opportunity_count", len(opportunities)),
            ("opportunities", opportunities),
            ("blocked_candidates", blocked_candidates),
            ("authority_denials", AUTHORITY_DENIALS),
            ("owner_lane_exclusions", OWNER_LANE_EXCLUSIONS),
            ("protected_surface_exclusions", PROTECTED_SURFACE_EXCLUSIONS),
            ("marker_write_authority", False),
            ("final_receipt_authority", False),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_NO_OPPORTUNITIES:
        return 1 if strict else 0
    if status == STATUS_BLOCKED:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Basis commit: {report.get('basis_commit') or 'unknown'}",
            f"Candidates: {report.get('candidate_count')}",
            f"Opportunities: {report.get('opportunity_count')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit advisory cross-marker ratchet proof-reuse opportunities from ATLAS root receipts.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--source", action="append", default=[], help="Optional root-relative admitted source ref. May be repeated.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, source_refs=list(args.source or []))
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKED
                report["safe_to_use"] = False
                report["blocked_candidates"] = sorted(
                    list(report.get("blocked_candidates", [])) + [output_error],
                    key=lambda item: (str(item.get("source_receipt")), str(item.get("candidate_marker")), str(item.get("blocker_class"))),
                )
                report["candidate_count"] = int(report.get("candidate_count") or 0) + 1
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
                ("basis_commit", None),
                ("source_receipts", []),
                ("candidate_count", 1),
                ("opportunity_count", 0),
                ("opportunities", []),
                (
                    "blocked_candidates",
                    [
                        _blocked_candidate(
                            "internal",
                            "unknown",
                            BLOCKER_MISSING_RECEIPT,
                            "Cross-marker ratchet opportunity helper failed closed.",
                            str(exc),
                        )
                    ],
                ),
                ("authority_denials", AUTHORITY_DENIALS),
                ("owner_lane_exclusions", OWNER_LANE_EXCLUSIONS),
                ("protected_surface_exclusions", PROTECTED_SURFACE_EXCLUSIONS),
                ("marker_write_authority", False),
                ("final_receipt_authority", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
