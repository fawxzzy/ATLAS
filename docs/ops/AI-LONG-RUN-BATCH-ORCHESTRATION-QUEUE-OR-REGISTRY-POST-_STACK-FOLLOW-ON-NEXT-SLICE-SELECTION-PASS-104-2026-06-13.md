# AI Long-Run Batch Orchestration Queue-Or-Registry Post-`_stack` Follow-On Next-Slice Selection Pass 104 - 2026-06-13

- Date: `2026-06-13`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded next-slice selection`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/_STACK-READINESS-STACK-QUEUE-OR-REGISTRY-FOLLOW-ON-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-13.md`
  - `docs/ops/ROOT-SIDE-STACK-LOCK-REFRESH-AFTER-_STACK-QUEUE-OR-REGISTRY-FOLLOW-ON-FIRST-IMPLEMENTATION-2026-06-13.md`
  - `repos/_stack/scripts/queue-or-registry-follow-on.mjs`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@3a794f63`

## Objective

Choose the strongest remaining bounded post-worker next slice for the queue-or-registry family now that the first shared `_stack` follow-on helper is real and root lock truth has been refreshed.

## Candidate Comparison

The strongest honest post-worker next-slice candidates are:

1. `live direct-json-read follow-on`
2. `live directory-read follow-on`

## Selection

Select exactly one next slice:

- `live direct-json-read follow-on`

## Why `Live Direct-Json-Read Follow-On` Wins

This is now the strongest remaining bounded seam because:

- the direct-file blocked branch is narrower than the directory branch
- the shared helper now packages that branch explicitly without performing the read
- the next honest gain is one exact admission question for a single-file live-read seam, not broader directory semantics or queue behavior

What it improves without widening:

- narrows the next question from generic blocked follow-on posture to one exact direct-json-read seam only
- keeps directory reads, queue mutation, registry mutation, queue-drop emission, and worker launch still deferred

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry live direct-json-read follow-on contract-freeze pass 105`

## Marker Decision

- `none`

## Rule

After the first shared follow-on helper lands, reopen the narrowest blocked live-read seam first, not the broader directory or queue-execution branches.
