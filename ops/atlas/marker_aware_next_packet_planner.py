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
from ops.atlas import cross_marker_ratchet_opportunity

SCHEMA_VERSION = "atlas.marker_aware_next_packet_planner.v1"

STATUS_OK = "ok"
STATUS_ADVISORY_RECOMMENDATION = "advisory_recommendation"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

CLASS_IMMEDIATE = "immediately_executable_packet"
CLASS_HELD = "held_lane"
CLASS_PROOF_GATED = "proof_gated_lane"
CLASS_OWNER_BLOCKED = "owner_lane_blocked_lane"
CLASS_EXTERNAL_PROOF = "external_proof_blocked_lane"
CLASS_STALE = "stale_packet"
CLASS_IMPLEMENTATION_READY = "implementation_ready_packet"
CLASS_DOCS_ONLY = "docs_only_packet"
CLASS_UNSAFE = "unsafe_authority_risk_packet"
CLASS_NO_ACTION = "no_action_hold"

CROSS_MARKER_SCORE_BONUS = 15

CLASS_SCORES = {
    CLASS_IMPLEMENTATION_READY: 100,
    CLASS_IMMEDIATE: 90,
    CLASS_DOCS_ONLY: 70,
    CLASS_PROOF_GATED: 40,
    CLASS_EXTERNAL_PROOF: 35,
    CLASS_OWNER_BLOCKED: 25,
    CLASS_HELD: 10,
    CLASS_STALE: 5,
    CLASS_NO_ACTION: 0,
    CLASS_UNSAFE: -100,
}

PLAYBOOK_RULE_REFS = [
    "docs/PLAYBOOK_NOTES.md#marker-ratchet-threshold",
    "docs/PLAYBOOK_NOTES.md#implementation-readiness-before-worker-routing",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md#explicit-artifact-ref-handoff",
    "docs/standards/WORKER-ORCHESTRATION.md#handoff-artifacts",
]

PATTERN_REFS = [
    "contract freeze -> first-implementation admission -> prompt-pack -> implementation-readiness -> worker reconciliation",
    "green CI is advisory until backed by an artifact or durable receipt",
    "owner lanes stay separate from ATLAS root marker progress unless explicitly admitted",
    "Cortex output is advisory substrate, not execution authority",
]

FAILURE_MODE_REFS = [
    "held lane reopened by wording instead of changed evidence",
    "owner repo drift treated as ATLAS root blocker",
    "workflow design constraint widened into workflow edit or dispatch authority",
    "green CI treated as protected proof without artifact or receipt evidence",
    "docs-only ladder continues after readiness instead of routing the bounded worker",
]

PROOF_REQUIREMENTS = [
    "deterministic JSON ordering",
    "held-lane classification",
    "proof-gated-lane classification",
    "owner-lane blocked classification",
    "external-proof blocked classification",
    "implementation-ready packet classification",
    "numbered worker packet classification",
    "docs-only packet classification",
    "unsafe authority-risk rejection",
    "Playbook refs surfaced as evidence only",
    "Cortex advisory inputs remain authority-denying",
    "non-actionable cross-marker opportunities remain advisory only",
    "actionable cross-marker opportunities can add bounded score uplift without inventing packets",
    "workflow-style candidates cannot edit .github/workflows/**",
    "optional output writes limited to explicit tmp/**.json",
    "no marker movement or final-receipt authority",
]

