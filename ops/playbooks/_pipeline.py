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
    "adopted_partially",
    "rejected",
}
ALLOWED_SAFETY = {"allowed_for_review", "restricted", "rejected"}
ALLOWED_VENDOR_SPECIFICITY = {"low", "medium", "high"}
TEXT_EXTENSIONS = {
    ".bat", ".cfg", ".cmd", ".conf", ".cjs", ".ini", ".json", ".js", ".md",
    ".mjs", ".ps1", ".py", ".sh", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
EXECUTABLE_EXTENSIONS = {
    ".bat", ".bin", ".cmd", ".com", ".dll", ".exe", ".jar", ".js", ".msi",
    ".ps1", ".py", ".rb", ".sh",
}
VENDOR_PATTERNS = {
    "anthropic": re.compile(r"\banthropic\b|\bclaude\b", re.IGNORECASE),
    "cursor": re.compile(r"\bcursor\b|\.cursorrules", re.IGNORECASE),
    "gemini": re.compile(r"\bgemini\b|\bgoogle ai\b", re.IGNORECASE),
    "openai": re.compile(r"\bopenai\b|\bgpt-?[45]\b|\bchatgpt\b", re.IGNORECASE),
    "windsurf": re.compile(r"\bwindsurf\b|\.windsurfrules", re.IGNORECASE),
}
FLAG_PATTERNS = {
    "vendor_lock": [
        re.compile(r"\b(?:openai|anthropic|claude|cursor|windsurf|gemini|copilot)\b", re.IGNORECASE),
        re.compile(r"\.cursorrules|\.windsurfrules|copilot-instructions", re.IGNORECASE),
    ],
    "hook_risk": [
        re.compile(r"\bhook(?:s|ed)?\b|\blifecycle\b|\bpre[_ -]?command\b|\bpost[_ -]?command\b", re.IGNORECASE),
        re.compile(r"\bpostinstall\b|\bpreinstall\b|\binstall hook\b", re.IGNORECASE),
    ],
    "daemon_risk": [
        re.compile(r"\bdaemon\b|\bbackground service\b|\bwatcher\b|\bworker loop\b", re.IGNORECASE),
        re.compile(r"\bscheduler\b|\bstart service\b|\bkeep alive\b", re.IGNORECASE),
    ],
    "repo_mutation_risk": [
        re.compile(r"\bgit (?:apply|checkout|switch|reset|clean)\b", re.IGNORECASE),
        re.compile(r"\bcopy .*repos/|\bwrite .*repos/|\bpatch .*repo", re.IGNORECASE),
        re.compile(r"\bmodify active repo\b|\bunpack .*repos/cortex\b", re.IGNORECASE),
    ],
    "secret_dependency": [
        re.compile(r"\bapi[_ -]?key\b|\bsecret\b|\btoken\b|\bcredential", re.IGNORECASE),
        re.compile(r"\.env\b|\bexport [A-Z0-9_]*KEY\b", re.IGNORECASE),
    ],
}
CATALOG_BEGIN = "<!-- PLAYBOOK-CATALOG:BEGIN -->"
CATALOG_END = "<!-- PLAYBOOK-CATALOG:END -->"


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def relative_to_atlas(path: Path) -> str:
    root = atlas_root()
    resolved = path.resolve()
    if resolved.is_relative_to(root):
        rel = resolved.relative_to(root)
        return "." if not rel.parts else rel.as_posix()
    return resolved.as_posix()


def ensure_within(parent: Path, candidate: Path) -> None:
    parent_resolved = parent.resolve()
    candidate_resolved = candidate.resolve()
    if not candidate_resolved.is_relative_to(parent_resolved):
        raise ValueError(f"Refusing path outside allowed root: {candidate_resolved}")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or "pack"


def source_dir(source_name: str) -> Path:
    return atlas_root() / "data" / "imports" / "playbooks" / slugify(source_name)


def import_dir(source_name: str, slug: str) -> Path:
    return source_dir(source_name) / slugify(slug)


def evaluation_path(pack_dir: Path) -> Path:
    return pack_dir / "EVALUATION.json"


def manifest_path(pack_dir: Path) -> Path:
    return pack_dir / "IMPORT-MANIFEST.json"


def normalized_path(source_name: str, slug: str) -> Path:
    return (
        atlas_root()
        / "runtime"
        / "cortex"
        / "catalog"
        / "playbooks"
        / f"{slugify(source_name)}--{slugify(slug)}.json"
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_manifest_status(pack_dir: Path, review_status: str, dry_run: bool) -> dict[str, Any]:
    manifest = read_json(manifest_path(pack_dir))
    manifest["review_status"] = review_status
    write_json(manifest_path(pack_dir), manifest, dry_run)
    return manifest


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
    return sorted([path for path in root.rglob("*") if path.is_file()])


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


def derive_vendor_terms(paths: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for vendor, pattern in VENDOR_PATTERNS.items():
        hits = 0
        for path in paths:
            haystacks = [path.name]
            if path.suffix.lower() in TEXT_EXTENSIONS:
                haystacks.append(read_text_limited(path))
            if any(pattern.search(haystack) for haystack in haystacks):
                hits += 1
        if hits:
            counts[vendor] = hits
    return counts


def classify_vendor_specificity(vendor_terms: dict[str, int], flags: dict[str, bool]) -> str:
    if flags["vendor_lock"] or len(vendor_terms) >= 2:
        return "high"
    if vendor_terms:
        return "medium"
    return "low"


def classify_safety(flags: dict[str, bool]) -> str:
    if flags["daemon_risk"] or flags["repo_mutation_risk"] or flags["secret_dependency"]:
        return "rejected"
    if flags["hook_risk"] or flags["vendor_lock"] or flags["executable_content"]:
        return "restricted"
    return "allowed_for_review"


def infer_capabilities(paths: list[Path]) -> list[str]:
    capabilities: set[str] = set()
    suffixes = {path.suffix.lower() for path in paths}
    names = {path.name.lower() for path in paths}
    if ".md" in suffixes or "readme.md" in names:
        capabilities.add("documentation")
    if ".json" in suffixes or ".yaml" in suffixes or ".yml" in suffixes:
        capabilities.add("structured_metadata")
    if any("prompt" in name for name in names):
        capabilities.add("prompt_pack")
    if any("checklist" in name or "runbook" in name for name in names):
        capabilities.add("operator_guidance")
    if any(suffix in EXECUTABLE_EXTENSIONS for suffix in suffixes):
        capabilities.add("executable_assets")
    return sorted(capabilities)


def import_pack(
    *,
    input_path: Path,
    source_name: str,
    slug: str | None,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    source_slug = slugify(source_name)
    pack_slug = slugify(slug or input_path.stem or input_path.name)
    pack_dir = import_dir(source_name, pack_slug)
    raw_dir = pack_dir / "raw"
    original_dir = pack_dir / "original"
    detected_type = "zip" if input_path.is_file() and input_path.suffix.lower() == ".zip" else "folder"
    if detected_type not in {"zip", "folder"}:
        raise ValueError("Input must be a directory or a .zip file.")
    if pack_dir.exists() and not force:
        raise FileExistsError(f"Import destination already exists: {relative_to_atlas(pack_dir)}")

    manifest: dict[str, Any] = {
        "source_name": source_name,
        "source_type": detected_type,
        "imported_at": utc_now(),
        "original_filename": input_path.name,
        "review_status": "imported",
    }
    if detected_type == "zip":
        manifest["checksum"] = file_checksum(input_path)

    operations: list[str] = []
    operations.append(f"prepare:{relative_to_atlas(pack_dir)}")
    if detected_type == "zip":
        archive_target = original_dir / input_path.name
        operations.append(f"copy:{relative_to_atlas(archive_target)}")
        operations.append(f"extract:{relative_to_atlas(raw_dir)}")
    else:
        operations.append(f"copytree:{relative_to_atlas(raw_dir)}")
    operations.append(f"write:{relative_to_atlas(manifest_path(pack_dir))}")

    if not dry_run:
        if pack_dir.exists() and force:
            shutil.rmtree(pack_dir)
        pack_dir.mkdir(parents=True, exist_ok=True)
        if detected_type == "zip":
            original_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, original_dir / input_path.name)
            extract_zip_safely(input_path, raw_dir)
        else:
            copy_folder(input_path, raw_dir)
        write_json(manifest_path(pack_dir), manifest, dry_run=False)

    return {
        "ok": True,
        "dry_run": dry_run,
        "no_execute_guarantee": True,
        "source_slug": source_slug,
        "slug": pack_slug,
        "import_dir": relative_to_atlas(pack_dir),
        "raw_dir": relative_to_atlas(raw_dir),
        "manifest": manifest,
        "planned_operations": operations,
    }


def evaluate_pack(*, pack_dir: Path, dry_run: bool) -> dict[str, Any]:
    pack_dir = pack_dir.resolve()
    raw_dir = pack_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Missing imported raw directory: {relative_to_atlas(raw_dir)}")
    manifest = read_json(manifest_path(pack_dir))
    paths = list_files(raw_dir)
    text_paths = iter_text_files(paths)
    flags: dict[str, bool] = {}
    indicators: dict[str, list[dict[str, str]]] = {}
    for name, patterns in FLAG_PATTERNS.items():
        hits = match_patterns(paths, patterns)
        indicators[name] = hits
        flags[name] = bool(hits)
    executable_flag, executable_hits = detect_executable_content(paths)
    indicators["executable_content"] = executable_hits
    flags["executable_content"] = executable_flag
    vendor_terms = derive_vendor_terms(paths)
    vendor_specificity = classify_vendor_specificity(vendor_terms, flags)
    safety = classify_safety(flags)
    normalization_allowed = safety != "rejected"
    capabilities = infer_capabilities(paths)
    adoption_surface = (
        "metadata and documentation only"
        if flags["executable_content"] or flags["hook_risk"] or flags["vendor_lock"]
        else "documentation and metadata"
    )
    notes = []
    if flags["vendor_lock"]:
        notes.append("Pack references vendor-specific conventions and should not become stack truth.")
    if flags["hook_risk"]:
        notes.append("Hook or lifecycle references were found; keep evaluation separate from handlers.")
    if flags["daemon_risk"] or flags["repo_mutation_risk"] or flags["secret_dependency"]:
        notes.append("High-risk signals require rejection until manually reviewed.")
    if not notes:
        notes.append("Pack can be reviewed without execution under the import/evaluate/normalize flow.")

    report = {
        "pack_id": f"{slugify(manifest['source_name'])}--{slugify(pack_dir.name)}",
        "source_name": manifest["source_name"],
        "slug": slugify(pack_dir.name),
        "evaluated_at": utc_now(),
        "import_dir": relative_to_atlas(pack_dir),
        "raw_dir": relative_to_atlas(raw_dir),
        "manifest_path": relative_to_atlas(manifest_path(pack_dir)),
        "review_status": "evaluated",
        "no_execute_guarantee": True,
        "summary": {
            "file_count": len(paths),
            "text_file_count": len(text_paths),
            "extension_counts": summarize_extension_counts(paths),
        },
        "risk_flags": flags,
        "risk_indicators": indicators,
        "vendor_terms": vendor_terms,
        "vendor_specificity": vendor_specificity,
        "safety": safety,
        "normalization_allowed": normalization_allowed,
        "capabilities": capabilities,
        "adoption_surface": adoption_surface,
        "notes": " ".join(notes),
    }
    write_json(evaluation_path(pack_dir), report, dry_run)
    update_manifest_status(pack_dir, "evaluated", dry_run)
    return report | {"dry_run": dry_run}


def normalize_pack(*, pack_dir: Path, dry_run: bool, force: bool) -> dict[str, Any]:
    pack_dir = pack_dir.resolve()
    manifest = read_json(manifest_path(pack_dir))
    report = read_json(evaluation_path(pack_dir))
    if not report.get("normalization_allowed") and not force:
        raise ValueError("Evaluation rejected normalization for this pack. Use --force to override.")
    output_path = normalized_path(manifest["source_name"], pack_dir.name)
    entry = {
        "pack_id": report["pack_id"],
        "source_name": manifest["source_name"],
        "source_type": manifest["source_type"],
        "slug": slugify(pack_dir.name),
        "status": "normalized",
        "imported_at": manifest["imported_at"],
        "evaluated_at": report["evaluated_at"],
        "normalized_at": utc_now(),
        "import_dir": relative_to_atlas(pack_dir),
        "manifest_path": relative_to_atlas(manifest_path(pack_dir)),
        "evaluation_path": relative_to_atlas(evaluation_path(pack_dir)),
        "risk_flags": report["risk_flags"],
        "vendor_specificity": report["vendor_specificity"],
        "safety": report["safety"],
        "normalization_allowed": report["normalization_allowed"],
        "capabilities": report["capabilities"],
        "adoption_surface": report["adoption_surface"],
        "notes": report["notes"],
        "no_execute_guarantee": True,
    }
    write_json(output_path, entry, dry_run)
    update_manifest_status(pack_dir, "normalized", dry_run)
    return entry | {
        "dry_run": dry_run,
        "output_path": relative_to_atlas(output_path),
    }


def discover_import_manifests() -> list[Path]:
    root = atlas_root() / "data" / "imports" / "playbooks"
    return sorted(root.glob("*/*/IMPORT-MANIFEST.json"))


def build_catalog_record(manifest_file: Path) -> dict[str, Any]:
    pack_dir = manifest_file.parent
    manifest = read_json(manifest_file)
    evaluation_file = evaluation_path(pack_dir)
    normalized_file = normalized_path(manifest["source_name"], pack_dir.name)
    evaluation = read_json(evaluation_file) if evaluation_file.exists() else None
    normalized = read_json(normalized_file) if normalized_file.exists() else None

    status = manifest.get("review_status", "imported")
    if normalized is not None:
        status = normalized.get("status", "normalized")
    elif evaluation is not None:
        status = evaluation.get("review_status", "evaluated")

    vendor_specificity = "low"
    safety = "allowed_for_review"
    adoption_surface = "pending evaluation"
    notes = "Imported and awaiting evaluation."
    if evaluation is not None:
        vendor_specificity = evaluation.get("vendor_specificity", vendor_specificity)
        safety = evaluation.get("safety", safety)
        adoption_surface = evaluation.get("adoption_surface", "review only")
        notes = evaluation.get("notes", notes)
    if normalized is not None:
        vendor_specificity = normalized.get("vendor_specificity", vendor_specificity)
        safety = normalized.get("safety", safety)
        adoption_surface = normalized.get("adoption_surface", adoption_surface)
        notes = normalized.get("notes", notes)

    return {
        "pack_id": f"{slugify(manifest['source_name'])}--{slugify(pack_dir.name)}",
        "source": manifest["source_name"],
        "status": status,
        "vendor_specificity": vendor_specificity,
        "safety": safety,
        "adoption_surface": adoption_surface,
        "notes": notes,
        "import_dir": relative_to_atlas(pack_dir),
        "manifest_path": relative_to_atlas(manifest_file),
        "evaluation_path": relative_to_atlas(evaluation_file) if evaluation_file.exists() else "",
        "normalized_path": relative_to_atlas(normalized_file) if normalized_file.exists() else "",
    }


def render_catalog(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Playbook Catalog",
        "",
        "This document is the human-readable index for external playbook packs evaluated by ATLAS.",
        "",
        "## Catalog Fields",
        "",
        "| Field | Meaning |",
        "| --- | --- |",
        "| `pack_id` | Stable local identifier |",
        "| `source` | Where the pack came from |",
        "| `status` | `imported`, `evaluated`, `normalized`, `adopted_partially`, or `rejected` |",
        "| `vendor_specificity` | `low`, `medium`, or `high` |",
        "| `safety` | `allowed_for_review`, `restricted`, or `rejected` |",
        "| `adoption_surface` | What ATLAS may reuse, if anything |",
        "| `notes` | Short explanation of the decision |",
        "",
        "## Current State",
        "",
        "The intended machine-readable companion lane is:",
        "",
        "- `runtime/cortex/catalog/playbooks/`",
        "",
        "The intended raw import lane is:",
        "",
        "- `data/imports/playbooks/`",
        "",
        "## Catalog Records",
        "",
        CATALOG_BEGIN,
    ]
    if records:
        lines.extend(
            [
                "| pack_id | source | status | vendor_specificity | safety | adoption_surface | notes |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for record in records:
            notes = record["notes"].replace("|", "/").replace("\n", " ").strip()
            adoption_surface = record["adoption_surface"].replace("|", "/").replace("\n", " ").strip()
            lines.append(
                f"| `{record['pack_id']}` | `{record['source']}` | `{record['status']}` | `{record['vendor_specificity']}` | `{record['safety']}` | `{adoption_surface}` | `{notes}` |"
            )
    else:
        lines.append("No third-party playbook packs are cataloged yet in this pass.")
    lines.extend(
        [
            CATALOG_END,
            "",
            "## Review Discipline",
            "",
            "When a new pack is reviewed:",
            "",
            "1. preserve the raw import in `data/imports/playbooks/`",
            "2. document the decision in this catalog",
            "3. write normalized runtime catalog entries only for packs that survive evaluation",
            "4. keep adopted concepts ATLAS-owned and vendor-neutral",
            "",
            "## Example Entry Template",
            "",
            "| pack_id | source | status | vendor_specificity | safety | adoption_surface | notes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            "| `example-pack` | `manual import` | `evaluated` | `medium` | `allowed_for_review` | `review checklist only` | `Prompt templates were reusable; installer logic was rejected.` |",
            "",
        ]
    )
    return "\n".join(lines)


def update_catalog_doc(*, dry_run: bool) -> dict[str, Any]:
    records = [build_catalog_record(manifest_file) for manifest_file in discover_import_manifests()]
    catalog_text = render_catalog(records)
    path = atlas_root() / "docs" / "playbooks" / "PLAYBOOK-CATALOG.md"
    if not dry_run:
        path.write_text(catalog_text, encoding="utf-8")
    return {
        "dry_run": dry_run,
        "catalog_path": relative_to_atlas(path),
        "record_count": len(records),
        "records": records,
        "rendered_markdown": catalog_text,
    }


def parse_catalog_table(text: str) -> list[dict[str, str]]:
    if CATALOG_BEGIN not in text or CATALOG_END not in text:
        raise ValueError("Catalog markers are missing from PLAYBOOK-CATALOG.md")
    block = text.split(CATALOG_BEGIN, 1)[1].split(CATALOG_END, 1)[0]
    rows = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("| pack_id ") or stripped.startswith("| --- "):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) != 7:
            continue
        rows.append(
            {
                "pack_id": parts[0].strip("`"),
                "source": parts[1].strip("`"),
                "status": parts[2].strip("`"),
                "vendor_specificity": parts[3].strip("`"),
                "safety": parts[4].strip("`"),
                "adoption_surface": parts[5].strip("`"),
                "notes": parts[6].strip("`"),
            }
        )
    return rows


def validate_catalog() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    records = [build_catalog_record(manifest_file) for manifest_file in discover_import_manifests()]
    for manifest_file in discover_import_manifests():
        manifest = read_json(manifest_file)
        missing = [field for field in ["source_name", "source_type", "imported_at", "original_filename", "review_status"] if field not in manifest]
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
        if record["status"] not in IMPORT_STATUSES:
            findings.append({"severity": "error", "path": record["manifest_path"], "message": f"Unsupported status '{record['status']}'."})
        if record["vendor_specificity"] not in ALLOWED_VENDOR_SPECIFICITY:
            findings.append({"severity": "error", "path": record["manifest_path"], "message": f"Unsupported vendor_specificity '{record['vendor_specificity']}'."})
        if record["safety"] not in ALLOWED_SAFETY:
            findings.append({"severity": "error", "path": record["manifest_path"], "message": f"Unsupported safety '{record['safety']}'."})
        normalized_file = record["normalized_path"]
        if record["status"] in {"normalized", "adopted_partially"} and not normalized_file:
            findings.append({"severity": "error", "path": record["manifest_path"], "message": "Normalized status requires a runtime catalog entry."})

    catalog_path = atlas_root() / "docs" / "playbooks" / "PLAYBOOK-CATALOG.md"
    doc_rows = parse_catalog_table(catalog_path.read_text(encoding="utf-8"))
    expected = {
        (
            record["pack_id"],
            record["status"],
            record["vendor_specificity"],
            record["safety"],
        )
        for record in records
    }
    actual = {
        (
            row["pack_id"],
            row["status"],
            row["vendor_specificity"],
            row["safety"],
        )
        for row in doc_rows
    }
    if expected != actual:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(catalog_path),
                "message": "Catalog document rows do not match discovered playbook records.",
            }
        )
    return {
        "generated_at": utc_now(),
        "catalog_path": relative_to_atlas(catalog_path),
        "record_count": len(records),
        "summary": {
            "errors": sum(1 for finding in findings if finding["severity"] == "error"),
            "warnings": sum(1 for finding in findings if finding["severity"] == "warning"),
            "total": len(findings),
        },
        "findings": findings,
    }


def resolve_pack_dir(source_name: str | None, slug: str | None, pack_dir: Path | None) -> Path:
    if pack_dir is not None:
        return pack_dir.resolve()
    if not source_name or not slug:
        raise ValueError("Provide either --pack-dir or both --source-name and --slug.")
    return import_dir(source_name, slug).resolve()


def add_common_pack_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pack-dir", type=Path)
    parser.add_argument("--source-name")
    parser.add_argument("--slug")
    parser.add_argument("--dry-run", action="store_true")
