from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, load_repo_registry
from ops.atlas.observations import canonical_observation_type, emit_observation, load_observations
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import load_descriptors, read_json, stable_json_digest, write_json
from ops.cortex.index_working_memory import load_working_memory_catalog, write_working_memory_catalog
from ops.cortex.render_status import latest_worker_states, render_status_payload

SNAPSHOT_CONTRACT_VERSION = "atlas.state.snapshot.v1"
OBSERVATION_CONTRACT_VERSION = "atlas.observation.v1"
ATTENTION_ITEM_CONTRACT_VERSION = "atlas.attention.item.v1"
INVENTORY_ENTRY_CONTRACT_VERSION = "atlas.inventory.entry.v1"


def stable_item_id(payload: dict[str, Any]) -> str:
    return stable_json_digest(payload)


def world_model_state_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "state" / "atlas"


def snapshot_output_path(root: Path | None = None) -> Path:
    return world_model_state_root(root) / "world-model.snapshot.latest.json"


def attention_output_path(root: Path | None = None) -> Path:
    return world_model_state_root(root) / "world-model.attention.latest.json"


def relative_paths(paths: list[Path], *, root: Path) -> list[str]:
    return sorted(atlas_relative(path, root=root) for path in paths if path.exists())


def latest_receipt_paths(root: Path, relative_dir: str) -> list[Path]:
    base = root / Path(relative_dir)
    if not base.exists():
        return []
    results: list[Path] = []
    for latest in sorted(base.rglob("latest.json")):
        if latest.is_file():
            results.append(latest.resolve())
    return results


def validation_receipt_paths(root: Path) -> list[Path]:
    base = root / "runtime" / "receipts" / "validation"
    if not base.exists():
        return []
    names = ["stack-validation.latest.json"]
    return [path.resolve() for name in names if (path := base / name).exists()]


def working_memory_catalog_ref(root: Path) -> str:
    catalog = load_working_memory_catalog(root)
    return str(catalog.get("output_path", "runtime/cortex/catalog/memory/working-memory.latest.json"))


def build_inventory_entry(
    *,
    entry_type: str,
    key: str,
    label: str,
    status: str,
    source_ref: str,
    trust_class: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "contract_version": INVENTORY_ENTRY_CONTRACT_VERSION,
        "entry_type": entry_type,
        "key": key,
        "label": label,
        "status": status,
        "trust_class": trust_class,
        "source_ref": source_ref,
        "details": details or {},
    }
    return {
        **base,
        "entry_id": stable_item_id(base),
    }


def build_observation(
    *,
    observation_type: str,
    source_kind: str,
    status: str,
    source_ref: str,
    observed_at: str | None,
    scope_ref: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "contract_version": OBSERVATION_CONTRACT_VERSION,
        "observation_type": observation_type,
        "source_kind": source_kind,
        "status": status,
        "observed_at": observed_at,
        "source_ref": source_ref,
        "scope_ref": scope_ref,
        "details": details or {},
    }
    return {
        **base,
        "observation_id": stable_item_id(base),
    }


def build_attention_item(
    *,
    kind: str,
    severity: str,
    summary: str,
    source_ref: str | None,
    observation_ids: list[str],
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "contract_version": ATTENTION_ITEM_CONTRACT_VERSION,
        "kind": kind,
        "severity": severity,
        "summary": summary,
        "status": "open",
        "source_ref": source_ref,
        "observation_ids": sorted(set(observation_ids)),
        "details": details or {},
    }
    return {
        **base,
        "attention_id": stable_item_id(base),
    }


