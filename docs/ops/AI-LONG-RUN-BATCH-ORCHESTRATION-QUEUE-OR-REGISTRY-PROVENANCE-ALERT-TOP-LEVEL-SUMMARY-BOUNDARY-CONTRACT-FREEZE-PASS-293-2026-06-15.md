# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Top-Level Summary Boundary Contract Freeze Pass 293 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-PROOF-AND-PAYLOAD-BOUNDARY-HARDENING-PASS-287-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-RENDER-STATUS-PAYLOAD-INTEGRATION-PROOF-PASS-288-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-DECISION-PASS-289-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-RESTART-TRUTH-RECEIPT-PASS-291-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-NEXT-SLICE-SELECTION-PASS-292-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@0092bd28`

## Objective

Freeze one exact root-bounded contract for the top-level `provenance_alerts` summary so the post-budget status payload becomes restart-safe without reopening broader `attention_queue` semantics, provenance repair work, runtime mutation, or supervisor/operator proof.

This pass does not implement code, change queue routing, repair provenance drift, or move any marker.

## Root Health Baseline

- pass 292 already selected `provenance-alert top-level summary boundary` as the smallest honest follow-on after queue-budget restart truth
- passes 287 through 290 already proved:
  - malformed provenance queue payloads fail closed
  - `render_status_payload(...)` preserves the top-level `provenance_alerts` summary
  - `attention_queue` may emit a smaller derived provenance signal set than the top-level summary
- `ops/cortex/render_status.py` already expresses the unfrozen seam in `provenance_alert_summary(...)`
- root validation is currently clean at `critical=0 error=0 warning=0 info=0`

## Frozen Family Contract

### `family_name`

- `provenance-alert top-level summary boundary`

### `trigger`

- the queue-side provenance signal budget is already decided, integrated, and restart-safe
- the status payload still retains a separate top-level `provenance_alerts` summary whose contract is only implicit in `provenance_alert_summary(...)`
- the smallest remaining bounded seam is the explicit meaning of that top-level summary, not broader queue semantics and not provenance-repair behavior

### `stable_inputs`

- the provenance queue payload boundary from pass 287
- the full `render_status_payload(...)` integration proof from pass 288
- the queue signal budget plus overflow rule from passes 289 through 291
- the exact next-slice selection from pass 292
- the current helper and test surfaces in:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
- the retained stack-governance doctrine in:
  - `stack.yaml`
  - `AGENTS.md`

### `expected_artifact`

- one exact bounded top-level `provenance_alerts` summary contract only
- the contract may freeze only:
  - the top-level payload surface:
    - `status`
    - `initiative_item_count`
    - `proposal_item_count`
    - `item_count`
    - `items`
  - the status meanings:
    - `unavailable` when current attention refs cannot be loaded
    - `clear` when actionable provenance drift is absent
    - `drift_detected` when one or more actionable provenance-drift items exist
  - the count meanings:
    - `initiative_item_count` counts only actionable initiative provenance-drift items
    - `proposal_item_count` counts only actionable proposed-session provenance-drift items
    - `item_count` is the total of those two actionable groups
  - the top-level item composition rule:
    - initiative provenance-drift items appear first
    - proposed-session provenance-drift items appear second
    - the preserved top-level `items` array is bounded to `items[:10]`
  - the separation rule:
    - `provenance_alerts` remains the fuller bounded status summary
    - `attention_queue` remains a separate derived operator-signal surface that may emit fewer provenance items because of its stricter queue budget and overflow handling

### `failure_boundary`

- the top-level summary starts acting like a broader `attention_queue` contract
- queue-budget behavior and top-level summary behavior collapse into one implied surface
- the top-level summary starts implying provenance repair, mutation, or supervisor escalation rather than bounded status reporting
- the item contract widens beyond initiative plus proposed-session actionable drift records from the current helper family

### `safe_fallback`

- keep the top-level summary separate from queue routing
- fail closed to `unavailable` when attention refs cannot be loaded
- keep actionable counts and bounded item projection only
- stop below provenance repair, runtime mutation, or broader queue-model claims

### `owner_boundary`

- ATLAS root owns this contract freeze, restart projection, and non-claim boundaries
- exact code-level helper changes or proof-hardening changes remain a separate next-pass owner-surface question
- owner repos keep mutation truth, verification truth, and implementation truth

### `non_claim_boundary`

- no code or test implementation change
- no queue-budget or queue-ordering change
- no provenance-drift repair, stale-ref cleanup, or missing-file restoration claim
- no queue, registry, session, merge, deployment, or runtime mutation claim
- no supervisor/operator proof claim

## Supporting Dependency Decision

- `none yet`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry provenance-alert top-level summary boundary owner-surface admission pass 294`

## Marker Decision

- `none`

## Rule

Freeze the top-level `provenance_alerts` summary boundary before reopening broader queue semantics, provenance repair, or supervisor-facing follow-on families.
