from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PIPELINE_VERSION = "atlas.knowledge.pipeline.v2"
RECEIPT_VERSION = "atlas.knowledge.receipt.v1"
PROMOTION_SCHEMA_VERSION = "atlas.knowledge.promotion.v1"

IMPORT_STATUSES = {
    "imported",
    "evaluated",
    "normalized",
    "indexed_metadata_only",
    "rejected",
}
PRIVACY_FLAGS = {"private", "mixed", "shareable"}
SAFE_FOR_INDEXING = {"pending_review", "no", "restricted", "yes"}
INDEXING_PROFILES = {"metadata_only", "derived_only", "full_text"}
PROMOTION_STATUSES = {"not_promoted", "draft", "promoted"}
RETENTION_CLASSES = {"ephemeral", "operational", "governed-audit", "regulated"}
PROMOTION_REQUIRED_SECTIONS = [
    "Derived Summary",
    "Topic Map",
    "Evidence References",
    "Exclusions And Redactions",
]
TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".cmd",
    ".conf",
    ".cjs",
    ".csv",
    ".ini",
    ".ipynb",
    ".json",
    ".js",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".rst",
    ".sh",
    ".tex",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
EXECUTABLE_EXTENSIONS = {
    ".app",
    ".bat",
    ".bin",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".jar",
    ".js",
    ".msi",
    ".ps1",
    ".py",
    ".rb",
    ".sh",
}
PRIVATE_PATTERNS = [
    re.compile(r"\b(?:student|employee|member)[ _-]?id\b", re.IGNORECASE),
    re.compile(r"\b(?:grade|gpa|transcript|attendance|dob|date of birth)\b", re.IGNORECASE),
    re.compile(r"\b(?:phone|email|address|passport|license number|ssn)\b", re.IGNORECASE),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
]
SECRET_PATTERNS = [
    re.compile(r"\bapi[_ -]?key\b|\baccess[_ -]?token\b|\bsecret\b|\bpassword\b", re.IGNORECASE),
    re.compile(r"\baws_secret_access_key\b|\baws_access_key_id\b", re.IGNORECASE),
    re.compile(r"\bBEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY\b", re.IGNORECASE),
    re.compile(r"\b(?:sk|rk|ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
]
COPYRIGHT_PATTERNS = [
    re.compile(r"\ball rights reserved\b", re.IGNORECASE),
    re.compile(r"\bcopyright\b", re.IGNORECASE),
    re.compile(r"\bdo not redistribute\b|\blicensed to\b", re.IGNORECASE),
    re.compile(r"\b(?:course pack|lecture slides|syllabus|assignment|instructor)\b", re.IGNORECASE),
    re.compile(r"\b(?:coursera|udemy|pluralsight|linkedin learning|edx)\b", re.IGNORECASE),
]
CATALOG_BEGIN = "<!-- KNOWLEDGE-CATALOG:BEGIN -->"
CATALOG_END = "<!-- KNOWLEDGE-CATALOG:END -->"


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def relative_to_atlas(path: Path) -> str:
    root = atlas_root()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(
            f"Input must already be staged under ATLAS so paths stay ATLAS-relative: {resolved}"
        )
    rel = resolved.relative_to(root)
    return "." if not rel.parts else rel.as_posix()


def resolve_atlas_path(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (atlas_root() / path).resolve()


def ensure_within(parent: Path, candidate: Path) -> None:
    parent_resolved = parent.resolve()
    candidate_resolved = candidate.resolve()
    if not candidate_resolved.is_relative_to(parent_resolved):
        raise ValueError(f"Refusing path outside allowed root: {candidate_resolved}")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or "archive"


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def deep_merge(existing: Any, updates: Any) -> Any:
    if not isinstance(existing, dict) or not isinstance(updates, dict):
        return updates
    merged = dict(existing)
    for key, value in updates.items():
        if key in merged:
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def source_dir(source_name: str) -> Path:
    return atlas_root() / "data" / "imports" / "knowledge" / slugify(source_name)


def archive_dir(source_name: str, slug: str) -> Path:
    return source_dir(source_name) / slugify(slug)


def raw_dir(path: Path) -> Path:
    return path / "raw"


def extracted_dir(path: Path) -> Path:
    return path / "extracted"


def manifest_path(path: Path) -> Path:
    return path / "IMPORT-MANIFEST.json"


def evaluation_path(path: Path) -> Path:
    return path / "EVALUATION.json"


def promotions_dir() -> Path:
    return atlas_root() / "docs" / "knowledge" / "promotions"


def promotion_doc_path(archive_id: str) -> Path:
    return promotions_dir() / f"{archive_id}.md"


def normalized_path(source_name: str, slug: str) -> Path:
    return (
        atlas_root()
        / "runtime"
        / "cortex"
        / "catalog"
        / "knowledge"
        / f"{slugify(source_name)}--{slugify(slug)}.json"
    )


def catalog_doc_path() -> Path:
    return atlas_root() / "docs" / "knowledge" / "KNOWLEDGE-CATALOG.md"


def knowledge_receipts_root() -> Path:
    return atlas_root() / "runtime" / "receipts" / "knowledge"


def receipt_dir(archive_id: str) -> Path:
    return knowledge_receipts_root() / archive_id


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def list_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in list_files(root):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_checksum(path).encode("utf-8"))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def extract_zip_safely(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = destination / member.filename
            ensure_within(destination, member_path)
            if member.is_dir():
                member_path.mkdir(parents=True, exist_ok=True)
                continue
            member_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, member_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def copy_folder(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def build_raw_entries(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in list_files(root):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "checksum": file_checksum(path),
            }
        )
    return entries


def summarize_extension_counts(paths: list[Path]) -> dict[str, int]:
    counts = Counter(path.suffix.lower() or "<no_ext>" for path in paths)
    return {key: counts[key] for key in sorted(counts)}


def iter_text_files(paths: list[Path]) -> list[Path]:
    return [path for path in paths if path.suffix.lower() in TEXT_EXTENSIONS]


def read_text_limited(path: Path, max_chars: int = 4000) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def detect_executable_content(paths: list[Path]) -> tuple[bool, list[dict[str, str]]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        rel = relative_to_atlas(path)
        suffix = path.suffix.lower()
        if suffix in EXECUTABLE_EXTENSIONS:
            hits.append({"path": rel, "reason": f"extension:{suffix or '<no_ext>'}"})
            continue
        if suffix in TEXT_EXTENSIONS:
            text = read_text_limited(path, max_chars=200)
            if text.startswith("#!"):
                hits.append({"path": rel, "reason": "shebang"})
    return bool(hits), hits[:20]


def match_patterns(paths: list[Path], patterns: list[re.Pattern[str]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        rel = relative_to_atlas(path)
        haystacks = [path.name]
        if path.suffix.lower() in TEXT_EXTENSIONS:
            haystacks.append(read_text_limited(path))
        for pattern in patterns:
            for haystack in haystacks:
                matched = pattern.search(haystack)
                if matched:
                    hits.append({"path": rel, "match": matched.group(0)})
                    break
            else:
                continue
            break
    return hits[:20]


def classify_safe_for_indexing(privacy_flag: str, flags: dict[str, bool]) -> str:
    if flags["credentials_secrets_risk"]:
        return "no"
    if (
        privacy_flag != "shareable"
        or flags["personal_private_material"]
        or flags["copyrighted_courseware_risk"]
        or flags["executable_content"]
    ):
        return "restricted"
    return "yes"


def recommend_indexing_profile(
    *,
    privacy_flag: str,
    safe_for_indexing_status: str,
    flags: dict[str, bool],
) -> str:
    if safe_for_indexing_status == "yes" and privacy_flag == "shareable" and not any(flags.values()):
        return "full_text"
    return "metadata_only"


def promotion_allowed(flags: dict[str, bool]) -> bool:
    return not flags["credentials_secrets_risk"]


def quarantine_flags(flags: dict[str, bool]) -> list[str]:
    return ["credentials_secrets_risk"] if flags["credentials_secrets_risk"] else []


def quarantine_reason(flag_names: list[str]) -> str | None:
    if not flag_names:
        return None
    if flag_names == ["credentials_secrets_risk"]:
        return "Credential-like material was detected. Keep the archive quarantined to metadata-only handling until rotation and scrub are complete."
    return "Archive remains quarantined pending manual review."


def normalization_allowed(flags: dict[str, bool]) -> bool:
    return not flags["credentials_secrets_risk"]


def risk_summary(flags: dict[str, bool]) -> str:
    active = [name for name, enabled in flags.items() if enabled]
    return ", ".join(active) if active else "none"


def default_retention_class() -> str:
    return "operational"


def infer_promotion_status(archive_id: str, existing_manifest: dict[str, Any] | None = None) -> str:
    if promotion_doc_path(archive_id).exists():
        return existing_manifest.get("promotion_status", "draft") if existing_manifest else "draft"
    if existing_manifest and existing_manifest.get("promotion_status") in PROMOTION_STATUSES:
        return str(existing_manifest["promotion_status"])
    return "not_promoted"


def build_manifest_artifact_digests(manifest: dict[str, Any], archive_path: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    raw_root = raw_dir(archive_path)
    if manifest.get("source_type") == "zip":
        raw_archive_rel = manifest.get("raw_archive_path")
        if isinstance(raw_archive_rel, str):
            raw_archive = resolve_atlas_path(Path(raw_archive_rel))
            if raw_archive.exists():
                digests["raw_archive"] = file_checksum(raw_archive)
        input_path = manifest.get("input_path")
        if isinstance(input_path, str):
            input_candidate = resolve_atlas_path(Path(input_path))
            if input_candidate.exists() and input_candidate.is_file():
                digests["input_source"] = file_checksum(input_candidate)
    else:
        if raw_root.exists():
            digests["raw_tree"] = tree_digest(raw_root)
        input_path = manifest.get("input_path")
        if isinstance(input_path, str):
            input_candidate = resolve_atlas_path(Path(input_path))
            if input_candidate.exists() and input_candidate.is_dir():
                digests["input_source"] = tree_digest(input_candidate)
    return digests


def extracted_snapshot_digest(archive_path: Path) -> str:
    extracted_root = extracted_dir(archive_path)
    return tree_digest(extracted_root) if extracted_root.exists() else "sha256:missing"


def update_manifest(archive_path: Path, updates: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    path = manifest_path(archive_path)
    existing = read_json(path) if path.exists() else {}
    merged = deep_merge(existing, updates)
    write_json(path, merged, dry_run)
    return merged


def update_evaluation(archive_path: Path, updates: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    path = evaluation_path(archive_path)
    existing = read_json(path) if path.exists() else {}
    merged = deep_merge(existing, updates)
    write_json(path, merged, dry_run)
    return merged


def update_runtime_catalog(
    archive_path: Path,
    *,
    source_name: str,
    slug: str,
    updates: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    path = normalized_path(source_name, slug)
    existing = read_json(path) if path.exists() else {}
    merged = deep_merge(existing, updates)
    write_json(path, merged, dry_run)
    return merged


def frontmatter_block(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Promotion document must start with a YAML front matter block.")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            metadata: dict[str, Any] = {}
            for raw in lines[1:index]:
                stripped = raw.strip()
                if not stripped:
                    continue
                key, sep, value = stripped.partition(":")
                if not sep:
                    raise ValueError(f"Invalid promotion front matter line: {raw}")
                metadata[key.strip()] = parse_scalar(value.strip())
            body = "\n".join(lines[index + 1 :]).strip() + "\n"
            return metadata, body
    raise ValueError("Promotion document front matter is missing its closing delimiter.")


def extract_section_map(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def render_frontmatter(metadata: dict[str, Any]) -> str:
    ordered_keys = [
        "schema_version",
        "archive_id",
        "promotion_status",
        "indexing_profile",
        "retention_class",
        "created_at",
        "updated_at",
    ]
    lines = ["---"]
    for key in ordered_keys:
        lines.append(f"{key}: {metadata[key]}")
    lines.append("---")
    return "\n".join(lines)


def clean_markdown_text(value: str) -> str:
    text = value.strip()
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip()


def build_promotion_document(
    *,
    archive_path: Path,
    archive_id: str,
    manifest: dict[str, Any],
    evaluation: dict[str, Any],
    indexing_profile: str,
    promotion_status: str,
    retention_class: str,
    existing_text: str | None,
) -> str:
    existing_metadata: dict[str, Any] = {}
    existing_sections: dict[str, str] = {}
    if existing_text:
        existing_metadata, existing_body = frontmatter_block(existing_text)
        existing_sections = extract_section_map(existing_body)

    created_at = str(existing_metadata.get("created_at", utc_now()))
    updated_at = utc_now()
    title = f"# Promotion: {archive_id}"
    summary_default = (
        f"Draft promotion created from evaluation metadata for `{archive_id}`. "
        "Replace this section with a human-authored derived summary before downstream derived indexing."
    )
    dominant_extensions = list(evaluation.get("summary", {}).get("extension_counts", {}).items())[:5]
    topic_lines = [
        f"- source: `{manifest['source_name']}`",
        f"- privacy flag: `{manifest['privacy_flag']}`",
        f"- file count: `{evaluation.get('summary', {}).get('file_count', 'unknown')}`",
        f"- safe_for_indexing: `{evaluation.get('safe_for_indexing', 'pending_review')}`",
    ]
    if dominant_extensions:
        rendered = ", ".join(f"{ext}={count}" for ext, count in dominant_extensions)
        topic_lines.append(f"- top extensions: `{rendered}`")
    evidence_lines = [
        f"- manifest: `{relative_to_atlas(manifest_path(archive_path))}`",
        f"- evaluation: `{relative_to_atlas(evaluation_path(archive_path))}`",
        f"- import lane: `{relative_to_atlas(archive_path)}`",
    ]
    if manifest.get("raw_archive_path"):
        evidence_lines.append(f"- raw archive: `{manifest['raw_archive_path']}`")
    exclusion_lines = []
    for name, enabled in evaluation.get("risk_flags", {}).items():
        if enabled:
            exclusion_lines.append(f"- `{name}` remains excluded from promotion-safe derived output.")
    if not exclusion_lines:
        exclusion_lines.append("- No additional redactions are recorded in this draft.")

    sections = {
        "Derived Summary": existing_sections.get("Derived Summary") or summary_default,
        "Topic Map": existing_sections.get("Topic Map") or "\n".join(topic_lines),
        "Evidence References": existing_sections.get("Evidence References") or "\n".join(evidence_lines),
        "Exclusions And Redactions": existing_sections.get("Exclusions And Redactions") or "\n".join(exclusion_lines),
    }
    metadata = {
        "schema_version": PROMOTION_SCHEMA_VERSION,
        "archive_id": archive_id,
        "promotion_status": promotion_status,
        "indexing_profile": indexing_profile,
        "retention_class": retention_class,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    body_lines = [title, ""]
    for section_name in PROMOTION_REQUIRED_SECTIONS:
        body_lines.append(f"## {section_name}")
        body_lines.append("")
        body_lines.append(sections[section_name].strip())
        body_lines.append("")
    return render_frontmatter(metadata) + "\n\n" + "\n".join(body_lines).strip() + "\n"


def read_promotion_doc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata, body = frontmatter_block(text)
    missing_keys = [
        key
        for key in [
            "schema_version",
            "archive_id",
            "promotion_status",
            "indexing_profile",
            "retention_class",
            "created_at",
            "updated_at",
        ]
        if key not in metadata
    ]
    if missing_keys:
        raise ValueError(f"Promotion document is missing required front matter keys: {', '.join(missing_keys)}")
    if metadata["schema_version"] != PROMOTION_SCHEMA_VERSION:
        raise ValueError(f"Promotion schema_version must be '{PROMOTION_SCHEMA_VERSION}'.")
    if metadata["promotion_status"] not in PROMOTION_STATUSES:
        raise ValueError("Promotion status is invalid.")
    if metadata["indexing_profile"] not in INDEXING_PROFILES:
        raise ValueError("Promotion indexing_profile is invalid.")
    if metadata["retention_class"] not in RETENTION_CLASSES:
        raise ValueError("Promotion retention_class is invalid.")
    sections = extract_section_map(body)
    missing_sections = [name for name in PROMOTION_REQUIRED_SECTIONS if not sections.get(name)]
    if missing_sections:
        raise ValueError(
            "Promotion document is missing required sections: " + ", ".join(missing_sections)
        )
    title = "Promotion"
    for line in body.splitlines():
        if line.startswith("# "):
            title = clean_markdown_text(line[2:])
            break
    return {
        "path": relative_to_atlas(path),
        "metadata": metadata,
        "sections": sections,
        "title": title,
        "digest": file_checksum(path),
    }


def build_promotion_summary(doc: dict[str, Any]) -> dict[str, Any]:
    sections = doc["sections"]
    evidence_refs = [line.strip() for line in sections["Evidence References"].splitlines() if line.strip()]
    topic_map = [line.strip() for line in sections["Topic Map"].splitlines() if line.strip()]
    return {
        "title": doc["title"],
        "path": doc["path"],
        "digest": doc["digest"],
        "schema_version": doc["metadata"]["schema_version"],
        "promotion_status": doc["metadata"]["promotion_status"],
        "indexing_profile": doc["metadata"]["indexing_profile"],
        "retention_class": doc["metadata"]["retention_class"],
        "derived_summary": clean_markdown_text(sections["Derived Summary"]),
        "topic_map": topic_map[:8],
        "evidence_references": evidence_refs[:8],
        "exclusions": clean_markdown_text(sections["Exclusions And Redactions"]),
    }


def current_validation_placeholder() -> dict[str, Any]:
    return {"status": "not_run", "findings": []}


def write_knowledge_receipt(
    *,
    archive_path: Path,
    action: str,
    validation_results: dict[str, Any] | None,
    dry_run: bool,
) -> dict[str, Any]:
    manifest = read_json(manifest_path(archive_path))
    archive_id = manifest["archive_id"]
    evaluation = read_json(evaluation_path(archive_path)) if evaluation_path(archive_path).exists() else None
    normalized_file = normalized_path(manifest["source_name"], manifest["slug"])
    normalized = read_json(normalized_file) if normalized_file.exists() else None
    promotion_file = promotion_doc_path(archive_id)
    promotion = read_promotion_doc(promotion_file) if promotion_file.exists() else None
    recorded_at = utc_now()
    timestamp = recorded_at.replace("-", "").replace(":", "").replace(".", "")
    receipt_folder = receipt_dir(archive_id)
    receipt_path_value = receipt_folder / f"{timestamp}-{action}.json"
    latest_path = receipt_folder / "latest.json"
    runtime_outputs = []
    if normalized is not None:
        runtime_outputs.append(relative_to_atlas(normalized_file))
    runtime_outputs.append(relative_to_atlas(catalog_doc_path()))
    receipt = {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": f"{archive_id}-{action}-{timestamp}",
        "recorded_at": recorded_at,
        "pipeline_version": PIPELINE_VERSION,
        "archive_id": archive_id,
        "action": action,
        "atlas_root": ".",
        "paths": {
            "manifest_path": relative_to_atlas(manifest_path(archive_path)),
            "evaluation_path": relative_to_atlas(evaluation_path(archive_path))
            if evaluation is not None
            else None,
            "promotion_doc_path": promotion["path"] if promotion is not None else None,
            "runtime_catalog_path": relative_to_atlas(normalized_file) if normalized is not None else None,
            "receipt_path": relative_to_atlas(receipt_path_value),
            "latest_path": relative_to_atlas(latest_path),
        },
        "inputs": {
            "artifact_digests": manifest.get("artifact_digests", {}),
            "extracted_snapshot_digest": manifest.get("extracted_snapshot_digest"),
        },
        "no_execute_guarantee": bool(manifest.get("no_execute_guarantee", True)),
        "evaluation": {
            "safe_for_indexing": evaluation.get("safe_for_indexing"),
            "indexing_profile": evaluation.get("indexing_profile"),
            "promotion_allowed": evaluation.get("promotion_allowed"),
            "quarantine_flags": evaluation.get("quarantine_flags"),
            "quarantine_reason": evaluation.get("quarantine_reason"),
        }
        if evaluation is not None
        else None,
        "promotion": {
            "path": promotion["path"],
            "digest": promotion["digest"],
            "promotion_status": promotion["metadata"]["promotion_status"],
            "indexing_profile": promotion["metadata"]["indexing_profile"],
        }
        if promotion is not None
        else None,
        "runtime_outputs": runtime_outputs,
        "validation_results": validation_results or current_validation_placeholder(),
    }
    if not dry_run:
        receipt_folder.mkdir(parents=True, exist_ok=True)
        receipt_path_value.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        latest_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def import_archive(
    *,
    input_path: Path,
    source_name: str,
    slug: str | None,
    privacy_flag: str,
    provenance_note: str | None,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    if privacy_flag not in PRIVACY_FLAGS:
        raise ValueError(f"Unsupported privacy flag: {privacy_flag}")
    input_path = resolve_atlas_path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {relative_to_atlas(input_path)}")
    input_path_rel = relative_to_atlas(input_path)
    archive_slug = slugify(slug or input_path.stem or input_path.name)
    knowledge_dir = archive_dir(source_name, archive_slug)
    detected_type = "zip" if input_path.is_file() and input_path.suffix.lower() == ".zip" else "folder"
    if detected_type not in {"zip", "folder"}:
        raise ValueError("Input must be a directory or a .zip file.")
    if knowledge_dir.exists() and not force:
        raise FileExistsError(
            f"Import destination already exists: {relative_to_atlas(knowledge_dir)}"
        )

    manifest: dict[str, Any] = {
        "archive_id": f"{slugify(source_name)}--{archive_slug}",
        "source_name": source_name,
        "slug": archive_slug,
        "source_type": detected_type,
        "imported_at": utc_now(),
        "input_path": input_path_rel,
        "original_filename": input_path.name,
        "privacy_flag": privacy_flag,
        "review_status": "imported",
        "safe_for_indexing": "pending_review",
        "indexing_profile": "metadata_only",
        "promotion_status": "not_promoted",
        "retention_class": default_retention_class(),
        "pipeline_version": PIPELINE_VERSION,
        "no_execute_guarantee": True,
        "paths": {
            "import_dir": relative_to_atlas(knowledge_dir),
            "raw_dir": relative_to_atlas(raw_dir(knowledge_dir)),
            "extracted_dir": relative_to_atlas(extracted_dir(knowledge_dir)),
        },
        "provenance": {
            "staged_under_atlas": True,
            "source_label": source_name,
            "original_filename": input_path.name,
        },
    }
    if provenance_note:
        manifest["provenance"]["note"] = provenance_note
    if detected_type == "zip":
        manifest["checksum"] = file_checksum(input_path)
        manifest["raw_archive_path"] = f"{relative_to_atlas(raw_dir(knowledge_dir))}/{input_path.name}"
    else:
        manifest["raw_reference_dir"] = relative_to_atlas(raw_dir(knowledge_dir))
        manifest["raw_entries"] = build_raw_entries(input_path)

    operations: list[str] = [f"prepare:{relative_to_atlas(knowledge_dir)}"]
    if detected_type == "zip":
        operations.append(f"copy:{relative_to_atlas(raw_dir(knowledge_dir) / input_path.name)}")
        operations.append(f"extract:{relative_to_atlas(extracted_dir(knowledge_dir))}")
    else:
        operations.append(f"copytree:{relative_to_atlas(raw_dir(knowledge_dir))}")
        operations.append(f"copytree:{relative_to_atlas(extracted_dir(knowledge_dir))}")
    operations.append(f"write:{relative_to_atlas(manifest_path(knowledge_dir))}")

    if not dry_run:
        if knowledge_dir.exists() and force:
            shutil.rmtree(knowledge_dir)
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        if detected_type == "zip":
            raw_dir(knowledge_dir).mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, raw_dir(knowledge_dir) / input_path.name)
            extract_zip_safely(input_path, extracted_dir(knowledge_dir))
        else:
            copy_folder(input_path, raw_dir(knowledge_dir))
            copy_folder(input_path, extracted_dir(knowledge_dir))
        manifest["artifact_digests"] = build_manifest_artifact_digests(manifest, knowledge_dir)
        manifest["extracted_snapshot_digest"] = extracted_snapshot_digest(knowledge_dir)
        write_json(manifest_path(knowledge_dir), manifest, dry_run=False)
        write_knowledge_receipt(
            archive_path=knowledge_dir,
            action="import",
            validation_results=None,
            dry_run=False,
        )
    else:
        manifest["artifact_digests"] = {}
        manifest["extracted_snapshot_digest"] = "sha256:dry-run"

    return {
        "ok": True,
        "dry_run": dry_run,
        "archive_id": manifest["archive_id"],
        "pipeline_version": PIPELINE_VERSION,
        "no_execute_guarantee": True,
        "import_dir": relative_to_atlas(knowledge_dir),
        "manifest": manifest,
        "planned_operations": operations,
    }


def evaluate_archive(*, archive_path: Path, dry_run: bool) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    review_dir = extracted_dir(archive_path)
    if not review_dir.exists():
        raise FileNotFoundError(f"Missing extracted directory: {relative_to_atlas(review_dir)}")
    manifest = read_json(manifest_path(archive_path))
    paths = list_files(review_dir)
    text_paths = iter_text_files(paths)
    private_hits = match_patterns(paths, PRIVATE_PATTERNS)
    secrets_hits = match_patterns(paths, SECRET_PATTERNS)
    copyright_hits = match_patterns(paths, COPYRIGHT_PATTERNS)
    executable_flag, executable_hits = detect_executable_content(paths)
    flags = {
        "personal_private_material": manifest["privacy_flag"] != "shareable" or bool(private_hits),
        "credentials_secrets_risk": bool(secrets_hits),
        "copyrighted_courseware_risk": bool(copyright_hits),
        "executable_content": executable_flag,
    }
    safe_for_indexing_status = classify_safe_for_indexing(manifest["privacy_flag"], flags)
    indexing_profile = recommend_indexing_profile(
        privacy_flag=manifest["privacy_flag"],
        safe_for_indexing_status=safe_for_indexing_status,
        flags=flags,
    )
    quarantine = quarantine_flags(flags)
    notes: list[str] = []
    if flags["personal_private_material"]:
        notes.append("Treat the archive as private or partially private.")
    if flags["credentials_secrets_risk"]:
        notes.append("Potential credentials or secret-bearing material were detected.")
    if flags["copyrighted_courseware_risk"]:
        notes.append("Courseware copyright signals were detected; retain metadata only.")
    if flags["executable_content"]:
        notes.append("Executable or script content exists and must remain non-executed.")
    if not notes:
        notes.append("Archive metadata is low-risk for cataloging based on the current scan.")

    generated = {
        "archive_id": manifest["archive_id"],
        "source_name": manifest["source_name"],
        "slug": manifest["slug"],
        "evaluated_at": utc_now(),
        "import_dir": relative_to_atlas(archive_path),
        "extracted_dir": relative_to_atlas(review_dir),
        "manifest_path": relative_to_atlas(manifest_path(archive_path)),
        "review_status": "evaluated",
        "privacy_flag": manifest["privacy_flag"],
        "safe_for_indexing": safe_for_indexing_status,
        "indexing_profile": indexing_profile,
        "promotion_allowed": promotion_allowed(flags),
        "quarantine_flags": quarantine,
        "quarantine_reason": quarantine_reason(quarantine),
        "normalization_allowed": normalization_allowed(flags),
        "retention_class": manifest.get("retention_class", default_retention_class()),
        "pipeline_version": PIPELINE_VERSION,
        "no_execute_guarantee": True,
        "summary": {
            "file_count": len(paths),
            "text_file_count": len(text_paths),
            "extension_counts": summarize_extension_counts(paths),
        },
        "risk_flags": flags,
        "risk_indicators": {
            "personal_private_material": private_hits,
            "credentials_secrets_risk": secrets_hits,
            "copyrighted_courseware_risk": copyright_hits,
            "executable_content": executable_hits,
        },
        "notes": " ".join(notes),
    }
    report = update_evaluation(archive_path, generated, dry_run)
    manifest_updates = {
        "review_status": "evaluated",
        "safe_for_indexing": safe_for_indexing_status,
        "indexing_profile": report["indexing_profile"],
        "promotion_status": infer_promotion_status(manifest["archive_id"], existing_manifest=manifest),
        "retention_class": manifest.get("retention_class", default_retention_class()),
        "pipeline_version": PIPELINE_VERSION,
        "artifact_digests": build_manifest_artifact_digests(manifest, archive_path),
        "extracted_snapshot_digest": extracted_snapshot_digest(archive_path),
        "last_reviewed_at": report["evaluated_at"],
    }
    manifest = update_manifest(archive_path, manifest_updates, dry_run)
    if not dry_run:
        write_knowledge_receipt(
            archive_path=archive_path,
            action="evaluate",
            validation_results=None,
            dry_run=False,
        )
    return report | {"dry_run": dry_run, "manifest": manifest}


def promote_archive(
    *,
    archive_path: Path,
    indexing_profile: str | None,
    promotion_status: str,
    retention_class: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    manifest = read_json(manifest_path(archive_path))
    report = read_json(evaluation_path(archive_path))
    if not report.get("promotion_allowed", False):
        raise ValueError("This archive cannot be promoted because evaluation kept it quarantined.")
    chosen_profile = indexing_profile or str(report.get("indexing_profile", "metadata_only"))
    if chosen_profile not in INDEXING_PROFILES:
        raise ValueError(f"Unsupported indexing profile: {chosen_profile}")
    if promotion_status not in PROMOTION_STATUSES or promotion_status == "not_promoted":
        raise ValueError("Promotion status must be one of: draft, promoted.")
    chosen_retention = retention_class or str(
        manifest.get("retention_class", report.get("retention_class", default_retention_class()))
    )
    if chosen_retention not in RETENTION_CLASSES:
        raise ValueError(f"Unsupported retention class: {chosen_retention}")

    promotion_file = promotion_doc_path(manifest["archive_id"])
    existing_text = promotion_file.read_text(encoding="utf-8") if promotion_file.exists() else None
    rendered = build_promotion_document(
        archive_path=archive_path,
        archive_id=manifest["archive_id"],
        manifest=manifest,
        evaluation=report,
        indexing_profile=chosen_profile,
        promotion_status=promotion_status,
        retention_class=chosen_retention,
        existing_text=existing_text,
    )
    if not dry_run:
        promotions_dir().mkdir(parents=True, exist_ok=True)
        promotion_file.write_text(rendered, encoding="utf-8")

    promotion = read_promotion_doc(promotion_file) if not dry_run else None
    manifest = update_manifest(
        archive_path,
        {
            "promotion_status": promotion_status,
            "retention_class": chosen_retention,
            "pipeline_version": PIPELINE_VERSION,
            "last_reviewed_at": utc_now(),
        },
        dry_run,
    )
    if not dry_run:
        write_knowledge_receipt(
            archive_path=archive_path,
            action="promote",
            validation_results=None,
            dry_run=False,
        )
    return {
        "archive_id": manifest["archive_id"],
        "dry_run": dry_run,
        "promotion_doc_path": relative_to_atlas(promotion_file),
        "promotion_status": promotion_status,
        "indexing_profile": chosen_profile,
        "retention_class": chosen_retention,
        "promotion": build_promotion_summary(promotion) if promotion is not None else None,
    }


def normalize_archive(*, archive_path: Path, dry_run: bool, force: bool) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    manifest = read_json(manifest_path(archive_path))
    report = read_json(evaluation_path(archive_path))
    if not report.get("normalization_allowed") and not force:
        raise ValueError("Evaluation rejected normalization for this archive. Use --force to override.")

    promotion_file = promotion_doc_path(manifest["archive_id"])
    promotion = read_promotion_doc(promotion_file) if promotion_file.exists() else None
    final_indexing_profile = (
        str(promotion["metadata"]["indexing_profile"])
        if promotion is not None
        else str(report.get("indexing_profile", manifest.get("indexing_profile", "metadata_only")))
    )
    final_promotion_status = (
        str(promotion["metadata"]["promotion_status"])
        if promotion is not None
        else str(manifest.get("promotion_status", "not_promoted"))
    )
    output_path = normalized_path(manifest["source_name"], manifest["slug"])
    generated = {
        "archive_id": manifest["archive_id"],
        "source_name": manifest["source_name"],
        "slug": manifest["slug"],
        "source_type": manifest["source_type"],
        "status": "normalized",
        "privacy_flag": manifest["privacy_flag"],
        "imported_at": manifest["imported_at"],
        "evaluated_at": report["evaluated_at"],
        "normalized_at": utc_now(),
        "safe_for_indexing": report["safe_for_indexing"],
        "indexing_profile": final_indexing_profile,
        "promotion_status": final_promotion_status,
        "promotion_doc_path": relative_to_atlas(promotion_file) if promotion is not None else None,
        "promotion": build_promotion_summary(promotion) if promotion is not None else None,
        "normalization_allowed": report["normalization_allowed"],
        "retention_class": manifest.get("retention_class", report.get("retention_class", default_retention_class())),
        "pipeline_version": PIPELINE_VERSION,
        "import_dir": relative_to_atlas(archive_path),
        "manifest_path": relative_to_atlas(manifest_path(archive_path)),
        "evaluation_path": relative_to_atlas(evaluation_path(archive_path)),
        "catalog_doc_path": relative_to_atlas(catalog_doc_path()),
        "risk_flags": report["risk_flags"],
        "summary": report["summary"],
        "notes": report["notes"],
        "no_execute_guarantee": True,
        "provenance": deep_merge(
            manifest.get("provenance", {}),
            {
                "manifest_path": relative_to_atlas(manifest_path(archive_path)),
                "evaluation_path": relative_to_atlas(evaluation_path(archive_path)),
            },
        ),
    }
    if "raw_archive_path" in manifest:
        generated["provenance"]["raw_archive_path"] = manifest["raw_archive_path"]
    if "raw_reference_dir" in manifest:
        generated["provenance"]["raw_reference_dir"] = manifest["raw_reference_dir"]
    if "raw_entries" in manifest:
        generated["raw_entries"] = manifest["raw_entries"]

    entry = update_runtime_catalog(
        archive_path,
        source_name=manifest["source_name"],
        slug=manifest["slug"],
        updates=generated,
        dry_run=dry_run,
    )
    manifest = update_manifest(
        archive_path,
        {
            "review_status": "normalized",
            "safe_for_indexing": report["safe_for_indexing"],
            "indexing_profile": final_indexing_profile,
            "promotion_status": final_promotion_status,
            "retention_class": generated["retention_class"],
            "pipeline_version": PIPELINE_VERSION,
            "artifact_digests": build_manifest_artifact_digests(manifest, archive_path),
            "extracted_snapshot_digest": extracted_snapshot_digest(archive_path),
            "last_reviewed_at": entry["normalized_at"],
        },
        dry_run,
    )
    if not dry_run:
        write_knowledge_receipt(
            archive_path=archive_path,
            action="normalize",
            validation_results=None,
            dry_run=False,
        )
    return entry | {"dry_run": dry_run, "output_path": relative_to_atlas(output_path), "manifest": manifest}


def discover_import_manifests() -> list[Path]:
    root = atlas_root() / "data" / "imports" / "knowledge"
    return sorted(root.glob("*/*/IMPORT-MANIFEST.json"))


def build_catalog_record(manifest_file: Path) -> dict[str, Any]:
    archive_path = manifest_file.parent
    manifest = read_json(manifest_file)
    evaluation_file = evaluation_path(archive_path)
    normalized_file = normalized_path(manifest["source_name"], manifest["slug"])
    evaluation = read_json(evaluation_file) if evaluation_file.exists() else None
    normalized = read_json(normalized_file) if normalized_file.exists() else None
    promotion_file = promotion_doc_path(manifest["archive_id"])
    promotion = None
    promotion_error = None
    if promotion_file.exists():
        try:
            promotion = read_promotion_doc(promotion_file)
        except ValueError as exc:
            promotion_error = str(exc)

    status = str(manifest.get("review_status", "imported"))
    safe_status = str(manifest.get("safe_for_indexing", "pending_review"))
    indexing_profile = str(manifest.get("indexing_profile", "metadata_only"))
    promotion_status = str(manifest.get("promotion_status", "not_promoted"))
    allowed = False
    notes = "Imported and awaiting evaluation."
    flags: dict[str, bool] = {
        "personal_private_material": False,
        "credentials_secrets_risk": False,
        "copyrighted_courseware_risk": False,
        "executable_content": False,
    }
    if evaluation is not None:
        status = str(evaluation.get("review_status", status))
        safe_status = str(evaluation.get("safe_for_indexing", safe_status))
        indexing_profile = str(evaluation.get("indexing_profile", indexing_profile))
        allowed = bool(evaluation.get("normalization_allowed", False))
        notes = str(evaluation.get("notes", notes))
        flags = evaluation.get("risk_flags", flags)
    if normalized is not None:
        status = str(normalized.get("status", "normalized"))
        safe_status = str(normalized.get("safe_for_indexing", safe_status))
        indexing_profile = str(normalized.get("indexing_profile", indexing_profile))
        promotion_status = str(normalized.get("promotion_status", promotion_status))
        allowed = bool(normalized.get("normalization_allowed", allowed))
        notes = str(normalized.get("notes", notes))
        flags = normalized.get("risk_flags", flags)
    if promotion is not None:
        promotion_status = str(promotion["metadata"]["promotion_status"])
        indexing_profile = str(promotion["metadata"]["indexing_profile"])
    return {
        "archive_id": manifest["archive_id"],
        "source": manifest["source_name"],
        "privacy_flag": manifest["privacy_flag"],
        "status": status,
        "safe_for_indexing": safe_status,
        "indexing_profile": indexing_profile,
        "promotion_status": promotion_status,
        "normalization_allowed": "yes" if allowed else "no",
        "risk_summary": risk_summary(flags),
        "notes": notes,
        "manifest_path": relative_to_atlas(manifest_file),
        "evaluation_path": relative_to_atlas(evaluation_file) if evaluation_file.exists() else "",
        "normalized_path": relative_to_atlas(normalized_file) if normalized_file.exists() else "",
        "promotion_doc_path": relative_to_atlas(promotion_file) if promotion_file.exists() else "",
        "promotion_error": promotion_error,
    }


def render_catalog(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Knowledge Catalog",
        "",
        "This document is the human-readable index for imported knowledge archives reviewed by ATLAS.",
        "",
        "## Catalog Fields",
        "",
        "| Field | Meaning |",
        "| --- | --- |",
        "| `archive_id` | Stable local identifier |",
        "| `source` | Where the archive came from |",
        "| `privacy_flag` | `private`, `mixed`, or `shareable` |",
        "| `status` | `imported`, `evaluated`, `normalized`, `indexed_metadata_only`, or `rejected` |",
        "| `safe_for_indexing` | `pending_review`, `no`, `restricted`, or `yes` |",
        "| `indexing_profile` | Downstream execution policy: `metadata_only`, `derived_only`, or `full_text` |",
        "| `promotion_status` | `not_promoted`, `draft`, or `promoted` |",
        "| `normalization_allowed` | Whether metadata may be retained in the runtime catalog |",
        "| `risk_summary` | Short list of active risk flags |",
        "| `notes` | Short explanation of the decision |",
        "",
        "## Current State",
        "",
        "The machine-readable companion lane is:",
        "",
        "- `runtime/cortex/catalog/knowledge/`",
        "",
        "The raw import lane is:",
        "",
        "- `data/imports/knowledge/`",
        "",
        "The promotion lane is:",
        "",
        "- `docs/knowledge/promotions/`",
        "",
        "The receipt lane is:",
        "",
        "- `runtime/receipts/knowledge/`",
        "",
        "## Catalog Records",
        "",
        CATALOG_BEGIN,
    ]
    if records:
        lines.extend(
            [
                "| archive_id | source | privacy_flag | status | safe_for_indexing | indexing_profile | promotion_status | normalization_allowed | risk_summary | notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for record in records:
            notes = record["notes"].replace("|", "/").replace("\n", " ").strip()
            summary = record["risk_summary"].replace("|", "/").replace("\n", " ").strip()
            lines.append(
                f"| `{record['archive_id']}` | `{record['source']}` | `{record['privacy_flag']}` | `{record['status']}` | `{record['safe_for_indexing']}` | `{record['indexing_profile']}` | `{record['promotion_status']}` | `{record['normalization_allowed']}` | `{summary}` | `{notes}` |"
            )
    else:
        lines.append("No knowledge archives are cataloged yet in this pass.")
    lines.extend(
        [
            CATALOG_END,
            "",
            "## Review Discipline",
            "",
            "When a new archive is reviewed:",
            "",
            "1. preserve the raw import in `data/imports/knowledge/`",
            "2. record the evaluation decision and indexing profile",
            "3. create a promotion doc only when derived or promoted knowledge is intentional",
            "4. write normalized runtime catalog entries from manifest, evaluation, and optional promotion docs",
            "5. keep copied notes high-level and non-sensitive",
            "6. do not treat imported courseware as stack-owned source",
        ]
    )
    return "\n".join(lines)


def update_catalog_doc(*, dry_run: bool) -> dict[str, Any]:
    records = [build_catalog_record(path) for path in discover_import_manifests()]
    rendered = render_catalog(records)
    path = catalog_doc_path()
    if not dry_run:
        path.write_text(rendered, encoding="utf-8")
    return {
        "dry_run": dry_run,
        "catalog_path": relative_to_atlas(path),
        "record_count": len(records),
        "records": records,
        "rendered_markdown": rendered,
    }


def parse_catalog_table(text: str) -> list[dict[str, str]]:
    if CATALOG_BEGIN not in text or CATALOG_END not in text:
        raise ValueError("Catalog markers are missing from KNOWLEDGE-CATALOG.md")
    block = text.split(CATALOG_BEGIN, 1)[1].split(CATALOG_END, 1)[0]
    rows = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("| archive_id ") or stripped.startswith("| --- "):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) != 10:
            continue
        rows.append(
            {
                "archive_id": parts[0].strip("`"),
                "source": parts[1].strip("`"),
                "privacy_flag": parts[2].strip("`"),
                "status": parts[3].strip("`"),
                "safe_for_indexing": parts[4].strip("`"),
                "indexing_profile": parts[5].strip("`"),
                "promotion_status": parts[6].strip("`"),
                "normalization_allowed": parts[7].strip("`"),
                "risk_summary": parts[8].strip("`"),
                "notes": parts[9].strip("`"),
            }
        )
    return rows


def validate_catalog() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    records = [build_catalog_record(path) for path in discover_import_manifests()]
    for manifest_file in discover_import_manifests():
        archive_path = manifest_file.parent
        manifest = read_json(manifest_file)
        archive_id = manifest["archive_id"]
        required_manifest = [
            "archive_id",
            "source_name",
            "slug",
            "source_type",
            "imported_at",
            "input_path",
            "original_filename",
            "privacy_flag",
            "review_status",
            "safe_for_indexing",
            "indexing_profile",
            "promotion_status",
            "retention_class",
            "pipeline_version",
            "artifact_digests",
            "extracted_snapshot_digest",
            "no_execute_guarantee",
            "paths",
            "provenance",
        ]
        missing = [field for field in required_manifest if field not in manifest]
        if manifest.get("source_type") == "zip" and "checksum" not in manifest:
            missing.append("checksum")
        if missing:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Manifest missing required fields: {', '.join(missing)}",
                }
            )
        if manifest.get("pipeline_version") != PIPELINE_VERSION:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Manifest pipeline_version must be '{PIPELINE_VERSION}'.",
                }
            )
        if manifest.get("privacy_flag") not in PRIVACY_FLAGS:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Unsupported privacy flag '{manifest.get('privacy_flag')}'.",
                }
            )
        if manifest.get("safe_for_indexing") not in SAFE_FOR_INDEXING:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Unsupported safe_for_indexing '{manifest.get('safe_for_indexing')}'.",
                }
            )
        if manifest.get("indexing_profile") not in INDEXING_PROFILES:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Unsupported indexing_profile '{manifest.get('indexing_profile')}'.",
                }
            )
        if manifest.get("promotion_status") not in PROMOTION_STATUSES:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Unsupported promotion_status '{manifest.get('promotion_status')}'.",
                }
            )
        if manifest.get("retention_class") not in RETENTION_CLASSES:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": f"Unsupported retention_class '{manifest.get('retention_class')}'.",
                }
            )

        evaluation_file = evaluation_path(archive_path)
        evaluation = read_json(evaluation_file) if evaluation_file.exists() else None
        if evaluation is not None:
            required_evaluation = [
                "archive_id",
                "source_name",
                "slug",
                "evaluated_at",
                "review_status",
                "safe_for_indexing",
                "indexing_profile",
                "promotion_allowed",
                "quarantine_flags",
                "normalization_allowed",
                "retention_class",
                "pipeline_version",
                "summary",
                "risk_flags",
                "notes",
            ]
            missing_eval = [field for field in required_evaluation if field not in evaluation]
            if missing_eval:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(evaluation_file),
                        "message": f"Evaluation missing required fields: {', '.join(missing_eval)}",
                    }
                )
            if evaluation.get("pipeline_version") != PIPELINE_VERSION:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(evaluation_file),
                        "message": f"Evaluation pipeline_version must be '{PIPELINE_VERSION}'.",
                    }
                )
            if evaluation.get("indexing_profile") not in INDEXING_PROFILES:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(evaluation_file),
                        "message": f"Unsupported indexing_profile '{evaluation.get('indexing_profile')}'.",
                    }
                )
            if evaluation.get("retention_class") not in RETENTION_CLASSES:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(evaluation_file),
                        "message": f"Unsupported retention_class '{evaluation.get('retention_class')}'.",
                    }
                )

        promotion_file = promotion_doc_path(archive_id)
        promotion = None
        if promotion_file.exists():
            try:
                promotion = read_promotion_doc(promotion_file)
            except ValueError as exc:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(promotion_file),
                        "message": str(exc),
                    }
                )
            else:
                if promotion["metadata"]["archive_id"] != archive_id:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(promotion_file),
                            "message": "Promotion archive_id does not match the manifest archive_id.",
                        }
                    )
                if evaluation is not None and not evaluation.get("promotion_allowed", False):
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(promotion_file),
                            "message": "Promotion doc exists even though evaluation disallowed promotion.",
                        }
                    )
        elif manifest.get("promotion_status") != "not_promoted":
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": "Manifest promotion_status requires a promotion doc, but none exists.",
                }
            )

        normalized_file = normalized_path(manifest["source_name"], manifest["slug"])
        normalized = read_json(normalized_file) if normalized_file.exists() else None
        if manifest.get("review_status") == "normalized" and normalized is None:
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(manifest_file),
                    "message": "Normalized review_status requires a runtime catalog entry.",
                }
            )
        if normalized is not None:
            required_normalized = [
                "archive_id",
                "source_name",
                "slug",
                "status",
                "safe_for_indexing",
                "indexing_profile",
                "promotion_status",
                "retention_class",
                "pipeline_version",
                "manifest_path",
                "evaluation_path",
            ]
            missing_normalized = [field for field in required_normalized if field not in normalized]
            if missing_normalized:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(normalized_file),
                        "message": f"Runtime catalog missing required fields: {', '.join(missing_normalized)}",
                    }
                )
            if normalized.get("pipeline_version") != PIPELINE_VERSION:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(normalized_file),
                        "message": f"Runtime catalog pipeline_version must be '{PIPELINE_VERSION}'.",
                    }
                )
            if normalized.get("promotion_status") not in PROMOTION_STATUSES:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(normalized_file),
                        "message": f"Unsupported promotion_status '{normalized.get('promotion_status')}'.",
                    }
                )
            if normalized.get("promotion_doc_path") and promotion is None:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(normalized_file),
                        "message": "Runtime catalog references a promotion doc that does not validate.",
                    }
                )
            if promotion is None and normalized.get("promotion_status") != "not_promoted":
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(normalized_file),
                        "message": "Runtime catalog promotion_status requires a valid promotion doc.",
                    }
                )
            if promotion is not None:
                if normalized.get("promotion_doc_path") != promotion["path"]:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(normalized_file),
                            "message": "Runtime catalog promotion_doc_path does not match the promotion doc location.",
                        }
                    )
                if normalized.get("indexing_profile") != promotion["metadata"]["indexing_profile"]:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(normalized_file),
                            "message": "Runtime catalog indexing_profile must match the promotion doc when a promotion doc exists.",
                        }
                    )

    catalog_path_value = catalog_doc_path()
    doc_rows = parse_catalog_table(catalog_path_value.read_text(encoding="utf-8"))
    expected = {
        (
            record["archive_id"],
            record["privacy_flag"],
            record["status"],
            record["safe_for_indexing"],
            record["indexing_profile"],
            record["promotion_status"],
        )
        for record in records
    }
    actual = {
        (
            row["archive_id"],
            row["privacy_flag"],
            row["status"],
            row["safe_for_indexing"],
            row["indexing_profile"],
            row["promotion_status"],
        )
        for row in doc_rows
    }
    if expected != actual:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(catalog_path_value),
                "message": "Catalog document rows do not match discovered knowledge records.",
            }
        )

    return {
        "generated_at": utc_now(),
        "catalog_path": relative_to_atlas(catalog_path_value),
        "record_count": len(records),
        "summary": {
            "errors": sum(1 for finding in findings if finding["severity"] == "error"),
            "warnings": sum(1 for finding in findings if finding["severity"] == "warning"),
            "total": len(findings),
        },
        "findings": findings,
    }