def build_inventory_entries(
    *,
    root: Path,
    descriptors: list[dict[str, Any]],
    registry_bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    repo_registry = load_repo_registry(root=root)

    for repo_id, repo in sorted(repo_registry.items()):
        entries.append(
            build_inventory_entry(
                entry_type="repo",
                key=repo_id,
                label=repo_id,
                status=repo.status,
                source_ref=repo.atlas_path,
                trust_class=None,
                details={
                    "role": repo.role,
                    "path": repo.atlas_path,
                },
            )
        )

    for tool in registry_bundle.get("tool_registry", {}).get("entries", []):
        if not isinstance(tool, dict):
            continue
        tool_id = str(tool.get("tool_id", "")).strip()
        if not tool_id:
            continue
        entries.append(
            build_inventory_entry(
                entry_type="tool",
                key=tool_id,
                label=str(tool.get("display_name", tool_id)),
                status=str(tool.get("status", "unknown")),
                source_ref="docs/registry/ATLAS-TOOL-REGISTRY.json",
                trust_class=str(tool.get("trust_class")) if tool.get("trust_class") is not None else None,
                details={
                    "surface_kind": tool.get("surface_kind"),
                    "owner": tool.get("owner"),
                    "extension_id": tool.get("extension_id"),
                },
            )
        )

    for extension in registry_bundle.get("extension_registry", {}).get("entries", []):
        if not isinstance(extension, dict):
            continue
        extension_id = str(extension.get("extension_id", "")).strip()
        if not extension_id:
            continue
        entries.append(
            build_inventory_entry(
                entry_type="extension",
                key=extension_id,
                label=str(extension.get("display_name", extension_id)),
                status=str(extension.get("status", "unknown")),
                source_ref="docs/registry/ATLAS-EXTENSION-REGISTRY.json",
                trust_class=str(extension.get("trust_class")) if extension.get("trust_class") is not None else None,
                details={
                    "owner": extension.get("owner"),
                    "tool_ids": extension.get("tool_ids", []),
                },
            )
        )

    for descriptor in descriptors:
        artifact_type = str(descriptor.get("artifact_type", "")).strip()
        source_ref = str(descriptor.get("source_ref", "")).strip()
        trust_class = descriptor.get("trust_class")
        identity = descriptor.get("identity", {})
        state = descriptor.get("state", {})
        if artifact_type in {"state_snapshot", "attention_snapshot"}:
            continue
        if artifact_type == "session_manifest":
            session_id = str(identity.get("session_id", "")).strip()
            if session_id:
                entries.append(
                    build_inventory_entry(
                        entry_type="session",
                        key=session_id,
                        label=session_id,
                        status=str(state.get("session_state", "unknown")),
                        source_ref=source_ref,
                        trust_class=str(trust_class) if trust_class is not None else None,
                        details={
                            "task_id": identity.get("task_id"),
                            "worker_id": identity.get("worker_id"),
                            "assignment_id": identity.get("assignment_id"),
                            "final_status": state.get("final_status"),
                        },
                    )
                )
        elif artifact_type == "worker_status":
            worker_id = str(identity.get("worker_id", "")).strip()
            if worker_id:
                entries.append(
                    build_inventory_entry(
                        entry_type="worker",
                        key=f"{worker_id}:{identity.get('assignment_id')}",
                        label=worker_id,
                        status=str(state.get("worker_state", "unknown")),
                        source_ref=source_ref,
                        trust_class=str(trust_class) if trust_class is not None else None,
                        details={
                            "assignment_id": identity.get("assignment_id"),
                            "tool_id": identity.get("tool_id"),
                            "extension_id": identity.get("extension_id"),
                            "blocked_reason": state.get("blocked_reason"),
                        },
                    )
                )
        elif artifact_type == "knowledge_catalog":
            archive_id = str(identity.get("archive_id", "")).strip()
            if archive_id:
                entries.append(
                    build_inventory_entry(
                        entry_type="knowledge",
                        key=archive_id,
                        label=archive_id,
                        status=str(state.get("promotion_status", "unknown")),
                        source_ref=source_ref,
                        trust_class=str(trust_class) if trust_class is not None else None,
                        details={
                            "indexing_profile": state.get("indexing_profile"),
                            "safe_for_indexing": state.get("safe_for_indexing"),
                            "normalization_allowed": state.get("normalization_allowed"),
                        },
                    )
                )

        artifact_key = f"{artifact_type}:{source_ref}"
        entries.append(
            build_inventory_entry(
                entry_type="artifact",
                key=artifact_key,
                label=artifact_type or "artifact",
                status=str(state.get("result") or state.get("worker_state") or state.get("session_state") or "recorded"),
                source_ref=source_ref,
                trust_class=str(trust_class) if trust_class is not None else None,
                details={
                    "artifact_type": artifact_type,
                    "digest": descriptor.get("digest"),
                    "schema_ref": descriptor.get("schema_ref"),
                },
            )
        )

    working_memory = load_working_memory_catalog(root)
    for item in working_memory.get("items", []):
        if not isinstance(item, dict):
            continue
        memory_id = str(item.get("id", "")).strip()
        if not memory_id:
            continue
        entries.append(
            build_inventory_entry(
                entry_type="memory",
                key=memory_id,
                label=str(item.get("title") or memory_id),
                status=str(item.get("status", "unknown")),
                source_ref=str(item.get("path") or working_memory.get("output_path") or "docs/memory"),
                trust_class="trusted",
                details={
                    "memory_kind": item.get("memory_kind"),
                    "owner": item.get("owner"),
                    "related_session_refs": item.get("related_session_refs", []),
                    "related_artifact_refs": item.get("related_artifact_refs", []),
                    "evidence_refs": item.get("evidence_refs", []),
                },
            )
        )

    entries.sort(key=lambda item: (item["entry_type"], item["key"], item["source_ref"]))
    return entries


def build_observations(
    *,
    root: Path,
    descriptors: list[dict[str, Any]],
    registry_bundle: dict[str, Any],
    event_latest: list[Path],
    knowledge_latest: list[Path],
    validation_latest: list[Path],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    observations.append(
        build_observation(
            observation_type="registry_bundle",
            source_kind="registry",
            status="loaded",
            observed_at=None,
            source_ref="docs/registry",
            details={
                "registry_digest": registry_bundle.get("registry_digest"),
                "tool_count": registry_bundle.get("tool_count"),
                "extension_count": registry_bundle.get("extension_count"),
            },
        )
    )

    for path in event_latest:
        payload = read_json(path)
        event = payload.get("event", {})
        processing = payload.get("processing", {})
        source_ref = atlas_relative(path, root=root)
        observations.append(
            build_observation(
                observation_type=f"event_receipt.{event.get('event_type', 'unknown')}",
                source_kind="event_receipt",
                status=str(processing.get("status", "unknown")),
                observed_at=str(payload.get("recorded_at")) if payload.get("recorded_at") is not None else None,
                source_ref=source_ref,
                scope_ref=str(event.get("session", {}).get("session_id")) if isinstance(event.get("session"), dict) else None,
                details={
                    "receipt_id": payload.get("receipt_id"),
                    "accepted": processing.get("accepted"),
                    "error_count": len(processing.get("errors", [])) if isinstance(processing.get("errors"), list) else 0,
                },
            )
        )

    for path in knowledge_latest:
        payload = read_json(path)
        source_ref = atlas_relative(path, root=root)
        observations.append(
            build_observation(
                observation_type=f"knowledge_receipt.{payload.get('action', 'unknown')}",
                source_kind="knowledge_receipt",
                status="blocked" if payload.get("promotion_blocked") else "recorded",
                observed_at=str(payload.get("recorded_at")) if payload.get("recorded_at") is not None else None,
                source_ref=source_ref,
                scope_ref=str(payload.get("archive_id")) if payload.get("archive_id") is not None else None,
                details={
                    "archive_id": payload.get("archive_id"),
                    "promotion_status": payload.get("promotion", {}).get("promotion_status")
                    if isinstance(payload.get("promotion"), dict)
                    else None,
                    "indexing_profile": payload.get("promotion", {}).get("indexing_profile")
                    if isinstance(payload.get("promotion"), dict)
                    else None,
                },
            )
        )

    for path in validation_latest:
        payload = read_json(path)
        summary = payload.get("summary", {})
        source_ref = atlas_relative(path, root=root)
        observations.append(
            build_observation(
                observation_type="validation.stack",
                source_kind="validation_receipt",
                status="blocking" if (summary.get("critical", 0) or summary.get("error", 0)) else "clean",
                observed_at=str(payload.get("generated_at")) if payload.get("generated_at") is not None else None,
                source_ref=source_ref,
                scope_ref="stack",
                details={
                    "critical": summary.get("critical"),
                    "error": summary.get("error"),
                    "warning": summary.get("warning"),
                    "total": summary.get("total"),
                },
            )
        )

    for descriptor in descriptors:
        artifact_type = str(descriptor.get("artifact_type", "")).strip()
        source_ref = str(descriptor.get("source_ref", "")).strip()
        identity = descriptor.get("identity", {})
        state = descriptor.get("state", {})
        if artifact_type == "session_manifest":
            observations.append(
                build_observation(
                    observation_type="session.state",
                    source_kind="descriptor",
                    status=str(state.get("session_state", "unknown")),
                    observed_at=str(state.get("updated_at")) if state.get("updated_at") is not None else None,
                    source_ref=source_ref,
                    scope_ref=str(identity.get("session_id")) if identity.get("session_id") is not None else None,
                    details={
                        "task_id": identity.get("task_id"),
                        "final_status": state.get("final_status"),
                    },
                )
            )
        elif artifact_type == "execution_receipt":
            observations.append(
                build_observation(
                    observation_type="execution.result",
                    source_kind="descriptor",
                    status=str(state.get("result", "unknown")),
                    observed_at=str(state.get("executed_at")) if state.get("executed_at") is not None else None,
                    source_ref=source_ref,
                    scope_ref=str(identity.get("receipt_id")) if identity.get("receipt_id") is not None else None,
                    details={
                        "worker_id": identity.get("worker_id"),
                        "assignment_id": identity.get("assignment_id"),
                        "tool_id": identity.get("tool_id"),
                    },
                )
            )

    for descriptor in latest_worker_states(descriptors):
        identity = descriptor.get("identity", {})
        state = descriptor.get("state", {})
        source_ref = str(descriptor.get("source_ref", "")).strip()
        observations.append(
            build_observation(
                observation_type="worker.state",
                source_kind="descriptor",
                status=str(state.get("worker_state", "unknown")),
                observed_at=str(state.get("heartbeat_at")) if state.get("heartbeat_at") is not None else None,
                source_ref=source_ref,
                scope_ref=str(identity.get("worker_id")) if identity.get("worker_id") is not None else None,
                details={
                    "assignment_id": identity.get("assignment_id"),
                    "blocked_reason": state.get("blocked_reason"),
                },
            )
        )

    observations.extend(
        build_governed_session_observations(
            root=root,
            descriptors=descriptors,
        )
    )
    observations.sort(key=lambda item: (item["observation_type"], item["source_ref"], item["status"]))
    return observations


def load_source_payload(root: Path, source_ref: str | None) -> dict[str, Any] | None:
    if not isinstance(source_ref, str) or not source_ref.strip():
        return None
    candidate = (root / Path(source_ref)).resolve()
    if not candidate.exists():
        return None
    try:
        payload = read_json(candidate)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def unique_source_refs(*values: Any) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
        elif isinstance(value, list):
            refs.extend(
                str(item).strip()
                for item in value
                if isinstance(item, str) and str(item).strip()
            )
    return sorted(set(refs))


def optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def approval_has_expired(approval_payload: dict[str, Any]) -> bool:
    expiry_at = optional_string(approval_payload.get("expiry_at"))
    if not expiry_at:
        return False
    try:
        expiry = expiry_at.replace("Z", "+00:00")
        return datetime.fromisoformat(expiry) <= datetime.now(timezone.utc)
    except ValueError:
        return False


def governed_observation_details(
    *,
    session_id: str,
    stack_lock_digest: str,
    tool_id: str,
    registry_digest: str,
    source_artifact_refs: list[str],
    worker_id: str | None = None,
    assignment_id: str | None = None,
    extension_id: str | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    details: dict[str, Any] = {
        "session_id": session_id,
        "stack_lock_digest": stack_lock_digest,
        "tool_id": tool_id,
        "registry_digest": registry_digest,
        "source_artifact_refs": unique_source_refs(source_artifact_refs),
    }
    if worker_id:
        details["worker_id"] = worker_id
    if assignment_id:
        details["assignment_id"] = assignment_id
    if extension_id:
        details["extension_id"] = extension_id
    for key, value in (extras or {}).items():
        if value is not None:
            details[key] = value
    return details


def maybe_add_observation(
    target: list[dict[str, Any]],
    *,
    observation_type: str,
    status: str,
    source_ref: str | None,
    observed_at: str | None,
    session_id: str,
    stack_lock_digest: str,
    tool_id: str,
    registry_digest: str,
    source_artifact_refs: list[str],
    worker_id: str | None = None,
    assignment_id: str | None = None,
    extension_id: str | None = None,
    extras: dict[str, Any] | None = None,
) -> None:
    normalized_source_ref = optional_string(source_ref)
    if not normalized_source_ref:
        return
    target.append(
        build_observation(
            observation_type=observation_type,
            source_kind="governed_flow",
            status=status,
            observed_at=observed_at,
            source_ref=normalized_source_ref,
            scope_ref=session_id,
            details=governed_observation_details(
                session_id=session_id,
                worker_id=worker_id,
                assignment_id=assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=tool_id,
                extension_id=extension_id,
                registry_digest=registry_digest,
                source_artifact_refs=source_artifact_refs,
                extras=extras,
            ),
        )
    )


def build_governed_session_observations(
    *,
    root: Path,
    descriptors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for descriptor in descriptors:
        if str(descriptor.get("artifact_type", "")) != "session_manifest":
            continue

        source_ref = optional_string(descriptor.get("source_ref"))
        session_payload = load_source_payload(root, source_ref)
        if not session_payload:
            continue

        governed_surfaces = session_payload.get("governed_surfaces")
        if not isinstance(governed_surfaces, dict):
            continue
        execution_surface = governed_surfaces.get("execution")
        if not isinstance(execution_surface, dict):
            continue

        session_id = optional_string(session_payload.get("session_id")) or optional_string(descriptor.get("identity", {}).get("session_id"))
        worker_id = optional_string(session_payload.get("worker", {}).get("worker_id")) or optional_string(descriptor.get("identity", {}).get("worker_id"))
        assignment_id = optional_string(session_payload.get("worker", {}).get("assignment_id")) or optional_string(descriptor.get("identity", {}).get("assignment_id"))
        stack_lock_digest = optional_string(session_payload.get("stack_lock_digest"))
        tool_id = optional_string(execution_surface.get("tool_id")) or optional_string(descriptor.get("identity", {}).get("execution_tool_id"))
        extension_id = optional_string(execution_surface.get("extension_id")) or optional_string(descriptor.get("identity", {}).get("execution_extension_id"))
        registry_digest = optional_string(governed_surfaces.get("registry_digest")) or optional_string(descriptor.get("state", {}).get("registry_digest"))
        refs = session_payload.get("refs") if isinstance(session_payload.get("refs"), dict) else {}
        completion = session_payload.get("completion") if isinstance(session_payload.get("completion"), dict) else {}
        if not session_id or not stack_lock_digest or not tool_id or not registry_digest:
            continue

        assignment_ref = optional_string(session_payload.get("worker", {}).get("assignment_ref")) or optional_string(refs.get("assignment_ref")) or optional_string(descriptor.get("links", {}).get("assignment_ref"))
        request_ref = optional_string(refs.get("request_ref")) or optional_string(descriptor.get("links", {}).get("request_ref"))
        approval_ref = optional_string(refs.get("approval_receipt_ref")) or optional_string(descriptor.get("links", {}).get("approval_receipt_ref"))
        execution_receipt_ref = optional_string(refs.get("execution_receipt_ref")) or optional_string(descriptor.get("links", {}).get("execution_receipt_ref"))
        merge_request_refs = unique_source_refs(refs.get("merge_request_refs"), descriptor.get("links", {}).get("merge_request_refs"))
        pause_status_refs = unique_source_refs(refs.get("pause_status_refs"), descriptor.get("links", {}).get("pause_status_refs"))
        resume_context_refs = unique_source_refs(refs.get("resume_context_refs"), descriptor.get("links", {}).get("resume_context_refs"))
        merge_assignment_ref = optional_string(refs.get("merge_assignment_ref")) or optional_string(descriptor.get("links", {}).get("merge_assignment_ref"))
        merge_context_ref = optional_string(refs.get("merge_context_ref")) or optional_string(descriptor.get("links", {}).get("merge_context_ref"))
        merge_prompt_ref = optional_string(refs.get("merge_prompt_ref")) or optional_string(descriptor.get("links", {}).get("merge_prompt_ref"))
        merge_completion_ref = optional_string(refs.get("merge_completion_ref")) or optional_string(descriptor.get("links", {}).get("merge_completion_ref"))
        close_receipt_refs = unique_source_refs(completion.get("close_receipt_refs"), descriptor.get("links", {}).get("close_receipt_refs"))
        final_status = optional_string(completion.get("final_status")) or optional_string(descriptor.get("state", {}).get("final_status"))
        final_status_ref = optional_string(completion.get("final_status_ref")) or optional_string(descriptor.get("links", {}).get("final_status_ref"))
        session_updated_at = optional_string(session_payload.get("updated_at")) or optional_string(descriptor.get("state", {}).get("updated_at"))
        session_created_at = optional_string(session_payload.get("created_at"))
        session_closed_at = optional_string(session_payload.get("closed_at")) or optional_string(descriptor.get("state", {}).get("closed_at"))

        if assignment_ref:
            maybe_add_observation(
                observations,
                observation_type="assignment_created",
                status="emitted",
                source_ref=assignment_ref,
                observed_at=session_created_at or session_updated_at,
                session_id=session_id,
                worker_id=worker_id,
                assignment_id=assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=tool_id,
                extension_id=extension_id,
                registry_digest=registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, assignment_ref),
            )

        running_status_ref: str | None = None
        running_status_payload: dict[str, Any] | None = None
        for status_ref in unique_source_refs(refs.get("status_refs"), descriptor.get("links", {}).get("status_refs")):
            status_payload = load_source_payload(root, status_ref)
            if isinstance(status_payload, dict) and optional_string(status_payload.get("state")) == "running":
                running_status_ref = status_ref
                running_status_payload = status_payload
                break
        if running_status_ref and running_status_payload:
            maybe_add_observation(
                observations,
                observation_type="heartbeat",
                status="running",
                source_ref=running_status_ref,
                observed_at=optional_string(running_status_payload.get("heartbeat_at")) or session_updated_at,
                session_id=session_id,
                worker_id=optional_string(running_status_payload.get("worker_id")) or worker_id,
                assignment_id=optional_string(running_status_payload.get("assignment_id")) or assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=optional_string(running_status_payload.get("tool_id")) or tool_id,
                extension_id=optional_string(running_status_payload.get("extension_id")) or extension_id,
                registry_digest=optional_string(running_status_payload.get("registry_digest")) or registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, assignment_ref, running_status_ref),
            )

        request_payload = load_source_payload(root, request_ref)
        if request_ref and request_payload:
            maybe_add_observation(
                observations,
                observation_type="execution_requested",
                status="requested",
                source_ref=request_ref,
                observed_at=optional_string(request_payload.get("requested_at")) or session_updated_at,
                session_id=session_id,
                worker_id=optional_string(request_payload.get("worker_id")) or worker_id,
                assignment_id=optional_string(request_payload.get("assignment_id")) or assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=optional_string(request_payload.get("tool_id")) or tool_id,
                extension_id=optional_string(request_payload.get("extension_id")) or extension_id,
                registry_digest=optional_string(request_payload.get("registry_digest")) or registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, request_ref, request_payload.get("source_refs")),
            )

        approval_payload = load_source_payload(root, approval_ref)
        if approval_ref and approval_payload:
            approval_status = optional_string(approval_payload.get("approval_status")) or "unknown"
            approval_type = "execution_expired" if approval_has_expired(approval_payload) else (
                "execution_rejected" if approval_status == "rejected" else "execution_approved"
            )
            maybe_add_observation(
                observations,
                observation_type=approval_type,
                status="expired" if approval_type == "execution_expired" else approval_status,
                source_ref=approval_ref,
                observed_at=optional_string(approval_payload.get("issued_at")) or session_updated_at,
                session_id=session_id,
                worker_id=optional_string(approval_payload.get("worker_id")) or worker_id,
                assignment_id=optional_string(approval_payload.get("assignment_id")) or assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=optional_string(approval_payload.get("tool_id")) or tool_id,
                extension_id=optional_string(approval_payload.get("extension_id")) or extension_id,
                registry_digest=optional_string(approval_payload.get("registry_digest")) or registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, request_ref, approval_ref),
                extras={"approval_receipt_id": approval_payload.get("approval_receipt_id")},
            )

        receipt_ref = execution_receipt_ref or (close_receipt_refs[0] if close_receipt_refs else None)
        receipt_payload = load_source_payload(root, receipt_ref)
        if receipt_ref and receipt_payload:
            maybe_add_observation(
                observations,
                observation_type="execution_completed",
                status=optional_string(receipt_payload.get("result")) or "unknown",
                source_ref=receipt_ref,
                observed_at=optional_string(receipt_payload.get("executed_at")) or session_updated_at,
                session_id=session_id,
                worker_id=optional_string(receipt_payload.get("worker_id")) or worker_id,
                assignment_id=optional_string(receipt_payload.get("assignment_id")) or assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=optional_string(receipt_payload.get("tool_id")) or tool_id,
                extension_id=optional_string(receipt_payload.get("extension_id")) or extension_id,
                registry_digest=optional_string(receipt_payload.get("registry_digest")) or registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, request_ref, approval_ref, receipt_ref, receipt_payload.get("source_refs")),
                extras={
                    "approval_status": receipt_payload.get("approval_status"),
                    "execution_mode": receipt_payload.get("execution_mode"),
                },
            )

        if final_status in {"completed", "failed"} and final_status_ref:
            final_status_payload = load_source_payload(root, final_status_ref)
            maybe_add_observation(
                observations,
                observation_type="completed",
                status=final_status,
                source_ref=final_status_ref,
                observed_at=(
                    optional_string(final_status_payload.get("heartbeat_at")) if final_status_payload else None
                ) or (
                    optional_string(final_status_payload.get("executed_at")) if final_status_payload else None
                ) or session_closed_at or session_updated_at,
                session_id=session_id,
                worker_id=worker_id,
                assignment_id=assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=tool_id,
                extension_id=extension_id,
                registry_digest=registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, final_status_ref, close_receipt_refs),
                extras={"final_status": final_status},
            )

        for merge_request_ref in merge_request_refs:
            maybe_add_observation(
                observations,
                observation_type="merge_requested",
                status="open",
                source_ref=merge_request_ref,
                observed_at=session_updated_at,
                session_id=session_id,
                worker_id=worker_id,
                assignment_id=assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=tool_id,
                extension_id=extension_id,
                registry_digest=registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, merge_request_ref, pause_status_refs),
            )

        for pause_status_ref in pause_status_refs:
            pause_payload = load_source_payload(root, pause_status_ref)
            maybe_add_observation(
                observations,
                observation_type="paused",
                status="paused",
                source_ref=pause_status_ref,
                observed_at=(optional_string(pause_payload.get("heartbeat_at")) if pause_payload else None) or session_updated_at,
                session_id=session_id,
                worker_id=optional_string(pause_payload.get("worker_id")) if pause_payload else worker_id,
                assignment_id=optional_string(pause_payload.get("assignment_id")) if pause_payload else assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=(optional_string(pause_payload.get("tool_id")) if pause_payload else None) or tool_id,
                extension_id=(optional_string(pause_payload.get("extension_id")) if pause_payload else None) or extension_id,
                registry_digest=(optional_string(pause_payload.get("registry_digest")) if pause_payload else None) or registry_digest,
                source_artifact_refs=unique_source_refs(source_ref, merge_request_refs, pause_status_ref),
            )

        merge_assignment_payload = load_source_payload(root, merge_assignment_ref)
        if merge_assignment_ref and merge_assignment_payload:
            maybe_add_observation(
                observations,
                observation_type="merger_assigned",
                status="assigned",
                source_ref=merge_assignment_ref,
                observed_at=session_updated_at,
                session_id=session_id,
                worker_id=optional_string(merge_assignment_payload.get("worker_id")),
                assignment_id=optional_string(merge_assignment_payload.get("assignment_id")),
                stack_lock_digest=stack_lock_digest,
                tool_id=optional_string(merge_assignment_payload.get("tool_id")) or tool_id,
                extension_id=optional_string(merge_assignment_payload.get("extension_id")) or extension_id,
                registry_digest=optional_string(merge_assignment_payload.get("registry_digest")) or registry_digest,
                source_artifact_refs=unique_source_refs(
                    source_ref,
                    merge_request_refs,
                    merge_assignment_ref,
                    merge_context_ref,
                    merge_prompt_ref,
                ),
            )

        if resume_context_refs:
            for resume_context_ref in resume_context_refs:
                resume_payload = load_source_payload(root, resume_context_ref)
                maybe_add_observation(
                    observations,
                    observation_type="resume_ready",
                    status="ready",
                    source_ref=resume_context_ref,
                    observed_at=session_closed_at or session_updated_at,
                    session_id=session_id,
                    worker_id=optional_string(resume_payload.get("worker_id")) if resume_payload else worker_id,
                    assignment_id=optional_string(resume_payload.get("assignment_id")) if resume_payload else assignment_id,
                    stack_lock_digest=stack_lock_digest,
                    tool_id=tool_id,
                    extension_id=extension_id,
                    registry_digest=registry_digest,
                    source_artifact_refs=unique_source_refs(
                        source_ref,
                        merge_request_refs,
                        merge_assignment_ref,
                        merge_completion_ref,
                        resume_context_ref,
                    ),
                    extras={"merge_completion_ref": merge_completion_ref},
                )
        elif merge_completion_ref:
            maybe_add_observation(
                observations,
                observation_type="resume_ready",
                status="ready",
                source_ref=merge_completion_ref,
                observed_at=session_closed_at or session_updated_at,
                session_id=session_id,
                worker_id=worker_id,
                assignment_id=assignment_id,
                stack_lock_digest=stack_lock_digest,
                tool_id=tool_id,
                extension_id=extension_id,
                registry_digest=registry_digest,
                source_artifact_refs=unique_source_refs(
                    source_ref,
                    merge_request_refs,
                    merge_assignment_ref,
                    merge_completion_ref,
                ),
            )

    return observations


