# ATLAS Import Storage Convergence -- Wave S / Wave 1

## Scope

Wave 1 delivers reusable knowledge-import pipeline architecture only:

- first-class, independently configurable storage/work roots
  (`ATLAS_IMPORT_STORAGE_ROOT`, `ATLAS_IMPORT_WORK_ROOT`)
- long-path-safe deterministic file enumeration
- symlink confinement (external-target file symlinks rejected before any
  copy starts)
- per-volume peak-space preflight budgeting
- resumable, atomic file copy (including symlink preservation)
- explicit, named, opt-in generated-cache exclusion policy (never applied
  by default to a raw preservation copy)
- a source-anchored relocation manifest, copy, and exact destination
  reconciliation
- durably persisted relocation receipts and restore verification

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

### Long-path-safe, anchor-stable I/O

Every filesystem touch in `storage.py` -- enumeration, `mkdir`, `stat`,
`lstat`, `copy2`, `replace`, `unlink`, `symlink`, `readlink`, `open` --
routes through a small set of `_lp_*` wrappers that apply Windows' `\\?\`
extended-length-path prefix before the real OS call, and are a no-op on
non-Windows platforms.

`enumerate_files(root)` returns entries anchored to `root` exactly as
passed (`root / <relative-path>`), never `root.resolve() / <relative-path>`.
This was a real, hosted-CI-caught bug during development: that Windows
runner's temp directory resolves through an 8.3 short-name alias
(`RUNNER~1` vs `runneradmin`), so a caller doing `entry.relative_to(root)`
against its own original `root` broke when entries were anchored to a
resolved copy instead. Sort order matches the previous `rglob()`-based
enumeration's per-platform behavior exactly (case-sensitive on POSIX,
case-insensitive on Windows, since `pathlib.Path` ordering is
case-insensitive there) -- a plain POSIX-string sort would have silently
reordered mixed-case siblings relative to the old implementation, which
would have changed `tree_digest()` output for any tree with case-differing
filenames even though nothing about the tree's content changed.

`ops/knowledge/_pipeline.py`'s `list_files()` now delegates to this
function. This is the one live-pipeline change in this PR, and it is a
pure correctness fix: identical signature, identical return type,
identical sort order, identical behavior for any path under the limit --
proven directly by a compatibility test comparing old- and new-derived
relative-path sets and orderings for an ordinary mixed-case tree.

### Symlink confinement

`enumerate_files()` uses `lstat`, not `stat`, so symlinks are enumerated
as themselves without being silently followed. `check_symlink_confinement()`
rejects (as a blocking preflight finding) any file symlink whose real
target resolves outside the admitted source root -- without this, a
staged archive could contain `innocent-name.txt -> /somewhere/else/entirely`
and `shutil.copy2()` would silently copy content from outside the admitted
root into the "preserved" destination. A symlink whose target stays inside
the source root is preserved as a symlink during copy (see
`_copy_one_symlink_resumable()`), not dereferenced into a regular-file
copy of its target's content.

### Peak-space preflight, modeled per real volume

`preflight_space_budget()` groups demand by actual filesystem volume
(`st_dev`), not by logical root name -- raw destination, extracted
destination, and work root can be three separate volumes, two of the
three, or all one, and the budget reflects whichever is actually true
rather than checking each root independently (two individually-passing
checks could previously both be true while the real combined operation
ran out of space). Per volume, demand includes:

- bytes still needed for that leg (resumable: already-matching
  destination content contributes nothing, so a mostly-complete resume
  budgets only the remainder)
- an "atomic fallback peak" -- when `resumable_copy_tree()`'s
  `_atomic_place()` cannot rename directly across volumes, it stages a
  same-directory temp copy before the final rename, so a single file's
  transient footprint on the destination volume can reach roughly 2x that
  file's size, not just its final size
- the work root's single largest remaining file (files are staged and
  moved one at a time, not all at once)

A source file that cannot be stat'd is a **blocking** finding -- it does
not silently drop out of the byte estimate the way an earlier draft of
this preflight did. Symlink-confinement violations are blocking findings
here too, so nothing copies until every check passes.

### Resumable, atomic copy

`resumable_copy_tree()`: re-run skips already-matching destination
entries (checksum match for regular files, same link target for
symlinks); each regular file is staged, checksum-verified, then atomically
moved into place, so the destination never shows a partial file.

### Generated-cache exclusion: named, opt-in, never the raw default

`GENERATED_CACHE_EXCLUSION_PATTERNS` / `is_generated_cache_path()` --
explicit and documented, not a broad heuristic. The Unity entries
(`Library/PackageCache`, `Library/APIUpdater/ConfigurationCache`,
`Library/ScriptAssemblies`, `Library/Bee`) are the exact classes
root-caused as stale, fully-regenerable-from-source content during a
prior real import's reconciliation. `Temp`, `obj`, `node_modules`, and
`__pycache__` are similarly well-established, never-unique generated
content. **`.git` is deliberately not in this list** -- it is
version-control data (history, reflogs, unreachable objects,
repository configuration, unpushed work objects), never generated cache,
and a "raw preservation copy" must not silently drop it.

