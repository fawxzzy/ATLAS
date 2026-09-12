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

### Discovery follows the configured root, and stays complete

`discover_import_manifests()` (the one function that walks
`*/*/IMPORT-MANIFEST.json` to enumerate every imported archive --
consumed by `backfill_v2.py`, `rank_promotion_candidates.py`, and the
catalog/validation builders in `_pipeline.py`) now scans
`storage.import_storage_root()` instead of a hardcoded path -- and, since
relocating that root is a configuration change, not a migration, it also
scans the legacy default location whenever the two differ, so nothing
already sitting at the previous location goes missing from discovery on
its own. See "Discovery preserves legacy inventory across a
configuration change" and "Discovery distinguishes complete from
partial inventory" below for the full contract, including what happens
when the configured root itself is unavailable.

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
  `personal/verta-core-sanitized/{raw,extracted}` is unchanged in this
  wave -- that archive is not being relocated by this wave, so the check
  stays correct today, while `ATLAS_IMPORT_STORAGE_ROOT` remains unset in
  production. **This is a named prerequisite for S2B, not a permanent
  exemption**: if `personal/verta-core-sanitized` is ever migrated onto
  a relocated storage root, this hardcoded scan must be updated (or
  routed through `discover_import_manifests()`/`resolve_atlas_path()`
  like everything else in `_pipeline.py`) as part of that migration --
  it will not track the relocation on its own.
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

## The `@storage-root` reference is a defined, confined grammar

A marker reference is not unrestricted path concatenation. `resolve_atlas_path()`:

1. Rejects any component that is empty, `.`, `..`, or contains `:`
   **before** joining it -- a fast, clear "invalid reference" error for a
   malformed or adversarial string, distinct from an escape.
2. Verifies the fully **resolved** result still lives under
   `import_storage_root()` -- this is what catches a symlink or junction
   *inside* the storage root whose target escapes it, which
   per-component rejection alone cannot see (every individual component
   can look perfectly ordinary; only the resolved destination is wrong).

`relative_to_atlas()` refuses to encode an ordinary ATLAS path whose
first component is literally named `@storage-root`: that string would be
indistinguishable from a genuine marker reference on decode. No real
ATLAS directory is named this, so treating it as reserved is what keeps
every *accepted* encoded reference decoding to the same location it was
encoded from.

### Encoding enforces the same grammar as decoding

The component grammar is not decode-only. `relative_to_atlas()` applies
`_reject_unsafe_storage_reference_component()` -- the same validator
`resolve_atlas_path()` uses -- to every component of a storage-root
reference **before** returning it, not just when reading one back. A
colon is an ordinary character in a POSIX filename (and irrelevant on
Windows, where such a name cannot exist on disk at all), but it is
reserved in this grammar precisely because it is also how a Windows
drive letter would be injected into a reference -- so a real file named
e.g. `notes:2026.txt` sitting under the storage root on a POSIX
filesystem must never be *encoded* into a reference the decoder would
then refuse. Refusing at encode time means the underlying file is never
renamed, moved, or silently omitted -- only the specific operation that
would need to produce an unrepresentable portable reference for it
fails, loudly, instead of handing a caller a string that breaks the
moment anything tries to resolve it back.

## Discovery preserves legacy inventory across a configuration change

`discover_import_manifests()` reads **both** the configured storage root
and the legacy default location (`atlas_root()/data/imports/knowledge`)
whenever they differ, deduplicating when they are the same physical
location (the common, unconfigured case). Changing
`ATLAS_IMPORT_STORAGE_ROOT` changes where *new* archives are written; it
must never make an archive that already exists at the previous default
location invisible to the catalog/validation/backfill/ranking tooling
that all consume this list, since nothing has actually moved it there.

Identity for both the legacy-preservation dedup and the collision check
below is the manifest's **own declared** `(source_name, slug)` -- read
from `IMPORT-MANIFEST.json` and slugified exactly as
`source_dir()`/`archive_dir()` derive it -- not simply the literal
directory names discovery happened to find the manifest under. Those two
always agree for anything this pipeline itself wrote; if they disagree,
`ArchiveIdentityLayoutMismatchError` is raised rather than trusting
either side over the other, since a manifest or its containing
directories having been edited or moved out of band is exactly the
situation where guessing wrong (for dedup, or for the identity every
downstream consumer reads) is unsafe. If two different roots each hold a
manifest whose validated identity resolves to the same `archive_id`,
that is a genuine collision -- `DuplicateArchiveIdentityError` is raised
rather than silently picking one, even when the two manifests sit under
different directory layouts.

### Discovery distinguishes complete from partial inventory

