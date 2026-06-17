# AI Long-Run Batch Orchestration Queue-Or-Registry Legacy-Compatibility Top-Level Payload Boundary Owner-Surface Admission Pass 406 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `docs/ops/LEGACY-RUNTIME-BACKFILL-RUNBOOK.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LEGACY-COMPATIBILITY-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-405-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Admit the exact owner-facing surface for the contract-frozen top-level `legacy_compatibility` payload boundary, keep queue semantics and legacy remediation semantics deferred, and stop below supporting-lane admission, implementation, or blocker-doctrine widening.

This pass does not:

- implement helper code
- change `attention_queue` routing or queue budgets
- admit `_stack` helper-runtime ownership
- admit archive action, repair action, governed-v1 blocker semantics, or runtime mutation
- admit owner-repo mutation, deploy/publication work, `.env`, or secret work
- claim that owner-surface admission alone earns marker movement

## Root Health Baseline

- pass 405 already froze one exact top-level `legacy_compatibility` payload contract
- the unresolved question from pass 405 is which surface honestly owns that bounded payload seam before any support or implementation talk
- `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` already show the seam as root-local status read-model logic plus proof, not shared execution runtime
- root validation remains clean at `critical=0 error=0 warning=3 info=0`

## Owner-Surface Candidates Considered

### ATLAS root control-plane surfaces

What they already own:

- stack doctrine
- lane definitions
- restart projection and receipt consequence
- status read-model truth for root-bounded Cortex surfaces
- the non-claim boundary that separates the richer top-level `legacy_compatibility` payload from the stricter queue-side `legacy_compatibility_signal`

Why they win:

- the seam is still one bounded status-payload contract inside root-owned descriptor, read-model, and proof surfaces
- the family remains below shared helper-runtime, archive action, repair action, governed-v1 blocker semantics, and owner-repo mutation
- admitting root here preserves the explicit split between the fuller top-level legacy payload and the smaller queue-side signal without implying `_stack` command ownership
- the concrete implementation and proof surfaces already live in ATLAS root and do not require a cross-repo helper home for this stage

### `_stack`

Why it does not win yet:

- `_stack` owns shared execution-oriented orchestration helpers, command-runtime behavior, and worker flow
- this family has not admitted command-design work, shared helper-runtime behavior, or any execution-home dependency
- moving the top-level legacy payload seam into `_stack` now would blur root-owned status meaning with later operator/runtime semantics

### Playbook

Why it does not win:

- Playbook owns reusable doctrine and cross-repo pattern extraction
- this family is still fixing one exact root-local owner home before any doctrine export or reusable helper shape is in scope

### owner repos

Why they do not win:

- the seam is stack-level status truth, not repo-local mutation truth
- owner repos do not own `render_status` payload semantics or the Book restart consequences for this boundary

## Admission Decision

### Summary home remains at root

- `ATLAS root control-plane surfaces`

What that means:

- ATLAS root owns the canonical top-level `legacy_compatibility` payload boundary
- ATLAS root owns the meaning of the bounded descriptor-backed item set, richer field surface, and deterministic ordering below queue-runtime and remediation semantics
- ATLAS root owns restart-safe projection of this payload seam and next-packet consequence
- ATLAS root does not thereby become an archive-action, repair-action, governed-v1 blocker, or owner-repo mutation home

### Execution and helper-runtime ownership remain deferred

- `_stack` remains a later candidate owner only if this family crosses into shared command-runtime or operator-helper semantics

### Doctrine ownership remains deferred

- Playbook remains a later candidate consumer for reusable pattern extraction

### Repo ownership remains unchanged

- owner repos still own:
  - repo-local mutation truth
  - repo-local verification truth
  - repo-local implementation truth

## Supporting Dependency Decision

- `none yet`

Why:

- owner-surface admission is now exact
- the next honest question is whether any separate support seam actually reopens from that decision
- support should be admitted explicitly rather than assumed from eventual implementation

## Still Not Admitted In This Pass

- queue-budget changes
- `attention_queue` contract widening
- archive action, repair action, or governed-v1 blocker semantics
- `_stack` helper-home or command-design work
- supervisor/operator proof
- marker movement

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry legacy_compatibility top-level payload boundary supporting-lane admission pass 407`

Why:

- the payload contract and owner-facing home are now explicit
- the next honest question is whether one exact separate support seam reopens now or whether the family remains root-local at this stage
- implementation would be premature before that support question is frozen

## Marker Decision

- `none`

Why:

- this pass admits the owner-facing surface only
- it does not land code, proof hardening, or broader operator adoption

## Rule

`Top-Level Legacy Compatibility Truth Stays At Root`

Until the top-level `legacy_compatibility` payload crosses from root-bounded status meaning into shared helper-runtime or execution semantics, the owner-facing home belongs to ATLAS root control-plane surfaces rather than `_stack`, Playbook, or any owner repo.

## Pattern

top-level payload contract freeze -> root control-plane owner admission -> explicit support decision -> only then discuss shared helper-runtime or implementation

## Failure Mode

`Legacy Payload Home Collapse`

This family becomes dishonest when a root-bounded top-level legacy status seam is pushed into `_stack` or owner-repo helper ownership before support and implementation semantics are explicitly admitted.
