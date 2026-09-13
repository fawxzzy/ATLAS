from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.observations import build_observation, emit_observation
from ops.knowledge import storage
from ops.knowledge.storage import enumerate_files as _long_path_safe_enumerate_files

# Wave S2A: opt-out switch back to the pre-convergence folder-import
# behavior (two unconditional shutil copies into raw/ and extracted/).
# Default is the convergence path: one verified relocation into raw/,
# extracted/ materialized only when explicitly requested. Set
# ATLAS_IMPORT_LEGACY_FOLDER_COPY=1 to roll back per-run without a code
# change.
_LEGACY_FOLDER_COPY_ENV = "ATLAS_IMPORT_LEGACY_FOLDER_COPY"


def _legacy_folder_copy_enabled(*, env: dict[str, str] | None = None) -> bool:
    source = env if env is not None else os.environ
    return source.get(_LEGACY_FOLDER_COPY_ENV, "").strip().lower() in {"1", "true", "yes", "on"}

PIPELINE_VERSION = "atlas.knowledge.pipeline.v2"
RECEIPT_VERSION = "atlas.knowledge.receipt.v1"
PROMOTION_SCHEMA_VERSION = "atlas.knowledge.promotion.v1"
QUERY_BUNDLE_VERSION = "atlas.knowledge.query-bundle.v1"
QUERY_RESULT_VERSION = "atlas.knowledge.query-results.v1"
QUERY_FULL_TEXT_STATUS = "reserved"

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
PROMOTION_DRAFT_PREFIX_OLD = "Draft promotion created from evaluation metadata for"
PROMOTION_DRAFT_PREFIX_V21 = "Draft promotion created from structural metadata for"
PROMOTION_SCAFFOLD_SECTION_PREFIXES = {
    "Topic Map": (
        "- source:",
        "- privacy flag:",
        "- safe_for_indexing:",
        "- file count:",
        "- text file count:",
        "- dominant extensions:",
        "- top-level directories:",
        "- representative paths:",
    ),
    "Evidence References": (
        "- manifest:",
        "- evaluation:",
        "- import lane:",
        "- raw archive:",
        "- raw tree:",
        "- extracted tree:",
        "- extracted snapshot digest:",
    ),
    "Exclusions And Redactions": (
        "- `",
        "- No additional redactions are recorded in this draft.",
        "- Promotion scaffolds omit raw body text, code blocks, and long excerpts by default.",
    ),
}
RECEIPT_ENTRYPOINTS = {
    "import": "ops/knowledge/import_archive.py",
    "evaluate": "ops/knowledge/evaluate_archive.py",
    "promote": "ops/knowledge/promote_archive.py",
    "normalize": "ops/knowledge/normalize_archive.py",
    "backfill-v2": "ops/knowledge/backfill_v2.py",
}


