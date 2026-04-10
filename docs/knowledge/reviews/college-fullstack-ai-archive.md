# College Fullstack AI Archive Review

## Archive

- `archive_id`: `personal--college-fullstack-ai-archive`
- `source_name`: `personal`
- `import_dir`: `data/imports/knowledge/personal/college-fullstack-ai-archive`
- `reviewed_at`: `2026-04-09T17:24:22Z`
- `reviewer`: `Codex`

## Provenance

- original input: `data/imports/knowledge/personal/college-fullstack-ai-archive/raw/college-fullstack-ai-archive.zip`
- import manifest: `data/imports/knowledge/personal/college-fullstack-ai-archive/IMPORT-MANIFEST.json`
- owner or source context: personal study archive already staged in the ATLAS raw knowledge lane
- copyright or license notes: course handouts, assignment PDFs, rubrics, and third-party licensed materials are present
- provenance confidence: high

## Privacy And Risk

- `privacy_flag`: `private`
- `personal_private_material`: `true`
- `credentials_secrets_risk`: `false` after human review
- `copyrighted_courseware_risk`: `true`
- `executable_content`: `true`
- `safe_for_indexing`: `restricted`
- recommended indexing scope: `metadata_only`

## Decision

- review status: `normalized`
- normalization allowed: `true`
- metadata retention allowed: `true`
- content indexing allowed: `false`
- no-execute guarantee confirmed: `true`

## Notes

- The archive contains 4,155 files, including course PDFs, lab handouts, source trees, virtualenv contents, compiled executables, and bundled libraries.
- The default secret scanner produced keyword hits from teaching examples and vendored packages, but the follow-up high-confidence scan found no private keys, token-like strings, or real credential assignments.
- Metadata should remain high-level and provenance-aware. Do not quote courseware or copy executable content into stack-owned docs or runtime artifacts.
