# AI Long-Run Batch Orchestration Queue-Or-Registry Runtime-State Child-Home Selection Next-Slice Selection Pass 36 - 2026-06-10

- Date: `2026-06-10`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded next-slice selection`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/architecture/STATE-AND-MEMORY-BOUNDARIES.md`
  - `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
  - `docs/ops/MESSAGE-ORIGIN-ID-WORKFLOW-RULE-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-NEXT-SLICE-SELECTION-PASS-29-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-CONTRACT-FREEZE-PASS-30-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-31-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-32-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-33-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-PROMPT-PACK-AND-HANDOFF-CONTRACT-PASS-34-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-PASS-35-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-10.md`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/state/atlas/operator-preferences/codex-desktop-low-interruption.json`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Choose the strongest remaining bounded post-storage next slice for the root-owned `queue-or-registry` family now that top-level `runtime/` home-class truth has real implementation proof, and record the subordinate progress-marker side-objective classification without widening into concrete runtime layout, queue or registry writes, validator execution, lifecycle semantics, `_stack` execution-home admission, or UI work.

This pass does not:

- implement helper code
- freeze the chosen next-slice contract
- choose one exact runtime subtree, filename, schema, or persistence layout
- create queue or registry state
- admit validator execution, status transitions, supervisor behavior, or `_stack` execution-home semantics
- create a native Codex status bar or broader UI surface
- move any marker

## Root Health Baseline

- passes 1 through 35 plus the reconciled storage-home classifier worker cluster are already durable
- the lane now has real proof for validator, scaffold, handoff, summary, and top-level storage-home classification on canonical `main`
- stack path policy already distinguishes retained mutable state from append-only receipts and from fixtures, packages, tmp, and secrets
- `STATE-AND-MEMORY-BOUNDARIES` already says mutable retained state belongs under `runtime/**`, with likely future homes under `runtime/state/` and `runtime/receipts/`
- `AWARENESS-FIRST-WORLD-MODEL` already says queue-like read models should live under `runtime/state/**` when needed and observations belong under `runtime/receipts/**`
- root validation remains clean at `critical=0 error=0 warning=51 info=0`

## Candidate Comparison

The strongest honest post-storage next-slice candidates are:

1. `runtime-state child-home selection`
2. `concrete runtime-layout selection`
3. `execution-ready transition semantics`
4. `_stack` execution-home follow-on

## Selection

Select exactly one next slice:

- `runtime-state child-home selection`

## Why `runtime-state child-home selection` Wins

This is now the strongest remaining bounded seam because the lane already proved the top-level `runtime/` home class, but it still has not frozen whether mutable pre-execution queue-or-registry truth belongs under a retained mutable state lane such as `runtime/state/` or an append-only receipt lane such as `runtime/receipts/`.

What it improves without widening:

- narrows storage truth from `runtime/` in general to one child-home class question only
- separates mutable queue state from receipt history before any concrete subtree or filename is chosen
- uses already-admitted stack path policy and world-model doctrine instead of inventing new runtime buckets
- stays below concrete runtime layout, queue writes, registry writes, validator execution, lifecycle semantics, and `_stack` execution-home routing

Why this is smaller than the remaining alternatives:

- it does not choose one exact runtime subtree, filename, or schema
- it does not require a final queue-home versus registry-home concrete path
- it does not require stronger validated-entry or lifecycle truth than the lane currently owns
- it resolves a real remaining storage ambiguity that concrete layout and execution semantics both depend on

## Deferred Alternatives

### `concrete runtime-layout selection`

Deferred because:

- child-home meaning is still not frozen, so choosing a concrete runtime subtree or filename would invent layout before the state class is fully settled
- it would make the lane sound closer to live persistence than current proof actually supports

Reopen condition:

- only after runtime-state child-home meaning is frozen

### `execution-ready transition semantics`

Deferred because:

- lifecycle semantics still depend on stronger persistence truth than the lane currently owns
- it would widen too quickly from storage classification into status-transition language

Reopen condition:

- only after storage child-home meaning and later concrete persistence seams are frozen

### `_stack` execution-home follow-on

Deferred because:

- `_stack` execution-home semantics remain explicitly later than the current root-local storage family stage
- the stronger immediate gain is still inside root-owned persistence meaning, not shared execution routing

Reopen condition:

- only after later queue-or-registry semantics clearly require execution-home admission beyond root-local storage truth

## Progress-Marker Side Objective Classification

Active target surface inspected:

- local Codex desktop collaboration at the ATLAS root

Observed admitted status surfaces:

- `MESSAGE-ORIGIN-ID-WORKFLOW-RULE-2026-06-09.md` names visible response metadata and the closing `Completion: X%` convention
- `runtime/state/atlas/operator-preferences/codex-desktop-low-interruption.json` prefers low interruption and avoiding visible focus-stealing behavior
- no admitted root doc or runtime contract in the active surface names a writable native Codex statusline or status bar

Decision:

- no native statusline/status bar is admitted for the active target surface
- preserve the fallback convention:
  - end-of-response `Completion: X%`
  - optional durable state-file convention only if restart truth later benefits materially
- do not open broad UI work from this side objective

Marker consequence:

- `none`

Why:

- this classifies the active surface honestly
- it does not land UI, tests, or a broader delivery-state surface

## Supporting Dependency Decision

- `none new yet`

Why:

- next-slice selection alone still does not admit implementation, execution-home work, or support-lane work
- the next honest move is one contract freeze for the chosen child-home seam

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry runtime-state child-home selection contract-freeze pass 37`

Why:

- the strongest remaining bounded seam is now the mutable-state versus receipt-lane child-home question inside `runtime/`
- the next honest move is to freeze that child-home contract around retained mutable state, append-only receipt exclusion, deferred concrete layout, and continued no-write/no-execution boundaries

## Marker Decision

- `none`

Why:

- this pass selects the next slice and classifies the side objective only
- it does not land code, execution proof, or broader operator adoption

## Rule

Freeze Mutable State Class Before Concrete Queue Layout

After top-level `runtime/` admission is real, the next honest step is to freeze whether queue-or-registry truth is retained mutable state or receipt history before choosing any concrete subtree, filename, or lifecycle behavior.

## Pattern

top-level runtime-home proof -> child-home reselection -> child-home contract freeze -> later concrete layout discussion

## Failure Mode

`Receipt-As-Queue Drift`

If the lane jumps from top-level `runtime/` admission straight into concrete path layout or lifecycle semantics without freezing mutable-state-versus-receipt-lane meaning first, receipt history can start masquerading as live queue state and the storage contract becomes misleading.
