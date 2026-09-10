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
