from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from ops._atlas import atlas_relative, atlas_root

MANIFEST_SCHEMA_VERSION = "atlas.continuity.source.manifest.v1"
CONTINUITY_HANDOFF_SCHEMA_VERSION = "atlas.continuity.handoff.v1"
CONTINUITY_MANIFEST_PATH = "data/imports/knowledge/continuity/harvest-manifest.json"
PLAYBOOK_INITIATIVE_REF = "initiative-playbook-convergence-and-continuity"
PLAYBOOK_PLAN_REF = "wave-9b-playbook-convergence-and-continuity"
SOURCE_TEXT_LIMIT = 40000
HISTORICAL_QUERY_HIT_LIMIT = 5
INITIATIVE_CONTINUITY_MANIFEST_GLOB = "docs/memory/initiatives/continuity-manifest-*.json"
_BOOK_MARKER_LINE_PATTERN = re.compile(r"^- ([^:]+): `(\d+)%`$")
_CONTINUITY_HANDOFF_SOURCE_CHANNELS = {"codex", "chatgpt", "mixed", "manual"}
_CONTINUITY_HANDOFF_PROMOTION_TARGETS = {"initiative", "working_memory", "plan", "knowledge", "receipt"}
_CONTINUITY_HANDOFF_EVIDENCE_KINDS = {
    "code_change",
    "test",
    "manual_observation",
    "repo_doc",
    "runtime_artifact",
    "chat_summary",
}
_CONTINUITY_HANDOFF_DECISION_STATUSES = {"accepted", "proposed", "deferred", "rejected"}
_CONTINUITY_HANDOFF_PRIORITIES = {"p0", "p1", "p2", "p3"}
_CONTINUITY_HANDOFF_RISK_SEVERITIES = {"low", "medium", "high", "critical"}

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
    superseded_by: list[str] | None = None,
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
        "superseded_by": superseded_by or [],
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
        if "superseded_by" in item:
            superseded_by = item.get("superseded_by")
            if not isinstance(superseded_by, list) or any(
                not isinstance(value, str) or not value.strip() for value in superseded_by
            ):
                errors.append(f"sources[{index}].superseded_by must be an array of non-empty strings.")
    return errors


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_handoff_string_list(
    payload: dict[str, Any],
    key: str,
    *,
    errors: list[str],
    required: bool = True,
) -> list[str]:
    value = payload.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list):
        errors.append(f"{key} must be an array.")
        return []
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not _is_non_empty_string(item):
            errors.append(f"{key}[{index}] must be a non-empty string.")
            continue
        normalized.append(str(item))
    return normalized


