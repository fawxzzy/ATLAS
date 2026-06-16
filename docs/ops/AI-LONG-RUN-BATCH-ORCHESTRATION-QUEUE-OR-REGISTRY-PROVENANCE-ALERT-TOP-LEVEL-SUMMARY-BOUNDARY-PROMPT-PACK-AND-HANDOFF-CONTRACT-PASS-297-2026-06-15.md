# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Top-Level Summary Boundary Prompt-Pack And Handoff Contract Pass 297 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-CONTRACT-FREEZE-PASS-293-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-294-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-295-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-FIRST-IMPLEMENTATION-ADMISSION-PASS-296-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-RENDER-STATUS-PAYLOAD-INTEGRATION-PROOF-PASS-288-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@561671a0`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-owned top-level `provenance_alerts` summary boundary.

This pass does not:

- implement or widen code
- change queue-budget or queue-signal behavior
- mutate queue, registry, session, merge, runtime, or manifest state
- reopen `_stack`, Playbook, or owner-repo support
- infer truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media
- claim marker movement, execution-home proof, or broader operator adoption

## Root Health Baseline

- pass 293 already froze the exact top-level `provenance_alerts` summary contract
- pass 294 already admitted `ATLAS root control-plane surfaces` as the owner-facing home
- pass 295 already proved no honest separate supporting lane reopens now
- pass 296 already froze the exact first implementation slice and proof matrix
- passes 288 and 290 already prove the top-level summary stays separate from the stricter bounded `attention_queue` signal set
- root validation is currently clean at `critical=0 error=0 warning=0 info=0`
- local `HEAD` is in parity with `origin/main`
- the shared-root cleanliness gate remains active and is intentionally preserved by leaving the current broad untracked root backlog untouched outside this bounded receipt-and-Book slice

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 293 top-level `provenance_alerts` summary contract, including the preserved payload fields, status meanings, count meanings, and `items[:10]` boundary
- pass 294 root control-plane owner admission for this summary seam
- pass 295 supporting-lane hold at `none yet`
- pass 296 exact first implementation slice and exact proof matrix

The worker must also preserve the already-proved separation from passes 288 and 290:

- the top-level `provenance_alerts` summary remains the fuller bounded status surface
- `attention_queue` remains the stricter derived operator-signal surface and may emit fewer provenance items because of its separate queue cap and overflow handling

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `provenance_alert_summary(...)` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it loads current attention refs exactly once, derives actionable initiative and proposed-session provenance-drift items through the existing bounded helpers, preserves initiative items first and proposed-session items second, emits only the admitted top-level summary payload surface, preserves only the admitted `unavailable` / `clear` / `drift_detected` status meanings, and proves behavior against the frozen pass-296 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget changes
- provenance-drift repair or stale-ref cleanup
- queue or registry mutation
- manifest or runtime-state mutation
- supervisor, merge, dispatch, or resume behavior
- any new evidence family outside the already frozen summary seam

## Exact Preserved Payload Surface

The worker must preserve exactly this bounded payload surface:

- `status`
- `initiative_item_count`
- `proposal_item_count`
- `item_count`
- `items`

Allowed `status` values only:

- `unavailable`
- `clear`
- `drift_detected`

Top-level payload rules remain:

- `initiative_item_count` counts actionable initiative provenance-drift items only
- `proposal_item_count` counts actionable proposed-session provenance-drift items only
- `item_count` is the total of those two actionable groups
- `items` preserves initiative items first and proposed-session items second
- `items` is bounded to `items[:10]`

The worker may render this payload surface only.
The worker may not widen it into queue-budget metadata, provenance-repair plans, runtime-state narration, or broader operator routing semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. current attention refs unavailable
   - emit `status` as `unavailable`
   - preserve all counts as `0`
   - preserve `items` as `[]`

2. actionable initiative-only drift
   - emit `status` as `drift_detected`
   - preserve `initiative_item_count` above `0`
   - preserve `proposal_item_count` as `0`
   - preserve the first item as `initiative_provenance_drift`

3. actionable proposed-session-only drift
   - emit `status` as `drift_detected`
   - preserve `initiative_item_count` as `0`
   - preserve `proposal_item_count` above `0`
   - preserve the first item as `proposed_session_provenance_drift`

4. mixed initiative and proposed-session drift
   - emit `status` as `drift_detected`
   - preserve both count families above `0`
   - preserve initiative items before proposed-session items

5. fully resolved attention and initiative refs
   - emit `status` as `clear`
   - preserve all counts as `0`
   - preserve `items` as `[]`

6. more than ten actionable drift items
   - preserve full actionable totals in the three count fields
   - preserve `items` as bounded to the first ten ordered items only

These proof cases inherit the pass-296 matrix exactly.

## Exact No-Mutation / No-Queue-State / No-Registry-State Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one explicit current-attention-ref load gate, one initiative provenance-alert helper invocation, one proposed-session provenance-alert helper invocation, one initiative-first ordered concatenation layer, one top-level status-and-count renderer, and one fail-closed unavailable fallback for the root-owned provenance_alert_summary(...) slice, but it may not mutate queue, registry, runtime, session, merge, manifest, or owner-repo state, change queue-budget behavior, repair provenance drift, widen into attention_queue semantics, or imply supervisor/operator proof.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted root-local helper and test files
- do not infer payload meaning, proof scope, blocker state, or next-step authority from uncited transcript memory, hidden operator state, or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`
- local non-secret fixtures or static inputs strictly needed to prove the admitted matrix, if such fixtures become necessary inside the same root-owned slice

The worker may touch only implementation-local surfaces for the admitted first slice.
The worker may not widen into shared helper-runtime, owner-repo, deploy, or protected backlog surfaces.

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry mutation surfaces
- session-manifest or runtime-state mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- owner-repo mutation surfaces
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- supervisor, merge, dispatch, resume, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes or queue-signal overflow changes
- queue, registry, runtime, manifest, session, or merge mutation
- provenance repair or missing-file restoration
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, or reordered item families
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited passes 293 through 296 as frozen inputs
3. the preserved separation from passes 288 and 290 between top-level summary truth and bounded queue signals
4. the exact preserved payload surface
5. the exact proof matrix
6. the exact no-mutation guard verbatim
7. the exact no-hidden-transcript-state boundary
8. the exact allowed-touch and forbidden-touch surfaces
9. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry provenance-alert top-level summary boundary implementation-readiness closeout and worker-routing pass 298`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether this docs chain is materially complete enough to leave docs-only mode and route one bounded implementation packet without reopening queue-budget, provenance-repair, or shared-helper questions

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for the top-level `provenance_alerts` summary seam.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Top-Level Provenance Summary Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted summary seam expands through prompt wording into queue-budget edits, provenance repair, hidden transcript-state inference, protected backlog cleanup, or broader operator semantics that the durable chain has not admitted.
