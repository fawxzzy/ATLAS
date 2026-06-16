# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Registry-Error Owner-Surface Admission Pass 322 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-REGISTRY-ERROR-CONTRACT-FREEZE-PASS-321-2026-06-16.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@2ef38044`

## Objective

Admit the exact owner-facing home for the contract-frozen `registry_error` queue seam, keep the family rooted in ATLAS control-plane registry and read-model helpers, and stop below supporting-lane admission, implementation, contradiction-family widening, registry repair, or owner-repo reopening.

This pass does not:

- implement helper code or tests
- change the contract-frozen qualification rule, payload fields, severity, source ref, or ordering
- admit `_stack` command-runtime or helper ownership
- admit Playbook doctrine export
- admit registry repair, registry mutation, queue mutation, or hidden-state inference
- admit active-session contradiction, governed-surface contradiction, merge, closure, or worker-family ownership transfer
- admit owner-repo mutation, deploy/publication work, `.env`, or secret work

## Root Health Baseline

- pass 321 already froze the exact `registry_error` sentinel contract around falsey `registry_state.ok`, fixed `critical` severity, fixed `docs/registry` source-ref discipline, and `details.error` only
- `ops/cortex/render_status.py` already shows the seam as one bounded root-local producer-consumer chain: `load_registry_state()` derives the registry payload, `validate_surface_ref(...)` fails closed when registry health is unavailable, `attention_queue(...)` emits the compact queue sentinel, and `render_status_payload(...)` carries the queue into the top-level status payload
- the same helper also keeps adjacent registry-derived contradiction families separate: `unknown_tool_surface`, `unknown_extension_surface`, and `registry_drift` remain different seams with stricter registry-health preconditions
- root validation remains clean at `critical=0 error=0 warning=0 info=0`
- local `HEAD` remains in parity with `origin/main`

## Owner-Surface Candidates Considered

### ATLAS root control-plane surfaces

What they already own here:

- root-local `load_registry_state()` registry-load and error capture behavior
- root-local `attention_queue(...)` emission semantics for this bounded sentinel
- root-local `validate_surface_ref(...)` fail-closed behavior when registry health is unavailable
- root-local `render_status_payload(...)` handoff of the derived queue into operator-facing status output
- receipt, restart, and marker consequence for this queue seam

Why they win:

- all producing truth for this family already stays inside ATLAS-root control-plane helpers
- all current consuming truth for this family also stays inside ATLAS-root operator status surfaces
- the family still defines bounded derived registry-load failure meaning, not registry repair, runtime command execution, or doctrine export
- keeping ownership at root preserves the contract-frozen separation between the compact `registry_error` sentinel and the separate contradiction families that only exist when registry health is available

### `_stack`

Why it does not win yet:

- `_stack` owns shared execution-oriented command and helper-runtime seams
- `registry_error` is still one root-local read-model sentinel, not a command-runtime, registry-repair, or shared execution contract
- moving ownership into `_stack` now would blur control-plane registry visibility with later repair or operator-routing semantics that this pass has not admitted

### Playbook

Why it does not win:

- Playbook is still a later doctrine or export consumer at most
- this family is not yet a reusable cross-repo helper or ratified doctrine lane; it remains one exact ATLAS-root queue seam

### owner repos

Why they do not win:

- no owner repo owns `load_registry_state()`, root-side registry bundle interpretation, `validate_surface_ref(...)`, or root-side `attention_queue(...)` rendering
- the family is stack-level control-plane truth rather than repo-local mutation or release truth

### Registry repair and contradiction families

Why they do not win:

- `registry_error` describes failed registry load only; it does not grant repair authority
- `unknown_tool_surface`, `unknown_extension_surface`, and `registry_drift` are adjacent but separate queue families with different admission conditions
- contradiction visibility cannot inherit ownership of this sentinel when its own branches remain fail-closed under unhealthy registry state

## Admission Decision

The exact owner-facing home is:

- `ATLAS root control-plane surfaces`

That home includes only the bounded seam currently visible in:

- `ops/cortex/render_status.py` inside `load_registry_state()`
- `ops/cortex/render_status.py` inside `validate_surface_ref(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`
- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- root book and receipt mirrors that carry restart truth for this queue family

This owner admission means:

- ATLAS root owns the canonical qualification rule for `registry_error`
- ATLAS root owns the bounded read-model meaning of the emitted queue item
- ATLAS root owns the fail-closed split between this sentinel and the separate registry-health-dependent contradiction families
- ATLAS root owns restart-safe consequence for the next packet in this family

This owner admission does not mean:

- ATLAS root now owns registry repair or registry mutation authority
- `_stack` ownership is rejected forever
- implementation is admitted

## Supporting Dependency Decision

- `none yet`

Why:

- the producing and consuming surfaces already sit inside one root-owned registry and read-model seam
- no shared runtime, doctrine, gateway, or owner-repo dependency is required merely to state ownership honestly
- if support is later admitted, it must be proven explicitly rather than inferred from eventual code touch

## Still Deferred

The following remain outside this pass:

- `_stack` command or runtime helpers
- Playbook doctrine export
- implementation proof
- registry repair or registry mutation
- governed-surface contradiction family admission
- queue-budget or overflow redesign
- owner-repo mutation

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue registry_error supporting-lane admission pass 323`

Why:

- the family contract and owner home are now explicit
- the next honest question is whether any exact separate support seam reopens, or whether support still holds at `none yet`

## Marker Decision

- `none`

Why:

- this is docs-only ownership clarification
- no new implementation, proof expansion, or adoption widening landed

## Rule

When one registry-failure queue family is produced and consumed entirely inside ATLAS-root registry and read-model helpers, ownership stays at ATLAS root until a shared runtime, repair, or doctrine seam is explicitly admitted.

## Pattern

exact family contract freeze -> root owner-surface admission -> explicit support decision -> only then implementation admission

## Failure Mode

`Registry Error Ownership Drift`

If this family is pushed into `_stack`, Playbook, owner repos, or registry-repair ownership before support and implementation boundaries are admitted, bounded root-side registry visibility turns into premature repair, doctrine, or contradiction creep.
