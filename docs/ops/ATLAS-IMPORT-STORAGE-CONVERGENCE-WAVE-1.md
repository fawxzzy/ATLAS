# ATLAS Import Storage Convergence -- Wave S / Wave 1

## Scope

Wave 1 delivers reusable knowledge-import pipeline architecture only:

- first-class, independently configurable storage/work roots
  (`ATLAS_IMPORT_STORAGE_ROOT`, `ATLAS_IMPORT_WORK_ROOT`)
- long-path-safe deterministic file enumeration
- symlink and Windows-junction confinement (external-target links of
  either kind rejected before any copy starts) -- covering both file and
  directory links
- root-topology validation (dangerous nesting between source/destination/
  work/receipt/manifest paths rejected before any enumeration)
- per-volume peak-space preflight budgeting, with a distinct, much larger
  reserve floor for the system volume
- resumable, atomic, no-follow-safe file copy (including file and
  directory symlink/junction preservation, with absolute internal link
  targets rewritten so a relocated tree is self-contained)
- explicit, named, opt-in generated-cache exclusion policy (never applied
  by default to a raw preservation copy)
- a source-anchored relocation manifest, copy, and exact destination
  reconciliation
- durably persisted relocation receipts *and* the expected manifest
  itself, plus runtime semantic validation of a receipt's internal
  consistency

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

## Second hardening wave (post-push, adversarial review)

A full adversarial review of the first implementation found five real
architectural gaps, all confirmed against the code before fixing:

1. **Directory symlinks/junctions were ungoverned.** `enumerate_files()`
   only ever recorded `filenames`, never `dirnames` -- a directory link
   was invisible to the manifest (a real lossless-preservation break) and
   never confinement-checked. Fixed with `enumerate_directory_links()`
   (enumerated, not descended into) and `_is_reparse_point()` (detects
   Windows junctions via `st_reparse_tag`, since `Path.is_symlink()`
   alone does not recognize `IO_REPARSE_TAG_MOUNT_POINT`). Both file and
   directory links are now confinement-checked, manifest-represented, and
   copied as links (junctions recreated via `mklink /J`, since
   `os.readlink()` cannot portably read a junction's raw target).
2. **Destination-side replacement could still follow a symlink on
   Windows.** `_lp_replace()` was resolve()-based on both arguments; if a
   destination path was already a symlink, the "atomic replace" would
   silently target the link's *external* destination instead of the link
   entry itself -- a real outside-root-overwrite risk, for copies and for
   receipt/manifest writes alike. Fixed: `_lp_replace()` is now
   `_win_long_path_no_follow()`-based on both sides.
3. **Absolute internal symlinks preserved the wrong meaning.** A relative
   link target survives an identical-layout copy unchanged; an absolute
   target confined to `source_root` did not -- it kept pointing at the
   original source, defeating the point of a relocation once that source
   is later moved or deleted. Fixed: `_rewrite_symlink_target_if_needed()`
   rewrites a confined absolute target to the corresponding path under
   `destination_root`; a relative target is left untouched.
4. **The receipt was durable; the authoritative manifest was not.**
   `expected_manifest`/`destination_manifest` were digest-only in the
   receipt -- no way to reconstruct the expected entries for a later
   restore proof once the process exits. Fixed:
   `write_relocation_manifest()`/`read_relocation_manifest()` persist the
   expected (source-anchored) manifest atomically, bound into the receipt
   as `expected_manifest_ref`. `validate_relocation_receipt_semantics()`
   additionally rejects an internally contradictory receipt on readback
   (e.g. `raw_leg.ok=true` with a non-empty `raw_leg.files_failed`).
5. **The preflight lacked a host reserve and root-topology enforcement.**
   A flat 512 MiB margin did not reflect the much larger reserve this
   ATLAS engagement already established for the system volume the hard
   way; and nothing rejected a destination nested inside its own source,
   which a resumed operation could enumerate as part of the source and
   recursively re-copy. Fixed: `VolumeReservePolicy` applies
   `SYSTEM_VOLUME_MINIMUM_FREE_BYTES` (25 GiB) on the system volume and
   the ordinary margin elsewhere; `validate_root_topology()` rejects
   nested/overlapping source, destination, extracted, work, receipt, and
   manifest paths before any enumeration or copy starts.

## Tests

`tests/test_atlas_knowledge_storage.py` -- 93 tests (79 unconditional, 14
symlink/junction-dependent tests that gracefully skip in environments
lacking symlink-creation privilege, e.g. non-admin Windows without
Developer Mode -- junction tests are unaffected by that privilege and run
regardless), including everything from the first wave plus:

- directory symlink and Windows junction: internal (enumerated, not
  flagged), external (confinement-rejected), manifest-represented, and
  copied as a link rather than descended into
- destination-side symlink safety: a planted symlink at a copy
  destination or a receipt path is replaced as a link, never followed
  through to overwrite its external target
- absolute internal symlink rewriting, including the full acceptance
  test: relocate a tree with an absolute internal link, delete the
  original source entirely, and prove the destination link still
  resolves and exact restore verification still passes
- durable expected-manifest persistence and reload, including verifying
  restore against a manifest reloaded from disk rather than the
  in-memory original
- semantic receipt validation: five synthetic contradiction cases
  rejected, plus a genuine `relocate_archive_source()` receipt proven to
  always pass its own semantic validator
- system-volume reserve: the much larger floor enforced on the system
  volume, the ordinary margin elsewhere, and a caller override recorded
  on the returned budget
- root topology: six dangerous-nesting cases each rejected on their own,
  plus an end-to-end preflight proof that a nested destination is
  rejected before any enumeration happens

No real archive data anywhere in this PR -- every fixture is synthetic,
created and destroyed within its own test.

## Hosted CI

`.github/workflows/atlas-knowledge-storage-convergence.yml` -- path-filtered
to this change's own files, matrix over `[ubuntu-latest, windows-latest]`.
Rather than a fixed module list, the workflow scans every `tests/*.py`
file for an `ops.knowledge` import reference and runs whatever it finds
(always including this PR's own test module) via
`python -m unittest <discovered modules> -v` -- so a future test file
that starts exercising `ops.knowledge._pipeline` is picked up
automatically without a workflow edit, rather than the workflow silently
missing it.
