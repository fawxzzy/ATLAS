# AI Long-Run Batch Orchestration Queue-Or-Registry Post-Broader Attention-Queue Registry-Error Next-Slice Selection Pass 327 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded next-slice selection`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-CONTRACT-FREEZE-PASS-321-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@003d32d6`

## Objective

Choose the strongest remaining bounded `attention_queue` follow-on now that the root-local `registry_error` slice is implementation-backed and proven on canonical `main`.

## Candidate Comparison

The strongest honest remaining next-slice candidates are:

1. the root-local `blocked_worker` queue family
2. active-session / open-merge-request / closure-receipt / registry-surface-derived queue families
3. inactive `legacy_compatibility_payload` queue work or broader remediation/adoption work

## Selection

Select exactly one next slice:

- the root-local `blocked_worker` queue family

## Why `blocked_worker` Wins

- it is already live inside `attention_queue(...)`, so the family is implementation-visible without inventing a new queue taxonomy or reviving an inactive payload seam
- it stays root-local because it depends only on the bounded `blocked_workers_payload` read-model already consumed by `render_status_payload(...)`
- it is the smallest remaining live runtime-derived queue family because it emits one compact item shape per worker with one bounded severity branch and one bounded details payload, instead of reopening the broader active-session, merge-request, or closure-record families
- it preserves one compact admitted payload shape around `worker_id`, `assignment_id`, `state`, and `blocked_reason` rather than reopening merge, closure, or broader registry-surface contradiction clusters
- it remains deterministic and mutation-free because it is a read-model blocked-state sentinel only; it does not require worker mutation, merge resolution, receipt repair, or owner-repo work
- it is narrower than the remaining active-session / merge-request / closure families because those families already depend on more branches, more conditional meanings, or broader cross-record semantics

## Deferred Alternatives

### Active-session / open-merge-request / closure-receipt / registry-surface-derived queue families

Deferred because:

- they depend on broader runtime and governance surfaces than the current smallest root-local follow-on
- they reopen more cross-surface contradiction, conditional severity, and payload-shape questions than the single bounded blocked-worker seam

Reopen condition:

- only after the `blocked_worker` family is either frozen and bounded or honestly rejected

### Inactive `legacy_compatibility_payload` queue work or broader remediation/adoption work

Deferred because:

- `legacy_compatibility_payload` still is not yet a live `attention_queue(...)` seam, so choosing it here would route to a not-yet-live family instead of the smallest remaining live slice
- remediation or adoption work widens into mutation, cleanup, or supervisor/operator proof rather than one bounded queue-semantic seam

Reopen condition:

- only after the remaining live root-local broader queue families are either frozen or exhausted

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue blocked_worker contract freeze pass 328`

## Marker Decision

- `none`

Why:

- this pass chooses the next bounded slice only
- the implementation-backed movement already landed in the reconciliation receipt, so no second ratchet is justified here

## Rule

After the smallest remaining registry sentinel lands, prefer the smallest remaining live root-local worker-state sentinel before reopening broader active-session, merge-request, closure, or mutation-adjacent queue work.

## Pattern

reconciled bounded queue family -> post-family next-slice selection -> next exact family contract freeze

## Failure Mode

`Route Past Smallest Remaining Live Worker-State Queue Family`

If the lane jumps from the reconciled registry-error slice straight into active-session, merge-request, closure, or inactive payload seams, the queue family widens into broader runtime doctrine before the smaller live blocked-worker seam is frozen and bounded.