A missing or not-yet-created default root is ordinary first use --
nothing has ever been imported, so an empty list is correct, not an
error. But once `ATLAS_IMPORT_STORAGE_ROOT` is **explicitly** set, its
target being unavailable is a different situation: missing, not a
directory, or an `OSError` partway through enumeration all mean some of
its contents might be unreachable rather than genuinely absent, so the
list `discover_import_manifests()` would otherwise return cannot be
proven complete. Silently falling back to whatever the legacy root alone
finds would let a configuration change masquerade as a completed
migration -- exactly the failure mode this wave exists to prevent.
`IncompleteDiscoveryError` is raised instead, before
`update_catalog_doc()` (or `validate_catalog()`, backfill, or ranking)
ever builds or publishes a record from a possibly-partial list; since
the error is raised before any write, an existing catalog document is
left completely unchanged on refusal. A caller that only wants a
best-effort, read-only snapshot -- not an authoritative inventory used
for publication -- may pass `discover_import_manifests(allow_partial=True)`
to opt out and see whatever the legacy root still finds.

## `env=` is honored consistently within `import_archive()`

`import_archive(env=...)`'s explicit override, once given, is used for
**every** storage-root-relative decision the call makes internally
(admission, manifest fields, the attempt record, the artifact-digest
lookup, the knowledge receipt) -- not silently ignored for some of them
while honored for `ATLAS_IMPORT_WORK_ROOT`. `source_dir()`,
`archive_dir()`, `relative_to_atlas()`, and `resolve_atlas_path()` all
accept an optional `env` parameter for this; every call site *inside*
`import_archive()`'s own call graph threads it through.
Standalone entry points with no `env` parameter of their own
(`evaluate_archive()`, `promote_archive()`, `normalize_archive()`,
`discover_import_manifests()`, `resolve_archive_dir()`, the catalog and
validation builders) read real `os.environ` directly, as a normal CLI
invocation would.

## Tests

`tests/test_atlas_knowledge_pipeline_s2a.py` -- 59 tests. Local: Windows
59/59 (3 skipped, symlink-privilege), Ubuntu (WSL) 59/59 (0 skipped).
Combined with the storage suite (106, unchanged): 165 total.

- archive resolution follows a configured `ATLAS_IMPORT_STORAGE_ROOT`
  entirely outside the ATLAS checkout; the default (unconfigured) root
  never produces the `@storage-root` marker
- `resolve_atlas_path()` round-trips a marker-form manifest path back to
  the real, relocated filesystem location; an explicit `env=` override
  is honored end to end (proven with no `os.environ` mutation at all)
- **reference grammar, both directions**: on decode, a `..`
  parent-traversal reference and a symlinked escape *inside* the storage
  root are both rejected before any consumer sees the resolved path (the
  sentinel each attempts to reach is proven untouched); a literal ATLAS
  path named `@storage-root` is rejected at encode time, not misdecoded;
  a Windows drive-letter component in a realistic (single-string)
  reference is rejected; the component validator itself is proven to
  reject empty/`.`/`..` directly, since pathlib normalizes those away
  before they could ever reach it through a real string. On encode, a
  name containing a reserved character (e.g. a POSIX filename with a
  literal colon) is refused rather than turned into a reference the
  decoder would then reject, while an ordinary representable name still
  round-trips through encode and decode both
- **discovery migration safety and completeness**: an archive left at
  the legacy default location remains discoverable after the root is
  reconfigured; the same physical root reached two ways is not
  double-counted; two different roots whose manifests declare the same
  archive identity raise `DuplicateArchiveIdentityError` even when filed
  under different directory layouts; a manifest whose declared identity
  disagrees with its own directory layout raises
  `ArchiveIdentityLayoutMismatchError`; an unconfigured, not-yet-existing
  default root is a normal empty first-use inventory; an *explicitly
  configured* root that is missing raises `IncompleteDiscoveryError`
  instead of silently returning a legacy-only partial list, and a
  read-only caller may opt into that partial view with
  `allow_partial=True`; `update_catalog_doc()` refusing on incomplete
  discovery leaves an existing catalog document completely unchanged
- **downstream consumers, end to end, against a relocated archive**:
  persisted import -> `evaluate_archive()` -> `normalize_archive()` ->
  `update_catalog_doc()` -> `validate_catalog()` (asserting a fully
  clean result, not just that it returned), plus a second CLI-style
  resolution via `resolve_archive_dir()`'s `--archive-dir` path from the
  saved marker string, plus an independent restore check against the
  persisted relocation receipt/manifest
- promotion and catalog docs stay under `atlas_root()` regardless of
  where the storage root points
