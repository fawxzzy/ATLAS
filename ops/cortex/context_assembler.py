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
from ops.cortex.current_state import default_current_state_latest_json_path, default_validation_receipt_path
from ops.cortex.kernel import default_rule_registry_path, default_state_model_path
from ops.cortex.rail_state_reader import default_rail_state_latest_json_path
from ops.cortex.workflow_profile import build_workflow_profile_payload

CONTEXT_PACKET_CONTRACT_VERSION = "atlas.cortex.context-packet.v1"


def context_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "context"


def default_context_latest_json_path(root: Path | None = None) -> Path:
    return context_root(root) / "latest.json"


def default_context_latest_markdown_path(root: Path | None = None) -> Path:
    return context_root(root) / "latest.md"


@dataclass(frozen=True)
class PersistedContextPacketArtifact:
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


def _rule_index(rule_registry_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rules = rule_registry_payload.get("rules")
    if not isinstance(rules, list):
        return {}
    index: dict[str, dict[str, Any]] = {}
    for item in rules:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("id", "")).strip()
        if not rule_id:
            continue
        index[rule_id] = item
    return index


def _rule_highlights(matched_rule_ids: list[str], rule_registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    index = _rule_index(rule_registry_payload)
    highlights: list[dict[str, Any]] = []
    for rule_id in matched_rule_ids:
        item = index.get(rule_id)
        if item is None:
            continue
        highlights.append(
            {
                "id": rule_id,
                "kind": str(item.get("kind", "")).strip(),
                "statement": str(item.get("statement", "")).strip(),
                "next_action_hint": str(item.get("next_action_hint", "")).strip(),
                "evidence": _ordered_unique_strings(item.get("evidence", [])) if isinstance(item.get("evidence"), list) else [],
            }
        )
    return highlights


def _boundary_reminders(
    rail_state_payload: dict[str, Any],
    current_state_payload: dict[str, Any],
    state_model_payload: dict[str, Any],
) -> list[str]:
    current_rail_state = current_state_payload.get("rail_state")
    posture = state_model_payload.get("posture")
    values: list[Any] = []
    if isinstance(rail_state_payload.get("boundary_reminders"), list):
        values.extend(rail_state_payload["boundary_reminders"])
    if isinstance(current_rail_state, dict) and isinstance(current_rail_state.get("boundary_reminders"), list):
        values.extend(current_rail_state["boundary_reminders"])
    if isinstance(posture, dict):
        if isinstance(posture.get("boundary_reminders"), list):
            values.extend(posture["boundary_reminders"])
        rail_state = posture.get("rail_state")
        if isinstance(rail_state, dict) and isinstance(rail_state.get("boundary_reminders"), list):
            values.extend(rail_state["boundary_reminders"])
    return _ordered_unique_strings(values)


def _stabilization_title(lane_id: str) -> str:
    if lane_id == "stabilize-stack-validation":
        return "Stabilize stack validation before advancing the next Cortex lane."
    if lane_id == "stabilize-root-worktree":
        return "Stabilize the root worktree before advancing the next Cortex lane."
    return "Stabilize the active Cortex blockers before advancing the next lane."


def _stabilization_verification_steps(lane_id: str) -> list[str]:
    steps = ["python .\\ops\\validation\\validate_stack.py"]
    if lane_id == "stabilize-root-worktree":
        return ["git status --short", *steps]
    return steps


def _task_frame(
    *,
    immediate_lane: dict[str, Any],
    seeded_next_action: dict[str, Any] | None,
    blockers: list[dict[str, Any]],
    rail_status: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    lane_id = str(immediate_lane.get("lane_id", "")).strip() or "capture-current-state"
    owner_layer = str(immediate_lane.get("owner_layer", "atlas")).strip() or "atlas"
    blocked_by = _ordered_unique_strings([item.get("code") for item in blockers])
    seeded_action_id = (
        str(seeded_next_action.get("action_id", "")).strip() if isinstance(seeded_next_action, dict) else ""
    )
    is_seeded_lane = seeded_action_id and seeded_action_id == lane_id

    if is_seeded_lane and isinstance(seeded_next_action, dict):
        title = str(seeded_next_action.get("title", "")).strip() or lane_id
        required_inputs = _ordered_unique_strings(seeded_next_action.get("required_inputs", []))
        verification_steps = _ordered_unique_strings(seeded_next_action.get("verification_plan", []))
        receipt_scope = str(seeded_next_action.get("receipt_scope", "")).strip() or None
    else:
        title = _stabilization_title(lane_id)
        required_inputs = evidence_refs
        verification_steps = _stabilization_verification_steps(lane_id)
        receipt_scope = None

    return {
        "lane_id": lane_id,
        "owner_layer": owner_layer,
        "title": title,
        "status": "ready" if not blockers else rail_status,
        "rationale": str(immediate_lane.get("rationale", "")).strip(),
        "blocked_by": blocked_by,
        "required_inputs": required_inputs,
        "verification_steps": verification_steps,
        "receipt_scope": receipt_scope,
        "ready_to_execute": not blockers,
    }


def _deferred_lane(
    *,
    immediate_lane: dict[str, Any],
    seeded_next_action: dict[str, Any] | None,
    seeded_source_refs: list[str],
) -> dict[str, Any] | None:
    if not isinstance(seeded_next_action, dict):
        return None
    immediate_lane_id = str(immediate_lane.get("lane_id", "")).strip()
    seeded_lane_id = str(seeded_next_action.get("action_id", "")).strip()
    if not seeded_lane_id or seeded_lane_id == immediate_lane_id:
        return None
    return {
        "lane_id": seeded_lane_id,
        "owner_layer": str(seeded_next_action.get("owner_layer", "")).strip(),
        "title": str(seeded_next_action.get("title", "")).strip(),
        "rationale": str(seeded_next_action.get("rationale", "")).strip(),
        "required_inputs": _ordered_unique_strings(seeded_next_action.get("required_inputs", [])),
        "verification_steps": _ordered_unique_strings(seeded_next_action.get("verification_plan", [])),
        "receipt_scope": str(seeded_next_action.get("receipt_scope", "")).strip() or None,
        "source_refs": seeded_source_refs,
    }


def _evidence_list(
    *,
    current_state_ref: str,
    current_state_payload: dict[str, Any],
    rail_state_ref: str,
    rail_state_payload: dict[str, Any],
    validation_ref: str,
    validation_payload: dict[str, Any],
    state_model_ref: str,
    state_model_payload: dict[str, Any],
    rule_registry_ref: str,
    rule_registry_payload: dict[str, Any],
    workflow_profile_ref: str,
    workflow_profile_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "ref": current_state_ref,
            "kind": "current_state",
            "role": "workspace posture and active blocker projection",
            "generated_at": str(current_state_payload.get("generated_at", "")),
        },
        {
            "ref": rail_state_ref,
            "kind": "rail_state",
            "role": "active rail routing and dirty-lane projection",
            "generated_at": str(rail_state_payload.get("generated_at", "")),
        },
        {
            "ref": validation_ref,
            "kind": "validation_receipt",
            "role": "live validation counts and blocker findings",
            "generated_at": str(validation_payload.get("generated_at", "")),
        },
        {
            "ref": state_model_ref,
            "kind": "state_seed",
            "role": "seeded posture, dirty lanes, and next-action doctrine",
            "posture_id": str(state_model_payload.get("posture", {}).get("posture_id", "")),
        },
        {
            "ref": rule_registry_ref,
            "kind": "rule_seed",
            "role": "matched rules, patterns, and failure modes",
            "rule_count": len(rule_registry_payload.get("rules", [])) if isinstance(rule_registry_payload.get("rules"), list) else 0,
        },
        {
            "ref": workflow_profile_ref,
            "kind": "workflow_profile",
            "role": "canonical operator workflow profile for Cortex bootstrap and response-shape guidance",
            "profile_id": str(workflow_profile_payload.get("profile_id", "")),
        },
    ]


def build_context_packet_payload(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_current_state = (current_state_path or default_current_state_latest_json_path(base)).resolve()
    resolved_rail_state = (rail_state_path or default_rail_state_latest_json_path(base)).resolve()
    resolved_validation = (validation_path or default_validation_receipt_path(base)).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()

    current_state_payload = _require_json_object(resolved_current_state, label="Cortex current-state artifact")
    rail_state_payload = _require_json_object(resolved_rail_state, label="Cortex rail-state artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")
    state_model_payload = _require_json_object(resolved_state_model, label="Cortex state model seed")
    rule_registry_payload = _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")

    current_state_ref = atlas_relative(resolved_current_state, root=base)
    rail_state_ref = atlas_relative(resolved_rail_state, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)
    workflow_profile_payload = build_workflow_profile_payload(root=base)
    workflow_profile_markdown_ref = str(workflow_profile_payload.get("canonical_refs", {}).get("markdown", "")).strip()
    workflow_profile_metadata_ref = str(workflow_profile_payload.get("canonical_refs", {}).get("metadata", "")).strip()

    seeded_rail_state = (
        rail_state_payload.get("seeded_rail_state") if isinstance(rail_state_payload.get("seeded_rail_state"), dict) else {}
    )
    seeded_next_action = (
        seeded_rail_state.get("next_action") if isinstance(seeded_rail_state.get("next_action"), dict) else None
    )
    matched_rule_ids = _ordered_unique_strings(seeded_rail_state.get("matched_rule_ids", []))
    blockers = rail_state_payload.get("active_blockers", []) if isinstance(rail_state_payload.get("active_blockers"), list) else []
    immediate_lane = (
        rail_state_payload.get("next_recommended_lane")
        if isinstance(rail_state_payload.get("next_recommended_lane"), dict)
        else {}
    )

    validation_counts = _normalize_counts(
        validation_payload.get("summary", {}) if isinstance(validation_payload.get("summary"), dict) else {}
    )
    evidence_refs = [
        current_state_ref,
        rail_state_ref,
        validation_ref,
        state_model_ref,
        rule_registry_ref,
        workflow_profile_markdown_ref,
        workflow_profile_metadata_ref,
    ]
    task_frame = _task_frame(
        immediate_lane=immediate_lane,
        seeded_next_action=seeded_next_action,
        blockers=[item for item in blockers if isinstance(item, dict)],
        rail_status=str(rail_state_payload.get("rail_status", "ready")).strip() or "ready",
        evidence_refs=evidence_refs,
    )

    return {
        "contract_version": CONTEXT_PACKET_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "stack_root": normalize_slashes(str(base)),
        "packet_id": f"context-{task_frame['lane_id']}",
        "active_rail": str(rail_state_payload.get("active_rail", "unknown")).strip() or "unknown",
        "rail_status": str(rail_state_payload.get("rail_status", "ready")).strip() or "ready",
        "context_summary": (
            f"Cortex context packet for {task_frame['lane_id']} derived from explicit current-state, rail-state, "
            f"validation, and seed artifacts."
        ),
        "posture_snapshot": {
            "branch": str(current_state_payload.get("branch", "")).strip(),
            "head": str(current_state_payload.get("head", "")).strip(),
            "worktree_status": str(current_state_payload.get("worktree_status", "")).strip(),
            "active_blocker_count": len([item for item in blockers if isinstance(item, dict)]),
            "latest_clean_step_id": str(current_state_payload.get("latest_clean_step", {}).get("step_id", "")).strip(),
            "dirty_lanes": _ordered_unique_strings(rail_state_payload.get("dirty_lanes", [])),
            "validation_status": str(rail_state_payload.get("validation_posture", {}).get("status", "")).strip(),
            "validation_counts": validation_counts,
        },
        "task_frame": task_frame,
        "deferred_lane": _deferred_lane(
            immediate_lane=immediate_lane,
            seeded_next_action=seeded_next_action,
            seeded_source_refs=_ordered_unique_strings(seeded_rail_state.get("source_refs", [])),
        ),
        "rule_highlights": _rule_highlights(matched_rule_ids, rule_registry_payload),
        "workflow_profile": workflow_profile_payload,
        "boundary_reminders": _boundary_reminders(
            rail_state_payload=rail_state_payload,
            current_state_payload=current_state_payload,
            state_model_payload=state_model_payload,
        ),
        "evidence_list": _evidence_list(
            current_state_ref=current_state_ref,
            current_state_payload=current_state_payload,
            rail_state_ref=rail_state_ref,
            rail_state_payload=rail_state_payload,
            validation_ref=validation_ref,
            validation_payload=validation_payload,
            state_model_ref=state_model_ref,
            state_model_payload=state_model_payload,
            rule_registry_ref=rule_registry_ref,
            rule_registry_payload=rule_registry_payload,
            workflow_profile_ref=workflow_profile_markdown_ref,
            workflow_profile_payload=workflow_profile_payload,
        ),
        "source_refs": evidence_refs,
    }


def render_context_packet_summary(payload: dict[str, Any]) -> str:
    task_frame = payload["task_frame"]
    posture = payload["posture_snapshot"]
    deferred_lane = payload.get("deferred_lane")
    workflow_profile = payload.get("workflow_profile", {})
    lines = [
        "# Cortex Context Packet",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Packet id: `{payload['packet_id']}`",
        f"- Active rail: `{payload['active_rail']}`",
        f"- Rail status: `{payload['rail_status']}`",
        f"- Branch: `{posture['branch']}`",
        f"- HEAD: `{posture['head']}`",
        f"- Worktree: `{posture['worktree_status']}`",
        (
            f"- Validation: `{posture['validation_status']}` "
            f"(critical={posture['validation_counts']['critical']} error={posture['validation_counts']['error']} "
            f"warning={posture['validation_counts']['warning']} info={posture['validation_counts']['info']} "
            f"total={posture['validation_counts']['total']})"
        ),
        f"- Task frame: `{task_frame['lane_id']}` ({task_frame['owner_layer']})",
        f"- Task status: `{task_frame['status']}`",
        "",
        "## Objective",
        f"- {task_frame['title']}",
        f"- {task_frame['rationale']}",
    ]
    if deferred_lane:
        lines.extend(
            [
                "",
                "## Deferred Lane",
                f"- `{deferred_lane['lane_id']}` ({deferred_lane['owner_layer']})",
                f"- {deferred_lane['title']}",
            ]
        )
    lines.extend(["", "## Blockers"])
    if task_frame["blocked_by"]:
        for blocker in task_frame["blocked_by"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Evidence"])
    for item in payload.get("evidence_list", []):
        lines.append(f"- `{item['ref']}`: {item['role']}")
    lines.extend(["", "## Rule Highlights"])
    if payload.get("rule_highlights"):
        for item in payload["rule_highlights"]:
            lines.append(f"- `{item['id']}` ({item['kind']}): {item['statement']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Workflow Profile"])
    if isinstance(workflow_profile, dict) and workflow_profile:
        response_contract = (
            workflow_profile.get("response_contract")
            if isinstance(workflow_profile.get("response_contract"), dict)
            else {}
        )
        lines.append(
            f"- `{workflow_profile.get('profile_id', '')}`: {workflow_profile.get('summary', '')}"
        )
        if response_contract:
            lines.append(
                f"- Response block: `{', '.join(response_contract.get('status_block_labels', []))}`"
            )
            lines.append(
                f"- Recommended execution path footer: `{response_contract.get('recommended_execution_path_footer', False)}`"
            )
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def persist_context_packet_artifact(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedContextPacketArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_context_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_context_latest_markdown_path(base)).resolve() if write_markdown else None
    )
    payload = build_context_packet_payload(
        root=base,
        current_state_path=current_state_path.resolve() if current_state_path is not None else None,
        rail_state_path=rail_state_path.resolve() if rail_state_path is not None else None,
        validation_path=validation_path.resolve() if validation_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
    )
    summary = render_context_packet_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedContextPacketArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the Cortex context packet artifact for ATLAS.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--current-state-path", type=Path)
    parser.add_argument("--rail-state-path", type=Path)
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
        artifact = persist_context_packet_artifact(
            root=args.root.resolve(),
            current_state_path=args.current_state_path.resolve() if args.current_state_path else None,
            rail_state_path=args.rail_state_path.resolve() if args.rail_state_path else None,
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
