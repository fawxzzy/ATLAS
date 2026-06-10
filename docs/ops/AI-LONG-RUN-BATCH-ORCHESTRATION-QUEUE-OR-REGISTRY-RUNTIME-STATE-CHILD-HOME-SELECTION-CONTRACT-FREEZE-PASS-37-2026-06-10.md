# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Child-Home Selection Contract Freeze Pass 37 - 2026-06-10

- Date: `2026-06-10`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/architecture/STATE-AND-MEMORY-BOUNDARIES.md`
  - `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
  - `docs/architecture/ORCHESTRATION-BOUNDARIES.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-CONTRACT-FREEZE-PASS-30-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-31-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-32-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-33-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-PROMPT-PACK-AND-HANDOFF-CONTRACT-PASS-34-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-PASS-35-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-NEXT-SLICE-SELECTION-PASS-36-2026-06-10.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one exact root-bounded contract for `runtime-state child-home selection` so the selected post-storage seam becomes restart-safe and bounded without implying concrete runtime subtree choice, queue writes, registry writes, validator execution, lifecycle semantics, `_stack` execution-home admission, or owner-repo mutation.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one exact runtime subtree, filename, schema, or persistence layout
- admit `_stack` execution-home semantics
- admit validator execution, status-transition, supervisor, dispatch, or resume behavior
- reopen owner-repo, Fitness, `archive/`, deploy/publication, `.env`, or secret surfaces
- claim that contract freeze alone earns marker movement

## Root Health Baseline

- the queue-or-registry batch-entry contract from pass 1 is already frozen
- the validator, scaffold, handoff, summary, and top-level storage-home classifier slices are already landed and reconciled on canonical `main`
- pass 36 already selected `runtime-state child-home selection` as the strongest remaining bounded post-storage seam
- `STATE-AND-MEMORY-BOUNDARIES` already says retained mutable state belongs under `runtime/**`, with likely future homes under `runtime/state/` and `runtime/receipts/`
- `AWARENESS-FIRST-WORLD-MODEL` already says queue-like read models should live under `runtime/state/**` when needed, while observations belong under `runtime/receipts/**`
- `ORCHESTRATION-BOUNDARIES` already treats receipt lanes as handoff and observation surfaces rather than active orchestration truth
- the current root validation surface is clean at `critical=0 error=0 warning=52 info=0`

## Frozen Family Contract

### `family_name`

- `runtime-state child-home selection`

### `trigger`

- the lane already has real proof that durable pre-execution queue-or-registry truth belongs somewhere under `runtime/`
- the lane still lacks one exact child-home decision for whether that truth is retained mutable state or append-only receipt history
- the next honest gain is child-home meaning only, not concrete runtime layout, queue writes, or execution semantics

### `stable_inputs`

- the frozen queue-or-registry field and status contract from `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
- the reconciled top-level storage-home classifier truth from `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
- the child-home reselection basis from `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-RUNTIME-STATE-CHILD-HOME-SELECTION-NEXT-SLICE-SELECTION-PASS-36-2026-06-10.md`
- the current mutable-state contract in:
  - `stack.yaml`
  - `AGENTS.md`
  - `docs/architecture/STATE-AND-MEMORY-BOUNDARIES.md`
- the current world-model and orchestration doctrine in:
  - `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
  - `docs/architecture/ORCHESTRATION-BOUNDARIES.md`
- the current lane, marker, and restart truth in:
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

### `expected_child_home_artifact`

- one exact bounded child-home contract only
- mutable pre-execution queue-or-registry truth is admitted under `runtime/state/`
- append-only receipt lanes such as `runtime/receipts/` are explicitly not the live mutable queue-or-registry state home
- the contract may freeze only:
  - admitted child-home class: `runtime/state/`
  - excluded receipt-history child-home class: `runtime/receipts/`
  - the rule that exact subtree, filename, schema, snapshot shape, and persistence layout remain separate later questions
- the contract may describe queue-or-registry truth only as retained mutable root-owned control-plane state below validator execution and below owner-repo mutation truth
- the contract must preserve the distinction between mutable queue truth and append-only observation history

### `failure_boundary`

- append-only receipt lanes start acting as the live mutable queue-or-registry truth by convenience
- mutable queue-or-registry truth is narrated as historical observation instead of retained state
- the contract chooses one exact runtime subtree, filename, schema, or layout by implication
- child-home wording starts implying validator execution, lifecycle advancement, dispatch, supervisor behavior, or `_stack` execution-home routing
- child-home wording starts acting like permission for owner-repo mutation or owner-truth replacement

### `safe_fallback`

- keep queue-or-registry persistence below child-home specificity and preserve explicit local artifacts only
- emit no `runtime/state/` claim when retained-state versus receipt-history meaning is still contradictory
- route back to manual lane receipts rather than inventing live queue or registry state
- stop below owner-surface admission if the exact helper home is still ambiguous

### `owner_boundary`

- ATLAS root owns this contract freeze, child-home meaning, restart projection, and non-claim boundaries
- the exact future helper home for implementation is still a separate next-pass owner-surface question
- `_stack` may later own execution-oriented orchestration semantics, but not from this pass
- Playbook may later consume repeated child-home doctrine, but not from this pass
- owner repos keep mutation truth, verification truth, and implementation truth

### `non_claim_boundary`

- no live queue or registry implementation claim
- no exact runtime subtree or concrete persistence-layout claim
- no validator-execution claim
- no execution-ready, status-transition, running-supervised, or dispatch claim
- no `_stack` execution-home claim
- no owner-repo mutation claim

## Deferred And Non-Automated Boundaries

### Still deferred below this family

- `runtime-state child-home selection` owner-surface admission
- exact runtime subtree, filename, schema, or snapshot shape
- concrete queue-home or registry-home layout
- `execution-ready transition semantics`
- `_stack` execution-home follow-on

### Intentionally non-automated

- live queue or registry writes
- validator execution
- status transitions
- worker dispatch or supervision
- owner-repo mutation
- deploy or publication judgment

## Supporting Dependency Decision

- `none yet`

Why:

- the child-home contract is now exact
- the next honest question is which owner-facing surface should carry this seam
- helper-home admission should be priced explicitly before any implementation or concrete layout discussion

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-home selection owner-surface admission pass 38`

Why:

- the child-home seam now has one exact trigger, input, artifact, failure, fallback, owner, and non-claim contract
- the next honest question is whether the exact future home stays with ATLAS root control-plane surfaces or another already-named surface before any implementation or concrete layout discussion

## Marker Decision

- `none`

Why:

- this pass freezes one exact child-home contract only
- it does not land code, execution proof, or widened operator adoption

## Rule

Mutable Queue Truth Must Not Hide Inside Receipt History

No queue-or-registry persistence seam is honest unless mutable pre-execution truth is explicitly separated from append-only receipt history before any concrete layout or lifecycle semantics reopen.

## Pattern

top-level runtime-home proof -> child-home reselection -> child-home contract freeze -> owner-surface admission -> later concrete layout discussion

## Failure Mode

`Receipt-Lane Storage Drift`

This family becomes fake progress when append-only receipt lanes start acting like live mutable queue state instead of forcing one explicit retained-state child-home first.

## What This Pass Proves

This pass proves:

- `runtime-state child-home selection` now has one exact bounded contract
- mutable queue-or-registry truth is classified as retained runtime state, not append-only receipt history
- the next honest question is owner-surface admission rather than implementation

This pass does not prove:

- that any helper home is now admitted
- that any exact runtime subtree or schema is now chosen
- that child-home classification counts as validator execution, queue mutation, or execution-ready state
