# AI Long-Run Batch Orchestration Queue-Or-Registry Scaffold Persistence Or Queue-Home Selection Contract Freeze Pass 30 - 2026-06-10

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
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BATCH-ENTRY-VALIDATOR-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-DRAFT-ENTRY-SCAFFOLD-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-TO-VALIDATOR-HANDOFF-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-ENTRY-STATUS-SUMMARY-RENDERER-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-NEXT-SLICE-SELECTION-PASS-29-2026-06-10.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one exact root-bounded contract for `scaffold persistence or queue-home selection` so the selected post-summary seam becomes restart-safe and bounded without implying concrete queue-home choice, registry-home choice, validator execution, status-transition semantics, `_stack` execution-home admission, or owner-repo mutation.

This pass does not:

- implement helper code
- create live queue or registry state
- choose one exact runtime subpath, filename, registry schema, or persistence layout
- admit `_stack` execution-home semantics
- admit validator execution, status-transition, supervisor, dispatch, or resume behavior
- reopen Fitness, `archive/`, `.vercel`, `.env`, secrets, deployment, publication, or `_stack Readiness` surfaces
- claim that contract freeze alone earns marker movement

## Root Health Baseline

- the queue-or-registry batch-entry contract from pass 1 is already frozen
- the validator, scaffold, handoff, and summary first slices are already landed and reconciled on canonical `main`
- the current lane now has one explicit local-input read model over admitted pre-validation artifacts, but still no frozen storage-home seam for durable queue-or-registry state
- pass 29 already selected `scaffold persistence or queue-home selection` as the strongest remaining bounded post-summary seam
- stack path policy already says runtime state belongs in `runtime/`, durable fixtures belong in `data/`, disposable scratch belongs in `tmp/`, and secrets belong in `secrets/`
- the current root validation surface is clean at `critical=0 error=0 warning=50 info=0`
- local `HEAD` is in parity with `origin/main`

## Frozen Family Contract

### `family_name`

- `scaffold persistence or queue-home selection`

### `trigger`

- the operator now has one proven validator gate, one proven scaffold surface, one proven handoff seam, and one proven explicit local-input entry-set summary, but still lacks one durable answer for where queue-or-registry pre-execution state could honestly live
- repeated manual preservation of candidate-entry, scaffold, handoff, or summary artifacts outside one admitted state-home seam is already too lossy for safe long-run batching
- stack path policy already distinguishes runtime state from fixtures, packages, tmp, and secrets, but the queue-or-registry storage-home meaning is still not frozen for this lane
- the next gain should be storage-home definition only, not lifecycle, validator-execution, or execution-home semantics

### `stable_inputs`

