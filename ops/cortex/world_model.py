from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, load_repo_registry
from ops.atlas.observations import emit_observation, load_observations
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import load_descriptors, read_json, stable_json_digest, write_json
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

    observations.sort(key=lambda item: (item["observation_type"], item["source_ref"], item["status"]))
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
    for observation in observations:
        observation_id = str(observation.get("observation_id", "")).strip()
        if not observation_id or observation_id in emitted_ids:
            continue
        emit_observation(
            observation,
            owner="cortex-world-model-sync",
            root=root,
        )
        emitted_ids.add(observation_id)
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
