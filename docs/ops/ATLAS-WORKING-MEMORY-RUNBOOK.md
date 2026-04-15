# ATLAS Working Memory Runbook

This runbook defines the durable working-memory lane for plans, decisions, initiatives, and hypotheses at the ATLAS root.

## Purpose

Working memory is structured document memory.

- event memory explains what happened through receipts and observations
- working memory explains what ATLAS is planning, deciding, driving, and testing

This lane exists so future sessions build on durable artifacts instead of chat residue.

In the operating loop, working memory is the bridge between attention and governed action. It is where plans, decisions, initiatives, and hypotheses remain queryable after a session ends.

## Storage

Store working-memory artifacts under:

- `docs/memory/plans/`
- `docs/memory/decisions/`
- `docs/memory/initiatives/`
- `docs/memory/hypotheses/`

Each artifact is a JSON document validated against its matching schema in `schemas/`.

## Required Fields

Every working-memory artifact must include:

- `contract_version`
- `id`
- `title`
- `summary`
- `status`
- `owner`
- `created_at`
- `updated_at`
- `related_session_refs`
- `related_artifact_refs`
- `evidence_refs`
- `supersedes`
- `superseded_by`

## Provenance Rules

- `related_session_refs` links the memory item to governed sessions when relevant
- `related_artifact_refs` points at durable artifacts that the memory item depends on
- `evidence_refs` records the supporting docs, receipts, or manifests
- `supersedes` and `superseded_by` make revision lineage explicit instead of silently overwriting prior intent

Do not dump raw transcript text into working memory.

## Memory Versus Event Memory

Use working memory for:

- plans that remain active across sessions
- architecture or policy decisions that affect later work
- initiatives spanning multiple repos or waves
- falsifiable hypotheses that need evidence and follow-up

Do not use working memory for:

- raw terminal logs
- ephemeral scratch notes
- unreviewed transcript summaries
- mutable runtime state that belongs in `runtime/`

## Initiative Policy

Initiatives are the durable identity for repeated related work.

Use initiatives to:

- cluster multiple related sessions under one objective
- record why follow-on work still exists
- keep evidence, decisions, plans, and hypotheses attached to the same thread of work
- propose future sessions without treating the proposal as execution authority

Do not:

- create a new initiative for every session touching the same objective
- treat transcript summaries as initiative artifacts
- skip provenance fields when refining an existing initiative

The intended lifecycle is:

1. attention surfaces a real issue or opportunity
2. an initiative captures the durable objective and evidence
3. proposed sessions attach to that initiative
4. governed execution produces receipts
5. working memory is refined from those receipts instead of forked into duplicate artifacts

## Indexing

Build or refresh the working-memory catalog with:

```powershell
python .\ops\cortex\index_working_memory.py
```

The deterministic catalog is written to:

- `runtime/cortex/catalog/memory/working-memory.latest.json`

Awareness and status consume this catalog as a read model. The source of truth remains the JSON artifacts under `docs/memory/**`.

## Supersession Rules

- create a new artifact when the identity of the plan or decision changes materially
- use `supersedes` and `superseded_by` instead of mutating history out of existence
- update `updated_at` whenever the current artifact changes
- keep `id` stable for in-place refinements of the same memory item

## Validation

Malformed working-memory artifacts are blocking validation failures.

Validation checks:

- schema and required fields
- ISO timestamps
- string-array provenance fields
- duplicate ids
- catalog drift against the source documents

## Operating Rule

Working memory is queryable truth, not hidden context.

If a plan or decision should influence later behavior, put it in this lane or ATLAS will treat it as non-durable.
