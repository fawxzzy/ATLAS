from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, resolve_atlas_path
from ops.atlas.backfill_legacy_runtime_artifacts import backfill_legacy_runtime_artifacts
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import (
    default_artifact_source_paths,
    load_descriptors,
    read_json,
    register_artifact_descriptors,
    write_json,
)
from ops.cortex.index_working_memory import WORKING_MEMORY_OUTPUT, load_working_memory_catalog
from ops.cortex.render_status import initiative_view, render_status_payload
from ops.cortex.world_model import (
    attention_output_path,
    snapshot_output_path,
    world_model_state_root,
    write_world_model_state,
)
from ops.knowledge._pipeline import build_query_bundle, knowledge_query_bundle_path
from ops.stack.export_repo_inventory import (
    build_repo_inventory,
    find_excluded_surface,
    find_repo_inventory_entry,
)

STATUS_CONTRACT_VERSION = "atlas.awareness.status.v1"
SEARCH_CONTRACT_VERSION = "atlas.awareness.search.v1"
FETCH_CONTRACT_VERSION = "atlas.awareness.fetch.v1"
SESSION_CONTRACT_VERSION = "atlas.awareness.session.v1"
ARTIFACT_CONTRACT_VERSION = "atlas.awareness.artifact.v1"
VOICE_CONTRACT_VERSION = "atlas.awareness.voice.v1"
OBSERVE_AUTOMATION_LEVEL = "observe"
CONTEXT_AUTOMATION_LEVEL = "context"

ALLOWED_FETCH_PREFIXES = [
    "docs/",
    "ops/",
    "runtime/atlas/conversations/",
    "runtime/atlas/sessions/",
    "runtime/atlas/proposed-sessions/",
    "runtime/atlas/session-workspaces/",
    "runtime/atlas/voice/",
    "runtime/cortex/catalog/knowledge/",
    "runtime/cortex/context/",
    "runtime/cortex/query/knowledge/",
    "runtime/cortex/supervisor/",
    "runtime/lifeline/worker-execution/",
    "runtime/receipts/",
    "runtime/state/atlas/",
    "stack.yaml",
    "stack.lock.yaml",
    "README-STACK.md",
]


def _bundle_path(root: Path) -> Path:
    return (root / "runtime" / "cortex" / "query" / "knowledge" / "bundle.json").resolve()


def ensure_world_model(*, root: Path | None = None, refresh: bool = False) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot_path = snapshot_output_path(base_root)
    attention_path = attention_output_path(base_root)
    if refresh or not snapshot_path.exists() or not attention_path.exists():
        backfill_legacy_runtime_artifacts(root=base_root)
        register_artifact_descriptors(
            default_artifact_source_paths(base_root),
            output_dir=base_root / "runtime" / "cortex" / "artifacts",
            root=base_root,
        )
        summary = write_world_model_state(
            descriptor_root=base_root / "runtime" / "cortex" / "artifacts",
            root=base_root,
        )
        register_artifact_descriptors(
            [world_model_state_root(base_root)],
            output_dir=base_root / "runtime" / "cortex" / "artifacts",
            root=base_root,
        )
        write_json(base_root / "runtime" / "state" / "atlas" / "world-model.last-build.json", summary)
    return {
        "snapshot_path": snapshot_path,
        "attention_path": attention_path,
        "descriptor_root": base_root / "runtime" / "cortex" / "artifacts",
    }


def ensure_query_bundle(*, root: Path | None = None, refresh: bool = False) -> Path:
    base_root = (root or atlas_root()).resolve()
    bundle_path = _bundle_path(base_root)
    if refresh or not bundle_path.exists():
        build_query_bundle(dry_run=False)
    return bundle_path


def _load_snapshot(*, root: Path | None = None, refresh: bool = False) -> dict[str, Any]:
    paths = ensure_world_model(root=root, refresh=refresh)
    return read_json(paths["snapshot_path"])


def _load_attention(*, root: Path | None = None, refresh: bool = False) -> dict[str, Any]:
    paths = ensure_world_model(root=root, refresh=refresh)
    return read_json(paths["attention_path"])


def _load_query_bundle(*, root: Path | None = None, refresh: bool = False) -> dict[str, Any]:
    bundle_path = ensure_query_bundle(root=root, refresh=refresh)
    return read_json(bundle_path)


def _resolve_allowed_fetch_ref(ref: str, *, root: Path) -> Path:
    normalized = ref.strip().replace("\\", "/")
    if not normalized:
        raise ValueError("Artifact ref must be non-empty.")
    if not any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix)
        for prefix in ALLOWED_FETCH_PREFIXES
    ):
        raise ValueError(f"Artifact ref is outside the awareness fetch allowlist: {normalized}")
    resolved = resolve_atlas_path(normalized, root=root)
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"Artifact ref does not resolve to a readable file: {normalized}")
    return resolved


def _artifact_url(kind: str, identifier: str) -> str:
    return f"atlas://{kind}/{identifier}"


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True)


def _trimmed_text(value: str, limit: int = 320) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def _inventory_text(entry: dict[str, Any]) -> str:
    details = entry.get("details") if isinstance(entry.get("details"), dict) else {}
    parts = [
        str(entry.get("entry_type", "")),
        str(entry.get("key", "")),
        str(entry.get("label", "")),
        str(entry.get("status", "")),
        str(entry.get("trust_class", "")),
        str(entry.get("source_ref", "")),
        _json_text(details),
    ]
    return " ".join(parts)


def _score_text(query: str, *haystacks: str) -> int:
    normalized_query = " ".join(query.lower().split())
    if not normalized_query:
        return 0
    tokens = [token for token in normalized_query.split(" ") if token]
    score = 0
    for haystack in haystacks:
        text = haystack.lower()
        if normalized_query in text:
            score += 20
        for token in tokens:
            if token in text:
                score += 5
    return score


def _knowledge_search_haystacks(record: dict[str, Any]) -> tuple[str, str, str]:
    query_policy = record.get("query_policy") if isinstance(record.get("query_policy"), dict) else {}
    search_terms = record.get("search_terms") if isinstance(record.get("search_terms"), dict) else {}
    metadata_terms = " ".join(str(item) for item in search_terms.get("metadata", []))
    derived_terms = (
        " ".join(str(item) for item in search_terms.get("derived", []))
        if query_policy.get("derived_searchable")
        else ""
    )
    evidence_terms = (
        " ".join(str(item) for item in search_terms.get("evidence", []))
        if query_policy.get("derived_searchable")
        else ""
    )
    return metadata_terms, derived_terms, evidence_terms


