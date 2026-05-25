from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ops._atlas import atlas_relative, atlas_root, normalize_slashes

WORKFLOW_PROFILE_CONTRACT_VERSION = "atlas.cortex.workflow-profile.v1"


def default_workflow_profile_markdown_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "docs" / "memory" / "profiles" / "zachariah_workflow_profile.md"


def default_workflow_profile_metadata_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "docs" / "memory" / "profiles" / "zachariah_workflow_profile.json"


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def _require_file(path: Path, *, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} not found: {normalize_slashes(str(resolved))}")
    return resolved


def _ordered_unique_strings(values: list[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"^## (.+)$", markdown, re.MULTILINE))
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[title] = markdown[start:end].strip()
    return sections


def _extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return _ordered_unique_strings(bullets)


def _extract_numbered_items(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if match:
            items.append(match.group(1).strip())
    return _ordered_unique_strings(items)


def _paragraph_after(label: str, text: str) -> str:
    pattern = rf"{re.escape(label)}\s*\n(.*?)(?:\n[A-Z][^:\n]*:|\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return ""
    return " ".join(match.group(1).strip().split())


def _line_after(label: str, text: str) -> str:
    match = re.search(rf"^{re.escape(label)}\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def build_workflow_profile_payload(
    *,
    root: Path | None = None,
    markdown_path: Path | None = None,
    metadata_path: Path | None = None,
) -> dict[str, Any]:
    base = (root or atlas_root()).resolve()
    fallback_root = atlas_root().resolve()
    markdown_candidate = (markdown_path or default_workflow_profile_markdown_path(base)).resolve()
    metadata_candidate = (metadata_path or default_workflow_profile_metadata_path(base)).resolve()
    refs_root = base
    if not markdown_candidate.exists() and base != fallback_root:
        markdown_candidate = default_workflow_profile_markdown_path(fallback_root).resolve()
        refs_root = fallback_root
    if not metadata_candidate.exists() and base != fallback_root:
        metadata_candidate = default_workflow_profile_metadata_path(fallback_root).resolve()
        refs_root = fallback_root

    resolved_markdown = _require_file(
        markdown_candidate,
        label="Workflow profile markdown",
    )
    resolved_metadata = _require_file(
        metadata_candidate,
        label="Workflow profile metadata",
    )

    metadata = _read_json_object(resolved_metadata)
    markdown = resolved_markdown.read_text(encoding="utf-8")
    sections = _sections(markdown)

    response_style = sections.get("Response style", "")
    implementation_style = sections.get("Implementation style", "")
    reasoning_depth = sections.get("Reasoning depth routing", "")
    cortex_plan = sections.get("Cortex long-term plan", "")
    canonical_memory = sections.get("Canonical memory architecture rule", "")
    playbook_context = sections.get("Playbook project context", "")

    preferred_style_text, _, helping_text = response_style.partition("When helping:")
    implementation_prompt_text, _, implementation_worker_text = implementation_style.partition(
        "When working on Playbook or repository development and speed matters, default to a parallel Codex worker approach:"
    )

    return {
        "contract_version": WORKFLOW_PROFILE_CONTRACT_VERSION,
        "profile_id": str(metadata.get("id", "")).strip(),
        "title": str(metadata.get("title", "")).strip(),
        "type": str(metadata.get("type", "")).strip(),
        "owner": str(metadata.get("owner", "")).strip(),
        "status": str(metadata.get("status", "")).strip(),
        "canonical": bool(metadata.get("canonical")),
        "last_updated": str(metadata.get("last_updated", "")).strip(),
        "source": str(metadata.get("source", "")).strip(),
        "tags": _ordered_unique_strings(metadata.get("tags", []) if isinstance(metadata.get("tags"), list) else []),
        "summary": str(metadata.get("summary", "")).strip(),
        "canonical_refs": {
            "markdown": atlas_relative(resolved_markdown, root=refs_root),
            "metadata": atlas_relative(resolved_metadata, root=refs_root),
        },
        "response_contract": {
            "status_block_labels": ["Done", "Now", "Next"],
            "include_repo_health_check": "include a brief health check" in response_style,
            "include_no_repo_context_note": "If no repo context is loaded" in response_style,
            "recommended_execution_path_footer": "Recommended execution path" in reasoning_depth,
        },
        "style_preferences": {
            "preferred_style": _extract_bullets(preferred_style_text),
            "when_helping": _extract_bullets(helping_text),
        },
        "reasoning_routes": _extract_bullets(reasoning_depth),
        "implementation_preferences": {
            "codex_prompt_fields": _extract_bullets(implementation_prompt_text),
            "parallel_worker_defaults": _extract_bullets(implementation_worker_text),
        },
        "cortex_roadmap": {
            "priority_order": _extract_numbered_items(cortex_plan),
            "historical_context_ingestion": _extract_bullets(cortex_plan),
        },
        "playbook_context": {
            "main_repo": _line_after("Main Playbook repo:", playbook_context),
            "demo_repo": _line_after("Demo repo:", playbook_context),
            "external_pilot_repo": _line_after("External pilot target repo:", playbook_context),
            "roadmap_ref": "docs/PLAYBOOK_PRODUCT_ROADMAP.md",
        },
        "canonical_memory_rules": {
            "rule": _paragraph_after("Rule:", canonical_memory),
            "pattern": _paragraph_after("Pattern:", canonical_memory),
            "failure_mode": _paragraph_after("Failure Mode:", canonical_memory),
        },
    }
