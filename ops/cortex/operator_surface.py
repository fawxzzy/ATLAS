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
from ops.cortex.rail_state_reader import default_rail_state_latest_json_path
from ops.cortex.shadow_agent_registry import default_shadow_agent_registry_path, load_shadow_agent_registry

OPERATOR_SURFACE_CONTRACT_VERSION = "atlas.cortex.operator-surface.v1"


def operator_surface_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "operator-surface"


def default_operator_surface_latest_json_path(root: Path | None = None) -> Path:
    return operator_surface_root(root) / "latest.json"


def default_operator_surface_latest_markdown_path(root: Path | None = None) -> Path:
    return operator_surface_root(root) / "latest.md"


def shadow_agent_consumption_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "cortex" / "shadow-agent-consumption"


@dataclass(frozen=True)
class PersistedOperatorSurfaceArtifact:
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


def _task_frame_summary(value: Any) -> dict[str, Any]:
    task_frame = value if isinstance(value, dict) else {}
    blocked_by = task_frame.get("blocked_by")
    required_inputs = task_frame.get("required_inputs")
    verification_steps = task_frame.get("verification_steps")
    return {
        "lane_id": str(task_frame.get("lane_id", "")).strip(),
        "owner_layer": str(task_frame.get("owner_layer", "")).strip(),
        "title": str(task_frame.get("title", "")).strip(),
        "status": str(task_frame.get("status", "")).strip(),
        "rationale": str(task_frame.get("rationale", "")).strip(),
        "blocked_by": _ordered_unique_strings(blocked_by if isinstance(blocked_by, list) else []),
        "required_inputs": _ordered_unique_strings(required_inputs if isinstance(required_inputs, list) else []),
        "verification_steps": _ordered_unique_strings(
            verification_steps if isinstance(verification_steps, list) else []
        ),
        "receipt_scope": (
            str(task_frame.get("receipt_scope", "")).strip() or None
            if task_frame.get("receipt_scope") is not None
            else None
        ),
        "ready_to_execute": bool(task_frame.get("ready_to_execute", False)),
    }


def _boundary_reminders(
    *,
    context_payload: dict[str, Any],
    rail_payload: dict[str, Any],
    state_model_payload: dict[str, Any],
) -> list[str]:
    posture = state_model_payload.get("posture")
    posture_payload = posture if isinstance(posture, dict) else {}
    rail_state = posture_payload.get("rail_state")
    rail_state_payload = rail_state if isinstance(rail_state, dict) else {}
    values: list[Any] = []
    values.extend(context_payload.get("boundary_reminders", []) if isinstance(context_payload.get("boundary_reminders"), list) else [])
    values.extend(rail_payload.get("boundary_reminders", []) if isinstance(rail_payload.get("boundary_reminders"), list) else [])
    values.extend(posture_payload.get("boundary_reminders", []) if isinstance(posture_payload.get("boundary_reminders"), list) else [])
    values.extend(rail_state_payload.get("boundary_reminders", []) if isinstance(rail_state_payload.get("boundary_reminders"), list) else [])
    return _ordered_unique_strings(values)


def _top_evidence_refs(
    *,
    current_payload: dict[str, Any],
    rail_payload: dict[str, Any],
    context_payload: dict[str, Any],
) -> list[str]:
    refs: list[Any] = []
    evidence_list = context_payload.get("evidence_list")
    if isinstance(evidence_list, list):
        for item in evidence_list:
            if isinstance(item, dict):
                refs.append(item.get("ref"))
    refs.extend(context_payload.get("source_refs", []) if isinstance(context_payload.get("source_refs"), list) else [])
    refs.extend(rail_payload.get("evidence_refs", []) if isinstance(rail_payload.get("evidence_refs"), list) else [])
    refs.extend(current_payload.get("source_refs", []) if isinstance(current_payload.get("source_refs"), list) else [])
    return _ordered_unique_strings(refs)[:8]


def _shadow_agent_summary(record: Any) -> dict[str, Any]:
    return {
        "agent_id": record.agent_id,
        "contract_id": record.contract_id,
        "family_name": record.family_name,
        "trigger": record.trigger,
        "admissibility_state": record.admissibility_state,
        "stage": record.stage,
        "runnable": record.runnable,
        "owner_boundary": record.owner_boundary,
        "non_claim_boundary": record.non_claim_boundary,
    }