def _knowledge_search(query: str, *, limit: int, root: Path, refresh: bool) -> list[dict[str, Any]]:
    bundle = _load_query_bundle(root=root, refresh=refresh)
    results: list[dict[str, Any]] = []
    for record in bundle.get("records", []):
        if not isinstance(record, dict):
            continue
        metadata_terms, derived_terms, evidence_terms = _knowledge_search_haystacks(record)
        score = _score_text(
            query,
            str(record.get("archive_id", "")),
            str(record.get("source_name", "")),
            metadata_terms,
            derived_terms,
            evidence_terms,
        )
        if score <= 0:
            continue
        title = str(record.get("archive_id") or record.get("source_name") or "knowledge")
        query_policy = record.get("query_policy") if isinstance(record.get("query_policy"), dict) else {}
        snippet = (
            str(record.get("derived_summary_text"))
            if query_policy.get("derived_searchable") and record.get("derived_summary_text")
            else metadata_terms or title
        )
        results.append(
            {
                "id": f"knowledge:{record.get('archive_id')}",
                "title": title,
                "url": _artifact_url("knowledge", str(record.get("archive_id"))),
                "text": _trimmed_text(snippet),
                "metadata": {
                    "source_kind": "knowledge",
                    "archive_id": record.get("archive_id"),
                    "promotion_status": record.get("promotion_status"),
                    "indexing_profile": record.get("indexing_profile"),
                    "query_policy": record.get("query_policy"),
                },
                "_score": score,
            }
        )
    results.sort(key=lambda item: (-int(item["_score"]), str(item["title"])))
    return results[:limit]


def _load_working_memory(*, root: Path, refresh: bool) -> dict[str, Any]:
    catalog_path = (root / WORKING_MEMORY_OUTPUT).resolve()
    if refresh or not catalog_path.exists():
        ensure_world_model(root=root, refresh=refresh)
    return load_working_memory_catalog(root)


def _load_repo_inventory(*, root: Path, refresh: bool) -> dict[str, Any]:
    _ = refresh
    return build_repo_inventory(root=root)


def _memory_source_kind(item: dict[str, Any]) -> str:
    memory_kind = str(item.get("memory_kind", "")).strip()
    return memory_kind if memory_kind == "initiative" else "memory"


def _memory_identifier(item: dict[str, Any]) -> str:
    memory_id = str(item.get("id", "")).strip()
    source_kind = _memory_source_kind(item)
    return f"{source_kind}:{memory_id}"


def _memory_metadata(item: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "source_kind": _memory_source_kind(item),
        "memory_kind": item.get("memory_kind"),
        "status": item.get("status"),
        "owner": item.get("owner"),
        "path": item.get("path"),
        "document_metadata": item.get("metadata", {}),
    }
    for field in (
        "related_plan_refs",
        "related_decision_refs",
        "related_hypothesis_refs",
        "related_session_refs",
        "related_attention_refs",
        "related_artifact_refs",
        "evidence_refs",
        "proposed_next_session_refs",
        "supersedes",
        "superseded_by",
    ):
        if field in item:
            metadata[field] = item.get(field, [])
    return metadata


def _working_memory_search_haystacks(item: dict[str, Any]) -> list[str]:
    haystacks = [
        str(item.get("id", "")),
        str(item.get("title", "")),
        str(item.get("summary", "")),
        str(item.get("status", "")),
        str(item.get("owner", "")),
        str(item.get("memory_kind", "")),
        str(item.get("path", "")),
        _json_text(item.get("metadata", {})),
    ]
    for key, value in item.items():
        if not isinstance(key, str) or not key.endswith("_refs"):
            continue
        if isinstance(value, list):
            haystacks.append(" ".join(str(entry) for entry in value))
    return haystacks


def _working_memory_search(query: str, *, limit: int, root: Path, refresh: bool) -> list[dict[str, Any]]:
    catalog = _load_working_memory(root=root, refresh=refresh)
    results: list[dict[str, Any]] = []
    for item in catalog.get("items", []):
        if not isinstance(item, dict):
            continue
        score = _score_text(query, *_working_memory_search_haystacks(item))
        if score <= 0:
            continue
        memory_id = str(item.get("id", "")).strip()
        if not memory_id:
            continue
        results.append(
            {
                "id": _memory_identifier(item),
                "title": str(item.get("title") or memory_id),
                "url": _artifact_url(_memory_source_kind(item), memory_id),
                "text": _trimmed_text(str(item.get("summary") or item.get("title") or memory_id)),
                "metadata": _memory_metadata(item),
                "_score": score,
            }
        )
    results.sort(key=lambda item: (-int(item["_score"]), str(item["title"]), str(item["id"])))
    return results[:limit]


def _repo_inventory_search(query: str, *, limit: int, root: Path, refresh: bool) -> list[dict[str, Any]]:
    inventory = _load_repo_inventory(root=root, refresh=refresh)
    results: list[dict[str, Any]] = []
    for item in inventory.get("repos", []):
        if not isinstance(item, dict):
            continue
        local_path = str(item.get("local_path") or "")
        related_initiatives = item.get("related_initiatives", []) if isinstance(item.get("related_initiatives"), list) else []
        score = _score_text(
            query,
            str(item.get("logical_id", "")),
            local_path,
            local_path.replace("/", "\\"),
            str(item.get("role", "")),
            str(item.get("status", "")),
            str(item.get("branch", "")),
            str(item.get("remote_url", "")),
            _json_text(related_initiatives),
        )
        if score <= 0:
            continue
        results.append(
            {
                "id": f"repo:{item.get('logical_id')}",
                "title": str(item.get("logical_id") or local_path or "repo"),
                "url": _artifact_url("repo", str(item.get("logical_id") or local_path)),
                "text": _trimmed_text(
                    f"{local_path} branch={item.get('branch')} dirty={item.get('dirty')} trust={item.get('trust_class')}"
                ),
                "metadata": {
                    "source_kind": "repo_inventory",
                    "logical_id": item.get("logical_id"),
                    "local_path": local_path,
                    "branch": item.get("branch"),
                    "dirty": item.get("dirty"),
                    "trust_class": item.get("trust_class"),
                    "release_eligible": item.get("release_eligible"),
                    "related_initiative_refs": item.get("related_initiative_refs", []),
                },
                "_score": score,
            }
        )
    for item in inventory.get("excluded_surfaces", []):
        if not isinstance(item, dict):
            continue
        local_path = str(item.get("local_path") or "")
        score = _score_text(
            query,
            str(item.get("surface_id", "")),
            local_path,
            local_path.replace("/", "\\"),
            str(item.get("reason", "")),
            str(item.get("trust_class", "")),
        )
        if score <= 0:
            continue
        results.append(
            {
                "id": f"excluded_surface:{item.get('surface_id')}",
                "title": str(item.get("surface_id") or local_path or "excluded_surface"),
                "url": _artifact_url("excluded_surface", str(item.get("surface_id") or local_path)),
                "text": _trimmed_text(
                    f"{local_path} trust={item.get('trust_class')} visibility={item.get('visibility_mode')}"
                ),
                "metadata": {
                    "source_kind": "excluded_surface",
                    "surface_id": item.get("surface_id"),
                    "local_path": local_path,
                    "trust_class": item.get("trust_class"),
                    "visibility_mode": item.get("visibility_mode"),
                },
                "_score": score,
            }
        )
    results.sort(key=lambda item: (-int(item["_score"]), str(item["title"]), str(item["id"])))
    return results[:limit]


