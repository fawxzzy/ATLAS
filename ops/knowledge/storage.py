"""ATLAS knowledge-import storage architecture (Wave S / Wave 1).

Reusable, product-neutral pipeline mechanics for the knowledge-import
system:

- first-class, independently configurable storage/work roots
  (ATLAS_IMPORT_STORAGE_ROOT / ATLAS_IMPORT_WORK_ROOT)
- long-path-safe deterministic file enumeration
- peak-space preflight budgeting
- resumable, atomic file copy
- explicit generated-cache exclusions
- junction-independent relocation manifests
- relocation receipts and restore verification

Scope boundary: this module is reusable architecture only. It does not
migrate, repair, or otherwise touch any existing import -- in particular
personal--onedrive-desktop and its nine stale digest receipts are
out of scope here (see docs/ops/ATLAS-IMPORT-STORAGE-CONVERGENCE-WAVE-1.md).
`_pipeline.py`'s `list_files()` is wired to delegate to `enumerate_files()`
below because that is a pure correctness fix (same signature, same return
type, just correct near the 260-character path boundary); nothing else in
`_pipeline.py`'s existing behavior is changed by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RELOCATION_MANIFEST_VERSION = "atlas.knowledge-relocation-manifest.v1"
RELOCATION_RECEIPT_VERSION = "atlas.knowledge-relocation-receipt.v1"
RESTORE_VERIFICATION_VERSION = "atlas.knowledge-restore-verification.v1"

DEFAULT_SAFETY_MARGIN_BYTES = 512 * 1024 * 1024  # 512 MiB

_STORAGE_ROOT_ENV = "ATLAS_IMPORT_STORAGE_ROOT"
_WORK_ROOT_ENV = "ATLAS_IMPORT_WORK_ROOT"

# Generated-cache directories that are fully regenerable from source and
# never carry unique content. This list is intentionally explicit and
# documented rather than a broad heuristic -- see
# docs/ops/ATLAS-IMPORT-STORAGE-CONVERGENCE-WAVE-1.md for the justification
# for each entry and how to override per-import if a real archive genuinely
# needs one preserved. The Unity entries are the exact classes root-caused
# as stale during the personal--onedrive-desktop import reconciliation.
GENERATED_CACHE_EXCLUSION_PATTERNS: tuple[str, ...] = (
    "Library/PackageCache",
    "Library/APIUpdater/ConfigurationCache",
    "Library/ScriptAssemblies",
    "Library/Bee",
    "Temp",
    "obj",
    "node_modules",
    "__pycache__",
    ".git",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _win_long_path(path: Path) -> Path:
    """Return a `\\\\?\\`-prefixed absolute path so Windows APIs bypass the
    260-character MAX_PATH limit deterministically, regardless of whether
    the process-wide LongPathsEnabled policy (admin-only, opt-in) is set.
    No-op on non-Windows platforms. Safe to call on paths that do not exist
    yet -- Path.resolve() only normalizes, it does not require existence.
    """
    if os.name != "nt":
        return path
    resolved = path.resolve()
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


# Every actual filesystem touch in this module goes through one of these
# _lp_* wrappers rather than calling pathlib/shutil/os directly on a
# possibly-deep path. This was not an abstract concern: constructing this
# module's own test fixtures with plain Path.mkdir() failed past
# MAX_PATH on the very machine this was developed on, confirming the
# defect reaches every write/stat/copy/rename call, not only directory
# enumeration.


def _lp_exists(path: Path) -> bool:
    return _win_long_path(path).exists()


def _lp_is_file(path: Path) -> bool:
    prefixed = _win_long_path(path)
    return prefixed.exists() and prefixed.is_file()


def _lp_stat(path: Path) -> os.stat_result:
    return _win_long_path(path).stat()


def _lp_mkdir(path: Path) -> None:
    _win_long_path(path).mkdir(parents=True, exist_ok=True)


def _lp_unlink(path: Path, *, missing_ok: bool = False) -> None:
    _win_long_path(path).unlink(missing_ok=missing_ok)


def _lp_copy2(source: Path, destination: Path) -> None:
    shutil.copy2(_win_long_path(source), _win_long_path(destination))


def _lp_replace(source: Path, destination: Path) -> None:
    os.replace(_win_long_path(source), _win_long_path(destination))


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with _win_long_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def stable_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


# ---------------------------------------------------------------------------
# 1. First-class storage/work roots
# ---------------------------------------------------------------------------


def atlas_root() -> Path:
    return ROOT


def import_storage_root(*, env: dict[str, str] | None = None) -> Path:
    """Root for durable, long-lived import archival data (raw preservation
    copies, manifests, receipts).

    Defaults to the existing ATLAS-relative location
    (data/imports/knowledge) so any caller that never configures
    ATLAS_IMPORT_STORAGE_ROOT keeps behaving exactly as before. Passing
    `env` explicitly (rather than always reading os.environ) makes this
    testable without process-wide monkeypatching.
    """
    source = env if env is not None else os.environ
    configured = source.get(_STORAGE_ROOT_ENV, "").strip()
    if configured:
        return Path(configured).resolve()
    return (atlas_root() / "data" / "imports" / "knowledge").resolve()


def import_work_root(*, env: dict[str, str] | None = None) -> Path:
    """Root for transient, in-progress import work: resumable-copy staging
    and extraction scratch space. Never the durable destination for
    anything -- see resumable_copy_tree().

    Defaults to a runtime-relative directory distinct from the storage
    root's default so the two are never accidentally the same path when
    both are unconfigured.
    """
    source = env if env is not None else os.environ
    configured = source.get(_WORK_ROOT_ENV, "").strip()
    if configured:
        return Path(configured).resolve()
    return (atlas_root() / "runtime" / "knowledge-import-work").resolve()


# ---------------------------------------------------------------------------
# 2. Long-path-safe deterministic enumeration
# ---------------------------------------------------------------------------


class LongPathEnumerationError(Exception):
    """Raised when an enumerated path cannot actually be stat'd -- a real
    long-path failure rather than a silently dropped entry."""


def enumerate_files(root: Path) -> list[Path]:
    """Deterministic, long-path-safe file enumeration.

    Returns plain (non-`\\\\?\\`-prefixed) absolute paths rooted at
    `root.resolve()`, sorted by their POSIX-style relative-to-root
    representation -- not OS scandir order, which is not guaranteed stable
    across runs or platforms. Every returned entry is confirmed statable at
    enumeration time, so a long-path failure raises LongPathEnumerationError
    instead of silently vanishing from the result (the exact failure mode
    that caused a prior 290-file manifest gap in `_pipeline.py`'s previous
    `rglob()`-based enumeration).

    Junction-independent by construction: this only cares about what is
    actually reachable at `root` right now via long-path-safe traversal. It
    never inspects reparse-point metadata, so it behaves identically whether
    `root` is a plain directory or the far side of an NTFS junction.
    """
    if not root.exists():
        return []
    normal_root = root.resolve()
    walk_root = _win_long_path(normal_root)
    rel_entries: list[str] = []
    for dirpath, dirnames, filenames in os.walk(walk_root):
        dirnames.sort()
        dirpath_path = Path(dirpath)
        for name in sorted(filenames):
            candidate = dirpath_path / name
            try:
                candidate.stat()
            except OSError as exc:
                raise LongPathEnumerationError(
                    f"Enumerated path is not statable, likely a long-path failure: {candidate}"
                ) from exc
            rel_entries.append(candidate.relative_to(walk_root).as_posix())
    rel_entries.sort()
    return [normal_root / rel for rel in rel_entries]


# ---------------------------------------------------------------------------
# 3. Explicit generated-cache exclusions
# ---------------------------------------------------------------------------


def is_generated_cache_path(relative_posix_path: str) -> bool:
    """True if any path component sequence in `relative_posix_path` matches
    a known generated-cache directory. Matching is by directory-name
    sequence anywhere in the path, not just at the root, so a nested Unity
    project's Library/PackageCache is excluded the same as a top-level one.
    """
    parts = relative_posix_path.split("/")
    for pattern in GENERATED_CACHE_EXCLUSION_PATTERNS:
        pattern_parts = pattern.split("/")
        span = len(pattern_parts)
        for start in range(len(parts) - span + 1):
            if parts[start:start + span] == pattern_parts:
                return True
    return False


# ---------------------------------------------------------------------------
# 4. Peak-space preflight
# ---------------------------------------------------------------------------


@dataclass
class SpaceBudget:
    required_storage_bytes: int
    required_work_bytes: int
    available_storage_bytes: int
    available_work_bytes: int
    safety_margin_bytes: int
    ok: bool
    findings: list[str] = field(default_factory=list)


def _free_bytes(path: Path) -> int:
    probe = path
    while not _lp_exists(probe):
        parent = probe.parent
        if parent == probe:
            break
        probe = parent
    return shutil.disk_usage(_win_long_path(probe)).free


def preflight_space_budget(
    *,
    source_root: Path,
    storage_root: Path,
    work_root: Path,
    safety_margin_bytes: int = DEFAULT_SAFETY_MARGIN_BYTES,
    materialize_extracted: bool = False,
    exclude: Callable[[str], bool] | None = None,
) -> SpaceBudget:
    """Compute the PEAK space this relocation will actually require and
    compare it against free space on both the storage and work roots. Fails
    closed (ok=False) rather than letting a copy start and run out of disk
    mid-operation.

    Peak, not final size: resumable_copy_tree() stages one file at a time
    under work_root before an atomic rename into place, so the transient
    work-root peak for the whole operation is bounded by the single largest
    file, not the entire tree. The storage-root requirement is the full
    tree size (doubled if extracted materialization is requested, since
    that produces a second copy of the content alongside the raw
    preservation copy).
    """
    files = enumerate_files(source_root)
    if exclude is not None:
        normal_source_root = source_root.resolve()
        files = [
            f for f in files
            if not exclude(f.relative_to(normal_source_root).as_posix())
        ]
    tree_bytes = 0
    largest_file_bytes = 0
    for f in files:
        try:
            size = _lp_stat(f).st_size
        except OSError:
            continue
        tree_bytes += size
        largest_file_bytes = max(largest_file_bytes, size)

    multiplier = 2 if materialize_extracted else 1
    required_storage = (tree_bytes * multiplier) + safety_margin_bytes
    required_work = largest_file_bytes + safety_margin_bytes

    available_storage = _free_bytes(storage_root)
    available_work = _free_bytes(work_root)

    findings: list[str] = []
    ok = True
    if available_storage < required_storage:
        ok = False
        findings.append(
            "insufficient_storage_root_space: "
            f"required={required_storage} available={available_storage} root={storage_root}"
        )
    if available_work < required_work:
        ok = False
        findings.append(
            "insufficient_work_root_space: "
            f"required={required_work} available={available_work} root={work_root}"
        )
    return SpaceBudget(
        required_storage_bytes=required_storage,
        required_work_bytes=required_work,
        available_storage_bytes=available_storage,
        available_work_bytes=available_work,
        safety_margin_bytes=safety_margin_bytes,
        ok=ok,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# 5. Resumable, atomic copy
# ---------------------------------------------------------------------------


class ResumableCopyError(Exception):
    pass


@dataclass
class CopyResult:
    copied: list[str] = field(default_factory=list)
    skipped_already_present: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    total_bytes_copied: int = 0


def _matches_existing(source: Path, destination: Path) -> bool:
    if not _lp_is_file(destination):
        return False
    try:
        if _lp_stat(source).st_size != _lp_stat(destination).st_size:
            return False
    except OSError:
        return False
    return file_checksum(source) == file_checksum(destination)


def _atomic_place(staged: Path, destination: Path) -> None:
    """Move `staged` into `destination` so a reader never observes a
    partially-written destination file. Prefers a direct atomic rename;
    falls back to a same-directory temp copy + rename when `staged` and
    `destination` are on different volumes (os.replace raises EXDEV for
    cross-device renames on POSIX)."""
    try:
        _lp_replace(staged, destination)
        return
    except OSError:
        pass
    same_dir_temp = destination.parent / f"{destination.name}.{os.getpid()}.part"
    _lp_copy2(staged, same_dir_temp)
    _lp_replace(same_dir_temp, destination)
    _lp_unlink(staged, missing_ok=True)


def _copy_one_resumable(source: Path, destination: Path, *, work_root: Path) -> int:
    _lp_mkdir(destination.parent)
    stage_dir = work_root / "copy-staging"
    _lp_mkdir(stage_dir)
    stage_name = hashlib.sha1(str(destination).encode("utf-8")).hexdigest() + ".part"
    staged = stage_dir / stage_name
    if _lp_exists(staged):
        _lp_unlink(staged)
    _lp_copy2(source, staged)
    if file_checksum(staged) != file_checksum(source):
        _lp_unlink(staged, missing_ok=True)
        raise ResumableCopyError(f"staged copy checksum mismatch for {source}")
    size = _lp_stat(staged).st_size
    _atomic_place(staged, destination)
    return size


def resumable_copy_tree(
    source_root: Path,
    destination_root: Path,
    *,
    work_root: Path,
    exclude: Callable[[str], bool] | None = None,
) -> CopyResult:
    """Copy source_root's file tree into destination_root, resumably and
    atomically per file.

    Resumable: on re-invocation after an interruption, any destination file
    that already matches the source (same size and checksum) is skipped
    rather than re-copied, so an interrupted run can simply be re-run to
    completion.

    Atomic per file: each file is staged under work_root, checksum-verified
    against the source, and only then moved into destination_root with an
    atomic rename (see _atomic_place). destination_root never contains a
    partially-written file, even if the process is killed mid-copy.
    """
    files = enumerate_files(source_root)
    normal_source_root = source_root.resolve()
    result = CopyResult()
    for source_path in files:
        rel = source_path.relative_to(normal_source_root).as_posix()
        if exclude is not None and exclude(rel):
            continue
        destination_path = destination_root / rel
        if _matches_existing(source_path, destination_path):
            result.skipped_already_present.append(rel)
            continue
        try:
            size = _copy_one_resumable(source_path, destination_path, work_root=work_root)
            result.copied.append(rel)
            result.total_bytes_copied += size
        except (OSError, ResumableCopyError):
            result.failed.append(rel)
    return result


# ---------------------------------------------------------------------------
# 6. Junction-independent relocation manifests
# ---------------------------------------------------------------------------


def build_relocation_manifest(root: Path, *, exclude: Callable[[str], bool] | None = None) -> dict[str, Any]:
    """Build a manifest of `root`'s current real content via long-path-safe
    enumeration. Contains only relative paths, sizes, and checksums -- no
    reference to junctions, drive letters, or any storage mechanism -- so it
    reconciles identically regardless of how `root` is currently reached.
    """
    normal_root = root.resolve()
    files = enumerate_files(root)
    entries: list[dict[str, Any]] = []
    for path in files:
        rel = path.relative_to(normal_root).as_posix()
        if exclude is not None and exclude(rel):
            continue
        entries.append(
            {
                "path": rel,
                "size_bytes": _lp_stat(path).st_size,
                "checksum": file_checksum(path),
            }
        )
    entries.sort(key=lambda e: e["path"])
    return {
        "contract_version": RELOCATION_MANIFEST_VERSION,
        "entry_count": len(entries),
        "total_bytes": sum(e["size_bytes"] for e in entries),
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# 7. Relocation receipts
# ---------------------------------------------------------------------------


def build_relocation_receipt(
    *,
    archive_id: str,
    source_description: str,
    destination_root: Path,
    copy_result: CopyResult,
    manifest: dict[str, Any],
    space_budget: SpaceBudget,
) -> dict[str, Any]:
    return {
        "contract_version": RELOCATION_RECEIPT_VERSION,
        "archive_id": archive_id,
        "recorded_at": utc_now_iso(),
        "source_description": source_description,
        "destination_root": str(destination_root),
        "files_copied": len(copy_result.copied),
        "files_skipped_already_present": len(copy_result.skipped_already_present),
        "files_failed": list(copy_result.failed),
        "bytes_copied": copy_result.total_bytes_copied,
        "manifest_entry_count": manifest["entry_count"],
        "manifest_total_bytes": manifest["total_bytes"],
        "manifest_digest": stable_json_digest(manifest),
        "space_budget": {
            "required_storage_bytes": space_budget.required_storage_bytes,
            "required_work_bytes": space_budget.required_work_bytes,
            "available_storage_bytes": space_budget.available_storage_bytes,
            "available_work_bytes": space_budget.available_work_bytes,
            "ok": space_budget.ok,
            "findings": list(space_budget.findings),
        },
        "ok": not copy_result.failed and space_budget.ok,
    }


# ---------------------------------------------------------------------------
# 8. Restore verification
# ---------------------------------------------------------------------------


def verify_restore(*, manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    """Independently re-walk `root` and reconcile it against a previously
    recorded manifest. Junction-independent: only current, real content
    reachable at `root` via long-path-safe enumeration is considered, so a
    manifest recorded before a junction existed (or after the junction is
    gone and the data lives at a plain path) reconciles the same way.
    """
    current = build_relocation_manifest(root)
    expected_by_path = {e["path"]: e for e in manifest["entries"]}
    current_by_path = {e["path"]: e for e in current["entries"]}
    missing = sorted(set(expected_by_path) - set(current_by_path))
    unexpected = sorted(set(current_by_path) - set(expected_by_path))
    mismatched = sorted(
        path
        for path in (set(expected_by_path) & set(current_by_path))
        if expected_by_path[path]["checksum"] != current_by_path[path]["checksum"]
    )
    ok = not missing and not mismatched
    return {
        "contract_version": RESTORE_VERIFICATION_VERSION,
        "root": str(root),
        "expected_entry_count": len(expected_by_path),
        "current_entry_count": len(current_by_path),
        "missing_paths": missing,
        "unexpected_paths": unexpected,
        "mismatched_paths": mismatched,
        "ok": ok,
    }


# ---------------------------------------------------------------------------
# 9. High-level composed entry point (opt-in; not wired into the existing
#    import_archive() default in this PR -- see PR body / docs for why)
# ---------------------------------------------------------------------------


@dataclass
class RelocationResult:
    ok: bool
    space_budget: SpaceBudget
    copy_result: CopyResult | None
    manifest: dict[str, Any] | None
    receipt: dict[str, Any] | None
    restore_verification: dict[str, Any] | None


def relocate_archive_source(
    *,
    archive_id: str,
    source_root: Path,
    destination_root: Path,
    work_root: Path,
    source_description: str,
    materialize_extracted_root: Path | None = None,
    exclude: Callable[[str], bool] = is_generated_cache_path,
) -> RelocationResult:
    """Compose the full Wave 1 architecture into one call: preflight, one
    raw preservation copy, optional selective extracted materialization,
    manifest, relocation receipt, and restore verification.

    `materialize_extracted_root`, when given, makes a second copy at that
    location -- this is the "selective" part: callers opt in explicitly
    per invocation rather than getting a second copy by default.
    """
    budget = preflight_space_budget(
        source_root=source_root,
        storage_root=destination_root,
        work_root=work_root,
        materialize_extracted=materialize_extracted_root is not None,
        exclude=exclude,
    )
    if not budget.ok:
        return RelocationResult(
            ok=False,
            space_budget=budget,
            copy_result=None,
            manifest=None,
            receipt=None,
            restore_verification=None,
        )

    copy_result = resumable_copy_tree(source_root, destination_root, work_root=work_root, exclude=exclude)
    if materialize_extracted_root is not None:
        resumable_copy_tree(source_root, materialize_extracted_root, work_root=work_root, exclude=exclude)

    manifest = build_relocation_manifest(destination_root)
    receipt = build_relocation_receipt(
        archive_id=archive_id,
        source_description=source_description,
        destination_root=destination_root,
        copy_result=copy_result,
        manifest=manifest,
        space_budget=budget,
    )
    verification = verify_restore(manifest=manifest, root=destination_root)
    return RelocationResult(
        ok=receipt["ok"] and verification["ok"],
        space_budget=budget,
        copy_result=copy_result,
        manifest=manifest,
        receipt=receipt,
        restore_verification=verification,
    )
