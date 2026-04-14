from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from ops._atlas import atlas_relative, atlas_root, normalize_slashes

DESCRIPTOR_CONTRACT_VERSION = "atlas.artifact.descriptor.v1"
WORKER_CONTEXT_VERSION = "atlas.cortex.worker-context.v1"
SUPERVISOR_CONSUMER_VERSION = "atlas.stack.supervisor-consumer.v1"
LEGACY_RUNTIME_BACKFILL_VERSION = "atlas.legacy-runtime.backfill.v1"


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def stable_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256_bytes(encoded)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    rendered = json.dumps(payload, indent=2) + "\n"
    try:
        if path.exists() and path.read_text(encoding="utf-8") == rendered:
            return False
    except OSError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def iter_candidate_json_paths(paths: Iterable[Path]) -> list[Path]:
    results: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if not resolved.exists():
            continue
        if resolved.is_file():
            if resolved.suffix.lower() == ".json" and resolved not in seen:
                seen.add(resolved)
                results.append(resolved)
            continue
        for candidate in sorted(resolved.rglob("*.json")):
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            results.append(candidate)
    return results


def default_artifact_source_paths(root: Path | None = None) -> list[Path]:
    base = (root or atlas_root()).resolve()
    return [
        base / "runtime" / "atlas" / "sessions",
        base / "runtime" / "cortex" / "context",
        base / "runtime" / "cortex" / "supervisor",
        base / "runtime" / "lifeline" / "worker-execution",
        base / "runtime" / "cortex" / "catalog" / "knowledge",
        base / "runtime" / "state" / "atlas",
    ]


def descriptor_output_path(source_path: Path, output_dir: Path, *, root: Path | None = None) -> Path:
    source_relative = Path(atlas_relative(source_path, root=root or atlas_root()))
    if source_relative.suffix:
        target_relative = source_relative.with_suffix(".descriptor.json")
    else:
        target_relative = Path(f"{normalize_slashes(str(source_relative))}.descriptor.json")
    return output_dir / target_relative


def clean_refs(values: Iterable[Any]) -> list[str]:
    refs = [str(value).strip() for value in values if isinstance(value, str) and str(value).strip()]
    return sorted(set(refs))


def ordered_strings(values: Iterable[Any]) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        refs.append(stripped)
    return refs


def first_string(values: Iterable[Any]) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def action_summary(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for field in ("summary", "operation", "cwd"):
        candidate = value.get(field)
        if isinstance(candidate, str) and candidate.strip():
            result[field] = candidate.strip()
    command = ordered_strings(value.get("command", [])) if isinstance(value.get("command"), list) else []
    if command:
        result["command"] = command
    return result


def governed_surface_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "tool_id": None,
            "extension_id": None,
        }
    return {
        "tool_id": value.get("tool_id"),
        "extension_id": value.get("extension_id"),
    }


def governed_surface_identity(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool_id": payload.get("tool_id"),
        "extension_id": payload.get("extension_id"),
    }


def descriptor_base(
    *,
    artifact_class: str,
    artifact_type: str,
    schema_ref: str,
    digest: str,
    size_bytes: int,
    source_ref: str,
    trust_class: str,
    release_eligible: bool,
    retention_class: str,
    regulated_artifact_class: str,
    identity: dict[str, Any],
    state: dict[str, Any],
    links: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": DESCRIPTOR_CONTRACT_VERSION,
        "artifact_class": artifact_class,
        "artifact_type": artifact_type,
        "schema_ref": schema_ref,
        "digest": digest,
        "media_type": "application/json",
        "size_bytes": size_bytes,
        "source_ref": source_ref,
        "trust_class": trust_class,
        "release_eligible": release_eligible,
        "retention_class": retention_class,
        "regulated_artifact_class": regulated_artifact_class,
        "identity": identity,
        "state": state,
        "links": links,
    }