def atlas_status(*, root: Path | None = None, refresh: bool = False) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot = _load_snapshot(root=base_root, refresh=refresh)
    attention = _load_attention(root=base_root, refresh=refresh)
    status = render_status_payload(base_root / "runtime" / "cortex" / "artifacts")
    return {
        "schema_version": STATUS_CONTRACT_VERSION,
        "registry": status.get("registry"),
        "active_session": status.get("active_session"),
        "artifact_inventory": status.get("artifact_inventory"),
        "snapshot": {
            "path": atlas_relative(snapshot_output_path(base_root), root=base_root),
            "content_digest": snapshot.get("content_digest"),
            "summary": snapshot.get("summary"),
        },
        "attention": {
            "path": atlas_relative(attention_output_path(base_root), root=base_root),
            "content_digest": attention.get("content_digest"),
            "summary": attention.get("summary"),
        },
        "trust_posture": status.get("trust_posture"),
        "repo_inventory": status.get("repo_inventory"),
        "working_memory": status.get("working_memory"),
        "initiatives": status.get("initiatives"),
        "slices": status.get("slices"),
        "conversations": status.get("conversations"),
        "governed_writes": status.get("governed_writes"),
        "digests": {
            "registry_digest": status.get("registry", {}).get("registry_digest")
            if isinstance(status.get("registry"), dict)
            else None,
            "world_model_digest": snapshot.get("content_digest"),
            "attention_digest": attention.get("content_digest"),
            "working_memory_digest": status.get("working_memory", {}).get("content_digest")
            if isinstance(status.get("working_memory"), dict)
            else None,
            "repo_inventory_digest": status.get("repo_inventory", {}).get("content_digest")
            if isinstance(status.get("repo_inventory"), dict)
            else None,
        },
        "automation_policy": {
            "surface": "awareness_api",
            "default_level": OBSERVE_AUTOMATION_LEVEL,
            "max_level": CONTEXT_AUTOMATION_LEVEL,
            "read_only": True,
        },
        "world_model": status.get("world_model"),
    }


def _slice_titles() -> dict[str, str]:
    return {
        "active_initiatives": "Active Initiatives",
        "waiting_on_review": "Waiting On Review",
        "pending_proposals": "Pending Proposals",
        "repo_linked_initiatives": "Repo-Linked Initiatives",
        "trust_posture": "Trust Posture",
        "repo_inventory": "Repo Inventory",
    }


def _status_slices(status: dict[str, Any]) -> dict[str, Any]:
    return status.get("slices", {}) if isinstance(status.get("slices"), dict) else {}


def _status_slice_payload(status: dict[str, Any], slice_name: str) -> dict[str, Any]:
    slices = _status_slices(status)
    titles = _slice_titles()
    if slice_name == "trust_posture":
        payload = slices.get(slice_name, status.get("trust_posture", {}))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "slice_name": slice_name,
            "title": titles.get(slice_name, slice_name),
            "item_count": int(payload.get("item_count", 0) or 0),
            "items": payload.get("items", []) if isinstance(payload.get("items"), list) else [],
            "payload": payload,
        }
    items = slices.get(slice_name, [])
    if not isinstance(items, list):
        items = []
    return {
        "slice_name": slice_name,
        "title": titles.get(slice_name, slice_name),
        "item_count": len(items),
        "items": items,
        "payload": {
            "slice_name": slice_name,
            "item_count": len(items),
            "items": items,
        },
    }


def _initiative_catalog_item(initiative_id: str, *, root: Path, refresh: bool) -> dict[str, Any] | None:
    catalog = _load_working_memory(root=root, refresh=refresh)
    for item in catalog.get("items", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("memory_kind", "")).strip() != "initiative":
            continue
        if str(item.get("id", "")).strip() != initiative_id:
            continue
        return item
    return None


def _initiative_status_view(initiative_id: str, *, root: Path, refresh: bool) -> dict[str, Any] | None:
    status = atlas_status(root=root, refresh=refresh)
    initiatives = status.get("initiatives", {}) if isinstance(status.get("initiatives"), dict) else {}
    for key in ("active_items", "pending_proposal_items", "waiting_on_review_items", "repo_linked_items"):
        items = initiatives.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and str(item.get("id", "")).strip() == initiative_id:
                return item
    catalog_item = _initiative_catalog_item(initiative_id, root=root, refresh=refresh)
    if catalog_item is None:
        return None
    return initiative_view(catalog_item)


