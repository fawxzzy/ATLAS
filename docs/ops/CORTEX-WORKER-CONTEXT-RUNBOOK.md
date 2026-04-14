# Cortex Worker Context

The Cortex worker context lane builds deterministic context artifacts for worker assignments from promoted knowledge and receipt-backed runtime metadata.

## Purpose

Workers should consume a stable context artifact instead of ad hoc pasted notes.

The context pack is query-first and hydrate-later:

- select candidate knowledge through the deterministic query bundle
- hydrate only allowed fields from promotion docs, runtime catalogs, and latest receipts
- never hydrate raw import content

## Artifact Lane

Context artifacts are written under:

- `runtime/cortex/context/`

Default artifact path:

- `runtime/cortex/context/<assignment_id>.json`

Schema version:

- `atlas.cortex.worker-context.v1`

## Inputs

Required:

- `assignment_id`
- `worker_id`
- `task_id`
- `stack_lock_digest`

Optional selection inputs:

- query terms
- task tags

Source surfaces:

- `runtime/cortex/query/knowledge/bundle.json`
- `docs/knowledge/promotions/*.md`
- `runtime/cortex/catalog/knowledge/*.json`
- `runtime/receipts/knowledge/**/latest.json`

## Indexing Policy

- `metadata_only` archives contribute metadata only
- `derived_only` archives may contribute derived summary, topic map terms, and evidence references when `query_policy.derived_searchable = true`
- `full_text` remains reserved; this lane does not hydrate raw or extracted file bodies
- quarantined Verta surfaces stay metadata-only until policy changes for real

## Run

Example:

```powershell
python ops/cortex/build_worker_context.py `
  --assignment-id assignment-demo-001 `
  --worker-id worker-demo-001 `
  --task-id atlas-doc-sync `
  --stack-lock-digest sha256:demo `
  --query-term "atlas interoperability" `
  --task-tag architecture
```

## Determinism

Given the same:

- lock digest
- query terms
- task tags
- query bundle and source surfaces

the context artifact must produce the same `content_digest`.

Determinism rules:

- stable query normalization
- lexical-first ranking only
- stable tie-breaking by score, match count, and `archive_id`
- stable JSON digest over the artifact payload

## Consumption

`_stack` should attach the context artifact path to worker handoff refs and prompt scaffolding, not inline the full artifact body into mutable transcript text.

Root sessions should register a descriptor for the emitted worker context artifact and reference that descriptor-backed context ref from the session manifest.
