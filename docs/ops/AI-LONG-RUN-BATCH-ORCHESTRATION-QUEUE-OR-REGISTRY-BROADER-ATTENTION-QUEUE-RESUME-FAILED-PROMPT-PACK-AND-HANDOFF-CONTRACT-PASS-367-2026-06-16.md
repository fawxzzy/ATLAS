# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Resume-Failed Prompt-Pack And Handoff Contract Pass 367 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-CONTRACT-FREEZE-PASS-363-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-OWNER-SURFACE-ADMISSION-PASS-364-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-SUPPORTING-LANE-ADMISSION-PASS-365-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-FIRST-IMPLEMENTATION-ADMISSION-PASS-366-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@9c7db2f2`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-local `resume_failed` family inside the broader `attention_queue` render-status surface.

This pass does not:

- implement or widen code
- change queue-budget, overflow, or provenance-derived family behavior
- mutate queue, registry, runtime, session, execution-receipt, merge, manifest, or owner-repo state
- reopen `_stack`, Playbook, failure doctrine, contradiction families, or owner-repo support
- widen into retry execution, resume execution, merge execution, registry repair, or owner-repo semantics
- infer session truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media

## Root Health Baseline

- pass 363 already froze the exact `resume_failed` contract around admitted active-session qualification, bounded queue payload only, fixed severity, deterministic ordering, and separation from retry execution, resume execution, merge execution, registry repair, or owner-repo authority
- pass 364 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 365 already proved separate support still honestly holds at `none yet`
- pass 366 already froze the exact first implementation slice around admitted active-session qualification, queue emission, inherited deterministic queue merge, unchanged top-level handoffs, and the exact proof matrix
- pass 290 already proves the bounded provenance-derived queue path that this slice must preserve without redesigning overflow or queue-budget behavior
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 363 exact `resume_failed` contract
- pass 364 root control-plane owner admission
- pass 365 supporting-lane hold at `none yet`
- pass 366 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `resume_failed` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it preserves admitted active-session qualification through `session_state` plus `final_status` only, preserves one fixed `resume_failed` queue item with no widened detail payload beyond `session_id`, `task_id`, and `resume_failure_reason`, preserves fixed `high` severity, preserves inherited deterministic `attention_item_sort_key(...)` queue ordering against the already-admitted broader queue families, preserves queue emission when the admitted active-session state qualifies even if registry health is unavailable while preserving separate `registry_error` coexistence only, preserves separate `registry_drift` coexistence when the active-session registry digest differs from the current registry digest, preserves the unchanged top-level `attention_queue` and `active_session` handoffs through `render_status_payload(...)`, and proves behavior against the frozen pass-366 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget or overflow changes
- retry execution, resume execution, merge execution, registry repair, or owner-repo mutation authority
- broader failure or contradiction-family widening
- queue, registry, runtime, session, execution-receipt, merge, manifest, or owner-repo mutation
- any new item family, status value, payload field, or ordering rule outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- queue payload:
  - `status`
  - `item_count`
  - `highest_severity`
  - `items`
- `resume_failed` item payload:
  - `kind`
  - `severity`
  - `summary`
  - `source_ref`
  - `details.session_id`
  - `details.task_id`
  - `details.resume_failure_reason`
- top-level active-session payload:
  - `active_session`

The worker may render these payload surfaces only.
The worker may not widen them into retry authority, resume authority, merge authority, registry-repair routing, contradiction-family projection, queue-budget metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. `session_state`-qualified emission
   - emit one `resume_failed` when `session_state == "resume_failed"`
   - preserve admitted `session_id`, `task_id`, and `resume_failure_reason` detail fields only
   - preserve fixed `high` severity

2. `final_status`-qualified emission
   - emit one `resume_failed` when `final_status == "resume_failed"` even if `session_state` is different
   - preserve the same bounded payload shape

3. non-qualifying omission
   - omit `resume_failed` when neither admitted active-session state field equals `resume_failed`

4. registry-unavailable coexistence
   - preserve `resume_failed`
   - preserve separate `registry_error` coexistence when registry health is unavailable
   - do not widen into contradiction-family, retry, or repair semantics

5. registry-drift coexistence
   - preserve `resume_failed`
   - preserve separate `registry_drift` coexistence when registry health is available and the active-session digest differs from the current registry digest
   - do not widen the resume-failure payload

6. mixed resume-failed plus other broader queue families
   - preserve all admitted families in one queue
   - preserve final item ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item

7. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `active_session` payload
   - do not widen those handoffs into retry authority, resume authority, merge authority, or doctrine semantics

8. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `resume_failed` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact No-Mutation / No-Repair / No-Queue-State Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one active-session qualification layer using session_state plus final_status only, one resume_failed emission branch inside attention_queue(...), one inherited deterministic attention_item_sort_key(...) queue merge layer, and one unchanged top-level render_status_payload(...) handoff for attention_queue plus active_session, but it may not mutate queue, registry, runtime, session, execution-receipt, merge, manifest, or owner-repo state, change queue-budget or overflow behavior, widen into retry execution, resume execution, merge execution, registry repair, broader failure or contradiction-family mutation, or imply supervisor/operator proof.`

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
- session-manifest, execution-receipt, merge-execution, or runtime-state mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- owner-repo mutation surfaces
- `ops/atlas/*`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader retry-execution, resume-execution, merge-execution, failure, contradiction, supervisor, dispatch, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes or queue-signal overflow changes
- retry execution, resume execution, merge execution, registry repair, broader failure-doctrine widening, or owner-repo mutation authority
- contradiction-family widening
- queue, registry, runtime, session, execution-receipt, merge, manifest, or owner-repo mutation
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, new resume states, reordered item families, or non-deterministic sort behavior
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited pass 290 plus passes 363 through 366 as frozen inputs
3. the exact preserved payload surfaces
4. the exact proof matrix
5. the exact no-mutation guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue resume_failed implementation-readiness closeout and worker-routing pass 368`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local `resume_failed` queue seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Resume Failed Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted resume-failure seam expands through prompt wording into retry execution, resume execution, merge execution, registry repair, failure-doctrine, hidden-state, protected-backlog, or broader runtime semantics that the durable chain has not admitted.
