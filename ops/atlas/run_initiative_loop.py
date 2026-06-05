from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.atlas.author_working_memory import all_proposed_session_manifests, all_session_manifests
from ops.atlas.load_tool_registry import load_tool_registry_bundle, select_tool_entry
from ops.atlas.run_session import (
    APPROVED_ACTION_AUTOMATION_LEVEL,
    CONTEXT_TOOL_ID,
    OBSERVE_AUTOMATION_LEVEL,
    READ_ONLY_EXECUTION_TOOL_ID,
    SESSION_CONTRACT_VERSION,
    SUPERVISION_TOOL_ID,
    component_snapshot,
    load_stack_lock_payload,
)
from ops.cortex._artifacts import (
    default_artifact_source_paths,
    read_json,
    register_artifact_descriptors,
    stable_json_digest,
    write_json_if_changed,
)
from ops.cortex.index_working_memory import load_working_memory_catalog, write_working_memory_catalog
from ops.cortex.world_model import attention_output_path, world_model_state_root, write_world_model_state

PROPOSAL_SESSION_ROLE = "proposed_session"
PROPOSAL_SCENARIO = "proposed_session"
PROPOSAL_STATE = "proposed"
PROPOSAL_ROOT = Path("runtime/atlas/proposed-sessions")
INITIATIVE_ROOT = Path("docs/memory/initiatives")
ACTIONABLE_ATTENTION_KINDS = {
    "blocked_worker",
    "closure_receipt_issue",
    "missing_closure_receipt",
    "open_merge_request",
    "registry_drift",
    "resume_failed",
    "session_failed",
    "session_needs_resume",
    "unknown_extension_surface",
    "unknown_tool_surface",
}


def parse_iso(value: str | None) -> datetime:
    if not isinstance(value, str) or not value.strip():
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "initiative"


def humanize(value: str) -> str:
    parts = [part for part in value.replace("_", "-").split("-") if part]
    return " ".join(part.capitalize() for part in parts) or value