def backfill_archive(archive_path: Path, *, dry_run: bool) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    manifest = read_json(manifest_path(archive_path))
    evaluation = read_json(evaluation_path(archive_path)) if evaluation_path(archive_path).exists() else None
    promotion_file = promotion_doc_path(manifest["archive_id"])
    promotion = read_promotion_doc(promotion_file) if promotion_file.exists() else None
    default_profile = "metadata_only"
    retention_class = str(manifest.get("retention_class", default_retention_class()))
    manifest = update_manifest(
        archive_path,
        {
            "indexing_profile": str(manifest.get("indexing_profile", default_profile)),
            "promotion_status": promotion["metadata"]["promotion_status"] if promotion is not None else "not_promoted",
            "retention_class": retention_class,
            "pipeline_version": PIPELINE_VERSION,
            "artifact_digests": build_manifest_artifact_digests(manifest, archive_path),
            "extracted_snapshot_digest": extracted_snapshot_digest(archive_path),
            "last_reviewed_at": utc_now(),
        },
        dry_run,
    )
    if evaluation is not None:
        flags = evaluation.get("risk_flags", {})
        quarantine = quarantine_flags(flags)
        update_evaluation(
            archive_path,
            {
                "indexing_profile": str(evaluation.get("indexing_profile", default_profile)),
                "promotion_allowed": bool(
                    evaluation.get("promotion_allowed", not flags.get("credentials_secrets_risk", False))
                ),
                "quarantine_flags": evaluation.get("quarantine_flags", quarantine),
                "quarantine_reason": evaluation.get("quarantine_reason", quarantine_reason(quarantine)),
                "retention_class": str(evaluation.get("retention_class", retention_class)),
                "pipeline_version": PIPELINE_VERSION,
            },
            dry_run,
        )
        normalize_archive(archive_path=archive_path, dry_run=dry_run, force=True)
    if not dry_run:
        write_knowledge_receipt(
            archive_path=archive_path,
            action="backfill-v2",
            validation_results=None,
            dry_run=False,
        )
    return {
        "archive_id": manifest["archive_id"],
        "dry_run": dry_run,
        "archive_dir": relative_to_atlas(archive_path),
    }


def resolve_archive_dir(
    source_name: str | None,
    slug: str | None,
    archive_path: Path | None,
) -> Path:
    if archive_path is not None:
        return resolve_atlas_path(archive_path)
    if not source_name or not slug:
        raise ValueError("Provide either --archive-dir or both --source-name and --slug.")
    return archive_dir(source_name, slug).resolve()


def add_common_archive_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--archive-dir", type=Path)
    parser.add_argument("--source-name")
    parser.add_argument("--slug")
    parser.add_argument("--dry-run", action="store_true")
