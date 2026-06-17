# AI Long-Run Batch Orchestration Queue-Or-Registry Conversations Top-Level Payload Boundary Prompt-Pack And Handoff Contract Pass 430 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-426-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-427-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-428-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-FIRST-IMPLEMENTATION-ADMISSION-PASS-429-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-16.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@034aa55b`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned top-level `conversations` payload boundary.

This pass does not:

- implement or widen code
- change queue semantics, queue ordering, or queue-family behavior
- change `proposal_only` semantics
- mutate queue, registry, runtime, session, merge, manifest, world-model, or owner-repo state
- reopen `_stack`, Playbook, transcript hydration, Awareness widening, or owner-repo support
- infer conversation-state truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media

## Root Health Baseline

- pass 426 already froze the exact top-level `conversations` payload contract around `conversation_manifest` qualification, exact count and recent-item fields, deterministic ordering, and separation from the narrower queue-side `conversation_action_request` family and queue-derived `proposal_only`
- pass 427 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 428 already proved separate support still honestly holds at `none yet`
- pass 429 already froze the exact first implementation slice around `conversation_manifest` scan, exact `item_count`, active-only `active_count`, descending `updated_at` then `conversation_id`, bounded `recent_items[:5]`, unchanged top-level handoff, and the exact proof matrix
- the reconciled queue-side request worker already proves the top-level payload stays separate from the narrower `conversation_action_request` family and filtered `proposal_only` subset
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 426 exact top-level `conversations` payload contract
- pass 427 root control-plane owner admission
- pass 428 supporting-lane hold at `none yet`
- pass 429 exact first implementation slice and exact proof matrix

The worker must also preserve the already-admitted top-level versus queue and proposal-only split:

- top-level `conversations` remains the fuller bounded conversation-state payload
- `attention_queue` may still emit only the narrower `conversation_action_request` family
- top-level `proposal_only` remains the filtered queue-derived subset

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `conversation_summary(...)` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it scans only `conversation_manifest` descriptors, preserves exact `item_count`, preserves active-only `active_count`, preserves descending `updated_at` then `conversation_id` ordering, preserves only the admitted top-level `recent_items[:5]` field set, preserves the unchanged top-level `conversations` handoff through `render_status_payload(...)`, preserves separation from the narrower queue-side `conversation_action_request` family and the filtered top-level `proposal_only` subset, and proves behavior against the frozen pass-429 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- `proposal_only` redesign
- transcript hydration, transcript-derived meaning, or conversation-turn body projection
- Awareness or `/atlas/voice` payload redesign
- queue, registry, runtime, session, merge, manifest, world-model, or owner-repo mutation
- any new payload field, new status value, new count family, or ordering rule outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- top-level `conversations`
- top-level fields:
  - `item_count`
  - `active_count`
  - `recent_items`
- `recent_items[*]` fields:
  - `conversation_id`
  - `mode`
  - `status`
  - `turn_count`
  - `last_turn_at`
  - `recent_turn_refs`
  - `active_initiative_refs`
  - `active_session_refs`
  - `source_ref`

Top-level payload rules remain:

- only `conversation_manifest` descriptors participate
- `item_count` counts all qualifying manifests
- `active_count` counts only manifests whose `state.status = "active"`
- `recent_items` sort by descending `state.updated_at`, then descending `identity.conversation_id`
- `recent_items` remain capped at `[:5]`
- the top-level payload remains separate from the narrower queue-side `conversation_action_request` family and the filtered top-level `proposal_only` subset

The worker may render these payload surfaces only.
The worker may not widen them into queue metadata, proposal-only metadata, transcript bodies, Awareness delivery metadata, world-model metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. no qualifying conversation manifests
   - preserve top-level `conversations.item_count` as `0`
   - preserve top-level `conversations.active_count` as `0`
   - preserve top-level `conversations.recent_items` as `[]`

2. non-conversation descriptors
   - omit descriptors whose `artifact_type` is not `conversation_manifest`

3. one active conversation manifest
   - preserve one top-level recent item with the exact admitted field set
   - preserve `item_count` as `1`
   - preserve `active_count` as `1`

4. one non-active conversation manifest
   - preserve `item_count` as `1`
   - preserve `active_count` as `0`
   - preserve the admitted recent-item fields without adding queue, transcript, or derived initiative/session meaning

5. multiple qualifying conversation manifests
   - preserve deterministic descending ordering by `updated_at`, then `conversation_id`
   - preserve only the top five recent items

6. top-level versus queue and proposal-only separation
   - preserve the fuller top-level `conversations` payload unchanged while `attention_queue` may still emit only the narrower `conversation_action_request` family and `proposal_only` may still remain the filtered queue-derived subset

These proof cases inherit the pass-429 matrix exactly.

## Exact No-Mutation / No-Transcript / No-Awareness-Widening Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one explicit conversation_manifest descriptor scan, one exact item_count layer, one active-only active_count layer, one descending updated_at-then-conversation_id ordering layer, one bounded recent_items[:5] projector preserving only the admitted top-level conversation-state fields, and one unchanged top-level render_status_payload(...) handoff for conversation_summary(...), but it may not mutate queue, registry, runtime, session, merge, manifest, world-model, or owner-repo state, change queue or proposal_only semantics, widen into transcript hydration, broader Awareness or /atlas/voice payload redesign, broader conversations payload redesign, or imply supervisor/operator proof.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted root-local helper and test files
- do not infer payload meaning, proof scope, blocker state, or next-step authority from uncited transcript memory, hidden operator state, or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry mutation surfaces
- session-manifest, runtime-state, merge, world-model, or owner-repo mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- `ops/atlas/converse.py`
- `ops/atlas/awareness.py`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader transcript-hydration, Awareness-delivery, voice-read-model, supervision, dispatch, resume, merge-completion, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue changes or `proposal_only` changes
- queue, registry, runtime, session, merge, manifest, world-model, or owner-repo mutation
- transcript hydration or transcript-derived inference
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, reordered item families, or non-deterministic sort behavior
- Awareness or `/atlas/voice` widening beyond the admitted helper boundary
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 426 through 429 as frozen inputs
3. the preserved separation between fuller top-level conversation state, narrower queue-side request family, and filtered top-level proposal-only subset
4. the exact preserved payload surfaces
5. the exact proof matrix
6. the exact no-mutation guard verbatim
7. the exact no-hidden-transcript-state boundary
8. the exact allowed-touch and forbidden-touch surfaces
9. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry conversations top-level payload boundary implementation-readiness closeout and worker-routing pass 431`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local top-level `conversations` payload seam that already has its contract, owner, support posture, and first slice admitted.
