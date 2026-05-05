from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json
from ops.cortex.current_state import (
    default_current_state_latest_json_path,
    default_validation_receipt_path,
)
from ops.cortex.kernel import default_rule_registry_path, default_state_model_path
from ops.cortex.rail_state import load_and_classify_rail_state

RAIL_STATE_READER_CONTRACT_VERSION = "atlas.cortex.rail-state.v1"
VALIDATION_BLOCKING_SEVERITIES = {"critical", "error"}
BLOCKED_RAIL_STATUS = "blocked"
STABILIZE_FIRST_RAIL_STATUS = "stabilize-first"
READY_RAIL_STATUS = "ready"
BOUNDED_FALLBACK_RAIL_STATUS = "bounded-fallback"


def rail_state_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "rail-state"


def default_rail_state_latest_json_path(root: Path | None = None) -> Path:
    return rail_state_root(root) / "latest.json"


def default_rail_state_latest_markdown_path(root: Path | None = None) -> Path:
    return rail_state_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedRailStateArtifact:
    artifact_path: Path
    summary_path: Path | None
    payload_digest: str
    payload: dict[str, Any]
    summary: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def _require_json_object(path: Path, *, label: str) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} not found: {normalize_slashes(str(resolved))}")
    return _read_json_object(resolved)


def _normalize_counts(summary: dict[str, Any]) -> dict[str, int]:
    counts = {
        "critical": int(summary.get("critical", 0) or 0),
        "error": int(summary.get("error", 0) or 0),
        "warning": int(summary.get("warning", 0) or 0),
        "info": int(summary.get("info", 0) or 0),
    }
    counts["total"] = int(summary.get("total", sum(counts.values())) or sum(counts.values()))
    return counts


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    results: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        results.append(normalize_slashes(stripped))
    return results


def _severity_rank(value: str) -> int:
    order = {
        "critical": 0,
        "error": 1,
        "warning": 2,
        "info": 3,
    }
    return order.get(value, 99)


def _normalize_blocker(item: dict[str, Any]) -> dict[str, Any]:
    details = item.get("details")
    details_payload = details if isinstance(details, dict) else {}
    return {
        "code": str(item.get("code", "")).strip(),
        "severity": str(item.get("severity", "warning")).strip() or "warning",
        "summary": str(item.get("summary", "")).strip(),
        "source_kind": str(item.get("source_kind", "current_state")).strip() or "current_state",
        "source_ref": str(item.get("source_ref", "")).strip(),
        "details": details_payload,
    }


def _current_state_blockers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = payload.get("active_blockers")
    if not isinstance(blockers, list):
        return []
    return [_normalize_blocker(item) for item in blockers if isinstance(item, dict)]


