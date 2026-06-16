# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention_Queue Semantics Beyond Provenance Alerts Prompt-Pack And Handoff Contract Pass 304 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-OWNER-SURFACE-ADMISSION-PASS-301-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-SUPPORTING-LANE-ADMISSION-PASS-302-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-FIRST-IMPLEMENTATION-ADMISSION-PASS-303-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6776920e`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned broader `attention_queue` seam beyond the separate top-level `provenance_alerts` summary.

This pass does not:

- implement or widen code
- change queue-budget, queue-signal, or overflow behavior
- mutate queue, registry, runtime, session, merge, manifest, or owner-repo state
- reopen `_stack`, Playbook, or owner-repo support
- infer truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media
- claim marker movement, execution-home proof, or broader operator adoption

## Root Health Baseline

- pass 300 already froze the exact broader `attention_queue` contract, including the preserved payload fields, severity-first deterministic ordering, and admitted item-family set
- pass 301 already admitted `ATLAS root control-plane surfaces` as the owner-facing home
- pass 302 already proved no honest separate supporting lane reopens now
- pass 303 already froze the exact first implementation slice and exact proof matrix
- pass 290 already proves the bounded provenance-derived queue path that this mixed-family first slice must preserve, including the overflow sentinel boundary
- root validation is currently clean at `critical=0 error=0 warning=0 info=0`
- local `HEAD` is in parity with `origin/main`
- the shared-root cleanliness gate remains active and is intentionally preserved by leaving the current broad untracked root backlog untouched outside this bounded receipt-and-Book slice

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 300 broader `attention_queue` contract, including the preserved payload fields, severity-first ordering, admitted item-family set, and strict separation from the fuller top-level `provenance_alerts` summary
- pass 301 root control-plane owner admission for this broader queue seam
- pass 302 supporting-lane hold at `none yet`
- pass 303 exact first implementation slice and exact proof matrix

The worker must also preserve the already-proved bounded provenance-derived queue behavior from pass 290:

- provenance-derived queue items remain bounded through the existing queue-signal cap
- `provenance_alert_overflow` remains the sentinel family when the admitted provenance signal exceeds that cap
- queue-level `item_count` still measures only the admitted bounded queue payload rather than suppressed provenance totals

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local broader `attention_queue` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it invokes `initiative_attention_items(...)` exactly once, invokes `provenance_attention_items(...)` exactly once, preserves actionable `initiative_open_attention` plus the admitted provenance-derived queue families only, performs one bounded concatenation layer, applies final deterministic ordering through `attention_item_sort_key(...)`, emits only the admitted top-level queue payload surface, preserves only the admitted `clear` / `needs_review` status meanings, and proves behavior against the frozen pass-303 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget or overflow changes
- provenance-drift repair or stale-ref cleanup
- queue, registry, runtime, manifest, session, or merge mutation
- supervisor, dispatch, resume, execution-home, or operator-proof behavior
- any new item family outside the already frozen mixed-family seam
- any rewrite of the separate top-level `provenance_alerts` summary boundary

## Exact Preserved Payload Surface

The worker must preserve exactly this bounded payload surface:

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

The worker may render this payload surface only.
The worker may not widen it into queue-budget metadata, provenance-repair plans, registry/session/runtime narration, merge status, or broader operator routing semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

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

These proof cases inherit the pass-303 matrix exactly.

## Exact No-Mutation / No-Queue-State / No-Registry-State Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one explicit initiative_attention_items(...) invocation, one explicit provenance_attention_items(...) invocation, one bounded concatenation layer, one final deterministic attention_item_sort_key(...) ordering layer, one top-level queue status/count/highest-severity renderer, and one fail-closed empty-queue fallback for the root-owned broader attention_queue slice, but it may not mutate queue, registry, runtime, session, merge, manifest, or owner-repo state, change queue-budget or overflow behavior, repair provenance drift, widen into registry/session/runtime/execution queue families, or imply supervisor/operator proof.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted root-local helper and test files
- do not infer payload meaning, proof scope, blocker state, or next-step authority from uncited transcript memory, hidden operator state, or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`
- local non-secret fixtures or static inputs strictly needed to prove the admitted matrix, if such fixtures become necessary inside the same root-owned slice

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into shared helper-runtime, owner-repo, deploy, or protected backlog surfaces.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry mutation surfaces
- session-manifest or runtime-state mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- owner-repo mutation surfaces
- top-level `provenance_alerts` summary contract surfaces beyond narrow test or implementation reconciliation for the admitted helper entrypoint
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- supervisor, dispatch, resume, merge-completion, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes or queue-signal overflow changes
- queue, registry, runtime, manifest, session, or merge mutation
- provenance repair or missing-file restoration
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, reordered item families, or non-deterministic sort behavior
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 300 through 303 as frozen inputs
3. the preserved bounded provenance-derived queue behavior from pass 290
4. the exact preserved payload surface
5. the exact proof matrix
6. the exact no-mutation guard verbatim
7. the exact no-hidden-transcript-state boundary
8. the exact allowed-touch and forbidden-touch surfaces
9. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue semantics beyond provenance alerts implementation-readiness closeout and worker-routing pass 305`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether this docs chain is materially complete enough to leave docs-only mode and route one bounded implementation packet without reopening queue-budget, provenance-repair, or shared-helper questions

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for the broader mixed-family `attention_queue` seam.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Broader Attention Queue Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted mixed-family queue seam expands through prompt wording into queue-budget edits, provenance repair, registry/session/runtime widening, hidden transcript-state inference, protected backlog cleanup, or broader operator semantics that the durable chain has not admitted.
