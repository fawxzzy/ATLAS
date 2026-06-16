# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention_Queue Semantics Beyond Provenance Alerts First-Implementation Admission Pass 303 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-OWNER-SURFACE-ADMISSION-PASS-301-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-SUPPORTING-LANE-ADMISSION-PASS-302-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@d6f0cdf7`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned broader `attention_queue` seam plus one proof matrix for validating that slice without crossing the no-registry/session/worker/merge/closure/trust/conversation widening boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one root-local `initiative_attention_items(...)` invocation that preserves actionable `initiative_open_attention` items only
2. one root-local `provenance_attention_items(...)` invocation that preserves bounded provenance-derived queue items only, including the existing overflow sentinel path
3. one bounded concatenation layer that combines those two derived item families into one queue candidate list
4. one final deterministic queue-ordering layer via `attention_item_sort_key(...)`
5. one top-level queue status, count, and highest-severity renderer
6. one fail-closed empty-queue fallback with no execution or mutation widening

The first-slice queue renderer may distinguish only:

- `clear` when no admitted initiative or provenance queue items remain
- `needs_review` when one or more admitted initiative or provenance queue items remain

## Exact Preserved Payload Surface

The worker must preserve only:

- `status`
- `item_count`
- `highest_severity`
- `items`

Allowed `status` values only:

- `clear`
- `needs_review`

Top-level payload rules remain:

- `item_count` is the total length of the admitted queue items after bounded provenance overflow handling
- `highest_severity` is the first item severity after final deterministic sorting, or `null` when no items remain
- `items` preserves the final severity-first ordering from `attention_item_sort_key(...)`
- `items` may include only:
  - `initiative_open_attention`
  - `initiative_provenance_drift`
  - `proposed_session_provenance_drift`
  - `provenance_alert_overflow`

## Exact Mandatory Proof Cases

1. no initiative or provenance queue items remain
   - emit `status` as `clear`
   - preserve `item_count` as `0`
   - preserve `highest_severity` as `null`
   - preserve `items` as `[]`

2. initiative-only open attention
   - emit `status` as `needs_review`
   - preserve `item_count` above `0`
   - preserve the first item as `initiative_open_attention`

3. provenance-only drift
   - emit `status` as `needs_review`
   - preserve `item_count` above `0`
   - preserve the first item as one provenance-derived queue family

4. mixed initiative and provenance-derived queue items
   - emit `status` as `needs_review`
   - preserve final item ordering by `attention_item_sort_key(...)`
   - preserve `highest_severity` from the first sorted item

5. provenance overflow remains in force
   - preserve `provenance_alert_overflow` when the admitted provenance signal exceeds the existing cap
   - preserve queue-level `item_count` against the bounded queue payload rather than the suppressed provenance total

6. initiative items with no actionable summary
   - preserve them as omitted from the queue
   - do not widen the slice into inactive initiative, registry, session, worker, merge, closure, trust, or conversation families

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue semantics beyond provenance alerts prompt-pack and handoff contract pass 304`

## Marker Decision

- `none`

## Rule

Admit the smallest root-local mixed-family `attention_queue` slice first: initiative open-attention items plus provenance-derived queue items, then final sort/render, before reopening registry/session/runtime/execution queue families.
