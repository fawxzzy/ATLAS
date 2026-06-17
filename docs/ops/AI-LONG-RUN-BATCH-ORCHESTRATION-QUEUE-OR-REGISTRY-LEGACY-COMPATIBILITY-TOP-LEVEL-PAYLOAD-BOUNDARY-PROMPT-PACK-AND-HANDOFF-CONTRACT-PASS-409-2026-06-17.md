# AI Long-Run Batch Orchestration Queue-Or-Registry Legacy-Compatibility Top-Level Payload Boundary Prompt-Pack And Handoff Contract Pass 409 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-405-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-406-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-407-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-FIRST-IMPLEMENTATION-ADMISSION-PASS-408-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned top-level `legacy_compatibility` payload boundary.

This pass does not:

- implement or widen code
- change queue semantics, queue budget, or queue ordering
- mutate queue, registry, runtime, session, merge, manifest, archive, repair, blocker, or owner-repo state
- reopen `_stack`, Playbook, archive doctrine, repair doctrine, governed-v1 blocker doctrine, or owner-repo support
- infer legacy compatibility truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media

## Root Health Baseline

- pass 405 already froze the exact top-level `legacy_compatibility` payload contract around descriptor-backed qualification, admitted field set, deterministic ordering, and separation from the smaller queue-side signal
- pass 406 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 407 already proved separate support still honestly holds at `none yet`
- pass 408 already froze the exact first implementation slice around descriptor scan, `source_ref` qualification, admitted field-only projection, deterministic ordering, unchanged top-level handoff, and the exact proof matrix
- the reconciled queue-side legacy worker already proves the top-level payload stays separate from the smaller `legacy_compatibility_signal` subset
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 405 exact top-level `legacy_compatibility` payload contract
- pass 406 root control-plane owner admission
- pass 407 supporting-lane hold at `none yet`
- pass 408 exact first implementation slice and exact proof matrix

The worker must also preserve the already-proved top-level versus queue-side split:

- top-level `legacy_compatibility` remains the fuller bounded status payload
- `attention_queue` may still emit only the smaller `legacy_compatibility_signal` subset

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `legacy_compatibility_surfaces(...)` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it scans only `legacy_runtime_backfill` descriptors, preserves only truthy trimmed `source_ref` survivors, projects only the admitted top-level legacy fields, preserves deterministic `observed_at` then `session_id` then `source_ref` ordering, preserves the unchanged top-level `legacy_compatibility` handoff through `render_status_payload(...)`, preserves the richer top-level fields that intentionally stay outside the smaller queue-side signal, and proves behavior against the frozen pass-408 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget or queue-ordering changes
- archive action, repair action, or governed-v1 blocker widening
- queue, registry, runtime, session, merge, manifest, archive, repair, blocker, or owner-repo mutation
- broader legacy payload redesign or doctrine semantics
- any new item family, status value, payload field, or ordering rule outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- top-level `legacy_compatibility`
- per-item fields:
  - `session_id`
  - `source_ref`
  - `original_session_ref`
  - `epoch`
  - `cutover_at`
  - `observed_at`
  - `recorded_at`
  - `missing_governed_requirements`
  - `governed_identity`

The worker may render these payload surfaces only.
The worker may not widen them into archive metadata, repair metadata, blocker metadata, queue metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. no qualifying legacy backfill descriptors
   - preserve top-level `legacy_compatibility` as `[]`

2. non-legacy descriptor shapes
   - omit descriptors whose `artifact_type` is not `legacy_runtime_backfill`

3. missing or empty `source_ref`
   - omit legacy backfill descriptors when `source_ref` is missing, empty, or whitespace-only

4. one qualifying legacy descriptor
   - preserve one top-level item with the exact admitted field set
   - preserve richer top-level-only fields:
     - `cutover_at`
     - `observed_at`
     - `recorded_at`
     - `governed_identity`

5. multiple qualifying legacy descriptors
   - preserve deterministic ordering by `observed_at`, then `session_id`, then `source_ref`

6. top-level and queue-side separation
   - preserve the top-level `legacy_compatibility` payload unchanged while `attention_queue` may still emit only the smaller `legacy_compatibility_signal` subset

These proof cases inherit the pass-408 matrix exactly.

## Exact No-Mutation / No-Archive / No-Repair Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one explicit legacy_runtime_backfill descriptor scan, one truthy trimmed source_ref qualification gate, one admitted top-level legacy field projector, one deterministic observed_at-then-session_id-then-source_ref ordering layer, and one unchanged top-level render_status_payload(...) handoff for legacy_compatibility, but it may not mutate queue, registry, runtime, session, merge, manifest, archive, repair, blocker, or owner-repo state, change queue semantics, widen into archive action, repair action, governed-v1 blocker semantics, broader legacy payload redesign, or imply supervisor/operator proof.`

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
- session-manifest, runtime-state, merge, archive, repair, blocker, or owner-repo mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- `ops/atlas/*`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader archive-doctrine, repair-doctrine, governed-v1 blocker, contradiction, supervision, dispatch, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes, queue-ordering changes, or queue-family changes
- queue, registry, runtime, session, merge, manifest, archive, repair, blocker, or owner-repo mutation
- archive action, repair action, or governed-v1 blocker widening
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, reordered item families, or non-deterministic sort behavior
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 405 through 408 as frozen inputs
3. the exact preserved payload surfaces
4. the exact proof matrix
5. the exact no-mutation guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry legacy_compatibility top-level payload boundary implementation-readiness closeout and worker-routing pass 410`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local top-level `legacy_compatibility` payload seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Legacy Top-Level Payload Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted top-level legacy seam expands through prompt wording into archive doctrine, repair doctrine, governed-v1 blocker semantics, broader legacy payload redesign, hidden-state, protected-backlog, or broader runtime semantics that the durable chain has not admitted.