def unique_strings(values: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        ordered.append(stripped)
    return ordered


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return payload


def session_ref_to_id(ref: str) -> str | None:
    parts = normalize_slashes(ref).split("/")
    if "sessions" in parts:
        index = parts.index("sessions")
        if index + 1 < len(parts):
            return parts[index + 1] or None
    if "proposed-sessions" in parts:
        index = parts.index("proposed-sessions")
        if index + 1 < len(parts):
            return parts[index + 1] or None
    if "supervisor" in parts:
        index = parts.index("supervisor")
        if index + 1 < len(parts):
            return parts[index + 1] or None
    for part in parts:
        if part.startswith("session-"):
            return part
    return None


def first_text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def latest_timestamp(values: list[str | None]) -> str:
    parsed = [parse_iso(value) for value in values if isinstance(value, str) and value.strip()]
    return isoformat(max(parsed)) if parsed else "1970-01-01T00:00:00Z"


def earliest_timestamp(values: list[str | None]) -> str:
    parsed = [parse_iso(value) for value in values if isinstance(value, str) and value.strip()]
    return isoformat(min(parsed)) if parsed else "1970-01-01T00:00:00Z"


def infer_timestamp(payload: dict[str, Any]) -> str | None:
    return first_text(
        payload.get("updated_at"),
        payload.get("closed_at"),
        payload.get("created_at"),
        payload.get("generated_at"),
        payload.get("recorded_at"),
    )


def load_latest_attention(root: Path) -> dict[str, Any]:
    attention_path = attention_output_path(root)
    if not attention_path.exists():
        raise FileNotFoundError(
            "Missing runtime/state/atlas/world-model.attention.latest.json. Build the world model first."
        )
    return read_json(attention_path)


@dataclass
class SessionRecord:
    ref: str
    path: Path
    payload: dict[str, Any]
    session_id: str
    task_id: str
    title: str
    session_role: str
    session_state: str
    final_status: str | None
    updated_at: str | None
    execution_tool_id: str | None
    execution_extension_id: str | None
    max_automation_level: str | None


@dataclass
class MemoryRecord:
    ref: str
    path: Path
    payload: dict[str, Any]
    item: dict[str, Any]


@dataclass
class Cluster:
    key: str
    initiative_id: str
    initiative_ref: str
    task_id: str | None = None
    title: str | None = None
    summary: str | None = None
    existing_payload: dict[str, Any] | None = None
    related_plan_refs: set[str] = field(default_factory=set)
    related_decision_refs: set[str] = field(default_factory=set)
    related_hypothesis_refs: set[str] = field(default_factory=set)
    related_session_refs: set[str] = field(default_factory=set)
    related_attention_refs: set[str] = field(default_factory=set)
    evidence_refs: set[str] = field(default_factory=set)
    proposed_next_session_refs: set[str] = field(default_factory=set)
    supersedes: list[str] = field(default_factory=list)
    superseded_by: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_candidates: list[str] = field(default_factory=list)
    updated_candidates: list[str] = field(default_factory=list)
    attention_kinds: set[str] = field(default_factory=set)
    actionable_attention_refs: set[str] = field(default_factory=set)
    supporting_session_records: list[SessionRecord] = field(default_factory=list)


def build_session_record(path: Path, payload: dict[str, Any], *, root: Path) -> SessionRecord:
    governed_surfaces = payload.get("governed_surfaces") if isinstance(payload.get("governed_surfaces"), dict) else {}
    execution_surface = governed_surfaces.get("execution") if isinstance(governed_surfaces.get("execution"), dict) else {}
    session_id = str(payload.get("session_id") or path.parent.name).strip()
    return SessionRecord(
        ref=atlas_relative(path, root=root),
        path=path,
        payload=payload,
        session_id=session_id,
        task_id=str(payload.get("task_id") or session_id).strip(),
        title=str(payload.get("title") or session_id).strip(),
        session_role=str(payload.get("session_role") or "governed_session").strip(),
        session_state=str(payload.get("session_state") or "unknown").strip(),
        final_status=first_text(
            (payload.get("completion") if isinstance(payload.get("completion"), dict) else {}).get("final_status")
        ),
        updated_at=infer_timestamp(payload),
        execution_tool_id=first_text(execution_surface.get("tool_id")),
        execution_extension_id=first_text(execution_surface.get("extension_id")),
        max_automation_level=first_text(payload.get("max_automation_level")),
    )


def build_memory_record(item: dict[str, Any], *, root: Path) -> MemoryRecord:
    path = resolve_atlas_path(str(item.get("path")), root=root)
    return MemoryRecord(
        ref=atlas_relative(path, root=root),
        path=path,
        payload=load_json_object(path),
        item=item,
    )


def load_memory_by_kind(root: Path) -> dict[str, list[MemoryRecord]]:
    catalog = load_working_memory_catalog(root)
    grouped: dict[str, list[MemoryRecord]] = {}
    for item in catalog.get("items", []):
        if not isinstance(item, dict):
            continue
        memory_kind = str(item.get("memory_kind", "")).strip()
        if not memory_kind or not item.get("path"):
            continue
        grouped.setdefault(memory_kind, []).append(build_memory_record(item, root=root))
    return grouped


def ensure_cluster(
    clusters: dict[str, Cluster],
    *,
    key: str,
    initiative_id: str,
    initiative_ref: str,
    task_id: str | None,
    title: str | None = None,
    summary: str | None = None,
    existing_payload: dict[str, Any] | None = None,
) -> Cluster:
    cluster = clusters.get(key)
    if cluster is None:
        cluster = Cluster(
            key=key,
            initiative_id=initiative_id,
            initiative_ref=initiative_ref,
            task_id=task_id,
            title=title,
            summary=summary,
            existing_payload=existing_payload,
            supersedes=list(existing_payload.get("supersedes", [])) if isinstance(existing_payload, dict) else [],
            superseded_by=list(existing_payload.get("superseded_by", [])) if isinstance(existing_payload, dict) else [],
            metadata=dict(existing_payload.get("metadata", {})) if isinstance(existing_payload, dict) and isinstance(existing_payload.get("metadata"), dict) else {},
        )
        clusters[key] = cluster
    if task_id and not cluster.task_id:
        cluster.task_id = task_id
    if title and not cluster.title:
        cluster.title = title
    if summary and not cluster.summary:
        cluster.summary = summary
    if existing_payload is not None:
        cluster.existing_payload = existing_payload
    return cluster


def infer_task_id_from_attention(
    item: dict[str, Any],
    *,
    sessions_by_id: dict[str, SessionRecord],
) -> str | None:
    details = item.get("details") if isinstance(item.get("details"), dict) else {}
    task_id = first_text(details.get("task_id"))
    if task_id:
        return task_id
    source_ref = first_text(item.get("source_ref"))
    if not source_ref:
        return None
    session_id = session_ref_to_id(source_ref)
    if session_id and session_id in sessions_by_id:
        return sessions_by_id[session_id].task_id
    return None


def find_existing_cluster_key_for_attention(
    item: dict[str, Any],
    *,
    initiatives: list[MemoryRecord],
    sessions_by_id: dict[str, SessionRecord],
) -> str | None:
    attention_id = first_text(item.get("attention_id"))
    attention_ref = f"attention:{attention_id}" if attention_id else None
    source_ref = first_text(item.get("source_ref"))
    inferred_task_id = infer_task_id_from_attention(item, sessions_by_id=sessions_by_id)
    candidates: list[tuple[str, str]] = []
    for initiative in initiatives:
        payload = initiative.payload
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        related_attention_refs = payload.get("related_attention_refs") if isinstance(payload.get("related_attention_refs"), list) else []
        related_session_refs = payload.get("related_session_refs") if isinstance(payload.get("related_session_refs"), list) else []
        cluster_key = str(metadata.get("task_id") or payload.get("id"))
        if attention_ref and attention_ref in related_attention_refs:
            candidates.append(("0", cluster_key))
        elif source_ref and (source_ref in related_attention_refs or source_ref in related_session_refs):
            candidates.append(("1", cluster_key))
        elif inferred_task_id and str(metadata.get("task_id") or "").strip() == inferred_task_id:
            candidates.append(("2", cluster_key))
    if not candidates:
        return None
    return sorted(candidates)[0][1]


def proposal_session_ref(session_id: str) -> str:
    return normalize_slashes(str(PROPOSAL_ROOT / session_id / "session.manifest.json"))


def proposal_session_path(root: Path, session_id: str) -> Path:
    return (root / PROPOSAL_ROOT / session_id / "session.manifest.json").resolve()


def initiative_path(root: Path, initiative_id: str) -> Path:
    return (root / INITIATIVE_ROOT / f"{initiative_id}.json").resolve()


def select_execution_surface(cluster: Cluster, tool_bundle: dict[str, Any]) -> dict[str, Any]:
    ordered_sessions = sorted(
        cluster.supporting_session_records,
        key=lambda record: (parse_iso(record.updated_at), record.session_id),
        reverse=True,
    )
    for session in ordered_sessions:
        if not session.execution_tool_id:
            continue
        try:
            return select_tool_entry(tool_bundle, session.execution_tool_id)
        except KeyError:
            continue
    return select_tool_entry(tool_bundle, READ_ONLY_EXECUTION_TOOL_ID)


def build_initiative_payload(cluster: Cluster) -> dict[str, Any]:
    existing = cluster.existing_payload or {}
    title = cluster.title or f"{humanize(cluster.task_id or cluster.initiative_id)} Initiative"
    summary = cluster.summary or (
        f"Keep the current {cluster.task_id or cluster.initiative_id} work owned above the session layer so "
        "persistent attention and proposed governed work stay attached to one durable objective."
    )
    status = (
        "active"
        if (cluster.related_attention_refs or cluster.related_hypothesis_refs or cluster.proposed_next_session_refs)
        else str(existing.get("status") or "active")
    )
    return {
        "contract_version": "atlas.initiative.v1",
        "id": cluster.initiative_id,
        "title": title,
        "summary": summary,
        "status": status,
        "owner": "stack-root",
        "created_at": str(existing.get("created_at") or earliest_timestamp(cluster.created_candidates)),
        "updated_at": latest_timestamp(cluster.updated_candidates),
        "related_plan_refs": sorted(cluster.related_plan_refs),
        "related_decision_refs": sorted(cluster.related_decision_refs),
        "related_hypothesis_refs": sorted(cluster.related_hypothesis_refs),
        "related_session_refs": sorted(cluster.related_session_refs),
        "related_attention_refs": sorted(cluster.related_attention_refs),
        "evidence_refs": sorted(cluster.evidence_refs),
        "proposed_next_session_refs": sorted(cluster.proposed_next_session_refs),
        "supersedes": unique_strings(cluster.supersedes),
        "superseded_by": unique_strings(cluster.superseded_by),
        "metadata": {
            **cluster.metadata,
            "authoring_source": "initiative-proposal-loop",
            "task_id": cluster.task_id,
            "attention_kinds": sorted(cluster.attention_kinds),
            "session_count": len(cluster.related_session_refs),
        },
    }


def build_proposal_payload(
    *,
    cluster: Cluster,
    tool_bundle: dict[str, Any],
    stack_lock_payload: dict[str, Any],
) -> dict[str, Any]:
    execution_tool = select_execution_surface(cluster, tool_bundle)
    context_tool = select_tool_entry(tool_bundle, CONTEXT_TOOL_ID)
    supervision_tool = select_tool_entry(tool_bundle, SUPERVISION_TOOL_ID)
    session_id = f"session-proposed-{slugify(cluster.task_id or cluster.initiative_id)}"
    proposal = {
        "initiative_ref": cluster.initiative_ref,
        "triggering_attention_refs": sorted(cluster.actionable_attention_refs),
        "supporting_evidence_refs": sorted(cluster.evidence_refs),
        "related_plan_refs": sorted(cluster.related_plan_refs),
        "related_decision_refs": sorted(cluster.related_decision_refs),
        "related_hypothesis_refs": sorted(cluster.related_hypothesis_refs),
        "related_prior_session_refs": sorted(cluster.related_session_refs),
    }
    proposal["generated_from_digest"] = stable_json_digest(proposal)
    updated_at = latest_timestamp(
        [
            *cluster.updated_candidates,
            *(record.updated_at for record in cluster.supporting_session_records),
        ]
    )
    created_at = earliest_timestamp(
        [
            *cluster.created_candidates,
            *(record.updated_at for record in cluster.supporting_session_records),
        ]
    )
    latest_session = cluster.supporting_session_records[0] if cluster.supporting_session_records else None
    return {
        "contract_version": SESSION_CONTRACT_VERSION,
        "session_id": session_id,
        "title": f"Proposed next session for {cluster.title or humanize(cluster.task_id or cluster.initiative_id)}",
        "task_id": cluster.task_id or cluster.initiative_id,
        "scenario": PROPOSAL_SCENARIO,
        "session_role": PROPOSAL_SESSION_ROLE,
        "session_state": PROPOSAL_STATE,
        "automation_level": OBSERVE_AUTOMATION_LEVEL,
        "max_automation_level": str(
            latest_session.max_automation_level
            if latest_session and latest_session.max_automation_level
            else execution_tool.get("max_automation_level") or APPROVED_ACTION_AUTOMATION_LEVEL
        ),
        "stack_lock_digest": str(stack_lock_payload.get("lock_digest")),
        "stack_manifest_ref": "stack.yaml",
        "created_at": created_at,
        "updated_at": updated_at,
        "closed_at": None,
        "orchestrator": {
            "owner": "stack-root",
            "stack_component": component_snapshot(stack_lock_payload, "stack", fallback_path="."),
            "orchestrator_component": component_snapshot(stack_lock_payload, "_stack", fallback_path="repos/_stack"),
            "supervisor_component": {
                "path": "runtime/cortex",
                "model": "root-owned-subsystem",
            },
            "executor_component": component_snapshot(
                stack_lock_payload,
                "lifeline",
                fallback_path="repos/lifeline",
            ),
        },
        "governed_surfaces": {
            "registry_digest": tool_bundle["registry_digest"],
            "context": {
                "tool_id": context_tool["tool_id"],
                "extension_id": context_tool["extension_id"],
            },
            "supervision": {
                "tool_id": supervision_tool["tool_id"],
                "extension_id": supervision_tool["extension_id"],
            },
            "execution": {
                "tool_id": execution_tool["tool_id"],
                "extension_id": execution_tool["extension_id"],
            },
        },
        "worker": {
            "worker_id": f"{session_id}-worker",
            "assignment_id": f"{session_id}-assignment",
            "context_ref": None,
            "assignment_ref": None,
        },
        "refs": {
            "status_refs": [],
            "capability_profile_ref": None,
            "request_ref": None,
            "approval_receipt_ref": None,
            "execution_receipt_ref": None,
            "bridge_record_ref": None,
            "merge_request_refs": [],
            "pause_status_refs": [],
            "resume_context_refs": [],
            "merge_assignment_ref": None,
            "merge_prompt_ref": None,
            "merge_context_ref": None,
            "merge_completion_ref": None,
            "resume_request_ref": None,
            "resume_dispatch_ref": None,
            "resume_run_manifest_ref": None,
            "resumed_assignment_ref": None,
            "resumed_running_status_ref": None,
            "resumed_completed_status_ref": None,
        },
        "resume": {
            "status": "not_requested",
            "requested_at": None,
            "requested_worker_id": None,
            "resume_context_ref": None,
            "merge_completion_ref": None,
            "dispatched_at": None,
            "completed_at": None,
            "failure_reason": None,
        },
        "completion": {
            "final_status": None,
            "final_status_ref": None,
            "close_receipt_refs": [],
        },
        "proposal": proposal,
    }


def validate_proposal_payload(
    payload: dict[str, Any],
    *,
    known_attention_refs: set[str],
    known_file_refs: set[str],
    root: Path,
) -> list[str]:
    errors: list[str] = []
    if str(payload.get("session_state")) != PROPOSAL_STATE:
        errors.append("session_state must remain 'proposed'.")
    if str(payload.get("session_role")) != PROPOSAL_SESSION_ROLE:
        errors.append("session_role must remain 'proposed_session'.")
    refs = payload.get("refs") if isinstance(payload.get("refs"), dict) else {}
    if any(refs.get(field) for field in ("request_ref", "approval_receipt_ref", "execution_receipt_ref", "bridge_record_ref")):
        errors.append("proposal refs may not include execution or approval linkage.")
    if any(refs.get(field) for field in ("merge_assignment_ref", "merge_prompt_ref", "merge_context_ref", "merge_completion_ref")):
        errors.append("proposal refs may not include merge execution linkage.")
    if any(isinstance(refs.get(field), list) and refs.get(field) for field in ("status_refs", "merge_request_refs", "pause_status_refs", "resume_context_refs")):
        errors.append("proposal refs may not include live status or resume refs.")
    proposal = payload.get("proposal") if isinstance(payload.get("proposal"), dict) else {}
    initiative_ref = first_text(proposal.get("initiative_ref"))
    if not initiative_ref:
        errors.append("proposal.initiative_ref is required.")
    elif initiative_ref not in known_file_refs and not resolve_atlas_path(initiative_ref, root=root).exists():
        errors.append(f"proposal.initiative_ref does not resolve: {initiative_ref}")
    attention_refs = unique_strings(list(proposal.get("triggering_attention_refs", [])))
    if not attention_refs:
        errors.append("proposal.triggering_attention_refs must be non-empty.")
    for ref in attention_refs:
        if ref not in known_attention_refs:
            errors.append(f"unknown triggering attention ref: {ref}")
    evidence_refs = unique_strings(list(proposal.get("supporting_evidence_refs", [])))
    if not evidence_refs:
        errors.append("proposal.supporting_evidence_refs must be non-empty.")
    for ref in evidence_refs:
        if ref not in known_file_refs and not resolve_atlas_path(ref, root=root).exists():
            errors.append(f"unknown supporting evidence ref: {ref}")
    for field in (
        "related_plan_refs",
        "related_decision_refs",
        "related_hypothesis_refs",
        "related_prior_session_refs",
    ):
        for ref in unique_strings(list(proposal.get(field, []))):
            if ref not in known_file_refs and not resolve_atlas_path(ref, root=root).exists():
                errors.append(f"unknown {field} ref: {ref}")
    return errors


def refresh_descriptors_and_world_model(root: Path) -> dict[str, Any]:
    descriptor_root = root / "runtime" / "cortex" / "artifacts"
    register_artifact_descriptors(
        default_artifact_source_paths(root),
        output_dir=descriptor_root,
        root=root,
    )
    world_model_summary = write_world_model_state(
        descriptor_root=descriptor_root,
        root=root,
    )
    register_artifact_descriptors(
        [world_model_state_root(root)],
        output_dir=descriptor_root,
        root=root,
    )
    return world_model_summary


def attach_existing_relations(cluster: Cluster) -> None:
    if not cluster.existing_payload:
        return
    payload = cluster.existing_payload
    for field_name, target in (
        ("related_plan_refs", cluster.related_plan_refs),
        ("related_decision_refs", cluster.related_decision_refs),
        ("related_hypothesis_refs", cluster.related_hypothesis_refs),
        ("related_session_refs", cluster.related_session_refs),
        ("related_attention_refs", cluster.related_attention_refs),
        ("evidence_refs", cluster.evidence_refs),
        ("proposed_next_session_refs", cluster.proposed_next_session_refs),
    ):
        for ref in payload.get(field_name, []):
            if isinstance(ref, str) and ref.strip():
                target.add(ref.strip())
    if infer_timestamp(payload):
        cluster.created_candidates.append(first_text(payload.get("created_at")) or "1970-01-01T00:00:00Z")
        cluster.updated_candidates.append(infer_timestamp(payload) or "1970-01-01T00:00:00Z")


def cluster_is_material(cluster: Cluster) -> bool:
    return bool(
        cluster.existing_payload
        or cluster.related_attention_refs
        or cluster.related_hypothesis_refs
        or len(cluster.related_session_refs) > 1
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert durable ATLAS attention into initiatives and non-executing proposed sessions."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    refresh_descriptors_and_world_model(root)
    attention_payload = load_latest_attention(root)
    tool_bundle = load_tool_registry_bundle(root=root)
    stack_lock_payload = load_stack_lock_payload()
    memories = load_memory_by_kind(root)
    existing_initiatives = memories.get("initiative", [])
    plans = memories.get("plan", [])
    decisions = memories.get("decision", [])
    hypotheses = memories.get("hypothesis", [])

    governed_sessions = [
        build_session_record(path, payload, root=root)
        for path, payload in all_session_manifests(root)
    ]
    sessions_by_id = {session.session_id: session for session in governed_sessions}
    sessions_by_ref = {session.ref: session for session in governed_sessions}
    existing_proposals = {
        record.ref: record
        for record in (
            build_session_record(path, payload, root=root)
            for path, payload in all_proposed_session_manifests(root)
        )
    }

    clusters: dict[str, Cluster] = {}
    task_to_cluster_key: dict[str, str] = {}

    for initiative in existing_initiatives:
        payload = initiative.payload
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        initiative_id = str(payload.get("id"))
        task_id = first_text(metadata.get("task_id"))
        key = task_id or initiative_id
        cluster = ensure_cluster(
            clusters,
            key=key,
            initiative_id=initiative_id,
            initiative_ref=initiative.ref,
            task_id=task_id,
            title=first_text(payload.get("title")),
            summary=first_text(payload.get("summary")),
            existing_payload=payload,
        )
        attach_existing_relations(cluster)
        if task_id:
            task_to_cluster_key[task_id] = key

    for session in governed_sessions:
        if session.session_role == PROPOSAL_SESSION_ROLE:
            continue
        cluster_key = task_to_cluster_key.get(session.task_id, session.task_id)
        initiative_id = f"initiative-{slugify(session.task_id)}"
        cluster = ensure_cluster(
            clusters,
            key=cluster_key,
            initiative_id=initiative_id,
            initiative_ref=atlas_relative(initiative_path(root, initiative_id), root=root),
            task_id=session.task_id,
            title=f"{humanize(session.task_id)} Initiative",
        )
        task_to_cluster_key[session.task_id] = cluster_key
        cluster.related_session_refs.add(session.ref)
        cluster.evidence_refs.add(session.ref)
        cluster.supporting_session_records.append(session)
        if session.updated_at:
            cluster.created_candidates.append(session.updated_at)
            cluster.updated_candidates.append(session.updated_at)
        completion = session.payload.get("completion") if isinstance(session.payload.get("completion"), dict) else {}
        for ref in unique_strings(list(completion.get("close_receipt_refs", []))):
            cluster.evidence_refs.add(ref)

    for hypothesis in hypotheses:
        payload = hypothesis.payload
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        task_id = first_text(metadata.get("task_id"))
        if not task_id:
            for ref in payload.get("related_session_refs", []):
                session = sessions_by_ref.get(str(ref))
                if session is not None:
                    task_id = session.task_id
                    break
        if not task_id:
            continue
        cluster_key = task_to_cluster_key.get(task_id, task_id)
        initiative_id = f"initiative-{slugify(task_id)}"
        cluster = ensure_cluster(
            clusters,
            key=cluster_key,
            initiative_id=initiative_id,
            initiative_ref=atlas_relative(initiative_path(root, initiative_id), root=root),
            task_id=task_id,
            title=f"{humanize(task_id)} Initiative",
        )
        task_to_cluster_key[task_id] = cluster_key
        cluster.related_hypothesis_refs.add(hypothesis.ref)
        for ref in unique_strings(list(payload.get("related_session_refs", []))):
            cluster.related_session_refs.add(ref)
        for ref in unique_strings(list(payload.get("related_artifact_refs", [])) + list(payload.get("evidence_refs", []))):
            cluster.evidence_refs.add(ref)
        if infer_timestamp(payload):
            cluster.created_candidates.append(first_text(payload.get("created_at")) or infer_timestamp(payload) or "1970-01-01T00:00:00Z")
            cluster.updated_candidates.append(infer_timestamp(payload) or "1970-01-01T00:00:00Z")

    for item in attention_payload.get("attention_items", []):
        if not isinstance(item, dict):
            continue
        attention_id = first_text(item.get("attention_id"))
        if not attention_id:
            continue
        attention_ref = f"attention:{attention_id}"
        source_ref = first_text(item.get("source_ref"))
        existing_cluster_id = find_existing_cluster_key_for_attention(
            item,
            initiatives=existing_initiatives,
            sessions_by_id=sessions_by_id,
        )
        task_id = infer_task_id_from_attention(item, sessions_by_id=sessions_by_id)
        cluster_key = existing_cluster_id or task_to_cluster_key.get(task_id or "", task_id or "")
        if not cluster_key:
            continue
        initiative_id = (
            clusters[cluster_key].initiative_id
            if cluster_key in clusters
            else f"initiative-{slugify(task_id or attention_id)}"
        )
        cluster = ensure_cluster(
            clusters,
            key=cluster_key,
            initiative_id=initiative_id,
            initiative_ref=atlas_relative(initiative_path(root, initiative_id), root=root),
            task_id=task_id,
            title=f"{humanize(task_id or initiative_id)} Initiative",
        )
        if task_id:
            task_to_cluster_key[task_id] = cluster_key
        cluster.related_attention_refs.add(attention_ref)
        if source_ref:
            cluster.evidence_refs.add(source_ref)
            session_id = session_ref_to_id(source_ref)
            if session_id and session_id in sessions_by_id:
                cluster.related_session_refs.add(sessions_by_id[session_id].ref)
        attention_kind = str(item.get("kind") or "attention")
        cluster.attention_kinds.add(attention_kind)
        if attention_kind in ACTIONABLE_ATTENTION_KINDS:
            cluster.actionable_attention_refs.add(attention_ref)

    for cluster in clusters.values():
        cluster.supporting_session_records = sorted(
            {
                record.ref: record
                for record in cluster.supporting_session_records
                if record.ref in cluster.related_session_refs
            }.values(),
            key=lambda record: (parse_iso(record.updated_at), record.session_id),
            reverse=True,
        )
        cluster.related_session_refs = {ref for ref in cluster.related_session_refs if ref in sessions_by_ref}
        if not cluster_is_material(cluster):
            continue
        cluster.updated_candidates.extend(
            record.updated_at or "1970-01-01T00:00:00Z" for record in cluster.supporting_session_records
        )
        cluster.created_candidates.extend(
            record.updated_at or "1970-01-01T00:00:00Z" for record in cluster.supporting_session_records
        )
        related_sessions = set(cluster.related_session_refs)
        for collection, target in ((plans, cluster.related_plan_refs), (decisions, cluster.related_decision_refs)):
            for memory in collection:
                payload = memory.payload
                metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
                direct_match = bool(related_sessions.intersection(set(payload.get("related_session_refs", []))))
                task_match = bool(cluster.task_id and str(metadata.get("task_id") or "").strip() == cluster.task_id)
                existing_match = memory.ref in target
                if direct_match or task_match or existing_match:
                    target.add(memory.ref)
                    for ref in unique_strings(list(payload.get("evidence_refs", []))):
                        cluster.evidence_refs.add(ref)
                    if infer_timestamp(payload):
                        cluster.updated_candidates.append(infer_timestamp(payload) or "1970-01-01T00:00:00Z")

    known_attention_refs = {
        f"attention:{item.get('attention_id')}"
        for item in attention_payload.get("attention_items", [])
        if isinstance(item, dict) and isinstance(item.get("attention_id"), str)
    }
    known_file_refs = {
        atlas_relative(path, root=root)
        for path in [
            *[record.path for record in governed_sessions],
            *[record.path for record in existing_proposals.values()],
            *[record.path for group in memories.values() for record in group],
        ]
    }

    initiative_writes: list[dict[str, Any]] = []
    proposal_writes: list[dict[str, Any]] = []
    errors: list[str] = []

    for cluster in sorted(clusters.values(), key=lambda value: value.initiative_id):
        if not cluster_is_material(cluster):
            continue
        if cluster.actionable_attention_refs:
            proposal_payload = build_proposal_payload(
                cluster=cluster,
                tool_bundle=tool_bundle,
                stack_lock_payload=stack_lock_payload,
            )
            proposal_ref = proposal_session_ref(str(proposal_payload["session_id"]))
            cluster.proposed_next_session_refs = {proposal_ref}
            known_file_refs.add(cluster.initiative_ref)
            proposal_errors = validate_proposal_payload(
                proposal_payload,
                known_attention_refs=known_attention_refs,
                known_file_refs=known_file_refs,
                root=root,
            )
            if proposal_errors:
                errors.extend(f"{proposal_ref}: {message}" for message in proposal_errors)
            proposal_writes.append(
                {
                    "path": proposal_session_path(root, str(proposal_payload["session_id"])),
                    "ref": proposal_ref,
                    "payload": proposal_payload,
                }
            )
        initiative_payload = build_initiative_payload(cluster)
        initiative_writes.append(
            {
                "path": initiative_path(root, cluster.initiative_id),
                "ref": cluster.initiative_ref,
                "payload": initiative_payload,
            }
        )
        known_file_refs.add(cluster.initiative_ref)

    if errors:
        print(json.dumps({"errors": errors}, indent=2))
        return 1

    written_initiatives: list[dict[str, Any]] = []
    written_proposals: list[dict[str, Any]] = []

    for item in initiative_writes:
        changed = False
        if not args.dry_run:
            changed = write_json_if_changed(item["path"], item["payload"])
        written_initiatives.append(
            {
                "ref": item["ref"],
                "id": item["payload"]["id"],
                "changed": changed,
            }
        )

    for item in proposal_writes:
        changed = False
        if not args.dry_run:
            changed = write_json_if_changed(item["path"], item["payload"])
        written_proposals.append(
            {
                "ref": item["ref"],
                "session_id": item["payload"]["session_id"],
                "initiative_ref": item["payload"]["proposal"]["initiative_ref"],
                "changed": changed,
            }
        )

    if not args.dry_run:
        catalog_summary = write_working_memory_catalog(root)
        world_model_summary = refresh_descriptors_and_world_model(root)
    else:
        catalog_summary = {
            "output_path": "runtime/cortex/catalog/memory/working-memory.latest.json",
            "item_count": None,
            "content_digest": None,
        }
        world_model_summary = {
            "snapshot_ref": atlas_relative(root / "runtime" / "state" / "atlas" / "world-model.snapshot.latest.json", root=root),
            "attention_ref": atlas_relative(root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json", root=root),
        }

    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "initiative_count": len(written_initiatives),
                "proposal_count": len(written_proposals),
                "initiatives": written_initiatives,
                "proposals": written_proposals,
                "working_memory": catalog_summary,
                "world_model": world_model_summary,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
