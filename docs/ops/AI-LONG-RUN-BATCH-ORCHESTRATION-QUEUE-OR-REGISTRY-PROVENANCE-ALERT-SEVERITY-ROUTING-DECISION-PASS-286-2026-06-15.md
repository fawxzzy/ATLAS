# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Severity Routing Decision Pass 286 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned status and attention routing decision`
- Source surfaces:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`

## Objective

Decide whether the pass-284 `provenance_alerts` status surface should remain a quiet preflight summary only or also feed the governed attention queue.

## Decision

- selected routing behavior:
  - route provenance drift into `attention_queue`
  - preserve the top-level `provenance_alerts` summary unchanged
  - treat stale attention refs as `medium`
  - escalate missing initiative or file refs to `high`
- rejected alternative:
  - keep provenance drift status-only and require the operator to cross-check a separate summary block before it can affect queue severity

## Executed Changes

- updated `ops/cortex/render_status.py`
  - `attention_queue(...)` now accepts the already-computed `provenance_alerts` summary
  - added `provenance_attention_items(...)` to translate provenance drift into queue items without mutating queue or registry state
  - initiative or proposed-session drift with unresolved file or initiative refs now routes as `high`
  - stale attention-ref-only drift now routes as `medium`
- updated `tests/test_cortex_render_status_provenance.py`
  - added proof that routed provenance alerts enter the attention queue with the expected severities
  - preserved the pass-284 summary-only proofs

## Proof Command

- `python -m unittest tests.test_cortex_render_status_provenance`
- `python ops/validation/validate_stack.py --ratchet`

## Result

- provenance drift is now visible in both compact status output and the governed attention queue
- the queue still remains read-only: this pass does not mutate queue state, registry state, session state, merge state, or deployment state

## Non-Claim Boundary

- this pass does not repair stale refs automatically
- this pass does not infer hidden transcript state
- this pass does not launch, resume, dispatch, merge, or deploy
- this pass does not widen into owner-repo or protected-surface mutation

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry provenance-alert queue-proof and payload-boundary hardening`
