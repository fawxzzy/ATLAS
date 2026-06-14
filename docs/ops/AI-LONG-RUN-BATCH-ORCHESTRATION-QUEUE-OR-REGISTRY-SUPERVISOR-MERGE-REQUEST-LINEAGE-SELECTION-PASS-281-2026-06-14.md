# AI Long-Run Batch Orchestration Queue-Or-Registry Supervisor Merge-Request Lineage Selection Pass 281 - 2026-06-14

- Date: `2026-06-14`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned supervisor lineage selection and residue collapse`
- Source surfaces:
  - `ops/atlas/queue_or_registry_supervisor_merge_request_selection.py`
  - `ops/atlas/test_queue_or_registry_supervisor_merge_request_selection.py`
  - `ops/cortex/_artifacts.py`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_merge_requests.py`
  - `runtime/cortex/supervisor/**`
  - `runtime/atlas/sessions/**/status.snapshot.json`

## Objective

Stop older stack-lock-specific supervisor merge-request duplicates from resurfacing as active open merge requests once a later manifest-linked or completed lineage member already carries the same overlap truth.

## Executed Changes

- added `ops/atlas/queue_or_registry_supervisor_merge_request_selection.py`
  - groups supervisor merge-request files by overlap lineage instead of stack-lock-specific conflict key
  - selects one canonical lineage member per session
  - classifies duplicate lineage members as either superseded residue or retained residue
- added `ops/atlas/test_queue_or_registry_supervisor_merge_request_selection.py`
  - proves a completed manifest-linked lineage member collapses same-lineage duplicates into superseded residue
  - proves unlinked lineages prefer the broadest conflict set as canonical
- updated `ops/cortex/_artifacts.py`
  - merge-request descriptors now carry `identity.lineage_key`
- updated `ops/cortex/render_status.py`
  - merge-request status grouping now uses `lineage_key` first, then falls back to `conflict_key`
- added `tests/test_cortex_render_status_merge_requests.py`
  - proves completed lineage members suppress false duplicate open merge requests
  - proves unlinked lineages still surface one active canonical member

## Live Proof

- `python .\ops\atlas\queue_or_registry_supervisor_merge_request_selection.py`
- current runtime result:
  - `selected_lineage_count: 3`
  - `canonical_completed_lineage_count: 2`
  - `canonical_linked_lineage_count: 1`
  - `active_unlinked_lineage_count: 0`
  - `superseded_residue_ref_count: 2`
- for `session-atlas-session-conflict-20260414T080843Z`
  - one three-member supervisor lineage now resolves to canonical `merge-request-6c16d4cdfc862069`
  - `merge-request-3b94f045fc7cb773` and `merge-request-c814978bffdac481` are now explicit superseded residue
- refreshed status rendering no longer reports a false open merge request for `session-atlas-session-conflict-20260414T080843Z`

## State Sync

- refreshed the active conflict-session descriptor/status surfaces
- rebuilt `runtime/cortex/catalog/memory/working-memory.latest.json` after initiative-provenance updates
- removed the obsolete attention provenance ref for the governed session-conflict proposed-session path after the attention queue legitimately changed

## Test Proof

- `python -m unittest ops.atlas.test_queue_or_registry_supervisor_inventory ops.atlas.test_queue_or_registry_supervisor_merge_request_selection ops.atlas.test_queue_or_registry_execution_home_inventory ops.atlas.test_queue_or_registry_execution_receipt_selection ops.atlas.test_queue_or_registry_execution_receipt_writeback ops.atlas.test_queue_or_registry_runtime_state_inventory ops.atlas.test_queue_or_registry_history tests.test_cortex_render_status_merge_requests tests.test_atlas_marker_knockout_selector tests.test_atlas_resume_session tests.validation.test_validate_stack_execution_receipt_repairs tests.validation.test_validate_stack_resume_contract tests.validation.test_validate_stack_mutable_state_rules`
  - `Ran 41 tests`
  - `OK`
- `python .\ops\validation\validate_stack.py --ratchet`
  - final result: `critical=0 error=0 warning=0 info=0`

## Result

- supervisor duplicate families now collapse on overlap lineage instead of reopening because `stack_lock_digest` changed
- the repeating false-open merge-request surface for `080843` is removed without deleting retained runtime artifacts
- the lane now has both canonical receipt writeback and canonical supervisor lineage collapse in durable proof

## Next Best Move

- tighten validation or attention-surface doctrine around stale supervisor residue so future duplicate lineage files are either explicitly tolerated as residue or elevated only when they widen real conflict truth
