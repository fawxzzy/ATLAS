# ATLAS Import Storage Convergence -- Wave S / Wave 1

## Scope

Wave 1 delivers reusable knowledge-import pipeline architecture only:

- first-class, independently configurable storage/work roots
  (`ATLAS_IMPORT_STORAGE_ROOT`, `ATLAS_IMPORT_WORK_ROOT`)
- long-path-safe deterministic file enumeration
- link detection and rejection (`LinkPolicy.REJECT_ALL`): every file
  symlink, directory symlink, and Windows junction is a blocking preflight
  finding -- internal or external target, it does not matter -- recorded
  precisely and refused before any copy starts, covering both file and
  directory links
- root-topology validation (dangerous nesting between source/destination/
  work/receipt/manifest paths rejected before any enumeration)
- per-volume peak-space preflight budgeting, with a distinct, much larger
  reserve floor for the system volume
- resumable, atomic, no-follow-safe copy of regular files, with each
  copy failure retaining a bounded, structured category
  (`unsupported_link_entry`, `source_read_failed`, `staging_copy_failed`,
  `checksum_mismatch`, `destination_replace_failed`) and a digest of the
  underlying error rather than raw error text
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

### Link detection and rejection: `LinkPolicy.REJECT_ALL`

`enumerate_files()` uses `lstat`, not `stat`, so symlinks are enumerated
as themselves without being silently followed, and `_is_reparse_point()`
detects both symlinks and Windows junctions (`st_reparse_tag`, since
`Path.is_symlink()` alone does not recognize
`IO_REPARSE_TAG_MOUNT_POINT`). `check_link_entries()` turns every link
entry -- file symlink, directory symlink, or junction, internal or
external target alike -- into a blocking preflight finding under
`LinkPolicy.REJECT_ALL`, the only policy this module ships and the
default everywhere a policy is accepted. Nothing copies until every one
of these findings is gone, i.e. until the archive being relocated
contains no links at all.

**This is a deliberate scope narrowing from an earlier draft of this
module**, which attempted to preserve symlinks and junctions live through
the copy: recreate them at the destination, confine external targets,
and rewrite absolute internal targets so a relocated tree stayed
self-contained. That approach survived two rounds of adversarial review
and fixes (see "Second hardening wave" below) but broke a third time in
hosted CI in two platform-specific ways that exposed the same underlying
problem: preserving live filesystem links across POSIX and Windows,
across relative and absolute targets, across 8.3 short-name aliasing and
long-path prefixing, in a way that is provably correct on both platforms
and still lets a relocated tree be moved again later, is a portable
archive-format problem in its own right -- materially larger than "copy
a directory tree to a new location so it can be read back later," which
is what Wave 1 actually needs to do. Rather than chase a fourth
incremental patch, Wave 1's contract was narrowed instead: **detect
unsupported filesystem semantics early, record them precisely, and fail
before mutation.** A file-tree copier that refuses what it cannot
losslessly reproduce is safer than one that quietly reproduces it wrong.
Live cross-platform link preservation is deferred to a future, dedicated
wave that can treat it as the archive-format problem it is, rather than
folding it into ordinary relocation.

`check_symlink_confinement()` -- the external-target-only predicate from
the first two hardening waves -- is kept in the module and still tested,
as a building block a future non-REJECT_ALL policy could reuse; it is no
longer wired into `preflight_space_budget()`, which calls
`check_link_entries()` instead.

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
this preflight did. Every `check_link_entries()` finding is blocking
here too, so nothing copies until the source tree is link-free.

### Resumable, atomic copy -- regular files only

`resumable_copy_tree()` iterates `enumerate_files()` only; link entries
are never in its scope. In the normal `relocate_archive_source()` flow a
link entry should never actually reach this function -- preflight already
refused the operation -- but if it is ever called directly on a tree that
still contains one, `_copy_one_resumable()` rejects it defensively with
an `unsupported_link_entry` failure rather than copying or dereferencing
it. Each admitted regular file is staged under `work_root`,
checksum-verified against the source, and only then moved into
`destination_root` with an atomic rename, so the destination never shows
a partial file; re-running after an interruption skips any destination
file that already checksum-matches the source rather than re-copying it.
A copy failure is retained as a structured `CopyFailure(path, category,
message_digest)`, never a bare string -- `category` is one of a fixed,
bounded set (`unsupported_link_entry`, `source_read_failed`,
`staging_copy_failed`, `checksum_mismatch`, `destination_replace_failed`)
and `message_digest` is a digest of the underlying error's `repr()`,
deliberately not the raw error text, since a raw OS error can embed local
machine paths.

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
   alone does not recognize `IO_REPARSE_TAG_MOUNT_POINT`). At the time,
   both file and directory links were confinement-checked,
   manifest-represented, and copied as links (junctions recreated via
   `mklink /J`, since `os.readlink()` cannot portably read a junction's
   raw target) -- the live-copy half of this was later removed in the
   third hardening wave below; `enumerate_directory_links()` and
   `_is_reparse_point()` themselves remain exactly as fixed here.
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
   is later moved or deleted. Fixed at the time via a rewrite step for
   confined absolute targets; that rewrite step -- and the whole class of
   problem it was patching -- no longer exists after the third hardening
   wave below, since links are now rejected rather than copied.
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