def _validation_blockers(payload: dict[str, Any], *, validation_ref: str) -> list[dict[str, Any]]:
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return []
    blockers: list[dict[str, Any]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity", "")).strip()
        if severity not in VALIDATION_BLOCKING_SEVERITIES:
            continue
        path = str(finding.get("path", "")).strip()
        category = str(finding.get("category", "")).strip() or "validation-blocker"
        blockers.append(
            {
                "code": category,
                "severity": severity,
                "summary": str(finding.get("message", "")).strip() or "Blocking stack-validation finding.",
                "source_kind": "validation_receipt",
                "source_ref": validation_ref,
                "details": {
                    "path": normalize_slashes(path) if path else "",
                    "category": category,
                },
            }
        )
    return blockers


def _dedupe_and_sort_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for blocker in blockers:
        normalized = _normalize_blocker(blocker)
        key = json.dumps(
            [
                normalized["code"],
                normalized["severity"],
                normalized["summary"],
                normalized["source_kind"],
                normalized["source_ref"],
                normalized["details"],
            ],
            sort_keys=True,
        )
        keyed[key] = normalized
    return sorted(
        keyed.values(),
        key=lambda item: (
            _severity_rank(item["severity"]),
            item["code"],
            item["source_kind"],
            item["source_ref"],
            json.dumps(item["details"], sort_keys=True),
            item["summary"],
        ),
    )


def _unique_refs(values: list[str]) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()
    for item in values:
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        results.append(stripped)
    return results


def _load_seeded_assessment(
    *,
    root: Path,
    state_model_path: Path | None,
    rule_registry_path: Path | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    resolved_state_model = (state_model_path or default_state_model_path(root)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(root)).resolve()
    try:
        assessment = load_and_classify_rail_state(
            root=root,
            state_model_path=resolved_state_model,
            rule_registry_path=resolved_rule_registry,
        )
    except (FileNotFoundError, ValueError):
        return None, []

    summary = {
        "posture_id": assessment.posture_id,
        "classification": assessment.posture_classification,
        "rail_id": assessment.rail_id,
        "verification_status": assessment.verification_status,
        "known_validation_debt": list(assessment.known_validation_debt),
        "active_dirty_lane_ids": list(assessment.active_dirty_lane_ids),
        "matched_rule_ids": list(assessment.matched_rule_ids),
        "safe_to_proceed": assessment.safe_to_proceed,
        "next_action": {
            "action_id": assessment.next_action.action_id,
            "owner_layer": assessment.next_action.owner_layer,
            "title": assessment.next_action.title,
            "rationale": assessment.next_action.rationale,
            "required_inputs": list(assessment.next_action.required_inputs),
            "verification_plan": list(assessment.next_action.verification_plan),
            "receipt_scope": assessment.next_action.receipt_scope,
        },
        "boundary_reminders": list(assessment.boundary_reminders),
    }
    refs = [
        atlas_relative(resolved_state_model, root=root),
        atlas_relative(resolved_rule_registry, root=root),
    ]
    return summary, refs


def _validation_posture_status(counts: dict[str, int]) -> str:
    if counts["critical"] > 0 or counts["error"] > 0:
        return "blocking-findings"
    if counts["warning"] > 0 or counts["info"] > 0:
        return "ambient-debt-only"
    return "clean"


def _dirty_lanes(
    *,
    blockers: list[dict[str, Any]],
    seeded_rail_state: dict[str, Any] | None,
    current_rail_state: dict[str, Any] | None,
) -> list[str]:
    lanes: list[str] = []
    if any(item["source_kind"] == "validation_receipt" for item in blockers):
        lanes.append("stabilize-stack-validation")
    if any(item["code"] == "dirty-worktree" for item in blockers):
        lanes.append("stabilize-root-worktree")

    seeded_ids = []
    if isinstance(seeded_rail_state, dict):
        seeded_ids = seeded_rail_state.get("active_dirty_lane_ids") or []
    elif isinstance(current_rail_state, dict):
        seeded_ids = current_rail_state.get("active_dirty_lane_ids") or []

    for item in seeded_ids:
        if not isinstance(item, str):
            continue
        lane_id = item.strip()
        if lane_id and lane_id not in lanes:
            lanes.append(lane_id)
    return lanes


def _next_lane(
    *,
    blockers: list[dict[str, Any]],
    current_payload: dict[str, Any],
    seeded_rail_state: dict[str, Any] | None,
    validation_ref: str,
    current_state_ref: str,
) -> dict[str, Any]:
    if any(item["source_kind"] == "validation_receipt" for item in blockers):
        blocked_by = [item["code"] for item in blockers]
        return {
            "lane_id": "stabilize-stack-validation",
            "owner_layer": "atlas",
            "rationale": "Blocking stack-validation findings remain active, so the rail must stabilize validation before new Cortex work proceeds.",
            "blocked_by": blocked_by,
            "source_refs": [validation_ref],
        }
    if any(item["code"] == "dirty-worktree" for item in blockers):
        blocked_by = [item["code"] for item in blockers]
        return {
            "lane_id": "stabilize-root-worktree",
            "owner_layer": "atlas",
            "rationale": "The root worktree is dirty, so the rail must stabilize the checkout before advancing the next Cortex lane.",
            "blocked_by": blocked_by,
            "source_refs": ["git status --porcelain=v1 --untracked-files=all"],
        }
    if isinstance(seeded_rail_state, dict):
        action = seeded_rail_state["next_action"]
        return {
            "lane_id": action["action_id"],
            "owner_layer": action["owner_layer"],
            "rationale": action["rationale"],
            "blocked_by": [],
            "source_refs": [current_state_ref, *seeded_rail_state.get("source_refs", [])],
        }

    current_lane = current_payload.get("next_recommended_lane")
    if isinstance(current_lane, dict):
        return {
            "lane_id": str(current_lane.get("lane_id", "")).strip() or "capture-current-state",
            "owner_layer": str(current_lane.get("owner_layer", "atlas")).strip() or "atlas",
            "rationale": "The rail-state seed was unavailable, so the bounded fallback is the explicit current-state recommendation.",
            "blocked_by": [],
            "source_refs": [current_state_ref],
        }

    return {
        "lane_id": "capture-current-state",
        "owner_layer": "atlas",
        "rationale": "No seeded rail-state input was available, so the bounded fallback is to refresh the explicit current-state artifact.",
        "blocked_by": [],
        "source_refs": [current_state_ref],
    }


def _rail_status(*, blockers: list[dict[str, Any]], seeded_rail_state: dict[str, Any] | None) -> str:
    if any(item["source_kind"] == "validation_receipt" for item in blockers):
        return BLOCKED_RAIL_STATUS
    if blockers:
        return STABILIZE_FIRST_RAIL_STATUS
    if seeded_rail_state is None:
        return BOUNDED_FALLBACK_RAIL_STATUS
    return READY_RAIL_STATUS


def build_rail_state_payload(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_current_state = (current_state_path or default_current_state_latest_json_path(base)).resolve()
    resolved_validation = (validation_path or default_validation_receipt_path(base)).resolve()

    current_payload = _require_json_object(resolved_current_state, label="Cortex current-state artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")

    current_state_ref = atlas_relative(resolved_current_state, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)

    validation_counts = _normalize_counts(
        validation_payload.get("summary", {}) if isinstance(validation_payload.get("summary"), dict) else {}
    )
    current_blockers = _current_state_blockers(current_payload)
    live_validation_blockers = _validation_blockers(validation_payload, validation_ref=validation_ref)
    blockers = _dedupe_and_sort_blockers([*current_blockers, *live_validation_blockers])

    seeded_summary, seeded_refs = _load_seeded_assessment(
        root=base,
        state_model_path=state_model_path,
        rule_registry_path=rule_registry_path,
    )
    if isinstance(seeded_summary, dict):
        seeded_summary["source_refs"] = seeded_refs

    current_rail_state = current_payload.get("rail_state") if isinstance(current_payload.get("rail_state"), dict) else None
    latest_clean_step = current_payload.get("latest_clean_step")
    if not isinstance(latest_clean_step, dict):
        latest_clean_step = {
            "step_id": "current-state-unavailable",
            "owner_layer": "atlas",
            "summary": "Current-state did not include a latest clean step.",
            "status": "unknown",
            "source_ref": current_state_ref,
        }

    next_lane = _next_lane(
        blockers=blockers,
        current_payload=current_payload,
        seeded_rail_state=seeded_summary,
        validation_ref=validation_ref,
        current_state_ref=current_state_ref,
    )
    dirty_lanes = _dirty_lanes(
        blockers=blockers,
        seeded_rail_state=seeded_summary,
        current_rail_state=current_rail_state,
    )
    boundary_reminders = _unique_refs(
        _normalize_string_list(seeded_summary.get("boundary_reminders") if isinstance(seeded_summary, dict) else [])
        + _normalize_string_list(current_rail_state.get("boundary_reminders") if isinstance(current_rail_state, dict) else [])
    )
    evidence_refs = _unique_refs([current_state_ref, validation_ref, *seeded_refs])

    return {
        "contract_version": RAIL_STATE_READER_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "stack_root": normalize_slashes(str(base)),
        "active_rail": (
            str(seeded_summary.get("rail_id")).strip()
            if isinstance(seeded_summary, dict) and seeded_summary.get("rail_id")
            else str(current_rail_state.get("rail_id", "unknown")) if isinstance(current_rail_state, dict) else "unknown"
        ),
        "rail_status": _rail_status(blockers=blockers, seeded_rail_state=seeded_summary),
        "latest_clean_step": latest_clean_step,
        "dirty_lanes": dirty_lanes,
        "validation_posture": {
            "status": _validation_posture_status(validation_counts),
            "counts": validation_counts,
            "receipt_generated_at": str(validation_payload.get("generated_at", "")),
            "receipt_path": validation_ref,
        },
        "active_blockers": blockers,
        "next_recommended_lane": next_lane,
        "boundary_reminders": boundary_reminders,
        "evidence_refs": evidence_refs,
        "source_refs": evidence_refs,
        "current_state_ref": current_state_ref,
        "seeded_rail_state": seeded_summary,
    }


def render_rail_state_summary(payload: dict[str, Any]) -> str:
    latest_clean_step = payload["latest_clean_step"]
    validation_posture = payload["validation_posture"]
    next_lane = payload["next_recommended_lane"]
    lines = [
        "# Cortex Rail State",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Active rail: `{payload['active_rail']}`",
        f"- Rail status: `{payload['rail_status']}`",
        (
            f"- Validation posture: `{validation_posture['status']}` "
            f"(critical={validation_posture['counts']['critical']} error={validation_posture['counts']['error']} "
            f"warning={validation_posture['counts']['warning']} info={validation_posture['counts']['info']} "
            f"total={validation_posture['counts']['total']})"
        ),
        f"- Latest clean step: `{latest_clean_step['step_id']}` ({latest_clean_step['owner_layer']})",
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        "",
        "## Active Blockers",
    ]
    blockers = payload.get("active_blockers", [])
    if blockers:
        for blocker in blockers:
            lines.append(f"- `{blocker['code']}` [{blocker['severity']}]: {blocker['summary']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Dirty Lanes"])
    dirty_lanes = payload.get("dirty_lanes", [])
    if dirty_lanes:
        for lane_id in dirty_lanes:
            lines.append(f"- `{lane_id}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Boundary Reminders"])
    boundary_reminders = payload.get("boundary_reminders", [])
    if boundary_reminders:
        for reminder in boundary_reminders:
            lines.append(f"- {reminder}")
    else:
        lines.append("- none")

    lines.extend(["", "## Evidence"])
    for ref in payload.get("evidence_refs", []):
        lines.append(f"- `{ref}`")
    return "\n".join(lines) + "\n"


def persist_rail_state_artifact(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedRailStateArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_rail_state_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_rail_state_latest_markdown_path(base)).resolve() if write_markdown else None
    )
    payload = build_rail_state_payload(
        root=base,
        current_state_path=current_state_path.resolve() if current_state_path is not None else None,
        validation_path=validation_path.resolve() if validation_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
    )
    summary = render_rail_state_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedRailStateArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the Cortex rail-state artifact for ATLAS.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--current-state-path", type=Path)
    parser.add_argument("--validation-path", type=Path)
    parser.add_argument("--state-model-path", type=Path)
    parser.add_argument("--rule-registry-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--no-write-markdown", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        artifact = persist_rail_state_artifact(
            root=args.root.resolve(),
            current_state_path=args.current_state_path.resolve() if args.current_state_path else None,
            validation_path=args.validation_path.resolve() if args.validation_path else None,
            state_model_path=args.state_model_path.resolve() if args.state_model_path else None,
            rule_registry_path=args.rule_registry_path.resolve() if args.rule_registry_path else None,
            output_json_path=args.output_json.resolve() if args.output_json else None,
            output_markdown_path=args.output_markdown.resolve() if args.output_markdown else None,
            write_markdown=not args.no_write_markdown,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.print_json:
        print(json.dumps(artifact.payload, indent=2))
    elif not args.quiet:
        print(artifact.summary, end="")
        print(f"JSON artifact: {normalize_slashes(str(artifact.artifact_path))}")
        if artifact.summary_path is not None:
            print(f"Markdown summary: {normalize_slashes(str(artifact.summary_path))}")
        print(f"Payload digest: {artifact.payload_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