- the frozen queue-or-registry field and status contract from `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
- the reconciled validator proof and fail-closed behavior locked by `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BATCH-ENTRY-VALIDATOR-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-09.md`
- the reconciled scaffold proof and fail-closed behavior locked by `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-DRAFT-ENTRY-SCAFFOLD-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-09.md`
- the reconciled handoff proof and fail-closed behavior locked by `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-TO-VALIDATOR-HANDOFF-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
- the reconciled summary proof and fail-closed behavior locked by `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-ENTRY-STATUS-SUMMARY-RENDERER-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
- the post-summary next-slice selection basis from `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-NEXT-SLICE-SELECTION-PASS-29-2026-06-10.md`
- the current stack path contract and state-placement rules in:
  - `stack.yaml`
  - `AGENTS.md`
- the current lane, marker, and restart truth in:
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

### `expected_storage_home_artifact`

- one exact bounded storage-home contract only
- any future durable queue-or-registry pre-execution state must be classified as non-secret runtime state rather than source, fixture, release, scratch, or secret state
- the contract may freeze only:
  - the admitted top-level home class: `runtime/`
  - the forbidden top-level home classes:
    - `repos/`
    - `docs/`
    - `ops/`
    - `data/`
    - `packages/`
    - `tmp/`
    - `secrets/`
  - the rule that exact concrete subpath, filename, registry schema, and persistence layout remain separate later questions
- the contract may describe queue-or-registry state only as pre-execution, root-owned control-plane state below validator execution and below owner-repo mutation truth
- the contract must preserve the pass-1 batch-entry field meanings without rewriting them for storage convenience
- the contract must not treat fixtures, summaries, or receipts as live queue truth by convenience

### `failure_boundary`

- queue-or-registry pre-execution state is allowed to live in repo roots or owner repos
- `data/` fixtures or imports start acting as live queue-or-registry state
- `docs/`, `ops/`, `packages/`, or `tmp/` start acting as durable queue-or-registry storage by convenience
- the contract chooses one exact runtime subpath, filename, schema, or persistence layout by implication rather than leaving those as later bounded questions
- storage-home wording starts implying validator execution, lifecycle advancement, dispatch, supervisor behavior, or `_stack` execution-home routing
- storage-home wording starts acting like permission for owner-repo mutation or owner-truth replacement

### `safe_fallback`

- keep queue-or-registry state storage-agnostic and explicit-local only
- preserve explicit local validator, scaffold, handoff, and summary artifacts only
- emit no persistence-home claim when storage classification contradicts stack path policy
- route back to manual lane receipts rather than inventing live queue or registry state
- stop below owner-surface admission if the exact helper home is still ambiguous

### `owner_boundary`

- ATLAS root owns this contract freeze, state-class meaning, restart projection, and non-claim boundaries
- the exact future helper home for implementation is still a separate next-pass owner-surface question
- `_stack` may later own execution-oriented orchestration semantics, but not from this pass
- Playbook may later consume repeated storage-home doctrine, but not from this pass
- owner repos keep mutation truth, verification truth, and implementation truth

### `non_claim_boundary`

- no live queue-home or registry-home implementation claim
- no exact runtime subpath or concrete persistence-layout claim
- no validator-execution claim
- no execution-ready, status-transition, running-supervised, or dispatch claim
- no `_stack` execution-home claim
- no owner-repo mutation claim
- no admitted, deploy, publication, archive/delete, `.env`, secret, or Fitness claim

## Deferred And Non-Automated Boundaries

### Still deferred below this family

- `scaffold persistence or queue-home selection` owner-surface admission
- exact runtime subpath, filename, or registry schema
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

- the family contract is now exact
- the next honest question is which owner-facing surface should carry this storage-home seam
- helper-home admission should be priced explicitly before any implementation or concrete path discussion

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry scaffold persistence or queue-home selection owner-surface admission pass 31`

Why:

- the storage-home seam now has one exact trigger, input, artifact, failure, fallback, owner, and non-claim contract
- the next honest question is whether the exact future home stays with ATLAS root control-plane surfaces or another already-named surface before any implementation or concrete persistence-layout discussion

## Marker Decision

- `none`

Why:

- this pass freezes one exact storage-home contract only
- it does not land code, execution proof, or widened operator adoption

## Rule

`Persisted Batch State Must Respect Stack Path Classes`

No queue-or-registry persistence seam is honest unless it first classifies future durable state as runtime state and explicitly excludes source, fixtures, releases, scratch, and secret surfaces before any lifecycle or execution semantics reopen.

## Pattern

validator proof -> scaffold proof -> handoff proof -> summary proof -> next-slice reselection -> storage-home contract freeze -> owner-surface admission -> later concrete path discussion

## Failure Mode

`Fixture-As-Queue Drift`

This family becomes fake progress when fixtures, summaries, or docs start acting like live queue-or-registry state instead of forcing one explicit runtime-state classification first.

## What This Pass Proves

This pass proves:

- `scaffold persistence or queue-home selection` now has one exact bounded contract
- the family is restart-safe without choosing one concrete runtime path, execution-home, or lifecycle semantics
- the next honest question is owner-surface admission rather than implementation

This pass does not prove:

- that any helper home is now admitted
- that any concrete queue-home path or registry schema is now chosen
- that storage-home classification counts as validator execution, queue mutation, or execution-ready state