def _proposal_payload_for_initiative(
    initiative_id: str,
    *,
    root: Path,
    refresh: bool,
) -> dict[str, Any]:
    initiative_payload = fetch_memory(initiative_id, root=root, refresh=refresh)
    initiative_metadata = initiative_payload.get("metadata", {}) if isinstance(initiative_payload.get("metadata"), dict) else {}
    status_view = _initiative_status_view(initiative_id, root=root, refresh=refresh) or {}
    proposal_ref = str(status_view.get("proposal_ref") or "").strip()
    if not proposal_ref:
        proposal_ref = str(initiative_metadata.get("document_metadata", {}).get("proposal_ref") or "").strip()
    proposed_refs = status_view.get("proposed_next_session_refs", []) if isinstance(status_view.get("proposed_next_session_refs"), list) else []
    if not proposal_ref and proposed_refs:
        proposal_ref = str(proposed_refs[0] or "").strip()
    if not proposal_ref:
        proposed_from_metadata = initiative_metadata.get("proposed_next_session_refs", [])
        if isinstance(proposed_from_metadata, list) and proposed_from_metadata:
            proposal_ref = str(proposed_from_metadata[0] or "").strip()
    if not proposal_ref:
        raise FileNotFoundError(f"No proposal is linked to initiative: {initiative_id}")
    proposal_artifact = fetch_artifact(proposal_ref, root=root)
    proposal_json = proposal_artifact.get("json") if isinstance(proposal_artifact.get("json"), dict) else {}
    return {
        "schema_version": FETCH_CONTRACT_VERSION,
        "id": f"proposal:{initiative_id}",
        "title": str(proposal_json.get("title") or f"Pending proposal for {initiative_id}"),
        "url": _artifact_url("proposal", initiative_id),
        "text": _json_text(
            {
                "initiative_id": initiative_id,
                "initiative_title": status_view.get("title") or initiative_payload.get("title"),
                "proposal_ref": proposal_ref,
                "proposal_session": proposal_json,
            }
        ),
        "metadata": {
            "source_kind": "proposal",
            "initiative_id": initiative_id,
            "proposal_ref": proposal_ref,
            "session_id": proposal_json.get("session_id"),
            "initiative_ref": initiative_metadata.get("path"),
        },
    }


