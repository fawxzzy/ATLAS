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
from ops.cortex.context_assembler import default_context_latest_json_path
from ops.cortex.current_state import (
    default_current_state_latest_json_path,
    default_validation_receipt_path,
)
from ops.cortex.kernel import default_rule_registry_path, default_state_model_path
from ops.cortex.operator_surface import default_operator_surface_latest_json_path
from ops.cortex.rail_state_reader import default_rail_state_latest_json_path
from ops.cortex.run_ledger import summarize_run_ledger

LEDGER_SCHEMA_VERSION = "atlas.cortex.ledger.v1"
LEDGER_AUTHORITY_LEVEL = "read_only_advisory"


def ledger_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "ledger"


def default_ledger_latest_json_path(root: Path | None = None) -> Path:
    return ledger_root(root) / "latest.json"


def default_ledger_latest_markdown_path(root: Path | None = None) -> Path:
    return ledger_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedCortexLedgerArtifact:
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


def _ordered_unique_strings(values: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


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
    return {
        "code": str(item.get("code", "")).strip(),
        "severity": str(item.get("severity", "warning")).strip() or "warning",
        "summary": str(item.get("summary", "")).strip(),
        "source_kind": str(item.get("source_kind", "unknown")).strip() or "unknown",
        "source_ref": str(item.get("source_ref", "")).strip(),
        "details": details if isinstance(details, dict) else {},
    }


def _sorted_blockers(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    blockers = [_normalize_blocker(item) for item in values if isinstance(item, dict)]
    keyed: dict[str, dict[str, Any]] = {}
    for blocker in blockers:
        key = json.dumps(blocker, sort_keys=True)
        keyed[key] = blocker
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


def _boundary_reminders(
    *,
    context_payload: dict[str, Any],
    operator_payload: dict[str, Any],
    rail_payload: dict[str, Any],
    state_model_payload: dict[str, Any],
) -> list[str]:
    values: list[Any] = []
    values.extend(context_payload.get("boundary_reminders", []) if isinstance(context_payload.get("boundary_reminders"), list) else [])
    values.extend(operator_payload.get("boundary_reminders", []) if isinstance(operator_payload.get("boundary_reminders"), list) else [])
    values.extend(rail_payload.get("boundary_reminders", []) if isinstance(rail_payload.get("boundary_reminders"), list) else [])
    posture = state_model_payload.get("posture")
    if isinstance(posture, dict):
        values.extend(posture.get("boundary_reminders", []) if isinstance(posture.get("boundary_reminders"), list) else [])
        rail_state = posture.get("rail_state")
        if isinstance(rail_state, dict):
            values.extend(rail_state.get("boundary_reminders", []) if isinstance(rail_state.get("boundary_reminders"), list) else [])
    return _ordered_unique_strings(values)


def _source_artifact_refs(
    *,
    current_state_ref: str,
    rail_state_ref: str,
    context_ref: str,
    operator_surface_ref: str,
    validation_ref: str,
    state_model_ref: str,
    rule_registry_ref: str,
) -> dict[str, str]:
    return {
        "current_state": current_state_ref,
        "rail_state": rail_state_ref,
        "context": context_ref,
        "operator_surface": operator_surface_ref,
        "validation": validation_ref,
        "seed": state_model_ref,
        "rules": rule_registry_ref,
    }


def _evidence_refs(
    *,
    source_artifact_refs: dict[str, str],
    operator_payload: dict[str, Any],
    proof_summary: dict[str, Any],
) -> list[dict[str, str]]:
    refs = [
        {"label": "current_state", "ref": source_artifact_refs["current_state"]},
        {"label": "rail_state", "ref": source_artifact_refs["rail_state"]},
        {"label": "context", "ref": source_artifact_refs["context"]},
        {"label": "operator_surface", "ref": source_artifact_refs["operator_surface"]},
        {"label": "validation", "ref": source_artifact_refs["validation"]},
        {"label": "seed", "ref": source_artifact_refs["seed"]},
        {"label": "rules", "ref": source_artifact_refs["rules"]},
    ]
    latest_run_path = proof_summary.get("latest_run_path")
    if isinstance(latest_run_path, str) and latest_run_path.strip():
        refs.append({"label": "run_ledger.latest_run", "ref": latest_run_path.strip()})
    top_refs = operator_payload.get("top_evidence_refs")
    if isinstance(top_refs, list):
        for index, ref in enumerate(_ordered_unique_strings(top_refs), start=1):
            if any(existing["ref"] == ref for existing in refs):
                continue
            refs.append({"label": f"top_evidence_{index:02d}", "ref": ref})
    return refs


def _proof_or_receipt_readiness(*, root: Path) -> dict[str, Any]:
    try:
        summary = summarize_run_ledger(root=root)
    except FileNotFoundError:
        return {
            "status": "unavailable",
            "receipt_ready": None,
            "latest_run_id": None,
            "latest_run_path": None,
            "selected_next_action": None,
            "owner_layer": None,
            "next_required_layer": None,
            "blocked_reason": None,
            "known_ambient_debt": [],
            "current_validation_debt": [],
            "applied_rule_ids": [],
            "summary": "No Cortex run artifacts are available yet.",
        }
    return {
        "status": summary.proof_status,
        "receipt_ready": summary.receipt_ready,
        "latest_run_id": summary.latest_run_id,
        "latest_run_path": summary.latest_run_path,
        "selected_next_action": summary.selected_next_action,
        "owner_layer": summary.owner_layer,
        "next_required_layer": summary.next_required_layer,
        "blocked_reason": summary.blocked_reason,
        "known_ambient_debt": list(summary.known_ambient_debt),
        "current_validation_debt": list(summary.current_validation_debt),
        "applied_rule_ids": list(summary.applied_rules.rule_ids),
        "summary": (
            f"Latest Cortex run {summary.latest_run_id} is {summary.proof_status}; "
            f"receipt_ready={'yes' if summary.receipt_ready else 'no'}."
        ),
    }


def build_cortex_ledger_payload(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    context_path: Path | None = None,
    operator_surface_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_current_state = (current_state_path or default_current_state_latest_json_path(base)).resolve()
    resolved_rail_state = (rail_state_path or default_rail_state_latest_json_path(base)).resolve()
    resolved_context = (context_path or default_context_latest_json_path(base)).resolve()
    resolved_operator_surface = (operator_surface_path or default_operator_surface_latest_json_path(base)).resolve()
    resolved_validation = (validation_path or default_validation_receipt_path(base)).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()

    current_payload = _require_json_object(resolved_current_state, label="Cortex current-state artifact")
    rail_payload = _require_json_object(resolved_rail_state, label="Cortex rail-state artifact")
    context_payload = _require_json_object(resolved_context, label="Cortex context artifact")
    operator_payload = _require_json_object(resolved_operator_surface, label="Cortex operator-surface artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")
    state_model_payload = _require_json_object(resolved_state_model, label="Cortex state model seed")
    rule_registry_payload = _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")

    current_ref = atlas_relative(resolved_current_state, root=base)
    rail_ref = atlas_relative(resolved_rail_state, root=base)
    context_ref = atlas_relative(resolved_context, root=base)
    operator_ref = atlas_relative(resolved_operator_surface, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)

    source_artifact_refs = _source_artifact_refs(
        current_state_ref=current_ref,
        rail_state_ref=rail_ref,
        context_ref=context_ref,
        operator_surface_ref=operator_ref,
        validation_ref=validation_ref,
        state_model_ref=state_model_ref,
        rule_registry_ref=rule_registry_ref,
    )
    proof_summary = _proof_or_receipt_readiness(root=base)
    validation_counts = _normalize_counts(
        validation_payload.get("summary", {}) if isinstance(validation_payload.get("summary"), dict) else {}
    )
    next_lane = (
        operator_payload.get("next_recommended_lane")
        if isinstance(operator_payload.get("next_recommended_lane"), dict)
        else {}
    )
    blockers = _sorted_blockers(operator_payload.get("active_blockers"))
    if not blockers:
        blockers = _sorted_blockers(rail_payload.get("active_blockers"))
    if not blockers:
        blockers = _sorted_blockers(current_payload.get("active_blockers"))
    publication = (
        current_payload.get("remote_publication_state")
        if isinstance(current_payload.get("remote_publication_state"), dict)
        else {}
    )
    boundary_reminders = _boundary_reminders(
        context_payload=context_payload,
        operator_payload=operator_payload,
        rail_payload=rail_payload,
        state_model_payload=state_model_payload,
    )
    ledger_id = f"ledger-{str(next_lane.get('lane_id', 'unknown')).strip() or 'unknown'}"

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "ledger_id": ledger_id,
        "generated_at": _utc_now(),
        "authority_level": LEDGER_AUTHORITY_LEVEL,
        "stack_root": normalize_slashes(str(base)),
        "active_rail": str(operator_payload.get("active_rail", rail_payload.get("active_rail", "unknown"))).strip() or "unknown",
        "rail_status": str(operator_payload.get("rail_status", rail_payload.get("rail_status", "unknown"))).strip() or "unknown",
        "next_recommended_lane": {
            "lane_id": str(next_lane.get("lane_id", "")).strip(),
            "owner_layer": str(next_lane.get("owner_layer", "")).strip(),
            "rationale": str(next_lane.get("rationale", "")).strip(),
            "blocked_by": _ordered_unique_strings(
                next_lane.get("blocked_by", []) if isinstance(next_lane.get("blocked_by"), list) else []
            ),
            "source_refs": _ordered_unique_strings(
                next_lane.get("source_refs", []) if isinstance(next_lane.get("source_refs"), list) else []
            ),
        },
        "active_blockers": blockers,
        "dirty_lanes": _ordered_unique_strings(
            operator_payload.get("dirty_lanes", [])
            if isinstance(operator_payload.get("dirty_lanes"), list)
            else rail_payload.get("dirty_lanes", []) if isinstance(rail_payload.get("dirty_lanes"), list) else []
        ),
        "validation_counts": validation_counts,
        "worktree_status": str(current_payload.get("worktree_status", "")).strip(),
        "branch": str(current_payload.get("branch", "")).strip(),
        "head": str(current_payload.get("head", "")).strip(),
        "remote_status": str(publication.get("status", "")).strip() or str(current_payload.get("remote_status", {}).get("status", "")).strip(),
        "upstream": (
            str(publication.get("upstream", "")).strip() or None
            if publication.get("upstream") is not None
            else None
        ),
        "published": bool(publication.get("published", False)),
        "context_packet_id": str(context_payload.get("packet_id", "")).strip(),
        "operator_surface_ref": operator_ref,
        "task_frame_summary": (
            operator_payload.get("task_frame_summary")
            if isinstance(operator_payload.get("task_frame_summary"), dict)
            else {}
        ),
        "proof_or_receipt_readiness": proof_summary,
        "evidence_refs": _evidence_refs(
            source_artifact_refs=source_artifact_refs,
            operator_payload=operator_payload,
            proof_summary=proof_summary,
        ),
        "boundary_reminders": boundary_reminders,
        "source_artifact_refs": source_artifact_refs,
    }


def render_cortex_ledger_summary(payload: dict[str, Any]) -> str:
    counts = payload["validation_counts"]
    next_lane = payload["next_recommended_lane"]
    task_frame = payload["task_frame_summary"]
    proof = payload["proof_or_receipt_readiness"]
    lines = [
        "# Cortex Ledger",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Ledger id: `{payload['ledger_id']}`",
        f"- Authority level: `{payload['authority_level']}`",
        f"- Active rail: `{payload['active_rail']}`",
        f"- Rail status: `{payload['rail_status']}`",
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        (
            f"- Validation: `critical={counts['critical']} error={counts['error']} "
            f"warning={counts['warning']} info={counts['info']} total={counts['total']}`"
        ),
        f"- Branch: `{payload['branch']}`",
        f"- HEAD: `{payload['head']}`",
        f"- Worktree: `{payload['worktree_status']}`",
        f"- Remote status: `{payload['remote_status']}`",
        f"- Context packet: `{payload['context_packet_id']}`",
        f"- Operator surface: `{payload['operator_surface_ref']}`",
        "",
        "## Task Frame",
        f"- `{task_frame.get('lane_id', '')}` ({task_frame.get('owner_layer', '')})",
        f"- {task_frame.get('title', '')}",
        f"- Status: `{task_frame.get('status', '')}`",
    ]
    rationale = str(task_frame.get("rationale", "")).strip()
    if rationale:
        lines.append(f"- {rationale}")

    lines.extend(["", "## Active Blockers"])
    if payload["active_blockers"]:
        for blocker in payload["active_blockers"]:
            lines.append(f"- `{blocker['code']}` [{blocker['severity']}]: {blocker['summary']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Proof / Receipt Readiness"])
    lines.append(f"- Status: `{proof['status']}`")
    lines.append(f"- Receipt ready: `{'yes' if proof['receipt_ready'] else 'no' if proof['receipt_ready'] is False else 'unknown'}`")
    if proof.get("latest_run_id"):
        lines.append(f"- Latest run: `{proof['latest_run_id']}`")
    if proof.get("blocked_reason"):
        lines.append(f"- Blocked reason: {proof['blocked_reason']}")
    lines.append(f"- {proof['summary']}")

    lines.extend(["", "## Evidence Refs"])
    for item in payload["evidence_refs"]:
        lines.append(f"- `{item['label']}` -> `{item['ref']}`")

    lines.extend(["", "## Boundary Reminders"])
    if payload["boundary_reminders"]:
        for reminder in payload["boundary_reminders"]:
            lines.append(f"- {reminder}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def persist_cortex_ledger_artifact(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    context_path: Path | None = None,
    operator_surface_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedCortexLedgerArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_ledger_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_ledger_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    payload = build_cortex_ledger_payload(
        root=base,
        current_state_path=current_state_path.resolve() if current_state_path is not None else None,
        rail_state_path=rail_state_path.resolve() if rail_state_path is not None else None,
        context_path=context_path.resolve() if context_path is not None else None,
        operator_surface_path=operator_surface_path.resolve() if operator_surface_path is not None else None,
        validation_path=validation_path.resolve() if validation_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
    )
    summary = render_cortex_ledger_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedCortexLedgerArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the canonical Cortex ledger artifact for ATLAS.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--current-state-path", type=Path)
    parser.add_argument("--rail-state-path", type=Path)
    parser.add_argument("--context-path", type=Path)
    parser.add_argument("--operator-surface-path", type=Path)
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
        artifact = persist_cortex_ledger_artifact(
            root=args.root.resolve(),
            current_state_path=args.current_state_path.resolve() if args.current_state_path else None,
            rail_state_path=args.rail_state_path.resolve() if args.rail_state_path else None,
            context_path=args.context_path.resolve() if args.context_path else None,
            operator_surface_path=args.operator_surface_path.resolve() if args.operator_surface_path else None,
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