`ExclusionPolicy` gives an exclusion predicate a stable identity and
version (`policy_id`, `version`) so the receipt can bind exactly which
named policy was applied, not just its behavior. `relocate_archive_source()`
defaults to `NO_EXCLUSION_POLICY`: raw preservation preserves every
admitted source entry by default. `GENERATED_CACHE_EXCLUSION_POLICY` is
available for callers that explicitly want a filtered (e.g. catalog or
selective-extracted) view.

### Source-anchored manifest, copy, and exact reconciliation

The expected manifest is built from `source_root` **before** any copy
happens, with the chosen exclusion policy already applied -- the
authoritative statement of what the relocation is supposed to produce.
After copying, `destination_root` is reconciled against that
source-anchored manifest, not against a manifest built from the
destination itself (which would only prove the destination still matched
itself a moment later, and would silently certify any pre-existing
unrelated content already sitting at the destination). `verify_restore()`'s
`require_exact_match` (default `True`) fails closed on missing,
mismatched, **and unexpected** paths -- an unexplained extra file at the
destination does not read as "verified" by default; an explicit
`require_exact_match=False` allow-extra mode exists for callers that
genuinely want it, but it is never the default.

### Durable relocation receipts

`build_relocation_receipt()` binds, per
`schemas/atlas.knowledge-relocation-receipt.v1.json` (closed schema,
draft 2020-12): the exclusion policy id/version and excluded-path count
and digest, the raw copy leg and the extracted copy leg (independently --
a failure in either fails the whole receipt, neither is silently
discarded), the source-anchored expected-manifest digest and the
destination-manifest digest, destination (and extracted, if requested)
verification results, and the full per-volume space-budget outcome.
`write_relocation_receipt()` / `read_relocation_receipt()` persist and
read back a receipt atomically (same-directory temp file, then atomic
rename) -- an in-memory dict alone is not yet a durable receipt.

**Note on this repo's schema validator:** `ops/atlas/ui_standards/validate.py`
falls back to a dependency-free subset validator when the `jsonschema`
package is unavailable (the case in this environment). That fallback does
not support `$ref` combined with sibling keywords, `oneOf`, or `anyOf`, so
the schema expresses nullable object fields (`extracted_leg`,
`extracted_verification`) as `type: ["object", "null"]` with properties
declared inline, duplicated rather than shared via `$ref`, so the schema
is genuinely enforced under both the real validator and the fallback.

### Composed entry point

`relocate_archive_source()` composes preflight, the raw copy, optional
selective (opt-in, via `materialize_extracted_root`) extracted
materialization -- independently tracked and verified, not discarded --
manifest, exact reconciliation, and receipt into one call. Overall `ok`
requires: the space preflight passed, the raw leg copied with zero
failures, the extracted leg (if requested) copied with zero failures, and
destination (and extracted, if requested) verification found no missing,
mismatched, or unexpected paths.

**This entry point is new and not wired into the existing
`import_archive()` default in this PR.** `import_archive()`'s current
double-copy behavior for folder inputs is unchanged. Adopting
`relocate_archive_source()` as `import_archive()`'s implementation is
follow-on work, deliberately left out of Wave 1 so this PR does not change
any behavior of the actively-used live import path -- only `list_files()`
changes, and only in a way proven to be a pure correctness fix.

## Tests

`tests/test_atlas_knowledge_storage.py` -- 63 tests (58 unconditional, 5
symlink-preservation/confinement tests that gracefully skip in
environments lacking symlink-creation privilege, e.g. non-admin Windows
without Developer Mode), including:

- a genuine >260-character path fixture proving long-path safety directly
- a deterministic Windows-only regression test reproducing the exact
  8.3-short-name-alias mismatch shape found on hosted CI
- a Windows-only mixed-case sort-order compatibility test, plus a
  cross-platform old-vs-new relative-path-set compatibility test against
  `_pipeline.list_files()`
- external-symlink rejection (blocking preflight, before any copy starts)
  and internal-symlink preservation-as-a-link
- per-volume preflight: aggregation when roots share a volume, independent
  accounting when they don't, fail-closed on an unstatable source file,
  budgeting only the remaining bytes on a resumed operation
- resumability (full copy / re-run skips / interrupted-and-resumed / stale
  content re-copied) and atomicity (a failed staged copy leaves no partial
  destination file)
- source-anchored verification: an undercopy that a buggy copy step
  silently drops is still caught (proving the proof isn't
  self-referential), and pre-existing unrelated destination content is
  caught as unexpected rather than silently certified
- an extracted-leg-only failure (raw leg succeeds) still fails the whole
  composed result
- durable receipt round-trip (write, then independently read back)
- lossless raw-preservation default, including `.git` and generated-cache-shaped
  content, both preserved by default
- a named exclusion policy bound into the receipt's `exclusion_policy_id`
- full receipt schema validation (well-formed with and without an
  extracted leg, five malformed shapes rejected)

No real archive data anywhere in this PR -- every fixture is synthetic,
created and destroyed within its own test.

## Hosted CI

`.github/workflows/atlas-knowledge-storage-convergence.yml` -- path-filtered
to this change's own files, matrix over `[ubuntu-latest, windows-latest]`,
runs `python -m unittest tests.test_atlas_knowledge_storage -v` directly.