## Third hardening wave: live link preservation removed (`LinkPolicy.REJECT_ALL`)

Hosted CI failed a third consecutive time after the second hardening
wave -- not a repeat of a prior bug, but two new, platform-specific
failures that both traced back to the same root problem:

- **Ubuntu:** the absolute-internal-link acceptance test's expected
  manifest was built from the source tree *before* the copy's
  target-rewrite step ran, so its recorded checksum reflected the
  pre-rewrite target -- which necessarily disagreed with the
  destination's legitimately-rewritten (and therefore different) target
  string. A location-specific target string cannot be the thing a
  location-independent proof compares.
- **Windows:** newly-created symlink/junction entries were absent from
  `resumable_copy_tree()`'s results entirely, even though a sibling test
  calling `enumerate_directory_links()` directly against the identical
  fixture found them correctly.

Both failures were symptoms of trying to make a plain resumable file
copier also behave as a cross-platform, relocatable link-preservation
format. Rather than patch a fourth time, the contract was narrowed:
`LinkPolicy.REJECT_ALL` is now the only policy, and live link
materialization was removed from the merge-critical path entirely.

- `resumable_copy_tree()` now iterates regular files only; the
  `_copy_one_symlink_resumable()` / `_copy_one_junction_resumable()` /
  `_resolved_and_rebased_target()` / `_rewrite_symlink_target_if_needed()`
  helpers, and the `os.symlink()` / `mklink /J` recreation they drove,
  are gone from that path.
- `check_link_entries()` is the new preflight enforcement point: every
  link entry the source tree contains is a blocking finding, internal or
  external target alike, before any destination write happens.
  `check_symlink_confinement()` (external-target-only) is kept as a
  building block for a hypothetical future non-REJECT_ALL policy, but is
  no longer wired into `preflight_space_budget()`.
- Link entries still get canonical, location-independent diagnostics in
  `build_relocation_manifest()` via `_classify_link_entry()`: an internal
  link (target confined to `source_root`) records
  `{kind, target_scope: "internal", target_path}` (root-relative, so two
  logically identical trees produce the same entry regardless of where
  either physically lives); an external link records
  `{kind, target_scope: "external", target_digest}` -- a digest, never
  the raw external path, so the manifest itself cannot leak a local
  filesystem layout.
- `CopyResult.failed` changed from a list of bare strings to a list of
  `CopyFailure(path, category, message_digest)` -- `category` is one of
  `unsupported_link_entry`, `source_read_failed`, `staging_copy_failed`,
  `checksum_mismatch`, `destination_replace_failed`; `message_digest` is
  a digest of the failing error's `repr()`, not the raw error text.
  `schemas/atlas.knowledge-relocation-receipt.v1.json`'s `files_failed`
  items were updated to match (`$defs.copyFailure`), so a receipt with a
  populated failure list is schema-valid under the new shape, not just
  the old bare-string one.

Everything from the first and second hardening waves that is unrelated
to live link preservation was deliberately left exactly as it was: the
no-follow-based `_lp_replace()`, per-volume peak-space budgeting, the
system-volume reserve floor, root-topology validation, the
source-anchored (not self-referential) manifest, exact destination
reconciliation, the lossless-by-default exclusion policy (`.git`
included), atomic manifest/receipt persistence, and semantic receipt
validation are all unchanged by this wave.

**Rule going forward:** do not make a file-tree copier pretend to be a
portable archive format. Detect unsupported filesystem semantics early,
record them precisely, and fail before mutation. Live cross-platform
link preservation, if it is ever needed, belongs in a separate, dedicated
wave that can treat it as the archive-format problem it actually is.

## Tests

`tests/test_atlas_knowledge_storage.py` -- 92 tests (80 unconditional, 12
symlink-dependent tests that gracefully skip in environments lacking
symlink-creation privilege, e.g. non-admin Windows without Developer
Mode -- junction tests are unaffected by that privilege, since `mklink /J`
does not require it, and run regardless), including everything from the
first two waves plus, from the third:

- a link source (file symlink, directory symlink, or Windows junction)
  is rejected at preflight before any destination write, whether its
  target is internal or external to the source root -- the old
  confinement-era assumption that an internal-target link is safe no
  longer holds under `LinkPolicy.REJECT_ALL`, and has its own explicit
  regression test
- `relocate_archive_source()` end-to-end: a directory link blocks the
  whole operation before the destination root is even created
- a defensive rejection at `resumable_copy_tree()` itself if a link
  entry is ever passed to it directly (belt-and-suspenders on top of the
  preflight enforcement point)
- a failed regular-file copy retains a bounded `CopyFailure` category and
  a digest-form `message_digest`, never a bare string or raw error text
- destination-side symlink safety: a planted symlink at a copy
  destination or a receipt path is replaced as a link, never followed
  through to overwrite its external target (unaffected by this wave --
  still exercised against `_lp_replace()` directly)
- durable expected-manifest persistence and reload, including verifying
  restore against a manifest reloaded from disk rather than the
  in-memory original
- semantic receipt validation: five synthetic contradiction cases
  rejected, plus a genuine `relocate_archive_source()` receipt proven to
  always pass its own semantic validator
- the relocation receipt schema accepts the new structured
  `files_failed` shape (`$defs.copyFailure`), including a populated,
  non-empty failure list
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
