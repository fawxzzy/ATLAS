# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Queue-Proof And Payload-Boundary Hardening Pass 287 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned queue-proof and payload-boundary hardening`
- Source surfaces:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`

## Objective

Harden the new provenance-to-attention routing so malformed or unsupported payload entries fail closed while actionable provenance drift still reaches the governed attention queue.

## Executed Changes

- updated `ops/cortex/render_status.py`
  - hardened `provenance_attention_items(...)` so initiative and proposed-session alerts with no actionable stale or missing refs are ignored
  - normalized missing `initiative_id` and `session_id` values to bounded `unknown` summaries instead of leaking raw null-like text
- updated `tests/test_cortex_render_status_provenance.py`
  - added direct proof that malformed, empty, and unknown provenance payload entries are ignored
  - preserved the pass-286 queue severity proof and the pass-284 summary proofs

## Proof Command

- `python -m unittest tests.test_cortex_render_status_provenance`
- `python ops/validation/validate_stack.py --ratchet`

## Result

- provenance routing now has an explicit payload boundary instead of assuming every queued provenance item is well formed
- the governed attention queue still accepts actionable provenance drift, but malformed payload shapes do not create synthetic queue noise

## Non-Claim Boundary

- this pass does not widen the queue beyond provenance-alert routing
- this pass does not repair stale refs or missing initiative files
- this pass does not mutate queue state, registry state, session state, merge state, or deployment state
- this pass does not infer hidden transcript state

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry provenance-alert render-status payload integration proof`
