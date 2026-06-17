# AI Long-Run Batch Orchestration Queue-Or-Registry World-Model Top-Level Payload Boundary Prompt-Pack And Handoff Contract Pass 458 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-454-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-455-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-456-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-FIRST-IMPLEMENTATION-ADMISSION-PASS-457-2026-06-17.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@fa72b428`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned top-level `world_model` payload boundary.

This pass does not:

- implement or widen code
- change registry semantics, artifact-inventory semantics, queue semantics, or queue ordering
- mutate builder state, snapshot files, attention files, queue, registry, runtime, session, merge, manifest, archive, or owner-repo state
- reopen `_stack`, Playbook, builder ownership, snapshot repair, attention repair, or owner-repo support
- infer world-model truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, runtime state residue, or broad untracked root docs and media

## Root Health Baseline

- pass 454 already froze the exact top-level `world_model` contract around refs, presence booleans, optional digest fields, bounded count fields, fail-closed content omission, and preserved separation from top-level `artifact_inventory` and `registry`
- pass 455 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 456 already proved separate support still honestly holds at `none yet`
- pass 457 already froze the exact first implementation slice around the ref-and-presence layer, readable snapshot and attention dict branches, bounded count fallback, fail-closed omission, unchanged top-level handoff, and the exact proof matrix
- the current helper code in `ops/cortex/render_status.py` already exposes the admitted `world_model_state()` shape while the remaining proof gap stays concentrated in direct helper assertions plus top-level handoff assertions
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 454 top-level `world_model` payload contract, including refs, presence booleans, optional digest fields, bounded count fields, fail-closed omission, top-level `world_model` handoff only, and preserved separation from top-level `artifact_inventory` and `registry`
- pass 455 root control-plane owner admission for this seam
- pass 456 supporting-lane hold at `none yet`
- pass 457 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `world_model_state()` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it preserves only the inherited ref-and-presence layer, preserves only the admitted readable snapshot and attention dict branches, preserves only the admitted digest passthrough and bounded count fallback rules, preserves fail-closed omission for unreadable, undecodable, or non-dict files, preserves the unchanged top-level `world_model` handoff through `render_status_payload(...)`, preserves separation from top-level `artifact_inventory` and top-level `registry`, and proves behavior against the frozen pass-457 matrix

The worker is not allowed to pursue:

- broader `render_status_payload(...)` redesign
- registry-summary or artifact-inventory changes
- queue-budget or queue-ordering changes
- world-model builder mutation, snapshot generation, attention generation, snapshot repair, or attention repair
- queue, registry, runtime, session, merge, manifest, archive, or owner-repo mutation
- any new payload field, new summary family, new runtime-state branch, or adjacent semantics outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly this bounded payload surface:

- `snapshot_ref`
- `attention_ref`
- `snapshot_present`
- `attention_present`
- `snapshot_content_digest`
- `inventory_entry_count`
- `observation_count`
- `attention_content_digest`
- `attention_item_count`

Top-level payload rules remain:

- `snapshot_ref` and `attention_ref` are always present
- `snapshot_present` and `attention_present` are always present
- absent files preserve the refs plus `False` presence booleans without content-derived fields for that file
- present readable JSON object payloads may emit:
  - digest fields through direct `payload.get("content_digest")`
  - bounded snapshot and attention count fields through list-length checks or `0` fallback
- unreadable, undecodable, or non-dict present payloads preserve refs and presence booleans while omitting content-derived fields for that file
- no snapshot-body hydration, observation-body hydration, attention-item hydration, registry-summary fields, or artifact-inventory descriptor projection may leak into top-level `world_model`
- `render_status_payload(...)` preserves the same bounded helper output under top-level `world_model` only
- top-level `artifact_inventory` and top-level `registry` remain separate read-model consequences rather than part of the top-level `world_model` payload

The worker may render this payload surface only.
The worker may not widen it into builder metadata, runtime metadata, queue metadata, registry metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. no world-model files present
   - `world_model_state()` emits only refs and `False` presence booleans
   - no content-derived fields appear

2. snapshot populated dict branch
   - a readable snapshot dict preserves `snapshot_content_digest`
   - `inventory_entry_count` equals the snapshot `inventory_entries` list length
   - `observation_count` equals the snapshot `observations` list length

3. attention populated dict branch
   - a readable attention dict preserves `attention_content_digest`
   - `attention_item_count` equals the attention `attention_items` list length

4. bounded count fallback
   - snapshot count fields fall back to `0` when `inventory_entries` or `observations` are missing or not lists
   - attention count falls back to `0` when `attention_items` is missing or not a list

5. fail-closed content omission
   - present unreadable, undecodable, or non-dict files preserve refs and `True` presence booleans
   - content-derived fields for the failed file stay omitted

6. render-status handoff preservation
   - `render_status_payload(...)` preserves the helper result under top-level `world_model`
   - the handoff does not widen into top-level `artifact_inventory` or top-level `registry` semantics

These proof cases inherit the pass-457 matrix exactly.

## Exact No-Mutation / No-Builder / No-Runtime-Widening Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one inherited world_model_state() ref-and-presence layer, one readable snapshot dict branch, one readable attention dict branch, one bounded count fallback layer, one fail-closed content-omission layer, and one unchanged top-level world_model render_status_payload(...) handoff for the root-owned world-model slice, but it may not mutate builder, snapshot, attention, queue, registry, runtime, session, merge, manifest, archive, or owner-repo state, change artifact-inventory or registry semantics, widen into snapshot generation, attention generation, builder redesign, broader world-model payload redesign, or imply supervisor/operator proof.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted root-local helper and test files
- do not infer payload meaning, proof scope, blocker state, or next-step authority from uncited transcript memory, hidden operator state, or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into builder-runtime, owner-repo, deploy, or protected backlog surfaces.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- world-model builder, snapshot writer, or attention writer implementation surfaces outside the admitted helper file
- registry-summary or artifact-inventory implementation surfaces outside the admitted helper file
- queue or registry mutation surfaces
- runtime-state, session-manifest, merge, archive, or owner-repo mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- `ops/atlas/*`
- `runtime/state/atlas/world-model.*`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader builder, hydration, repair, runtime-snapshot, contradiction, supervision, dispatch, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- builder redesign, snapshot generation, attention generation, snapshot repair, or attention repair
- registry-summary changes, artifact-inventory changes, queue-budget changes, or queue-ordering changes
- builder, queue, registry, runtime, session, merge, manifest, archive, or owner-repo mutation
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, hydrated payload semantics, new branch families, or adjacent summary semantics
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 454 through 457 as frozen inputs
3. the preserved separation between top-level `world_model` truth and top-level `artifact_inventory` plus `registry`
4. the exact preserved payload surface
5. the exact proof matrix
6. the exact no-mutation guard verbatim
7. the exact no-hidden-transcript-state boundary
8. the exact allowed-touch and forbidden-touch surfaces
9. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry world_model top-level payload boundary implementation-readiness closeout and worker-routing pass 459`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local top-level `world_model` seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`World Model Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted top-level `world_model` seam expands through prompt wording into builder mutation, snapshot generation, attention generation, hidden-state, protected-backlog, registry-summary changes, artifact-inventory changes, or broader runtime semantics that the durable chain has not admitted.
