# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance Status Surface Hardening Pass 284 - 2026-06-14

- Date: `2026-06-14`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned status-surface hardening`
- Source surfaces:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `stack.lock.yaml`

## Objective

Expose initiative and proposed-session provenance drift directly in the root status payload so the operator can see this class before running the full validator.

## Executed Changes

- updated `ops/cortex/render_status.py`
  - added `load_current_attention_refs()`
  - added `initiative_provenance_alerts(...)`
  - added `proposed_session_provenance_alerts(...)`
  - added `provenance_alert_summary(...)`
  - `render_status_payload(...)` now emits a top-level `provenance_alerts` block summarizing stale initiative attention refs, missing initiative refs, and stale proposal triggering-attention refs
- added `tests/test_cortex_render_status_provenance.py`
  - proves the status surface reports both initiative and proposed-session provenance drift
  - proves the status surface stays clear when refs resolve cleanly
- refreshed `stack.lock.yaml`
  - kept the pinned working set aligned after the status-surface change

## Test Proof

- `python -m unittest tests.test_cortex_render_status_provenance tests.test_cortex_render_status_merge_requests tests.validation.test_validate_stack_initiative_provenance tests.test_atlas_run_initiative_loop tests.validation.test_validate_stack_execution_receipt_repairs tests.validation.test_validate_stack_resume_contract tests.validation.test_validate_stack_mutable_state_rules`
  - `Ran 20 tests`
  - `OK`
- `python .\ops\validation\validate_stack.py --ratchet`
  - final result: `critical=0 error=0 warning=0 info=0`

## Result

- provenance drift is now visible in the compact root status surface before a dedicated validator run
- the queue-or-registry family now has three aligned layers for this failure mode:
  - sync-path repair in session output refresh
  - validator enforcement
  - operator-visible status surfacing

## Marker Read

- `AI Long-Run Batch Orchestration -> 49%`
- reason:
  - the lane now widened from repair-plus-validation into repair-plus-validation-plus operator-visible status surfacing
  - the marker still stays below broader orchestration adoption, runtime-state expansion, or execution-home widening

## Next Best Move

- decide whether the new `provenance_alerts` surface should feed attention-queue severity directly or remain a quieter status-only preflight signal
