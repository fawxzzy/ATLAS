# ATLAS Import Storage Convergence -- Wave S2A (live pipeline integration)

Wave S1 (PR #216, merged to `main` at `cebe3c2`) delivered
`ops/knowledge/storage.py` but deliberately did **not** change the
active import path. Wave S2A wires it into
`ops/knowledge/_pipeline.import_archive()` for **folder** inputs.

**This section describes current behavior.** "Design history" at the
end records what earlier drafts of this PR got wrong and why, for
anyone reconstructing the reasoning -- it is not itself the contract.

## What a folder import does now

### One verified copy, admitted only when ownership is established

A folder import makes a single copy into `raw/` via
`storage.relocate_archive_source()` -- per-volume peak-space preflight
(fail closed), a source-anchored expected manifest, an atomic resumable
copy with S1's bounded write confinement, exact destination
reconciliation, and a durable `RELOCATION-RECEIPT.json` +
`RELOCATION-MANIFEST.json` (schema- and semantically-validated on read;
digests and refs recorded in `IMPORT-MANIFEST.json` under
`raw_relocation`).

Before any of that runs, **admission decides whether this call is even
entitled to write into the destination**:

| Destination state | Admission decision |
|---|---|
| No `IMPORT-MANIFEST.json`, `raw/`+`extracted/` empty or absent | fresh import -- proceeds |
| Completed archive (`IMPORT-MANIFEST.json` present), no `--force` | `FileExistsError` |
| Completed archive, `--force` given | `FolderImportReplacementUnsupportedError` -- refused, not deleted (see below) |
| `raw/` or `extracted/` holds content, no `IMPORT-MANIFEST.json`, no `IMPORT-ATTEMPT.json` | `UnownedDestinationError` -- refused, untouched |
| `IMPORT-ATTEMPT.json` present but its recorded identity doesn't match this request | `AdmissionIdentityMismatchError` -- refused, untouched |
| `IMPORT-ATTEMPT.json` present and matches this request exactly | resumes |

**Why a directory existing is not proof of ownership.** `knowledge_dir`
is deterministic from `(source_name, slug)`, but that only makes the
*path* predictable -- it says nothing about what is actually sitting
there. A different source, a changed source, or content a person
deliberately preserved can occupy the same path. `resumable_copy_tree()`
overwrites any file that doesn't byte-for-byte match the new source, so
"resuming" into content whose ownership was merely assumed would
silently destroy it -- and `relocate_archive_source()`'s exact
reconciliation, which only runs *after* the copy, cannot protect
content the copy already overwrote. Ownership is therefore established
**before** any copying starts, via a durable attempt record
(`IMPORT-ATTEMPT.json`, written after admission passes and before the
copy begins) binding `archive_id`, a content-sensitive digest of the
source tree, the destination, and `materialize_extracted`. A retry is
only ever treated as a resume when every one of those matches the
current request exactly; otherwise it is refused, and nothing under the
destination is touched. An unrelated or mismatched leftover always gets
a specific, named refusal -- never a silent overwrite and never a
blanket "delete it yourself" without saying why.

A genuine matching resume still isn't unconditionally trusted:
`relocate_archive_source()`'s own exact reconciliation
(`require_exact_match=True`) runs regardless, and fails closed -- with
the specific missing/unexpected/mismatched paths named in the error --
if the destination doesn't end up matching the source exactly (e.g. a
file dropped in after the interruption that the source never had).

`--force` against a *completed* archive is refused outright
(`FolderImportReplacementUnsupportedError`) on the storage-convergence
path rather than attempted destructively: replacing a verified archive
safely needs transactional (atomic swap) replacement, which is real,
separate work not built here. `ATLAS_IMPORT_LEGACY_FOLDER_COPY=1` still
gets the old destructive `--force` behavior for zip and legacy-copy
imports, where no preflight or resumability was ever in the picture.

Source content is only ever hashed for the manifest (`raw_entries`)
*after* the relocation has succeeded, read from `raw/` -- the verified,
link-free destination -- never from the unchecked source beforehand. A
rejected link's content is never opened.

### `extracted/` is materialized only on request

`raw/` is the single copy by default. `extracted/` is written only when
the caller passes `--materialize-extracted` (CLI) /
`materialize_extracted=True` (`import_archive()`), as a second
independently-verified leg of the same `relocate_archive_source()` call.
Zip imports are unchanged -- they always extract, because `raw/` there
is the `.zip` file, not a tree.

### Review tree is chosen from manifest contract, never directory presence

`review_source_dir(archive_path, manifest)` decides the tree
`evaluate_archive()`, `build_promotion_scaffold_sections()`, and the
promotion secret scan read, from the manifest's own recorded contract:

```text
new raw-only folder import            -> raw/
explicitly materialized folder import -> extracted/
zip import                            -> extracted/ (required)
missing required tree                 -> error, not fallback
```

Fields are validated, not coerced: an unsupported `source_type` or a
non-boolean `extracted_materialized` (e.g. the JSON string `"false"`,
which `bool()` would silently turn into `True`) is rejected outright.
`extracted_materialized` absent from the manifest entirely (a pre-S2A
archive) is the one case defaulted -- to `True`, matching what every
import from that era actually produced on disk. The selected path must
exist **and** be a directory. A stray `extracted/` next to a raw-only
import can never redirect evaluation to it -- selection never looks at
what exists, only at what the manifest declares. A zip missing its
`extracted/` tree fails closed instead of silently "reviewing" the raw
`.zip` blob. `evaluate_archive()`'s persisted evidence records
`review_source_kind` (`"raw"`/`"extracted"`) and `review_source_digest`,
binding which tree was actually scanned into the evidence.