def atlas_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Wave S2A2: the import archive tree (source_dir()/archive_dir() and
# everything under them) is anchored to storage.import_storage_root(),
# which is ATLAS-relative by default (ATLAS_IMPORT_STORAGE_ROOT unset)
# but can be configured to live anywhere, including off the checkout
# entirely -- exactly like ATLAS_IMPORT_WORK_ROOT already does for
# transient staging. relative_to_atlas()/resolve_atlas_path() are the one
# shared pair every manifest, evaluation, receipt, and catalog path
# round-trips through (100+ call sites) -- rather than touch every one of
# them individually, this marker teaches the pair a second root, so every
# existing caller becomes storage-root-aware automatically. When the
# storage root is at its default (still under atlas_root()), a path under
# it resolves via the first branch exactly as before and the marker never
# appears -- fully backward compatible, proven by the existing S2A suite
# passing unchanged.
#
# The marker is a defined reference grammar, not unrestricted path
# concatenation: resolve_atlas_path() rejects a component that is empty,
# ".", "..", or contains ":" (a Windows drive letter) or a raw separator
# (defensive -- Path.parts should never produce one) BEFORE joining it,
# and separately verifies the fully resolved result still lives under
# import_storage_root() -- closing both a lexical ".." traversal and a
# symlink/junction that points outside the root, in one check, regardless
# of how the escape was attempted. relative_to_atlas() refuses to encode
# an ordinary ATLAS path whose first component is literally named
# "@storage-root": since that string would be indistinguishable from a
# genuine marker reference on decode, treating it as reserved (no real
# ATLAS directory is named this) is what keeps every accepted encoded
# reference decoding to the same location it encoded from.
_STORAGE_ROOT_MARKER = "@storage-root"


def _reject_unsafe_storage_reference_component(part: str, *, reference: str) -> None:
    if not part or part in {".", ".."} or ":" in part or "/" in part or "\\" in part:
        raise ValueError(
            f"Invalid {_STORAGE_ROOT_MARKER} reference component {part!r} in {reference!r}"
        )


def relative_to_atlas(path: Path, *, env: dict[str, str] | None = None) -> str:
    root = atlas_root()
    resolved = path.resolve()
    if resolved.is_relative_to(root):
        rel = resolved.relative_to(root)
        if rel.parts and rel.parts[0] == _STORAGE_ROOT_MARKER:
            raise ValueError(
                f"{resolved} sits directly under a path component literally named "
                f"{_STORAGE_ROOT_MARKER!r}, which is reserved for encoding storage-root "
                f"references and cannot itself be represented as a plain ATLAS-relative path."
            )
        return "." if not rel.parts else rel.as_posix()
    storage_root = storage.import_storage_root(env=env).resolve()
    try:
        rel = resolved.relative_to(storage_root)
    except ValueError:
        raise ValueError(
            f"Input must already be staged under ATLAS or the configured import "
            f"storage root so paths stay portable: {resolved}"
        ) from None
    if not rel.parts:
        return _STORAGE_ROOT_MARKER
    reference = f"{_STORAGE_ROOT_MARKER}/{rel.as_posix()}"
    # Encoding must refuse exactly what decoding refuses: resolve_atlas_path()
    # rejects an empty/"."/".."/colon/separator-containing component before
    # trusting it. Emitting a reference the decoder cannot round-trip would
    # produce a manifest field that silently stops resolving the moment
    # anything reads it back -- e.g. an ordinary (on POSIX) filename
    # containing a literal colon, which a Windows drive-letter reference
    # also uses, so the grammar must forbid it on both ends alike. Refused
    # here rather than renaming or omitting the underlying file: the file
    # itself is untouched, only representing it as a portable reference
    # fails.
    for part in rel.parts:
        _reject_unsafe_storage_reference_component(part, reference=reference)
    return reference


def resolve_atlas_path(path: Path, *, env: dict[str, str] | None = None) -> Path:
    if path.parts and path.parts[0] == _STORAGE_ROOT_MARKER:
        reference = path.as_posix()
        storage_root = storage.import_storage_root(env=env).resolve()
        target = storage_root
        for part in path.parts[1:]:
            _reject_unsafe_storage_reference_component(part, reference=reference)
            target = target / part
        resolved = target.resolve()
        # Containment is verified on the RESOLVED path, not the lexical
        # join: this is what catches a symlink/junction inside the
        # storage root whose target escapes it, which per-component
        # rejection above cannot see (each individual component looks
        # perfectly ordinary; only the resolved destination is wrong).
        try:
            ensure_within(storage_root, resolved)
        except ValueError:
            raise ValueError(
                f"{_STORAGE_ROOT_MARKER} reference {reference!r} resolves outside the "
                f"configured import storage root ({storage_root}): {resolved}"
            ) from None
        return resolved
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


def source_dir(source_name: str, *, env: dict[str, str] | None = None) -> Path:
    return storage.import_storage_root(env=env) / slugify(source_name)


def archive_dir(source_name: str, slug: str, *, env: dict[str, str] | None = None) -> Path:
    return source_dir(source_name, env=env) / slugify(slug)


def raw_dir(path: Path) -> Path:
    return path / "raw"


def extracted_dir(path: Path) -> Path:
    return path / "extracted"


def review_source_dir(archive_path: Path, manifest: dict[str, Any]) -> Path:
    """The tree downstream review (evaluate/promote/catalog/secret-scan)
    must read -- chosen from the import's own recorded contract, never
    from which directories happen to exist on disk.

    Selecting by directory presence is wrong two ways: a stray extracted/
    sitting next to a raw-only folder import would silently redirect
    evaluation to it, and a zip import missing its extracted/ tree would
    silently fall back to "reviewing" the raw .zip blob instead of
    failing. Both must fail closed instead.

        new raw-only folder import          -> raw/
        explicitly materialized folder import -> extracted/
        zip import                          -> extracted/ (required)
        missing required tree               -> error, not fallback

    Legacy compatibility: a manifest written before Wave S2A has no
    extracted_materialized key at all -- every import back then always
    produced both raw/ and extracted/, so its absence (the key missing
    entirely) is treated as materialized=True, matching that era's
    actual on-disk guarantee rather than reinterpreting history. This is
    the ONLY case coerced; a key that is merely falsy/malformed is not
    treated as absent -- see below.

    Field values are validated, not coerced: a malformed
    extracted_materialized (e.g. the string "false", which bool()
    would silently turn into True) or an unsupported source_type is
    rejected outright rather than quietly selecting the wrong tree. The
    selected tree must also actually be a directory, not merely exist.
    """
    source_type = manifest.get("source_type")
    if source_type not in {"zip", "folder"}:
        raise ValueError(
            f"Manifest for {relative_to_atlas(archive_path)} has an unsupported "
            f"source_type: {source_type!r}"
        )
    if "extracted_materialized" in manifest:
        raw_value = manifest["extracted_materialized"]
        if not isinstance(raw_value, bool):
            raise ValueError(
                f"Manifest for {relative_to_atlas(archive_path)} has a non-boolean "
                f"extracted_materialized value: {raw_value!r}"
            )
        extracted_materialized = raw_value
    else:
        extracted_materialized = True  # legacy default -- key absent entirely, see above

    if source_type == "zip" or extracted_materialized:
        chosen, label = extracted_dir(archive_path), "extracted/"
    else:
        chosen, label = raw_dir(archive_path), "raw/"
    if not chosen.exists():
        raise FileNotFoundError(
            f"Manifest for {relative_to_atlas(archive_path)} requires {label} as the review "
            f"tree (source_type={source_type!r}, extracted_materialized={extracted_materialized}), "
            f"but it does not exist"
        )
    if not chosen.is_dir():
        raise NotADirectoryError(
            f"Manifest for {relative_to_atlas(archive_path)} requires {label} as the review "
            f"tree, but {relative_to_atlas(chosen)} is not a directory"
        )
    return chosen


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


def knowledge_query_root() -> Path:
    return atlas_root() / "runtime" / "cortex" / "query" / "knowledge"


def knowledge_query_bundle_path() -> Path:
    return knowledge_query_root() / "bundle.json"


def latest_receipt_path(archive_id: str) -> Path:
    return receipt_dir(archive_id) / "latest.json"


def emit_knowledge_observations(receipt: dict[str, Any], *, dry_run: bool) -> None:
    if dry_run:
        return
    source_ref = str(receipt.get("paths", {}).get("latest_path", "")).strip()
    if not source_ref:
        return
    archive_id = str(receipt.get("archive_id", "")).strip() or None
    recorded_at = str(receipt.get("recorded_at")) if receipt.get("recorded_at") is not None else None
    emit_observation(
        build_observation(
            observation_type=f"knowledge_receipt.{receipt.get('action', 'unknown')}",
            source_kind="knowledge_receipt",
            status="blocked" if receipt.get("promotion_blocked") else "recorded",
            observed_at=recorded_at,
            source_ref=source_ref,
            scope_ref=archive_id,
            details={
                "archive_id": archive_id,
                "promotion_status": receipt.get("promotion", {}).get("promotion_status")
                if isinstance(receipt.get("promotion"), dict)
                else None,
                "indexing_profile": receipt.get("promotion", {}).get("indexing_profile")
                if isinstance(receipt.get("promotion"), dict)
                else receipt.get("evaluation", {}).get("indexing_profile")
                if isinstance(receipt.get("evaluation"), dict)
                else None,
            },
        ),
        owner="knowledge-pipeline",
        root=atlas_root(),
    )

    if receipt.get("action") == "import":
        emit_observation(
            build_observation(
                observation_type="knowledge.archive",
                source_kind="knowledge_receipt",
                status="imported",
                observed_at=recorded_at,
                source_ref=source_ref,
                scope_ref=archive_id,
                details={
                    "archive_id": archive_id,
                    "manifest_path": receipt.get("paths", {}).get("manifest_path")
                    if isinstance(receipt.get("paths"), dict)
                    else None,
                },
            ),
            owner="knowledge-pipeline",
            root=atlas_root(),
        )

    promotion = receipt.get("promotion") if isinstance(receipt.get("promotion"), dict) else {}
    if receipt.get("action") == "promote" or promotion.get("promotion_status") not in {None, "not_promoted"}:
        emit_observation(
            build_observation(
                observation_type="knowledge.promotion",
                source_kind="knowledge_receipt",
                status=str(promotion.get("promotion_status") or "not_promoted"),
                observed_at=recorded_at,
                source_ref=source_ref,
                scope_ref=archive_id,
                details={
                    "archive_id": archive_id,
                    "indexing_profile": promotion.get("indexing_profile"),
                    "promotion_doc_path": receipt.get("paths", {}).get("promotion_doc_path")
                    if isinstance(receipt.get("paths"), dict)
                    else None,
                },
            ),
            owner="knowledge-pipeline",
            root=atlas_root(),
        )

    evaluation = receipt.get("evaluation") if isinstance(receipt.get("evaluation"), dict) else {}
    if receipt.get("promotion_blocked") or evaluation.get("quarantine_flags"):
        emit_observation(
            build_observation(
                observation_type="knowledge.trust_gate",
                source_kind="knowledge_receipt",
                status="blocked",
                observed_at=recorded_at,
                source_ref=source_ref,
                scope_ref=archive_id,
                details={
                    "archive_id": archive_id,
                    "promotion_block_reason": receipt.get("promotion_block_reason"),
                    "quarantine_flags": evaluation.get("quarantine_flags"),
                    "quarantine_reason": evaluation.get("quarantine_reason"),
                },
            ),
            owner="knowledge-pipeline",
            root=atlas_root(),
        )


def discover_runtime_catalogs() -> list[Path]:
    root = atlas_root() / "runtime" / "cortex" / "catalog" / "knowledge"
    return sorted(path for path in root.glob("*.json") if path.is_file())


def discover_promotion_docs() -> list[Path]:
    return sorted(path for path in promotions_dir().glob("*.md") if path.is_file())


def discover_latest_receipts() -> list[Path]:
    return sorted(path for path in knowledge_receipts_root().glob("*/latest.json") if path.is_file())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def file_checksum(path: Path) -> str:
    # Long-path-safe: a plain path.open() fails past the 260-character
    # MAX_PATH boundary on Windows without the admin-only LongPathsEnabled
    # policy. list_files()/enumerate_files() already return long-path-safe
    # paths, but reading their content still needs the same \\?\ prefixing
    # storage.py applies internally -- found via a >260-character fixture
    # pushed through the actual import -> evaluate path, not just
    # storage.py's own enumeration tests.
    digest = hashlib.sha256()
    with storage._win_long_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def stable_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def file_checksum_if_exists(path: Path) -> str | None:
    return file_checksum(path) if path.exists() and path.is_file() else None


def list_files(root: Path) -> list[Path]:
    # Delegates to ops.knowledge.storage.enumerate_files(), which is
    # long-path-safe on Windows (rglob() silently drops entries past the
    # 260-character MAX_PATH boundary unless the process-wide
    # LongPathsEnabled policy is set, which requires admin rights and is
    # not guaranteed). Same signature and return type as before -- this is
    # a correctness fix, not a behavior change for any path under the
    # limit. See ops/knowledge/storage.py and
    # docs/ops/ATLAS-IMPORT-STORAGE-CONVERGENCE-WAVE-1.md.
    return _long_path_safe_enumerate_files(root)


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in list_files(root):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(str(storage._lp_stat(path).st_size).encode("utf-8"))
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


class FolderImportRelocationError(RuntimeError):
    """A folder import's verified relocation into raw/ failed at preflight
    or copy. Raised before the import manifest is written, so a failed
    relocation never produces a half-imported archive."""


class FolderImportReplacementUnsupportedError(RuntimeError):
    """--force was given to replace an already-completed archive under the
    storage-convergence folder path, which cannot yet do that safely: a
    destructive delete-then-relocate would destroy the existing archive
    before the new one's preflight/link checks even run. Rather than
    build transactional replacement (a separate, larger piece of work),
    this refuses the destructive path outright. The operator can remove
    the existing archive directory themselves first, or set
    ATLAS_IMPORT_LEGACY_FOLDER_COPY=1 to use the old destructive --force
    behavior."""


class UnownedDestinationError(RuntimeError):
    """raw/ and/or extracted/ under this archive's destination already
    hold content, there is no completed IMPORT-MANIFEST.json, and there
    is no IMPORT-ATTEMPT.json proving the content belongs to an earlier
    attempt at this exact import. A deterministic destination path
    (source_name + slug) does not by itself prove ownership -- it could
    be a different source, a changed source, or content someone
    deliberately preserved there. resumable_copy_tree() overwrites any
    file that doesn't match the new source byte-for-byte, so resuming
    without proof of ownership would silently destroy whatever is
    actually there. Refused instead; nothing under the destination is
    touched."""


class AdmissionIdentityMismatchError(RuntimeError):
    """An IMPORT-ATTEMPT.json exists at this destination, but its
    recorded identity (archive_id, source content snapshot, destination,
    materialize_extracted) does not match the current request. Treating
    this as a legitimate resume would let a changed or different source
    silently overwrite content that a genuine interrupted attempt left
    behind. Refused instead; nothing under the destination is touched."""


class CorruptAttemptRecordError(RuntimeError):
    """IMPORT-ATTEMPT.json exists but is not safe to trust as ownership
    evidence: it is a symlink / reparse point (never read or written
    through -- the record itself is part of the protected write
    boundary, exactly like any other destination path), its content is
    not valid JSON, its contract_version is not recognized, or a
    required field is missing or the wrong type. Refused before any of
    its claimed content is trusted and before any write touches it."""


ATTEMPT_RECORD_CONTRACT_VERSION = "atlas.knowledge.import-attempt.v1"
_ATTEMPT_RECORD_REQUIRED_FIELDS: dict[str, type] = {
    "archive_id": str,
    "destination": str,
    "source_snapshot_digest": str,
    "materialize_extracted": bool,
}


def import_attempt_record_path(knowledge_dir: Path) -> Path:
    return knowledge_dir / "IMPORT-ATTEMPT.json"


def _describe_archive_path_lexically(path: Path, *, env: dict[str, str] | None = None) -> str:
    """Lexical (never-resolves, never-follows-a-symlink) description of
    `path` for error messages where `path` might itself be a symlink --
    relative_to_atlas() calls Path.resolve(), which would follow it
    straight through to wherever it points. `path` is always constructed
    from archive_dir(...) by this module, so it is always lexically
    under either atlas_root() or the configured storage root (never
    resolved, so a symlink at the leaf doesn't change which one)."""
    try:
        return path.relative_to(atlas_root()).as_posix()
    except ValueError:
        pass
    storage_root = storage.import_storage_root(env=env)
    try:
        rel = path.relative_to(storage_root)
    except ValueError:
        return str(path)
    return _STORAGE_ROOT_MARKER if not rel.parts else f"{_STORAGE_ROOT_MARKER}/{rel.as_posix()}"


def _read_and_validate_attempt_record(
    path: Path, *, env: dict[str, str] | None = None
) -> dict[str, Any] | None:
    """Return the existing attempt record at `path`, or None if none
    exists. Never opens or reads through a symlink -- checked first, via
    storage's own no-follow primitive, exactly as the write path (see
    _write_json_atomic()) never writes through one. Any content that
    exists but cannot be trusted (unreadable, malformed JSON, wrong
    contract_version, a required field missing or the wrong type) raises
    CorruptAttemptRecordError rather than being silently treated as
    absent or, worse, partially trusted."""
    if storage._lp_is_symlink(path):
        raise CorruptAttemptRecordError(
            f"{_describe_archive_path_lexically(path, env=env)} is a symlink, not a plain "
            f"record file. Refusing to read or write through it -- remove it yourself first "
            f"if you have independently confirmed it is safe to discard."
        )
    if not path.exists():
        return None
    try:
        record = read_json(path)
    except (OSError, ValueError) as exc:
        raise CorruptAttemptRecordError(
            f"{relative_to_atlas(path, env=env)} could not be read as a valid JSON record: {exc}"
        ) from exc
    if not isinstance(record, dict) or record.get("contract_version") != ATTEMPT_RECORD_CONTRACT_VERSION:
        raise CorruptAttemptRecordError(
            f"{relative_to_atlas(path, env=env)} is not a recognized attempt record "
            f"(contract_version={(record.get('contract_version') if isinstance(record, dict) else None)!r})"
        )
    for key, expected_type in _ATTEMPT_RECORD_REQUIRED_FIELDS.items():
        if key not in record or not isinstance(record[key], expected_type):
            raise CorruptAttemptRecordError(
                f"{relative_to_atlas(path, env=env)} has a missing or invalid field: {key!r}"
            )
    return record


def _folder_relocation_layout(
    *, archive_id: str, knowledge_dir: Path, env: dict[str, str] | None
) -> dict[str, Path]:
    """The three derived paths a folder relocation needs, shared between
    the standalone preflight check run during admission and the actual
    relocate_archive_source() call, so the two can never drift apart."""
    return {
        "work_root": storage.import_work_root(env=env) / archive_id,
        "receipt_path": knowledge_dir / "RELOCATION-RECEIPT.json",
        "expected_manifest_path": knowledge_dir / "RELOCATION-MANIFEST.json",
    }


def _archive_destination_has_content(knowledge_dir: Path) -> bool:
    """True if raw/ or extracted/ under knowledge_dir already hold at
    least one entry. Checked shallowly (one iterdir() at the raw/ or
    extracted/ level itself, whose own path is short and bounded even
    when content nested inside it is deep) -- existence alone is enough
    to require proof of ownership before anything resumes into it."""
    for sub in (raw_dir(knowledge_dir), extracted_dir(knowledge_dir)):
        if not sub.exists():
            continue
        try:
            next(sub.iterdir())
            return True
        except StopIteration:
            continue
    return False


def _source_snapshot_digest(input_path: Path) -> str:
    """A content-sensitive identity for a folder import's source tree,
    computed the same way relocate_archive_source() computes its own
    source-anchored expected manifest (so a same-named file with
    different bytes changes this digest, not just a different file
    list). Computed independently in the pipeline layer, before any
    admission decision, rather than extending storage.py's API for it --
    the redundant tree walk inside relocate_archive_source() itself is
    an accepted, bounded cost for a correctness-critical identity check,
    not a hot path."""
    manifest = storage.build_relocation_manifest(input_path)
    return storage.stable_json_digest(manifest)


def _relocate_folder_import(
    *,
    archive_id: str,
    input_path: Path,
    knowledge_dir: Path,
    materialize_extracted: bool,
    env: dict[str, str] | None,
) -> dict[str, Any]:
    """Wave S2A: a folder import copies its source into raw/ exactly once,
    through storage.relocate_archive_source() -- per-volume peak-space
    preflight (fail closed, no silent fallback), a source-anchored
    manifest, an atomic resumable copy with bounded write confinement,
    exact destination reconciliation, and a durable relocation receipt.
    The pre-S2A path made two unconditional shutil copies (raw/ and
    extracted/); extracted/ is now materialized only when the caller
    asks for it.

    Staging uses storage.import_work_root() (ATLAS_IMPORT_WORK_ROOT), so
    the transient copy volume can be moved off a constrained system
    drive without touching where the durable archive lands.
    """
    layout = _folder_relocation_layout(archive_id=archive_id, knowledge_dir=knowledge_dir, env=env)
    work_root = layout["work_root"]
    receipt_path = layout["receipt_path"]
    expected_manifest_ref_path = layout["expected_manifest_path"]
    result = storage.relocate_archive_source(
        archive_id=archive_id,
        source_root=input_path,
        destination_root=raw_dir(knowledge_dir),
        work_root=work_root,
        source_description=f"knowledge-import folder relocation for {archive_id}",
        materialize_extracted_root=extracted_dir(knowledge_dir) if materialize_extracted else None,
        receipt_path=receipt_path,
        expected_manifest_path=expected_manifest_ref_path,
    )
    if not result.ok:
        # Surface every distinct failure mode so a caller sees a precise,
        # recoverable state -- not just "it failed" -- including the case
        # where knowledge_dir held a leftover partial from an earlier
        # interrupted attempt that didn't cleanly resume: verify_restore's
        # require_exact_match=True catches an orphaned/mismatched leftover
        # rather than silently accepting it, and that shows up here as a
        # destination_verification finding, not a copy failure.
        findings = list(result.space_budget.findings)
        raw_failures = [f.category for f in result.raw_copy_result.failed] if result.raw_copy_result else []
        extracted_failures = (
            [f.category for f in result.extracted_copy_result.failed] if result.extracted_copy_result else []
        )
        destination_issues = {
            k: v
            for k, v in (result.destination_verification or {}).items()
            if k in {"missing_paths", "unexpected_paths", "mismatched_paths"} and v
        }
        raise FolderImportRelocationError(
            f"folder import relocation failed for {archive_id}: "
            f"space_budget_ok={result.space_budget.ok} findings={findings} "
            f"raw_copy_failures={raw_failures} extracted_copy_failures={extracted_failures} "
            f"destination_verification_issues={destination_issues}"
        )
    receipt = result.receipt or {}
    return {
        "ok": True,
        "mode": "storage-convergence",
        "materialized_extracted": bool(materialize_extracted),
        "expected_manifest_digest": receipt.get("expected_manifest_digest"),
        "destination_manifest_digest": receipt.get("destination_manifest_digest"),
        "expected_manifest_ref": relative_to_atlas(expected_manifest_ref_path, env=env),
        "receipt_ref": relative_to_atlas(receipt_path, env=env),
        "space_budget_ok": result.space_budget.ok,
        "staging_outside_atlas_root": not work_root.resolve().is_relative_to(atlas_root()),
        "destination_verification_ok": bool((result.destination_verification or {}).get("ok")),
    }


def build_raw_entries(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in list_files(root):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": storage._lp_stat(path).st_size,
                "checksum": file_checksum(path),
            }
        )
    return entries


