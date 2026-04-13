from __future__ import annotations

import argparse
import json
from pathlib import Path

from _pipeline import (
    QUERY_BUNDLE_VERSION,
    QUERY_RESULT_VERSION,
    knowledge_query_bundle_path,
    read_json,
    relative_to_atlas,
    resolve_atlas_path,
    tokenize_lexical_terms,
)


def load_bundle(path: Path) -> dict:
    bundle = read_json(path)
    if bundle.get("schema_version") != QUERY_BUNDLE_VERSION:
        raise ValueError(
            f"Query bundle schema_version must be '{QUERY_BUNDLE_VERSION}', got '{bundle.get('schema_version')}'."
        )
    return bundle


def score_record(record: dict, query: str, query_tokens: list[str]) -> tuple[int, list[str]]:
    matched_fields: list[str] = []
    score = 0
    archive_id = str(record.get("archive_id", "")).lower()
    if query and query == archive_id:
        score += 100
        matched_fields.append("archive_id:exact")
    elif query and query in archive_id:
        score += 40
        matched_fields.append("archive_id:substring")

    search_terms = record.get("search_terms", {})
    metadata_terms = set(search_terms.get("metadata", []))
    derived_terms = set(search_terms.get("derived", []))
    evidence_terms = set(search_terms.get("evidence", []))

    if query and query in " ".join(str(term) for term in search_terms.get("metadata", [])):
        score += 10
        matched_fields.append("metadata:phrase")
    if query and query in " ".join(str(term) for term in search_terms.get("derived", [])):
        score += 6
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
    return score, matched_fields


def render_result(record: dict, score: int, matched_fields: list[str]) -> dict:
    result = {
        "archive_id": record.get("archive_id"),
        "source_name": record.get("source_name"),
        "status": record.get("status"),
        "privacy_flag": record.get("privacy_flag"),
        "promotion_status": record.get("promotion_status"),
        "indexing_profile": record.get("indexing_profile"),
        "retention_class": record.get("retention_class"),
        "query_policy": record.get("query_policy"),
        "paths": record.get("paths"),
        "receipt": record.get("receipt"),
        "score": score,
        "matched_fields": matched_fields,
    }
    if record.get("query_policy", {}).get("derived_searchable"):
        result["derived_summary_text"] = record.get("derived_summary_text")
        result["topic_map_terms"] = record.get("topic_map_terms", [])
        result["evidence_reference_ids"] = record.get("evidence_reference_ids", [])
    return result


def query_bundle(bundle: dict, query_text: str, limit: int) -> dict:
    normalized_query = " ".join(query_text.lower().split())
    query_tokens = tokenize_lexical_terms(normalized_query)
    ranked: list[dict] = []

    for record in bundle.get("records", []):
        score, matched_fields = score_record(record, normalized_query, query_tokens)
        if score <= 0:
            continue
        ranked.append(render_result(record, score, matched_fields))

    ranked.sort(
        key=lambda item: (
            -int(item["score"]),
            -len(item["matched_fields"]),
            str(item["archive_id"]),
        )
    )

    return {
        "schema_version": QUERY_RESULT_VERSION,
        "bundle_path": relative_to_atlas(knowledge_query_bundle_path()),
        "bundle_content_digest": bundle.get("content_digest"),
        "query": query_text,
        "query_tokens": query_tokens,
        "result_count": len(ranked[:limit]),
        "results": ranked[:limit],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search the deterministic ATLAS knowledge query bundle using lexical scoring over allowed fields only."
    )
    parser.add_argument("query", nargs="+")
    parser.add_argument("--bundle-path", type=Path)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    bundle_path = resolve_atlas_path(args.bundle_path) if args.bundle_path else knowledge_query_bundle_path()
    bundle = load_bundle(bundle_path)
    result = query_bundle(bundle, " ".join(args.query), limit=max(args.limit, 1))
    result["bundle_path"] = relative_to_atlas(bundle_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