### Staging volume follows `ATLAS_IMPORT_WORK_ROOT`

The transient copy staging uses `storage.import_work_root()`. Setting
`ATLAS_IMPORT_WORK_ROOT` moves the staging churn off a constrained
system drive without changing where the durable archive lands (that
stays ATLAS-relative under `data/imports/knowledge/…` -- see "Not in
S2A" below). `raw_relocation.staging_outside_atlas_root` in the manifest
records whether it was redirected.

### Long-path safety through the real pipeline path

`file_checksum()`, `build_raw_entries()`'s and `tree_digest()`'s
`stat()` calls, and `read_text_limited()` (used by the secret/private-
pattern scanners) all route through `storage`'s `\\?\`-prefixing
helpers, so a folder import and its evaluation survive a source tree
with a path past the 260-character Windows limit -- not just
`storage.py`'s own enumeration, which was already long-path-safe.

## Explicitly NOT in S2A

- The real `personal--onedrive-desktop` migration, its emergency
  junctions, and its nine stale `pipeline_digest` receipts -- Wave S2B.
- Relocating the durable archive root itself off the checkout via
  `ATLAS_IMPORT_STORAGE_ROOT` -- entangled with `relative_to_atlas()` /
  manifest-path semantics, needs its own bounded change. Tracked as the
  immediate next step (S2A2), not dropped.
- Transactional (atomic swap) replacement of a completed archive.
- `#142` / Fitness / Mazer.

## Tests

`tests/test_atlas_knowledge_pipeline_s2a.py` -- 26 tests, all synthetic
fixtures. Local: Windows 26/26 (1 skipped, symlink-privilege), Ubuntu
(WSL) 26/26 (0 skipped). Combined with the storage suite (106,
unchanged): 132 total.

- default folder import -> one verified `raw/`, no `extracted/`
- `RELOCATION-RECEIPT.json` round-trips through the public, validating
  reader; manifest digest checked on read
- downstream `evaluate_archive()` off `raw/` when `extracted/` absent
- `--materialize-extracted` -> both trees, both verified
- `ATLAS_IMPORT_LEGACY_FOLDER_COPY=1` -> exact legacy double-copy
- `ATLAS_IMPORT_WORK_ROOT` redirection; unset -> still completes
- **capacity, deterministic**: free-space observations injected into
  `storage._free_bytes`, never mocked away or weakened -- below the
  volume's actual reserve, at `reserve - 1`, and at `reserve + headroom`
  each produce the expected outcome, zero partial writes on failure
- zip import unchanged
- **admission / ownership**:
  - a completed archive survives a refused forced replacement
    byte-for-byte
  - a rejected source link's content is proven never read (spied)
  - a *genuine* interruption -- a real successful import with only
    `IMPORT-MANIFEST.json` removed afterward, simulating a crash between
    relocation succeeding and the manifest write -- resumes without
    `--force`
  - that same genuine resume still fails closed, precisely, if an
    orphaned file unrelated to the source is dropped in afterward
  - an **unmarked** destination holding a same-named file with different
    content (no manifest, no attempt record) is refused and the content
    is provably untouched
  - an attempt record whose source has since changed is refused before
    any overwrite, original bytes intact
  - an attempt record whose `materialize_extracted` no longer matches
    the request is refused before any overwrite
- **review selection**: a malformed `extracted_materialized` value and
  an unsupported `source_type` are rejected, not coerced; a selected
  tree that exists but isn't a directory is rejected
- persisted import -> evaluate -> normalize chain, plus an independent
  restore check against the persisted relocation evidence
- a >260-character fixture survives the real import/evaluate path

## Design history

Three review rounds shaped this PR before the table above became true.
Kept for anyone reconstructing the reasoning; the current-state
description above is authoritative, not this section.

1. **First draft:** folder imports made two unconditional `shutil`
   copies (`raw/` and `extracted/`), no preflight, no verification, no
   receipt -- replaced with the single verified
   `relocate_archive_source()` copy described above.
2. **First correction round:** `import_archive()` called the relocation
   engine in an order that didn't preserve its own guarantees --
   `build_raw_entries()` hashed source content (including a link a
   policy check would go on to reject) before any preflight ran, and
   `--force` deleted an existing archive before the new copy's preflight
   could fail. Fixed by moving admission and preflight before both
   hashing and mutation, and by refusing (rather than attempting)
   destructive replacement of a completed archive on this path. This is
   also where `review_source_dir()` first became manifest-driven instead
   of existence-driven, and where the long-path gaps in `_pipeline.py`
   itself (as opposed to `storage.py`) were found and closed.
3. **Second correction round:** the first round's admission fix still
   treated "no `IMPORT-MANIFEST.json`" as sufficient proof that a
   non-empty destination was an interrupted attempt at *this* import --
   a deterministic path is not identity. `resumable_copy_tree()`
   overwrites a same-named file that doesn't match the new source, so
   that assumption could silently destroy unrelated content sitting at
   the same destination path, with reconciliation only proving the
   *result* matched afterward -- not that the overwrite was authorized.
   Fixed with the durable, validated `IMPORT-ATTEMPT.json` record
   described above; this round also tightened `review_source_dir()` to
   validate field types rather than coerce them.