def build_session_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    worker = payload.get("worker", {})
    refs = payload.get("refs", {})
    completion = payload.get("completion", {})
    governed_surfaces = payload.get("governed_surfaces", {})
    context_surface = governed_surface_ref(governed_surfaces.get("context"))
    supervision_surface = governed_surface_ref(governed_surfaces.get("supervision"))
    execution_surface = governed_surface_ref(governed_surfaces.get("execution"))
    return descriptor_base(
        artifact_class="session",
        artifact_type="session_manifest",
        schema_ref="atlas.session.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="governed_session",
        identity={
            "session_id": payload.get("session_id"),
            "task_id": payload.get("task_id"),
            "worker_id": worker.get("worker_id"),
            "assignment_id": worker.get("assignment_id"),
            "context_tool_id": context_surface["tool_id"],
            "supervision_tool_id": supervision_surface["tool_id"],
            "execution_tool_id": execution_surface["tool_id"],
            "execution_extension_id": execution_surface["extension_id"],
        },
        state={
            "session_state": payload.get("session_state"),
            "scenario": payload.get("scenario"),
            "final_status": completion.get("final_status"),
            "updated_at": payload.get("updated_at"),
            "closed_at": payload.get("closed_at"),
            "registry_digest": governed_surfaces.get("registry_digest")
            if isinstance(governed_surfaces, dict)
            else None,
        },
        links={
            "context_ref": worker.get("context_ref"),
            "assignment_ref": worker.get("assignment_ref"),
            "governed_surfaces": {
                "context": context_surface,
                "supervision": supervision_surface,
                "execution": execution_surface,
            },
            "status_refs": clean_refs(refs.get("status_refs", [])),
            "capability_profile_ref": refs.get("capability_profile_ref"),
            "request_ref": refs.get("request_ref"),
            "approval_receipt_ref": refs.get("approval_receipt_ref"),
            "execution_receipt_ref": refs.get("execution_receipt_ref"),
            "bridge_record_ref": refs.get("bridge_record_ref"),
            "merge_request_refs": clean_refs(refs.get("merge_request_refs", [])),
            "pause_status_refs": clean_refs(refs.get("pause_status_refs", [])),
            "resume_context_refs": clean_refs(refs.get("resume_context_refs", [])),
            "merge_assignment_ref": refs.get("merge_assignment_ref"),
            "merge_prompt_ref": refs.get("merge_prompt_ref"),
            "merge_context_ref": refs.get("merge_context_ref"),
            "merge_completion_ref": refs.get("merge_completion_ref"),
            "close_receipt_refs": clean_refs(completion.get("close_receipt_refs", [])),
            "final_status_ref": completion.get("final_status_ref"),
        },
    )


def build_worker_context_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    assignment = payload.get("assignment", {})
    query = payload.get("query", {})
    return descriptor_base(
        artifact_class="coordination",
        artifact_type="worker_context",
        schema_ref=WORKER_CONTEXT_VERSION,
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="query_context",
        identity={
            "assignment_id": assignment.get("assignment_id"),
            "worker_id": assignment.get("worker_id"),
            "task_id": assignment.get("task_id"),
        },
        state={
            "result_count": payload.get("result_count"),
            "selection_limit": query.get("selection_limit"),
            "bundle_path": query.get("bundle_path"),
            "bundle_content_digest": query.get("bundle_content_digest"),
        },
        links={
            "query_terms": clean_refs(query.get("terms", [])),
            "task_tags": clean_refs(query.get("task_tags", [])),
            "archive_ids": clean_refs(
                item.get("archive_id")
                for item in payload.get("context_items", [])
                if isinstance(item, dict)
            ),
        },
    )


