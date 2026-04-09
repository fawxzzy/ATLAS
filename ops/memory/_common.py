from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_repo_registry, load_stack_config, normalize_slashes, path_is_within

DOC_SKIP_DIRS = {
    ".git",
    ".codex",
    "_archive",
    "archive",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "runtime",
    "tmp",
    "secrets",
}
MEMORY_SCHEMA_VERSION = "atlas.memory.artifact.v1"
CATALOG_NAME = "memory-catalog.latest.json"
RETENTION_RULES = {
    "preview_days": 7,
    "scratch_days": 3,
    "event_receipt_days": 14,
}


@dataclass(frozen=True)
class SourceDocument:
    path: Path
    relative_path: str
    kind: str
    repo_id: str | None


def slugify(value: str) -> str:
    lowered = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "artifact"


def resolve_atlas_path(candidate: str | Path) -> Path:
    path = Path(candidate)
    return path.resolve() if path.is_absolute() else (atlas_root() / path).resolve()


def clean_text(value: str) -> str:
    text = value.strip()
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^\s*[-*+]\s+", "", text)
    text = re.sub(r"^\s*\d+\.\s+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def markdown_title(lines: list[str], fallback: str) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return clean_text(stripped[2:])
    return fallback


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in DOC_SKIP_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            candidate = current / filename
            if candidate.suffix.lower() == ".md":
                files.append(candidate)
    return sorted(files)


def infer_doc_kind(path: Path, registry: dict[str, Any]) -> tuple[str | None, str | None]:
    rel = atlas_relative(path)
    if rel.startswith("docs/knowledge/"):
        return "knowledge_doc", None
    if rel.startswith("docs/playbooks/"):
        return "playbook_doc", None
    if rel.startswith("docs/"):
        return "stack_doc", None
    name = path.name.lower()
    for repo_id, entry in registry.items():
        if path_is_within(path, entry.root) and "audit" in name:
            return "repo_audit_doc", repo_id
    return None, None


def discover_memory_sources(selected: list[str] | None = None) -> list[SourceDocument]:
    root = atlas_root()
    registry = load_repo_registry(load_stack_config(root / "stack.yaml"), root=root)
    candidates: list[Path] = []

    if selected:
        for raw in selected:
            candidate = resolve_atlas_path(raw)
            if candidate.is_dir():
                candidates.extend(iter_markdown_files(candidate))
            elif candidate.suffix.lower() == ".md" and candidate.exists():
                candidates.append(candidate)
        result: list[SourceDocument] = []
        seen: set[Path] = set()
        for path in sorted(candidates):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            kind, repo_id = infer_doc_kind(resolved, registry)
            if kind is None:
                continue
            result.append(SourceDocument(resolved, atlas_relative(resolved), kind, repo_id))
        return result

    candidates.extend(iter_markdown_files(root / "docs"))
    for entry in registry.values():
        if entry.status not in {"active", "incubating", "unmanaged"}:
            continue
        docs_root = entry.root / "docs"
        if not docs_root.exists():
            continue
        for candidate in iter_markdown_files(docs_root):
            if "audit" not in candidate.name.lower():
                continue
            candidates.append(candidate)

    result: list[SourceDocument] = []
    seen = set()
    for path in sorted(candidates):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        kind, repo_id = infer_doc_kind(resolved, registry)
        if kind is None:
            continue
        result.append(SourceDocument(resolved, atlas_relative(resolved), kind, repo_id))
    return result


def build_memory_artifact(source: SourceDocument) -> dict[str, Any]:
    lines = source.path.read_text(encoding="utf-8", errors="replace").splitlines()
    title = markdown_title(lines, source.path.stem.replace("-", " ").replace("_", " "))

    section_index: list[dict[str, Any]] = []
    key_points: list[dict[str, Any]] = []
    overview = ""
    in_code_block = False
    seen_points: set[str] = set()

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped:
            continue
        if stripped.startswith("#"):
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            section_index.append(
                {
                    "heading": clean_text(stripped.lstrip("#").strip()),
                    "level": heading_level,
                    "line": line_number,
                }
            )
            continue

        cleaned = clean_text(stripped)
        if not cleaned:
            continue
        if not overview and len(cleaned) >= 20:
            overview = cleaned
        normalized = cleaned.lower()
        if normalized in seen_points:
            continue
        if len(cleaned) < 20 or len(cleaned) > 320:
            continue
        seen_points.add(normalized)
        key_points.append({"text": cleaned, "line": line_number})
        if len(key_points) >= 12:
            break

    artifact_id = slugify(source.relative_path.replace("/", "--"))
    return {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "artifact_id": artifact_id,
        "source": {
            "path": source.relative_path,
            "kind": source.kind,
            "repo_id": source.repo_id,
            "title": title,
        },
        "memory": {
            "overview": overview or title,
            "section_index": section_index,
            "key_points": key_points,
        },
        "provenance": {
            "source_file": source.relative_path,
            "line_count": len(lines),
        },
    }


def artifact_output_path(output_dir: Path, artifact: dict[str, Any]) -> Path:
    return output_dir / f"{artifact['artifact_id']}.json"


def build_memory_catalog(artifacts: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": "atlas.memory.catalog.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "output_dir": atlas_relative(output_dir),
        "artifact_count": len(artifacts),
        "artifacts": [
            {
                "artifact_id": artifact["artifact_id"],
                "artifact_file": atlas_relative(artifact_output_path(output_dir, artifact)),
                "source_path": artifact["source"]["path"],
                "source_kind": artifact["source"]["kind"],
                "repo_id": artifact["source"]["repo_id"],
                "overview": artifact["memory"]["overview"],
            }
            for artifact in artifacts
        ],
    }


def archive_destination(archive_root: Path, source_path: Path) -> Path:
    relative = source_path.resolve().relative_to(atlas_root())
    return archive_root / relative


def is_latest_receipt(path: Path) -> bool:
    return path.name.lower() == "latest.json"


def build_retention_plan(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    root = atlas_root()
    preview_cutoff = now - timedelta(days=RETENTION_RULES["preview_days"])
    scratch_cutoff = now - timedelta(days=RETENTION_RULES["scratch_days"])
    receipt_cutoff = now - timedelta(days=RETENTION_RULES["event_receipt_days"])
    archive_root = root / "runtime" / "receipts" / "retention-archive" / now.strftime("%Y%m%dT%H%M%SZ")

    kept: list[dict[str, Any]] = []
    compacted: list[dict[str, Any]] = []
    archived: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for candidate in sorted((root / "tmp" / "previews").rglob("*")):
        if not candidate.is_file() or candidate.name == ".gitkeep":
            continue
        modified_at = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
        if modified_at < preview_cutoff:
            compacted.append(
                {
                    "operation": "delete",
                    "path": atlas_relative(candidate),
                    "reason": "stale_preview",
                    "modified_at": modified_at.isoformat(),
                }
            )
        else:
            kept.append({"path": atlas_relative(candidate), "reason": "recent_preview"})

    for candidate in sorted((root / "tmp" / "scratch").rglob("*")):
        if not candidate.is_file():
            continue
        modified_at = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
        if modified_at < scratch_cutoff:
            compacted.append(
                {
                    "operation": "delete",
                    "path": atlas_relative(candidate),
                    "reason": "expired_temp_file",
                    "modified_at": modified_at.isoformat(),
                }
            )
        else:
            kept.append({"path": atlas_relative(candidate), "reason": "recent_temp_file"})

    events_root = root / "runtime" / "receipts" / "events"
    for category in sorted(events_root.iterdir() if events_root.exists() else []):
        if not category.is_dir():
            continue
        latest_path = category / "latest.json"
        if not latest_path.exists():
            skipped.append({"path": atlas_relative(category), "reason": "no_latest_receipt"})
            continue
        for candidate in sorted(category.glob("*.json")):
            if is_latest_receipt(candidate):
                kept.append({"path": atlas_relative(candidate), "reason": "latest_receipt"})
                continue
            modified_at = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
            if modified_at < receipt_cutoff:
                archive_path = archive_destination(archive_root, candidate)
                record = {
                    "operation": "archive",
                    "path": atlas_relative(candidate),
                    "archive_path": atlas_relative(archive_path),
                    "reason": "latest_receipt_supersedes_timestamped_copy",
                    "modified_at": modified_at.isoformat(),
                }
                compacted.append(record)
                archived.append(record)
            else:
                kept.append({"path": atlas_relative(candidate), "reason": "recent_receipt"})

    memory_root = root / "runtime" / "cortex" / "catalog" / "memory"
    memory_by_source: dict[str, list[Path]] = {}
    for candidate in sorted(memory_root.glob("*.json")) if memory_root.exists() else []:
        if candidate.name == CATALOG_NAME:
            kept.append({"path": atlas_relative(candidate), "reason": "memory_catalog"})
            continue
        try:
            payload = load_json(candidate)
        except Exception:
            skipped.append({"path": atlas_relative(candidate), "reason": "unreadable_memory_artifact"})
            continue
        source_path = payload.get("source", {}).get("path")
        if not isinstance(source_path, str):
            skipped.append({"path": atlas_relative(candidate), "reason": "missing_memory_source_path"})
            continue
        resolved_source = root / Path(source_path)
        if not resolved_source.exists():
            archive_path = archive_destination(archive_root, candidate)
            record = {
                "operation": "archive",
                "path": atlas_relative(candidate),
                "archive_path": atlas_relative(archive_path),
                "reason": "orphaned_memory_artifact",
            }
            compacted.append(record)
            archived.append(record)
            continue
        memory_by_source.setdefault(source_path, []).append(candidate)

    for source_path, items in memory_by_source.items():
        if len(items) == 1:
            kept.append({"path": atlas_relative(items[0]), "reason": f"latest_memory_for:{source_path}"})
            continue
        ranked = sorted(items, key=lambda path: path.stat().st_mtime, reverse=True)
        kept.append({"path": atlas_relative(ranked[0]), "reason": f"latest_memory_for:{source_path}"})
        for candidate in ranked[1:]:
            archive_path = archive_destination(archive_root, candidate)
            record = {
                "operation": "archive",
                "path": atlas_relative(candidate),
                "archive_path": atlas_relative(archive_path),
                "reason": "duplicate_memory_artifact",
            }
            compacted.append(record)
            archived.append(record)

    never_delete = [
        "docs/**",
        "repos/**",
        "data/imports/**",
        "packages/**",
        "runtime/receipts/handoffs/**",
    ]
    for item in never_delete:
        skipped.append({"path": item, "reason": "never_auto_delete_policy"})

    return {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "mode": "preview",
        "policy": RETENTION_RULES,
        "archive_root": atlas_relative(archive_root),
        "summary": {
            "kept": len(kept),
            "compacted": len(compacted),
            "archived": len(archived),
            "skipped": len(skipped),
        },
        "kept": kept,
        "compacted": compacted,
        "archived": archived,
        "skipped": skipped,
    }


def apply_retention_plan(report: dict[str, Any]) -> dict[str, Any]:
    archive_root = resolve_atlas_path(report["archive_root"])
    performed: list[dict[str, Any]] = []
    for record in report["compacted"]:
        source_path = resolve_atlas_path(record["path"])
        operation = record["operation"]
        if not source_path.exists():
            continue
        if operation == "delete":
            source_path.unlink()
            performed.append({**record, "performed": True})
        elif operation == "archive":
            target_path = resolve_atlas_path(record["archive_path"])
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target_path))
            performed.append({**record, "performed": True})
    report["mode"] = "execute"
    report["performed"] = performed
    report["summary"]["performed"] = len(performed)
    if performed:
        archive_root.mkdir(parents=True, exist_ok=True)
    return report


def write_retention_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "memory-retention.latest.json"
    md_path = output_dir / "memory-retention.latest.md"
    write_json(json_path, report)
    lines = [
        "# Memory Retention Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Mode: `{report['mode']}`",
        f"- Archive root: `{report['archive_root']}`",
        "",
        "## Summary",
        "",
        f"- Kept: {report['summary']['kept']}",
        f"- Compacted: {report['summary']['compacted']}",
        f"- Archived: {report['summary']['archived']}",
        f"- Skipped: {report['summary']['skipped']}",
        "",
    ]
    for label in ["compacted", "archived", "kept", "skipped"]:
        entries = report.get(label) or []
        if not entries:
            continue
        lines.extend([f"## {label.title()}", ""])
        for entry in entries:
            summary = f"- `{entry['path']}`: {entry['reason']}"
            if entry.get("archive_path"):
                summary += f" -> `{entry['archive_path']}`"
            lines.append(summary)
        lines.append("")
    md_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return json_path, md_path