def summarize_extension_counts(paths: list[Path]) -> dict[str, int]:
    counts = Counter(path.suffix.lower() or "<no_ext>" for path in paths)
    return {key: counts[key] for key in sorted(counts)}


def iter_text_files(paths: list[Path]) -> list[Path]:
    return [path for path in paths if path.suffix.lower() in TEXT_EXTENSIONS]


def top_level_directories(root: Path) -> list[str]:
    if not root.exists():
        return []
    entries = [path.name for path in root.iterdir() if path.is_dir()]
    return sorted(entries)[:8]


def representative_relative_paths(root: Path, paths: list[Path], limit: int = 6) -> list[str]:
    return [path.relative_to(root).as_posix() for path in paths[:limit]]


def read_text_limited(path: Path, max_chars: int = 4000) -> str:
    # Long-path-safe for the same reason as file_checksum(): this reads
    # arbitrary enumerated source-tree paths, which can exceed MAX_PATH.
    return storage._win_long_path(path).read_text(encoding="utf-8", errors="ignore")[:max_chars]


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


def match_inline_text(label: str, text: str, patterns: list[re.Pattern[str]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            matched = pattern.search(line)
            if matched:
                hits.append({"path": label, "line_number": index, "match": matched.group(0)})
                break
    return hits[:20]


def scan_secret_risk(
    *,
    paths: list[Path] | None = None,
    inline_documents: list[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if paths:
        hits.extend(match_patterns(paths, SECRET_PATTERNS))
    if inline_documents:
        for label, text in inline_documents:
            hits.extend(match_inline_text(label, text, SECRET_PATTERNS))
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


def build_manifest_artifact_digests(
    manifest: dict[str, Any], archive_path: Path, *, env: dict[str, str] | None = None
) -> dict[str, str]:
    digests: dict[str, str] = {}
    raw_root = raw_dir(archive_path)
    if manifest.get("source_type") == "zip":
        raw_archive_rel = manifest.get("raw_archive_path")
        if isinstance(raw_archive_rel, str):
            raw_archive = resolve_atlas_path(Path(raw_archive_rel), env=env)
            if raw_archive.exists():
                digests["raw_archive"] = file_checksum(raw_archive)
        input_path = manifest.get("input_path")
        if isinstance(input_path, str):
            input_candidate = resolve_atlas_path(Path(input_path), env=env)
            if input_candidate.exists() and input_candidate.is_file():
                digests["input_source"] = file_checksum(input_candidate)
    else:
        if raw_root.exists():
            digests["raw_tree"] = tree_digest(raw_root)
        input_path = manifest.get("input_path")
        if isinstance(input_path, str):
            input_candidate = resolve_atlas_path(Path(input_path), env=env)
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


def stable_unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        result.append(cleaned)
        seen.add(cleaned)
    return result


def tokenize_lexical_terms(*values: str) -> list[str]:
    tokens: set[str] = set()
    for value in values:
        for match in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", value.lower()):
            tokens.add(match)
            tokens.update(part for part in match.split("-") if part)
    return sorted(tokens)


def evidence_reference_ids(lines: list[str]) -> list[str]:
    identifiers: list[str] = []
    for line in lines:
        matches = re.findall(r"`([^`]+)`", line)
        if matches:
            identifiers.extend(matches)
            continue
        cleaned = clean_markdown_text(line)
        if cleaned:
            identifiers.append(cleaned)
    return stable_unique_strings(identifiers)


def promotion_draft_summary(archive_id: str) -> str:
    return (
        f"Draft promotion created from structural metadata for `{archive_id}`. "
        "Replace this section with a human-authored derived summary before marking the promotion as promoted."
    )


def build_promotion_scaffold_sections(
    *,
    archive_path: Path,
    manifest: dict[str, Any],
    evaluation: dict[str, Any],
    archive_id: str,
) -> dict[str, str]:
    extracted_root = review_source_dir(archive_path, manifest)
    extracted_files = list_files(extracted_root)
    dominant_extensions = list(evaluation.get("summary", {}).get("extension_counts", {}).items())[:5]
    rendered_extensions = (
        ", ".join(f"{ext}={count}" for ext, count in dominant_extensions) if dominant_extensions else "none"
    )
    top_dirs = top_level_directories(extracted_root)
    representative_paths = representative_relative_paths(extracted_root, extracted_files)
    topic_lines = [
        f"- source: `{manifest['source_name']}`",
        f"- privacy flag: `{manifest['privacy_flag']}`",
        f"- safe_for_indexing: `{evaluation.get('safe_for_indexing', 'pending_review')}`",
        f"- file count: `{evaluation.get('summary', {}).get('file_count', 'unknown')}`",
        f"- text file count: `{evaluation.get('summary', {}).get('text_file_count', 'unknown')}`",
        f"- dominant extensions: `{rendered_extensions}`",
        f"- top-level directories: `{', '.join(top_dirs) if top_dirs else 'none'}`",
        f"- representative paths: `{', '.join(representative_paths) if representative_paths else 'none'}`",
    ]
    evidence_lines = [
        f"- manifest: `{relative_to_atlas(manifest_path(archive_path))}`",
        f"- evaluation: `{relative_to_atlas(evaluation_path(archive_path))}`",
        f"- import lane: `{relative_to_atlas(archive_path)}`",
        f"- extracted tree: `{relative_to_atlas(extracted_root)}`",
        f"- extracted snapshot digest: `{manifest.get('extracted_snapshot_digest', 'sha256:pending')}`",
    ]
    if manifest.get("raw_archive_path"):
        evidence_lines.append(f"- raw archive: `{manifest['raw_archive_path']}`")
    if manifest.get("raw_reference_dir"):
        evidence_lines.append(f"- raw tree: `{manifest['raw_reference_dir']}`")

    exclusion_lines = [
        "- Promotion scaffolds omit raw body text, code blocks, and long excerpts by default.",
    ]
    for name, enabled in evaluation.get("risk_flags", {}).items():
        if enabled:
            exclusion_lines.append(f"- `{name}` remains excluded from promotion-safe derived output.")
    if len(exclusion_lines) == 1:
        exclusion_lines.append("- No additional redactions are recorded in this draft.")

    return {
        "Derived Summary": promotion_draft_summary(archive_id),
        "Topic Map": "\n".join(topic_lines),
        "Evidence References": "\n".join(evidence_lines),
        "Exclusions And Redactions": "\n".join(exclusion_lines),
    }


def is_promotion_summary_scaffold(archive_id: str, summary: str) -> bool:
    cleaned = clean_markdown_text(summary)
    expected_prefixes = [
        clean_markdown_text(promotion_draft_summary(archive_id)),
        clean_markdown_text(
            f"Draft promotion created from evaluation metadata for `{archive_id}`. "
            "Replace this section with a human-authored derived summary before downstream derived indexing."
        ),
        clean_markdown_text(PROMOTION_DRAFT_PREFIX_OLD + f" `{archive_id}`."),
        clean_markdown_text(PROMOTION_DRAFT_PREFIX_V21 + f" `{archive_id}`."),
    ]
    return any(cleaned.startswith(prefix) for prefix in expected_prefixes)


def section_looks_scaffold(section_name: str, value: str, archive_id: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if section_name == "Derived Summary":
        return is_promotion_summary_scaffold(archive_id, stripped)
    prefixes = PROMOTION_SCAFFOLD_SECTION_PREFIXES.get(section_name, ())
    if not prefixes:
        return False
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if not lines:
        return True
    return all(any(line.startswith(prefix) for prefix in prefixes) for line in lines)


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
    refresh_derived: bool,
) -> str:
    existing_metadata: dict[str, Any] = {}
    existing_sections: dict[str, str] = {}
    if existing_text:
        existing_metadata, existing_body = frontmatter_block(existing_text)
        existing_sections = extract_section_map(existing_body)

    timestamp_now = utc_now()
    created_at = str(existing_metadata.get("created_at", timestamp_now))
    title = f"# Promotion: {archive_id}"
    scaffold_sections = build_promotion_scaffold_sections(
        archive_path=archive_path,
        manifest=manifest,
        evaluation=evaluation,
        archive_id=archive_id,
    )
    sections: dict[str, str] = {}
    for section_name in PROMOTION_REQUIRED_SECTIONS:
        existing_value = existing_sections.get(section_name)
        if not existing_value:
            sections[section_name] = scaffold_sections[section_name]
            continue
        if refresh_derived and section_looks_scaffold(section_name, existing_value, archive_id):
            sections[section_name] = scaffold_sections[section_name]
            continue
        sections[section_name] = existing_value
    metadata_changed = any(
        str(existing_metadata.get(key)) != str(value)
        for key, value in {
            "schema_version": PROMOTION_SCHEMA_VERSION,
            "archive_id": archive_id,
            "promotion_status": promotion_status,
            "indexing_profile": indexing_profile,
            "retention_class": retention_class,
            "created_at": created_at,
        }.items()
    )
    sections_changed = any(
        (existing_sections.get(section_name, "").strip() != sections[section_name].strip())
        for section_name in PROMOTION_REQUIRED_SECTIONS
    )
    updated_at = (
        timestamp_now
        if metadata_changed or sections_changed or not existing_text
        else str(existing_metadata.get("updated_at", created_at))
    )
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


def query_search_policy(
    *,
    indexing_profile: str,
    promotion_exists: bool,
    promotion_allowed: bool,
) -> dict[str, Any]:
    derived_searchable = (
        promotion_exists
        and promotion_allowed
        and indexing_profile in {"derived_only", "full_text"}
    )
    return {
        "metadata_searchable": True,
        "derived_searchable": derived_searchable,
        "full_text_searchable": False,
        "full_text_status": QUERY_FULL_TEXT_STATUS,
    }


def build_query_bundle_payload() -> dict[str, Any]:
    promotion_docs = {
        doc["metadata"]["archive_id"]: doc
        for doc in (read_promotion_doc(path) for path in discover_promotion_docs())
    }
    receipt_docs = {
        receipt["archive_id"]: {"path": path, "payload": receipt}
        for path in discover_latest_receipts()
        for receipt in [read_json(path)]
    }
    runtime_sources: list[dict[str, str]] = []
    promotion_sources: list[dict[str, str]] = []
    receipt_sources: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []

    for path in discover_runtime_catalogs():
        catalog = read_json(path)
        archive_id = str(catalog["archive_id"])
        receipt_entry = receipt_docs.get(archive_id)
        if receipt_entry is None:
            raise FileNotFoundError(f"Missing latest receipt for archive_id '{archive_id}'.")
        receipt = receipt_entry["payload"]
        digests = receipt.get("digests")
        tooling = receipt.get("tooling")
        if not isinstance(digests, dict):
            raise ValueError(f"Latest receipt for '{archive_id}' is missing receipt digests.")
        if not isinstance(tooling, dict):
            raise ValueError(f"Latest receipt for '{archive_id}' is missing tooling metadata.")
        if not digests.get("manifest") or not digests.get("evaluation"):
            raise ValueError(f"Latest receipt for '{archive_id}' is missing manifest or evaluation digests.")
        if not tooling.get("pipeline_digest"):
            raise ValueError(f"Latest receipt for '{archive_id}' is missing the pipeline digest.")
        if receipt_entrypoint_path(str(receipt.get("action"))) is not None and not tooling.get("entrypoint_digest"):
            raise ValueError(f"Latest receipt for '{archive_id}' is missing the entrypoint digest.")

        promotion = promotion_docs.get(archive_id)
        promotion_summary = build_promotion_summary(promotion) if promotion is not None else None
        promotion_allowed = bool((receipt.get("evaluation") or {}).get("promotion_allowed", False))
        query_policy = query_search_policy(
            indexing_profile=str(catalog.get("indexing_profile", "metadata_only")),
            promotion_exists=promotion is not None,
            promotion_allowed=promotion_allowed,
        )
        derived_summary_text = (
            str(promotion_summary["derived_summary"])
            if promotion_summary is not None and query_policy["derived_searchable"]
            else None
        )
        topic_map_terms = (
            stable_unique_strings(
                [clean_markdown_text(term) for term in promotion_summary["topic_map"]]
            )
            if promotion_summary is not None and query_policy["derived_searchable"]
            else []
        )
        evidence_ids = (
            evidence_reference_ids(promotion_summary["evidence_references"])
            if promotion_summary is not None and query_policy["derived_searchable"]
            else []
        )

        metadata_terms = tokenize_lexical_terms(
            str(catalog.get("archive_id", "")),
            str(catalog.get("source_name", "")),
            str(catalog.get("status", "")),
            str(catalog.get("privacy_flag", "")),
            str(catalog.get("promotion_status", "")),
            str(catalog.get("indexing_profile", "")),
            str(catalog.get("retention_class", "")),
        )
        derived_terms = tokenize_lexical_terms(derived_summary_text or "", *topic_map_terms)
        evidence_terms = tokenize_lexical_terms(*evidence_ids)

        records.append(
            {
                "archive_id": archive_id,
                "source_name": str(catalog.get("source_name", "")),
                "status": str(catalog.get("status", "")),
                "privacy_flag": str(catalog.get("privacy_flag", "")),
                "promotion_status": str(catalog.get("promotion_status", "not_promoted")),
                "indexing_profile": str(catalog.get("indexing_profile", "metadata_only")),
                "retention_class": str(catalog.get("retention_class", default_retention_class())),
                "promotion_allowed": promotion_allowed,
                "paths": {
                    "runtime_catalog_path": relative_to_atlas(path),
                    "promotion_doc_path": promotion["path"] if promotion is not None else None,
                    "latest_receipt_path": relative_to_atlas(Path(receipt_entry["path"])),
                },
                "source_digests": {
                    "runtime_catalog": file_checksum(path),
                    "promotion_doc": promotion["digest"] if promotion is not None else None,
                    "latest_receipt": file_checksum(Path(receipt_entry["path"])),
                },
                "query_policy": query_policy,
                "derived_summary_text": derived_summary_text,
                "topic_map_terms": topic_map_terms,
                "evidence_reference_ids": evidence_ids,
                "receipt": {
                    "receipt_id": receipt.get("receipt_id"),
                    "action": receipt.get("action"),
                    "recorded_at": receipt.get("recorded_at"),
                    "digests": digests,
                    "tooling_digests": {
                        "entrypoint_digest": tooling.get("entrypoint_digest"),
                        "pipeline_digest": tooling.get("pipeline_digest"),
                    },
                },
                "search_terms": {
                    "metadata": metadata_terms,
                    "derived": derived_terms,
                    "evidence": evidence_terms,
                },
            }
        )

        runtime_sources.append(
            {
                "archive_id": archive_id,
                "path": relative_to_atlas(path),
                "digest": file_checksum(path),
            }
        )

    for archive_id, doc in sorted(promotion_docs.items()):
        promotion_sources.append(
            {
                "archive_id": archive_id,
                "path": doc["path"],
                "digest": doc["digest"],
            }
        )
    for receipt_path_value in discover_latest_receipts():
        receipt = read_json(receipt_path_value)
        receipt_sources.append(
            {
                "archive_id": str(receipt["archive_id"]),
                "path": relative_to_atlas(receipt_path_value),
                "digest": file_checksum(receipt_path_value),
            }
        )

    return {
        "schema_version": QUERY_BUNDLE_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "full_text_status": QUERY_FULL_TEXT_STATUS,
        "record_count": len(records),
        "bundle_inputs": {
            "runtime_catalogs": sorted(runtime_sources, key=lambda item: item["archive_id"]),
            "promotion_docs": sorted(promotion_sources, key=lambda item: item["archive_id"]),
            "latest_receipts": sorted(receipt_sources, key=lambda item: item["archive_id"]),
        },
        "records": records,
    }


def build_query_bundle(*, dry_run: bool) -> dict[str, Any]:
    payload = build_query_bundle_payload()
    content_digest = stable_json_digest(payload)
    bundle = payload | {"content_digest": content_digest}
    bundle_path_value = knowledge_query_bundle_path()
    if not dry_run:
        write_json(bundle_path_value, bundle, dry_run=False)
    return {
        "dry_run": dry_run,
        "bundle_path": relative_to_atlas(bundle_path_value),
        "record_count": bundle["record_count"],
        "content_digest": content_digest,
        "input_counts": {
            "runtime_catalogs": len(payload["bundle_inputs"]["runtime_catalogs"]),
            "promotion_docs": len(payload["bundle_inputs"]["promotion_docs"]),
            "latest_receipts": len(payload["bundle_inputs"]["latest_receipts"]),
        },
    }


def validate_query_bundle() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    bundle_path_value = knowledge_query_bundle_path()
    runtime_catalogs = discover_runtime_catalogs()
    if runtime_catalogs and not bundle_path_value.exists():
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": "Knowledge query bundle is missing for the current runtime knowledge catalog.",
            }
        )
        return findings
    if not bundle_path_value.exists():
        return findings

    bundle = read_json(bundle_path_value)
    required_fields = [
        "schema_version",
        "pipeline_version",
        "full_text_status",
        "record_count",
        "bundle_inputs",
        "records",
        "content_digest",
    ]
    missing = [field for field in required_fields if field not in bundle]
    if missing:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": f"Query bundle is missing required fields: {', '.join(missing)}",
            }
        )
        return findings
    if bundle.get("schema_version") != QUERY_BUNDLE_VERSION:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": f"Query bundle schema_version must be '{QUERY_BUNDLE_VERSION}'.",
            }
        )
    if bundle.get("pipeline_version") != PIPELINE_VERSION:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": f"Query bundle pipeline_version must be '{PIPELINE_VERSION}'.",
            }
        )
    if bundle.get("full_text_status") != QUERY_FULL_TEXT_STATUS:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": f"Query bundle full_text_status must remain '{QUERY_FULL_TEXT_STATUS}' in this pass.",
            }
        )
    try:
        expected_payload = build_query_bundle_payload()
    except Exception as exc:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": f"Query bundle could not be rebuilt from source lanes: {exc}",
            }
        )
        return findings

    actual_payload = dict(bundle)
    actual_digest = str(actual_payload.pop("content_digest"))
    expected_digest = stable_json_digest(expected_payload)
    if actual_digest != expected_digest:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": "Query bundle content_digest does not match the rebuilt deterministic payload.",
            }
        )
    if actual_payload != expected_payload:
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": "Query bundle contents do not match the rebuilt deterministic payload.",
            }
        )
    if bundle.get("record_count") != len(expected_payload["records"]):
        findings.append(
            {
                "severity": "error",
                "path": relative_to_atlas(bundle_path_value),
                "message": "Query bundle record_count does not match the rebuilt record set.",
            }
        )
    return findings