def _project_shadow_consumption(
    *,
    root: Path,
    shadow_agent_registry: Any,
) -> tuple[dict[str, Any], list[str]]:
    consumption_root = shadow_agent_consumption_root(root)
    refs: list[str] = []
    consumed_agents: list[dict[str, Any]] = []
    seen_agent_ids: set[str] = set()
    registry_by_id = {item.agent_id: item for item in shadow_agent_registry.agents}
    if consumption_root.exists():
        for artifact_path in sorted(consumption_root.glob("*.latest.json")):
            payload = _read_json_object(artifact_path)
            agent_payload = payload.get("agent")
            if not isinstance(agent_payload, dict):
                continue
            agent_id = str(agent_payload.get("id", "")).strip()
            if not agent_id or agent_id in seen_agent_ids:
                continue
            seen_agent_ids.add(agent_id)
            registry_record = registry_by_id.get(agent_id)
            authority_payload = payload.get("authority")
            authority = authority_payload if isinstance(authority_payload, dict) else {}
            consumed_agents.append(
                {
                    "agent_id": agent_id,
                    "contract_id": (
                        registry_record.contract_id
                        if registry_record is not None
                        else str(agent_payload.get("contract_id", "")).strip()
                    ),
                    "family_name": (
                        registry_record.family_name
                        if registry_record is not None
                        else str(agent_payload.get("family_name", "")).strip()
                    ),
                    "trigger": (
                        registry_record.trigger
                        if registry_record is not None
                        else str(agent_payload.get("trigger", "")).strip()
                    ),
                    "admissibility_state": (
                        registry_record.admissibility_state
                        if registry_record is not None
                        else str(agent_payload.get("admissibility_state", "")).strip()
                    ),
                    "artifact_ref": atlas_relative(artifact_path, root=root),
                    "contract_version": str(payload.get("contract_version", "")).strip(),
                    "generated_at": str(payload.get("generated_at", "")).strip(),
                    "consumption_status": str(payload.get("consumption_status", "")).strip(),
                    "stage": str(agent_payload.get("stage", "")).strip(),
                    "authority": {
                        key: bool(value)
                        for key, value in sorted(authority.items())
                        if isinstance(key, str) and isinstance(value, bool)
                    },
                }
            )
            refs.append(atlas_relative(artifact_path, root=root))
    consumed_agents.sort(key=lambda item: item["agent_id"])
    projected_agent_ids = [item["agent_id"] for item in consumed_agents]
    projected_contract_ids = [item["contract_id"] for item in consumed_agents if item["contract_id"]]
    missing_eligible_agent_ids = [
        item.agent_id for item in shadow_agent_registry.eligible_agents if item.agent_id not in seen_agent_ids
    ]
    missing_eligible_contract_ids = [
        item.contract_id for item in shadow_agent_registry.eligible_agents if item.agent_id not in seen_agent_ids
    ]
    projection = {
        "artifact_root": atlas_relative(consumption_root, root=root),
        "projected_agent_ids": projected_agent_ids,
        "projected_contract_ids": projected_contract_ids,
        "missing_eligible_agent_ids": missing_eligible_agent_ids,
        "missing_eligible_contract_ids": missing_eligible_contract_ids,
        "consumed_agents": consumed_agents,
    }
    return projection, refs


