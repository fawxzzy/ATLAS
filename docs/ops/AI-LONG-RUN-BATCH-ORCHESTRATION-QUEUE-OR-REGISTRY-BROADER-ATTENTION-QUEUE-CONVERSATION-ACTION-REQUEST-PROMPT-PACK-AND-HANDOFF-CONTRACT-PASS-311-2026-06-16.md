# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Conversation-Action-Request Prompt-Pack And Handoff Contract Pass 311 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-CONTRACT-FREEZE-PASS-307-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-OWNER-SURFACE-ADMISSION-PASS-308-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-SUPPORTING-LANE-ADMISSION-PASS-309-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-FIRST-IMPLEMENTATION-ADMISSION-PASS-310-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@0e0208eb`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-local `conversation_action_request` family inside the broader `attention_queue` and `proposal_only` render-status surfaces.

This pass does not:

- implement or widen code
- change queue-budget, overflow, or provenance-derived family behavior
- mutate queue, registry, runtime, session, merge, manifest, or owner-repo state
- reopen `_stack`, Playbook, or owner-repo support
- widen into conversation-runtime, awareness-delivery, or manifest-backed execution semantics
- infer request meaning from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media
- claim marker movement, execution-home proof, or broader operator adoption

## Root Health Baseline

- pass 307 already froze the exact `conversation_action_request` qualification rule, admitted item fields, fixed `medium` severity, deterministic ordering inheritance, and pass-290 overflow noninteraction
- pass 308 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 309 already proved separate support still honestly holds at `none yet`
- pass 310 already froze the exact first implementation slice around request emission, inherited queue merge, bounded `proposal_only_state(...)` filtering, and top-level `proposal_only` handoff
- pass 290 already proves the bounded provenance-derived queue path that this slice must preserve without redesigning overflow or queue-budget behavior
- root validation is currently clean at `critical=0 error=0 warning=0 info=0`
- local `HEAD` is in parity with `origin/main`
- the shared-root cleanliness gate remains active and is intentionally preserved by leaving the current broad untracked root backlog untouched outside this bounded receipt-and-Book slice

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 307 exact `conversation_action_request` contract
- pass 308 root control-plane owner admission
- pass 309 supporting-lane hold at `none yet`
- pass 310 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `conversation_action_request` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it emits request items only from `conversation_turn` descriptors with `state.action_mode == "proposal_required"`, preserves fixed `medium` severity plus the admitted `conversation_id` / `turn_id` / `intent` detail keys, merges those items into the already-admitted broader queue under final deterministic `attention_item_sort_key(...)` ordering, renders `proposal_only_state(...)` with only the inherited `clear` / `pending` meanings and bounded `items[:5]`, exposes that projection at top-level `render_status_payload(...)` as `proposal_only`, and proves behavior against the frozen pass-310 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget or overflow changes
- provenance repair or stale-ref cleanup
- queue, registry, runtime, manifest, session, merge, or owner-repo mutation
- broader conversation-runtime, awareness, or world-model behavior
- any new item family, status value, payload field, or ordering rule outside the frozen seam
- any rewrite of the separate top-level `provenance_alerts` summary boundary

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- queue payload:
  - `status`
  - `item_count`
  - `highest_severity`
  - `items`
- `conversation_action_request` item payload:
  - `kind`
  - `severity`
  - `summary`
  - `source_ref`
  - `details.conversation_id`
  - `details.turn_id`
  - `details.intent`
- `proposal_only` payload:
  - `status`
  - `item_count`
  - `items`
- `proposal_only` item payload:
  - `summary`
  - `severity`
  - `source_ref`
  - `conversation_id`
  - `turn_id`
  - `intent`

Allowed `proposal_only.status` values only:

- `clear`
- `pending`

The worker may render these payload surfaces only.
The worker may not widen them into queue-budget metadata, manifest semantics, awareness-delivery state, registry/session/runtime narration, merge status, or broader operator-routing semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. one proposal-required conversation turn and no higher-severity queue items
   - emit queue `status` as `needs_review`
   - emit one `conversation_action_request`
   - preserve queue `highest_severity` as `medium`
   - preserve `conversation_id`, `turn_id`, and `intent`

2. one informational or otherwise non-qualifying conversation turn
   - omit `conversation_action_request`
   - fail closed to no new queue item from that descriptor

3. mixed proposal-required turn plus higher-severity provenance-derived queue item
   - preserve both families in one queue
   - preserve final item ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

4. proposal-only projection with one or more request items
   - emit `proposal_only.status` as `pending`
   - preserve `item_count` as the number of qualifying request items
   - preserve only request-family fields
   - ignore all non-request queue families

5. proposal-only projection with no request items
   - emit `status` as `clear`
   - preserve `item_count` as `0`
   - preserve `items` as `[]`

6. proposal-only projection cap
   - preserve `items[:5]`
   - do not widen the projection into queue-budget, manifest, or world-model semantics

7. top-level render-status handoff
   - preserve the bounded `proposal_only` projection at top-level `render_status_payload(...)`
   - do not widen that handoff into conversation manifests, execution approval flows, or awareness-delivery proof

## Exact No-Mutation / No-Queue-State / No-Registry-State Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one descriptor-backed conversation_action_request emission branch inside attention_queue(...), one inherited deterministic attention_item_sort_key(...) queue merge layer, one bounded proposal_only_state(...) filter-and-project layer with items[:5], one top-level render_status_payload(...) proposal_only handoff, and one fail-closed omission path for non-qualifying conversation_turn descriptors, but it may not mutate queue, registry, runtime, session, merge, manifest, or owner-repo state, change queue-budget or overflow behavior, widen into conversation-runtime or awareness-delivery semantics, or imply supervisor/operator proof.`

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
- `ops/atlas/converse.py`
- `ops/atlas/awareness.py`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader conversation-runtime, awareness-delivery, supervisor, dispatch, resume, merge-completion, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes or queue-signal overflow changes
- queue, registry, runtime, manifest, session, merge, or owner-repo mutation
- provenance repair or missing-file restoration
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, reordered item families, or non-deterministic sort behavior
- awareness or conversation-runtime widening beyond the admitted helper boundary
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 290 and 307 through 310 as frozen inputs
3. the exact preserved payload surfaces
4. the exact proof matrix
5. the exact no-mutation guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue conversation_action_request implementation-readiness closeout and worker-routing pass 312`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local `conversation_action_request` queue seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Conversation Action Request Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted request seam expands through prompt wording into queue-budget edits, awareness or conversation-runtime widening, hidden transcript-state inference, protected backlog cleanup, or broader operator semantics that the durable chain has not admitted.