def current_validation_placeholder() -> dict[str, Any]:
    return {"status": "not_run", "findings": []}


def receipt_entrypoint_path(action: str) -> Path | None:
    relative = RECEIPT_ENTRYPOINTS.get(action)
    return atlas_root() / relative if relative else None


def receipt_tooling(action: str) -> dict[str, Any]:
    entrypoint = receipt_entrypoint_path(action)
    pipeline_path = Path(__file__).resolve()
    return {
        "entrypoint_path": relative_to_atlas(entrypoint) if entrypoint and entrypoint.exists() else None,
        "entrypoint_digest": file_checksum_if_exists(entrypoint) if entrypoint is not None else None,
        "pipeline_path": relative_to_atlas(pipeline_path),
        "pipeline_digest": file_checksum(pipeline_path),
        "python_version": sys.version.split()[0],
    }


def write_knowledge_receipt(
    *,
    archive_path: Path,
    action: str,
    validation_results: dict[str, Any] | None,
    promotion_blocked: bool = False,
    promotion_block_reason: str | None = None,
    dry_run: bool,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    manifest = read_json(manifest_path(archive_path))
    archive_id = manifest["archive_id"]
    evaluation = read_json(evaluation_path(archive_path)) if evaluation_path(archive_path).exists() else None
    normalized_file = normalized_path(manifest["source_name"], manifest["slug"])
    normalized = read_json(normalized_file) if normalized_file.exists() else None
    promotion_file = promotion_doc_path(archive_id)
    promotion = None
    if promotion_file.exists():
        try:
            promotion = read_promotion_doc(promotion_file)
        except ValueError:
            promotion = None
    recorded_at = utc_now()
    timestamp = recorded_at.replace("-", "").replace(":", "").replace(".", "")
    receipt_folder = receipt_dir(archive_id)
    receipt_path_value = receipt_folder / f"{timestamp}-{action}.json"
    latest_path = receipt_folder / "latest.json"
    runtime_outputs = []
    if normalized is not None:
        runtime_outputs.append(relative_to_atlas(normalized_file, env=env))
    runtime_outputs.append(relative_to_atlas(catalog_doc_path(), env=env))
    validation_payload = validation_results or current_validation_placeholder()
    receipt = {
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": f"{archive_id}-{action}-{timestamp}",
        "recorded_at": recorded_at,
        "pipeline_version": PIPELINE_VERSION,
        "archive_id": archive_id,
        "action": action,
        "atlas_root": ".",
        "promotion_blocked": promotion_blocked,
        "promotion_block_reason": promotion_block_reason,
        "paths": {
            "manifest_path": relative_to_atlas(manifest_path(archive_path), env=env),
            "evaluation_path": relative_to_atlas(evaluation_path(archive_path), env=env)
            if evaluation is not None
            else None,
            "promotion_doc_path": promotion["path"] if promotion is not None else None,
            "runtime_catalog_path": relative_to_atlas(normalized_file, env=env) if normalized is not None else None,
            "receipt_path": relative_to_atlas(receipt_path_value, env=env),
            "latest_path": relative_to_atlas(latest_path, env=env),
        },
        "inputs": {
            "artifact_digests": manifest.get("artifact_digests", {}),
            "extracted_snapshot_digest": manifest.get("extracted_snapshot_digest"),
        },
        "digests": {
            "manifest": file_checksum(manifest_path(archive_path)),
            "evaluation": file_checksum_if_exists(evaluation_path(archive_path)),
            "promotion_doc": promotion["digest"] if promotion is not None else file_checksum_if_exists(promotion_file),
            "runtime_catalog": file_checksum_if_exists(normalized_file),
            "validation_results": None
            if validation_payload == current_validation_placeholder()
            else stable_json_digest(validation_payload),
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
        "validation_results": validation_payload,
        "tooling": receipt_tooling(action),
    }
    if not dry_run:
        receipt_folder.mkdir(parents=True, exist_ok=True)
        receipt_path_value.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        latest_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        emit_knowledge_observations(receipt, dry_run=False)
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
    materialize_extracted: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if privacy_flag not in PRIVACY_FLAGS:
        raise ValueError(f"Unsupported privacy flag: {privacy_flag}")
    legacy_folder_copy = _legacy_folder_copy_enabled(env=env)
    # The env this call was given -- if any -- is honored consistently for
    # every storage-root-relative decision made anywhere in this call
    # (admission, manifest fields, the attempt record, receipts), not just
    # for storage.import_work_root(). Silently falling back to real
    # os.environ partway through would mean a caller's explicit
    # ATLAS_IMPORT_STORAGE_ROOT override was honored for staging but
    # ignored for where the archive itself resolves -- a real
    # inconsistency, not a documented, supported way to mix configuration
    # sources.
    input_path = resolve_atlas_path(input_path, env=env)
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {relative_to_atlas(input_path, env=env)}")
    input_path_rel = relative_to_atlas(input_path, env=env)
    archive_slug = slugify(slug or input_path.stem or input_path.name)
    archive_id_value = f"{slugify(source_name)}--{archive_slug}"
    knowledge_dir = archive_dir(source_name, archive_slug, env=env)
    detected_type = "zip" if input_path.is_file() and input_path.suffix.lower() == ".zip" else "folder"
    if detected_type not in {"zip", "folder"}:
        raise ValueError("Input must be a directory or a .zip file.")

    new_engine_folder_path = detected_type == "folder" and not legacy_folder_copy
    folder_materializes_extracted = detected_type == "folder" and (
        materialize_extracted or legacy_folder_copy
    )

    # "Does an import already live here" has two distinct positive
    # answers, and a leftover directory with neither is NOT one of them:
    #
    # 1. A *completed* prior import -- a written IMPORT-MANIFEST.json.
    # 2. A genuinely *interrupted* prior attempt at this exact request --
    #    proven by a durable IMPORT-ATTEMPT.json (written after this same
    #    admission gate passed, before any copying, on some earlier call)
    #    whose recorded identity (archive_id, a content-sensitive digest
    #    of the source tree, destination, materialize_extracted) matches
    #    the current request exactly.
    #
    # knowledge_dir being a deterministic function of (source_name, slug)
    # is NOT proof of either -- a different source, a changed source, or
    # content someone deliberately preserved can occupy the same path.
    # relocate_archive_source()'s resumable copy overwrites any file that
    # doesn't match the new source byte-for-byte (that is what makes
    # resuming a *genuine* interrupted attempt work); its final exact
    # reconciliation can only prove the destination matches the source
    # *afterward* -- it cannot protect content that a wrongly-assumed
    # resume already overwrote. So ownership must be established BEFORE
    # any copying starts, not inferred from the path alone and verified
    # only after the fact.
    archive_previously_completed = manifest_path(knowledge_dir).exists()
    if archive_previously_completed and not force:
        raise FileExistsError(
            f"Import destination already exists: {relative_to_atlas(knowledge_dir, env=env)}"
        )
    if archive_previously_completed and force and new_engine_folder_path:
        # Refuse the destructive replacement rather than delete the
        # completed archive and then risk the new copy's preflight or
        # link-rejection check failing with nothing left to restore.
        # Transactional (atomic) replacement is future work, not built
        # here -- see FolderImportReplacementUnsupportedError.
        raise FolderImportReplacementUnsupportedError(
            f"--force cannot yet safely replace the completed archive at "
            f"{relative_to_atlas(knowledge_dir, env=env)} under the storage-convergence "
            f"folder path (no transactional replacement implemented). Remove "
            f"the existing archive directory yourself first, or set "
            f"ATLAS_IMPORT_LEGACY_FOLDER_COPY=1 to use the prior destructive "
            f"--force behavior."
        )

    # Full attempt-record lifecycle, in this exact order:
    #   inspect destination and any existing evidence
    #   -> validate any existing attempt record, independent of whether
    #      raw/extracted hold content yet (a record can legitimately
    #      exist before a single byte has been copied)
    #   -> (in the execution block below) required preflight
    #   -> create a fresh record safely, or reuse a matching one unchanged
    #   -> copy/resume
    #   -> reconcile and publish completion evidence (IMPORT-MANIFEST.json)
    #
    # The record itself is part of the protected write boundary, exactly
    # like raw/ or extracted/: it is never read through a symlink, never
    # silently replaced because "there's no payload yet" (an attempt can
    # legitimately exist before any copying starts), and never rewritten
    # once it already matches the current request -- rewriting a valid
    # record for no reason is itself a way to destroy it, if interrupted
    # mid-write. See _read_and_validate_attempt_record(),
    # CorruptAttemptRecordError, AdmissionIdentityMismatchError.
    attempt_record_path = import_attempt_record_path(knowledge_dir)
    source_snapshot_digest_value: str | None = None
    existing_attempt: dict[str, Any] | None = None
    reuse_existing_attempt = False
    if new_engine_folder_path and not archive_previously_completed:
        # Needed either way: to validate a claimed resume below, or to
        # record for a *future* retry to validate against once this call
        # proceeds. Computed from input_path directly -- read-only, and
        # never touches a rejected link's content (see
        # _classify_link_entry(), which classifies a link entry without
        # opening it).
        source_snapshot_digest_value = _source_snapshot_digest(input_path)
        existing_attempt = _read_and_validate_attempt_record(attempt_record_path, env=env)
        if existing_attempt is None:
            if _archive_destination_has_content(knowledge_dir):
                raise UnownedDestinationError(
                    f"{relative_to_atlas(raw_dir(knowledge_dir), env=env)} and/or "
                    f"{relative_to_atlas(extracted_dir(knowledge_dir), env=env)} already contain content, "
                    f"but there is no IMPORT-MANIFEST.json (completed import) or "
                    f"IMPORT-ATTEMPT.json (proven interrupted attempt) to establish that it "
                    f"belongs to this import. Refusing to resume into it -- verify what is "
                    f"actually there and remove it yourself first if it is safe to discard."
                )
            # else: genuinely fresh -- no record, no content either.
        else:
            expected_attempt = {
                "archive_id": archive_id_value,
                "destination": relative_to_atlas(knowledge_dir, env=env),
                "source_snapshot_digest": source_snapshot_digest_value,
                "materialize_extracted": folder_materializes_extracted,
            }
            mismatches = {
                key: {"recorded": existing_attempt.get(key), "current": expected}
                for key, expected in expected_attempt.items()
                if existing_attempt.get(key) != expected
            }
            if mismatches:
                raise AdmissionIdentityMismatchError(
                    f"IMPORT-ATTEMPT.json at {relative_to_atlas(knowledge_dir, env=env)} does not match "
                    f"this request: {mismatches}. Refusing to resume into content that may "
                    f"belong to a different source, a changed source, or different import "
                    f"options -- nothing under the destination has been touched."
                )
            reuse_existing_attempt = True  # matches exactly -- never rewritten

    manifest: dict[str, Any] = {
        "archive_id": archive_id_value,
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
            "import_dir": relative_to_atlas(knowledge_dir, env=env),
            "raw_dir": relative_to_atlas(raw_dir(knowledge_dir), env=env),
            "extracted_dir": relative_to_atlas(extracted_dir(knowledge_dir), env=env),
        },
        "provenance": {
            "staged_under_atlas": True,
            "source_label": source_name,
            "original_filename": input_path.name,
        },
    }
    if provenance_note:
        manifest["provenance"]["note"] = provenance_note
    # For a folder import, extracted/ is only materialized when the caller
    # explicitly asks for it (or the legacy rollback switch is on) --
    # otherwise raw/ is the single verified copy and downstream review
    # reads it via review_source_dir(). A zip import always extracts.
    # (folder_materializes_extracted itself is computed earlier, before
    # the admission gate, since it's part of an attempt record's identity.)
    manifest["extracted_materialized"] = detected_type == "zip" or folder_materializes_extracted

    if detected_type == "zip":
        manifest["checksum"] = file_checksum(input_path)
        manifest["raw_archive_path"] = f"{relative_to_atlas(raw_dir(knowledge_dir), env=env)}/{input_path.name}"
    else:
        manifest["raw_reference_dir"] = relative_to_atlas(raw_dir(knowledge_dir), env=env)
        manifest["folder_import_mode"] = "legacy-double-copy" if legacy_folder_copy else "storage-convergence"
        if legacy_folder_copy:
            # No link-rejection check exists on this path (matches its
            # pre-S2A behavior exactly) -- reading source content here is
            # not a "read before reject" hazard the way it would be on
            # the storage-convergence path below.
            manifest["raw_entries"] = build_raw_entries(input_path)
        # For the storage-convergence path, raw_entries is filled in
        # after relocation succeeds, from raw_dir(knowledge_dir) -- the
        # verified destination, not the unchecked source -- so a
        # rejected link's content is never read. See _relocate_folder_import.

    operations: list[str] = [f"prepare:{relative_to_atlas(knowledge_dir, env=env)}"]
    if detected_type == "zip":
        operations.append(f"copy:{relative_to_atlas(raw_dir(knowledge_dir) / input_path.name, env=env)}")
        operations.append(f"extract:{relative_to_atlas(extracted_dir(knowledge_dir), env=env)}")
    elif legacy_folder_copy:
        operations.append(f"copytree:{relative_to_atlas(raw_dir(knowledge_dir), env=env)}")
        operations.append(f"copytree:{relative_to_atlas(extracted_dir(knowledge_dir), env=env)}")
    else:
        operations.append(f"relocate:{relative_to_atlas(raw_dir(knowledge_dir), env=env)}")
        if folder_materializes_extracted:
            operations.append(f"materialize-extracted:{relative_to_atlas(extracted_dir(knowledge_dir), env=env)}")
    operations.append(f"write:{relative_to_atlas(manifest_path(knowledge_dir), env=env)}")

    if not dry_run:
        # Destructive delete-then-recreate is preserved only for the
        # paths that have no preflight to bypass (zip, legacy double
        # copy) -- exactly their pre-S2A behavior. The storage-convergence
        # folder path never reaches here with force=True on a completed
        # archive (refused above); on an incomplete prior attempt it must
        # NOT be deleted -- relocate_archive_source() resumes into it
        # safely (see the comment above archive_previously_completed).
        if knowledge_dir.exists() and force and not new_engine_folder_path:
            shutil.rmtree(knowledge_dir)
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        if detected_type == "zip":
            raw_dir(knowledge_dir).mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, raw_dir(knowledge_dir) / input_path.name)
            extract_zip_safely(input_path, extracted_dir(knowledge_dir))
        elif legacy_folder_copy:
            copy_folder(input_path, raw_dir(knowledge_dir))
            copy_folder(input_path, extracted_dir(knowledge_dir))
        else:
            # Admission (ownership proven above) has already established
            # this call is entitled to write into knowledge_dir -- fresh,
            # or a validated matching resume -- before any destructive
            # mutation happens. What remains, in order:
            #   required preflight -> create a fresh record safely, or
            #   reuse the matching one unchanged -> copy/resume
            if not reuse_existing_attempt:
                layout = _folder_relocation_layout(
                    archive_id=manifest["archive_id"], knowledge_dir=knowledge_dir, env=env
                )
                budget = storage.preflight_space_budget(
                    source_root=input_path,
                    raw_destination_root=raw_dir(knowledge_dir),
                    work_root=layout["work_root"],
                    extracted_destination_root=(
                        extracted_dir(knowledge_dir) if folder_materializes_extracted else None
                    ),
                    receipt_path=layout["receipt_path"],
                    expected_manifest_path=layout["expected_manifest_path"],
                )
                if not budget.ok:
                    # No attempt record published for a preflight that
                    # never passed -- nothing here to resume from, and
                    # nothing to leave behind that a later retry would
                    # need to reconcile against.
                    raise FolderImportRelocationError(
                        f"folder import preflight failed for {manifest['archive_id']}: "
                        f"findings={list(budget.findings)}"
                    )
                # Published only now, after preflight passed and before
                # any byte of the copy starts -- so a *future* retry has
                # a durable, matching record to validate against no
                # matter where the copy itself is interrupted. Uses
                # storage's own confined atomic writer (mkstemp staging,
                # no-follow rename), the same machinery S1 built for
                # every other authority-bearing write in this system --
                # not a new one, and never the plain write_json() a
                # pre-planted symlink at this path could be written
                # through.
                storage._write_json_atomic(
                    {
                        "contract_version": ATTEMPT_RECORD_CONTRACT_VERSION,
                        "archive_id": manifest["archive_id"],
                        "destination": relative_to_atlas(knowledge_dir, env=env),
                        "source_snapshot_digest": source_snapshot_digest_value,
                        "materialize_extracted": folder_materializes_extracted,
                        "recorded_at": utc_now(),
                    },
                    attempt_record_path,
                )
            # else: existing_attempt already matches this request exactly
            # -- reused as-is. Rewriting a record that already says the
            # right thing is a needless risk, not a refresh: interrupted
            # mid-write, a plain (non-atomic) rewrite would have torn the
            # one piece of evidence a later retry depends on.
            manifest["raw_relocation"] = _relocate_folder_import(
                archive_id=manifest["archive_id"],
                input_path=input_path,
                knowledge_dir=knowledge_dir,
                materialize_extracted=folder_materializes_extracted,
                env=env,
            )
            manifest["raw_entries"] = build_raw_entries(raw_dir(knowledge_dir))
        manifest["artifact_digests"] = build_manifest_artifact_digests(manifest, knowledge_dir, env=env)
        manifest["extracted_snapshot_digest"] = extracted_snapshot_digest(knowledge_dir)
        if not extracted_dir(knowledge_dir).exists():
            manifest["raw_snapshot_digest"] = tree_digest(raw_dir(knowledge_dir))
        write_json(manifest_path(knowledge_dir), manifest, dry_run=False)
        write_knowledge_receipt(
            archive_path=knowledge_dir,
            action="import",
            validation_results=None,
            dry_run=False,
            env=env,
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
        "import_dir": relative_to_atlas(knowledge_dir, env=env),
        "manifest": manifest,
        "planned_operations": operations,
    }


