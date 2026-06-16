# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Top-Level Summary Boundary First-Implementation Admission Pass 296 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-CONTRACT-FREEZE-PASS-293-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-294-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-TOP-LEVEL-SUMMARY-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-295-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-RENDER-STATUS-PAYLOAD-INTEGRATION-PROOF-PASS-288-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@04187a36`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned top-level `provenance_alerts` summary boundary plus one proof matrix for validating that slice without crossing the no-queue-budget-change, no-provenance-repair, no-runtime-mutation, and no-supervisor/operator-proof boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one explicit current-attention-ref load gate
2. one initiative provenance-alert helper invocation that preserves actionable initiative drift items only
3. one proposed-session provenance-alert helper invocation that preserves actionable proposed-session drift items only
4. one bounded initiative-first then proposal-second item concatenation layer
5. one top-level status-and-count renderer
6. one fail-closed unavailable fallback with no queue-budget, repair, or mutation widening

The first-slice summary renderer may distinguish only:

- `unavailable` when current attention refs cannot be loaded
- `clear` when no actionable initiative or proposed-session drift items remain
- `drift_detected` when one or more actionable initiative or proposed-session drift items remain

## Exact Preserved Payload Surface

The worker must preserve only:

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

- `initiative_item_count` counts actionable initiative drift items only
- `proposal_item_count` counts actionable proposed-session drift items only
- `item_count` is the total of those two actionable groups
- `items` preserves initiative items first and proposed-session items second
- `items` is bounded to `items[:10]`

## Exact Mandatory Proof Cases

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

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry provenance-alert top-level summary boundary prompt-pack and handoff contract pass 297`

## Marker Decision

- `none`