def build_operator_surface_payload(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    context_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    shadow_agent_registry_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    resolved_current_state = (current_state_path or default_current_state_latest_json_path(base)).resolve()
    resolved_rail_state = (rail_state_path or default_rail_state_latest_json_path(base)).resolve()
    resolved_context = (context_path or default_context_latest_json_path(base)).resolve()
    resolved_validation = (validation_path or default_validation_receipt_path(base)).resolve()
    resolved_state_model = (state_model_path or default_state_model_path(base)).resolve()
    resolved_rule_registry = (rule_registry_path or default_rule_registry_path(base)).resolve()
    resolved_shadow_agent_registry = (
        shadow_agent_registry_path or default_shadow_agent_registry_path(base)
    ).resolve()

    current_payload = _require_json_object(resolved_current_state, label="Cortex current-state artifact")
    rail_payload = _require_json_object(resolved_rail_state, label="Cortex rail-state artifact")
    context_payload = _require_json_object(resolved_context, label="Cortex context artifact")
    validation_payload = _require_json_object(resolved_validation, label="Stack validation receipt")
    state_model_payload = _require_json_object(resolved_state_model, label="Cortex state model seed")
    rule_registry_payload = _require_json_object(resolved_rule_registry, label="Cortex rule registry seed")
    shadow_agent_registry = load_shadow_agent_registry(path=resolved_shadow_agent_registry, root=base)

    current_ref = atlas_relative(resolved_current_state, root=base)
    rail_ref = atlas_relative(resolved_rail_state, root=base)
    context_ref = atlas_relative(resolved_context, root=base)
    validation_ref = atlas_relative(resolved_validation, root=base)
    state_model_ref = atlas_relative(resolved_state_model, root=base)
    rule_registry_ref = atlas_relative(resolved_rule_registry, root=base)
    shadow_agent_registry_ref = atlas_relative(resolved_shadow_agent_registry, root=base)

    validation_counts = _normalize_counts(
        validation_payload.get("summary", {}) if isinstance(validation_payload.get("summary"), dict) else {}
    )
    task_frame = _task_frame_summary(context_payload.get("task_frame"))
    next_lane = rail_payload.get("next_recommended_lane") if isinstance(rail_payload.get("next_recommended_lane"), dict) else {}
    blockers = _sorted_blockers(rail_payload.get("active_blockers"))
    if not blockers:
        blockers = _sorted_blockers(current_payload.get("active_blockers"))
    dirty_lanes = _ordered_unique_strings(rail_payload.get("dirty_lanes", []) if isinstance(rail_payload.get("dirty_lanes"), list) else [])
    publication_posture = current_payload.get("remote_publication_state")
    publication_payload = publication_posture if isinstance(publication_posture, dict) else {}
    boundary_reminders = _boundary_reminders(
        context_payload=context_payload,
        rail_payload=rail_payload,
        state_model_payload=state_model_payload,
    )
    shadow_consumption, shadow_consumption_refs = _project_shadow_consumption(
        root=base,
        shadow_agent_registry=shadow_agent_registry,
    )

    operator_summary = (
        f"Cortex operator surface for {task_frame['lane_id'] or next_lane.get('lane_id', 'unknown')} derived from "
        "explicit current-state, rail-state, context, validation, and seed artifacts."
    )
    return {
        "contract_version": OPERATOR_SURFACE_CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "stack_root": normalize_slashes(str(base)),
        "operator_summary": operator_summary,
        "active_rail": str(rail_payload.get("active_rail", "unknown")).strip() or "unknown",
        "rail_status": str(rail_payload.get("rail_status", "unknown")).strip() or "unknown",
        "next_recommended_lane": {
            "lane_id": str(next_lane.get("lane_id", "")).strip(),
            "owner_layer": str(next_lane.get("owner_layer", "")).strip(),
            "rationale": str(next_lane.get("rationale", "")).strip(),
            "blocked_by": _ordered_unique_strings(next_lane.get("blocked_by", []) if isinstance(next_lane.get("blocked_by"), list) else []),
            "source_refs": _ordered_unique_strings(next_lane.get("source_refs", []) if isinstance(next_lane.get("source_refs"), list) else []),
        },
        "active_blockers": blockers,
        "dirty_lanes": dirty_lanes,
        "validation_status": str(rail_payload.get("validation_posture", {}).get("status", "")).strip()
        if isinstance(rail_payload.get("validation_posture"), dict)
        else "",
        "validation_counts": validation_counts,
        "context_packet_id": str(context_payload.get("packet_id", "")).strip(),
        "context_summary": str(context_payload.get("context_summary", "")).strip(),
        "task_frame_summary": task_frame,
        "top_evidence_refs": _top_evidence_refs(
            current_payload=current_payload,
            rail_payload=rail_payload,
            context_payload=context_payload,
        ),
        "boundary_reminders": boundary_reminders,
        "publication_posture": {
            "branch": str(current_payload.get("branch", "")).strip(),
            "head": str(current_payload.get("head", "")).strip(),
            "worktree_status": str(current_payload.get("worktree_status", "")).strip(),
            "remote_status": str(publication_payload.get("status", "")).strip(),
            "upstream": (
                str(publication_payload.get("upstream", "")).strip() or None
                if publication_payload.get("upstream") is not None
                else None
            ),
            "published": bool(publication_payload.get("published", False)),
            "pr_state": (
                str(publication_payload.get("pr_state", "")).strip() or None
                if publication_payload.get("pr_state") is not None
                else None
            ),
            "pr_url": (
                str(publication_payload.get("pr_url", "")).strip() or None
                if publication_payload.get("pr_url") is not None
                else None
            ),
        },
        "seed_snapshot": {
            "posture_id": str(state_model_payload.get("posture", {}).get("posture_id", "")).strip()
            if isinstance(state_model_payload.get("posture"), dict)
            else "",
            "matched_rule_ids": _ordered_unique_strings(
                rail_payload.get("seeded_rail_state", {}).get("matched_rule_ids", [])
                if isinstance(rail_payload.get("seeded_rail_state"), dict)
                else []
            ),
            "rule_count": len(rule_registry_payload.get("rules", []))
            if isinstance(rule_registry_payload.get("rules"), list)
            else 0,
        },
        "shadow_agents": {
            "registry_ref": shadow_agent_registry_ref,
            "source_receipts": list(shadow_agent_registry.source_receipts),
            "exportable_contract_ids": [item.contract_id for item in shadow_agent_registry.exportable_agents],
            "shadow_contract_ids": [item.contract_id for item in shadow_agent_registry.eligible_agents],
            "blocked_contract_ids": [item.contract_id for item in shadow_agent_registry.blocked_agents],
            "eligible_agent_ids": [item.agent_id for item in shadow_agent_registry.eligible_agents],
            "blocked_agent_ids": [item.agent_id for item in shadow_agent_registry.blocked_agents],
            "eligible_agents": [_shadow_agent_summary(item) for item in shadow_agent_registry.eligible_agents],
            "blocked_agents": [_shadow_agent_summary(item) for item in shadow_agent_registry.blocked_agents],
        },
        "shadow_consumption": shadow_consumption,
        "source_refs": [
            current_ref,
            rail_ref,
            context_ref,
            validation_ref,
            state_model_ref,
            rule_registry_ref,
            shadow_agent_registry_ref,
            *shadow_consumption_refs,
        ],
    }


def render_operator_surface_summary(payload: dict[str, Any]) -> str:
    counts = payload["validation_counts"]
    next_lane = payload["next_recommended_lane"]
    publication = payload["publication_posture"]
    task_frame = payload["task_frame_summary"]
    lines = [
        "# Cortex Operator Surface",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Active rail: `{payload['active_rail']}`",
        f"- Rail status: `{payload['rail_status']}`",
        f"- Next recommended lane: `{next_lane['lane_id']}` ({next_lane['owner_layer']})",
        (
            f"- Validation: `{payload['validation_status']}` "
            f"(critical={counts['critical']} error={counts['error']} "
            f"warning={counts['warning']} info={counts['info']} total={counts['total']})"
        ),
        f"- Context packet: `{payload['context_packet_id']}`",
        f"- Branch: `{publication['branch']}`",
        f"- HEAD: `{publication['head']}`",
        f"- Worktree: `{publication['worktree_status']}`",
        (
            f"- Remote publication: `{publication['remote_status']}` "
            f"(upstream={publication['upstream'] or 'none'}, published={'yes' if publication['published'] else 'no'})"
        ),
        "",
        "## Task Frame",
        f"- `{task_frame['lane_id']}` ({task_frame['owner_layer']})",
        f"- {task_frame['title']}",
        f"- Status: `{task_frame['status']}`",
        f"- Ready to execute: `{'yes' if task_frame['ready_to_execute'] else 'no'}`",
        f"- {task_frame['rationale']}",
    ]
    if task_frame["receipt_scope"]:
        lines.append(f"- Receipt scope: {task_frame['receipt_scope']}")

    lines.extend(["", "## Active Blockers"])
    if payload["active_blockers"]:
        for blocker in payload["active_blockers"]:
            lines.append(f"- `{blocker['code']}` [{blocker['severity']}]: {blocker['summary']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Dirty Lanes"])
    if payload["dirty_lanes"]:
        for lane_id in payload["dirty_lanes"]:
            lines.append(f"- `{lane_id}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Boundary Reminders"])
    if payload["boundary_reminders"]:
        for reminder in payload["boundary_reminders"]:
            lines.append(f"- {reminder}")
    else:
        lines.append("- none")

    shadow_agents = payload.get("shadow_agents", {})
    lines.extend(["", "## Shadow Agents"])
    lines.append(f"- Registry: `{shadow_agents.get('registry_ref', '')}`")
    exportable_contract_ids = shadow_agents.get("exportable_contract_ids", [])
    shadow_contract_ids = shadow_agents.get("shadow_contract_ids", [])
    blocked_contract_ids = shadow_agents.get("blocked_contract_ids", [])
    eligible_ids = shadow_agents.get("eligible_agent_ids", [])
    blocked_ids = shadow_agents.get("blocked_agent_ids", [])
    if exportable_contract_ids:
        lines.append(f"- Exportable contracts: `{', '.join(exportable_contract_ids)}`")
    else:
        lines.append("- Exportable contracts: none")
    if shadow_contract_ids:
        lines.append(f"- Shadow contracts: `{', '.join(shadow_contract_ids)}`")
    else:
        lines.append("- Shadow contracts: none")
    if blocked_contract_ids:
        lines.append(f"- Blocked contracts: `{', '.join(blocked_contract_ids)}`")
    else:
        lines.append("- Blocked contracts: none")
    if eligible_ids:
        lines.append(f"- Eligible: `{', '.join(eligible_ids)}`")
    else:
        lines.append("- Eligible: none")
    if blocked_ids:
        lines.append(f"- Blocked: `{', '.join(blocked_ids)}`")
    else:
        lines.append("- Blocked: none")

    shadow_consumption = payload.get("shadow_consumption", {})
    projected_ids = shadow_consumption.get("projected_agent_ids", [])
    missing_ids = shadow_consumption.get("missing_eligible_agent_ids", [])
    lines.extend(["", "## Shadow Consumption"])
    lines.append(f"- Artifact root: `{shadow_consumption.get('artifact_root', '')}`")
    if projected_ids:
        lines.append(f"- Projected: `{', '.join(projected_ids)}`")
    else:
        lines.append("- Projected: none")
    if missing_ids:
        lines.append(f"- Missing eligible projections: `{', '.join(missing_ids)}`")
    else:
        lines.append("- Missing eligible projections: none")
    for item in shadow_consumption.get("consumed_agents", []):
        lines.append(
            f"- `{item['agent_id']}` / `{item['contract_id']}` -> `{item['artifact_ref']}` "
            f"({item['admissibility_state'] or 'unknown'}, {item['consumption_status'] or 'unknown'}, {item['contract_version'] or 'unknown'})"
        )

    lines.extend(["", "## Top Evidence"])
    for ref in payload["top_evidence_refs"]:
        lines.append(f"- `{ref}`")
    return "\n".join(lines) + "\n"


