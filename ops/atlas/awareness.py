from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, resolve_atlas_path
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import load_descriptors, read_json, register_artifact_descriptors, write_json
from ops.cortex.render_status import render_status_payload
from ops.cortex.world_model import (
    attention_output_path,
    snapshot_output_path,
    world_model_state_root,
    write_world_model_state,
)
from ops.knowledge._pipeline import build_query_bundle, knowledge_query_bundle_path

STATUS_CONTRACT_VERSION = "atlas.awareness.status.v1"
SEARCH_CONTRACT_VERSION = "atlas.awareness.search.v1"
FETCH_CONTRACT_VERSION = "atlas.awareness.fetch.v1"
SESSION_CONTRACT_VERSION = "atlas.awareness.session.v1"
ARTIFACT_CONTRACT_VERSION = "atlas.awareness.artifact.v1"

ALLOWED_FETCH_PREFIXES = [
    "docs/",
    "ops/",
    "runtime/atlas/sessions/",
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
        "world_model": status.get("world_model"),
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
    session_root = base_root / "runtime" / "atlas" / "sessions" / session_id
    status_snapshot_path = session_root / "status.snapshot.json"
    status_snapshot = read_json(status_snapshot_path) if status_snapshot_path.exists() else None
    return {
        "schema_version": SESSION_CONTRACT_VERSION,
        "session_id": session_id,
        "manifest_ref": source_ref,
        "manifest": manifest.get("json"),
        "descriptor": session_descriptor,
        "status_snapshot_ref": atlas_relative(status_snapshot_path, root=base_root) if status_snapshot_path.exists() else None,
        "status_snapshot": status_snapshot,
        "observations": observations,
        "inventory_entries": related_inventory,
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
    results: list[dict[str, Any]] = []

    for entry in snapshot.get("inventory_entries", []):
        if not isinstance(entry, dict):
            continue
        score = _score_text(query, _inventory_text(entry))
        if score <= 0:
            continue
        entry_type = str(entry.get("entry_type", "artifact"))
        if entry_type == "session":
            result_id = f"session:{entry.get('key')}"
            url = _artifact_url("session", str(entry.get("key")))
        else:
            result_id = f"artifact:{entry.get('source_ref')}"
            url = _artifact_url("artifact", str(entry.get("source_ref")))
        results.append(
            {
                "id": result_id,
                "title": str(entry.get("label") or entry.get("key") or entry_type),
                "url": url,
                "text": _trimmed_text(
                    f"{entry_type} {entry.get('status')} {entry.get('source_ref')} {_json_text(entry.get('details', {}))}"
                ),
                "metadata": {
                    "source_kind": entry_type,
                    "key": entry.get("key"),
                    "trust_class": entry.get("trust_class"),
                    "status": entry.get("status"),
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

    results.extend(_knowledge_search(query, limit=max(limit, 1), root=base_root, refresh=refresh))
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
