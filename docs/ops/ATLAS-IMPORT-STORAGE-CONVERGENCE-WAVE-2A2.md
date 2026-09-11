# ATLAS Import Storage Convergence -- Wave S2A2 (durable storage-root integration)

PR #218 (Wave S2A, merged at `0173e9af`) made folder imports use
`storage.relocate_archive_source()` for the copy itself, and threaded
`ATLAS_IMPORT_WORK_ROOT` through **staging**. It deliberately left the
**durable archive root** hardcoded: `source_dir()` built every archive
path from `atlas_root() / "data" / "imports" / "knowledge"` directly,
never consulting `storage.import_storage_root()` (which already existed
from Wave S1 but had no caller). Wave S2A2 closes that gap.

## What changed

### Archive resolution follows `ATLAS_IMPORT_STORAGE_ROOT`

`source_dir(source_name)` now returns
`storage.import_storage_root() / slugify(source_name)`. `archive_dir()`,
built from it, follows automatically. Unconfigured, `import_storage_root()`
defaults to the same `atlas_root()/data/imports/knowledge` as before --
**zero behavior change** for every existing caller that has never set the
variable. Configured (to a path anywhere, including off the ATLAS
checkout entirely -- the same D:-off-C: use case `ATLAS_IMPORT_WORK_ROOT`
already serves for staging), every new archive is admitted, resolved, and
discovered there instead.

### One shared pair, not 130 call sites

`relative_to_atlas()` / `resolve_atlas_path()` are what every manifest,
evaluation, receipt, and catalog path already round-trips through --
over 130 call sites across `_pipeline.py`. Rather than touch each one,
this wave taught the pair a second root:

```text
relative_to_atlas(path):
  under atlas_root()                     -> plain atlas-relative string (unchanged)
  under import_storage_root(), not atlas -> "@storage-root/<relative path>"
  under neither                          -> ValueError (unchanged shape, updated message)

resolve_atlas_path(path):
  starts with "@storage-root"            -> resolved against import_storage_root()
  otherwise                              -> resolved against atlas_root() (unchanged)
```

Every existing caller of either function -- `evaluate_archive()`,
`promote_archive()`, `normalize_archive()`, `build_catalog_record()`,
`update_catalog_doc()`, `validate_catalog()`, `resolve_archive_dir()`
(the CLI `--archive-dir` resolver), the receipt/query-bundle builders --
becomes storage-root-aware automatically, with **no code change of its
own**. When the storage root is at its default (still under
`atlas_root()`), the marker never appears and every one of those 130+
call sites behaves byte-for-byte as before Wave S2A2 -- proven by the
full pre-existing test suite (106 storage + 35 S2A tests) passing
unchanged. When it is relocated, the same call sites correctly produce
and consume the marker without having been individually touched.

### Discovery follows the configured root

`discover_import_manifests()` (the one function that walks
`*/*/IMPORT-MANIFEST.json` to enumerate every imported archive --
consumed by `backfill_v2.py`, `rank_promotion_candidates.py`, and the
catalog/validation builders in `_pipeline.py`) now globs
`storage.import_storage_root()` instead of a hardcoded path. An archive
under the *previous* default location is invisible once the root is
relocated -- deliberately: this wave does not migrate existing archives
(that is real-data work, explicitly out of scope here and in S2A/S1 --
see below), it only changes where *new* activity looks.

### What deliberately stays ATLAS-relative regardless of the storage root

Not everything an archive touches lives under the storage root, and
none of it should move just because that root does:

- `input_path` (the *source* being imported -- could be anywhere under
  ATLAS, e.g. an inbox folder, unrelated to where the durable copy lands)
- promotion docs (`docs/knowledge/promotions/*.md`) and the catalog doc
  (`docs/knowledge/KNOWLEDGE-CATALOG.md`) -- durable ATLAS documentation,
  checked into the repo
- CLI entrypoint / pipeline-module digests recorded in receipts
  (`ops/knowledge/*.py`)
- `knowledge_receipts_root()` (`runtime/receipts/knowledge/`) -- kept
  under `runtime/`, the same operational-not-archival area
  `ATLAS_IMPORT_WORK_ROOT` already lives near; deliberately not moved
  with the storage root in this wave (see "Not in S2A2" below)

## Not in S2A2

- **No real archive migration.** `personal--onedrive-desktop`, its
  emergency junctions, and the nine stale `pipeline_digest` receipts
  stay exactly where Wave S1/S2A left them -- Wave S2B.
- `ops/validation/validate_stack.py`'s hardcoded scan of
  `personal/verta-core-sanitized/{raw,extracted}` is unchanged and
  unaffected: that archive is not being relocated by this wave, so its
  fixed default-location check remains correct for as long as the
  storage root stays at its default (true today -- nothing configures
  `ATLAS_IMPORT_STORAGE_ROOT` yet). Updating validators with their own
  hardcoded archive-path assumptions is S2B/real-migration work, once an
  archive actually moves.
- **No change to `knowledge_receipts_root()` / receipt storage.**
  Receipts are operational evidence under `runtime/`, not the archive
  tree itself; moving them was not asked for and is a separate,
  deliberately deferred decision.
- `ops/playbooks/_pipeline.py` (a separate, parallel content-pack
  pipeline with its own `discover_import_manifests()`) is untouched --
  a different system, not the knowledge-import pipeline this wave scopes.
- Destructive replacement of a completed archive -- unchanged from S2A
  (`FolderImportReplacementUnsupportedError` still applies, regardless
  of where the archive lives).
- `#142` / Fitness / Mazer.

## Tests

`tests/test_atlas_knowledge_pipeline_s2a.py` -- 42 tests (35 from S2A,
unchanged and passing with zero modification, plus 7 new in
`StorageRootIntegrationTests`, all synthetic). Local: Windows 42/42 (2
skipped, symlink-privilege), Ubuntu (WSL) 42/42 (0 skipped). Combined
with the storage suite (106, unchanged): 148 total.

New this wave:

- archive resolution follows a configured `ATLAS_IMPORT_STORAGE_ROOT`
  entirely outside the ATLAS checkout -- the archive lands there, not
  under the default `data/imports/knowledge/`
- the default (unconfigured) root never produces the `@storage-root`
  marker -- every manifest field is a plain atlas-relative string,
  byte-for-byte what Wave S2A produced
- `resolve_atlas_path()` round-trips a marker-form manifest path back to
  the real, relocated filesystem location
- `discover_import_manifests()` finds archives under the configured
  root and does **not** see an archive left behind at the previous
  default location once relocated
- `evaluate_archive()` and `update_catalog_doc()` -- downstream
  consumers -- both run end to end against a relocated archive without
  raising, and the catalog's recorded manifest/evaluation paths
  round-trip correctly
- promotion and catalog docs stay under `atlas_root()` regardless of
  where the storage root points