def persist_operator_surface_artifact(
    *,
    root: Path | None = None,
    current_state_path: Path | None = None,
    rail_state_path: Path | None = None,
    context_path: Path | None = None,
    validation_path: Path | None = None,
    state_model_path: Path | None = None,
    rule_registry_path: Path | None = None,
    output_json_path: Path | None = None,
    output_markdown_path: Path | None = None,
    write_markdown: bool = True,
) -> PersistedOperatorSurfaceArtifact:
    base = (root or atlas_root()).resolve()
    artifact_path = (output_json_path or default_operator_surface_latest_json_path(base)).resolve()
    summary_path = (
        (output_markdown_path or default_operator_surface_latest_markdown_path(base)).resolve()
        if write_markdown
        else None
    )
    payload = build_operator_surface_payload(
        root=base,
        current_state_path=current_state_path.resolve() if current_state_path is not None else None,
        rail_state_path=rail_state_path.resolve() if rail_state_path is not None else None,
        context_path=context_path.resolve() if context_path is not None else None,
        validation_path=validation_path.resolve() if validation_path is not None else None,
        state_model_path=state_model_path.resolve() if state_model_path is not None else None,
        rule_registry_path=rule_registry_path.resolve() if rule_registry_path is not None else None,
    )
    summary = render_operator_surface_summary(payload)
    write_json(artifact_path, payload)
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
    return PersistedOperatorSurfaceArtifact(
        artifact_path=artifact_path,
        summary_path=summary_path,
        payload_digest=stable_json_digest(payload),
        payload=payload,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the Cortex operator surface artifact for ATLAS.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--current-state-path", type=Path)
    parser.add_argument("--rail-state-path", type=Path)
    parser.add_argument("--context-path", type=Path)
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
        artifact = persist_operator_surface_artifact(
            root=args.root.resolve(),
            current_state_path=args.current_state_path.resolve() if args.current_state_path else None,
            rail_state_path=args.rail_state_path.resolve() if args.rail_state_path else None,
            context_path=args.context_path.resolve() if args.context_path else None,
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
