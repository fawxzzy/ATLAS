"""ATLAS knowledge-import storage architecture (Wave S / Wave 1).

Reusable, product-neutral pipeline mechanics for the knowledge-import
system:

- first-class, independently configurable storage/work roots
  (ATLAS_IMPORT_STORAGE_ROOT / ATLAS_IMPORT_WORK_ROOT)
- long-path-safe deterministic file enumeration
- symlink confinement (external-target file symlinks rejected before copy)
- per-volume peak-space preflight budgeting
- resumable, atomic file copy
- explicit generated-cache exclusions (opt-in, never the raw-preservation
  default)
- a source-anchored relocation manifest, copy, and exact destination
  reconciliation
- durably persisted relocation receipts and restore verification

Scope boundary: this module is reusable architecture only. It does not
migrate, repair, or otherwise touch any existing import -- in particular
personal--onedrive-desktop and its nine stale digest receipts are
out of scope here (see docs/ops/ATLAS-IMPORT-STORAGE-CONVERGENCE-WAVE-1.md).
`_pipeline.py`'s `list_files()` is wired to delegate to `enumerate_files()`
below because that is a pure correctness fix (same signature, same return
type, same sort order per platform, just correct near the 260-character
path boundary); nothing else in `_pipeline.py`'s existing behavior is
changed by this module.
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


def _win_long_path_no_follow(path: Path) -> Path:
    """Like _win_long_path, but never resolves through a trailing symlink.

    Path.resolve() always follows symlinks to their final target -- correct
    for most operations here, but wrong for anything that must act on a
    symlink *itself* (is_symlink, lstat, readlink, unlink): resolving first
    would silently operate on the link's target instead of the link, which
    is exactly the bug hosted Windows CI caught -- _lp_is_symlink() built on
    _win_long_path() always reported False because it was checking the
    resolved target, not the link. os.path.abspath() performs pure lexical
    normalization (collapsing `.`/`..`/duplicate separators) without
    touching the filesystem at all, so it never follows a symlink.
    """
    if os.name != "nt":
        return path
    absolute = Path(os.path.abspath(str(path)))
    text = str(absolute)
    if text.startswith("\\\\?\\"):
        return absolute
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


# Every actual filesystem touch in this module goes through one of these
# _lp_* wrappers rather than calling pathlib/shutil/os directly on a
# possibly-deep path. This was not an abstract concern: constructing this
# module's own test fixtures with plain Path.mkdir() failed past
# MAX_PATH on the machine this was developed on, confirming the defect
# reaches every write/stat/copy/rename call, not only directory
# enumeration. The link-aware wrappers below (_lp_lstat, _lp_is_symlink,
# _lp_readlink, _lp_unlink) deliberately use _win_long_path_no_follow
# instead, for the reason documented on that function.


def _lp_exists(path: Path) -> bool:
    return _win_long_path(path).exists()


def _lp_is_file(path: Path) -> bool:
    prefixed = _win_long_path(path)
    return prefixed.exists() and prefixed.is_file()


def _lp_stat(path: Path) -> os.stat_result:
    return _win_long_path(path).stat()


def _lp_lstat(path: Path) -> os.stat_result:
    return _win_long_path_no_follow(path).lstat()


def _lp_is_symlink(path: Path) -> bool:
    return _win_long_path_no_follow(path).is_symlink()


def _lp_readlink(path: Path) -> str:
    return os.readlink(_win_long_path_no_follow(path))


def _lp_mkdir(path: Path) -> None:
    _win_long_path(path).mkdir(parents=True, exist_ok=True)


def _lp_unlink(path: Path, *, missing_ok: bool = False) -> None:
    # No-follow: removing a path must remove that exact directory entry.
    # If path is a symlink, a resolve()-based prefix would target its
    # *destination* for deletion instead of the link itself.
    _win_long_path_no_follow(path).unlink(missing_ok=missing_ok)


def _lp_copy2(source: Path, destination: Path) -> None:
    shutil.copy2(_win_long_path(source), _win_long_path(destination))


def _lp_replace(source: Path, destination: Path) -> None:
    # No-follow on both sides. destination in particular must never be
    # resolve()d first: if a destination path is already a symlink (or a
    # symlink is planted there between preflight and copy), resolving it
    # would target os.replace() at the link's *target* instead of the
    # directory entry, silently overwriting whatever that target is --
    # potentially outside every admitted root. This applies to every
    # _lp_replace() caller, including receipt/manifest writes, not only
    # regular-file copy.
    os.replace(_win_long_path_no_follow(source), _win_long_path_no_follow(destination))


def _lp_symlink(target: str, link_path: Path) -> None:
    os.symlink(target, _win_long_path(link_path))


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
    """Raised when an enumerated directory entry cannot actually be lstat'd
    -- a real long-path failure rather than a silently dropped entry."""


def _sort_key(rel_path: str) -> str:
    # Matches the platform behavior of the previous rglob()-based
    # enumeration exactly: PureWindowsPath ordering is case-insensitive
    # (Windows filesystems are case-insensitive), PurePosixPath ordering is
    # case-sensitive. Sorting the plain POSIX-string relative path without
    # this would silently reorder mixed-case siblings on Windows relative
    # to the old implementation, changing tree_digest() output for any
    # tree with case-differing filenames at the same level even though
    # nothing about the tree's actual content changed.
    return rel_path.lower() if os.name == "nt" else rel_path


def enumerate_files(root: Path) -> list[Path]:
    """Deterministic, long-path-safe file enumeration.

    Returns plain (non-`\\\\?\\`-prefixed) paths anchored to `root` exactly
    as passed in -- each entry is `root / <relative-path>`, never
    `root.resolve() / <relative-path>` -- sorted by the same per-platform
    ordering the previous `rglob()`-based enumeration used (case-sensitive
    on POSIX, case-insensitive on Windows).

    Anchoring to the caller's own `root` object, not a resolved copy of it,
    matters: a caller that later does `entry.relative_to(root)` must get
    the same `root` value back out, or the call raises ValueError. This
    was found live on Windows CI, where the runner's temp directory
    resolves through an 8.3 short-name alias (`RUNNER~1` vs
    `runneradmin`) -- `root.resolve()` normalizes to the long form, so an
    entry built from the resolved root no longer satisfied
    `.relative_to(root)` against the caller's original, unresolved `root`.

    Every returned entry is confirmed to exist as a real directory entry
    (via `lstat`, which does not require a symlink's target to resolve) at
    enumeration time; a genuine long-path failure raises
    LongPathEnumerationError instead of silently vanishing from the result
    (the exact failure mode that caused a prior 290-file manifest gap in
    `_pipeline.py`'s previous `rglob()`-based enumeration). `lstat` rather
    than `stat` is deliberate: this function enumerates symlinks as
    themselves, without following them, so callers can apply their own
    symlink policy (see check_symlink_confinement()) rather than having
    one silently applied during enumeration.

    Junction-independent by construction: this only cares about what is
    actually reachable at `root` right now via long-path-safe traversal. It
    never inspects reparse-point metadata, so it behaves identically whether
    `root` is a plain directory or the far side of an NTFS junction.
    """
    if not root.exists():
        return []
    walk_root = _win_long_path(root)
    rel_entries: list[str] = []
    for dirpath, dirnames, filenames in os.walk(walk_root, followlinks=False):
        dirnames.sort(key=_sort_key)
        dirpath_path = Path(dirpath)
        for name in sorted(filenames, key=_sort_key):
            candidate = dirpath_path / name
            try:
                candidate.lstat()
            except OSError as exc:
                raise LongPathEnumerationError(
                    f"Enumerated path is not statable, likely a long-path failure: {candidate}"
                ) from exc
            rel_entries.append(candidate.relative_to(walk_root).as_posix())
    rel_entries.sort(key=_sort_key)
    return [root / rel for rel in rel_entries]


def _is_reparse_point(path: Path) -> bool:
    """True for both symlinks and Windows junctions/mount-point reparse
    points. `Path.is_symlink()` alone is not reliable for junctions on
    Windows -- junctions use `IO_REPARSE_TAG_MOUNT_POINT`, not
    `IO_REPARSE_TAG_SYMLINK` -- so this also checks the raw reparse tag
    via `lstat()`, which Python exposes as `st_reparse_tag` on Windows."""
    if _lp_is_symlink(path):
        return True
    if os.name != "nt":
        return False
    try:
        st = _win_long_path_no_follow(path).lstat()
    except OSError:
        return False
    return getattr(st, "st_reparse_tag", 0) != 0


def enumerate_directory_links(root: Path) -> list[Path]:
    """Enumerate directory symlinks and Windows junctions found under
    `root`, without descending into them -- `enumerate_files()`'s
    `os.walk(followlinks=False)` already prevents traversal into them, but
    it only records `filenames`, never `dirnames`, so a directory link was
    previously invisible to the manifest and to symlink confinement
    entirely: silently omitted from a claimed lossless raw preservation,
    and never checked for an external target.

    Kept separate from `enumerate_files()` rather than merged into it, so
    that function's contract for `_pipeline.list_files()` -- files only,
    proven identical to the previous `rglob()`-based behavior -- is
    unchanged.
    """
    if not root.exists():
        return []
    walk_root = _win_long_path(root)
    rel_entries: list[str] = []
    for dirpath, dirnames, _filenames in os.walk(walk_root, followlinks=False):
        dirpath_path = Path(dirpath)
        link_names = [name for name in dirnames if _is_reparse_point(dirpath_path / name)]
        for name in sorted(link_names, key=_sort_key):
            candidate = dirpath_path / name
            rel_entries.append(candidate.relative_to(walk_root).as_posix())
        # os.walk(followlinks=False) already will not descend into these;
        # removing them from dirnames here is hygiene, not a safety
        # requirement, so a later os.walk internals change can't
        # accidentally start recursing into a directory link.
        dirnames[:] = [d for d in dirnames if d not in link_names]
    rel_entries.sort(key=_sort_key)
    return [root / rel for rel in rel_entries]


# ---------------------------------------------------------------------------
# 3. Link policy and symlink/junction confinement
# ---------------------------------------------------------------------------
#
# Wave 1's contract is safe storage relocation, not a portable archive
# format. An earlier version of this module attempted to preserve file
# symlinks, directory symlinks, and Windows junctions as live links across
# a copy, including rewriting absolute internal targets. That produced
# three real, distinct defects across three review rounds (a resolve()d
# destination that could be redirected through a planted symlink; an
# 8.3-short-name mismatch in a target-rebasing comparison on Windows CI;
# and a manifest built from pre-rewrite targets that could never match a
# post-rewrite destination). Reliably preserving every combination of
# POSIX/Windows file and directory links, absolute and relative targets,
# and Windows reparse-point semantics is a separate, substantially larger
# problem than this wave's actual requirement. The policy below detects
# and reports every link entry precisely, then fails closed before any
# copy starts, rather than attempting to materialize link semantics this
# module does not yet get right on every platform.


class LinkPolicy:
    """Wave 1 ships exactly one policy: reject every link entry (file
    symlink, directory symlink, or Windows junction/reparse point) before
    any copy starts. A future dedicated wave can add a real portable
    link-preservation policy; this module deliberately does not pretend
    to be one yet."""

    REJECT_ALL = "reject-all"



def check_symlink_confinement(root: Path, entries: list[Path]) -> list[str]:
    """Return one blocking finding per symlink or junction among `entries`
    whose real target resolves outside `root`. `entries` should be the
    combination of `enumerate_files(root)` (file symlinks) and
    `enumerate_directory_links(root)` (directory symlinks and Windows
    junctions) -- checking only files would leave a directory link's
    target completely unconfined.

    Directory-link *recursion* is already prevented by
    `enumerate_files()`'s `os.walk(followlinks=False)`. This handles the
    remaining gap: a link inside an admitted source tree whose target
    points somewhere else entirely -- `shutil.copy2()` follows file
    symlinks by default, and a directory link would otherwise be silently
    omitted from the manifest with its target never checked at all --
    without this check either would silently expose content from outside
    the admitted root.
    """
    findings: list[str] = []
    normal_root = _win_long_path(root).resolve()
    for entry in entries:
        if not _is_reparse_point(entry):
            continue
        try:
            target = _win_long_path(entry).resolve()
        except OSError:
            findings.append(f"unresolvable_symlink_target: {entry}")
            continue
        try:
            target.relative_to(normal_root)
        except ValueError:
            findings.append(f"external_symlink_target_rejected: {entry} -> {target}")
    return findings


def _link_entry_kind(entry: Path, *, is_directory_entry: bool) -> str:
    if _lp_is_symlink(entry):
        return "directory_symlink" if is_directory_entry else "file_symlink"
    return "windows_junction"


def check_link_entries(
    root: Path,
    files: list[Path],
    directory_links: list[Path],
    *,
    link_policy: str = LinkPolicy.REJECT_ALL,
) -> list[str]:
    """Return one structured, blocking finding per link entry found under
    `link_policy`. Under LinkPolicy.REJECT_ALL (the only policy Wave 1
    ships), every file symlink, directory symlink, and Windows junction
    is rejected -- internal or external target, it does not matter --
    before any copy starts. See the module-level note above LinkPolicy
    for why this module does not attempt to preserve link semantics yet.
    """
    if link_policy != LinkPolicy.REJECT_ALL:
        return []
    findings: list[str] = []
    for entry in files:
        if _is_reparse_point(entry):
            kind = _link_entry_kind(entry, is_directory_entry=False)
            findings.append(f"unsupported_link_entry: path={entry.relative_to(root).as_posix()} kind={kind}")
    for entry in directory_links:
        kind = _link_entry_kind(entry, is_directory_entry=True)
        findings.append(f"unsupported_link_entry: path={entry.relative_to(root).as_posix()} kind={kind}")
    return findings


# ---------------------------------------------------------------------------
# 4. Generated-cache exclusions (opt-in policy, never the raw-preservation
#    default -- see relocate_archive_source())
# ---------------------------------------------------------------------------


# Generated-cache directories that are fully regenerable from source and
# never carry unique content. This list is intentionally explicit and
# documented rather than a broad heuristic -- see
# docs/ops/ATLAS-IMPORT-STORAGE-CONVERGENCE-WAVE-1.md for the justification
# for each entry and how to override per-import if a real archive
# genuinely needs one preserved. The Unity entries are the exact classes
# root-caused as stale during the personal--onedrive-desktop import
# reconciliation. `.git` is deliberately NOT included here: it is version
# control data (history, reflogs, unreachable objects, provenance), not
# generated cache, regardless of how this policy is applied.
GENERATED_CACHE_EXCLUSION_PATTERNS: tuple[str, ...] = (
    "Library/PackageCache",
    "Library/APIUpdater/ConfigurationCache",
    "Library/ScriptAssemblies",
    "Library/Bee",
    "Temp",
    "obj",
    "node_modules",
    "__pycache__",
)


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


@dataclass(frozen=True)
class ExclusionPolicy:
    """A named, versioned exclusion policy. relocate_archive_source() binds
    the policy identity (not just its behavior) into the relocation
    receipt, so what was excluded and under what named policy is part of
    the durable audit trail, not just an implicit side effect of whatever
    callable happened to be passed."""

    policy_id: str
    version: str
    predicate: Callable[[str], bool]


NO_EXCLUSION_POLICY = ExclusionPolicy(
    policy_id="atlas.knowledge.no-exclusion",
    version="v1",
    predicate=lambda rel: False,
)

GENERATED_CACHE_EXCLUSION_POLICY = ExclusionPolicy(
    policy_id="atlas.knowledge.generated-cache-exclusion",
    version="v1",
    predicate=is_generated_cache_path,
)


# ---------------------------------------------------------------------------
# 5. Per-volume peak-space preflight
# ---------------------------------------------------------------------------


@dataclass
class VolumeRequirement:
    probe_path: Path
    required_bytes: int
    available_bytes: int
    ok: bool


@dataclass
class SpaceBudget:
    volumes: list[VolumeRequirement] = field(default_factory=list)
    safety_margin_bytes: int = DEFAULT_SAFETY_MARGIN_BYTES
    ok: bool = True
    findings: list[str] = field(default_factory=list)


# System-volume floor: 25 GiB, matching the operational threshold this
# ATLAS engagement already established the hard way -- the constrained
# band starts at 25GB free on the system drive, below which no bounded
# large-write work should proceed at all. A universal 512 MiB margin does
# not protect that floor; the system volume needs a much larger reserve
# than any other volume this preflight might touch.
SYSTEM_VOLUME_MINIMUM_FREE_BYTES = 25 * 1024 * 1024 * 1024


@dataclass(frozen=True)
class VolumeReservePolicy:
    system_volume_minimum_free_bytes: int = SYSTEM_VOLUME_MINIMUM_FREE_BYTES
    non_system_volume_reserve_bytes: int = DEFAULT_SAFETY_MARGIN_BYTES


DEFAULT_VOLUME_RESERVE_POLICY = VolumeReservePolicy()


def _existing_ancestor(path: Path) -> Path:
    probe = path
    while not _lp_exists(probe):
        parent = probe.parent
        if parent == probe:
            break
        probe = parent
    return probe


def _volume_id(path: Path) -> Any:
    ancestor = _existing_ancestor(path)
    return _lp_stat(ancestor).st_dev


def _is_system_volume(probe_path: Path) -> bool:
    if os.name == "nt":
        system_drive = os.environ.get("SystemDrive", "C:").rstrip("\\").upper()
        return str(probe_path).upper().startswith(system_drive)
    try:
        return _lp_stat(probe_path).st_dev == _lp_stat(Path("/")).st_dev
    except OSError:
        return False


def _reserve_for(probe_path: Path, reserve_policy: VolumeReservePolicy) -> int:
    return (
        reserve_policy.system_volume_minimum_free_bytes
        if _is_system_volume(probe_path)
        else reserve_policy.non_system_volume_reserve_bytes
    )


def _is_within_or_equal(parent: Path, candidate: Path) -> bool:
    parent_r = parent.resolve()
    candidate_r = candidate.resolve()
    return candidate_r == parent_r or candidate_r.is_relative_to(parent_r)


def validate_root_topology(
    *,
    source_root: Path,
    raw_destination_root: Path,
    work_root: Path,
    extracted_destination_root: Path | None = None,
    receipt_path: Path | None = None,
    expected_manifest_path: Path | None = None,
) -> list[str]:
    """Reject dangerous root relationships before any filesystem mutation
    starts. The most dangerous case is a destination nested inside the
    source: a resumed operation would then enumerate its own previous
    output as part of the source and re-copy (or recursively expand) it.
    Called before any enumeration or space computation in
    preflight_space_budget() -- a topology violation is worse than a
    space shortfall and is checked first.
    """
    findings: list[str] = []
    if _is_within_or_equal(source_root, raw_destination_root):
        findings.append("raw_destination_root is inside (or equal to) source_root")
    if _is_within_or_equal(source_root, work_root):
        findings.append("work_root is inside (or equal to) source_root")
    if extracted_destination_root is not None:
        if _is_within_or_equal(source_root, extracted_destination_root):
            findings.append("extracted_destination_root is inside (or equal to) source_root")
        if extracted_destination_root.resolve() == raw_destination_root.resolve():
            findings.append("extracted_destination_root is identical to raw_destination_root")
        elif _is_within_or_equal(raw_destination_root, extracted_destination_root):
            findings.append("extracted_destination_root is nested inside raw_destination_root")
        elif _is_within_or_equal(extracted_destination_root, raw_destination_root):
            findings.append("raw_destination_root is nested inside extracted_destination_root")
    if receipt_path is not None and _is_within_or_equal(source_root, receipt_path):
        findings.append("receipt_path is inside source_root")
    if expected_manifest_path is not None and _is_within_or_equal(source_root, expected_manifest_path):
        findings.append("expected_manifest_path is inside source_root")
    return findings


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(_win_long_path(_existing_ancestor(path))).free


def _bytes_still_needed(
    source_root: Path,
    destination_root: Path,
    *,
    exclude: Callable[[str], bool] | None,
) -> tuple[int, int, list[str]]:
    """Bytes still required to complete a relocation into destination_root
    -- already-matching destination files (the resumable case) contribute
    zero, since resumable_copy_tree() will skip them. Symlinks contribute
    zero: preserving one costs a directory-entry-sized link, not the
    target's content size. A source file that cannot be stat'd produces a
    blocking finding rather than being silently excluded from the total
    (fail closed, not fail open).
    """
    files = enumerate_files(source_root)
    total = 0
    largest = 0
    blocking: list[str] = []
    for f in files:
        rel = f.relative_to(source_root).as_posix()
        if exclude is not None and exclude(rel):
            continue
        if _lp_is_symlink(f):
            continue
        try:
            size = _lp_stat(f).st_size
        except OSError:
            blocking.append(f"source_stat_failed:{rel}")
            continue
        destination_path = destination_root / rel
        if _matches_existing(f, destination_path):
            continue
        total += size
        largest = max(largest, size)
    return total, largest, blocking


def preflight_space_budget(
    *,
    source_root: Path,
    raw_destination_root: Path,
    work_root: Path,
    extracted_destination_root: Path | None = None,
    reserve_policy: VolumeReservePolicy = DEFAULT_VOLUME_RESERVE_POLICY,
    link_policy: str = LinkPolicy.REJECT_ALL,
    exclude: Callable[[str], bool] | None = None,
    receipt_path: Path | None = None,
    expected_manifest_path: Path | None = None,
) -> SpaceBudget:
    """Compute the PEAK space this relocation will actually require,
    modeled per real filesystem volume (`st_dev`), not per logical root --
    raw destination, extracted destination, and work root can be three
    separate volumes, two of the three, or all one, and the budget must
    reflect whichever is actually true rather than checking each root's
    requirement independently. Fails closed (ok=False) on: a dangerous
    root-topology relationship (checked first, before any enumeration --
    see validate_root_topology()), insufficient space on any volume, an
    unstatable source file, or -- under LinkPolicy.REJECT_ALL, the
    default -- any link entry at all, internal or external target alike
    (see check_link_entries()) -- nothing starts copying until every one
    of these passes.

    Demand modeled per volume:
    - raw/extracted destination volumes: bytes still needed (not yet
      matching) for that leg, plus one "atomic fallback" peak -- when
      resumable_copy_tree()'s _atomic_place() cannot rename directly
      across volumes (work_root cross-volume from the destination), it
      stages a same-directory temp copy before the final rename, so a
      single file's peak footprint on the destination volume can
      transiently reach ~2x that file's size, not just its final size.
    - work root volume: the single largest remaining file, since files are
      staged and moved one at a time, not all at once.
    - volumes shared by more than one of the above (e.g. raw destination
      and work root on the same drive) sum their demands rather than being
      checked independently, so two individually-passing checks can no
      longer both be true while the real combined operation runs out of
      space.

    `reserve_policy` sets the minimum free space each volume must retain
    after the operation, distinct for the system volume versus any other
    -- a flat 512 MiB margin does not protect the much larger operational
    floor this ATLAS engagement already established for the system drive
    (see SYSTEM_VOLUME_MINIMUM_FREE_BYTES). The policy actually used is
    recorded on the returned SpaceBudget so a caller override is bound
    into the relocation receipt, not silently applied.
    """
    topology_findings = validate_root_topology(
        source_root=source_root,
        raw_destination_root=raw_destination_root,
        work_root=work_root,
        extracted_destination_root=extracted_destination_root,
        receipt_path=receipt_path,
        expected_manifest_path=expected_manifest_path,
    )
    if topology_findings:
        # A topology violation is worse than a space shortfall -- do not
        # even enumerate the source, let alone compute demand, once one
        # is found.
        return SpaceBudget(
            volumes=[],
            safety_margin_bytes=reserve_policy.non_system_volume_reserve_bytes,
            ok=False,
            findings=list(topology_findings),
        )

    all_source_files = enumerate_files(source_root)
    all_source_directory_links = enumerate_directory_links(source_root)
    blocking_findings = list(
        check_link_entries(
            source_root, all_source_files, all_source_directory_links, link_policy=link_policy
        )
    )

    raw_needed, raw_largest, raw_blocking = _bytes_still_needed(source_root, raw_destination_root, exclude=exclude)
    blocking_findings.extend(raw_blocking)

    extracted_needed = 0
    extracted_largest = 0
    if extracted_destination_root is not None:
        extracted_needed, extracted_largest, extracted_blocking = _bytes_still_needed(
            source_root, extracted_destination_root, exclude=exclude
        )
        blocking_findings.extend(extracted_blocking)

    largest_remaining = max(raw_largest, extracted_largest)
    atomic_fallback_peak = largest_remaining  # see docstring: up to one extra full copy, transiently

    demands: dict[Any, dict[str, Any]] = {}

    def _add_demand(path: Path, bytes_needed: int, label: str) -> None:
        vol = _volume_id(path)
        entry = demands.setdefault(vol, {"probe_path": _existing_ancestor(path), "bytes": 0, "labels": []})
        entry["bytes"] += bytes_needed
        entry["labels"].append(f"{label}={bytes_needed}")

    _add_demand(raw_destination_root, raw_needed + atomic_fallback_peak, "raw_destination")
    if extracted_destination_root is not None:
        _add_demand(extracted_destination_root, extracted_needed + atomic_fallback_peak, "extracted_destination")
    _add_demand(work_root, largest_remaining, "work_staging")

    volumes: list[VolumeRequirement] = []
    findings = list(blocking_findings)
    for entry in demands.values():
        reserve = _reserve_for(entry["probe_path"], reserve_policy)
        required = entry["bytes"] + reserve
        available = _free_bytes(entry["probe_path"])
        volume_ok = available >= required
        if not volume_ok:
            findings.append(
                "insufficient_volume_space: "
                f"volume_probe={entry['probe_path']} required={required} available={available} "
                f"reserve={reserve} demands=[{', '.join(entry['labels'])}]"
            )
        volumes.append(
            VolumeRequirement(
                probe_path=entry["probe_path"],
                required_bytes=required,
                available_bytes=available,
                ok=volume_ok,
            )
        )

    ok = not blocking_findings and all(v.ok for v in volumes)
    return SpaceBudget(
        volumes=volumes,
        safety_margin_bytes=reserve_policy.non_system_volume_reserve_bytes,
        ok=ok,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# 6. Resumable, atomic copy -- REGULAR FILES ONLY
# ---------------------------------------------------------------------------
#
# See the module note above LinkPolicy (section 3): link entries are never
# copied here. resumable_copy_tree() rejects one defensively if it ever
# sees one, but the primary enforcement point is
# preflight_space_budget()/check_link_entries(), which blocks before this
# function is ever called on a tree containing a link.


class ResumableCopyError(Exception):
    def __init__(self, message: str, *, category: str = "staging_copy_failed"):
        super().__init__(message)
        self.category = category


@dataclass(frozen=True)
class CopyFailure:
    path: str
    category: str
    message_digest: str


@dataclass
class CopyResult:
    copied: list[str] = field(default_factory=list)
    skipped_already_present: list[str] = field(default_factory=list)
    failed: list[CopyFailure] = field(default_factory=list)
    total_bytes_copied: int = 0


def _copy_failure(path: str, exc: Exception, *, category: str) -> CopyFailure:
    # Bounded, reproducible failure reason: a digest of the error's repr,
    # not the raw text. Raw provider/system error text can disclose local
    # machine paths (already a real concern this module handles carefully
    # elsewhere -- see _win_long_path()); a digest is still useful for
    # correlating repeated failures without that exposure.
    return CopyFailure(
        path=path, category=category, message_digest=stable_json_digest({"error_repr": repr(exc)})
    )


def _matches_existing(source: Path, destination: Path) -> bool:
    """Regular-file resumability check only. A link source never reaches
    this function in the normal flow -- resumable_copy_tree() rejects
    link entries before considering whether they "match" anything."""
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
    """Copy exactly one regular file, resumably and atomically. Raises
    ResumableCopyError (with a bounded category) rather than attempting
    anything for a link source -- this is a defense-in-depth check, not
    the primary enforcement point: under LinkPolicy.REJECT_ALL,
    preflight_space_budget() already blocks before resumable_copy_tree()
    is ever called on a tree containing one."""
    if _is_reparse_point(source):
        raise ResumableCopyError(
            f"link entries are not copied under LinkPolicy.REJECT_ALL: {source}",
            category="unsupported_link_entry",
        )
    _lp_mkdir(destination.parent)
    stage_dir = work_root / "copy-staging"
    _lp_mkdir(stage_dir)
    stage_name = hashlib.sha1(str(destination).encode("utf-8")).hexdigest() + ".part"
    staged = stage_dir / stage_name
    if _lp_exists(staged):
        _lp_unlink(staged)
    try:
        _lp_copy2(source, staged)
    except OSError as exc:
        failing_path = str(getattr(exc, "filename", "") or "")
        category = "source_read_failed" if failing_path and failing_path in str(source) else "staging_copy_failed"
        raise ResumableCopyError(f"copy to staging failed for {source}: {exc}", category=category) from exc
    if file_checksum(staged) != file_checksum(source):
        _lp_unlink(staged, missing_ok=True)
        raise ResumableCopyError(f"staged copy checksum mismatch for {source}", category="checksum_mismatch")
    size = _lp_stat(staged).st_size
    try:
        _atomic_place(staged, destination)
    except OSError as exc:
        _lp_unlink(staged, missing_ok=True)
        raise ResumableCopyError(
            f"atomic replace into destination failed for {destination}: {exc}",
            category="destination_replace_failed",
        ) from exc
    return size


def resumable_copy_tree(
    source_root: Path,
    destination_root: Path,
    *,
    work_root: Path,
    exclude: Callable[[str], bool] | None = None,
) -> CopyResult:
    """Copy source_root's REGULAR FILE tree into destination_root,
    resumably and atomically per file. Link entries (file symlinks,
    directory symlinks, Windows junctions) are recorded as a bounded
    `unsupported_link_entry` failure, never copied or dereferenced -- see
    the module-level note above LinkPolicy for why. In the normal
    relocate_archive_source() flow this should never actually happen,
    since preflight_space_budget() already blocked before this function
    is called on a tree containing any link.

    Resumable: on re-invocation after an interruption, any destination
    file that already matches the source (same size and checksum) is
    skipped rather than re-copied, so an interrupted run can simply be
    re-run to completion.

    Atomic per file: each file is staged under work_root, checksum-
    verified against the source, and only then moved into
    destination_root with an atomic rename (see _atomic_place).
    destination_root never contains a partially-written file, even if the
    process is killed mid-copy.
    """
    files = enumerate_files(source_root)
    result = CopyResult()
    for source_path in files:
        rel = source_path.relative_to(source_root).as_posix()
        if exclude is not None and exclude(rel):
            continue
        destination_path = destination_root / rel
        if _is_reparse_point(source_path):
            result.failed.append(_copy_failure(rel, ResumableCopyError("link entry"), category="unsupported_link_entry"))
            continue
        if _matches_existing(source_path, destination_path):
            result.skipped_already_present.append(rel)
            continue
        try:
            size = _copy_one_resumable(source_path, destination_path, work_root=work_root)
            result.copied.append(rel)
            result.total_bytes_copied += size
        except (OSError, ResumableCopyError) as exc:
            category = getattr(exc, "category", "staging_copy_failed")
            result.failed.append(_copy_failure(rel, exc, category=category))
    return result


# ---------------------------------------------------------------------------
# 7. Relocation manifests
# ---------------------------------------------------------------------------


def _classify_link_entry(path: Path, *, root: Path, is_directory_entry: bool) -> dict[str, Any]:
    """Canonical, location-independent classification of a link entry for
    manifest/diagnostic purposes -- kind, and whether its target is
    confined within root ('internal', with a root-relative target_path
    two logically-identical trees produce the same entry for regardless
    of where either physically lives) or escapes it ('external', where
    only a bounded target_digest is recorded -- never the full external
    path, which could disclose machine-specific detail in a broadly
    retained receipt). This is diagnostic inventory only: Wave 1 never
    copies a link (see LinkPolicy.REJECT_ALL), so this is what lets a
    caller see precisely what was found and rejected.
    """
    kind = _link_entry_kind(path, is_directory_entry=is_directory_entry)
    try:
        resolved_target = _win_long_path(path).resolve()
    except OSError:
        return {"kind": kind, "target_scope": "unresolvable"}
    normal_root = _win_long_path(root).resolve()
    try:
        rel_target = resolved_target.relative_to(normal_root)
        return {"kind": kind, "target_scope": "internal", "target_path": rel_target.as_posix()}
    except ValueError:
        return {
            "kind": kind,
            "target_scope": "external",
            "target_digest": stable_json_digest({"resolved_target": str(resolved_target)}),
        }


def build_relocation_manifest(root: Path, *, exclude: Callable[[str], bool] | None = None) -> dict[str, Any]:
    """Build a manifest of `root`'s current real content via long-path-safe
    enumeration -- files, file symlinks, and directory symlinks/junctions
    (see enumerate_directory_links()) alike. Contains relative paths,
    kinds, sizes, and checksums; a link entry's checksum is derived from
    its canonical classification (see _classify_link_entry()), not raw
    target text, so two logically-identical trees produce the same
    checksum for a link regardless of where either physically lives -- no
    reference to drive letters or any storage mechanism -- so the
    manifest reconciles identically regardless of how `root` is currently
    reached. A directory link's own target is never traversed into for
    this manifest; the link is one entry, not a subtree. Wave 1 never
    copies a link entry (LinkPolicy.REJECT_ALL); this remains a
    diagnostic inventory usable independently of that policy.
    """
    files = enumerate_files(root)
    directory_links = enumerate_directory_links(root)
    directory_link_set = set(directory_links)
    entries: list[dict[str, Any]] = []
    for path in list(files) + list(directory_links):
        rel = path.relative_to(root).as_posix()
        if exclude is not None and exclude(rel):
            continue
        if _is_reparse_point(path):
            classification = _classify_link_entry(path, root=root, is_directory_entry=path in directory_link_set)
            entries.append(
                {
                    "path": rel,
                    "size_bytes": 0,
                    "checksum": stable_json_digest(classification),
                    **classification,
                }
            )
            continue
        entries.append(
            {
                "path": rel,
                "kind": "file",
                "size_bytes": _lp_stat(path).st_size,
                "checksum": file_checksum(path),
            }
        )
    entries.sort(key=lambda e: _sort_key(e["path"]))
    return {
        "contract_version": RELOCATION_MANIFEST_VERSION,
        "entry_count": len(entries),
        "total_bytes": sum(e["size_bytes"] for e in entries),
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# 8. Restore verification
# ---------------------------------------------------------------------------


def verify_restore(*, manifest: dict[str, Any], root: Path, require_exact_match: bool = True) -> dict[str, Any]:
    """Independently re-walk `root` and reconcile it against a previously
    recorded manifest. Junction-independent: only current, real content
    reachable at `root` via long-path-safe enumeration is considered, so a
    manifest recorded before a junction existed (or after the junction is
    gone and the data lives at a plain path) reconciles the same way.

    `require_exact_match` (default True) means an unexpected extra file at
    `root` -- content the manifest never described -- fails verification,
    not only a missing or mismatched one. This is the relocation-proof
    default deliberately: a destination that silently accumulated
    unrelated content should not read as "verified." Pass False only for
    an explicit allow-extra use case; unexpected paths are still reported
    either way.
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
    ok = not missing and not mismatched and (not require_exact_match or not unexpected)
    return {
        "contract_version": RESTORE_VERIFICATION_VERSION,
        "root": str(root),
        "require_exact_match": require_exact_match,
        "expected_entry_count": len(expected_by_path),
        "current_entry_count": len(current_by_path),
        "missing_paths": missing,
        "unexpected_paths": unexpected,
        "mismatched_paths": mismatched,
        "ok": ok,
    }


# ---------------------------------------------------------------------------
# 9. Durable relocation receipts
# ---------------------------------------------------------------------------


def _serialize_copy_failures(failures: list[CopyFailure]) -> list[dict[str, str]]:
    return [{"path": f.path, "category": f.category, "message_digest": f.message_digest} for f in failures]


def build_relocation_receipt(
    *,
    archive_id: str,
    source_description: str,
    destination_root: Path,
    raw_copy_result: CopyResult,
    extracted_copy_result: CopyResult | None,
    expected_manifest: dict[str, Any],
    expected_manifest_ref: str | None,
    destination_manifest: dict[str, Any],
    space_budget: SpaceBudget,
    exclusion_policy: ExclusionPolicy,
    excluded_paths: list[str],
    destination_verification: dict[str, Any],
    extracted_verification: dict[str, Any] | None,
    ok: bool,
) -> dict[str, Any]:
    return {
        "contract_version": RELOCATION_RECEIPT_VERSION,
        "archive_id": archive_id,
        "recorded_at": utc_now_iso(),
        "source_description": source_description,
        "destination_root": str(destination_root),
        "exclusion_policy_id": exclusion_policy.policy_id,
        "exclusion_policy_version": exclusion_policy.version,
        "excluded_path_count": len(excluded_paths),
        "excluded_paths_digest": stable_json_digest(excluded_paths),
        "raw_leg": {
            "files_copied": len(raw_copy_result.copied),
            "files_skipped_already_present": len(raw_copy_result.skipped_already_present),
            "files_failed": _serialize_copy_failures(raw_copy_result.failed),
            "bytes_copied": raw_copy_result.total_bytes_copied,
            "ok": not raw_copy_result.failed,
        },
        "extracted_leg": (
            {
                "files_copied": len(extracted_copy_result.copied),
                "files_skipped_already_present": len(extracted_copy_result.skipped_already_present),
                "files_failed": _serialize_copy_failures(extracted_copy_result.failed),
                "bytes_copied": extracted_copy_result.total_bytes_copied,
                "ok": not extracted_copy_result.failed,
            }
            if extracted_copy_result is not None
            else None
        ),
        # expected_manifest_ref: where the full expected-manifest content
        # (not just its digest) was durably persisted, when it was --
        # a digest alone cannot reconstruct the expected entries for a
        # later restore proof once the process that computed it has
        # exited. destination_manifest is deliberately digest-only: it is
        # always recomputable on demand from a live destination_root via
        # build_relocation_manifest(), so persisting it separately would
        # be redundant with what is already sitting on disk.
        "expected_manifest_ref": expected_manifest_ref,
        "expected_manifest_digest": stable_json_digest(expected_manifest),
        "destination_manifest_digest": stable_json_digest(destination_manifest),
        "destination_verification": destination_verification,
        "extracted_verification": extracted_verification,
        "space_budget": {
            "safety_margin_bytes": space_budget.safety_margin_bytes,
            "ok": space_budget.ok,
            "findings": list(space_budget.findings),
            "volumes": [
                {
                    "probe_path": str(v.probe_path),
                    "required_bytes": v.required_bytes,
                    "available_bytes": v.available_bytes,
                    "ok": v.ok,
                }
                for v in space_budget.volumes
            ],
        },
        "ok": ok,
    }


def _write_json_atomic(payload: dict[str, Any], path: Path) -> None:
    """Atomically persist a JSON document to disk. Written to a
    same-directory temp file first, then moved into place with an atomic,
    no-follow rename (see _atomic_place / _lp_replace), so a reader never
    observes a partially-written file and a planted symlink at `path`
    cannot redirect the write."""
    _lp_mkdir(path.parent)
    temp_path = path.parent / f"{path.name}.{os.getpid()}.tmp"
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    _win_long_path(temp_path).write_text(text, encoding="utf-8")
    _atomic_place(temp_path, path)


def _read_json_atomic(path: Path) -> dict[str, Any]:
    return json.loads(_win_long_path(path).read_text(encoding="utf-8"))


def write_relocation_receipt(receipt: dict[str, Any], path: Path) -> None:
    _write_json_atomic(receipt, path)


def read_relocation_receipt(path: Path) -> dict[str, Any]:
    return _read_json_atomic(path)


def write_relocation_manifest(manifest: dict[str, Any], path: Path) -> None:
    """Durably persist the manifest itself, not only its digest. At
    minimum the expected (source-anchored) manifest should be persisted
    this way -- a receipt's expected_manifest_digest alone gives no way
    to reconstruct the expected entries for a later restore proof once
    the process that computed it has exited."""
    _write_json_atomic(manifest, path)


def read_relocation_manifest(path: Path) -> dict[str, Any]:
    return _read_json_atomic(path)


def validate_relocation_receipt_semantics(receipt: dict[str, Any]) -> list[str]:
    """Beyond schema-shape validation, check that a receipt's own claims
    are mutually consistent. A closed schema shape alone can still accept
    an internally contradictory receipt -- e.g. raw_leg.ok=true with a
    non-empty raw_leg.files_failed. Runtime readback should reject
    incoherent evidence rather than trust a shape-valid but self-
    contradictory record.
    """
    findings: list[str] = []
    raw_leg = receipt.get("raw_leg") or {}
    if raw_leg.get("files_failed") and raw_leg.get("ok"):
        findings.append("raw_leg.ok is true but raw_leg.files_failed is non-empty")
    if not raw_leg.get("files_failed") and raw_leg.get("ok") is False:
        findings.append("raw_leg.ok is false but raw_leg.files_failed is empty")

    extracted_leg = receipt.get("extracted_leg")
    if extracted_leg is not None:
        if extracted_leg.get("files_failed") and extracted_leg.get("ok"):
            findings.append("extracted_leg.ok is true but extracted_leg.files_failed is non-empty")
        if not extracted_leg.get("files_failed") and extracted_leg.get("ok") is False:
            findings.append("extracted_leg.ok is false but extracted_leg.files_failed is empty")

    destination_verification = receipt.get("destination_verification") or {}
    space_budget = receipt.get("space_budget") or {}
    extracted_verification = receipt.get("extracted_verification")

    if receipt.get("ok"):
        if raw_leg.get("ok") is False:
            findings.append("receipt.ok is true but raw_leg.ok is false")
        if extracted_leg is not None and extracted_leg.get("ok") is False:
            findings.append("receipt.ok is true but extracted_leg.ok is false")
        if destination_verification and destination_verification.get("ok") is False:
            findings.append("receipt.ok is true but destination_verification.ok is false")
        if extracted_verification is not None and extracted_verification.get("ok") is False:
            findings.append("receipt.ok is true but extracted_verification.ok is false")
        if space_budget and space_budget.get("ok") is False:
            findings.append("receipt.ok is true but space_budget.ok is false")
    return findings


# ---------------------------------------------------------------------------
# 10. High-level composed entry point (opt-in; not wired into the existing
#     import_archive() default in this PR -- see PR body / docs for why)
# ---------------------------------------------------------------------------


@dataclass
class RelocationResult:
    ok: bool
    space_budget: SpaceBudget
    raw_copy_result: CopyResult | None
    extracted_copy_result: CopyResult | None
    expected_manifest: dict[str, Any] | None
    destination_manifest: dict[str, Any] | None
    destination_verification: dict[str, Any] | None
    extracted_verification: dict[str, Any] | None
    receipt: dict[str, Any] | None


def relocate_archive_source(
    *,
    archive_id: str,
    source_root: Path,
    destination_root: Path,
    work_root: Path,
    source_description: str,
    materialize_extracted_root: Path | None = None,
    exclusion_policy: ExclusionPolicy = NO_EXCLUSION_POLICY,
    require_exact_match: bool = True,
    receipt_path: Path | None = None,
    expected_manifest_path: Path | None = None,
    reserve_policy: VolumeReservePolicy = DEFAULT_VOLUME_RESERVE_POLICY,
    link_policy: str = LinkPolicy.REJECT_ALL,
) -> RelocationResult:
    """Compose the full Wave 1 architecture into one call: root-topology
    validation, preflight, one raw preservation copy, optional selective
    extracted materialization, a source-anchored expected manifest, exact
    destination reconciliation, and a relocation receipt.

    `link_policy` defaults to LinkPolicy.REJECT_ALL, the only policy this
    module ships: any file symlink, directory symlink, or Windows
    junction found under source_root fails the preflight with a
    structured `unsupported_link_entry` finding per entry, before any
    copy starts. This module does not attempt to preserve link semantics
    -- see the note above LinkPolicy for why.

    `exclusion_policy` defaults to NO_EXCLUSION_POLICY: raw preservation
    means every admitted source entry is preserved by default, including
    `.git` and anything else -- filtering is available (pass
    GENERATED_CACHE_EXCLUSION_POLICY, or a caller-defined policy) but is
    never silently applied to what claims to be a preservation copy.

    `materialize_extracted_root`, when given, makes a second copy at that
    location -- this is the "selective" part: callers opt in explicitly
    per invocation rather than getting a second copy by default. Its
    result is tracked and verified independently; a failure there fails
    the whole operation, it is never silently discarded.

    The proof this produces is source-anchored, not self-referential: the
    expected manifest is built from source_root BEFORE any copy happens,
    with the exclusion policy already applied, and destination_root is
    reconciled against that expected manifest afterward -- not against a
    manifest built from the destination itself, which would only prove the
    destination still matched itself a moment later.

    Passing `receipt_path` durably persists the receipt via
    write_relocation_receipt(). Passing `expected_manifest_path` durably
    persists the expected manifest itself (not just its digest) via
    write_relocation_manifest() -- at minimum this should be given,
    since a digest alone cannot reconstruct the expected entries for a
    later restore proof once this process has exited; the destination
    manifest is not separately persisted since it is always recomputable
    on demand from a live destination_root.

    `reserve_policy` and the root-topology check (dangerous nesting
    between source/destination/work/receipt/manifest paths) are enforced
    inside preflight_space_budget() before anything is enumerated or
    copied -- see that function and validate_root_topology().
    """
    exclude = exclusion_policy.predicate

    budget = preflight_space_budget(
        source_root=source_root,
        raw_destination_root=destination_root,
        work_root=work_root,
        extracted_destination_root=materialize_extracted_root,
        reserve_policy=reserve_policy,
        link_policy=link_policy,
        exclude=exclude,
        receipt_path=receipt_path,
        expected_manifest_path=expected_manifest_path,
    )
    if not budget.ok:
        # Topology or space failures are both checked before any
        # enumeration of source content beyond what the preflight itself
        # needed, so no expected_manifest is built here either.
        return RelocationResult(
            ok=False,
            space_budget=budget,
            raw_copy_result=None,
            extracted_copy_result=None,
            expected_manifest=None,
            destination_manifest=None,
            destination_verification=None,
            extracted_verification=None,
            receipt=None,
        )

    all_source_files = enumerate_files(source_root)
    excluded_paths = sorted(
        f.relative_to(source_root).as_posix()
        for f in all_source_files
        if exclude(f.relative_to(source_root).as_posix())
    )
    expected_manifest = build_relocation_manifest(source_root, exclude=exclude)
    expected_manifest_ref: str | None = None
    if expected_manifest_path is not None:
        write_relocation_manifest(expected_manifest, expected_manifest_path)
        expected_manifest_ref = str(expected_manifest_path)

    raw_copy_result = resumable_copy_tree(source_root, destination_root, work_root=work_root, exclude=exclude)

    extracted_copy_result: CopyResult | None = None
    extracted_verification: dict[str, Any] | None = None
    if materialize_extracted_root is not None:
        extracted_copy_result = resumable_copy_tree(
            source_root, materialize_extracted_root, work_root=work_root, exclude=exclude
        )
        extracted_verification = verify_restore(
            manifest=expected_manifest,
            root=materialize_extracted_root,
            require_exact_match=require_exact_match,
        )

    destination_manifest = build_relocation_manifest(destination_root)
    destination_verification = verify_restore(
        manifest=expected_manifest, root=destination_root, require_exact_match=require_exact_match
    )

    raw_failed = bool(raw_copy_result.failed)
    extracted_failed = bool(extracted_copy_result.failed) if extracted_copy_result is not None else False
    verification_failed = not destination_verification["ok"] or (
        extracted_verification is not None and not extracted_verification["ok"]
    )
    ok = not raw_failed and not extracted_failed and not verification_failed

    receipt = build_relocation_receipt(
        archive_id=archive_id,
        source_description=source_description,
        destination_root=destination_root,
        raw_copy_result=raw_copy_result,
        extracted_copy_result=extracted_copy_result,
        expected_manifest=expected_manifest,
        expected_manifest_ref=expected_manifest_ref,
        destination_manifest=destination_manifest,
        space_budget=budget,
        exclusion_policy=exclusion_policy,
        excluded_paths=excluded_paths,
        destination_verification=destination_verification,
        extracted_verification=extracted_verification,
        ok=ok,
    )
    if receipt_path is not None:
        write_relocation_receipt(receipt, receipt_path)

    return RelocationResult(
        ok=ok,
        space_budget=budget,
        raw_copy_result=raw_copy_result,
        extracted_copy_result=extracted_copy_result,
        expected_manifest=expected_manifest,
        destination_manifest=destination_manifest,
        destination_verification=destination_verification,
        extracted_verification=extracted_verification,
        receipt=receipt,
    )
