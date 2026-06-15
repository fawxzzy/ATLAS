# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Queue Signal Budget Decision Pass 289 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned queue signal budget decision`
- Source surfaces:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`

## Objective

Decide how many provenance-alert-derived signals may enter `attention_queue` before the queue starts summarizing overflow instead of emitting every provenance item individually.

## Decision

- selected routing behavior:
  - cap provenance-derived queue items at `3`
  - preserve severity-first ordering inside the provenance-derived subset before the cap is applied
  - surface overflow as one `provenance_alert_overflow` queue item
  - preserve the separate `provenance_alerts` status payload instead of expanding queue output to carry every alert
- rejected alternative:
  - emit every provenance alert item-by-item and let bursty drift spam the governed attention queue

## Executed Changes

- updated `ops/cortex/render_status.py`
  - introduced `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP = 3`
  - extracted a shared `attention_item_sort_key(...)` so provenance-derived items and the final queue use the same severity-first ordering
  - changed `provenance_attention_items(...)` to keep only the highest-priority three provenance items and append one overflow summary item when more alerts exist
- updated `tests/test_cortex_render_status_provenance.py`
  - added direct proof that five actionable provenance alerts collapse into three routed items plus one overflow summary
  - proved that the overflow summary reports suppressed count, cap, total alert count, and highest suppressed severity

## Proof Command

- `python -m unittest tests.test_cortex_render_status_provenance`
- `python ops/validation/validate_stack.py --ratchet`

## Result

- provenance drift remains operator-visible without allowing a large stale-ref burst to dominate the governed attention queue
- the budget changes queue item count only; the severity contract for actionable provenance drift remains intact

## Non-Claim Boundary

- this pass does not widen the top-level `provenance_alerts` payload contract
- this pass does not repair stale refs or missing initiative files
- this pass does not mutate queue state, registry state, session state, merge state, or deployment state
- this pass does not infer hidden transcript state

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry provenance-alert queue signal budget integration proof`
