from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes, resolve_atlas_path
from ops.knowledge._pipeline import (
    QUERY_BUNDLE_VERSION,
    knowledge_query_bundle_path,
    read_json,
    read_promotion_doc,
    stable_json_digest,
    tokenize_lexical_terms,
)

WORKER_CONTEXT_VERSION = "atlas.cortex.worker-context.v1"


def load_bundle(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if payload.get("schema_version") != QUERY_BUNDLE_VERSION:
        raise ValueError(
            f"Query bundle schema_version must be '{QUERY_BUNDLE_VERSION}', got '{payload.get('schema_version')}'."
        )
    return payload


def normalize_query_terms(values: list[str]) -> list[str]:
    terms = []
    for value in values:
        normalized = " ".join(str(value).strip().split())
        if normalized:
            terms.append(normalized)
    return sorted(set(terms), key=lambda item: item.lower())


def score_record(record: dict[str, Any], query_terms: list[str], task_tags: list[str]) -> tuple[int, list[str]]:
    matched_fields: list[str] = []
    score = 0
    archive_id = str(record.get("archive_id", "")).lower()
    search_terms = record.get("search_terms", {})
    metadata_terms = set(search_terms.get("metadata", []))
    derived_terms = set(search_terms.get("derived", []))
    evidence_terms = set(search_terms.get("evidence", []))

    normalized_queries = [" ".join(term.lower().split()) for term in query_terms if term.strip()]
    query_tokens = tokenize_lexical_terms(*normalized_queries, *task_tags)

    for query in normalized_queries:
        if not query:
            continue
        if query == archive_id:
            score += 100
            matched_fields.append("archive_id:exact")
        elif query in archive_id:
            score += 40
            matched_fields.append("archive_id:substring")
        if query in " ".join(str(term) for term in search_terms.get("metadata", [])):
            score += 12
            matched_fields.append("metadata:phrase")
        if query in " ".join(str(term) for term in search_terms.get("derived", [])):
            score += 7
            matched_fields.append("derived:phrase")

    for token in query_tokens:
        if token in metadata_terms:
            score += 12
            matched_fields.append(f"metadata:{token}")
        if token in derived_terms:
            score += 7
            matched_fields.append(f"derived:{token}")
        if token in evidence_terms:
            score += 4
            matched_fields.append(f"evidence:{token}")

    deduped = list(dict.fromkeys(matched_fields))
    return score, deduped


def select_records(
    bundle: dict[str, Any],
    *,
    query_terms: list[str],
    task_tags: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for record in bundle.get("records", []):
        score, matched_fields = score_record(record, query_terms, task_tags)
        if score <= 0:
            continue
        ranked.append(
            {
                "record": record,
                "score": score,
                "matched_fields": matched_fields,
            }
        )

    ranked.sort(
        key=lambda item: (
            -int(item["score"]),
            -len(item["matched_fields"]),
            str(item["record"].get("archive_id", "")),
        )
    )
    return ranked[:limit]


def build_context_item(scored: dict[str, Any]) -> dict[str, Any]:
    record = scored["record"]
    runtime_catalog_path = resolve_atlas_path(record["paths"]["runtime_catalog_path"], root=atlas_root())
    receipt_path = resolve_atlas_path(record["paths"]["latest_receipt_path"], root=atlas_root())
    runtime_catalog = read_json(runtime_catalog_path)
    receipt = read_json(receipt_path)

    item: dict[str, Any] = {
        "archive_id": record.get("archive_id"),
        "source_name": record.get("source_name"),
        "status": record.get("status"),
        "privacy_flag": record.get("privacy_flag"),
        "promotion_status": record.get("promotion_status"),
        "indexing_profile": record.get("indexing_profile"),
        "retention_class": record.get("retention_class"),
        "query_policy": record.get("query_policy"),
        "score": scored["score"],
        "matched_fields": scored["matched_fields"],
        "paths": record.get("paths"),
        "source_digests": record.get("source_digests"),
        "runtime_catalog": {
            "summary": runtime_catalog.get("summary"),
            "notes": runtime_catalog.get("notes"),
            "no_execute_guarantee": runtime_catalog.get("no_execute_guarantee"),
            "risk_flags": runtime_catalog.get("risk_flags"),
            "document_metadata": runtime_catalog.get("document_metadata"),
        },
        "receipt": {
            "receipt_id": receipt.get("receipt_id"),
            "action": receipt.get("action"),
            "recorded_at": receipt.get("recorded_at"),
            "evaluation": receipt.get("evaluation"),
            "validation_results": receipt.get("validation_results"),
            "tooling": receipt.get("tooling"),
            "digests": receipt.get("digests"),
        },
    }

    if bool(record.get("query_policy", {}).get("derived_searchable")):
        promotion_doc_path = record.get("paths", {}).get("promotion_doc_path")
        promotion_doc = (
            read_promotion_doc(resolve_atlas_path(promotion_doc_path, root=atlas_root()))
            if isinstance(promotion_doc_path, str) and promotion_doc_path
            else None
        )
        item["derived"] = {
            "derived_summary_text": record.get("derived_summary_text"),
            "topic_map_terms": record.get("topic_map_terms", []),
            "evidence_reference_ids": record.get("evidence_reference_ids", []),
            "promotion_doc": {
                "path": promotion_doc["path"] if promotion_doc is not None else promotion_doc_path,
                "digest": promotion_doc["digest"] if promotion_doc is not None else record.get("source_digests", {}).get("promotion_doc"),
                "updated_at": promotion_doc["metadata"]["updated_at"] if promotion_doc is not None else None,
            },
        }
    return item


def default_output_path(assignment_id: str) -> Path:
    return atlas_root() / "runtime" / "cortex" / "context" / f"{assignment_id}.json"


def build_worker_context_payload(
    *,
    assignment_id: str,
    worker_id: str,
    task_id: str,
    stack_lock_digest: str,
    query_terms: list[str],
    task_tags: list[str],
    bundle_path: Path,
    limit: int,
) -> dict[str, Any]:
    bundle = load_bundle(bundle_path)
    selected = select_records(bundle, query_terms=query_terms, task_tags=task_tags, limit=limit)
    context_items = [build_context_item(item) for item in selected]

    payload = {
        "schema_version": WORKER_CONTEXT_VERSION,
        "assignment": {
            "assignment_id": assignment_id,
            "worker_id": worker_id,
            "task_id": task_id,
            "stack_lock_digest": stack_lock_digest,
        },
        "query": {
            "terms": query_terms,
            "task_tags": task_tags,
            "bundle_path": atlas_relative(bundle_path),
            "bundle_content_digest": bundle.get("content_digest"),
            "selection_limit": limit,
        },
        "policy": {
            "query_first": True,
            "hydrate_later": True,
            "raw_content_hydration": False,
            "metadata_only_rule": "metadata_only archives contribute metadata only.",
            "derived_only_rule": "derived_only archives may contribute derived summary, topic map, and evidence references when query_policy.derived_searchable is true.",
        },
        "result_count": len(context_items),
        "context_items": context_items,
    }
    return payload | {"content_digest": stable_json_digest(payload)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic Cortex worker context artifact from the promoted knowledge query plane."
    )
    parser.add_argument("--assignment-id", required=True)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--stack-lock-digest", required=True)
    parser.add_argument("--query-term", action="append", dest="query_terms")
    parser.add_argument("--task-tag", action="append", dest="task_tags")
    parser.add_argument("--bundle-path", type=Path)
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    query_terms = normalize_query_terms(args.query_terms or [])
    task_tags = normalize_query_terms(args.task_tags or [])
    if not query_terms:
        query_terms = [args.task_id]

    bundle_path = resolve_atlas_path(args.bundle_path, root=atlas_root()) if args.bundle_path else knowledge_query_bundle_path()
    output_path = resolve_atlas_path(args.output_path, root=atlas_root()) if args.output_path else default_output_path(args.assignment_id)

    payload = build_worker_context_payload(
        assignment_id=args.assignment_id,
        worker_id=args.worker_id,
        task_id=args.task_id,
        stack_lock_digest=args.stack_lock_digest,
        query_terms=query_terms,
        task_tags=task_tags,
        bundle_path=bundle_path,
        limit=max(args.limit, 1),
    )

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "schema_version": WORKER_CONTEXT_VERSION,
                "artifact_type": "worker_context",
                "dry_run": args.dry_run,
                "output_path": normalize_slashes(str(output_path.resolve())),
                "atlas_output_path": atlas_relative(output_path),
                "content_digest": payload["content_digest"],
                "result_count": payload["result_count"],
                "query_terms": query_terms,
                "task_tags": task_tags,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
