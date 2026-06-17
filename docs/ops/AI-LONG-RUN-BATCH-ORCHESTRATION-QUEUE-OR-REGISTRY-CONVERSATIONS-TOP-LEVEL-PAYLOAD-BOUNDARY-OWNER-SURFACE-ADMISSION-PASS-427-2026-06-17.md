# AI Long-Run Batch Orchestration Queue-Or-Registry Conversations Top-Level Payload Boundary Owner-Surface Admission Pass 427 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-CONVERSATION-ACTION-REQUEST-OWNER-SURFACE-ADMISSION-PASS-308-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONVERSATIONS-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-426-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `ops/atlas/converse.py`
  - `ops/atlas/awareness.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@837b6cad`

## Objective

Admit the exact owner-facing home for the contract-frozen top-level `conversations` payload boundary, keep queue/request semantics and broader Awareness meaning deferred, and stop below supporting-lane admission, implementation, or runtime-mutation widening.

This pass does not:

- implement helper code or tests
- change the contract-frozen `conversations` qualifier, payload shape, bounded window, or ordering
- change `conversation_action_request` queue semantics
- change top-level `proposal_only` filtering semantics
- admit `_stack` helper-runtime ownership
- admit Playbook doctrine export
- admit transcript hydration, world-model mutation, runtime mutation, or owner-repo mutation
- claim that owner-surface admission alone earns marker movement

## Root Health Baseline

- pass 426 already froze one exact top-level `conversations` payload contract
- the unresolved question from pass 426 is which surface honestly owns that fuller conversation-state seam before any support or implementation talk
- `ops/cortex/render_status.py`, `ops/atlas/converse.py`, and `ops/atlas/awareness.py` already show the seam as root-local status read-model plus operator-facing consumer logic, not shared execution runtime
- root validation remains clean at `critical=0 error=0 warning=3 info=0`

## Owner-Surface Candidates Considered

### ATLAS root control-plane surfaces

What they already own:

- root-local `conversation_manifest` truth and manifest path discipline through `ops/atlas/converse.py`
- root-local `conversation_summary(...)` and `render_status_payload(...)` semantics in `ops/cortex/render_status.py`
- root-local separation between fuller top-level `conversations`, narrower queue-side `conversation_action_request`, and queue-derived top-level `proposal_only`
- root-local operator-facing consumers in `ops/atlas/awareness.py`, including Awareness fetch/search and the thin `/atlas/voice` read model
- restart-book consequence and receipt routing for this payload seam

Why they win:

- all producing truth remains inside ATLAS-root conversation manifest, status read-model, and operator-facing projection helpers
- all currently observed consuming truth also remains inside ATLAS-root control-plane surfaces
- the family still defines one bounded status payload and downstream root-local read-model usage, not shared execution runtime behavior
- admitting root here preserves the explicit split between fuller top-level conversation state, narrower queue-side request signals, and the filtered queue-derived `proposal_only` subset without implying `_stack` command ownership

### `_stack`

Why it does not win yet:

- `_stack` owns shared execution-oriented command and runtime seams
- this family has not admitted command-design work, shared helper-runtime behavior, or any execution-home dependency
- moving the top-level `conversations` seam into `_stack` now would blur root-owned status meaning with later operator/runtime semantics

### Playbook

Why it does not win:

- Playbook owns reusable doctrine and cross-repo pattern extraction
- this family is still fixing one exact root-local owner home before any doctrine export or reusable helper shape is in scope

### owner repos

Why they do not win:

- the seam is stack-level conversation status truth, not repo-local mutation truth
- owner repos do not own `conversation_summary(...)`, `render_status_payload(...)`, root-side Awareness payloads, or the Book restart consequences for this boundary

### voice and awareness consumers as separate ownership homes

Why they do not win separately:

- `/atlas/voice` and Awareness fetch/search are downstream consumers of the already-root-owned conversation status payload
- they reuse the seam, but they do not displace the owner-facing home of the payload contract itself

## Admission Decision

### Summary home remains at root

- `ATLAS root control-plane surfaces`

What that means:

- ATLAS root owns the canonical top-level `conversations` payload boundary
- ATLAS root owns the meaning of the bounded descriptor-backed count and recent-item payload, deterministic ordering, and explicit separation from queue/request semantics
- ATLAS root owns restart-safe projection of this payload seam and next-packet consequence
- ATLAS root does not thereby become a transcript-hydration, runtime-execution, or owner-repo mutation home

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

- queue severity or queue-family changes
- top-level `proposal_only` widening
- transcript hydration or transcript-derived inference
- `_stack` helper-home or command-design work
- Playbook doctrine export
- Awareness or `/atlas/voice` payload widening beyond current root-local consumption
- implementation proof
- marker movement

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry conversations top-level payload boundary supporting-lane admission pass 428`

Why:

- the payload contract and owner-facing home are now explicit
- the next honest question is whether one exact separate support seam reopens now or whether the family remains root-local at this stage
- implementation would be premature before that support question is frozen

## Marker Decision

- `none`

## Rule

`Top-Level Conversations Truth Stays At Root`

Until the top-level `conversations` payload crosses from root-bounded status meaning into shared helper-runtime or execution semantics, the owner-facing home belongs to ATLAS root control-plane surfaces rather than `_stack`, Playbook, or any owner repo.

## Pattern

top-level payload contract freeze -> root control-plane owner admission -> explicit support decision -> only then discuss shared helper-runtime or implementation

## Failure Mode

`Conversations Home Collapse`

This family becomes dishonest when a root-bounded top-level conversation-state seam is pushed into `_stack`, standalone Awareness ownership, voice ownership, or owner-repo helper ownership before support and implementation semantics are explicitly admitted.