def sync_world_model_observations(
    *,
    root: Path,
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    emitted = load_observations(root)
    emitted_ids = {
        str(item.get("observation_id"))
        for item in emitted
        if isinstance(item.get("observation_id"), str)
    }
    emitted_keys = {
        (
            canonical_observation_type(
                str(item.get("observation_type", "")),
                status=str(item.get("status", "")),
            ),
            str(item.get("source_ref", "")),
        )
        for item in emitted
        if isinstance(item, dict)
    }
    for observation in observations:
        observation_id = str(observation.get("observation_id", "")).strip()
        observation_key = (
            canonical_observation_type(
                str(observation.get("observation_type", "")),
                status=str(observation.get("status", "")),
            ),
            str(observation.get("source_ref", "")),
        )
        if (
            not observation_id
            or observation_id in emitted_ids
            or observation_key in emitted_keys
        ):
            continue
        emit_observation(
            observation,
            owner="cortex-world-model-sync",
            root=root,
        )
        emitted_ids.add(observation_id)
        emitted_keys.add(observation_key)
    return load_observations(root)


def build_attention_items(
    *,
    status_payload: dict[str, Any],
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    observation_ids_by_source: dict[str, list[str]] = {}
    for observation in observations:
        source_ref = str(observation.get("source_ref", "")).strip()
        if not source_ref:
            continue
        observation_ids_by_source.setdefault(source_ref, []).append(str(observation.get("observation_id")))

    items: list[dict[str, Any]] = []
    for item in status_payload.get("attention_queue", {}).get("items", []):
        if not isinstance(item, dict):
            continue
        source_ref = item.get("source_ref")
        observation_ids = observation_ids_by_source.get(str(source_ref), []) if isinstance(source_ref, str) else []
        items.append(
            build_attention_item(
                kind=str(item.get("kind", "attention")),
                severity=str(item.get("severity", "medium")),
                summary=str(item.get("summary", "Attention item")),
                source_ref=str(source_ref) if isinstance(source_ref, str) else None,
                observation_ids=observation_ids,
                details=item.get("details") if isinstance(item.get("details"), dict) else {},
            )
        )
    items.sort(key=lambda item: (item["severity"], item["kind"], item["summary"]))
    return items


def build_snapshot_payload(
    *,
    root: Path,
    descriptor_root: Path,
    inventory_entries: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    attention_items: list[dict[str, Any]],
    status_payload: dict[str, Any],
    registry_bundle: dict[str, Any],
    event_latest: list[Path],
    knowledge_latest: list[Path],
    validation_latest: list[Path],
) -> dict[str, Any]:
    payload = {
        "contract_version": SNAPSHOT_CONTRACT_VERSION,
        "snapshot_kind": "state",
        "source_refs": {
            "descriptor_root": atlas_relative(descriptor_root, root=root),
            "registry_refs": [
                "docs/registry/ATLAS-TOOL-REGISTRY.json",
                "docs/registry/ATLAS-EXTENSION-REGISTRY.json",
            ],
            "working_memory_refs": [working_memory_catalog_ref(root)],
            "event_latest_refs": relative_paths(event_latest, root=root),
            "knowledge_latest_refs": relative_paths(knowledge_latest, root=root),
            "validation_refs": relative_paths(validation_latest, root=root),
        },
        "registry": status_payload.get("registry", {}),
        "active_session": status_payload.get("active_session"),
        "summary": {
            "inventory_entry_count": len(inventory_entries),
            "observation_count": len(observations),
            "attention_item_count": len(attention_items),
            "descriptor_count": status_payload.get("artifact_inventory", {}).get("descriptor_count", 0),
            "registry_digest": registry_bundle.get("registry_digest"),
            "attention_status": status_payload.get("attention_queue", {}).get("status"),
            "attention_highest_severity": status_payload.get("attention_queue", {}).get("highest_severity"),
            "working_memory_item_count": status_payload.get("working_memory", {}).get("item_count", 0),
        },
        "inventory_entries": inventory_entries,
        "observations": observations,
        "attention_items": attention_items,
    }
    payload["content_digest"] = stable_json_digest(payload)
    return payload


def build_attention_payload(
    *,
    root: Path,
    descriptor_root: Path,
    status_payload: dict[str, Any],
    attention_items: list[dict[str, Any]],
    registry_bundle: dict[str, Any],
    event_latest: list[Path],
    knowledge_latest: list[Path],
    validation_latest: list[Path],
) -> dict[str, Any]:
    payload = {
        "contract_version": SNAPSHOT_CONTRACT_VERSION,
        "snapshot_kind": "attention",
        "source_refs": {
            "descriptor_root": atlas_relative(descriptor_root, root=root),
            "registry_refs": [
                "docs/registry/ATLAS-TOOL-REGISTRY.json",
                "docs/registry/ATLAS-EXTENSION-REGISTRY.json",
            ],
            "working_memory_refs": [working_memory_catalog_ref(root)],
            "event_latest_refs": relative_paths(event_latest, root=root),
            "knowledge_latest_refs": relative_paths(knowledge_latest, root=root),
            "validation_refs": relative_paths(validation_latest, root=root),
        },
        "registry": status_payload.get("registry", {}),
        "active_session": status_payload.get("active_session"),
        "summary": {
            "attention_item_count": len(attention_items),
            "attention_status": status_payload.get("attention_queue", {}).get("status"),
            "highest_severity": status_payload.get("attention_queue", {}).get("highest_severity"),
            "registry_digest": registry_bundle.get("registry_digest"),
        },
        "inventory_entries": [],
        "observations": [],
        "attention_items": attention_items,
    }
    payload["content_digest"] = stable_json_digest(payload)
    return payload


def build_world_model_payloads(
    *,
    descriptor_root: Path | None = None,
    root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    resolved_descriptor_root = (descriptor_root or (base_root / "runtime" / "cortex" / "artifacts")).resolve()
    descriptors = load_descriptors(resolved_descriptor_root)
    registry_bundle = load_tool_registry_bundle(root=base_root)
    status_payload = render_status_payload(resolved_descriptor_root)
    event_latest = latest_receipt_paths(base_root, "runtime/receipts/events")
    knowledge_latest = latest_receipt_paths(base_root, "runtime/receipts/knowledge")
    validation_latest = validation_receipt_paths(base_root)
    inventory_entries = build_inventory_entries(
        root=base_root,
        descriptors=descriptors,
        registry_bundle=registry_bundle,
    )
    observations = build_observations(
        root=base_root,
        descriptors=descriptors,
        registry_bundle=registry_bundle,
        event_latest=event_latest,
        knowledge_latest=knowledge_latest,
        validation_latest=validation_latest,
    )
    observations = sync_world_model_observations(
        root=base_root,
        observations=observations,
    )
    attention_items = build_attention_items(
        status_payload=status_payload,
        observations=observations,
    )
    return {
        "snapshot": build_snapshot_payload(
            root=base_root,
            descriptor_root=resolved_descriptor_root,
            inventory_entries=inventory_entries,
            observations=observations,
            attention_items=attention_items,
            status_payload=status_payload,
            registry_bundle=registry_bundle,
            event_latest=event_latest,
            knowledge_latest=knowledge_latest,
            validation_latest=validation_latest,
        ),
        "attention": build_attention_payload(
            root=base_root,
            descriptor_root=resolved_descriptor_root,
            status_payload=status_payload,
            attention_items=attention_items,
            registry_bundle=registry_bundle,
            event_latest=event_latest,
            knowledge_latest=knowledge_latest,
            validation_latest=validation_latest,
        ),
    }


def write_world_model_state(
    *,
    descriptor_root: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    try:
        write_working_memory_catalog(base_root)
    except ValueError:
        # Validation reports malformed working-memory artifacts separately.
        pass
    payloads = build_world_model_payloads(descriptor_root=descriptor_root, root=base_root)
    state_root = world_model_state_root(base_root)
    snapshot_path = snapshot_output_path(base_root)
    attention_path = attention_output_path(base_root)
    state_root.mkdir(parents=True, exist_ok=True)
    write_json(snapshot_path, payloads["snapshot"])
    write_json(attention_path, payloads["attention"])
    return {
        "snapshot_ref": atlas_relative(snapshot_path, root=base_root),
        "attention_ref": atlas_relative(attention_path, root=base_root),
        "snapshot_content_digest": payloads["snapshot"]["content_digest"],
        "attention_content_digest": payloads["attention"]["content_digest"],
        "inventory_entry_count": len(payloads["snapshot"]["inventory_entries"]),
        "observation_count": len(payloads["snapshot"]["observations"]),
        "attention_item_count": len(payloads["snapshot"]["attention_items"]),
    }


def world_model_refs(root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot_path = snapshot_output_path(base_root)
    attention_path = attention_output_path(base_root)
    result: dict[str, Any] = {
        "snapshot_ref": atlas_relative(snapshot_path, root=base_root),
        "attention_ref": atlas_relative(attention_path, root=base_root),
        "snapshot_present": snapshot_path.exists(),
        "attention_present": attention_path.exists(),
    }
    if snapshot_path.exists():
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            result["snapshot_content_digest"] = payload.get("content_digest")
            result["inventory_entry_count"] = len(payload.get("inventory_entries", [])) if isinstance(payload.get("inventory_entries"), list) else 0
            result["observation_count"] = len(payload.get("observations", [])) if isinstance(payload.get("observations"), list) else 0
    if attention_path.exists():
        payload = json.loads(attention_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            result["attention_content_digest"] = payload.get("content_digest")
            result["attention_item_count"] = len(payload.get("attention_items", [])) if isinstance(payload.get("attention_items"), list) else 0
    return result
