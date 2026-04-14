from __future__ import annotations

import argparse
import json
from pathlib import Path

from _pipeline import (
    PROMOTION_STATUSES,
    discover_import_manifests,
    read_json,
    resolve_atlas_path,
)

RELEVANCE_TERMS = {
    "atlas": 6,
    "stack": 6,
    "git": 5,
    "versioning": 5,
    "openai": 4,
    "storage": 5,
    "compression": 4,
    "deduplication": 4,
    "graph": 3,
    "interoperability": 5,
    "universal": 3,
    "ecosystem": 3,
    "linux": 3,
    "ai": 3,
}


def keyword_score(text: str) -> tuple[int, list[str]]:
    lowered = text.lower()
    matches: list[str] = []
    score = 0
    for term, value in sorted(RELEVANCE_TERMS.items()):
        if term in lowered:
            score += value
            matches.append(term)
    return score, matches


def privacy_score(privacy_flag: str) -> int:
    return {"shareable": 30, "mixed": 12, "private": 4}.get(privacy_flag, 0)


def risk_penalty(risk_flags: dict[str, bool]) -> int:
    penalty = 0
    if risk_flags.get("credentials_secrets_risk"):
        penalty -= 100
    if risk_flags.get("copyrighted_courseware_risk"):
        penalty -= 40
    if risk_flags.get("executable_content"):
        penalty -= 25
    if risk_flags.get("personal_private_material"):
        penalty -= 5
    return penalty


def indexing_score(indexing_profile: str, safe_for_indexing: str) -> int:
    base = {"yes": 40, "restricted": 28, "no": 0, "pending_review": 0}.get(safe_for_indexing, 0)
    if indexing_profile == "derived_only":
        base += 18
    elif indexing_profile == "metadata_only":
        base += 6
    elif indexing_profile == "full_text":
        base += 10
    return base


def promotion_score(promotion_allowed: bool, promotion_status: str) -> int:
    score = 60 if promotion_allowed else -60
    if promotion_status in PROMOTION_STATUSES - {"not_promoted"}:
        score += 12
    return score


def rank_candidate(manifest_file: Path) -> dict[str, object]:
    archive_path = manifest_file.parent
    manifest = read_json(manifest_file)
    evaluation_path = archive_path / "EVALUATION.json"
    evaluation = read_json(evaluation_path) if evaluation_path.exists() else {}
    normalized_path = resolve_atlas_path(
        Path("runtime") / "cortex" / "catalog" / "knowledge" / f"{manifest['source_name']}--{manifest['slug']}.json"
    )
    normalized = read_json(normalized_path) if normalized_path.exists() else {}
    promotion_doc_path = resolve_atlas_path(Path("docs") / "knowledge" / "promotions" / f"{manifest['archive_id']}.md")
    title = " ".join(
        str(value)
        for value in [
            manifest.get("source_name", ""),
            manifest.get("slug", ""),
            normalized.get("document_metadata", {}).get("title", ""),
        ]
    ).strip()
    relevance_score, relevance_terms = keyword_score(title)
    safe_for_indexing = str(evaluation.get("safe_for_indexing", manifest.get("safe_for_indexing", "pending_review")))
    indexing_profile = str(normalized.get("indexing_profile", evaluation.get("indexing_profile", manifest.get("indexing_profile", "metadata_only"))))
    promotion_allowed = bool(evaluation.get("promotion_allowed", False))
    risk_flags = evaluation.get("risk_flags", {})
    ranking = (
        promotion_score(promotion_allowed, str(manifest.get("promotion_status", "not_promoted")))
        + indexing_score(indexing_profile, safe_for_indexing)
        + privacy_score(str(manifest.get("privacy_flag", "private")))
        + relevance_score
        + risk_penalty(risk_flags if isinstance(risk_flags, dict) else {})
    )
    return {
        "archive_id": manifest["archive_id"],
        "source_name": manifest.get("source_name"),
        "slug": manifest.get("slug"),
        "promotion_allowed": promotion_allowed,
        "safe_for_indexing": safe_for_indexing,
        "indexing_profile": indexing_profile,
        "privacy_flag": manifest.get("privacy_flag"),
        "promotion_status": manifest.get("promotion_status"),
        "retention_class": manifest.get("retention_class"),
        "risk_flags": risk_flags,
        "relevance_terms": relevance_terms,
        "promotion_doc_path": promotion_doc_path.relative_to(resolve_atlas_path(Path("."))).as_posix() if promotion_doc_path.exists() else "",
        "score": ranking,
        "eligible_for_derived_only": bool(
            promotion_allowed
            and safe_for_indexing in {"restricted", "yes"}
            and str(manifest.get("privacy_flag")) in {"private", "mixed", "shareable"}
            and not (isinstance(risk_flags, dict) and (
                risk_flags.get("credentials_secrets_risk")
                or risk_flags.get("copyrighted_courseware_risk")
            ))
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank knowledge archives for safe derived_only promotion.")
    parser.add_argument("--output", choices={"json", "markdown"}, default="json")
    args = parser.parse_args()

    candidates = [rank_candidate(path) for path in discover_import_manifests()]
    candidates.sort(
        key=lambda item: (
            -int(item["score"]),
            -int(item["promotion_allowed"]),
            -int(item["eligible_for_derived_only"]),
            str(item["archive_id"]),
        )
    )
    payload = {"candidates": candidates}
    if args.output == "markdown":
        lines = ["# Promotion Candidate Ranking", ""]
        for item in candidates:
            status = "eligible" if item["eligible_for_derived_only"] else "hold"
            terms = ", ".join(item["relevance_terms"]) if item["relevance_terms"] else "none"
            lines.append(
                f"- `{item['archive_id']}`: score={item['score']} status={status} safe_for_indexing={item['safe_for_indexing']} indexing_profile={item['indexing_profile']} terms={terms}"
            )
        print("\n".join(lines))
        return 0
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