def fetch_status_slice(
    slice_name: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    if slice_name not in _slice_titles():
        raise FileNotFoundError(f"Unknown awareness status slice: {slice_name}")
    status = atlas_status(root=base_root, refresh=refresh)
    payload = _status_slice_payload(status, slice_name)
    return {
        "schema_version": FETCH_CONTRACT_VERSION,
        "id": f"slice:{slice_name}",
        "title": payload["title"],
        "url": _artifact_url("slice", slice_name),
        "text": _json_text(payload["payload"]),
        "metadata": {
            "source_kind": "status_slice",
            "slice_name": slice_name,
            "item_count": payload["item_count"],
        },
    }


def list_inventory(
    *,
    root: Path | None = None,
    refresh: bool = False,
    entry_type: str | None = None,
    status: str | None = None,
    trust_class: str | None = None,
    query: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    snapshot = _load_snapshot(root=root, refresh=refresh)
    entries = snapshot.get("inventory_entries", [])
    if not isinstance(entries, list):
        entries = []
    filtered: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        if entry_type and str(item.get("entry_type")) != entry_type:
            continue
        if status and str(item.get("status")) != status:
            continue
        if trust_class and str(item.get("trust_class")) != trust_class:
            continue
        if query and _score_text(query, _inventory_text(item)) <= 0:
            continue
        filtered.append(item)
    filtered.sort(key=lambda item: (str(item.get("entry_type", "")), str(item.get("key", ""))))
    if limit is not None:
        filtered = filtered[: max(limit, 0)]
    return {
        "schema_version": "atlas.awareness.inventory.v1",
        "snapshot_content_digest": snapshot.get("content_digest"),
        "entry_count": len(filtered),
        "entries": filtered,
    }


def list_attention(
    *,
    root: Path | None = None,
    refresh: bool = False,
    severity: str | None = None,
    query: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    attention = _load_attention(root=root, refresh=refresh)
    items = attention.get("attention_items", [])
    if not isinstance(items, list):
        items = []
    filtered: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if severity and str(item.get("severity")) != severity:
            continue
        if query and _score_text(query, str(item.get("summary", "")), _json_text(item.get("details", {}))) <= 0:
            continue
        filtered.append(item)
    if limit is not None:
        filtered = filtered[: max(limit, 0)]
    return {
        "schema_version": "atlas.awareness.attention.v1",
        "attention_content_digest": attention.get("content_digest"),
        "item_count": len(filtered),
        "items": filtered,
    }


def fetch_artifact(
    ref: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    resolved = _resolve_allowed_fetch_ref(ref, root=base_root)
    relative_ref = atlas_relative(resolved, root=base_root)
    if resolved.suffix.lower() == ".json":
        payload = read_json(resolved)
        text = _json_text(payload)
        media_type = "application/json"
    else:
        text = resolved.read_text(encoding="utf-8", errors="replace")
        payload = None
        media_type = "text/plain"
    return {
        "schema_version": ARTIFACT_CONTRACT_VERSION,
        "ref": relative_ref,
        "title": resolved.name,
        "url": _artifact_url("artifact", relative_ref),
        "media_type": media_type,
        "text": text,
        "json": payload,
    }


def fetch_session(
    session_id: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot = _load_snapshot(root=base_root, refresh=refresh)
    descriptors = load_descriptors(base_root / "runtime" / "cortex" / "artifacts")
    session_descriptor = next(
        (
            descriptor
            for descriptor in descriptors
            if descriptor.get("artifact_type") == "session_manifest"
            and descriptor.get("identity", {}).get("session_id") == session_id
        ),
        None,
    )
    if session_descriptor is None:
        raise FileNotFoundError(f"Unknown session_id: {session_id}")
    source_ref = str(session_descriptor.get("source_ref", ""))
    manifest = fetch_artifact(source_ref, root=base_root)
    observations = [
        item
        for item in snapshot.get("observations", [])
        if isinstance(item, dict)
        and (
            item.get("source_ref") == source_ref
            or item.get("scope_ref") == session_id
        )
    ]
    related_inventory = [
        item
        for item in snapshot.get("inventory_entries", [])
        if isinstance(item, dict)
        and (
            item.get("source_ref") == source_ref
            or item.get("key") == session_id
        )
    ]
    session_root = resolve_atlas_path(source_ref, root=base_root).parent
    status_snapshot_path = session_root / "status.snapshot.json"
    status_snapshot = read_json(status_snapshot_path) if status_snapshot_path.exists() else None
    return {
        "schema_version": SESSION_CONTRACT_VERSION,
        "session_id": session_id,
        "manifest_ref": source_ref,
        "automation_level": manifest.get("json", {}).get("automation_level") if isinstance(manifest.get("json"), dict) else None,
        "max_automation_level": manifest.get("json", {}).get("max_automation_level") if isinstance(manifest.get("json"), dict) else None,
        "manifest": manifest.get("json"),
        "descriptor": session_descriptor,
        "status_snapshot_ref": atlas_relative(status_snapshot_path, root=base_root) if status_snapshot_path.exists() else None,
        "status_snapshot": status_snapshot,
        "observations": observations,
        "inventory_entries": related_inventory,
    }


def fetch_conversation(
    conversation_id: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot = _load_snapshot(root=base_root, refresh=refresh)
    descriptors = load_descriptors(base_root / "runtime" / "cortex" / "artifacts")
    conversation_descriptor = next(
        (
            descriptor
            for descriptor in descriptors
            if descriptor.get("artifact_type") == "conversation_manifest"
            and descriptor.get("identity", {}).get("conversation_id") == conversation_id
        ),
        None,
    )
    if conversation_descriptor is None:
        raise FileNotFoundError(f"Unknown conversation_id: {conversation_id}")
    source_ref = str(conversation_descriptor.get("source_ref", ""))
    manifest = fetch_artifact(source_ref, root=base_root)
    related_inventory = [
        item
        for item in snapshot.get("inventory_entries", [])
        if isinstance(item, dict)
        and (
            item.get("source_ref") == source_ref
            or item.get("key") == conversation_id
            or item.get("details", {}).get("conversation_id") == conversation_id
        )
    ]
    turn_refs = (
        conversation_descriptor.get("links", {}).get("recent_turn_refs", [])
        if isinstance(conversation_descriptor.get("links"), dict)
        else []
    )
    turns = [
        fetch_artifact(str(ref), root=base_root).get("json")
        for ref in turn_refs
        if isinstance(ref, str) and ref.strip()
    ]
    return {
        "schema_version": "atlas.awareness.conversation.v1",
        "conversation_id": conversation_id,
        "manifest_ref": source_ref,
        "manifest": manifest.get("json"),
        "descriptor": conversation_descriptor,
        "turns": [turn for turn in turns if isinstance(turn, dict)],
        "inventory_entries": related_inventory,
    }


def fetch_conversation_turn(
    turn_id: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot = _load_snapshot(root=base_root, refresh=refresh)
    descriptors = load_descriptors(base_root / "runtime" / "cortex" / "artifacts")
    turn_descriptors = [
        descriptor
        for descriptor in descriptors
        if descriptor.get("artifact_type") == "conversation_turn"
        and descriptor.get("identity", {}).get("turn_id") == turn_id
    ]
    if not turn_descriptors:
        raise FileNotFoundError(f"Unknown turn_id: {turn_id}")
    if len(turn_descriptors) > 1:
        refs = ", ".join(sorted(str(descriptor.get("source_ref", "")) for descriptor in turn_descriptors))
        raise ValueError(f"Ambiguous turn_id '{turn_id}' matches multiple turn artifacts: {refs}")
    turn_descriptor = turn_descriptors[0]
    source_ref = str(turn_descriptor.get("source_ref", ""))
    artifact = fetch_artifact(source_ref, root=base_root)
    conversation_id = str(turn_descriptor.get("identity", {}).get("conversation_id") or "").strip()
    conversation_ref = None
    if conversation_id:
        conversation_descriptor = next(
            (
                descriptor
                for descriptor in descriptors
                if descriptor.get("artifact_type") == "conversation_manifest"
                and descriptor.get("identity", {}).get("conversation_id") == conversation_id
            ),
            None,
        )
        if conversation_descriptor is not None:
            conversation_ref = conversation_descriptor.get("source_ref")
    observations = [
        item
        for item in snapshot.get("observations", [])
        if isinstance(item, dict)
        and (
            item.get("source_ref") == source_ref
            or item.get("scope_ref") == conversation_id
            or item.get("details", {}).get("turn_id") == turn_id
        )
    ]
    related_inventory = [
        item
        for item in snapshot.get("inventory_entries", [])
        if isinstance(item, dict)
        and (
            item.get("source_ref") == source_ref
            or item.get("key") == turn_id
            or item.get("details", {}).get("turn_id") == turn_id
        )
    ]
    return {
        "schema_version": "atlas.awareness.conversation-turn.v1",
        "conversation_id": conversation_id or None,
        "conversation_ref": conversation_ref,
        "turn_id": turn_id,
        "turn_ref": source_ref,
        "turn": artifact.get("json"),
        "descriptor": turn_descriptor,
        "observations": observations,
        "inventory_entries": related_inventory,
    }


def _voice_notification(
    *,
    key: str,
    category: str,
    summary: str,
    source_ref: str | None,
    kind: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "category": category,
        "kind": kind,
        "summary": summary,
        "source_ref": source_ref,
    }


def _voice_session_notification(active_session: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(active_session, dict):
        return None
    session_id = str(active_session.get("session_id") or "").strip()
    state = str(active_session.get("final_status") or active_session.get("session_state") or "").strip()
    if not session_id or not state:
        return None
    lowered = state.lower()
    if lowered in {"completed", "complete", "succeeded", "success", "merged", "closed"}:
        return _voice_notification(
            key=f"completion:{session_id}:{lowered}",
            category="completion",
            kind="session_completion",
            summary=f"Session {session_id} completed with state {state}.",
            source_ref=str(active_session.get("source_ref") or "") or None,
        )
    if lowered in {"blocked", "resume_failed", "failed"}:
        return _voice_notification(
            key=f"blocked:{session_id}:{lowered}",
            category="blocked",
            kind="session_blocked",
            summary=f"Session {session_id} is blocked with state {state}.",
            source_ref=str(active_session.get("source_ref") or "") or None,
        )
    if lowered in {"approval_pending", "awaiting_approval"}:
        return _voice_notification(
            key=f"approval:{session_id}:{lowered}",
            category="approval_needed",
            kind="session_approval_pending",
            summary=f"Session {session_id} is waiting on approval.",
            source_ref=str(active_session.get("source_ref") or "") or None,
        )
    return None


def _voice_attention_category(kind: str) -> str | None:
    if kind in {"conversation_action_request", "initiative_open_attention", "execution_approval_pending"}:
        return "approval_needed"
    if kind in {"blocked_worker", "resume_failed", "session_needs_resume", "open_merge_request"}:
        return "blocked"
    return None


def _voice_attention_notifications(
    attention_items: list[dict[str, Any]],
    *,
    conversation_id: str | None,
) -> list[dict[str, Any]]:
    notifications: list[dict[str, Any]] = []
    conversation_token = f"/conversations/{conversation_id}/" if conversation_id else None
    for item in attention_items:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        category = _voice_attention_category(kind)
        if category is None:
            continue
        source_ref = str(item.get("source_ref") or "").strip() or None
        if kind == "conversation_action_request" and conversation_token and source_ref:
            normalized_ref = source_ref.replace("\\", "/")
            if conversation_token not in normalized_ref:
                continue
        attention_id = str(item.get("attention_id") or "").strip()
        summary = str(item.get("summary") or kind or "attention").strip()
        notifications.append(
            _voice_notification(
                key=f"{category}:{attention_id or kind}:{source_ref or ''}",
                category=category,
                kind=kind,
                summary=summary,
                source_ref=source_ref,
            )
        )
    return notifications


def voice_runtime(
    *,
    root: Path | None = None,
    refresh: bool = False,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    status = atlas_status(root=base_root, refresh=refresh)
    attention_payload = list_attention(root=base_root, refresh=refresh, limit=25)
    active_session = status.get("active_session") if isinstance(status.get("active_session"), dict) else None
    attention_items = attention_payload.get("items", []) if isinstance(attention_payload.get("items"), list) else []
    notifications = _voice_attention_notifications(attention_items, conversation_id=conversation_id)
    session_notification = _voice_session_notification(active_session)
    if session_notification is not None:
        notifications.insert(0, session_notification)

    conversation_payload = None
    if isinstance(conversation_id, str) and conversation_id.strip():
        try:
            conversation_payload = fetch_conversation(conversation_id.strip(), root=base_root, refresh=refresh)
        except FileNotFoundError:
            conversation_payload = None

    conversation_view = None
    if isinstance(conversation_payload, dict):
        manifest = conversation_payload.get("manifest") if isinstance(conversation_payload.get("manifest"), dict) else {}
        turns = conversation_payload.get("turns", []) if isinstance(conversation_payload.get("turns"), list) else []
        conversation_view = {
            "conversation_id": conversation_payload.get("conversation_id"),
            "manifest_ref": conversation_payload.get("manifest_ref"),
            "summary": manifest.get("summary"),
            "recent_turns": [
                {
                    "turn_id": turn.get("turn_id"),
                    "created_at": turn.get("created_at"),
                    "input_summary": turn.get("input_summary"),
                    "response_summary": turn.get("response_summary"),
                    "action_mode": turn.get("provenance", {}).get("action_mode")
                    if isinstance(turn.get("provenance"), dict)
                    else None,
                }
                for turn in turns[-4:]
                if isinstance(turn, dict)
            ],
        }

    initiatives = status.get("initiatives") if isinstance(status.get("initiatives"), dict) else {}
    conversations = status.get("conversations") if isinstance(status.get("conversations"), dict) else {}
    return {
        "schema_version": VOICE_CONTRACT_VERSION,
        "conversation_id": conversation_id,
        "digests": status.get("digests"),
        "active_session": active_session,
        "attention_summary": {
            "item_count": attention_payload.get("item_count"),
            "content_digest": attention_payload.get("attention_content_digest"),
        },
        "notifications": notifications,
        "initiatives": {
            "active_items": initiatives.get("active_items", [])[:5]
            if isinstance(initiatives.get("active_items"), list)
            else [],
            "open_attention_items": initiatives.get("open_attention_items", [])[:5]
            if isinstance(initiatives.get("open_attention_items"), list)
            else [],
        },
        "conversations": {
            "active_count": conversations.get("active_count"),
            "recent_items": conversations.get("recent_items", [])[:5]
            if isinstance(conversations.get("recent_items"), list)
            else [],
        },
        "conversation": conversation_view,
    }


def fetch_memory(
    memory_id: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    catalog = _load_working_memory(root=base_root, refresh=refresh)
    item = next(
        (
            candidate
            for candidate in catalog.get("items", [])
            if isinstance(candidate, dict) and str(candidate.get("id")) == memory_id
        ),
        None,
    )
    if item is None:
        raise FileNotFoundError(f"Unknown working-memory id: {memory_id}")
    artifact = fetch_artifact(str(item.get("path")), root=base_root)
    source_kind = _memory_source_kind(item)
    return {
        "schema_version": FETCH_CONTRACT_VERSION,
        "id": f"{source_kind}:{memory_id}",
        "title": str(item.get("title") or memory_id),
        "url": _artifact_url(source_kind, memory_id),
        "text": artifact["text"],
        "metadata": _memory_metadata(item),
    }


def _knowledge_record(archive_id: str, *, root: Path, refresh: bool) -> dict[str, Any]:
    bundle = _load_query_bundle(root=root, refresh=refresh)
    for record in bundle.get("records", []):
        if isinstance(record, dict) and str(record.get("archive_id")) == archive_id:
            return record
    raise FileNotFoundError(f"Unknown knowledge archive_id: {archive_id}")


def query_knowledge(
    query: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
    limit: int = 5,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    results = _knowledge_search(query, limit=max(limit, 1), root=base_root, refresh=refresh)
    return {
        "schema_version": "atlas.awareness.knowledge-query.v1",
        "query": query,
        "result_count": len(results),
        "results": [
            {
                "archive_id": item["metadata"]["archive_id"],
                "title": item["title"],
                "url": item["url"],
                "text": item["text"],
                "metadata": item["metadata"],
            }
            for item in results
        ],
    }


def search(
    query: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
    limit: int = 10,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    snapshot = _load_snapshot(root=base_root, refresh=refresh)
    status = atlas_status(root=base_root, refresh=refresh)
    results: list[dict[str, Any]] = []

    for entry in snapshot.get("inventory_entries", []):
        if not isinstance(entry, dict):
            continue
        score = _score_text(query, _inventory_text(entry))
        if score <= 0:
            continue
        entry_type = str(entry.get("entry_type", "artifact"))
        details = entry.get("details", {}) if isinstance(entry.get("details"), dict) else {}
        if entry_type == "session":
            result_id = f"session:{entry.get('key')}"
            url = _artifact_url("session", str(entry.get("key")))
        elif entry_type == "conversation":
            result_id = f"conversation:{entry.get('key')}"
            url = _artifact_url("conversation", str(entry.get("key")))
        elif entry_type == "conversation_turn":
            result_id = f"conversation_turn:{entry.get('key')}"
            url = _artifact_url("conversation_turn", str(entry.get("key")))
        elif entry_type == "memory":
            if str(details.get("memory_kind", "")) == "initiative":
                result_id = f"initiative:{entry.get('key')}"
                url = _artifact_url("initiative", str(entry.get("key")))
            else:
                result_id = f"memory:{entry.get('key')}"
                url = _artifact_url("memory", str(entry.get("key")))
        else:
            result_id = f"artifact:{entry.get('source_ref')}"
            url = _artifact_url("artifact", str(entry.get("source_ref")))
        source_kind = "initiative" if entry_type == "memory" and str(details.get("memory_kind", "")) == "initiative" else entry_type
        results.append(
            {
                "id": result_id,
                "title": str(entry.get("label") or entry.get("key") or entry_type),
                "url": url,
                "text": _trimmed_text(
                    f"{entry_type} {entry.get('status')} {entry.get('source_ref')} {_json_text(entry.get('details', {}))}"
                ),
                "metadata": {
                    "source_kind": source_kind,
                    "key": entry.get("key"),
                    "trust_class": entry.get("trust_class"),
                    "status": entry.get("status"),
                    "memory_kind": details.get("memory_kind"),
                    "automation_level": details.get("automation_level"),
                    "max_automation_level": details.get("max_automation_level"),
                },
                "_score": score,
            }
        )

    for item in snapshot.get("attention_items", []):
        if not isinstance(item, dict):
            continue
        score = _score_text(query, str(item.get("summary", "")), _json_text(item.get("details", {})))
        if score <= 0:
            continue
        results.append(
            {
                "id": f"attention:{item.get('attention_id')}",
                "title": str(item.get("summary") or item.get("attention_id") or "attention"),
                "url": _artifact_url("attention", str(item.get("attention_id"))),
                "text": _trimmed_text(str(item.get("summary", ""))),
                "metadata": {
                    "source_kind": "attention",
                    "severity": item.get("severity"),
                    "source_ref": item.get("source_ref"),
                },
                "_score": score,
            }
        )

    results.extend(_working_memory_search(query, limit=max(limit, 1), root=base_root, refresh=refresh))
    results.extend(_repo_inventory_search(query, limit=max(limit, 1), root=base_root, refresh=refresh))
    results.extend(_knowledge_search(query, limit=max(limit, 1), root=base_root, refresh=refresh))
    initiatives = status.get("initiatives", {}) if isinstance(status.get("initiatives"), dict) else {}
    pending_proposals = initiatives.get("pending_proposal_items", [])
    if isinstance(pending_proposals, list):
        for item in pending_proposals:
            if not isinstance(item, dict):
                continue
            initiative_id = str(item.get("id", "")).strip()
            if not initiative_id:
                continue
            score = _score_text(
                query,
                str(item.get("id", "")),
                str(item.get("title", "")),
                str(item.get("path", "")),
                str(item.get("proposal_ref", "")),
                str(item.get("next_step", "")),
                str(item.get("follow_up", "")),
                str(item.get("attention_summary", "")),
                " ".join(str(value) for value in item.get("waiting_on", []) if isinstance(value, str)),
                " ".join(str(value) for value in item.get("repo_refs", []) if isinstance(value, str)),
            )
            if score <= 0:
                continue
            results.append(
                {
                    "id": f"proposal:{initiative_id}",
                    "title": str(item.get("title") or initiative_id),
                    "url": _artifact_url("proposal", initiative_id),
                    "text": _trimmed_text(
                        f"proposal {item.get('proposal_ref')} next {item.get('next_step')} follow_up {item.get('follow_up')}"
                    ),
                    "metadata": {
                        "source_kind": "proposal",
                        "initiative_id": initiative_id,
                        "proposal_ref": item.get("proposal_ref"),
                        "initiative_ref": item.get("path"),
                    },
                    "_score": score,
                }
            )

    for slice_name, title in _slice_titles().items():
        payload = _status_slice_payload(status, slice_name)
        score = _score_text(
            query,
            slice_name,
            title,
            _json_text(payload["payload"]),
        )
        if score <= 0:
            continue
        results.append(
            {
                "id": f"slice:{slice_name}",
                "title": title,
                "url": _artifact_url("slice", slice_name),
                "text": _trimmed_text(_json_text(payload["payload"])),
                "metadata": {
                    "source_kind": "status_slice",
                    "slice_name": slice_name,
                    "item_count": payload["item_count"],
                },
                "_score": score,
            }
        )
    deduped: dict[str, dict[str, Any]] = {}
    for item in results:
        existing = deduped.get(str(item["id"]))
        if existing is None or int(item["_score"]) > int(existing["_score"]):
            deduped[str(item["id"])] = item
    ordered = sorted(
        deduped.values(),
        key=lambda item: (-int(item["_score"]), str(item["title"]), str(item["id"])),
    )[: max(limit, 1)]
    for item in ordered:
        item.pop("_score", None)
    return {
        "schema_version": SEARCH_CONTRACT_VERSION,
        "query": query,
        "result_count": len(ordered),
        "results": ordered,
    }


def fetch(
    identifier: str,
    *,
    root: Path | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    inventory = _load_repo_inventory(root=base_root, refresh=refresh)
    if identifier.startswith("knowledge:"):
        archive_id = identifier.split(":", 1)[1]
        record = _knowledge_record(archive_id, root=base_root, refresh=refresh)
        query_policy = record.get("query_policy") if isinstance(record.get("query_policy"), dict) else {}
        derived_summary = record.get("derived_summary_text")
        if not query_policy.get("derived_searchable"):
            derived_summary = (
                "Derived content is withheld for this archive. Use the metadata and receipt refs only."
            )
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": str(record.get("archive_id") or record.get("source_name") or archive_id),
            "url": _artifact_url("knowledge", archive_id),
            "text": _json_text(
                {
                    "archive_id": record.get("archive_id"),
                    "source_name": record.get("source_name"),
                    "status": record.get("status"),
                    "promotion_status": record.get("promotion_status"),
                    "indexing_profile": record.get("indexing_profile"),
                    "query_policy": query_policy,
                    "derived_summary_text": derived_summary,
                    "topic_map_terms": record.get("topic_map_terms", []) if query_policy.get("derived_searchable") else [],
                    "evidence_reference_ids": record.get("evidence_reference_ids", []) if query_policy.get("derived_searchable") else [],
                    "paths": record.get("paths"),
                    "receipt": record.get("receipt"),
                }
            ),
            "metadata": {
                "source_kind": "knowledge",
                "archive_id": record.get("archive_id"),
                "query_policy": query_policy,
            },
        }

    if identifier.startswith("attention:"):
        attention_id = identifier.split(":", 1)[1]
        attention = _load_attention(root=base_root, refresh=refresh)
        item = next(
            (
                candidate
                for candidate in attention.get("attention_items", [])
                if isinstance(candidate, dict) and str(candidate.get("attention_id")) == attention_id
            ),
            None,
        )
        if item is None:
            raise FileNotFoundError(f"Unknown attention item: {identifier}")
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": str(item.get("summary") or attention_id),
            "url": _artifact_url("attention", attention_id),
            "text": _json_text(item),
            "metadata": {
                "source_kind": "attention",
                "severity": item.get("severity"),
                "source_ref": item.get("source_ref"),
            },
        }

    if identifier.startswith("session:"):
        session_id = identifier.split(":", 1)[1]
        session = fetch_session(session_id, root=base_root, refresh=refresh)
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": session_id,
            "url": _artifact_url("session", session_id),
            "text": _json_text(session),
            "metadata": {
                "source_kind": "session",
                "session_id": session_id,
                "manifest_ref": session.get("manifest_ref"),
            },
        }

    if identifier.startswith("conversation:"):
        conversation_id = identifier.split(":", 1)[1]
        conversation = fetch_conversation(conversation_id, root=base_root, refresh=refresh)
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": conversation_id,
            "url": _artifact_url("conversation", conversation_id),
            "text": _json_text(conversation),
            "metadata": {
                "source_kind": "conversation",
                "conversation_id": conversation_id,
                "manifest_ref": conversation.get("manifest_ref"),
            },
        }

    if identifier.startswith("conversation_turn:") or identifier.startswith("turn:"):
        turn_id = identifier.split(":", 1)[1]
        turn = fetch_conversation_turn(turn_id, root=base_root, refresh=refresh)
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier if identifier.startswith("conversation_turn:") else f"conversation_turn:{turn_id}",
            "title": turn_id,
            "url": _artifact_url("conversation_turn", turn_id),
            "text": _json_text(turn),
            "metadata": {
                "source_kind": "conversation_turn",
                "turn_id": turn_id,
                "conversation_id": turn.get("conversation_id"),
                "turn_ref": turn.get("turn_ref"),
                "conversation_ref": turn.get("conversation_ref"),
            },
        }

    if identifier.startswith("memory:"):
        memory_id = identifier.split(":", 1)[1]
        return fetch_memory(memory_id, root=base_root, refresh=refresh)

    if identifier.startswith("initiative:"):
        initiative_id = identifier.split(":", 1)[1]
        return fetch_memory(initiative_id, root=base_root, refresh=refresh)

    if identifier.startswith("proposal:"):
        initiative_id = identifier.split(":", 1)[1]
        return _proposal_payload_for_initiative(initiative_id, root=base_root, refresh=refresh)

    if identifier.startswith("slice:"):
        slice_name = identifier.split(":", 1)[1]
        return fetch_status_slice(slice_name, root=base_root, refresh=refresh)

    if identifier.startswith("repo:"):
        repo_id = identifier.split(":", 1)[1]
        item = find_repo_inventory_entry(inventory, repo_id=repo_id)
        if item is None:
            raise FileNotFoundError(f"Unknown repo inventory id: {identifier}")
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": str(item.get("logical_id") or repo_id),
            "url": _artifact_url("repo", str(item.get("logical_id") or repo_id)),
            "text": _json_text(item),
            "metadata": {
                "source_kind": "repo_inventory",
                "logical_id": item.get("logical_id"),
                "local_path": item.get("local_path"),
                "branch": item.get("branch"),
                "dirty": item.get("dirty"),
                "trust_class": item.get("trust_class"),
                "release_eligible": item.get("release_eligible"),
                "related_initiative_refs": item.get("related_initiative_refs", []),
            },
        }

    if identifier.startswith("repo_path:"):
        repo_path = identifier.split(":", 1)[1]
        item = find_repo_inventory_entry(inventory, repo_path=repo_path)
        if item is None:
            raise FileNotFoundError(f"Unknown repo inventory path: {identifier}")
        logical_id = str(item.get("logical_id") or repo_path)
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": f"repo:{logical_id}",
            "title": logical_id,
            "url": _artifact_url("repo", logical_id),
            "text": _json_text(item),
            "metadata": {
                "source_kind": "repo_inventory",
                "logical_id": item.get("logical_id"),
                "local_path": item.get("local_path"),
                "branch": item.get("branch"),
                "dirty": item.get("dirty"),
                "trust_class": item.get("trust_class"),
                "release_eligible": item.get("release_eligible"),
                "related_initiative_refs": item.get("related_initiative_refs", []),
            },
        }

    if identifier.startswith("excluded_surface:"):
        surface_id = identifier.split(":", 1)[1]
        item = find_excluded_surface(inventory, surface_id)
        if item is None:
            raise FileNotFoundError(f"Unknown excluded surface: {identifier}")
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": str(item.get("surface_id") or surface_id),
            "url": _artifact_url("excluded_surface", str(item.get("surface_id") or surface_id)),
            "text": _json_text(item),
            "metadata": {
                "source_kind": "excluded_surface",
                "surface_id": item.get("surface_id"),
                "local_path": item.get("local_path"),
                "trust_class": item.get("trust_class"),
                "visibility_mode": item.get("visibility_mode"),
            },
        }

    if identifier.startswith("artifact:"):
        ref = identifier.split(":", 1)[1]
        artifact = fetch_artifact(ref, root=base_root)
        return {
            "schema_version": FETCH_CONTRACT_VERSION,
            "id": identifier,
            "title": artifact["title"],
            "url": artifact["url"],
            "text": artifact["text"],
            "metadata": {
                "source_kind": "artifact",
                "ref": artifact["ref"],
                "media_type": artifact["media_type"],
            },
        }

    raise FileNotFoundError(f"Unknown fetch identifier: {identifier}")
