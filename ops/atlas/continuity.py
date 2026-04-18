from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from ops._atlas import atlas_root

MANIFEST_SCHEMA_VERSION = "atlas.continuity.source.manifest.v1"
CONTINUITY_MANIFEST_PATH = "data/imports/knowledge/continuity/harvest-manifest.json"
PLAYBOOK_INITIATIVE_REF = "initiative-playbook-convergence-and-continuity"
PLAYBOOK_PLAN_REF = "wave-9b-playbook-convergence-and-continuity"
SOURCE_TEXT_LIMIT = 40000
HISTORICAL_QUERY_HIT_LIMIT = 5

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "do",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "show",
    "still",
    "that",
    "the",
    "their",
    "these",
    "this",
    "to",
    "up",
    "was",
    "were",
    "what",
    "where",
    "which",
    "with",
}
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_SOURCE_PRIORITY = {
    "reviewed_promotion_note": 7,
    "promotion_note": 6,
    "owner_repo_doc": 5,
    "root_doc": 5,
    "review_note": 4,
    "handoff": 3,
    "import_evaluation": 2,
    "imported_doc": 1,
    "imported_pdf": 1,
    "downloads_residue": 0,
    "other": -1,
}
_CANONICAL_HISTORICAL_QUESTIONS: tuple[dict[str, Any], ...] = (
    {
        "question_id": "original_atlas_roadmap_shape",
        "question": "what was the original Atlas roadmap shape?",
        "search_terms": [
            "original Atlas roadmap shape",
            "universal interoperable technology stack",
            "universal extensible ai-powered os ecosystem",
            "ATLAS absorption plan",
            "two-track export strategy",
            "coordination at the root",
        ],
    },
    {
        "question_id": "playbook_principles_into_atlas",
        "question": "what Playbook principles were meant to carry into Atlas?",
        "search_terms": [
            "Playbook principles",
            "shared principles",
            "repo-local governance owner",
            "docs-first",
            "private-first",
            "owner repos remain the owner of implementation truth",
            "promoted knowledge",
        ],
    },
    {
        "question_id": "persistent_codex_chatgpt_continuity",
        "question": "where did persistent Codex or ChatGPT continuity show up in earlier planning?",
        "search_terms": [
            "Codex",
            "ChatGPT",
            "continuity",
            "project memory",
            "operating doctrine",
            "persistent context",
            "structured handoff",
            "transcript traceability",
            "trace_only",
        ],
    },
    {
        "question_id": "pattern_engine_and_cross_repo_convergence",
        "question": "what prior docs talk about the pattern-recognition engine and cross-repo convergence?",
        "search_terms": [
            "pattern engine",
            "pattern recognition engine",
            "cross-repo convergence",
            "cross-repository",
            "Playbook engine",
            "convergence",
            "Atlas portable",
        ],
    },
    {
        "question_id": "old_ideas_active_deferred_superseded",
        "question": "what old roadmap ideas are still active, deferred, or superseded?",
        "search_terms": [
            "active",
            "deferred",
            "superseded",
            "planned-later",
            "Decision: DEFERRED",
            "archived execution-window snapshot",
        ],
    },
    {
        "question_id": "playbook_specific_vs_atlas_wide",
        "question": "what old ideas were specific to Playbook versus meant for the whole Atlas stack?",
        "search_terms": [
            "Playbook System (Separate)",
            "Atlas (Future, Not Built)",
            "whole Atlas stack",
            "ATLAS orchestrator",
            "owner repos remain the owner of implementation truth",
            "root coordinates, routes, and promotes",
        ],
    },
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _path_exists(path_text: str, *, root: Path) -> bool:
    if path_text.startswith("Downloads/"):
        downloads_path = Path.home() / path_text
        return downloads_path.exists()
    if "*" in path_text:
        return any(root.glob(path_text))
    return (root / path_text).resolve().exists()


def _artifact_type(path_text: str, *, path_kind: str) -> str:
    if path_kind == "dir":
        return "dir_root"
    if path_kind == "glob":
        return "glob_root"
    suffix = Path(path_text).suffix.lower()
    if suffix == ".md":
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix == ".pdf":
        return "pdf"
    return "other"


def _default_source_type(
    source_path: str,
    *,
    lane: str,
    artifact_type: str,
) -> str:
    normalized = source_path.replace("\\", "/")
    if normalized.startswith("docs/knowledge/promotions/"):
        return "promotion_note"
    if normalized.startswith("runtime/receipts/handoffs/"):
        return "handoff"
    if normalized.startswith("docs/knowledge/reviews/"):
        return "review_note"
    if normalized.startswith("data/imports/knowledge/") and normalized.endswith("/EVALUATION.json"):
        return "import_evaluation"
    if normalized.startswith("data/imports/knowledge/"):
        return "imported_pdf" if artifact_type == "pdf" else "imported_doc"
    if normalized.startswith("repos/"):
        return "owner_repo_doc"
    if normalized.startswith("docs/"):
        return "root_doc"
    if normalized.startswith("Downloads/"):
        return "downloads_residue"
    if lane == "imports":
        return "imported_doc"
    return "other"


def _source_entry(
    *,
    source_id: str,
    source_path: str,
    path_kind: str,
    lane: str,
    content_class: str,
    repo_scope: str,
    trust_posture: str,
    status: str,
    promotion_candidate: bool,
    promotion_targets: list[str],
    source_summary: str,
    source_type: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    artifact_type = _artifact_type(source_path, path_kind=path_kind)
    return {
        "source_id": source_id,
        "source_path": source_path,
        "path_kind": path_kind,
        "lane": lane,
        "artifact_type": artifact_type,
        "source_type": source_type or _default_source_type(source_path, lane=lane, artifact_type=artifact_type),
        "content_class": content_class,
        "repo_scope": repo_scope,
        "trust_posture": trust_posture,
        "status": status,
        "initiative_refs": [PLAYBOOK_INITIATIVE_REF],
        "plan_refs": [PLAYBOOK_PLAN_REF],
        "promotion_candidate": promotion_candidate,
        "promotion_targets": promotion_targets,
        "source_summary": source_summary,
        "notes": notes or [],
    }


def validate_continuity_source_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Continuity manifest must be a JSON object."]
    for field in ("manifest_id", "generated_at", "sources"):
        if field not in payload:
            errors.append(f"Missing top-level field: {field}")
    sources = payload.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be an array.")
        return errors

    valid_path_kinds = {"file", "dir", "glob"}
    valid_lanes = {"root_docs_ops", "playbook_roadmap", "imports", "downloads", "other"}
    valid_artifacts = {
        "markdown",
        "json",
        "pdf",
        "chat_export",
        "runbook",
        "plan",
        "dir_root",
        "glob_root",
        "other",
    }
    valid_content_classes = {
        "raw_evidence",
        "structured_artifact",
        "promoted_truth",
        "residue",
        "unknown",
    }
    valid_source_types = {
        "root_doc",
        "owner_repo_doc",
        "imported_doc",
        "imported_pdf",
        "reviewed_promotion_note",
        "promotion_note",
        "handoff",
        "review_note",
        "import_evaluation",
        "downloads_residue",
        "other",
    }
    valid_trust = {"trusted", "visible_untrusted", "unknown"}
    valid_status = {"indexed", "pending_review", "promoted", "superseded", "unknown"}

    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            errors.append(f"sources[{index}] must be an object.")
            continue
        if item.get("path_kind") not in valid_path_kinds:
            errors.append(f"sources[{index}].path_kind is invalid.")
        if item.get("lane") not in valid_lanes:
            errors.append(f"sources[{index}].lane is invalid.")
        if item.get("artifact_type") not in valid_artifacts:
            errors.append(f"sources[{index}].artifact_type is invalid.")
        if "source_type" in item and item.get("source_type") not in valid_source_types:
            errors.append(f"sources[{index}].source_type is invalid.")
        if item.get("content_class") not in valid_content_classes:
            errors.append(f"sources[{index}].content_class is invalid.")
        if item.get("trust_posture") not in valid_trust:
            errors.append(f"sources[{index}].trust_posture is invalid.")
        if item.get("status") not in valid_status:
            errors.append(f"sources[{index}].status is invalid.")
    return errors


def build_continuity_source_manifest(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    manifest_path = base_root / CONTINUITY_MANIFEST_PATH
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Continuity manifest file must contain a JSON object: {manifest_path}")
        errors = validate_continuity_source_manifest(payload)
        if errors:
            raise ValueError("Invalid continuity manifest: " + "; ".join(errors))
        return payload

    sources = [
        _source_entry(
            source_id="root_convergence_doc",
            source_path="docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md",
            path_kind="file",
            lane="root_docs_ops",
            content_class="structured_artifact",
            repo_scope="atlas_root",
            trust_posture="trusted",
            status="indexed",
            promotion_candidate=False,
            promotion_targets=[],
            source_summary="Root-owned roadmap for Playbook convergence and continuity.",
            notes=["Primary stack coordination artifact."],
        ),
        _source_entry(
            source_id="root_adoption_matrix",
            source_path="docs/ops/PLAYBOOK-ADOPTION-MATRIX.md",
            path_kind="file",
            lane="root_docs_ops",
            content_class="structured_artifact",
            repo_scope="atlas_root",
            trust_posture="trusted",
            status="indexed",
            promotion_candidate=False,
            promotion_targets=[],
            source_summary="Root-visible repo adoption matrix with negative-safe working states.",
        ),
        _source_entry(
            source_id="root_continuity_lane",
            source_path="docs/ops/ATLAS-CONTINUITY-LANE.md",
            path_kind="file",
            lane="root_docs_ops",
            content_class="structured_artifact",
            repo_scope="atlas_root",
            trust_posture="trusted",
            status="indexed",
            promotion_candidate=False,
            promotion_targets=[],
            source_summary="Root-owned continuity doctrine and promotion routing.",
        ),
        _source_entry(
            source_id="root_continuity_backlog",
            source_path="docs/ops/ATLAS-CONTINUITY-HARVEST-BACKLOG.md",
            path_kind="file",
            lane="root_docs_ops",
            content_class="structured_artifact",
            repo_scope="atlas_root",
            trust_posture="trusted",
            status="indexed",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Tracked backlog for harvesting prior planning artifacts into explicit continuity work.",
        ),
        _source_entry(
            source_id="playbook_readme",
            source_path="repos/fawxzzy-playbook/README.md",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed" if _path_exists("repos/fawxzzy-playbook/README.md", root=base_root) else "unknown",
            promotion_candidate=True,
            promotion_targets=["knowledge"],
            source_summary="Owner-repo overview and roadmap entry point.",
        ),
        _source_entry(
            source_id="playbook_roadmap_json",
            source_path="repos/fawxzzy-playbook/ROADMAP.json",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed" if _path_exists("repos/fawxzzy-playbook/ROADMAP.json", root=base_root) else "unknown",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Owner-repo roadmap state for convergence follow-on work.",
        ),
        _source_entry(
            source_id="playbook_repo_roadmap_system",
            source_path="repos/fawxzzy-playbook/REPO_ROADMAP_SYSTEM.md",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed"
            if _path_exists("repos/fawxzzy-playbook/REPO_ROADMAP_SYSTEM.md", root=base_root)
            else "unknown",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Owner-repo roadmap system guidance used for traceable promotion.",
        ),
        _source_entry(
            source_id="playbook_next_four_weeks",
            source_path="repos/fawxzzy-playbook/IMPLEMENTATION_PLAN_NEXT_4_WEEKS.md",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed"
            if _path_exists("repos/fawxzzy-playbook/IMPLEMENTATION_PLAN_NEXT_4_WEEKS.md", root=base_root)
            else "unknown",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Short-horizon owner-repo plan that informs downstream continuity routing.",
        ),
        _source_entry(
            source_id="imports_verta_core_glob",
            source_path="data/imports/knowledge/personal/verta-core*/**",
            path_kind="glob",
            lane="imports",
            content_class="raw_evidence",
            repo_scope="atlas_root",
            trust_posture="visible_untrusted",
            status="pending_review",
            promotion_candidate=True,
            promotion_targets=["initiative", "plan", "knowledge"],
            source_summary="Imported historical planning lane for Verta-derived artifacts and retained PDFs.",
            notes=["Discovery root only. Do not infer content before review."],
        ),
        _source_entry(
            source_id="imports_personal_planning_root",
            source_path="data/imports/knowledge/personal/**",
            path_kind="glob",
            lane="imports",
            content_class="raw_evidence",
            repo_scope="atlas_root",
            trust_posture="unknown",
            status="pending_review",
            promotion_candidate=True,
            promotion_targets=["initiative", "plan", "knowledge"],
            source_summary="Broader imported personal planning lane that may contain reusable planning residue.",
            notes=["Keep provenance explicit and promotion manual."],
        ),
        _source_entry(
            source_id="downloads_root_consumption_packet",
            source_path="Downloads/ATLAS-ROOT-PLAYBOOK-CONSUMPTION-PACKET (1).md",
            path_kind="file",
            lane="downloads",
            content_class="residue",
            repo_scope="local_only",
            trust_posture="trusted",
            status="pending_review",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Local packet residue for the root consumption tranche.",
            notes=["Local-only Downloads alias; not a canonical stack path."],
        ),
        _source_entry(
            source_id="downloads_root_consumption_prompt",
            source_path="Downloads/CODEX-PROMPT-ATLAS-ROOT-PLAYBOOK-CONSUMPTION.md",
            path_kind="file",
            lane="downloads",
            content_class="residue",
            repo_scope="local_only",
            trust_posture="trusted",
            status="pending_review",
            promotion_candidate=True,
            promotion_targets=["plan"],
            source_summary="Local prompt residue for the root consumption follow-on.",
            notes=["Local-only Downloads alias; not a canonical stack path."],
        ),
        _source_entry(
            source_id="downloads_continuity_packet",
            source_path="Downloads/ATLAS-CONTINUITY-SEARCH-PROMOTION-PACKET.md",
            path_kind="file",
            lane="downloads",
            content_class="residue",
            repo_scope="local_only",
            trust_posture="trusted",
            status="pending_review",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Local packet residue for the continuity search and promotion tranche.",
            notes=["Local-only Downloads alias; not a canonical stack path."],
        ),
        _source_entry(
            source_id="downloads_owner_repo_patch_packet",
            source_path="Downloads/PLAYBOOK-OWNER-REPO-PATCH-PACKET (1).md",
            path_kind="file",
            lane="downloads",
            content_class="residue",
            repo_scope="local_only",
            trust_posture="trusted",
            status="pending_review",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Owner-repo patch residue kept visible until promoted or superseded.",
            notes=["Local-only Downloads alias; not a canonical stack path."],
        ),
    ]

    for item in sources:
        if item["status"] == "indexed" and not _path_exists(str(item["source_path"]), root=base_root):
            item["status"] = "unknown"
            item["notes"].append("Source was declared but is not currently visible from this workspace.")

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_id": "atlas_continuity_sources_bootstrap",
        "generated_at": _utc_now(),
        "sources": sources,
    }
    errors = validate_continuity_source_manifest(manifest)
    if errors:
        raise ValueError("Invalid continuity manifest: " + "; ".join(errors))
    return manifest


def _resolve_source_path(path_text: str, *, root: Path) -> Path | None:
    if path_text.startswith("Downloads/"):
        resolved = Path.home() / path_text
        return resolved if resolved.exists() and resolved.is_file() else None
    resolved = (root / path_text).resolve()
    return resolved if resolved.exists() and resolved.is_file() else None


def _source_type(item: dict[str, Any]) -> str:
    source_path = str(item.get("source_path") or "")
    lane = str(item.get("lane") or "other")
    artifact_type = str(item.get("artifact_type") or "other")
    explicit = str(item.get("source_type") or "").strip()
    return explicit or _default_source_type(source_path, lane=lane, artifact_type=artifact_type)


def _compact_text(value: str, *, limit: int = SOURCE_TEXT_LIMIT) -> str:
    text = "\n".join(line.strip() for line in value.splitlines() if line.strip())
    return text[:limit]


def _compact_json(value: Any) -> str:
    return _compact_text(json.dumps(value, ensure_ascii=True, indent=2))


def _json_source_text(payload: Any, *, source_type: str) -> str:
    if not isinstance(payload, dict):
        return _compact_json(payload)
    if source_type == "handoff":
        parts: list[str] = [
            str(payload.get("summary") or ""),
            " ".join(str(item) for item in payload.get("repo_refs", []) if isinstance(item, str)),
            " ".join(str(item) for item in payload.get("initiative_refs", []) if isinstance(item, str)),
        ]
        for collection_name, text_fields in (
            ("durable_facts", ("statement",)),
            ("decisions", ("statement", "rationale")),
            ("next_actions", ("title", "scope")),
            ("open_questions", ("question",)),
            ("risks", ("statement", "mitigation")),
        ):
            collection = payload.get(collection_name, [])
            if not isinstance(collection, list):
                continue
            for item in collection:
                if not isinstance(item, dict):
                    continue
                for field in text_fields:
                    value = item.get(field)
                    if isinstance(value, str):
                        parts.append(value)
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            parts.append(_compact_json(metadata))
        return _compact_text("\n".join(part for part in parts if part))
    if source_type == "import_evaluation":
        parts = [
            str(payload.get("archive_id") or ""),
            str(payload.get("safe_for_indexing") or ""),
            str(payload.get("indexing_profile") or ""),
            str(payload.get("promotion_allowed") or ""),
            str(payload.get("quarantine_reason") or ""),
            str(payload.get("notes") or ""),
        ]
        if isinstance(payload.get("risk_flags"), dict):
            parts.append(_compact_json(payload["risk_flags"]))
        if isinstance(payload.get("summary"), dict):
            parts.append(_compact_json(payload["summary"]))
        return _compact_text("\n".join(part for part in parts if part))
    return _compact_json(payload)


def _pdf_metadata_text(path: Path) -> str:
    import_dir = path.parent.parent if path.parent.name in {"raw", "extracted"} else path.parent
    parts = [path.name]
    for meta_name in ("IMPORT-MANIFEST.json", "EVALUATION.json"):
        meta_path = import_dir / meta_name
        if not meta_path.exists():
            continue
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        parts.extend(
            value
            for value in (
                payload.get("archive_id"),
                payload.get("slug"),
                payload.get("document_metadata", {}).get("title")
                if isinstance(payload.get("document_metadata"), dict)
                else None,
                payload.get("document_metadata", {}).get("source_origin")
                if isinstance(payload.get("document_metadata"), dict)
                else None,
                payload.get("safe_for_indexing"),
                payload.get("indexing_profile"),
                payload.get("promotion_status"),
                payload.get("notes"),
            )
            if isinstance(value, str) and value.strip()
        )
        related_topics = (
            payload.get("document_metadata", {}).get("related_topics")
            if isinstance(payload.get("document_metadata"), dict)
            else None
        )
        if isinstance(related_topics, list):
            parts.append(" ".join(str(item) for item in related_topics if isinstance(item, str)))
    return _compact_text("\n".join(parts))


def _source_search_text(item: dict[str, Any], *, root: Path) -> tuple[str, str]:
    metadata_text = _compact_text(
        "\n".join(
            part
            for part in (
                str(item.get("source_id") or ""),
                str(item.get("source_path") or ""),
                str(item.get("source_summary") or ""),
                " ".join(str(note) for note in item.get("notes", []) if isinstance(note, str)),
                str(_source_type(item)),
                str(item.get("content_class") or ""),
                str(item.get("trust_posture") or ""),
                str(item.get("status") or ""),
            )
            if part
        )
    )
    if str(item.get("path_kind") or "") != "file":
        return metadata_text, "metadata"
    resolved = _resolve_source_path(str(item.get("source_path") or ""), root=root)
    if resolved is None:
        return metadata_text, "metadata"

    artifact_type = str(item.get("artifact_type") or "")
    source_type = _source_type(item)
    try:
        if artifact_type == "json":
            payload = json.loads(resolved.read_text(encoding="utf-8"))
            content_text = _json_source_text(payload, source_type=source_type)
        elif artifact_type == "pdf":
            content_text = _pdf_metadata_text(resolved)
        else:
            content_text = _compact_text(resolved.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        content_text = ""
    combined = _compact_text("\n".join(part for part in (metadata_text, content_text) if part))
    return combined, "content" if content_text else "metadata"


def _query_tokens(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if len(token) > 2 and token not in _STOPWORDS
    ]


def _matched_terms(query_text: str, search_terms: list[str], haystack: str) -> tuple[int, list[str]]:
    haystack_lower = haystack.lower()
    score = 0
    matches: list[str] = []
    for term in [query_text, *search_terms]:
        normalized = " ".join(term.lower().split())
        if not normalized:
            continue
        if normalized in haystack_lower:
            score += 30 if " " in normalized else 12
            matches.append(term)
            continue
        tokens = []
        for token in _query_tokens(normalized):
            if token not in tokens:
                tokens.append(token)
        token_hits = [token for token in tokens if token in haystack_lower]
        required_hits = 1 if len(tokens) <= 1 else 2
        if len(token_hits) >= required_hits:
            score += len(token_hits) * 4
            matches.extend(token_hits)
    deduped_matches: list[str] = []
    seen: set[str] = set()
    for match in matches:
        key = match.lower().strip()
        if key and key not in seen:
            seen.add(key)
            deduped_matches.append(match)
    return score, deduped_matches


def _matched_excerpt(text: str, matches: list[str]) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered_matches = [match.lower() for match in matches]
    for line in lines:
        line_lower = line.lower()
        if any(match in line_lower for match in lowered_matches):
            return line[:240]
    return lines[0][:240] if lines else ""


def evaluate_historical_planning_query(
    question: str,
    *,
    root: Path | None = None,
    search_terms: list[str] | None = None,
    limit: int = HISTORICAL_QUERY_HIT_LIMIT,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    manifest = build_continuity_source_manifest(root=base_root)
    terms = search_terms or []
    hits: list[dict[str, Any]] = []

    for raw_item in manifest.get("sources", []):
        if not isinstance(raw_item, dict):
            continue
        if str(raw_item.get("path_kind") or "") != "file":
            continue
        source_type = _source_type(raw_item)
        if source_type == "downloads_residue":
            continue
        haystack, grounding_mode = _source_search_text(raw_item, root=base_root)
        score, matched = _matched_terms(question, terms, haystack)
        if score <= 0:
            continue
        hits.append(
            {
                "source_id": raw_item.get("source_id"),
                "source_path": raw_item.get("source_path"),
                "source_type": source_type,
                "artifact_type": raw_item.get("artifact_type"),
                "content_class": raw_item.get("content_class"),
                "trust_posture": raw_item.get("trust_posture"),
                "status": raw_item.get("status"),
                "grounding_mode": grounding_mode,
                "matched_terms": matched,
                "excerpt": _matched_excerpt(haystack, matched),
                "_score": score,
                "_priority": _SOURCE_PRIORITY.get(source_type, 0),
            }
        )

    hits.sort(
        key=lambda item: (
            -int(item["_priority"]),
            -int(item["_score"]),
            str(item.get("source_path") or ""),
        )
    )
    trimmed_hits: list[dict[str, Any]] = []
    source_type_caps = {
        "reviewed_promotion_note": 1,
        "promotion_note": 1,
        "root_doc": 1,
        "owner_repo_doc": 1,
    }
    selected_type_counts: Counter[str] = Counter()
    for hit in hits:
        source_type = str(hit.get("source_type") or "other")
        cap = source_type_caps.get(source_type)
        if cap is not None and selected_type_counts[source_type] >= cap:
            continue
        trimmed_hits.append(hit)
        selected_type_counts[source_type] += 1
        if len(trimmed_hits) >= max(limit, 1):
            break
    strong_hit = any(
        str(hit.get("trust_posture") or "") == "trusted"
        and str(hit.get("content_class") or "") in {"promoted_truth", "structured_artifact"}
        and str(hit.get("source_type") or "") not in {"handoff", "downloads_residue"}
        for hit in trimmed_hits
    )
    status = "answered" if strong_hit else "partial" if trimmed_hits else "missing"
    if status == "missing":
        gap_reason = "No manifest-backed historical planning source matched the question terms."
    elif status == "partial":
        gap_reason = "Only trust-bounded, handoff-level, or raw-evidence matches were found."
    else:
        gap_reason = None

    source_type_counts = Counter(str(hit.get("source_type") or "other") for hit in trimmed_hits)
    for hit in trimmed_hits:
        hit.pop("_score", None)
        hit.pop("_priority", None)
    return {
        "question": question,
        "status": status,
        "hit_count": len(trimmed_hits),
        "hits": trimmed_hits,
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "gap_reason": gap_reason,
    }


def build_historical_query_coverage(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    items: list[dict[str, Any]] = []
    source_type_counts: Counter[str] = Counter()

    for spec in _CANONICAL_HISTORICAL_QUESTIONS:
        result = evaluate_historical_planning_query(
            str(spec["question"]),
            root=base_root,
            search_terms=[str(term) for term in spec.get("search_terms", []) if isinstance(term, str)],
        )
        result["question_id"] = spec["question_id"]
        items.append(result)
        source_type_counts.update(result.get("source_type_counts", {}))

    status_counts = Counter(str(item.get("status") or "missing") for item in items)
    overall_status = "answered"
    if status_counts.get("missing", 0) > 0:
        overall_status = "partial" if status_counts.get("answered", 0) or status_counts.get("partial", 0) else "missing"
    elif status_counts.get("partial", 0) > 0:
        overall_status = "partial"

    return {
        "status": overall_status,
        "item_count": len(items),
        "items": items,
        "answered_count": status_counts.get("answered", 0),
        "partial_count": status_counts.get("partial", 0),
        "missing_count": status_counts.get("missing", 0),
        "source_type_counts": dict(sorted(source_type_counts.items())),
    }


def build_continuity_status_slices(*, root: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    manifest = build_continuity_source_manifest(root=base_root)
    historical_query_coverage = build_historical_query_coverage(root=base_root)
    sources = manifest.get("sources", []) if isinstance(manifest.get("sources"), list) else []

    lane_counts = Counter(str(item.get("lane") or "other") for item in sources if isinstance(item, dict))
    status_counts = Counter(str(item.get("status") or "unknown") for item in sources if isinstance(item, dict))
    content_counts = Counter(str(item.get("content_class") or "unknown") for item in sources if isinstance(item, dict))

    queue_items = [
        {
            "source_id": item.get("source_id"),
            "source_path": item.get("source_path"),
            "lane": item.get("lane"),
            "status": item.get("status"),
            "promotion_targets": item.get("promotion_targets", []),
            "content_class": item.get("content_class"),
            "source_summary": item.get("source_summary"),
        }
        for item in sources
        if isinstance(item, dict)
        and bool(item.get("promotion_candidate"))
        and str(item.get("status") or "") != "promoted"
    ]
    lane_priority = {"root_docs_ops": 0, "playbook_roadmap": 1, "imports": 2, "downloads": 3, "other": 4}
    queue_items.sort(
        key=lambda item: (
            lane_priority.get(str(item.get("lane") or "other"), 9),
            str(item.get("status") or ""),
            str(item.get("source_id") or ""),
        )
    )

    group_items = [
        {
            "lane": lane,
            "source_count": count,
            "pending_review_count": sum(
                1
                for item in sources
                if isinstance(item, dict)
                and str(item.get("lane") or "") == lane
                and str(item.get("status") or "") == "pending_review"
            ),
            "promotion_candidate_count": sum(
                1
                for item in sources
                if isinstance(item, dict)
                and str(item.get("lane") or "") == lane
                and bool(item.get("promotion_candidate"))
            ),
        }
        for lane, count in sorted(lane_counts.items())
    ]

    handoff_schema_ref = "schemas/atlas.continuity.handoff.v1.json"
    handoff_receipt_count = len(list((base_root / "runtime" / "receipts" / "handoffs").glob("*.json")))
    coverage_status = "structured"
    if not (base_root / handoff_schema_ref).exists():
        coverage_status = "partial"
    elif status_counts.get("pending_review", 0) > 0:
        coverage_status = "partial"

    coverage = {
        "status": coverage_status,
        "item_count": len(sources),
        "source_count": len(sources),
        "pending_review_count": status_counts.get("pending_review", 0),
        "indexed_count": status_counts.get("indexed", 0),
        "promoted_count": status_counts.get("promoted", 0),
        "handoff_schema_ref": handoff_schema_ref,
        "handoff_receipt_count": handoff_receipt_count,
        "lane_doc_refs": [
            "docs/ops/ATLAS-CONTINUITY-LANE.md",
            "docs/ops/ATLAS-CONTINUITY-HARVEST-BACKLOG.md",
        ],
        "historical_query_status": historical_query_coverage.get("status"),
        "historical_answered_count": historical_query_coverage.get("answered_count"),
        "historical_partial_count": historical_query_coverage.get("partial_count"),
        "historical_missing_count": historical_query_coverage.get("missing_count"),
        "transcript_role": "trace_only",
        "transcript_memory": False,
    }

    slices = {
        "continuity_source_inventory": {
            "item_count": len(sources),
            "items": sources,
            "manifest_id": manifest["manifest_id"],
        },
        "continuity_promotion_queue": {
            "item_count": len(queue_items),
            "items": queue_items,
        },
        "continuity_source_groups": {
            "item_count": len(group_items),
            "items": group_items,
            "lane_counts": dict(sorted(lane_counts.items())),
        },
        "continuity_search_status": {
            "item_count": len(sources),
            "items": [],
            "status": coverage_status,
            "indexed_count": status_counts.get("indexed", 0),
            "pending_review_count": status_counts.get("pending_review", 0),
            "raw_evidence_count": content_counts.get("raw_evidence", 0),
            "structured_artifact_count": content_counts.get("structured_artifact", 0),
            "residue_count": content_counts.get("residue", 0),
            "historical_query_status": historical_query_coverage.get("status"),
            "historical_query_slice": "continuity_historical_query_coverage",
        },
        "continuity_historical_query_coverage": historical_query_coverage,
        "continuity_coverage": coverage | {"items": []},
    }
    return manifest, slices