def evaluate_archive(*, archive_path: Path, dry_run: bool) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    manifest = read_json(manifest_path(archive_path))
    review_dir = review_source_dir(archive_path, manifest)
    paths = list_files(review_dir)
    text_paths = iter_text_files(paths)
    private_hits = match_patterns(paths, PRIVATE_PATTERNS)
    secrets_hits = scan_secret_risk(paths=paths)
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
        "review_source_kind": "extracted" if review_dir == extracted_dir(archive_path) else "raw",
        "review_source_digest": tree_digest(review_dir),
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
    refresh_derived: bool,
    dry_run: bool,
) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    manifest = read_json(manifest_path(archive_path))
    report = read_json(evaluation_path(archive_path))
    if not report.get("promotion_allowed", False):
        if not dry_run:
            write_knowledge_receipt(
                archive_path=archive_path,
                action="promote",
                validation_results=None,
                promotion_blocked=True,
                promotion_block_reason="Evaluation kept the archive quarantined from promotion.",
                dry_run=False,
            )
        raise ValueError("This archive cannot be promoted because evaluation kept it quarantined.")
    chosen_profile = indexing_profile or "derived_only"
    if chosen_profile not in INDEXING_PROFILES:
        raise ValueError(f"Unsupported indexing profile: {chosen_profile}")
    if (
        chosen_profile == "full_text"
        and (
            report.get("safe_for_indexing") != "yes"
            or manifest.get("privacy_flag") != "shareable"
        )
    ):
        raise ValueError(
            "full_text promotion is allowed only for shareable archives whose evaluation returned safe_for_indexing = yes."
        )
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
        refresh_derived=refresh_derived,
    )
    evidence_secret_hits = scan_secret_risk(paths=list_files(review_source_dir(archive_path, manifest)))
    candidate_secret_hits = scan_secret_risk(
        inline_documents=[(relative_to_atlas(promotion_file), rendered)]
    )
    if evidence_secret_hits or candidate_secret_hits:
        block_reason = "Promotion blocked because the imported evidence or candidate promotion markdown failed secret scanning."
        if not dry_run:
            write_knowledge_receipt(
                archive_path=archive_path,
                action="promote",
                validation_results={
                    "status": "blocked",
                    "findings": {
                        "imported_evidence_secret_hits": evidence_secret_hits,
                        "candidate_promotion_secret_hits": candidate_secret_hits,
                    },
                },
                promotion_blocked=True,
                promotion_block_reason=block_reason,
                dry_run=False,
            )
        raise ValueError(block_reason)
    if not dry_run:
        promotions_dir().mkdir(parents=True, exist_ok=True)
        if existing_text != rendered:
            promotion_file.write_text(rendered, encoding="utf-8")

    promotion = read_promotion_doc(promotion_file) if not dry_run else None
    manifest_last_reviewed_at = (
        utc_now()
        if (
            manifest.get("indexing_profile") != chosen_profile
            or manifest.get("promotion_status") != promotion_status
            or manifest.get("retention_class") != chosen_retention
            or existing_text != rendered
        )
        else str(manifest.get("last_reviewed_at", utc_now()))
    )
    manifest = update_manifest(
        archive_path,
        {
            "indexing_profile": chosen_profile,
            "promotion_status": promotion_status,
            "retention_class": chosen_retention,
            "pipeline_version": PIPELINE_VERSION,
            "last_reviewed_at": manifest_last_reviewed_at,
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
        "refresh_derived": refresh_derived,
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


class DuplicateArchiveIdentityError(RuntimeError):
    """The same archive_id (the manifest's own declared identity, not just
    the directory names it happens to sit under) exists as a real, distinct
    manifest under two different roots discover_import_manifests() scanned.
    Silently preferring one would hide the other from every downstream
    consumer (catalog, validation, backfill, ranking) without any record
    that it happened. Refused instead -- an operator must resolve the
    collision explicitly (this never moves or deletes anything itself)."""


class ArchiveIdentityLayoutMismatchError(RuntimeError):
    """A manifest's own declared identity (source_name/slug, slugified)
    does not match the directory layout discover_import_manifests() found
    it under. archive_dir()/source_dir() guarantee this always agrees for
    anything this pipeline itself wrote; disagreement means the manifest or
    its containing directories were edited or moved out of band, and
    trusting either side over the other (directory layout for dedup, or
    the manifest's declared archive_id for identity) without checking the
    other could let a tampered or relocated manifest silently collide with,
    or shadow, a different archive. Refused instead -- nothing is renamed,
    moved, or chosen on the caller's behalf."""


class IncompleteDiscoveryError(RuntimeError):
    """A root discover_import_manifests() scanned could not be proven
    fully enumerated, so the manifest list it would otherwise return
    cannot be trusted as complete. Two distinct situations raise this:
    (1) the EXPLICITLY configured import storage root
    (ATLAS_IMPORT_STORAGE_ROOT) is missing or not a directory -- its
    absence might mean real content is simply unreachable, not that
    nothing was ever imported there; (2) a root that DOES exist (the
    configured root OR the legacy default location) cannot be fully
    scanned -- an unreadable subdirectory, a permission error, or any
    other OSError partway through enumeration. The second case applies
    to every root that is actually present, not only the configured one:
    an inaccessible legacy tree must not quietly present as "nothing
    more to find" either. Letting a partial inventory stand in for a
    complete one would silently drop real archives from catalog,
    validation, backfill, and promotion-ranking tooling with no record
    that anything was missed -- exactly the failure mode a configuration
    change (not a real migration) must never cause. Raised instead of
    returning a partial list. A caller that only needs a best-effort,
    read-only snapshot (diagnostics, not authoritative publication) may
    pass allow_partial=True to opt out. The narrower "missing entirely"
    case never applies to an unconfigured default root that simply has
    not been created yet (the normal, first-use case), since then there
    is nothing "configured" to be unavailable."""


def _storage_root_is_explicitly_configured(*, env: dict[str, str] | None = None) -> bool:
    source = env if env is not None else os.environ
    return bool(source.get(storage._STORAGE_ROOT_ENV, "").strip())


def _scan_subdirectories(path: Path) -> list[Path]:
    """A single directory level's immediate subdirectories, sorted by
    name, raising OSError normally on failure.

    Deliberately os.scandir(), not Path.iterdir()/Path.glob(): pathlib's
    glob() silently swallows an OSError raised while descending into an
    unreadable subdirectory (documented CPython behavior, confirmed
    against the exact Python version this project's hosted CI runs) --
    a whole subtree can vanish from a glob() result with no signal at
    all, which is exactly the failure IncompleteDiscoveryError exists to
    prevent. os.scandir() raises immediately if `path` itself can't be
    opened, and iterating it raises normally on a later entry-level
    failure too -- neither is caught here, so a caller's own try/except
    OSError sees it."""
    with os.scandir(path) as entries:
        return sorted(
            (Path(entry.path) for entry in entries if entry.is_dir(follow_symlinks=False)),
            key=lambda p: p.name,
        )


def _list_import_manifests(root: Path) -> list[Path]:
    """Bounded, error-propagating enumeration of root's known three-level
    layout: root / source_dir / archive_dir / IMPORT-MANIFEST.json.

    Deliberately NOT a recursive walk -- archive payloads (raw/,
    extracted/) can be arbitrarily large and deep, and discovery only
    needs the manifest layout two levels below root, not another pass
    over every file inside every archive."""
    manifests: list[Path] = []
    for source_dir in _scan_subdirectories(root):
        for archive_dir in _scan_subdirectories(source_dir):
            candidate = archive_dir / "IMPORT-MANIFEST.json"
            if candidate.is_file():
                manifests.append(candidate)
    return manifests


def discover_import_manifests(*, allow_partial: bool = False) -> list[Path]:
    """Enumerate every IMPORT-MANIFEST.json this ATLAS installation knows
    about.

    Reads BOTH the configured storage root (storage.import_storage_root())
    and the legacy default location
    (atlas_root()/data/imports/knowledge) whenever they differ.
    ATLAS_IMPORT_STORAGE_ROOT changes where NEW archives are written; it
    must never make an archive already sitting at the previous default
    location invisible to discovery, since nothing has actually migrated
    it there -- doing so would let a configuration change silently drop
    existing entries from the catalog, validation, backfill, and
    promotion-ranking tooling that all consume this list. When the two
    roots are the same physical location (the common, unconfigured
    case), only one is scanned -- exactly the previous, single-root
    behavior, proven unchanged by the existing test suite.

    A missing/unconfigured default root is a normal, empty first-use
    inventory, not an error. But an EXPLICITLY configured root
    (ATLAS_IMPORT_STORAGE_ROOT set) that is missing or not a directory is
    different: its absence might mean real content is simply unreachable
    rather than genuinely never having existed, so the list this function
    would otherwise return cannot be proven complete. Separately, ANY
    root that DOES exist -- configured or legacy -- but cannot be fully
    scanned (an unreadable subdirectory, or any other OSError partway
    through enumeration) is always incomplete, regardless of which root
    it is: an inaccessible legacy tree must not quietly present as
    "nothing more to find" either. IncompleteDiscoveryError is raised in
    either case instead of silently returning a partial list -- unless
    allow_partial=True, for read-only diagnostics that only want a
    best-effort snapshot rather than an authoritative inventory. The
    granularity of that best-effort view is per ROOT, not per
    subdirectory: a scan failure anywhere inside a root discards
    whatever that same root had already found (nothing under a root
    that could not be fully trusted is reported), but a fully readable
    sibling root is still scanned and returned normally.

    Identity is the manifest's OWN declared (source_name, slug) --
    slugified, exactly as source_dir()/archive_dir() derive it -- not the
    literal directory names discover_import_manifests() happened to find
    it under; those two must always agree for anything this pipeline
    itself wrote, and ArchiveIdentityLayoutMismatchError is raised if they
    do not. If two different roots each hold a manifest claiming the same
    resulting archive_id, that is a genuine collision, not something safe
    to resolve by silently preferring one -- DuplicateArchiveIdentityError
    is raised instead.
    """
    configured_root = storage.import_storage_root()
    legacy_root = atlas_root() / "data" / "imports" / "knowledge"
    same_physical_root = legacy_root.resolve() == configured_root.resolve()
    roots = [configured_root]
    if not same_physical_root:
        roots.append(legacy_root)
    explicitly_configured = _storage_root_is_explicitly_configured()

    by_identity: dict[str, Path] = {}
    manifests: list[Path] = []
    for root in roots:
        is_configured_root = root == configured_root
        missing_root_is_fatal = is_configured_root and explicitly_configured and not allow_partial
        unreadable_root_is_fatal = not allow_partial
        if not root.exists():
            if missing_root_is_fatal:
                raise IncompleteDiscoveryError(
                    f"configured import storage root {root} does not exist; "
                    f"discovery cannot be proven complete"
                )
            continue
        if not root.is_dir():
            if missing_root_is_fatal:
                raise IncompleteDiscoveryError(
                    f"configured import storage root {root} is not a directory; "
                    f"discovery cannot be proven complete"
                )
            continue
        try:
            found = sorted(_list_import_manifests(root))
        except OSError as exc:
            if unreadable_root_is_fatal:
                raise IncompleteDiscoveryError(
                    f"import storage root {root} exists but could not be fully "
                    f"enumerated: {exc}"
                ) from exc
            continue
        for manifest_file in found:
            source_dir_name = manifest_file.parent.parent.name
            slug_dir_name = manifest_file.parent.name
            manifest = read_json(manifest_file)
            source_name = manifest.get("source_name")
            slug = manifest.get("slug")
            archive_id = manifest.get("archive_id")
            if (
                not isinstance(source_name, str)
                or not isinstance(slug, str)
                or not isinstance(archive_id, str)
                or slugify(source_name) != source_dir_name
                or slugify(slug) != slug_dir_name
            ):
                raise ArchiveIdentityLayoutMismatchError(
                    f"{manifest_file} declares source_name={source_name!r} slug={slug!r} "
                    f"archive_id={archive_id!r}, which does not match its directory "
                    f"layout ({source_dir_name}/{slug_dir_name})"
                )
            existing = by_identity.get(archive_id)
            if existing is not None:
                if existing.resolve() == manifest_file.resolve():
                    continue  # the same physical file, reached via both roots
                raise DuplicateArchiveIdentityError(
                    f"archive_id {archive_id!r} exists at both {existing} and {manifest_file}"
                )
            by_identity[archive_id] = manifest_file
            manifests.append(manifest_file)
    return sorted(manifests)


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


def validate_catalog(*, include_query_bundle: bool = True) -> dict[str, Any]:
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
                if manifest.get("promotion_status") != promotion["metadata"]["promotion_status"]:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(manifest_file),
                            "message": "Manifest promotion_status must match the promotion doc.",
                        }
                    )
                if manifest.get("indexing_profile") != promotion["metadata"]["indexing_profile"]:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(manifest_file),
                            "message": "Manifest indexing_profile must match the promotion doc.",
                        }
                    )
                if (
                    promotion["metadata"]["promotion_status"] == "promoted"
                    and is_promotion_summary_scaffold(
                        archive_id,
                        promotion["sections"]["Derived Summary"],
                    )
                ):
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(promotion_file),
                            "message": "Promotion docs marked promoted must replace the scaffold-derived summary with human-authored content.",
                        }
                    )
                if (
                    promotion["metadata"]["indexing_profile"] == "full_text"
                    and (
                        manifest.get("privacy_flag") != "shareable"
                        or evaluation is None
                        or evaluation.get("safe_for_indexing") != "yes"
                    )
                ):
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(promotion_file),
                            "message": "full_text promotion is only valid for shareable archives whose evaluation returned safe_for_indexing = yes.",
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
                if normalized.get("promotion_status") != promotion["metadata"]["promotion_status"]:
                    findings.append(
                        {
                            "severity": "error",
                            "path": relative_to_atlas(normalized_file),
                            "message": "Runtime catalog promotion_status must match the promotion doc when a promotion doc exists.",
                        }
                    )

        latest_receipt = latest_receipt_path(archive_id)
        if not latest_receipt.exists():
            findings.append(
                {
                    "severity": "error",
                    "path": relative_to_atlas(receipt_dir(archive_id)),
                    "message": "Latest knowledge receipt is missing for this archive.",
                }
            )
        else:
            receipt = read_json(latest_receipt)
            required_receipt = [
                "receipt_version",
                "receipt_id",
                "recorded_at",
                "pipeline_version",
                "archive_id",
                "action",
                "paths",
                "inputs",
                "digests",
                "no_execute_guarantee",
                "evaluation",
                "promotion",
                "runtime_outputs",
                "validation_results",
                "tooling",
            ]
            missing_receipt = [field for field in required_receipt if field not in receipt]
            if missing_receipt:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": f"Latest receipt is missing required fields: {', '.join(missing_receipt)}",
                    }
                )
            if receipt.get("receipt_version") != RECEIPT_VERSION:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": f"Receipt receipt_version must be '{RECEIPT_VERSION}'.",
                    }
                )
            if receipt.get("pipeline_version") != PIPELINE_VERSION:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": f"Receipt pipeline_version must be '{PIPELINE_VERSION}'.",
                    }
                )
            if receipt.get("archive_id") != archive_id:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt archive_id does not match the manifest archive_id.",
                    }
                )

            receipt_paths = receipt.get("paths") if isinstance(receipt.get("paths"), dict) else {}
            if receipt_paths.get("latest_path") != relative_to_atlas(latest_receipt):
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt paths.latest_path does not match the stored latest.json location.",
                    }
                )
            if receipt_paths.get("manifest_path") != relative_to_atlas(manifest_file):
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt paths.manifest_path does not match the manifest location.",
                    }
                )

            receipt_digests = receipt.get("digests") if isinstance(receipt.get("digests"), dict) else {}
            expected_manifest_digest = file_checksum(manifest_file)
            if receipt_digests.get("manifest") != expected_manifest_digest:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt manifest digest is stale or missing.",
                    }
                )
            expected_evaluation_digest = file_checksum_if_exists(evaluation_file)
            if receipt_digests.get("evaluation") != expected_evaluation_digest:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt evaluation digest is stale or missing.",
                    }
                )
            expected_runtime_digest = file_checksum_if_exists(normalized_file)
            if receipt_digests.get("runtime_catalog") != expected_runtime_digest:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt runtime catalog digest is stale or missing.",
                    }
                )
            expected_promotion_digest = promotion["digest"] if promotion is not None else file_checksum_if_exists(promotion_file)
            if receipt_digests.get("promotion_doc") != expected_promotion_digest:
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt promotion doc digest is stale or missing.",
                    }
                )

            tooling = receipt.get("tooling") if isinstance(receipt.get("tooling"), dict) else {}
            if tooling.get("pipeline_digest") != file_checksum(Path(__file__).resolve()):
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt tooling.pipeline_digest is stale or missing.",
                    }
                )
            entrypoint = receipt_entrypoint_path(str(receipt.get("action")))
            if entrypoint is not None and tooling.get("entrypoint_digest") != file_checksum_if_exists(entrypoint):
                findings.append(
                    {
                        "severity": "error",
                        "path": relative_to_atlas(latest_receipt),
                        "message": "Latest receipt tooling.entrypoint_digest is stale or missing.",
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

    if include_query_bundle:
        findings.extend(validate_query_bundle())

    return {
        "generated_at": utc_now(),
        "catalog_path": relative_to_atlas(catalog_path_value),
        "query_bundle_path": relative_to_atlas(knowledge_query_bundle_path()),
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