def validate_continuity_handoff(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Continuity handoff must be a JSON object."]

    required_fields = (
        "contract_version",
        "artifact_id",
        "created_at",
        "source_channel",
        "summary",
        "repo_refs",
        "initiative_refs",
        "durable_facts",
        "decisions",
        "next_actions",
        "open_questions",
        "risks",
        "promotion_targets",
        "transcript_role",
        "transcript_refs",
    )
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing top-level field: {field}")
    if errors:
        return errors

    if payload.get("contract_version") != CONTINUITY_HANDOFF_SCHEMA_VERSION:
        errors.append(f"contract_version must be '{CONTINUITY_HANDOFF_SCHEMA_VERSION}'.")
    if not _is_non_empty_string(payload.get("artifact_id")):
        errors.append("artifact_id must be a non-empty string.")
    created_at = payload.get("created_at")
    if not _is_non_empty_string(created_at):
        errors.append("created_at must be an ISO 8601 timestamp.")
    else:
        try:
            datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        except ValueError:
            errors.append("created_at must be an ISO 8601 timestamp.")
    if payload.get("source_channel") not in _CONTINUITY_HANDOFF_SOURCE_CHANNELS:
        errors.append(
            "source_channel must be one of: "
            + ", ".join(sorted(_CONTINUITY_HANDOFF_SOURCE_CHANNELS))
            + "."
        )
    if not _is_non_empty_string(payload.get("summary")):
        errors.append("summary must be a non-empty string.")

    repo_refs = _validate_handoff_string_list(payload, "repo_refs", errors=errors)
    initiative_refs = _validate_handoff_string_list(payload, "initiative_refs", errors=errors)
    if not repo_refs and not initiative_refs:
        errors.append("At least one repo_ref or initiative_ref is required.")

    durable_facts = payload.get("durable_facts")
    if not isinstance(durable_facts, list) or not durable_facts:
        errors.append("durable_facts must be a non-empty array.")
    elif isinstance(durable_facts, list):
        for index, item in enumerate(durable_facts):
            if not isinstance(item, dict):
                errors.append(f"durable_facts[{index}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("id")):
                errors.append(f"durable_facts[{index}].id must be a non-empty string.")
            if not _is_non_empty_string(item.get("statement")):
                errors.append(f"durable_facts[{index}].statement must be a non-empty string.")
            confidence = item.get("confidence")
            if confidence is not None and confidence not in {"low", "medium", "high"}:
                errors.append(f"durable_facts[{index}].confidence must be low, medium, or high.")
            evidence_kind = item.get("evidence_kind")
            if evidence_kind is not None and evidence_kind not in _CONTINUITY_HANDOFF_EVIDENCE_KINDS:
                errors.append(
                    f"durable_facts[{index}].evidence_kind must be one of: "
                    + ", ".join(sorted(_CONTINUITY_HANDOFF_EVIDENCE_KINDS))
                    + "."
                )
            evidence_refs = item.get("evidence_refs")
            if evidence_refs is not None and not isinstance(evidence_refs, list):
                errors.append(f"durable_facts[{index}].evidence_refs must be an array when present.")
            elif isinstance(evidence_refs, list):
                for evidence_index, evidence_ref in enumerate(evidence_refs):
                    if not _is_non_empty_string(evidence_ref):
                        errors.append(
                            f"durable_facts[{index}].evidence_refs[{evidence_index}] must be a non-empty string."
                        )
            if item.get("promotion_target") not in _CONTINUITY_HANDOFF_PROMOTION_TARGETS:
                errors.append(
                    f"durable_facts[{index}].promotion_target must be one of: "
                    + ", ".join(sorted(_CONTINUITY_HANDOFF_PROMOTION_TARGETS))
                    + "."
                )

    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        errors.append("decisions must be an array.")
    elif isinstance(decisions, list):
        for index, item in enumerate(decisions):
            if not isinstance(item, dict):
                errors.append(f"decisions[{index}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("id")):
                errors.append(f"decisions[{index}].id must be a non-empty string.")
            if not _is_non_empty_string(item.get("statement")):
                errors.append(f"decisions[{index}].statement must be a non-empty string.")
            if item.get("status") not in _CONTINUITY_HANDOFF_DECISION_STATUSES:
                errors.append(
                    f"decisions[{index}].status must be one of: "
                    + ", ".join(sorted(_CONTINUITY_HANDOFF_DECISION_STATUSES))
                    + "."
                )

    next_actions = payload.get("next_actions")
    if not isinstance(next_actions, list):
        errors.append("next_actions must be an array.")
    elif isinstance(next_actions, list):
        for index, item in enumerate(next_actions):
            if not isinstance(item, dict):
                errors.append(f"next_actions[{index}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("id")):
                errors.append(f"next_actions[{index}].id must be a non-empty string.")
            if not _is_non_empty_string(item.get("title")):
                errors.append(f"next_actions[{index}].title must be a non-empty string.")
            acceptance = item.get("acceptance")
            if acceptance is not None and not isinstance(acceptance, list):
                errors.append(f"next_actions[{index}].acceptance must be an array when present.")
            elif isinstance(acceptance, list):
                for acceptance_index, acceptance_item in enumerate(acceptance):
                    if not _is_non_empty_string(acceptance_item):
                        errors.append(
                            f"next_actions[{index}].acceptance[{acceptance_index}] must be a non-empty string."
                        )
            priority = item.get("priority")
            if priority is not None and priority not in _CONTINUITY_HANDOFF_PRIORITIES:
                errors.append(
                    f"next_actions[{index}].priority must be one of: "
                    + ", ".join(sorted(_CONTINUITY_HANDOFF_PRIORITIES))
                    + "."
                )

    open_questions = payload.get("open_questions")
    if not isinstance(open_questions, list):
        errors.append("open_questions must be an array.")
    elif isinstance(open_questions, list):
        for index, item in enumerate(open_questions):
            if not isinstance(item, dict):
                errors.append(f"open_questions[{index}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("id")):
                errors.append(f"open_questions[{index}].id must be a non-empty string.")
            if not _is_non_empty_string(item.get("question")):
                errors.append(f"open_questions[{index}].question must be a non-empty string.")
            blocking = item.get("blocking")
            if blocking is not None and not isinstance(blocking, bool):
                errors.append(f"open_questions[{index}].blocking must be a boolean when present.")

    risks = payload.get("risks")
    if not isinstance(risks, list):
        errors.append("risks must be an array.")
    elif isinstance(risks, list):
        for index, item in enumerate(risks):
            if not isinstance(item, dict):
                errors.append(f"risks[{index}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("id")):
                errors.append(f"risks[{index}].id must be a non-empty string.")
            if not _is_non_empty_string(item.get("statement")):
                errors.append(f"risks[{index}].statement must be a non-empty string.")
            if item.get("severity") not in _CONTINUITY_HANDOFF_RISK_SEVERITIES:
                errors.append(
                    f"risks[{index}].severity must be one of: "
                    + ", ".join(sorted(_CONTINUITY_HANDOFF_RISK_SEVERITIES))
                    + "."
                )

    promotion_targets = _validate_handoff_string_list(payload, "promotion_targets", errors=errors)
    invalid_targets = [
        item for item in promotion_targets if item not in _CONTINUITY_HANDOFF_PROMOTION_TARGETS
    ]
    if invalid_targets:
        errors.append(
            "promotion_targets may contain only: "
            + ", ".join(sorted(_CONTINUITY_HANDOFF_PROMOTION_TARGETS))
            + "."
        )

    if payload.get("transcript_role") != "trace_only":
        errors.append("transcript_role must be 'trace_only'.")
    _validate_handoff_string_list(payload, "transcript_refs", errors=errors)

    metadata = payload.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("metadata must be an object when present.")

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
            source_path="repos/playbook/README.md",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed" if _path_exists("repos/playbook/README.md", root=base_root) else "unknown",
            promotion_candidate=True,
            promotion_targets=["knowledge"],
            source_summary="Owner-repo overview and roadmap entry point.",
        ),
        _source_entry(
            source_id="playbook_roadmap_json",
            source_path="repos/playbook/ROADMAP.json",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed" if _path_exists("repos/playbook/ROADMAP.json", root=base_root) else "unknown",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Owner-repo roadmap state for convergence follow-on work.",
        ),
        _source_entry(
            source_id="playbook_repo_roadmap_system",
            source_path="repos/playbook/REPO_ROADMAP_SYSTEM.md",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed"
            if _path_exists("repos/playbook/REPO_ROADMAP_SYSTEM.md", root=base_root)
            else "unknown",
            promotion_candidate=True,
            promotion_targets=["plan", "knowledge"],
            source_summary="Owner-repo roadmap system guidance used for traceable promotion.",
        ),
        _source_entry(
            source_id="playbook_next_four_weeks",
            source_path="repos/playbook/IMPLEMENTATION_PLAN_NEXT_4_WEEKS.md",
            path_kind="file",
            lane="playbook_roadmap",
            content_class="structured_artifact",
            repo_scope="playbook",
            trust_posture="trusted",
            status="indexed"
            if _path_exists("repos/playbook/IMPLEMENTATION_PLAN_NEXT_4_WEEKS.md", root=base_root)
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


def _load_book_marker_posture(*, root: Path) -> dict[str, int]:
    marker_path = root / "docs" / "atlas-book" / "02-lanes-and-markers.md"
    if not marker_path.exists():
        return {}
    markers: dict[str, int] = {}
    for raw_line in marker_path.read_text(encoding="utf-8").splitlines():
        match = _BOOK_MARKER_LINE_PATTERN.match(raw_line.strip())
        if not match:
            continue
        marker = match.group(1).replace("`", "").strip()
        markers[marker] = int(match.group(2))
    return markers


def _load_open_marker_groups(*, root: Path) -> list[dict[str, Any]]:
    marker_path = root / "docs" / "atlas-book" / "02-lanes-and-markers.md"
    if not marker_path.exists():
        return []

    section: str | None = None
    supporting_group: str | None = None
    items: list[dict[str, Any]] = []
    for raw_line in marker_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "## Active Front-Page Marker Table":
            section = "active_front_page"
            supporting_group = None
            continue
        if line == "## Supporting Open Markers":
            section = "supporting_open"
            supporting_group = None
            continue
        if line.startswith("## "):
            section = None
            supporting_group = None
            continue
        if section == "supporting_open" and line.startswith("### "):
            supporting_group = line.removeprefix("### ").strip()
            continue

        match = _BOOK_MARKER_LINE_PATTERN.match(line)
        if not match or section is None:
            continue

        marker = match.group(1).replace("`", "").strip()
        percent = int(match.group(2))
        items.append(
            {
                "marker": marker,
                "percent": percent,
                "section": section,
                "group": supporting_group if section == "supporting_open" else "front_page",
            }
        )
    return items


def _path_list_health(
    values: Any,
    *,
    root: Path,
    field_name: str,
    require_non_empty: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    refs: list[str] = []
    if not isinstance(values, list):
        return [f"{field_name} must be an array of path refs."], refs
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name}[{index}] must be a non-empty string.")
            continue
        ref = value.strip()
        refs.append(ref)
        if not _path_exists(ref, root=root):
            errors.append(f"{field_name}[{index}] does not exist: {ref}")
    if require_non_empty and not refs:
        errors.append(f"{field_name} must not be empty.")
    return errors, refs


def _surface_list_health(
    values: Any,
    *,
    root: Path,
    field_name: str,
) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[str] = []
    surfaces: list[dict[str, str]] = []
    if not isinstance(values, list):
        return [f"{field_name} must be an array of surface objects."], surfaces
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            errors.append(f"{field_name}[{index}] must be an object.")
            continue
        path_text = value.get("path")
        role_text = value.get("role")
        if not isinstance(path_text, str) or not path_text.strip():
            errors.append(f"{field_name}[{index}].path must be a non-empty string.")
            continue
        if not isinstance(role_text, str) or not role_text.strip():
            errors.append(f"{field_name}[{index}].role must be a non-empty string.")
            continue
        normalized = {"path": path_text.strip(), "role": role_text.strip()}
        surfaces.append(normalized)
        if not _path_exists(normalized["path"], root=root):
            errors.append(f"{field_name}[{index}].path does not exist: {normalized['path']}")
    if not surfaces:
        errors.append(f"{field_name} must not be empty.")
    return errors, surfaces


def _marker_posture_health(
    values: Any,
    *,
    root: Path,
    marker_posture: dict[str, int],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    if not isinstance(values, list):
        return [f"metadata.marker_posture must be an array."], warnings, items
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            errors.append(f"metadata.marker_posture[{index}] must be an object.")
            continue
        marker = value.get("marker")
        percent = value.get("percent")
        source = value.get("source")
        if not isinstance(marker, str) or not marker.strip():
            errors.append(f"metadata.marker_posture[{index}].marker must be a non-empty string.")
            continue
        if not isinstance(percent, int):
            errors.append(f"metadata.marker_posture[{index}].percent must be an integer.")
            continue
        if not isinstance(source, str) or not source.strip():
            errors.append(f"metadata.marker_posture[{index}].source must be a non-empty string.")
            continue
        normalized = {
            "marker": marker.strip(),
            "percent": percent,
            "source": source.strip(),
        }
        items.append(normalized)
        if not _path_exists(normalized["source"], root=root):
            errors.append(
                f"metadata.marker_posture[{index}].source does not exist: {normalized['source']}"
            )
        current_percent = marker_posture.get(normalized["marker"])
        if current_percent is None:
            errors.append(
                f"metadata.marker_posture[{index}].marker is not present in the Book marker table: {normalized['marker']}"
            )
            continue
        if current_percent != normalized["percent"]:
            errors.append(
                f"metadata.marker_posture[{index}] drift: manifest says {normalized['marker']}={normalized['percent']} but Book says {current_percent}."
            )
    if not items:
        errors.append("metadata.marker_posture must not be empty.")
    return errors, warnings, items


def _initiative_manifest_health_item(path: Path, *, root: Path, marker_posture: dict[str, int]) -> dict[str, Any]:
    relative_path = atlas_relative(path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "manifest_id": path.stem,
            "path": relative_path,
            "status": "error",
            "error_count": 1,
            "warning_count": 0,
            "errors": [f"manifest could not be parsed as JSON ({exc})"],
            "warnings": [],
        }
    if not isinstance(payload, dict):
        return {
            "manifest_id": path.stem,
            "path": relative_path,
            "status": "error",
            "error_count": 1,
            "warning_count": 0,
            "errors": ["manifest must be a JSON object"],
            "warnings": [],
        }

    manifest_id = str(payload.get("id") or path.stem)
    if payload.get("contract_version") != "atlas.initiative.v1":
        errors.append("contract_version must be 'atlas.initiative.v1'.")
    if not manifest_id.startswith("continuity-manifest-"):
        errors.append("id must start with 'continuity-manifest-'.")
    status_value = str(payload.get("status") or "")
    if status_value not in {"active", "completed"}:
        warnings.append("status is neither 'active' nor 'completed'.")
    if str(payload.get("owner") or "") != "stack-root":
        warnings.append("owner is not 'stack-root'.")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata must be an object.")
        metadata = {}
    elif str(metadata.get("artifact_kind") or "") != "continuity_manifest":
        errors.append("metadata.artifact_kind must be 'continuity_manifest'.")

    evidence_errors, evidence_refs = _path_list_health(
        payload.get("evidence_refs"),
        root=root,
        field_name="evidence_refs",
        require_non_empty=True,
    )
    errors.extend(evidence_errors)

    governing_errors, governing_refs = _path_list_health(
        metadata.get("governing_receipts"),
        root=root,
        field_name="metadata.governing_receipts",
        require_non_empty=True,
    )
    errors.extend(governing_errors)

    owner_surface_errors, owner_surfaces = _surface_list_health(
        metadata.get("owner_truth_surfaces"),
        root=root,
        field_name="metadata.owner_truth_surfaces",
    )
    errors.extend(owner_surface_errors)

    verification_surface_errors, verification_surfaces = _surface_list_health(
        metadata.get("verification_adoption_surfaces"),
        root=root,
        field_name="metadata.verification_adoption_surfaces",
    )
    errors.extend(verification_surface_errors)

    marker_errors, marker_warnings, marker_items = _marker_posture_health(
        metadata.get("marker_posture"),
        root=root,
        marker_posture=marker_posture,
    )
    errors.extend(marker_errors)
    warnings.extend(marker_warnings)

    current_checkpoint_receipt = metadata.get("current_checkpoint_receipt")
    if not isinstance(current_checkpoint_receipt, str) or not current_checkpoint_receipt.strip():
        errors.append("metadata.current_checkpoint_receipt must be a non-empty string.")
    else:
        current_checkpoint_receipt = current_checkpoint_receipt.strip()
        if not _path_exists(current_checkpoint_receipt, root=root):
            errors.append(
                f"metadata.current_checkpoint_receipt does not exist: {current_checkpoint_receipt}"
            )
        if current_checkpoint_receipt not in evidence_refs:
            errors.append(
                "metadata.current_checkpoint_receipt must also appear in evidence_refs."
            )
        if current_checkpoint_receipt not in governing_refs:
            warnings.append(
                "metadata.current_checkpoint_receipt is not listed in metadata.governing_receipts."
            )

    freshness_checked_receipt = metadata.get("freshness_checked_receipt")
    if not isinstance(freshness_checked_receipt, str) or not freshness_checked_receipt.strip():
        errors.append("metadata.freshness_checked_receipt must be a non-empty string.")
    else:
        freshness_checked_receipt = freshness_checked_receipt.strip()
        if not _path_exists(freshness_checked_receipt, root=root):
            errors.append(
                f"metadata.freshness_checked_receipt does not exist: {freshness_checked_receipt}"
            )
        if freshness_checked_receipt not in evidence_refs:
            warnings.append(
                "metadata.freshness_checked_receipt is not listed in evidence_refs."
            )

    next_package_ladder = metadata.get("next_package_ladder")
    if not isinstance(next_package_ladder, list) or not next_package_ladder:
        warnings.append("metadata.next_package_ladder is empty.")

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"

    return {
        "manifest_id": manifest_id,
        "path": relative_path,
        "status": status,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "current_checkpoint_receipt": current_checkpoint_receipt,
        "freshness_checked_receipt": freshness_checked_receipt,
        "freshness_state": metadata.get("freshness_state"),
        "marker_posture": marker_items,
        "owner_truth_surface_count": len(owner_surfaces),
        "verification_adoption_surface_count": len(verification_surfaces),
        "errors": errors,
        "warnings": warnings,
    }


def build_initiative_continuity_manifest_health(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    marker_posture = _load_book_marker_posture(root=base_root)
    items = [
        _initiative_manifest_health_item(path.resolve(), root=base_root, marker_posture=marker_posture)
        for path in sorted(base_root.glob(INITIATIVE_CONTINUITY_MANIFEST_GLOB))
        if path.is_file()
    ]
    status_counts = Counter(str(item.get("status") or "unknown") for item in items)
    overall_status = "ok"
    if status_counts.get("error", 0) > 0:
        overall_status = "error"
    elif status_counts.get("warning", 0) > 0:
        overall_status = "warning"
    return {
        "status": overall_status,
        "item_count": len(items),
        "manifest_count": len(items),
        "ok_count": status_counts.get("ok", 0),
        "warning_count": status_counts.get("warning", 0),
        "error_count": status_counts.get("error", 0),
        "items": items,
        "marker_table_ref": "docs/atlas-book/02-lanes-and-markers.md",
        "manifest_glob": INITIATIVE_CONTINUITY_MANIFEST_GLOB,
    }


def build_open_marker_manifest_coverage(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    manifest_health = build_initiative_continuity_manifest_health(root=base_root)
    manifest_items = manifest_health.get("items", [])
    manifest_by_marker: dict[str, dict[str, Any]] = {}
    for item in manifest_items:
        if not isinstance(item, dict):
            continue
        for marker_item in item.get("marker_posture", []):
            if not isinstance(marker_item, dict):
                continue
            marker_name = str(marker_item.get("marker") or "").strip()
            if marker_name and marker_name not in manifest_by_marker:
                manifest_by_marker[marker_name] = item

    open_marker_groups = _load_open_marker_groups(root=base_root)
    items: list[dict[str, Any]] = []
    seen_markers: set[str] = set()
    for marker_item in open_marker_groups:
        marker = str(marker_item.get("marker") or "").strip()
        if not marker or marker in seen_markers:
            continue
        seen_markers.add(marker)
        percent = int(marker_item.get("percent") or 0)
        section = str(marker_item.get("section") or "")
        group = str(marker_item.get("group") or "")
        if percent == 0:
            items.append(
                {
                    "marker": marker,
                    "percent": percent,
                    "section": section,
                    "group": group,
                    "eligibility": "excluded_zero",
                    "coverage_status": "not_required",
                    "manifest_id": None,
                    "manifest_path": None,
                }
            )
            continue
        if percent >= 100:
            items.append(
                {
                    "marker": marker,
                    "percent": percent,
                    "section": section,
                    "group": group,
                    "eligibility": "excluded_closed",
                    "coverage_status": "not_required",
                    "manifest_id": None,
                    "manifest_path": None,
                }
            )
            continue

        manifest_item = manifest_by_marker.get(marker)
        coverage_status = "missing"
        manifest_id: str | None = None
        manifest_path: str | None = None
        manifest_health_status: str | None = None
        if manifest_item:
            manifest_id = str(manifest_item.get("manifest_id") or "")
            manifest_path = str(manifest_item.get("path") or "")
            manifest_health_status = str(manifest_item.get("status") or "")
            if manifest_health_status == "ok":
                coverage_status = "manifest_backed"
            elif manifest_health_status == "warning":
                coverage_status = "manifest_warning"
            else:
                coverage_status = "manifest_error"

        items.append(
            {
                "marker": marker,
                "percent": percent,
                "section": section,
                "group": group,
                "eligibility": "eligible_open_marker",
                "coverage_status": coverage_status,
                "manifest_id": manifest_id,
                "manifest_path": manifest_path,
                "manifest_health_status": manifest_health_status,
            }
        )

    counts = Counter(str(item.get("coverage_status") or "unknown") for item in items)
    eligible_count = sum(1 for item in items if item.get("eligibility") == "eligible_open_marker")
    covered_count = counts.get("manifest_backed", 0)
    status = "ok"
    if counts.get("manifest_error", 0) > 0 or counts.get("missing", 0) > 0:
        status = "error"
    elif counts.get("manifest_warning", 0) > 0:
        status = "warning"

    return {
        "status": status,
        "item_count": len(items),
        "eligible_open_marker_count": eligible_count,
        "manifest_backed_count": covered_count,
        "missing_count": counts.get("missing", 0),
        "warning_count": counts.get("manifest_warning", 0),
        "error_count": counts.get("manifest_error", 0),
        "excluded_zero_count": counts.get("not_required", 0),
        "coverage_percent": 0 if eligible_count == 0 else round((covered_count / eligible_count) * 100, 2),
        "items": items,
        "marker_table_ref": "docs/atlas-book/02-lanes-and-markers.md",
        "manifest_glob": INITIATIVE_CONTINUITY_MANIFEST_GLOB,
        "health_slice": "continuity_initiative_manifest_health",
    }


def _load_initiative_manifest_bundles(*, root: Path) -> list[dict[str, Any]]:
    manifest_health = build_initiative_continuity_manifest_health(root=root)
    manifest_items = manifest_health.get("items", [])
    bundles: list[dict[str, Any]] = []
    for item in manifest_items:
        if not isinstance(item, dict):
            continue
        path_text = str(item.get("path") or "").strip()
        if not path_text:
            continue
        manifest_path = (root / path_text).resolve()
        if not manifest_path.exists():
            continue
        try:
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest_payload = {}
        bundles.append(
            {
                "health": item,
                "payload": manifest_payload,
            }
        )
    return bundles


def build_open_marker_restart_index(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    manifest_by_marker: dict[str, dict[str, Any]] = {}
    for bundle in _load_initiative_manifest_bundles(root=base_root):
        health_item = bundle.get("health") if isinstance(bundle.get("health"), dict) else {}
        manifest_payload = bundle.get("payload") if isinstance(bundle.get("payload"), dict) else {}
        for marker_item in health_item.get("marker_posture", []):
            if not isinstance(marker_item, dict):
                continue
            marker_name = str(marker_item.get("marker") or "").strip()
            if marker_name and marker_name not in manifest_by_marker:
                manifest_by_marker[marker_name] = {
                    "health": health_item,
                    "payload": manifest_payload,
                }

    open_marker_groups = _load_open_marker_groups(root=base_root)
    items: list[dict[str, Any]] = []
    seen_markers: set[str] = set()
    for marker_item in open_marker_groups:
        marker = str(marker_item.get("marker") or "").strip()
        if not marker or marker in seen_markers:
            continue
        seen_markers.add(marker)
        percent = int(marker_item.get("percent") or 0)
        section = str(marker_item.get("section") or "")
        group = str(marker_item.get("group") or "")
        if percent == 0:
            items.append(
                {
                    "marker": marker,
                    "percent": percent,
                    "section": section,
                    "group": group,
                    "eligibility": "excluded_zero",
                    "restart_status": "not_required",
                    "manifest_id": None,
                    "manifest_path": None,
                    "current_checkpoint_receipt": None,
                    "freshness_checked_receipt": None,
                    "next_package": None,
                    "blocked_item_count": 0,
                }
            )
            continue
        if percent >= 100:
            items.append(
                {
                    "marker": marker,
                    "percent": percent,
                    "section": section,
                    "group": group,
                    "eligibility": "excluded_closed",
                    "restart_status": "not_required",
                    "manifest_id": None,
                    "manifest_path": None,
                    "current_checkpoint_receipt": None,
                    "freshness_checked_receipt": None,
                    "next_package": None,
                    "blocked_item_count": 0,
                }
            )
            continue

        manifest_bundle = manifest_by_marker.get(marker)
        restart_status = "missing"
        manifest_id: str | None = None
        manifest_path: str | None = None
        current_checkpoint_receipt: str | None = None
        freshness_checked_receipt: str | None = None
        next_package: dict[str, Any] | None = None
        blocked_item_count = 0
        owner_truth_surface_count = 0
        verification_adoption_surface_count = 0
        manifest_health_status: str | None = None
        if manifest_bundle:
            health_item = (
                manifest_bundle.get("health") if isinstance(manifest_bundle.get("health"), dict) else {}
            )
            payload = manifest_bundle.get("payload") if isinstance(manifest_bundle.get("payload"), dict) else {}
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            manifest_id = str(health_item.get("manifest_id") or "") or None
            manifest_path = str(health_item.get("path") or "") or None
            manifest_health_status = str(health_item.get("status") or "")
            current_checkpoint_receipt = (
                str(metadata.get("current_checkpoint_receipt") or "").strip() or None
            )
            freshness_checked_receipt = (
                str(metadata.get("freshness_checked_receipt") or "").strip() or None
            )
            blocked_or_gated_work = (
                metadata.get("blocked_or_gated_work")
                if isinstance(metadata.get("blocked_or_gated_work"), list)
                else []
            )
            blocked_item_count = len(blocked_or_gated_work)
            next_package_ladder = (
                metadata.get("next_package_ladder")
                if isinstance(metadata.get("next_package_ladder"), list)
                else []
            )
            owner_truth_surface_count = int(health_item.get("owner_truth_surface_count") or 0)
            verification_adoption_surface_count = int(
                health_item.get("verification_adoption_surface_count") or 0
            )
            if next_package_ladder and isinstance(next_package_ladder[0], dict):
                first_next_package = next_package_ladder[0]
                next_package = {
                    "package": str(first_next_package.get("package") or "").strip(),
                    "mode": str(first_next_package.get("mode") or "").strip(),
                    "reason": str(first_next_package.get("reason") or "").strip(),
                }

            if manifest_health_status == "ok":
                if current_checkpoint_receipt and freshness_checked_receipt and next_package:
                    restart_status = "restart_ready"
                else:
                    restart_status = "restart_partial"
            elif manifest_health_status == "warning":
                restart_status = "manifest_warning"
            else:
                restart_status = "manifest_error"

        items.append(
            {
                "marker": marker,
                "percent": percent,
                "section": section,
                "group": group,
                "eligibility": "eligible_open_marker",
                "restart_status": restart_status,
                "manifest_id": manifest_id,
                "manifest_path": manifest_path,
                "manifest_health_status": manifest_health_status,
                "current_checkpoint_receipt": current_checkpoint_receipt,
                "freshness_checked_receipt": freshness_checked_receipt,
                "next_package": next_package,
                "blocked_item_count": blocked_item_count,
                "owner_truth_surface_count": owner_truth_surface_count,
                "verification_adoption_surface_count": verification_adoption_surface_count,
            }
        )

    counts = Counter(str(item.get("restart_status") or "unknown") for item in items)
    eligible_count = sum(1 for item in items if item.get("eligibility") == "eligible_open_marker")
    ready_count = counts.get("restart_ready", 0)
    status = "ok"
    if counts.get("missing", 0) > 0 or counts.get("manifest_error", 0) > 0:
        status = "error"
    elif counts.get("manifest_warning", 0) > 0 or counts.get("restart_partial", 0) > 0:
        status = "warning"

    return {
        "status": status,
        "item_count": len(items),
        "eligible_open_marker_count": eligible_count,
        "restart_ready_count": ready_count,
        "partial_count": counts.get("restart_partial", 0),
        "missing_count": counts.get("missing", 0),
        "warning_count": counts.get("manifest_warning", 0),
        "error_count": counts.get("manifest_error", 0),
        "excluded_zero_count": counts.get("not_required", 0),
        "restart_ready_percent": 0 if eligible_count == 0 else round((ready_count / eligible_count) * 100, 2),
        "items": items,
        "marker_table_ref": "docs/atlas-book/02-lanes-and-markers.md",
        "manifest_glob": INITIATIVE_CONTINUITY_MANIFEST_GLOB,
        "coverage_slice": "continuity_open_marker_manifest_coverage",
        "health_slice": "continuity_initiative_manifest_health",
    }


def build_maintained_manifest_restart_index(*, root: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    bundles = _load_initiative_manifest_bundles(root=base_root)
    items: list[dict[str, Any]] = []
    for bundle in bundles:
        health_item = bundle.get("health") if isinstance(bundle.get("health"), dict) else {}
        payload = bundle.get("payload") if isinstance(bundle.get("payload"), dict) else {}
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        manifest_id = str(health_item.get("manifest_id") or "").strip() or None
        manifest_path = str(health_item.get("path") or "").strip() or None
        manifest_health_status = str(health_item.get("status") or "").strip()
        current_checkpoint_receipt = str(metadata.get("current_checkpoint_receipt") or "").strip() or None
        freshness_checked_receipt = str(metadata.get("freshness_checked_receipt") or "").strip() or None
        marker_posture = health_item.get("marker_posture") if isinstance(health_item.get("marker_posture"), list) else []
        marker_names = [
            str(item.get("marker") or "").strip()
            for item in marker_posture
            if isinstance(item, dict) and str(item.get("marker") or "").strip()
        ]
        next_package_ladder = metadata.get("next_package_ladder") if isinstance(metadata.get("next_package_ladder"), list) else []
        next_package: dict[str, Any] | None = None
        if next_package_ladder and isinstance(next_package_ladder[0], dict):
            first_next_package = next_package_ladder[0]
            next_package = {
                "package": str(first_next_package.get("package") or "").strip(),
                "mode": str(first_next_package.get("mode") or "").strip(),
                "reason": str(first_next_package.get("reason") or "").strip(),
            }
        blocked_or_gated_work = metadata.get("blocked_or_gated_work") if isinstance(metadata.get("blocked_or_gated_work"), list) else []
        blocked_item_count = len(blocked_or_gated_work)
        owner_truth_surface_count = int(health_item.get("owner_truth_surface_count") or 0)
        verification_adoption_surface_count = int(health_item.get("verification_adoption_surface_count") or 0)
        manifest_status = str(payload.get("status") or "").strip() or None

        restart_status = "missing"
        if manifest_health_status == "ok":
            if current_checkpoint_receipt and freshness_checked_receipt and next_package:
                restart_status = "restart_ready"
            else:
                restart_status = "restart_partial"
        elif manifest_health_status == "warning":
            restart_status = "manifest_warning"
        elif manifest_health_status:
            restart_status = "manifest_error"

        items.append(
            {
                "manifest_id": manifest_id,
                "manifest_path": manifest_path,
                "manifest_status": manifest_status,
                "manifest_health_status": manifest_health_status,
                "marker_names": marker_names,
                "current_checkpoint_receipt": current_checkpoint_receipt,
                "freshness_checked_receipt": freshness_checked_receipt,
                "next_package": next_package,
                "blocked_item_count": blocked_item_count,
                "owner_truth_surface_count": owner_truth_surface_count,
                "verification_adoption_surface_count": verification_adoption_surface_count,
                "restart_status": restart_status,
            }
        )

    counts = Counter(str(item.get("restart_status") or "unknown") for item in items)
    ready_count = counts.get("restart_ready", 0)
    status = "ok"
    if counts.get("missing", 0) > 0 or counts.get("manifest_error", 0) > 0:
        status = "error"
    elif counts.get("manifest_warning", 0) > 0 or counts.get("restart_partial", 0) > 0:
        status = "warning"

    return {
        "status": status,
        "item_count": len(items),
        "maintained_manifest_count": len(items),
        "restart_ready_count": ready_count,
        "partial_count": counts.get("restart_partial", 0),
        "missing_count": counts.get("missing", 0),
        "warning_count": counts.get("manifest_warning", 0),
        "error_count": counts.get("manifest_error", 0),
        "restart_ready_percent": 0 if len(items) == 0 else round((ready_count / len(items)) * 100, 2),
        "items": items,
        "manifest_glob": INITIATIVE_CONTINUITY_MANIFEST_GLOB,
        "health_slice": "continuity_initiative_manifest_health",
    }


def build_continuity_status_slices(*, root: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    manifest = build_continuity_source_manifest(root=base_root)
    historical_query_coverage = build_historical_query_coverage(root=base_root)
    initiative_manifest_health = build_initiative_continuity_manifest_health(root=base_root)
    open_marker_manifest_coverage = build_open_marker_manifest_coverage(root=base_root)
    open_marker_restart_index = build_open_marker_restart_index(root=base_root)
    maintained_manifest_restart_index = build_maintained_manifest_restart_index(root=base_root)
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
            "superseded_by": item.get("superseded_by", []),
            "promotion_targets": item.get("promotion_targets", []),
            "content_class": item.get("content_class"),
            "source_summary": item.get("source_summary"),
        }
        for item in sources
        if isinstance(item, dict)
        and bool(item.get("promotion_candidate"))
        and str(item.get("status") or "") not in {"promoted", "superseded"}
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
        "superseded_count": status_counts.get("superseded", 0),
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
        "initiative_manifest_status": initiative_manifest_health.get("status"),
        "initiative_manifest_count": initiative_manifest_health.get("manifest_count"),
        "initiative_manifest_warning_count": initiative_manifest_health.get("warning_count"),
        "initiative_manifest_error_count": initiative_manifest_health.get("error_count"),
        "open_marker_manifest_coverage_status": open_marker_manifest_coverage.get("status"),
        "open_marker_manifest_coverage_percent": open_marker_manifest_coverage.get("coverage_percent"),
        "eligible_open_marker_count": open_marker_manifest_coverage.get("eligible_open_marker_count"),
        "open_marker_restart_index_status": open_marker_restart_index.get("status"),
        "open_marker_restart_ready_percent": open_marker_restart_index.get("restart_ready_percent"),
        "open_marker_restart_ready_count": open_marker_restart_index.get("restart_ready_count"),
        "maintained_manifest_restart_index_status": maintained_manifest_restart_index.get("status"),
        "maintained_manifest_restart_ready_percent": maintained_manifest_restart_index.get("restart_ready_percent"),
        "maintained_manifest_restart_ready_count": maintained_manifest_restart_index.get("restart_ready_count"),
        "maintained_manifest_count": maintained_manifest_restart_index.get("maintained_manifest_count"),
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
            "superseded_count": status_counts.get("superseded", 0),
            "raw_evidence_count": content_counts.get("raw_evidence", 0),
            "structured_artifact_count": content_counts.get("structured_artifact", 0),
            "residue_count": content_counts.get("residue", 0),
            "historical_query_status": historical_query_coverage.get("status"),
            "historical_query_slice": "continuity_historical_query_coverage",
        },
        "continuity_historical_query_coverage": historical_query_coverage,
        "continuity_initiative_manifest_health": initiative_manifest_health,
        "continuity_open_marker_manifest_coverage": open_marker_manifest_coverage,
        "continuity_open_marker_restart_index": open_marker_restart_index,
        "continuity_maintained_manifest_restart_index": maintained_manifest_restart_index,
        "continuity_coverage": coverage | {"items": []},
    }
    return manifest, slices

