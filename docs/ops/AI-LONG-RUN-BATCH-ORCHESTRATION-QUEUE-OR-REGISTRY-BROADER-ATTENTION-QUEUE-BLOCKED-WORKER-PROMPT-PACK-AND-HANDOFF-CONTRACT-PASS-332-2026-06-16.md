# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Blocked-Worker Prompt-Pack And Handoff Contract Pass 332 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-CONTRACT-FREEZE-PASS-328-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-OWNER-SURFACE-ADMISSION-PASS-329-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-SUPPORTING-LANE-ADMISSION-PASS-330-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-FIRST-IMPLEMENTATION-ADMISSION-PASS-331-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@6461b42c`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-local `blocked_worker` family inside the broader `attention_queue` render-status surface.

This pass does not:

- implement or widen code
- change queue-budget, overflow, or provenance-derived family behavior
- mutate queue, registry, runtime, session, merge, manifest, or owner-repo state
- reopen `_stack`, Playbook, worker-control doctrine, contradiction families, or owner-repo support
- widen into launch, dispatch, claim, done, pause, resume, merge, or repair semantics
- infer worker truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media

## Root Health Baseline

- pass 328 already froze the exact `blocked_worker` contract around `latest_worker_states(...)`, `blocked_workers(...)`, admitted detail fields only, state-to-severity branching, deterministic ordering, registry-health split, and separation from worker-control authority
- pass 329 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 330 already proved separate support still honestly holds at `none yet`
- pass 331 already froze the exact first implementation slice around latest-worker selection, blocked-worker derivation, queue emission, inherited deterministic queue merge, fail-closed contradiction omission, and unchanged top-level handoffs
- pass 290 already proves the bounded provenance-derived queue path that this slice must preserve without redesigning overflow or queue-budget behavior
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 328 exact `blocked_worker` contract
- pass 329 root control-plane owner admission
- pass 330 supporting-lane hold at `none yet`
- pass 331 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `blocked_worker` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it preserves latest-worker selection by `heartbeat_at`, preserves `blocked_workers(...)` qualification for `blocked`, `paused`, and `merge_wait` only, preserves one fixed `blocked_worker` queue item with admitted detail fields only, preserves `high` severity for `blocked` and `medium` severity for `paused` or `merge_wait`, preserves inherited deterministic `attention_item_sort_key(...)` queue ordering against the already-admitted broader queue families, preserves blocked-worker emission even when registry health is unavailable while preserving fail-closed omission of `unknown_tool_surface` and `unknown_extension_surface`, preserves the unchanged top-level `attention_queue` and `blocked_workers` handoffs through `render_status_payload(...)`, and proves behavior against the frozen pass-331 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget or overflow changes
- launch, dispatch, claim, done, pause, resume, merge, or repair authority
- registry repair or contradiction-family widening
- queue, registry, runtime, session, merge, manifest, or owner-repo mutation
- any new item family, status value, payload field, or ordering rule outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- queue payload:
  - `status`
  - `item_count`
  - `highest_severity`
  - `items`
- `blocked_worker` item payload:
  - `kind`
  - `severity`
  - `summary`
  - `source_ref`
  - `details.worker_id`
  - `details.assignment_id`
  - `details.state`
  - `details.blocked_reason`
- top-level blocked-worker read-model payload:
  - `blocked_workers`

The worker may render these payload surfaces only.
The worker may not widen them into worker-control routing, repair metadata, contradiction-family projection, queue-budget metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. latest-descriptor qualification
   - preserve only the latest `worker_status` descriptor per `worker_id`
   - omit a worker when the latest descriptor is non-blocking even if an older descriptor was blocking
   - preserve a worker when the latest descriptor is one of the admitted blocked-worker states

2. blocked state emission
   - emit one `blocked_worker`
   - preserve `high` severity when `state == "blocked"`
   - preserve only the admitted detail fields

3. paused or merge-wait emission
   - emit one `blocked_worker`
   - preserve `medium` severity when `state == "paused"` or `state == "merge_wait"`

4. unhealthy registry plus blocked worker
   - preserve `blocked_worker`
   - omit `unknown_tool_surface`
   - omit `unknown_extension_surface`
   - preserve the fail-closed split between blocked-worker visibility and registry-health-dependent contradiction emission

5. mixed blocked-worker plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final item ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

6. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `blocked_workers` payload
   - do not widen those handoffs into worker-control, repair, or doctrine semantics

7. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `blocked_worker` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact No-Mutation / No-Worker-Control / No-Queue-State Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one root-local latest_worker_states(...) selection layer, one blocked_workers(...) read-model derivation layer, one blocked_worker emission branch inside attention_queue(...), one inherited deterministic attention_item_sort_key(...) queue merge layer, one fail-closed omission path for registry-health-dependent contradiction families when registry health is unavailable, and one unchanged top-level render_status_payload(...) handoff for attention_queue plus blocked_workers, but it may not mutate queue, registry, runtime, session, merge, manifest, or owner-repo state, change queue-budget or overflow behavior, widen into launch, dispatch, claim, done, pause, resume, merge, repair, or contradiction-family mutation, or imply supervisor/operator proof.`

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
- session-manifest, worker-control, or runtime-state mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- owner-repo mutation surfaces
- `ops/atlas/*`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader worker-control, repair, contradiction, supervisor, dispatch, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes or queue-signal overflow changes
- launch, dispatch, claim, done, pause, resume, merge, or repair authority
- registry repair or contradiction-family widening
- queue, registry, runtime, session, merge, manifest, or owner-repo mutation
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, new blocked-worker states, reordered item families, or non-deterministic sort behavior
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited pass 290 plus passes 328 through 331 as frozen inputs
3. the exact preserved payload surfaces
4. the exact proof matrix
5. the exact no-mutation guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue blocked_worker implementation-readiness closeout and worker-routing pass 333`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local `blocked_worker` queue seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Blocked Worker Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted blocked-worker seam expands through prompt wording into worker-control, repair, overflow, hidden-state, protected-backlog, or broader runtime semantics that the durable chain has not admitted.
