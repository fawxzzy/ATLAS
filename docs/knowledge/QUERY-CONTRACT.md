# Knowledge Query Contract

This document defines the deterministic query bundle for promoted knowledge and receipt-backed metadata.

## Query Lane

Query artifacts are written under:

- `runtime/cortex/query/knowledge/`

Current bundle path:

- `runtime/cortex/query/knowledge/bundle.json`

The query bundle is derived runtime state. It is rebuildable from:

- `docs/knowledge/promotions/*.md`
- `runtime/cortex/catalog/knowledge/*.json`
- `runtime/receipts/knowledge/**/latest.json`

## Bundle Contract

- `schema_version`: `atlas.knowledge.query-bundle.v1`
- `pipeline_version`: `atlas.knowledge.pipeline.v2`
- `full_text_status`: `reserved`
- `record_count`
- `bundle_inputs`
- `records`
- `content_digest`

Each record includes:

- `archive_id`
- `source_name`
- `status`
- `privacy_flag`
- `promotion_status`
- `indexing_profile`
- `retention_class`
- `promotion_allowed`
- `paths`
- `source_digests`
- `query_policy`
- `derived_summary_text`
- `topic_map_terms`
- `evidence_reference_ids`
- `receipt`
- `search_terms`

## Queryability By Indexing Profile

- `metadata_only`: searchable only by metadata fields such as archive id, source, status, privacy flag, promotion status, indexing profile, and retention class
- `derived_only`: searchable by metadata fields plus derived summary, topic map terms, and evidence reference ids from a valid promotion doc
- `full_text`: reserved for future work; this pass does not hydrate or index raw imported content

`promotion_allowed` remains the safety gate for derived searchability. A promotion doc alone is not sufficient when the latest receipt still reports promotion blocked or quarantined.

## Privacy Rules

- never hydrate raw import content during search
- never index `raw/` or `extracted/` file bodies in this pass
- treat receipt digests and tooling digests as provenance metadata, not content
- keep `metadata_only` archives from exposing derived summary or topic map fields in query results

## Historical Continuity Preference

Historical continuity and planning queries should prefer grounded derivative artifacts in this order:

- `reviewed_promotion_note`
- `promotion_note`
- trusted root or owner-repo docs
- `handoff`
- `import_evaluation`
- raw `imported_doc` and `imported_pdf`

Rules:

- download residue and transcript residue must not be elevated into truth
- raw imported evidence may support a partial result, but should not outrank reviewed derivative notes
- source trust posture must remain explicit when an answer depends on visible-untrusted evidence

## Determinism

The query bundle must be stable when the source promotion docs, runtime catalogs, and latest receipts have not changed.

Determinism rules:

- no wall-clock timestamps in the bundle payload
- sorted source inputs and record ordering
- lexical tokenization only
- deterministic tie-breaking by score, match count, and `archive_id`
- `content_digest` computed from the stable payload

## Rebuild Semantics

- source of truth remains the import manifest, evaluation, promotion doc, runtime catalog, and latest receipt lanes
- the query bundle is disposable and may be rebuilt at any time
- deleting `runtime/cortex/query/knowledge/bundle.json` must not lose knowledge truth

## Worker Context Consumers

The worker context lane under `runtime/cortex/context/` is a query-plane consumer.

Rules:

- worker context packs must select through the query bundle first
- worker context packs may hydrate only policy-allowed fields from promotion docs, runtime catalogs, and latest receipts
- `metadata_only` archives must remain metadata-only inside worker context artifacts
- descriptor registration and status rendering must consume the worker context artifact, not re-run query selection from logs
