from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ops._atlas import atlas_root

MANIFEST_SCHEMA_VERSION = "atlas.continuity.source.manifest.v1"
CONTINUITY_MANIFEST_PATH = "data/imports/knowledge/continuity/harvest-manifest.json"
PLAYBOOK_INITIATIVE_REF = "initiative-playbook-convergence-and-continuity"
PLAYBOOK_PLAN_REF = "wave-9b-playbook-convergence-and-continuity"


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
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_path": source_path,
        "path_kind": path_kind,
        "lane": lane,
        "artifact_type": _artifact_type(source_path, path_kind=path_kind),
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


def build_continuity_status_slices(*, root: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    base_root = (root or atlas_root()).resolve()
    manifest = build_continuity_source_manifest(root=base_root)
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
        },
        "continuity_coverage": coverage | {"items": []},
    }
    return manifest, slices
