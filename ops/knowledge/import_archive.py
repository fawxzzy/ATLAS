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

IMPORT_STATUSES = {
    "imported",
    "evaluated",
    "normalized",
    "indexed_metadata_only",
    "rejected",
}
PRIVACY_FLAGS = {"private", "mixed", "shareable"}
SAFE_FOR_INDEXING = {"pending_review", "no", "restricted", "yes"}
TEXT_EXTENSIONS = {
    ".bat", ".cfg", ".cmd", ".conf", ".cjs", ".csv", ".ini", ".ipynb", ".json",
    ".js", ".md", ".mjs", ".ps1", ".py", ".rst", ".sh", ".tex", ".toml", ".ts",
    ".tsx", ".txt", ".yaml", ".yml",
}
EXECUTABLE_EXTENSIONS = {
    ".app", ".bat", ".bin", ".cmd", ".com", ".dll", ".exe", ".jar", ".js",
    ".msi", ".ps1", ".py", ".rb", ".sh",
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
            "Input must already be staged under ATLAS so manifests stay ATLAS-relative."
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


def list_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


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


def normalization_allowed(flags: dict[str, bool]) -> bool:
    return not flags["credentials_secrets_risk"]


def risk_summary(flags: dict[str, bool]) -> str:
    active = [name for name, enabled in flags.items() if enabled]
    return ", ".join(active) if active else "none"


def update_manifest(
    archive_path: Path,
    *,
    review_status: str,
    safe_for_indexing_status: str | None = None,
    dry_run: bool,
) -> dict[str, Any]:
    manifest = read_json(manifest_path(archive_path))
    manifest["review_status"] = review_status
    if safe_for_indexing_status is not None:
        manifest["safe_for_indexing"] = safe_for_indexing_status
    manifest["last_reviewed_at"] = utc_now()
    write_json(manifest_path(archive_path), manifest, dry_run)
    return manifest


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
        write_json(manifest_path(knowledge_dir), manifest, dry_run=False)

    return {
        "ok": True,
        "dry_run": dry_run,
        "archive_id": manifest["archive_id"],
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

    report = {
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
        "normalization_allowed": normalization_allowed(flags),
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
    write_json(evaluation_path(archive_path), report, dry_run)
    update_manifest(
        archive_path,
        review_status="evaluated",
        safe_for_indexing_status=safe_for_indexing_status,
        dry_run=dry_run,
    )
    return report | {"dry_run": dry_run}


def normalize_archive(*, archive_path: Path, dry_run: bool, force: bool) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    manifest = read_json(manifest_path(archive_path))
    report = read_json(evaluation_path(archive_path))
    if not report.get("normalization_allowed") and not force:
        raise ValueError("Evaluation rejected normalization for this archive. Use --force to override.")
    output_path = normalized_path(manifest["source_name"], manifest["slug"])
    entry = {
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
        "normalization_allowed": report["normalization_allowed"],
        "import_dir": relative_to_atlas(archive_path),
        "manifest_path": relative_to_atlas(manifest_path(archive_path)),
        "evaluation_path": relative_to_atlas(evaluation_path(archive_path)),
        "catalog_doc_path": relative_to_atlas(catalog_doc_path()),
        "risk_flags": report["risk_flags"],
        "summary": report["summary"],
        "notes": report["notes"],
        "no_execute_guarantee": True,
        "provenance": manifest.get("provenance", {})
        | {
            "manifest_path": relative_to_atlas(manifest_path(archive_path)),
            "evaluation_path": relative_to_atlas(evaluation_path(archive_path)),
        },
    }
    if "raw_archive_path" in manifest:
        entry["provenance"]["raw_archive_path"] = manifest["raw_archive_path"]
    if "raw_reference_dir" in manifest:
        entry["provenance"]["raw_reference_dir"] = manifest["raw_reference_dir"]
    if "raw_entries" in manifest:
        entry["raw_entries"] = manifest["raw_entries"]
    write_json(output_path, entry, dry_run)
    update_manifest(
        archive_path,
        review_status="normalized",
        safe_for_indexing_status=report["safe_for_indexing"],
        dry_run=dry_run,
    )
    return entry | {"dry_run": dry_run, "output_path": relative_to_atlas(output_path)}


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

    status = manifest.get("review_status", "imported")
    safe_status = manifest.get("safe_for_indexing", "pending_review")
    allowed = False
    notes = "Imported and awaiting evaluation."
    flags: dict[str, bool] = {
        "personal_private_material": False,
        "credentials_secrets_risk": False,
        "copyrighted_courseware_risk": False,
        "executable_content": False,
    }
    if evaluation is not None:
        status = evaluation.get("review_status", status)
        safe_status = evaluation.get("safe_for_indexing", safe_status)
        allowed = bool(evaluation.get("normalization_allowed", False))
        notes = evaluation.get("notes", notes)
        flags = evaluation.get("risk_flags", flags)
    if normalized is not None:
        status = normalized.get("status", "normalized")
        safe_status = normalized.get("safe_for_indexing", safe_status)
        allowed = bool(normalized.get("normalization_allowed", allowed))
        notes = normalized.get("notes", notes)
        flags = normalized.get("risk_flags", flags)

    return {
        "archive_id": manifest["archive_id"],
        "source": manifest["source_name"],
        "privacy_flag": manifest["privacy_flag"],
        "status": status,
        "safe_for_indexing": safe_status,
        "normalization_allowed": "yes" if allowed else "no",
        "risk_summary": risk_summary(flags),
        "notes": notes,
        "manifest_path": relative_to_atlas(manifest_file),
        "evaluation_path": relative_to_atlas(evaluation_file) if evaluation_file.exists() else "",
        "normalized_path": relative_to_atlas(normalized_file) if normalized_file.exists() else "",
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
        "| `normalization_allowed` | Whether metadata may be retained in the runtime catalog |",
        "| `risk_summary` | Short list of active risk flags |",
        "| `notes` | Short explanation of the decision |",
        "",
        "## Current State",
        "",
        "The intended machine-readable companion lane is:",
        "",
        "- `runtime/cortex/catalog/knowledge/`",
        "",
        "The intended raw import lane is:",
        "",
        "- `data/imports/knowledge/`",
        "",
        "## Catalog Records",
        "",
        CATALOG_BEGIN,
    ]
    if records:
        lines.extend(
            [
                "| archive_id | source | privacy_flag | status | safe_for_indexing | normalization_allowed | risk_summary | notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for record in records:
            notes = record["notes"].replace("|", "/").replace("\n", " ").strip()
            summary = record["risk_summary"].replace("|", "/").replace("\n", " ").strip()
            lines.append(
                f"| `{record['archive_id']}` | `{record['source']}` | `{record['privacy_flag']}` | `{record['status']}` | `{record['safe_for_indexing']}` | `{record['normalization_allowed']}` | `{summary}` | `{notes}` |"
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
            "2. document the decision in this catalog",
            "3. write normalized runtime catalog entries only for accepted metadata",
            "4. keep copied notes high-level and non-sensitive",
            "5. do not treat imported courseware as stack-owned source",
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
        if len(parts) != 8:
            continue
        rows.append(
            {
                "archive_id": parts[0].strip("`"),
                "source": parts[1].strip("`"),
                "privacy_flag": parts[2].strip("`"),
                "status": parts[3].strip("`"),
                "safe_for_indexing": parts[4].strip("`"),
                "normalization_allowed": parts[5].strip("`"),
                "risk_summary": parts[6].strip("`"),
                "notes": parts[7].strip("`"),
            }
        )
    return rows


def validate_catalog() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    records = [build_catalog_record(path) for path in discover_import_manifests()]
    for manifest_file in discover_import_manifests():
        manifest = read_json(manifest_file)
        required = [
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
            "no_execute_guarantee",
            "paths",
            "provenance",
        ]
        missing = [field for field in required if field not in manifest]
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

    for record in records:
        if record["privacy_flag"] not in PRIVACY_FLAGS:
            findings.append(
                {
                    "severity": "error",
                    "path": record["manifest_path"],
                    "message": f"Unsupported privacy flag '{record['privacy_flag']}'.",
                }
            )
        if record["status"] not in IMPORT_STATUSES:
            findings.append(
                {
                    "severity": "error",
                    "path": record["manifest_path"],
                    "message": f"Unsupported status '{record['status']}'.",
                }
            )
        if record["safe_for_indexing"] not in SAFE_FOR_INDEXING:
            findings.append(
                {
                    "severity": "error",
                    "path": record["manifest_path"],
                    "message": f"Unsupported safe_for_indexing '{record['safe_for_indexing']}'.",
                }
            )
        if record["status"] == "normalized" and not record["normalized_path"]:
            findings.append(
                {
                    "severity": "error",
                    "path": record["manifest_path"],
                    "message": "Normalized status requires a runtime catalog entry.",
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
        )
        for record in records
    }
    actual = {
        (
            row["archive_id"],
            row["privacy_flag"],
            row["status"],
            row["safe_for_indexing"],
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a knowledge archive into the ATLAS raw intake lane."
    )
    parser.add_argument("--input-path", required=True, type=Path)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--slug")
    parser.add_argument("--privacy-flag", choices=sorted(PRIVACY_FLAGS), default="private")
    parser.add_argument("--provenance-note")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = import_archive(
        input_path=args.input_path,
        source_name=args.source_name,
        slug=args.slug,
        privacy_flag=args.privacy_flag,
        provenance_note=args.provenance_note,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
