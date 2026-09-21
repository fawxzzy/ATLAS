from __future__ import annotations

"""Deterministic metadata-only inventory of two pinned committed-text corpora."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import quote

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ops.atlas.ui_standards.validate import validate_json_schema


SCHEMA_VERSION = "atlas.text-corpus.inventory.v1"
GENERATOR_VERSION = "atlas.text-corpus.inventory.generator.v1"
INVENTORY_ID = "atlas-playbook-committed-text-pilot-v1"
UNKNOWN = "UNKNOWN"
COUNT_FIELDS = ("total", "included", "excluded", "unknown", "exclusion_reasons")
UNKNOWN_REASON_CODES = frozenset({"SOURCE_PATH_UNAVAILABLE"})

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_OID_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
REASON_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

SCHEMA_PATH = Path("schemas/atlas.text-corpus.inventory.v1.json")
INDEX_PATH = Path("docs/registry/text-corpus/ATLAS-TEXT-CORPUS-INDEX.v1.json")
COMPONENT_PATHS = {
    "atlas-root": Path("docs/registry/text-corpus/components/atlas-root.v1.json"),
    "playbook": Path("docs/registry/text-corpus/components/playbook.v1.json"),
}

CONFIGURATION_MEDIA_TYPES = {
    ".cfg": "text/plain",
    ".conf": "text/plain",
    ".editorconfig": "text/plain",
    ".gitattributes": "text/plain",
    ".gitignore": "text/plain",
    ".ini": "text/plain",
    ".json": "application/json",
    ".jsonc": "application/json",
    ".lock": "text/plain",
    ".npmrc": "text/plain",
    ".nvmrc": "text/plain",
    ".prisma": "text/plain",
    ".properties": "text/plain",
    ".toml": "application/toml",
    ".txt": "text/plain",
    ".xml": "application/xml",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
}

TEXT_MEDIA_TYPES = {
    **CONFIGURATION_MEDIA_TYPES,
    ".adoc": "text/asciidoc",
    ".bash": "text/x-shellscript",
    ".bat": "text/x-msdos-batch",
    ".c": "text/x-c",
    ".cjs": "text/javascript",
    ".cmd": "text/x-msdos-batch",
    ".cpp": "text/x-c++",
    ".cs": "text/x-csharp",
    ".css": "text/css",
    ".csv": "text/csv",
    ".gql": "application/graphql",
    ".go": "text/x-go",
    ".graphql": "application/graphql",
    ".h": "text/x-c",
    ".hpp": "text/x-c++",
    ".htm": "text/html",
    ".html": "text/html",
    ".java": "text/x-java-source",
    ".js": "text/javascript",
    ".jsx": "text/jsx",
    ".kt": "text/x-kotlin",
    ".kts": "text/x-kotlin",
    ".less": "text/css",
    ".md": "text/markdown",
    ".mdx": "text/markdown",
    ".mjs": "text/javascript",
    ".proto": "text/x-protobuf",
    ".ps1": "text/x-powershell",
    ".py": "text/x-python",
    ".rst": "text/x-rst",
    ".rs": "text/x-rust",
    ".scss": "text/css",
    ".sh": "text/x-shellscript",
    ".sql": "application/sql",
    ".svelte": "text/plain",
    ".svg": "image/svg+xml",
    ".swift": "text/x-swift",
    ".ts": "text/typescript",
    ".tsx": "text/tsx",
    ".vue": "text/plain",
}

SPECIAL_TEXT_NAMES = {
    "agents.md": "text/markdown",
    "changelog": "text/plain",
    "changelog.md": "text/markdown",
    "codelist": "text/plain",
    "codeowners": "text/plain",
    "cmakelists.txt": "text/plain",
    "contributing": "text/plain",
    "dockerfile": "text/plain",
    "gemfile": "text/plain",
    "license": "text/plain",
    "makefile": "text/plain",
    "notice": "text/plain",
    "procfile": "text/plain",
    "rakefile": "text/plain",
    "readme": "text/plain",
}

SECRET_SEGMENTS = {"secret", "secrets"}
SECRET_NAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "secrets.json",
    "token",
    "tokens.json",
}
SECRET_STEMS = {"credential", "credentials", "secret", "secrets", "token", "tokens"}
SECRET_MANIFEST_SUFFIXES = frozenset(CONFIGURATION_MEDIA_TYPES)
SECRET_SUFFIXES = {".asc", ".der", ".key", ".p12", ".pem", ".pfx"}
RUNTIME_SEGMENTS = {".codex", ".playbook", "runtime", "tmp"}
DEPENDENCY_SEGMENTS = {
    ".pnpm",
    ".venv",
    "bower_components",
    "node_modules",
    "site-packages",
    "third_party",
    "vendor",
}
BUILD_SEGMENTS = {
    ".cache",
    ".next",
    ".parcel-cache",
    ".turbo",
    "build",
    "coverage",
    "dist",
    "generated",
    "out",
    "playwright-report",
    "target",
    "test-results",
}
PRIVATE_SEGMENTS = {
    ".chatgpt",
    "archive",
    "archives",
    "backups",
    "chat-history",
    "codex-history",
    "conversations",
    "private",
    "transcripts",
}


class InventoryError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    component_id: str
    repository_owner: str
    repository_name: str
    pinned_commit: str
    authority_tier: str
    expected_remote: str | None = None

    @property
    def repository_ref(self) -> str:
        return f"github:{self.repository_owner}/{self.repository_name}"


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    object_type: str
    oid: str
    byte_size: int | None
    relative_path: str


PINNED_SOURCE_SPECS = (
    SourceSpec(
        source_id="github:fawxzzy/ATLAS",
        component_id="atlas-root",
        repository_owner="fawxzzy",
        repository_name="ATLAS",
        pinned_commit="78a906240cf6c8a5fc1967cbf9d797df62cfa1f5",
        authority_tier="atlas_inventory_adoption_owner",
        expected_remote="github.com/fawxzzy/atlas",
    ),
    SourceSpec(
        source_id="github:fawxzzy/playbook",
        component_id="playbook",
        repository_owner="fawxzzy",
        repository_name="playbook",
        pinned_commit="952b63aa6457d871024a224a089c4088490d69c5",
        authority_tier="playbook_doctrine_owner",
        expected_remote="github.com/fawxzzy/playbook",
    ),
)


def stable_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_value(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def sha256_bytes(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def validate_relative_path(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise InventoryError("INVALID_RELATIVE_PATH", f"Non-portable repository path: {value!r}")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise InventoryError("ABSOLUTE_PATH_REJECTED", f"Absolute repository path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise InventoryError("PATH_TRAVERSAL_REJECTED", f"Unsafe repository path: {value!r}")
    if path.as_posix() != value:
        raise InventoryError("INVALID_RELATIVE_PATH", f"Non-canonical repository path: {value!r}")
    return value


def resolve_real_path(path: Path, *, allow_missing_leaf: bool = False) -> Path:
    if not allow_missing_leaf:
        return path.resolve(strict=True)
    probe = path
    suffix: list[str] = []
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            raise FileNotFoundError(path)
        suffix.append(probe.name)
        probe = parent
    resolved = probe.resolve(strict=True)
    for part in reversed(suffix):
        resolved = resolved / part
    return resolved


def ensure_resolved_contained(root: Path, candidate: Path) -> Path:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise InventoryError(
            "RESOLVED_PATH_ESCAPE",
            f"Resolved output path escapes the admitted workspace: {candidate}",
        ) from exc
    return candidate


def validate_output_root(workspace_root: Path, output_root: Path) -> tuple[Path, Path]:
    workspace_real = resolve_real_path(workspace_root)
    output_real = resolve_real_path(output_root, allow_missing_leaf=True)
    ensure_resolved_contained(workspace_real, output_real)
    return workspace_real, output_real


def git_read_env() -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_NO_LAZY_FETCH"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "--no-replace-objects", *args],
        check=False,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
        env=git_read_env(),
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace") if binary else completed.stderr
        raise InventoryError(
            "GIT_SOURCE_UNAVAILABLE",
            (stderr or "Pinned Git source is unavailable.").strip(),
        )
    return completed.stdout


def _normalize_remote(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    if normalized.startswith("git@github.com:"):
        normalized = "github.com/" + normalized.split(":", 1)[1]
    else:
        normalized = re.sub(r"^(?:https?|ssh|git)://(?:git@)?", "", normalized)
    return normalized.removesuffix(".git").rstrip("/").lower()


def _verify_remote(repo: Path, spec: SourceSpec) -> None:
    if spec.expected_remote is None:
        return
    actual = str(_git(repo, "remote", "get-url", "origin")).strip()
    if _normalize_remote(actual) != spec.expected_remote.lower():
        raise InventoryError(
            "AMBIGUOUS_REPOSITORY_ROOT",
            f"{spec.component_id} origin does not match {spec.expected_remote}.",
        )


def list_tree_entries(repo: Path, commit: str) -> tuple[str, list[TreeEntry]]:
    resolved_commit = str(_git(repo, "rev-parse", f"{commit}^{{commit}}")).strip()
    if resolved_commit != commit:
        raise InventoryError("PIN_MISMATCH", f"Expected {commit}, resolved {resolved_commit}.")
    tree_oid = str(_git(repo, "rev-parse", f"{commit}^{{tree}}")).strip()
    raw = _git(repo, "ls-tree", "-r", "-z", "--full-tree", "--long", commit, binary=True)
    assert isinstance(raw, bytes)
    entries: list[TreeEntry] = []
    seen_paths: set[str] = set()
    for encoded_entry in raw.split(b"\x00"):
        if not encoded_entry:
            continue
        try:
            metadata_raw, path_raw = encoded_entry.split(b"\t", 1)
            mode, object_type, oid, size_text = metadata_raw.decode("ascii").split()
            relative_path = path_raw.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise InventoryError("MALFORMED_TREE_ENTRY", "Git tree entry is not portable UTF-8 metadata.") from exc
        validate_relative_path(relative_path)
        if relative_path in seen_paths:
            raise InventoryError("DUPLICATE_RECORD_IDENTITY", f"Duplicate tree path: {relative_path}")
        seen_paths.add(relative_path)
        if size_text == "-":
            byte_size = None
        elif size_text == "BAD":
            raise InventoryError("GIT_BLOB_UNAVAILABLE", f"Git object size is unavailable for {relative_path} ({oid}).")
        else:
            try:
                byte_size = int(size_text)
            except ValueError as exc:
                raise InventoryError("MALFORMED_TREE_ENTRY", f"Git object size is malformed for {relative_path}.") from exc
        entries.append(
            TreeEntry(
                mode=mode,
                object_type=object_type,
                oid=oid,
                byte_size=byte_size,
                relative_path=relative_path,
            )
        )
    entries.sort(key=lambda item: item.relative_path)
    return tree_oid, entries


def batch_read_blobs(repo: Path, oids: Iterable[str]) -> dict[str, bytes]:
    ordered = sorted(set(oids))
    if not ordered:
        return {}
    process = subprocess.Popen(
        ["git", "-C", str(repo), "--no-replace-objects", "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=git_read_env(),
    )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    try:
        blobs: dict[str, bytes] = {}
        for requested_oid in ordered:
            # Interleave each request and response. Writing the entire request set
            # first can deadlock once both OS pipe buffers fill on large corpora.
            process.stdin.write(f"{requested_oid}\n".encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().rstrip(b"\n")
            parts = header.split()
            if len(parts) != 3 or parts[1] != b"blob":
                raise InventoryError("GIT_BLOB_UNAVAILABLE", f"Unable to read Git blob {requested_oid}: {header!r}")
            actual_oid = parts[0].decode("ascii")
            size = int(parts[2])
            content = process.stdout.read(size)
            terminator = process.stdout.read(1)
            if len(content) != size or terminator != b"\n":
                raise InventoryError("GIT_BLOB_UNAVAILABLE", f"Truncated Git blob {requested_oid}.")
            blobs[requested_oid] = content
            if actual_oid != requested_oid:
                raise InventoryError("BLOB_DIGEST_MISMATCH", f"Git returned {actual_oid} for {requested_oid}.")
        process.stdin.close()
        return_code = process.wait()
        stderr = process.stderr.read().decode("utf-8", errors="replace").strip()
        if return_code != 0:
            raise InventoryError("GIT_BLOB_UNAVAILABLE", stderr or "git cat-file --batch failed.")
        return blobs
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
        process.stderr.close()


def verify_git_blob_id(oid: str, raw: bytes) -> None:
    if len(oid) == 40:
        digest = hashlib.sha1()  # noqa: S324 - Git SHA-1 object identity, not a security decision.
    elif len(oid) == 64:
        digest = hashlib.sha256()
    else:
        raise InventoryError("MALFORMED_TREE_ENTRY", f"Unsupported Git object ID length: {oid}")
    digest.update(f"blob {len(raw)}\x00".encode("ascii"))
    digest.update(raw)
    if digest.hexdigest() != oid:
        raise InventoryError("BLOB_DIGEST_MISMATCH", f"Git blob content does not match {oid}.")


def text_media_type(relative_path: str) -> str | None:
    name = PurePosixPath(relative_path).name.lower()
    if name in SPECIAL_TEXT_NAMES:
        return SPECIAL_TEXT_NAMES[name]
    suffix = PurePosixPath(name).suffix.lower()
    return TEXT_MEDIA_TYPES.get(suffix)


def path_exclusion(entry: TreeEntry) -> tuple[str, str] | None:
    if entry.mode == "120000":
        return "SYMLINK_ENTRY", "internal"
    if entry.mode == "160000" or entry.object_type == "commit":
        return "GITLINK_ENTRY", "internal"
    if entry.object_type != "blob" or entry.mode not in {"100644", "100755"}:
        return "UNSUPPORTED_GIT_OBJECT", "internal"
    path = PurePosixPath(entry.relative_path)
    parts = tuple(part.lower() for part in path.parts)
    secret_parts = tuple(part[1:] if part.startswith(".") else part for part in parts)
    name = parts[-1]
    secret_stem = name.lstrip(".").split(".", 1)[0]
    if (
        any(part in SECRET_SEGMENTS for part in secret_parts)
        or name.startswith(".env")
        or name in SECRET_NAMES
        or (secret_stem in SECRET_STEMS and path.suffix.lower() in SECRET_MANIFEST_SUFFIXES)
        or path.suffix.lower() in SECRET_SUFFIXES
    ):
        return "SECRET_SURFACE", "restricted"
    if any(part in RUNTIME_SEGMENTS for part in parts):
        return "MUTABLE_RUNTIME_SURFACE", "restricted"
    if any(part in DEPENDENCY_SEGMENTS for part in parts):
        return "DEPENDENCY_OR_VENDOR_TREE", "internal"
    if any(part in BUILD_SEGMENTS for part in parts) or ".generated." in name:
        return "GENERATED_OR_BUILD_TREE", "internal"
    if any(part in PRIVATE_SEGMENTS for part in parts):
        return "PRIVATE_OR_TRANSCRIPT_SURFACE", "restricted"
    if text_media_type(entry.relative_path) is None:
        return "UNSUPPORTED_MEDIA_TYPE", "internal"
    return None


def source_class(relative_path: str, *, restricted: bool = False) -> str:
    if restricted:
        return "restricted_surface"
    first = PurePosixPath(relative_path).parts[0].lower()
    if first == "docs":
        return "documentation"
    if first == "schemas":
        return "schema"
    if first in {"test", "tests", "__tests__"}:
        return "test"
    if first in {"ops", "packages", "scripts", "src"}:
        return "source_code"
    if first == ".github":
        return "automation"
    if first == "data":
        return "data"
    if len(PurePosixPath(relative_path).parts) == 1:
        return "governance_config"
    return "text_artifact"


def record_id(spec: SourceSpec, relative_path: str) -> str:
    seed = f"{SCHEMA_VERSION}\x00{spec.source_id}\x00{relative_path}".encode("utf-8")
    return f"sha256:{hashlib.sha256(seed).hexdigest()}"


def provenance_ref(spec: SourceSpec, entry: TreeEntry) -> str:
    encoded_path = quote(entry.relative_path, safe="/._~-", encoding="utf-8", errors="strict")
    return f"{spec.repository_ref}@{spec.pinned_commit}:{encoded_path}#object={entry.oid}"


def base_record(
    spec: SourceSpec,
    entry: TreeEntry,
    *,
    disposition: str,
    reason: str,
    sha256: str = UNKNOWN,
    media_type: str = UNKNOWN,
    content_type: str = "not_applicable",
    privacy_class: str = "internal",
) -> dict[str, Any]:
    is_blob = entry.object_type == "blob"
    return {
        "record_id": record_id(spec, entry.relative_path),
        "source_id": spec.source_id,
        "component_id": spec.component_id,
        "repository_owner": spec.repository_owner,
        "repository_name": spec.repository_name,
        "relative_path": entry.relative_path,
        "pinned_commit": spec.pinned_commit,
        "git_object_id": entry.oid,
        "git_blob_id": entry.oid if is_blob else UNKNOWN,
        "sha256": sha256,
        "byte_size": entry.byte_size if entry.byte_size is not None else UNKNOWN,
        "media_type": media_type,
        "content_type": content_type,
        "source_class": source_class(entry.relative_path, restricted=privacy_class == "restricted"),
        "authority_tier": spec.authority_tier,
        "privacy_class": privacy_class,
        "indexing_profile": "metadata_and_digest" if disposition == "included" else "metadata_only_excluded",
        "lifecycle": {
            "status": "active_at_pinned_commit" if disposition == "included" else "excluded_at_pinned_commit",
            "supersedes": [],
            "superseded_by": [],
        },
        "disposition": disposition,
        "reason": reason,
        "provenance_ref": provenance_ref(spec, entry),
        "generator_version": GENERATOR_VERSION,
    }


def counts_for(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dispositions = Counter(str(record["disposition"]) for record in records)
    exclusions = Counter(
        str(record["reason"]) for record in records if record["disposition"] == "excluded"
    )
    return {
        "total": len(records),
        "included": dispositions["included"],
        "excluded": dispositions["excluded"],
        "unknown": dispositions[UNKNOWN],
        "exclusion_reasons": dict(sorted(exclusions.items())),
    }


def counts_are_all_unknown(counts: Any) -> bool:
    return isinstance(counts, dict) and all(counts.get(field) == UNKNOWN for field in COUNT_FIELDS)


def counts_are_concrete(counts: Any) -> bool:
    if not isinstance(counts, dict):
        return False
    for field in COUNT_FIELDS[:-1]:
        value = counts.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return False
    reasons = counts.get("exclusion_reasons")
    return isinstance(reasons, dict) and all(
        isinstance(key, str)
        and REASON_CODE_PATTERN.fullmatch(key) is not None
        and not isinstance(value, bool)
        and isinstance(value, int)
        and value >= 1
        for key, value in reasons.items()
    )


def source_payload(spec: SourceSpec, *, tree_oid: str, availability: str, unknown_reason: str | None) -> dict[str, Any]:
    return {
        "source_id": spec.source_id,
        "component_id": spec.component_id,
        "repository_owner": spec.repository_owner,
        "repository_name": spec.repository_name,
        "repository_ref": spec.repository_ref,
        "pinned_commit": spec.pinned_commit,
        "tree_oid": tree_oid,
        "authority_tier": spec.authority_tier,
        "availability": availability,
        "unknown_reason": unknown_reason,
    }


def unknown_component(spec: SourceSpec, reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA_VERSION,
        "document_kind": "component",
        "inventory_id": INVENTORY_ID,
        "generator_version": GENERATOR_VERSION,
        "source": source_payload(spec, tree_oid=UNKNOWN, availability=UNKNOWN, unknown_reason=reason),
        "counts": {
            "total": UNKNOWN,
            "included": UNKNOWN,
            "excluded": UNKNOWN,
            "unknown": UNKNOWN,
            "exclusion_reasons": UNKNOWN,
        },
        "component_digest": UNKNOWN,
        "records": [],
    }


def build_component(spec: SourceSpec, repo: Path) -> dict[str, Any]:
    _verify_remote(repo, spec)
    tree_oid, entries = list_tree_entries(repo, spec.pinned_commit)
    candidate_oids = [
        entry.oid
        for entry in entries
        if path_exclusion(entry) is None
    ]
    blobs = batch_read_blobs(repo, candidate_oids)
    records: list[dict[str, Any]] = []
    for entry in entries:
        excluded = path_exclusion(entry)
        if excluded is not None:
            reason, privacy_class = excluded
            records.append(
                base_record(
                    spec,
                    entry,
                    disposition="excluded",
                    reason=reason,
                    privacy_class=privacy_class,
                )
            )
            continue

        raw = blobs.get(entry.oid)
        if raw is None:
            raise InventoryError("GIT_BLOB_UNAVAILABLE", f"Missing candidate blob {entry.oid}.")
        if entry.byte_size != len(raw):
            raise InventoryError("BLOB_DIGEST_MISMATCH", f"Git tree size mismatch for {entry.relative_path}.")
        verify_git_blob_id(entry.oid, raw)
        media_type = text_media_type(entry.relative_path) or UNKNOWN
        if b"\x00" in raw:
            records.append(
                base_record(
                    spec,
                    entry,
                    disposition="excluded",
                    reason="BINARY_CONTENT",
                    media_type="application/octet-stream",
                    content_type="binary",
                )
            )
            continue
        try:
            raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            records.append(
                base_record(
                    spec,
                    entry,
                    disposition="excluded",
                    reason="NON_UTF8_TEXT",
                    media_type=media_type,
                    content_type="unknown",
                )
            )
            continue
        records.append(
            base_record(
                spec,
                entry,
                disposition="included",
                reason="COMMITTED_UTF8_TEXT",
                sha256=sha256_bytes(raw),
                media_type=media_type,
                content_type="text",
            )
        )

    counts = counts_for(records)
    source = source_payload(spec, tree_oid=tree_oid, availability="available", unknown_reason=None)
    component_digest = sha256_value({"source": source, "records": records})
    return {
        "schema": SCHEMA_VERSION,
        "document_kind": "component",
        "inventory_id": INVENTORY_ID,
        "generator_version": GENERATOR_VERSION,
        "source": source,
        "counts": counts,
        "component_digest": component_digest,
        "records": records,
    }


def component_summary(component: Mapping[str, Any]) -> dict[str, Any]:
    source = component["source"]
    component_id = str(source["component_id"])
    return {
        "source_id": source["source_id"],
        "component_id": component_id,
        "shard_ref": COMPONENT_PATHS[component_id].as_posix(),
        "pinned_commit": source["pinned_commit"],
        "tree_oid": source["tree_oid"],
        "authority_tier": source["authority_tier"],
        "availability": source["availability"],
        "unknown_reason": source["unknown_reason"],
        "counts": component["counts"],
        "component_digest": component["component_digest"],
    }


def build_index(components: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summaries = sorted((component_summary(component) for component in components), key=lambda item: item["component_id"])
    available = [item for item in summaries if item["availability"] == "available"]
    if len(available) == len(summaries):
        aggregate_counts = {
            "total": sum(int(item["counts"]["total"]) for item in summaries),
            "included": sum(int(item["counts"]["included"]) for item in summaries),
            "excluded": sum(int(item["counts"]["excluded"]) for item in summaries),
            "unknown": sum(int(item["counts"]["unknown"]) for item in summaries),
            "exclusion_reasons": dict(
                sorted(
                    sum(
                        (Counter(item["counts"]["exclusion_reasons"]) for item in summaries),
                        Counter(),
                    ).items()
                )
            ),
        }
        aggregate_digest = sha256_value(summaries)
    else:
        aggregate_counts = {
            "total": UNKNOWN,
            "included": UNKNOWN,
            "excluded": UNKNOWN,
            "unknown": UNKNOWN,
            "exclusion_reasons": UNKNOWN,
        }
        aggregate_digest = UNKNOWN
    return {
        "schema": SCHEMA_VERSION,
        "document_kind": "index",
        "inventory_id": INVENTORY_ID,
        "generator_version": GENERATOR_VERSION,
        "policy": {
            "source_basis": "committed_git_objects_only",
            "body_storage": "prohibited",
            "unavailable_semantics": UNKNOWN,
            "doctrine_owner": "playbook",
            "inventory_owner": "atlas",
            "authority_widening": False,
            "marker_movement": False,
        },
        "components": summaries,
        "aggregate": {
            "source_count": 2,
            "available_source_count": len(available),
            "counts": aggregate_counts,
            "aggregate_digest": aggregate_digest,
        },
    }


def validate_component_semantics(component: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    source = component.get("source", {})
    records = component.get("records", [])
    if not isinstance(source, dict) or not isinstance(records, list):
        return ["component source and records must be structured"]
    if not GIT_OID_PATTERN.fullmatch(str(source.get("pinned_commit", ""))):
        errors.append("component source pinned commit is malformed")
    if source.get("availability") == UNKNOWN:
        if source.get("tree_oid") != UNKNOWN or source.get("unknown_reason") not in UNKNOWN_REASON_CODES:
            errors.append("UNKNOWN component source must retain UNKNOWN tree_oid and a canonical unknown_reason")
        if records:
            errors.append("UNKNOWN component must not invent records")
        if component.get("component_digest") != UNKNOWN:
            errors.append("UNKNOWN component digest must remain UNKNOWN")
        counts = component.get("counts", {})
        if not counts_are_all_unknown(counts):
            errors.append("UNKNOWN component counts must remain UNKNOWN")
        return errors
    if source.get("availability") != "available":
        return [*errors, "component source availability is malformed"]
    if not GIT_OID_PATTERN.fullmatch(str(source.get("tree_oid", ""))):
        errors.append("component source tree OID is malformed")
    if source.get("unknown_reason") is not None:
        errors.append("available component source unknown_reason must be null")
    if not counts_are_concrete(component.get("counts")):
        errors.append("available component counts must remain concrete")
    if not SHA256_PATTERN.fullmatch(str(component.get("component_digest", ""))):
        errors.append("available component digest must remain concrete")
    paths = [record.get("relative_path") for record in records if isinstance(record, dict)]
    if paths != sorted(paths):
        errors.append("component records must be ordered by relative_path")
    record_ids = [record.get("record_id") for record in records if isinstance(record, dict)]
    if len(record_ids) != len(set(record_ids)) or len(paths) != len(set(paths)):
        errors.append("component contains duplicate record identity")
    for record in records:
        if not isinstance(record, dict):
            errors.append("component record must be an object")
            continue
        try:
            validate_relative_path(str(record.get("relative_path", "")))
        except InventoryError as exc:
            errors.append(str(exc))
        if record.get("source_id") != source.get("source_id") or record.get("component_id") != source.get("component_id"):
            errors.append("record source/component identity does not match shard")
        if record.get("pinned_commit") != source.get("pinned_commit"):
            errors.append("record pinned commit does not match shard")
        if not SHA256_PATTERN.fullmatch(str(record.get("record_id", ""))):
            errors.append("record identity digest is malformed")
        if not GIT_OID_PATTERN.fullmatch(str(record.get("git_object_id", ""))):
            errors.append("record Git object ID is malformed")
        if record.get("disposition") == "included":
            if not SHA256_PATTERN.fullmatch(str(record.get("sha256", ""))) or record.get("content_type") != "text":
                errors.append("included record lacks text digest proof")
            if not GIT_OID_PATTERN.fullmatch(str(record.get("git_blob_id", ""))):
                errors.append("included record Git blob ID is malformed")
        elif record.get("sha256") != UNKNOWN:
            errors.append("excluded or unknown record must not retain a content SHA-256")
    expected_counts = counts_for(records)
    if component.get("counts") != expected_counts:
        errors.append("component counts do not match records")
    expected_digest = sha256_value({"source": source, "records": records})
    if component.get("component_digest") != expected_digest:
        errors.append("component digest mismatch")
    return errors


def validate_index_semantics(index: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    components = index.get("components", [])
    if not isinstance(components, list):
        return ["index components must be an array"]
    component_ids = [item.get("component_id") for item in components if isinstance(item, dict)]
    if component_ids != ["atlas-root", "playbook"]:
        errors.append("index must contain exactly the atlas-root and playbook components in order")
    source_ids = [item.get("source_id") for item in components if isinstance(item, dict)]
    if len(source_ids) != len(set(source_ids)):
        errors.append("index contains duplicate source identity")
    available: list[Mapping[str, Any]] = []
    available_evidence_is_concrete = True
    for item in components:
        if not isinstance(item, dict):
            errors.append("index component summary must be an object")
            available_evidence_is_concrete = False
            continue
        if item.get("availability") == UNKNOWN:
            if (
                item.get("tree_oid") != UNKNOWN
                or item.get("unknown_reason") not in UNKNOWN_REASON_CODES
                or not counts_are_all_unknown(item.get("counts"))
                or item.get("component_digest") != UNKNOWN
            ):
                errors.append("UNKNOWN component summary evidence must remain UNKNOWN with a canonical reason")
        elif item.get("availability") == "available":
            available.append(item)
            item_is_concrete = (
                GIT_OID_PATTERN.fullmatch(str(item.get("tree_oid", ""))) is not None
                and item.get("unknown_reason") is None
                and counts_are_concrete(item.get("counts"))
                and SHA256_PATTERN.fullmatch(str(item.get("component_digest", ""))) is not None
            )
            if not item_is_concrete:
                errors.append("available component summary evidence must remain concrete with null unknown_reason")
                available_evidence_is_concrete = False
        else:
            errors.append("index component summary availability is malformed")
            available_evidence_is_concrete = False
    aggregate = index.get("aggregate", {})
    if not isinstance(aggregate, dict):
        return [*errors, "index aggregate must be an object"]
    if aggregate.get("available_source_count") != len(available):
        errors.append("available source count mismatch")
    if len(available) != len(components):
        counts = aggregate.get("counts", {})
        if (
            aggregate.get("aggregate_digest") != UNKNOWN
            or not isinstance(counts, dict)
            or not counts_are_all_unknown(counts)
        ):
            errors.append("unavailable source denominator must remain UNKNOWN")
    elif available_evidence_is_concrete:
        expected_counts = {
            "total": sum(int(item["counts"]["total"]) for item in components),
            "included": sum(int(item["counts"]["included"]) for item in components),
            "excluded": sum(int(item["counts"]["excluded"]) for item in components),
            "unknown": sum(int(item["counts"]["unknown"]) for item in components),
            "exclusion_reasons": dict(
                sorted(
                    sum(
                        (Counter(item["counts"]["exclusion_reasons"]) for item in components),
                        Counter(),
                    ).items()
                )
            ),
        }
        if aggregate.get("counts") != expected_counts:
            errors.append("aggregate counts do not match component summaries")
        if aggregate.get("aggregate_digest") != sha256_value(components):
            errors.append("aggregate digest mismatch")
    return errors


def validate_document(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    document_kind = payload.get("document_kind")
    definition_name = {"component": "component_document", "index": "index_document"}.get(str(document_kind))
    definitions = schema.get("$defs")
    if definition_name is None or not isinstance(definitions, dict) or not isinstance(definitions.get(definition_name), dict):
        return ["unknown document_kind or malformed schema definition"]
    selected_schema = dict(schema)
    selected_schema.pop("oneOf", None)
    selected_schema.update(definitions[definition_name])
    errors = validate_json_schema(payload, selected_schema)
    if document_kind == "component":
        errors.extend(validate_component_semantics(payload))
    elif document_kind == "index":
        errors.extend(validate_index_semantics(payload))
    return errors


def validate_cross_document(index: Mapping[str, Any], components: Sequence[Mapping[str, Any]]) -> list[str]:
    expected = sorted((component_summary(component) for component in components), key=lambda item: item["component_id"])
    if index.get("components") != expected:
        return ["index component summaries do not match component shards"]
    return []


def validate_source_specs(specs: Sequence[SourceSpec]) -> None:
    if [spec.component_id for spec in specs] != ["atlas-root", "playbook"]:
        raise InventoryError("AUTHORITY_WIDENING_REJECTED", "Pilot authority set must be exactly atlas-root and playbook.")
    for field in ("source_id", "component_id"):
        values = [getattr(spec, field) for spec in specs]
        if len(values) != len(set(values)):
            raise InventoryError("DUPLICATE_RECORD_IDENTITY", f"Duplicate source {field}.")


def build_components(specs: Sequence[SourceSpec], repo_paths: Mapping[str, Path]) -> list[dict[str, Any]]:
    validate_source_specs(specs)
    resolved: dict[str, Path] = {}
    components: list[dict[str, Any]] = []
    for spec in specs:
        candidate = repo_paths.get(spec.component_id)
        if candidate is None:
            components.append(unknown_component(spec, "SOURCE_PATH_UNAVAILABLE"))
            continue
        try:
            resolved_path = resolve_real_path(candidate)
        except (FileNotFoundError, PermissionError, OSError):
            components.append(unknown_component(spec, "SOURCE_PATH_UNAVAILABLE"))
            continue
        if resolved_path in resolved.values():
            raise InventoryError("AMBIGUOUS_REPOSITORY_ROOT", "Two component identities resolve to the same repository root.")
        resolved[spec.component_id] = resolved_path
        components.append(build_component(spec, resolved_path))
    return components


def load_schema(workspace_root: Path) -> dict[str, Any]:
    schema_path = ensure_resolved_contained(
        workspace_root,
        resolve_real_path(workspace_root / SCHEMA_PATH),
    )
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InventoryError("MALFORMED_SCHEMA", "Text corpus schema must be a JSON object.")
    return payload


def schema_contract_errors(schema: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "atlas://schemas/atlas.text-corpus.inventory.v1.json",
        "title": "ATLAS committed text corpus inventory v1",
    }
    for field, value in expected.items():
        if schema.get(field) != value:
            errors.append(f"schema {field} must equal {value!r}")
    refs = schema.get("oneOf")
    if refs != [{"$ref": "#/$defs/index_document"}, {"$ref": "#/$defs/component_document"}]:
        errors.append("schema oneOf must select the index and component definitions")
    definitions = schema.get("$defs")
    required_definitions = {
        "aggregate",
        "component_document",
        "component_summary",
        "count_or_unknown",
        "counts",
        "git_oid_or_unknown",
        "index_document",
        "lifecycle",
        "unknown_reason",
        "policy",
        "record",
        "sha256_or_unknown",
        "source",
    }
    if not isinstance(definitions, dict):
        errors.append("schema $defs must be an object")
    elif not required_definitions.issubset(definitions):
        errors.append("schema $defs is missing an inventory definition")
    return errors


def build_outputs(
    *,
    workspace_root: Path,
    repo_paths: Mapping[str, Path],
    specs: Sequence[SourceSpec] = PINNED_SOURCE_SPECS,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    schema = load_schema(workspace_root)
    schema_errors = schema_contract_errors(schema)
    if schema_errors:
        raise InventoryError("MALFORMED_SCHEMA", "; ".join(schema_errors))
    components = build_components(specs, repo_paths)
    index = build_index(components)
    errors: list[str] = []
    for component in components:
        errors.extend(validate_document(component, schema))
    errors.extend(validate_document(index, schema))
    errors.extend(validate_cross_document(index, components))
    if errors:
        raise InventoryError("MALFORMED_INVENTORY", "; ".join(errors[:20]))
    outputs = {INDEX_PATH: stable_json_bytes(index)}
    for component in components:
        component_id = component["source"]["component_id"]
        outputs[COMPONENT_PATHS[component_id]] = stable_json_bytes(component)
    return outputs, index


def materialize_outputs(
    *,
    workspace_root: Path,
    output_root: Path,
    outputs: Mapping[Path, bytes],
    check: bool,
) -> list[str]:
    drift: list[str] = []
    ensure_resolved_contained(workspace_root, output_root)
    for relative_path, raw in sorted(outputs.items(), key=lambda item: item[0].as_posix()):
        validate_relative_path(relative_path.as_posix())
        target = ensure_resolved_contained(
            output_root,
            resolve_real_path(output_root / relative_path, allow_missing_leaf=True),
        )
        if check:
            if not target.is_file() or target.read_bytes() != raw:
                drift.append(relative_path.as_posix())
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return drift


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--atlas-repo", type=Path)
    parser.add_argument("--playbook-repo", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--check", action="store_true", help="Fail if committed outputs differ; never write.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace_candidate = args.workspace_root
    output_candidate = args.output_root or workspace_candidate
    try:
        workspace_root, output_root = validate_output_root(workspace_candidate, output_candidate)
        atlas_repo = args.atlas_repo or workspace_root
        outputs, index = build_outputs(
            workspace_root=workspace_root,
            repo_paths={"atlas-root": atlas_repo, "playbook": args.playbook_repo},
        )
        drift = materialize_outputs(
            workspace_root=workspace_root,
            output_root=output_root,
            outputs=outputs,
            check=args.check,
        )
        if drift:
            print(json.dumps({"status": "drift", "paths": drift}, sort_keys=True))
            return 1
        aggregate = index["aggregate"]
        print(
            json.dumps(
                {
                    "status": "verified" if args.check else "generated",
                    "aggregate_digest": aggregate["aggregate_digest"],
                    "counts": aggregate["counts"],
                    "source_count": aggregate["source_count"],
                    "available_source_count": aggregate["available_source_count"],
                },
                sort_keys=True,
            )
        )
        return 0
    except (InventoryError, json.JSONDecodeError, OSError) as exc:
        code = exc.code if isinstance(exc, InventoryError) else "INVENTORY_IO_ERROR"
        print(json.dumps({"status": "error", "code": code, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
