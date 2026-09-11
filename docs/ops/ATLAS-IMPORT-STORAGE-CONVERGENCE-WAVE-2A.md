# ATLAS Import Storage Convergence -- Wave S2A (live pipeline integration)

Wave S1 (PR #216, merged to `main` at `cebe3c2`) delivered
`ops/knowledge/storage.py` but deliberately did **not** change the
active import path. Wave S2A wires it into
`ops/knowledge/_pipeline.import_archive()` for **folder** inputs.

## What changed

### One verified copy for folder imports, not two

Before S2A a folder import ran, unconditionally:

```python
copy_folder(input_path, raw_dir(knowledge_dir))
copy_folder(input_path, extracted_dir(knowledge_dir))
```

-- two full `shutil` copies of identical bytes, no space preflight, no
verification, no receipt. S2A replaces that with a single
`storage.relocate_archive_source()` into `raw/`:

- per-volume peak-space preflight, **fail closed** -- if the destination
  or work volume cannot hold the copy plus its reserve, the import
  raises `FolderImportRelocationError` **before any manifest is
  written**, so a failed import never leaves a half-imported archive;
- a source-anchored expected manifest, an atomic resumable copy with the
  bounded write-confinement from S1's fifth round, and exact destination
  reconciliation;
- a durable `RELOCATION-RECEIPT.json` + `RELOCATION-MANIFEST.json` under
  the archive directory, both schema- and semantically-validated on
  read; their digests and refs are recorded in
  `IMPORT-MANIFEST.json` under `raw_relocation`.

### `extracted/` is materialized only on request

`raw/` is now the single copy for a folder import.
`extracted/` is written only when the caller passes
`--materialize-extracted` (CLI) / `materialize_extracted=True`
(`import_archive()`), in which case it is a second independently-verified
leg of the same `relocate_archive_source()` call. Zip imports are
unchanged -- they always extract, because `raw/` there is the `.zip`
file, not a tree.

### Downstream review follows `raw/` when `extracted/` is absent

New `_pipeline.review_source_dir(archive_path)` returns `extracted/` if it
exists, else `raw/`. `evaluate_archive()`,
`build_promotion_scaffold_sections()`, and the promotion secret scan read
through it. For a folder import `raw/` holds exactly the tree the old
code would have duplicated into `extracted/`, so evaluation, promotion,
and cataloguing behave the same -- just off one copy instead of two.

### Staging volume follows `ATLAS_IMPORT_WORK_ROOT`

The transient copy staging uses `storage.import_work_root()`. Setting
`ATLAS_IMPORT_WORK_ROOT` moves the staging churn off a constrained
system drive without changing where the durable archive lands (that
stays ATLAS-relative under `data/imports/knowledge/…`). The manifest's
`raw_relocation.staging_outside_atlas_root` records whether it was
redirected.

### Rollback

`ATLAS_IMPORT_LEGACY_FOLDER_COPY=1` restores the exact pre-S2A
behavior (two unconditional `copy_folder` calls, no preflight, no
receipt) for one run, no code change. The manifest records
`folder_import_mode: "legacy-double-copy"` vs `"storage-convergence"`.

## Explicitly NOT in S2A

- The real `personal--onedrive-desktop` migration, its emergency
  junctions, and its nine stale `pipeline_digest` receipts -- Wave S2B.
- Relocating the durable archive root itself off the checkout via
  `ATLAS_IMPORT_STORAGE_ROOT` -- that is entangled with
  `relative_to_atlas()` / manifest-path semantics and belongs with the
  S2B storage-root migration, not this backward-compatible step.
- `#142` / Fitness / Mazer.

## Tests

`tests/test_atlas_knowledge_pipeline_s2a.py` -- 11 tests, all synthetic
fixtures:

- default folder import -> one verified `raw/`, no `extracted/`, manifest
  `folder_import_mode == "storage-convergence"`, relocation verified
- the `RELOCATION-RECEIPT.json` round-trips through
  `storage.read_relocation_receipt()` (schema + semantic validation) and
  the manifest digest is checked on read
- downstream `evaluate_archive()` runs off `raw/` when `extracted/` is
  absent
- `--materialize-extracted` -> both trees present, both verified,
  `review_source_dir()` prefers `extracted/`
- `ATLAS_IMPORT_LEGACY_FOLDER_COPY=1` -> exact double-copy behavior,
  no `raw_relocation` block
- `ATLAS_IMPORT_WORK_ROOT` -> staging reported outside the archive tree;
  unset -> still completes
- **capacity, deterministic**: free-space observations are injected
  (`storage._free_bytes`), not mocked away -- below the volume's actual
  reserve the import fails closed with no partial `raw/` tree and no
  manifest; at `reserve - 1` it fails, at `reserve + headroom` it
  succeeds; 64 GiB succeeds. The enforcement logic is never weakened.
- zip import -> unchanged (`raw/<name>.zip` + full `extracted/`)

## Correction round: ordering and review-selection at the public entry points

A source review of the first S2A commit found two integration defects --
the storage engine's own guarantees were correct, but `import_archive()`
called it in an order that didn't preserve them at the public boundary,
and `review_source_dir()` chose the reviewed tree by directory presence
instead of the import's own recorded contract. Both are fixed on this
same PR; the engine itself (`ops/knowledge/storage.py`, Wave S1) is
unchanged.

### 1. Admission and preflight now run before hashing or mutation

Before the fix, a folder import did, in order: build a raw-entries
inventory of the *source* (hashing every file, including one a link
policy would go on to reject) -> delete an existing archive if `--force`
-> call the relocation engine, whose preflight (space, link rejection)
only ran last. Two concrete consequences: a forced replacement could
delete a completed archive and then fail the new copy's capacity or
link-policy check, destroying data with nothing to show for it; and a
rejected symlink's target content was read (checksummed) before the
engine ever got a chance to reject it.

Fixed:

- **Admission is keyed on a completed prior import (a written
  `IMPORT-MANIFEST.json`), not mere directory presence.** `knowledge_dir`
  is a deterministic function of `(source_name, slug)`, so its existence
  without a manifest can only be an interrupted prior attempt at this
  exact `archive_id` -- never someone else's unrelated content. An
  ordinary re-run (no `--force`) now resumes into it instead of raising
  `FileExistsError`. `relocate_archive_source()`'s own exact
  reconciliation (`require_exact_match=True`) still fails closed --
  precisely, with the specific missing/unexpected/mismatched paths in the
  error -- if the leftover doesn't match the real source, so a stale or
  unrelated leftover can never be silently accepted as a successful
  resume.
- **`--force` no longer deletes a completed archive before the new
  copy's preflight has run.** For the storage-convergence folder path,
  replacing a completed archive destructively is refused outright
  (`FolderImportReplacementUnsupportedError`) rather than attempted --
  transactional (atomic swap) replacement is real, separate work this PR
  does not build. `ATLAS_IMPORT_LEGACY_FOLDER_COPY=1` still gets the old
  destructive `--force` behavior for zip and legacy-copy imports, where a
  preflight was never in the picture to bypass.
- **Source content is hashed only after the engine has verified it.**
  `raw_entries` for the storage-convergence path is now built from
  `raw_dir(knowledge_dir)` -- the relocated, link-free destination --
  after `relocate_archive_source()` succeeds, not from the unchecked
  source beforehand. A rejected link's content is never opened.

### 2. Review tree is chosen from manifest contract, never directory presence

`review_source_dir()` now takes the archive's manifest and decides from
`source_type` / `extracted_materialized`, not from which directories
happen to exist:

```text
new raw-only folder import           -> raw/
explicitly materialized folder import -> extracted/
zip import                           -> extracted/ (required)
missing required tree                -> error, not fallback
```

A manifest predating Wave S2A has no `extracted_materialized` key at
all; that absence is treated as `True` (extracted/ required), matching
what every import from that era actually produced on disk. A stray
`extracted/` directory next to a raw-only import can no longer redirect
evaluation to it -- the selection never looks at whether it exists,
only whether the manifest says to use it. A zip import missing its
`extracted/` tree now fails closed instead of silently "reviewing" the
raw `.zip` blob. `evaluate_archive()`'s persisted evidence now also
records `review_source_kind` (`"raw"` or `"extracted"`) and
`review_source_digest`, binding which tree was actually scanned into the
evidence rather than leaving it implicit.

### Also fixed in this round: long-path safety through the real pipeline path

Pushing a >260-character fixture through the actual `import_archive()` /
`evaluate_archive()` entry points (not just `storage.py`'s own
enumeration tests) surfaced three remaining plain, non-long-path-safe
filesystem calls in `_pipeline.py` itself: `file_checksum()`,
`build_raw_entries()`'s `stat()`, `tree_digest()`'s `stat()`, and
`read_text_limited()` (used by the secret/private-pattern scanners).
All four now route through `storage`'s `\\?\`-prefixing helpers.

### Tests added this round

`tests/test_atlas_knowledge_pipeline_s2a.py` grew from 11 to 20 (all
synthetic fixtures): a failed forced replacement leaves the existing
archive byte-for-byte unchanged; a rejected source link is proven never
content-read (spied, not just inferred); an interrupted first import
resumes without `--force`; an interrupted import with a genuinely
orphaned leftover fails closed with the specific reconciliation issue in
the error; a stray `extracted/` cannot redirect a raw-only review; a zip
missing `extracted/` fails closed rather than falling back to raw; a
legacy (pre-S2A-shaped) manifest defaults correctly; a persisted
import -> evaluate -> normalize chain runs end to end with quarantine
behavior unchanged for a benign fixture, plus an independent restore
check against the persisted relocation receipt/manifest; and a
>260-character fixture survives the real import/evaluate path. Local:
Windows 126/126 (18 skipped, symlink-privilege), Ubuntu (WSL) 126/126 (7
skipped, Windows-only).
