# AI Long-Run Batch Orchestration Queue-Or-Registry Governed-Writes Top-Level Payload Boundary Prompt-Pack And Handoff Contract Pass 437 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-GOVERNED-WRITES-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-433-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-GOVERNED-WRITES-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-434-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-GOVERNED-WRITES-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-435-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-GOVERNED-WRITES-TOP-LEVEL-PAYLOAD-BOUNDARY-FIRST-IMPLEMENTATION-ADMISSION-PASS-436-2026-06-17.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@676ed068`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned top-level `governed_writes` payload boundary.

This pass does not:

- implement or widen code
- change residue semantics, closure semantics, queue semantics, queue budget, or queue ordering
- mutate queue, registry, runtime, session, merge, repair, rollback, manifest, or owner-repo state
- reopen `_stack`, Playbook, repair, rollback, closure, or owner-repo support
- infer governed-write truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media

## Root Health Baseline

- pass 433 already froze the exact top-level `governed_writes` payload contract around `execution_receipt` qualification, residue exclusion, exact `workspace_file_apply` admission, admitted field projection, deterministic ordering, and separation from retained residue and session-scoped closure surfaces
- pass 434 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 435 already proved separate support still honestly holds at `none yet`
- pass 436 already froze the exact first implementation slice around `execution_receipt` scan, residue exclusion, exact `workspace_file_apply` qualification, `links.action` plus `state.executed_at` applied-time fallback, admitted field-only projection, deterministic descending ordering, unchanged top-level handoff, and the exact proof matrix
- `ops/cortex/render_status.py` already carries that first slice in `governed_writes(...)`
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 433 exact top-level `governed_writes` payload contract
- pass 434 root control-plane owner admission
- pass 435 supporting-lane hold at `none yet`
- pass 436 exact first implementation slice and exact proof matrix

The worker must also preserve the already-admitted top-level separation:

- top-level `governed_writes` remains the canonical current governed-write payload
- top-level `execution_receipt_residue` remains the retained non-current residue surface
- top-level `closure_receipts` remains the session-scoped closing-receipt surface

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `governed_writes(...)` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it scans only `execution_receipt` descriptors, excludes residue only through `execution_receipt_residue_records(atlas_root())`, preserves only `workspace_file_apply` survivors, preserves only the admitted top-level governed-write fields, preserves `links.action` sourcing for `workspace_root`, `target_path`, `rollback_ref`, and `prior_sha256`, preserves `links.action.applied_at` with fallback only to `state.executed_at`, preserves deterministic descending `applied_at` then `source_ref` ordering, preserves the unchanged top-level `governed_writes` handoff through `render_status_payload(...)`, preserves separation from retained top-level `execution_receipt_residue` and session-scoped top-level `closure_receipts`, and proves behavior against the frozen pass-436 matrix

The worker is not allowed to pursue:

- broader execution-receipt history redesign
- residue classification redesign
- closure semantics redesign
- repair mutation or rollback execution logic
- broader `attention_queue` redesign
- queue, registry, runtime, session, merge, repair, rollback, manifest, or owner-repo mutation
- any new payload field, new status value, new count family, or ordering rule outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- top-level `governed_writes`
- per-item fields:
  - `receipt_id`
  - `source_ref`
  - `result`
  - `tool_id`
  - `registry_digest`
  - `workspace_root`
  - `target_path`
  - `rollback_ref`
  - `prior_sha256`
  - `applied_at`

Top-level payload rules remain:

- only `execution_receipt` descriptors participate
- only descriptors absent from `execution_receipt_residue_records(atlas_root())` survive
- only descriptors whose `state.execution_mode` is `workspace_file_apply` survive
- `workspace_root`, `target_path`, `rollback_ref`, and `prior_sha256` may resolve only from `links.action`
- `applied_at` may resolve only from `links.action.applied_at` and may fall back only to `state.executed_at`
- top-level items preserve the admitted field set only
- top-level items sort by descending `applied_at`, then descending `source_ref`
- the top-level payload remains separate from retained top-level `execution_receipt_residue` and session-scoped top-level `closure_receipts`

The worker may render these payload surfaces only.
The worker may not widen them into repair metadata, rollback policy, queue metadata, session-close metadata, registry summary metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. no qualifying governed-write receipts
   - preserve top-level `governed_writes` as `[]`

2. non-qualifying descriptors
   - omit descriptors whose `artifact_type` is not `execution_receipt`
   - omit descriptors whose `source_ref` is classified as residue
   - omit descriptors whose `state.execution_mode` is not `workspace_file_apply`

3. one qualifying governed write with direct action fields
   - preserve one top-level item with the exact admitted field set
   - preserve `workspace_root`, `target_path`, `rollback_ref`, and `prior_sha256` from `links.action`

4. one qualifying governed write without `links.action.applied_at`
   - preserve `applied_at` from `state.executed_at`
   - preserve the admitted field set without widening into extra execution history or repair metadata

5. multiple qualifying governed writes
   - preserve deterministic descending ordering by `applied_at`, then `source_ref`

6. top-level versus residue and closure separation
   - preserve the canonical current top-level `governed_writes` payload unchanged while retained `execution_receipt_residue` and session-scoped `closure_receipts` remain separate top-level surfaces

These proof cases inherit the pass-436 matrix exactly.

## Exact No-Mutation / No-Repair / No-Rollback Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one explicit execution_receipt descriptor scan, one residue exclusion layer through execution_receipt_residue_records(atlas_root()), one exact workspace_file_apply qualification gate, one bounded links.action projector plus applied_at fallback to state.executed_at, one admitted top-level governed-write field projector, one deterministic descending applied_at-then-source_ref ordering layer, and one unchanged top-level render_status_payload(...) handoff for governed_writes(...), but it may not mutate queue, registry, runtime, session, merge, repair, rollback, manifest, or owner-repo state, change residue or closure semantics, widen into generic execution-receipt history, broader governed-writes payload redesign, repair policy, rollback execution, or imply supervisor/operator proof.`

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
- residue-classification, session-close, runtime-state, merge, repair, rollback, manifest, or owner-repo mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- `ops/atlas/*`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader repair, rollback, closure, contradiction, supervision, dispatch, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- residue redesign, closure redesign, queue-budget changes, queue-ordering changes, or queue-family changes
- queue, registry, runtime, session, merge, repair, rollback, manifest, or owner-repo mutation
- repair policy, rollback execution, or closure widening
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, reordered item families, or non-deterministic sort behavior
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 433 through 436 as frozen inputs
3. the preserved separation between canonical current top-level governed writes, retained residue, and session-scoped closure receipts
4. the exact preserved payload surfaces
5. the exact proof matrix
6. the exact no-mutation guard verbatim
7. the exact no-hidden-transcript-state boundary
8. the exact allowed-touch and forbidden-touch surfaces
9. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry governed_writes top-level payload boundary implementation-readiness closeout and worker-routing pass 438`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local top-level `governed_writes` payload seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Governed Writes Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted top-level governed-writes seam expands through prompt wording into generic execution-receipt history, residue redesign, closure redesign, repair doctrine, rollback execution, hidden-state, protected-backlog, or broader runtime semantics that the durable chain has not admitted.
