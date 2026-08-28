# ATLAS Import Storage Convergence -- Wave S / Wave 1

## Scope

Wave 1 delivers reusable knowledge-import pipeline architecture only:

- first-class, independently configurable storage/work roots
  (`ATLAS_IMPORT_STORAGE_ROOT`, `ATLAS_IMPORT_WORK_ROOT`)
- long-path-safe deterministic file enumeration
- peak-space preflight budgeting
- resumable, atomic file copy
- explicit, documented generated-cache exclusions
- junction-independent relocation manifests
- relocation receipts (`schemas/atlas.knowledge-relocation-receipt.v1.json`)
- restore verification

**Wave 1 explicitly does not include:**

- migrating or repairing `personal--onedrive-desktop`
- repairing the nine stale digest receipts associated with that import
- `#142` Board Authority work
- Fitness
- Mazer
- `C:\ATLAS` dirty-tree cleanup

Those are follow-on lanes tracked separately, not part of this change.

## Why

`ops/knowledge/_pipeline.py`'s prior file enumeration
(`root.rglob("*")`) is not long-path-safe on Windows: `rglob()` can
silently drop entries once the full path exceeds the classic 260-character
`MAX_PATH` boundary, unless the process-wide `LongPathsEnabled` registry
policy is set (admin rights required, not guaranteed). This is the exact
defect that produced a 290-file gap in a prior real import's manifest.
`import_archive()`'s folder-input path also unconditionally makes two full
copies (`raw/` and `extracted/`) of the same content by default, and there
was no first-class way to point either the durable archive or the
transient working state at a drive other than wherever `ATLAS_ROOT`
happens to be checked out.

## New module: `ops/knowledge/storage.py`

Self-contained, standalone -- it has no dependency on `_pipeline.py`, and
is imported the other direction (`_pipeline.py` imports `storage.py`).

### Storage/work roots

```
ATLAS_IMPORT_STORAGE_ROOT   -- durable archival data (raw preservation
                                copies, manifests, receipts)
ATLAS_IMPORT_WORK_ROOT      -- transient staging: resumable-copy temp
                                state, extraction scratch space
```

Both default to their pre-existing ATLAS-relative locations
(`data/imports/knowledge`, `runtime/knowledge-import-work`) when
unconfigured, so nothing that never sets these variables changes behavior.
Setting either lets a caller point that root at a different drive.

### Long-path-safe I/O

Every filesystem touch in `storage.py` -- enumeration, `mkdir`, `stat`,
`copy2`, `replace`, `unlink`, `open` -- routes through a small set of
`_lp_*` wrappers that apply Windows' `\\?\` extended-length-path prefix
before the real OS call, and are a no-op on non-Windows platforms. This
was not a theoretical concern: constructing this change's own test
fixtures with plain `Path.mkdir()` failed past `MAX_PATH` on the machine
this was developed on, which is itself a live demonstration of why every
touch point needs this, not only the top-level directory walk.

`enumerate_files(root)` returns plain (non-prefixed) `Path` objects rooted
at `root.resolve()`, in deterministic sorted order, so it is a drop-in
replacement for the previous `list_files()` contract. Every enumerated
entry is confirmed statable at enumeration time; a genuine long-path
failure raises `LongPathEnumerationError` instead of silently vanishing.

`ops/knowledge/_pipeline.py`'s `list_files()` now delegates to this
function. This is the one live-pipeline change in this PR, and it is a
pure correctness fix: identical signature, identical return type,
identical behavior for any path under the limit.

### Peak-space preflight

`preflight_space_budget()` computes the actual peak space a relocation
will require -- tree size (doubled only if selective extracted
materialization is requested) for the storage root, plus the single
largest file for the work root, since files are staged and moved one at a
time rather than all at once -- and compares it against real free space on
both roots via `shutil.disk_usage()`. Fails closed (`ok=False`,
structured `findings`) rather than letting a copy start and run out of
disk mid-operation.

### Resumable, atomic copy

`resumable_copy_tree()` copies a source tree into a destination root:

- **Resumable**: re-running after an interruption skips any destination
  file that already matches the source by size and checksum, rather than
  re-copying it.
- **Atomic per file**: each file is staged under the work root,
  checksum-verified against the source, then moved into place with an
  atomic rename (`os.replace`, falling back to a same-directory temp copy
  + rename for cross-volume staging). The destination never shows a
  partially-written file, even if the process is killed mid-copy.

### Generated-cache exclusions

`GENERATED_CACHE_EXCLUSION_PATTERNS` / `is_generated_cache_path()` -- an
explicit, documented list rather than a broad heuristic. The Unity
entries (`Library/PackageCache`, `Library/APIUpdater/ConfigurationCache`,
`Library/ScriptAssemblies`, `Library/Bee`) are the exact classes
root-caused as stale, fully-regenerable-from-source content during a
prior real import's reconciliation. `Temp`, `obj`, `node_modules`,
`__pycache__`, and `.git` are included as similarly well-established,
never-unique generated content. If a real archive genuinely needs one of
these preserved, pass `exclude=None` (or a narrower predicate) explicitly
-- nothing is excluded silently without this being visible in the call
site.

### Junction-independent manifests and restore verification

`build_relocation_manifest()` records only relative paths, sizes, and
checksums -- no reference to junctions, drive letters, or any specific
storage mechanism. `verify_restore()` independently re-walks a root and
reconciles it against a previously recorded manifest; a test proves this
reconciles identically whether the manifest was built at the original
location or the same content was later found at a completely different
path, which is exactly the junction-independence property required.

### Relocation receipts

`build_relocation_receipt()` produces a record conforming to
`schemas/atlas.knowledge-relocation-receipt.v1.json` (closed schema,
draft 2020-12): what was copied, whether the space preflight passed, and
the resulting manifest digest.

### Composed entry point

`relocate_archive_source()` composes preflight, copy, manifest, receipt,
and restore verification into one call. Raw preservation is the default;
passing `materialize_extracted_root` opts in to an additional extracted
copy at a caller-chosen location -- this is the "selective" part of
selective extracted materialization: opt-in per call, not automatic.

**This entry point is new and not wired into the existing
`import_archive()` default in this PR.** `import_archive()`'s current
double-copy behavior for folder inputs is unchanged. Adopting
`relocate_archive_source()` as `import_archive()`'s implementation is
follow-on work, deliberately left out of Wave 1 so this PR does not change
any behavior of the actively-used live import path -- only `list_files()`
changes, and only in a way that is a pure correctness fix.

## Tests

`tests/test_atlas_knowledge_storage.py` -- 36 tests covering every
component above, including:

- a genuine >260-character path fixture proving long-path safety directly,
  not by assumption
- a `_pipeline.list_files()` regression test proving the delegation works
  end to end
- resumability (full copy, re-run-skips, interrupted-and-resumed,
  stale-content-is-recopied)
- atomicity (a failed staged copy leaves no partial file at the
  destination)
- fail-closed space preflight
- manifest round-trip and junction-independence
- relocation-receipt schema validation (well-formed accepted, five
  malformed shapes rejected)
- two full synthetic end-to-end fixtures (raw-only default, and with
  selective extracted materialization) -- no real archive data anywhere in
  this test file

## Hosted CI

`.github/workflows/atlas-knowledge-storage-convergence.yml` -- path-filtered
to this change's own files, matrix over `[ubuntu-latest, windows-latest]`,
runs `python -m unittest tests.test_atlas_knowledge_storage -v` directly.