def build_worker_assignment_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    return descriptor_base(
        artifact_class="workflow",
        artifact_type="worker_assignment",
        schema_ref="atlas.worker.assignment.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="workflow_assignment",
        identity={
            "assignment_id": payload.get("assignment_id"),
            "worker_id": payload.get("worker_id"),
            "task_id": payload.get("task_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "stack_lock_digest": payload.get("stack_lock_digest"),
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "allowed_globs": clean_refs(payload.get("allowed_globs", [])),
            "forbidden_globs": clean_refs(payload.get("forbidden_globs", [])),
            "input_handoff_refs": clean_refs(payload.get("input_handoff_refs", [])),
            "expected_outputs": clean_refs(payload.get("expected_outputs", [])),
        },
    )


def build_worker_status_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    return descriptor_base(
        artifact_class="workflow",
        artifact_type="worker_status",
        schema_ref="atlas.worker.status.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="workflow_status",
        identity={
            "assignment_id": payload.get("assignment_id"),
            "worker_id": payload.get("worker_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "worker_state": payload.get("state"),
            "heartbeat_at": payload.get("heartbeat_at"),
            "blocked_reason": payload.get("blocked_reason"),
            "touched_range_count": len(payload.get("touched_ranges", [])) if isinstance(payload.get("touched_ranges"), list) else 0,
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "output_refs": clean_refs(payload.get("output_refs", [])),
            "merge_request_ref": payload.get("merge_request_ref"),
        },
    )


def build_merge_request_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    return descriptor_base(
        artifact_class="workflow",
        artifact_type="merge_request",
        schema_ref="atlas.worker.merge-request.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="merge_request",
        identity={
            "merge_request_id": payload.get("merge_request_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "stack_lock_digest": payload.get("stack_lock_digest"),
            "overlap_count": len(payload.get("overlaps", [])) if isinstance(payload.get("overlaps"), list) else 0,
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "conflicting_workers": clean_refs(payload.get("conflicting_workers", [])),
            "paused_handoff_refs": clean_refs(payload.get("paused_handoff_refs", [])),
            "merge_worker_assignment_id": payload.get("merge_worker_handoff", {}).get("assignment_id")
            if isinstance(payload.get("merge_worker_handoff"), dict)
            else None,
            "merge_worker_handoff_ref": payload.get("merge_worker_handoff", {}).get("handoff_ref")
            if isinstance(payload.get("merge_worker_handoff"), dict)
            else None,
            "merge_worker_tool_id": payload.get("merge_worker_handoff", {}).get("tool_id")
            if isinstance(payload.get("merge_worker_handoff"), dict)
            else None,
            "merge_worker_extension_id": payload.get("merge_worker_handoff", {}).get("extension_id")
            if isinstance(payload.get("merge_worker_handoff"), dict)
            else None,
            "overlap_paths": clean_refs(
                item.get("path")
                for item in payload.get("overlaps", [])
                if isinstance(item, dict)
            ),
        },
    )


def build_capability_profile_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    return descriptor_base(
        artifact_class="governance",
        artifact_type="capability_profile",
        schema_ref="atlas.capability.profile.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="capability_profile",
        identity={
            "capability_profile_id": payload.get("capability_profile_id"),
        },
        state={
            "elevation_requirement": payload.get("elevation_requirement"),
            "audit_class": payload.get("audit_class"),
        },
        links={
            "allowed_data_classes": clean_refs(payload.get("allowed_data_classes", [])),
            "filesystem_read_scopes": clean_refs(payload.get("filesystem_scopes", {}).get("read", []))
            if isinstance(payload.get("filesystem_scopes"), dict)
            else [],
            "allowed_commands": clean_refs(payload.get("process_execution_permissions", {}).get("allowed_commands", []))
            if isinstance(payload.get("process_execution_permissions"), dict)
            else [],
        },
    )


def build_privileged_request_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    requested_capability = payload.get("requested_capability", {})
    return descriptor_base(
        artifact_class="execution",
        artifact_type="privileged_action_request",
        schema_ref="atlas.privileged-action.request.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="execution_request",
        identity={
            "request_id": payload.get("request_id"),
            "worker_id": payload.get("worker_id"),
            "assignment_id": payload.get("assignment_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "requested_at": payload.get("requested_at"),
            "operation": payload.get("action", {}).get("operation") if isinstance(payload.get("action"), dict) else None,
            "capability_profile_id": requested_capability.get("capability_profile_id")
            if isinstance(requested_capability, dict)
            else None,
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "source_refs": clean_refs(payload.get("source_refs", [])),
            "target_paths": clean_refs(payload.get("target_paths", [])),
            "target_resources": clean_refs(payload.get("target_resources", [])),
            "action": action_summary(payload.get("action") if isinstance(payload.get("action"), dict) else None),
        },
    )


def build_approval_receipt_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    return descriptor_base(
        artifact_class="execution",
        artifact_type="approval_receipt",
        schema_ref="atlas.approval.receipt.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="approval_receipt",
        identity={
            "approval_receipt_id": payload.get("approval_receipt_id"),
            "request_id": payload.get("request_id"),
            "worker_id": payload.get("worker_id"),
            "assignment_id": payload.get("assignment_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "approval_status": payload.get("approval_status"),
            "issued_at": payload.get("issued_at"),
            "expiry_at": payload.get("expiry_at"),
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "request_digest": payload.get("request_digest"),
            "approver_kind": payload.get("approver", {}).get("kind") if isinstance(payload.get("approver"), dict) else None,
            "approver_name": payload.get("approver", {}).get("name") if isinstance(payload.get("approver"), dict) else None,
        },
    )


def build_execution_receipt_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    requested_action = payload.get("requested_action") if isinstance(payload.get("requested_action"), dict) else None
    executed_action = payload.get("executed_action") if isinstance(payload.get("executed_action"), dict) else None
    return descriptor_base(
        artifact_class="execution",
        artifact_type="execution_receipt",
        schema_ref="atlas.privileged-action.receipt.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="execution_receipt",
        identity={
            "receipt_id": payload.get("receipt_id"),
            "request_id": payload.get("request_id"),
            "approval_receipt_id": payload.get("approval_receipt_id"),
            "worker_id": payload.get("worker_id"),
            "assignment_id": payload.get("assignment_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "result": payload.get("result"),
            "approval_status": payload.get("approval_status"),
            "execution_mode": payload.get("execution_mode"),
            "executed_at": payload.get("executed_at"),
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "source_refs": clean_refs(payload.get("source_refs", [])),
            "target_paths": clean_refs(payload.get("target_paths", [])),
            "target_resources": clean_refs(payload.get("target_resources", [])),
            "request_digest": payload.get("request_digest"),
            "capability_profile_digest": payload.get("capability_profile_digest"),
            "action": action_summary(requested_action or executed_action),
        },
    )


def build_supervisor_consumer_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    return descriptor_base(
        artifact_class="workflow",
        artifact_type="supervisor_merge_completion",
        schema_ref=SUPERVISOR_CONSUMER_VERSION,
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="merge_completion",
        identity={
            "merge_request_id": payload.get("merge_request_id"),
            "tool_id": payload.get("tool_id"),
            "extension_id": payload.get("extension_id"),
        },
        state={
            "stack_lock_digest": payload.get("stack_lock_digest"),
            "transcript_dependency": payload.get("transcript_dependency"),
            "registry_digest": payload.get("registry_digest"),
        },
        links={
            "merge_request_ref": payload.get("merge_request_ref"),
            "merge_assignment_ref": payload.get("merge_assignment_ref"),
            "merge_prompt_ref": payload.get("merge_prompt_ref"),
            "merge_context_ref": payload.get("merge_context_ref"),
            "merge_handoff_ref": payload.get("merge_handoff_ref"),
            "pause_status_refs": clean_refs(
                item.get("path")
                for item in payload.get("pause_statuses", [])
                if isinstance(item, dict)
            ),
            "resume_context_refs": clean_refs(
                item.get("path")
                for item in payload.get("resume_contexts", [])
                if isinstance(item, dict)
            ),
        },
    )


def build_knowledge_catalog_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    archive_id = str(payload.get("archive_id", ""))
    trust_class = "untrusted" if archive_id.startswith("personal--verta-core") else (
        "trusted" if payload.get("promotion_status") == "promoted" else "adjacent"
    )
    return descriptor_base(
        artifact_class="knowledge",
        artifact_type="knowledge_catalog",
        schema_ref="atlas.knowledge.runtime-catalog.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class=trust_class,
        release_eligible=False,
        retention_class=str(payload.get("retention_class", "operational")),
        regulated_artifact_class=str(payload.get("indexing_profile", "metadata_only")),
        identity={
            "archive_id": payload.get("archive_id"),
            "source_name": payload.get("source_name"),
        },
        state={
            "safe_for_indexing": payload.get("safe_for_indexing"),
            "indexing_profile": payload.get("indexing_profile"),
            "promotion_status": payload.get("promotion_status"),
            "normalization_allowed": payload.get("normalization_allowed"),
            "no_execute_guarantee": payload.get("no_execute_guarantee"),
        },
        links={
            "promotion_doc_path": payload.get("promotion_doc_path"),
            "import_dir": payload.get("import_dir"),
            "manifest_path": payload.get("manifest_path"),
            "evaluation_path": payload.get("evaluation_path"),
        },
    )


def build_state_snapshot_descriptor(payload: dict[str, Any], *, digest: str, size_bytes: int, source_ref: str) -> dict[str, Any]:
    snapshot_kind = str(payload.get("snapshot_kind", "state"))
    artifact_type = "attention_snapshot" if snapshot_kind == "attention" else "state_snapshot"
    summary = payload.get("summary", {})
    active_session = payload.get("active_session", {})
    return descriptor_base(
        artifact_class="coordination",
        artifact_type=artifact_type,
        schema_ref="atlas.state.snapshot.v1",
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="world_model",
        identity={
            "snapshot_kind": snapshot_kind,
            "active_session_id": active_session.get("session_id") if isinstance(active_session, dict) else None,
        },
        state={
            "content_digest": payload.get("content_digest"),
            "inventory_entry_count": summary.get("inventory_entry_count"),
            "observation_count": summary.get("observation_count"),
            "attention_item_count": summary.get("attention_item_count"),
            "highest_severity": summary.get("highest_severity") or summary.get("attention_highest_severity"),
            "registry_digest": summary.get("registry_digest"),
        },
        links={
            "descriptor_root": payload.get("source_refs", {}).get("descriptor_root")
            if isinstance(payload.get("source_refs"), dict)
            else None,
            "event_latest_refs": clean_refs(payload.get("source_refs", {}).get("event_latest_refs", []))
            if isinstance(payload.get("source_refs"), dict)
            else [],
            "knowledge_latest_refs": clean_refs(payload.get("source_refs", {}).get("knowledge_latest_refs", []))
            if isinstance(payload.get("source_refs"), dict)
            else [],
            "validation_refs": clean_refs(payload.get("source_refs", {}).get("validation_refs", []))
            if isinstance(payload.get("source_refs"), dict)
            else [],
        },
    )


def build_legacy_runtime_backfill_descriptor(
    payload: dict[str, Any],
    *,
    digest: str,
    size_bytes: int,
    source_ref: str,
) -> dict[str, Any]:
    identity_resolution = payload.get("governed_identity") if isinstance(payload.get("governed_identity"), dict) else {}
    context_identity = identity_resolution.get("context") if isinstance(identity_resolution.get("context"), dict) else {}
    supervision_identity = (
        identity_resolution.get("supervision") if isinstance(identity_resolution.get("supervision"), dict) else {}
    )
    execution_identity = identity_resolution.get("execution") if isinstance(identity_resolution.get("execution"), dict) else {}
    registry_identity = identity_resolution.get("registry_digest") if isinstance(identity_resolution.get("registry_digest"), dict) else {}
    worker = payload.get("worker") if isinstance(payload.get("worker"), dict) else {}
    return descriptor_base(
        artifact_class="compatibility",
        artifact_type="legacy_runtime_backfill",
        schema_ref=LEGACY_RUNTIME_BACKFILL_VERSION,
        digest=digest,
        size_bytes=size_bytes,
        source_ref=source_ref,
        trust_class="trusted",
        release_eligible=False,
        retention_class="runtime",
        regulated_artifact_class="legacy_compatibility",
        identity={
            "session_id": payload.get("session_id"),
            "task_id": payload.get("task_id"),
            "worker_id": worker.get("worker_id"),
            "assignment_id": worker.get("assignment_id"),
            "context_tool_id": context_identity.get("tool_id"),
            "supervision_tool_id": supervision_identity.get("tool_id"),
            "execution_tool_id": execution_identity.get("tool_id"),
            "execution_extension_id": execution_identity.get("extension_id"),
        },
        state={
            "session_state": payload.get("session_state"),
            "final_status": payload.get("final_status"),
            "compatibility_class": payload.get("compatibility_class"),
            "cutover_at": payload.get("cutover_at"),
            "observed_at": payload.get("observed_at"),
            "recorded_at": payload.get("recorded_at"),
            "backfill_status": payload.get("backfill_status"),
            "registry_digest": registry_identity.get("value"),
        },
        links={
            "original_session_ref": payload.get("original_session_ref"),
            "source_refs": clean_refs(payload.get("source_refs", [])),
            "missing_governed_requirements": clean_refs(payload.get("missing_governed_requirements", [])),
            "inference_basis": payload.get("inference_basis", []),
            "governed_identity": identity_resolution,
            "source_ref_digests": payload.get("source_ref_digests", []),
        },
    )


def build_descriptor_for_payload(path: Path, payload: dict[str, Any], *, root: Path | None = None) -> dict[str, Any] | None:
    data = path.read_bytes()
    digest = sha256_bytes(data)
    size_bytes = len(data)
    source_ref = atlas_relative(path, root=root or atlas_root())
    contract_version = str(payload.get("contract_version", ""))
    schema_version = str(payload.get("schema_version", ""))

    if contract_version == "atlas.session.v1":
        return build_session_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if schema_version == WORKER_CONTEXT_VERSION:
        return build_worker_context_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.worker.assignment.v1":
        return build_worker_assignment_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.worker.status.v1":
        return build_worker_status_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.worker.merge-request.v1":
        return build_merge_request_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.capability.profile.v1":
        return build_capability_profile_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.privileged-action.request.v1":
        return build_privileged_request_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.approval.receipt.v1":
        return build_approval_receipt_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.privileged-action.receipt.v1":
        return build_execution_receipt_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if schema_version == SUPERVISOR_CONSUMER_VERSION:
        return build_supervisor_consumer_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == "atlas.state.snapshot.v1":
        return build_state_snapshot_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if contract_version == LEGACY_RUNTIME_BACKFILL_VERSION:
        return build_legacy_runtime_backfill_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    if "archive_id" in payload and "indexing_profile" in payload and "promotion_status" in payload:
        return build_knowledge_catalog_descriptor(payload, digest=digest, size_bytes=size_bytes, source_ref=source_ref)
    return None


def register_artifact_descriptors(
    paths: Iterable[Path],
    *,
    output_dir: Path,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    base = (root or atlas_root()).resolve()
    output_root = output_dir.resolve()
    written: list[dict[str, Any]] = []
    for path in iter_candidate_json_paths(paths):
        try:
            payload = read_json(path)
        except Exception:
            continue
        descriptor = build_descriptor_for_payload(path, payload, root=base)
        if descriptor is None:
            continue
        target_path = descriptor_output_path(path, output_root, root=base)
        write_json(target_path, descriptor)
        written.append(
            {
                "source_ref": atlas_relative(path, root=base),
                "descriptor_ref": atlas_relative(target_path, root=base),
                "artifact_type": descriptor["artifact_type"],
                "digest": descriptor["digest"],
            }
        )
    written.sort(key=lambda item: (str(item["artifact_type"]), str(item["source_ref"])))
    return written


def load_descriptors(descriptor_root: Path) -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    for path in iter_candidate_json_paths([descriptor_root]):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if payload.get("contract_version") != DESCRIPTOR_CONTRACT_VERSION:
            continue
        descriptors.append(payload)
    descriptors.sort(key=lambda item: (str(item.get("artifact_type", "")), str(item.get("source_ref", ""))))
    return descriptors
