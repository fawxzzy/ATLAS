# Private Material Policy

This policy governs stack-owned handling for personal learning materials imported into `data/imports/knowledge/`.

## Defaults

- treat personal notes, school materials, and purchased course packs as non-public by default
- prefer `privacy_flag = private` unless there is a clear reason to use `mixed` or `shareable`
- keep imported content ATLAS-local and outside `repos/`
- do not assume that possession implies redistribution rights

## Privacy Classes

### `private`

Use when the archive may contain personal notes, grades, contact details, transcripts, exports, or anything intended only for the owner.

Handling:

- do not enable downstream indexing of full content
- default promotion posture is `derived_only` if a human elects to promote safe derived knowledge
- normalize metadata only
- keep catalog notes high-level and non-sensitive

### `mixed`

Use when the archive mixes private notes with less sensitive public or shared reference material.

Handling:

- restrict indexing until manual review is complete
- default promotion posture is `derived_only`
- avoid copying quoted content into docs or runtime metadata
- treat the archive as partially sensitive

### `shareable`

Use only when the material is confirmed safe to catalog and index at content level.

Handling:

- still run evaluation for secrets, copyright, and executable content
- keep normalized metadata concise and provenance-aware

## Disallowed Actions

- unpacking imported archives into `repos/`
- executing scripts, notebooks, binaries, installers, or macros from imported content
- copying secret-bearing content into docs, runtime metadata, or repo files
- treating copyrighted courseware as if it were stack-owned source material

## Indexing Rule

`safe_for_indexing` remains the compatibility signal for coarse allow or restrict decisions.

`indexing_profile` is the v2 downstream execution policy:

- `metadata_only`: retain manifests, evaluation, catalog metadata, and receipts only
- `derived_only`: allow promoted summaries and topic maps, but not raw imported content
- `full_text`: allow content-level indexing for confirmed shareable material

Promotion-specific rule:

- promotion must stop until any credential-like material is rotated and scrubbed
- `derived_only` is the default promotion profile for `private` and `mixed` archives
- `full_text` promotion is allowed only when evaluation returned `safe_for_indexing = yes` and the archive is `shareable`

Compatibility mapping still applies:

- `no`: do not promote or index beyond metadata handling
- `restricted`: use `metadata_only` unless a human explicitly creates a safe promotion doc
- `yes`: content indexing may be acceptable based on the current scan and privacy flag

Metadata normalization can still be allowed when full-content indexing is not.
