# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Blocked-Worker Owner-Surface Admission Pass 329 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-BLOCKED-WORKER-CONTRACT-FREEZE-PASS-328-2026-06-16.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@7f32f81d`

## Objective

Admit the exact owner-facing home for the contract-frozen `blocked_worker` queue seam, keep the family rooted in ATLAS control-plane descriptor and read-model helpers, and stop below supporting-lane admission, implementation, worker-control doctrine, contradiction-family widening, or owner-repo reopening.

This pass does not:

- implement helper code or tests
- change the contract-frozen qualification rule, payload fields, severity, or ordering
- admit `_stack` command-runtime or helper ownership
- admit Playbook doctrine export
- admit worker launch, dispatch, claim, done, pause, resume, or merge authority
- admit queue, registry, runtime, session, manifest, or owner-repo mutation
- admit owner-repo mutation, deploy/publication work, `.env`, or secret work

## Root Health Baseline

- pass 328 already froze the exact `blocked_worker` contract around `latest_worker_states(...)` plus `blocked_workers(...)` qualification, admitted `worker_id`/`assignment_id`/`state`/`blocked_reason` detail fields only, fixed severity branching, inherited deterministic ordering, and strict separation from worker-control authority
- `ops/cortex/render_status.py` already shows the seam as one bounded root-local producer-consumer chain: `latest_worker_states(...)` chooses one latest `worker_status` descriptor per worker, `blocked_workers(...)` derives the compact blocked-worker read model, `attention_queue(...)` emits the compact queue item plus optional registry-surface validation follow-ons, and `render_status_payload(...)` carries the queue into the top-level status payload
- the same helper also keeps adjacent worker/runtime families separate: active-session, merge-request, closure, and contradiction-family visibility remain different seams with different admission conditions
- root validation remains clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` remains in parity with `origin/main`

## Owner-Surface Candidates Considered

### ATLAS root control-plane surfaces

What they already own here:

- root-local `latest_worker_states(...)` latest-descriptor selection behavior
- root-local `blocked_workers(...)` read-model derivation for this bounded seam
- root-local `attention_queue(...)` emission semantics for this bounded sentinel
- root-local `validate_surface_ref(...)` contradiction-family fail-closed behavior under unhealthy registry state
- root-local `render_status_payload(...)` handoff of the derived queue into operator-facing status output
- receipt, restart, and marker consequence for this queue seam

Why they win:

- all producing truth for this family already stays inside ATLAS-root control-plane helpers
- all current consuming truth for this family also stays inside ATLAS-root operator status surfaces
- the family still defines bounded worker-state visibility, not worker command execution, worker mutation, or doctrine export
- keeping ownership at root preserves the contract-frozen separation between compact blocked-worker visibility and separate launch, claim, done, merge, or contradiction families

### `_stack`

Why it does not win yet:

- `_stack` owns shared execution-oriented command and helper-runtime seams
- `blocked_worker` is still one root-local read-model sentinel, not a command-runtime, dispatch, or shared execution contract
- moving ownership into `_stack` now would blur control-plane visibility with later worker-action semantics that this pass has not admitted

### Playbook

Why it does not win:

- Playbook is still a later doctrine or export consumer at most
- this family is not yet a reusable cross-repo helper or ratified doctrine lane; it remains one exact ATLAS-root queue seam

### owner repos

Why they do not win:

- no owner repo owns `latest_worker_states(...)`, root-side blocked-worker read-model interpretation, `attention_queue(...)`, or root-side status rendering
- the family is stack-level control-plane truth rather than repo-local mutation or release truth

### Worker-control and contradiction families

Why they do not win:

- `blocked_worker` describes worker blockage visibility only; it does not grant launch, dispatch, claim, done, pause, resume, or merge authority
- `unknown_tool_surface` and `unknown_extension_surface` are adjacent but separate contradiction families with stricter registry-health preconditions
- worker-control visibility cannot inherit ownership of this sentinel when its own action semantics remain explicitly out of scope

## Admission Decision

The exact owner-facing home is:

- `ATLAS root control-plane surfaces`

That home includes only the bounded seam currently visible in:

- `ops/cortex/render_status.py` inside `latest_worker_states(...)`
- `ops/cortex/render_status.py` inside `blocked_workers(...)`
- `ops/cortex/render_status.py` inside `validate_surface_ref(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`
- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- root book and receipt mirrors that carry restart truth for this queue family

This owner admission means:

- ATLAS root owns the canonical qualification rule for `blocked_worker`
- ATLAS root owns the bounded read-model meaning of the emitted queue item
- ATLAS root owns the fail-closed split between this sentinel and separate registry-surface contradiction families
- ATLAS root owns restart-safe consequence for the next packet in this family

This owner admission does not mean:

- ATLAS root now owns worker-control authority
- `_stack` ownership is rejected forever
- implementation is admitted

## Supporting Dependency Decision

- `none yet`

Why:

- the producing and consuming surfaces already sit inside one root-owned descriptor and read-model seam
- no shared runtime, doctrine, gateway, or owner-repo dependency is required merely to state ownership honestly
- if support is later admitted, it must be proven explicitly rather than inferred from eventual code touch

## Still Deferred

The following remain outside this pass:

- `_stack` command or runtime helpers
- Playbook doctrine export
- implementation proof
- worker launch, dispatch, claim, done, pause, resume, or merge doctrine
- governed-surface contradiction family admission
- queue-budget or overflow redesign
- owner-repo mutation

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue blocked_worker supporting-lane admission pass 330`

Why:

- the family contract and owner home are now explicit
- the next honest question is whether any exact separate support seam reopens, or whether support still holds at `none yet`

## Marker Decision

- `none`

Why:

- this is docs-only ownership clarification
- no new implementation, proof expansion, or adoption widening landed

## Rule

When one blocked-worker queue family is produced and consumed entirely inside ATLAS-root descriptor and read-model helpers, ownership stays at ATLAS root until a shared runtime, worker-action, or doctrine seam is explicitly admitted.

## Pattern

exact family contract freeze -> root owner-surface admission -> explicit support decision -> only then implementation admission

## Failure Mode

`Blocked Worker Ownership Drift`

If this family is pushed into `_stack`, Playbook, owner repos, or worker-action ownership before support and implementation boundaries are admitted, bounded root-side worker-state visibility turns into premature dispatch, doctrine, or contradiction creep.
