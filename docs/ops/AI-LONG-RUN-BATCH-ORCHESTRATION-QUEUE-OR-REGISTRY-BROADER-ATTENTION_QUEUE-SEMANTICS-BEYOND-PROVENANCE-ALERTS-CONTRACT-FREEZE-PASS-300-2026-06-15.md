# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention_Queue Semantics Beyond Provenance Alerts Contract Freeze Pass 300 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-DECISION-PASS-289-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-CONTRACT-FREEZE-PASS-293-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-PROMPT-PACK-AND-HANDOFF-CONTRACT-PASS-297-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-NEXT-SLICE-SELECTION-PASS-299-2026-06-15.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@019e3e0b`

## Objective

Freeze one exact root-bounded contract for broader `attention_queue` semantics beyond provenance alerts so the operator-facing derived queue surface becomes restart-safe without widening into queue mutation, provenance repair, runtime mutation, transcript inference, or execution semantics.

This pass does not implement code, change queue behavior, repair provenance drift, or move any marker.

## Root Health Baseline

- pass 299 already selected broader `attention_queue` semantics beyond provenance alerts as the smallest honest follow-on after the top-level `provenance_alerts` summary seam was reconciled
- passes 289 and 290 already froze and proved the provenance-derived queue budget, including the separate `provenance_alert_overflow` signal
- pass 293 already froze the separate top-level `provenance_alerts` summary boundary so the broader queue contract no longer needs to carry that full top-level payload
- the status runbook already states that `attention_queue` is a derived operator surface, not an execution queue, and that it must stay descriptor-backed and deterministic
- `ops/cortex/render_status.py` already expresses the broader unfrozen queue seam in `attention_queue(...)`, `attention_item(...)`, `attention_item_sort_key(...)`, `validate_surface_ref(...)`, `initiative_attention_items(...)`, and `provenance_attention_items(...)`
- root validation is currently clean at `critical=0 error=0 warning=0 info=0`

## Frozen Family Contract

### `family_name`

- `broader attention_queue semantics beyond provenance alerts`

### `trigger`

- the provenance-only queue seam is already budgeted and proven
- the separate top-level `provenance_alerts` summary seam is already explicit and reconciled
- the remaining bounded read-model ambiguity is the broader contract for how `attention_queue` composes, orders, and reports its multi-family operator-review items

### `stable_inputs`

- the queue-budget and provenance overflow rule from passes 289 and 290
- the separate top-level summary boundary from pass 293
- the post-summary next-slice selection from pass 299
- the status runbook rule that `attention_queue` is descriptor-backed, deterministic, and not an execution queue
- the current helper and proof surfaces in:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
- the retained stack-governance doctrine in:
  - `stack.yaml`
  - `AGENTS.md`

### `expected_artifact`

- one exact bounded broader `attention_queue` contract only
- the contract may freeze only:
  - the top-level queue payload surface:
    - `status`
    - `item_count`
    - `highest_severity`
    - `items`
  - the queue status meanings:
    - `clear` when no operator-review items exist
    - `needs_review` when one or more operator-review items exist
  - the item-shape boundary:
    - every queue item preserves:
      - `kind`
      - `severity`
      - `summary`
    - queue items may also preserve:
      - `source_ref`
      - `details`
  - the queue-ordering rule:
    - items are sorted by `attention_item_sort_key(...)`
    - sorting is severity-first by `SEVERITY_ORDER`
    - equal-severity items then sort by:
      - `kind`
      - `source_ref`
      - `summary`
  - the admitted item-family set only:
    - `registry_error`
    - `registry_drift`
    - `session_needs_resume`
    - `resume_failed`
    - `session_failed`
    - `unknown_tool_surface`
    - `unknown_extension_surface`
    - `blocked_worker`
    - `open_merge_request`
    - `missing_closure_receipt`
    - `closure_receipt_issue`
    - `quarantined_trust_surface`
    - `initiative_open_attention`
    - `initiative_provenance_drift`
    - `proposed_session_provenance_drift`
    - `provenance_alert_overflow`
    - `conversation_action_request`
  - the separation rule:
    - `attention_queue` remains the stricter derived operator-review surface
    - the separate top-level `provenance_alerts` summary remains the fuller provenance-status surface
    - the provenance-derived queue subset may carry fewer provenance items than the top-level summary because the frozen queue cap and overflow handling remain in force

### `failure_boundary`

- the derived operator-review queue starts acting like a real execution queue
- queue semantics begin inspecting transcripts, terminal output, or raw imported evidence instead of descriptor-backed and working-memory-backed surfaces
- the broader queue contract collapses the separate top-level `provenance_alerts` summary into the queue surface
- queue behavior starts implying provenance repair, queue mutation, runtime mutation, or supervisor execution semantics
- new item families, new top-level queue fields, or new status values are implied without a separate admitted packet
- the current deterministic sort and severity-first ordering discipline stops being explicit

### `safe_fallback`

- keep the queue descriptor-backed and deterministic
- preserve only the admitted top-level queue payload surface
- preserve only the admitted item-family set already emitted by the current helper chain
- preserve the already-frozen provenance queue cap and overflow summary
- stop below provenance repair, queue mutation, runtime mutation, and execution semantics

### `owner_boundary`

- ATLAS root owns this broader queue contract freeze, restart projection, and non-claim boundaries
- exact helper or test changes remain a separate next-pass owner-surface question
- owner repos keep mutation truth, deploy truth, and execution truth

### `non_claim_boundary`

- no code or test implementation change
- no queue-budget or queue-ordering change
- no provenance-drift repair, stale-ref cleanup, or missing-file restoration claim
- no queue, registry, session, merge, deployment, or runtime mutation claim
- no transcript, terminal, or hidden-state inference claim
- no execution-queue, dispatch, supervisor-run, or operator-proof claim

## Supporting Dependency Decision

- `none yet`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue semantics beyond provenance alerts owner-surface admission pass 301`

## Marker Decision

- `none`

## Rule

Freeze the broader descriptor-backed `attention_queue` contract before reopening implementation, repair, or execution-facing queue families.