OWNER_LANE_BOUNDARIES = [
    "Fitness app work is an owner lane and is not mutated by this helper.",
    "Mazer game work is an owner lane and is not mutated by this helper.",
    "Playbook owner-repo work requires a separate owner-side packet.",
    "ATLAS root may read durable owner-truth mirrors but may not convert owner drift into root mutation authority.",
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


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
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
        return None, _finding(source_error, "Source ref is outside admitted marker-aware planner inputs.", severity="blocker", path=relative_path)
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


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _discover_default_sources(root: Path) -> list[Path]:
    paths = sorted((root / "docs" / "memory" / "initiatives").glob("continuity-manifest-*.json"))
    for relative in [
        "docs/PLAYBOOK_NOTES.md",
        "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
        "docs/standards/WORKER-ORCHESTRATION.md",
        "docs/atlas-book/01-current-state.md",
        "docs/atlas-book/02-lanes-and-markers.md",
        "docs/atlas-book/12-restart-and-handoff-guide.md",
    ]:
        candidate = root / relative
        if candidate.exists():
            paths.append(candidate)
    return paths


def _load_sources(*, root: Path, source_refs: list[str]) -> tuple[list[tuple[str, Path, str]], list[OrderedDict[str, Any]]]:
    blockers: list[OrderedDict[str, Any]] = []
    loaded: list[tuple[str, Path, str]] = []
    if source_refs:
        paths: list[tuple[str, Path]] = []
        for source_ref in source_refs:
            resolved, error = validate_source_ref(root=root, source_ref=source_ref)
            if error is not None:
                blockers.append(error)
                continue
            assert resolved is not None
            paths.append((_normalized_relative(source_ref), resolved))
    else:
        paths = [(normalize_slashes(str(path.relative_to(root))), path) for path in _discover_default_sources(root)]
    for source_ref, path in paths:
        try:
            loaded.append((source_ref, path, path.read_text(encoding="utf-8", errors="replace")))
        except OSError as exc:
            blockers.append(_finding("source_read_failed", "Failed to read admitted source ref.", severity="blocker", path=source_ref, error=str(exc)))
    return loaded, blockers


def _manifest_marker(manifest: dict[str, Any]) -> tuple[str | None, int | None]:
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    posture = metadata.get("marker_posture") if isinstance(metadata.get("marker_posture"), list) else []
    for item in posture:
        if isinstance(item, dict) and item.get("marker"):
            percent = item.get("percent")
            return str(item.get("marker")), int(percent) if isinstance(percent, int) else None
    title = manifest.get("title")
    return str(title) if title else None, None


def _first_next_package(metadata: dict[str, Any]) -> dict[str, Any]:
    ladder = metadata.get("next_package_ladder") if isinstance(metadata.get("next_package_ladder"), list) else []
    if ladder and isinstance(ladder[0], dict):
        return ladder[0]
    return {}


def _classify_packet(*, packet: str, mode: str, reason: str, blocked_text: str) -> str:
    text = " ".join([packet, mode, reason, blocked_text]).lower()
    authority_text = " ".join([packet, mode]).lower()
    packet_lower = packet.lower()
    mode_lower = mode.lower()
    if (
        "no immediate" in packet_lower
        or "no lane-internal" in packet_lower
        or packet_lower.startswith("none ")
        or packet_lower.startswith("no further")
        or "hold-flat" in mode_lower
        or "held after" in mode_lower
        or "closed" in mode_lower
        or "conditional reopen" in mode_lower
        or "blocked unless" in mode_lower
    ):
        return CLASS_HELD
    if "owner-lane blocked" in text or "owner-side blocker" in text:
        return CLASS_OWNER_BLOCKED
    if "proof-gated" in text or "protected proof" in text or "release-readiness" in text:
        return CLASS_PROOF_GATED
    if "external proof" in text or "browserstack" in text or "manual fallback" in text:
        return CLASS_EXTERNAL_PROOF
    if any(token in authority_text for token in [".github/workflows", "touch secrets", "secret", "deploy", "approve pr", "merge pr", "final receipt authority"]):
        return CLASS_UNSAFE
    if "stale" in text:
        return CLASS_STALE
    if (
        "first-implementation worker-cluster" in text
        or "worker packet" in packet_lower
        or "implementation worker" in mode.lower()
        or "root-local implementation worker" in text
    ):
        return CLASS_IMPLEMENTATION_READY
    if "docs-only" in mode.lower():
        return CLASS_DOCS_ONLY
    if "hold" in text:
        return CLASS_NO_ACTION
    return CLASS_IMMEDIATE


def _candidate_from_manifest(source_ref: str, manifest: dict[str, Any]) -> OrderedDict[str, Any] | None:
    metadata = manifest.get("metadata")
    if not isinstance(metadata, dict):
        return None
    marker, percent = _manifest_marker(manifest)
    if not marker:
        return None
    next_package = _first_next_package(metadata)
    packet = str(next_package.get("package") or "")
    mode = str(next_package.get("mode") or "")
    reason = str(next_package.get("reason") or "")
    blocked = metadata.get("blocked_or_gated_work") if isinstance(metadata.get("blocked_or_gated_work"), list) else []
    blocked_text = json.dumps(blocked, sort_keys=True)
    classification = _classify_packet(packet=packet, mode=mode, reason=reason, blocked_text=blocked_text)
    score = CLASS_SCORES[classification]
    return OrderedDict(
        [
            ("marker", marker),
            ("percent", percent),
            ("manifest_id", str(manifest.get("id") or "")),
            ("source_ref", source_ref),
            ("classification", classification),
            ("score", score),
            ("base_score", score),
            ("packet", packet or None),
            ("mode", mode or None),
            ("reason", reason or None),
            ("current_checkpoint_receipt", metadata.get("current_checkpoint_receipt")),
            ("safe_to_select", classification in {CLASS_IMMEDIATE, CLASS_IMPLEMENTATION_READY, CLASS_DOCS_ONLY}),
        ]
    )


def _classify_sources(sources: list[tuple[str, Path, str]]) -> list[OrderedDict[str, Any]]:
    candidates: list[OrderedDict[str, Any]] = []
    for source_ref, path, _text in sources:
        if path.suffix.lower() != ".json" or "continuity-manifest-" not in path.name:
            continue
        manifest = _load_json(path)
        if manifest is None:
            continue
        candidate = _candidate_from_manifest(source_ref, manifest)
        if candidate is not None:
            candidates.append(candidate)
    return sorted(candidates, key=lambda item: (-int(item["score"]), str(item["marker"]), str(item.get("packet") or "")))


def _is_nonheld_packet(packet: str | None) -> bool:
    if not packet:
        return False
    packet_lower = packet.lower()
    return not (
        "no immediate" in packet_lower
        or "no lane-internal" in packet_lower
        or packet_lower.startswith("none ")
        or packet_lower.startswith("no further")
    )


def _cross_marker_signal_reason(*, classification: str, follow_up_packet: str) -> str:
    if not _is_nonheld_packet(follow_up_packet):
        return "follow-up remains a hold packet, so the signal stays advisory-only"
    if classification not in {CLASS_IMMEDIATE, CLASS_IMPLEMENTATION_READY, CLASS_DOCS_ONLY}:
        return "candidate is not a safe selectable packet class, so the signal stays advisory-only"
    if classification == CLASS_IMPLEMENTATION_READY:
        return "candidate is already implementation-ready, so no cross-marker score bonus is required"
    if classification == CLASS_IMMEDIATE:
        return "candidate is already immediately executable, so no cross-marker score bonus is required"
    return "candidate already has explicit non-held next-package truth, so bounded advisory uplift is allowed"


def _cross_marker_bonus(*, classification: str, follow_up_packet: str) -> int:
    if not _is_nonheld_packet(follow_up_packet):
        return 0
    if classification == CLASS_DOCS_ONLY:
        return CROSS_MARKER_SCORE_BONUS
    return 0


def _apply_cross_marker_signals(*, root: Path, candidates: list[OrderedDict[str, Any]]) -> None:
    try:
        cross_marker_report = cross_marker_ratchet_opportunity.build_report(root=root)
    except Exception:
        return

    if cross_marker_report.get("status") != cross_marker_ratchet_opportunity.STATUS_OK:
        return
    if cross_marker_report.get("safe_to_use") is not True:
        return

    candidate_by_marker = {str(candidate.get("marker")): candidate for candidate in candidates}
    opportunities = cross_marker_report.get("opportunities")
    if not isinstance(opportunities, list):
        return

    for opportunity in opportunities:
        if not isinstance(opportunity, dict):
            continue
        marker = str(opportunity.get("candidate_marker") or "")
        candidate = candidate_by_marker.get(marker)
        if candidate is None:
            continue
        follow_up_packet = str(opportunity.get("required_follow_up_packet") or candidate.get("packet") or "")
        classification = str(candidate.get("classification") or "")
        bonus = _cross_marker_bonus(classification=classification, follow_up_packet=follow_up_packet)
        candidate["cross_marker_signal_applied"] = bonus > 0
        candidate["cross_marker_source_receipt"] = opportunity.get("source_receipt")
        candidate["cross_marker_source_marker"] = opportunity.get("source_marker")
        candidate["cross_marker_candidate_marker"] = opportunity.get("candidate_marker")
        candidate["cross_marker_required_follow_up_packet"] = opportunity.get("required_follow_up_packet")
        candidate["cross_marker_reason"] = _cross_marker_signal_reason(
            classification=classification,
            follow_up_packet=follow_up_packet,
        )
        candidate["cross_marker_score_bonus"] = bonus
        candidate["score"] = int(candidate.get("base_score") or 0) + bonus

    candidates.sort(key=lambda item: (-int(item["score"]), str(item["marker"]), str(item.get("packet") or "")))


def _selected_candidate(candidates: list[OrderedDict[str, Any]]) -> OrderedDict[str, Any] | None:
    for candidate in candidates:
        if candidate.get("safe_to_select") is True:
            return candidate
    return None


def _bucket(candidates: list[OrderedDict[str, Any]], *classes: str) -> list[OrderedDict[str, Any]]:
    selected_classes = set(classes)
    return [
        OrderedDict(
            [
                ("marker", candidate["marker"]),
                ("classification", candidate["classification"]),
                ("packet", candidate.get("packet")),
                ("reason", candidate.get("reason")),
                ("source_ref", candidate.get("source_ref")),
            ]
        )
        for candidate in candidates
        if candidate.get("classification") in selected_classes
    ]


def _authority_risks(candidates: list[OrderedDict[str, Any]], blockers: list[OrderedDict[str, Any]]) -> list[OrderedDict[str, Any]]:
    risks = [
        OrderedDict([("risk", "owner_lane_mutation"), ("mitigation", "planner rejects repos/** inputs and emits owner-lane boundaries as advisory only")]),
        OrderedDict([("risk", "secret_or_deploy_authority"), ("mitigation", "planner rejects secrets, .env*, deploy, platform, and Vercel inputs")]),
        OrderedDict([("risk", "workflow_edit_or_dispatch"), ("mitigation", "planner rejects .github/workflows/** and has no dispatch authority")]),
        OrderedDict([("risk", "marker_or_final_receipt_authority"), ("mitigation", "planner emits recommendation JSON only and cannot move markers or emit final receipts")]),
        OrderedDict([("risk", "cortex_authority_drift"), ("mitigation", "Cortex refs are scoring inputs only")]),
    ]
    for candidate in candidates:
        if candidate.get("classification") == CLASS_UNSAFE:
            risks.append(OrderedDict([("risk", "unsafe_candidate_detected"), ("mitigation", "candidate rejected from selection"), ("marker", candidate.get("marker"))]))
    for blocker in blockers:
        risks.append(OrderedDict([("risk", str(blocker.get("code") or "input_blocker")), ("mitigation", "planner fails closed until input is removed or rerouted")]))
    return risks


def build_report(*, root: Path, source_refs: list[str] | None = None) -> OrderedDict[str, Any]:
    branch = _git_stdout(root, "branch", "--show-current")
    head = _git_stdout(root, "rev-parse", "HEAD")
    loaded_sources, blockers = _load_sources(root=root, source_refs=source_refs or [])
    candidates = _classify_sources(loaded_sources)
    _apply_cross_marker_signals(root=root, candidates=candidates)
    selected = _selected_candidate(candidates)

    if blockers:
        status = STATUS_BLOCKED
    elif selected is not None:
        status = STATUS_OK
    elif candidates:
        status = STATUS_ADVISORY_RECOMMENDATION
    else:
        status = STATUS_BLOCKED
        blockers.append(_finding("no_marker_candidates", "No marker-aware next-packet candidates were found.", severity="blocker"))

    rejected_candidates = _bucket(candidates, CLASS_UNSAFE, CLASS_STALE)
    held_lanes = _bucket(candidates, CLASS_HELD, CLASS_NO_ACTION)
    proof_gated_lanes = _bucket(candidates, CLASS_PROOF_GATED, CLASS_EXTERNAL_PROOF)

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("selected_marker", selected.get("marker") if selected else None),
            ("selected_packet", selected.get("packet") if selected else None),
            ("candidate_count", len(candidates)),
            ("candidate_scores", candidates),
            ("held_lanes", held_lanes),
            ("proof_gated_lanes", proof_gated_lanes),
            ("owner_lane_boundaries", OWNER_LANE_BOUNDARIES),
            ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
            ("pattern_refs", PATTERN_REFS),
            ("failure_mode_refs", FAILURE_MODE_REFS),
            ("authority_risks", _authority_risks(candidates, blockers)),
            ("rejected_candidates", rejected_candidates),
            ("proof_requirements", PROOF_REQUIREMENTS),
            ("safe_to_continue", not blockers),
            ("blockers", blockers),
            ("branch", branch),
            ("head", head),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_RECOMMENDATION:
        return 1 if strict else 0
    if status == STATUS_BLOCKED:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Selected marker: {report.get('selected_marker') or 'none'}",
            f"Selected packet: {report.get('selected_packet') or 'none'}",
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
    parser = argparse.ArgumentParser(description="Recommend the next bounded ATLAS packet from marker, manifest, and proof-risk evidence.")
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
                ("selected_marker", None),
                ("selected_packet", None),
                ("candidate_count", 0),
                ("candidate_scores", []),
                ("held_lanes", []),
                ("proof_gated_lanes", []),
                ("owner_lane_boundaries", OWNER_LANE_BOUNDARIES),
                ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
                ("pattern_refs", PATTERN_REFS),
                ("failure_mode_refs", FAILURE_MODE_REFS),
                ("authority_risks", [OrderedDict([("risk", "internal_error"), ("mitigation", "planner failed closed before emitting a recommendation")])]),
                ("rejected_candidates", []),
                ("proof_requirements", PROOF_REQUIREMENTS),
                ("safe_to_continue", False),
                ("blockers", [_finding("internal_error", "Marker-aware next-packet planning failed.", severity="blocker", exception=str(exc))]),
                ("branch", None),
                ("head", None),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
