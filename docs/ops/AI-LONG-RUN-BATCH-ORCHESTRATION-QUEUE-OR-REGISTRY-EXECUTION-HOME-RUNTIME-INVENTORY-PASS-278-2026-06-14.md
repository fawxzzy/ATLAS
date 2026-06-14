# AI Long-Run Batch Orchestration Queue-Or-Registry Execution-Home Runtime Inventory Pass 278 - 2026-06-14

- Date: `2026-06-14`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned execution-home read-only inventory`
- Source surfaces:
  - `ops/atlas/queue_or_registry_execution_home_inventory.py`
  - `ops/atlas/test_queue_or_registry_execution_home_inventory.py`
  - `runtime/lifeline/worker-execution/**`
  - `runtime/atlas/sessions/**/session.manifest.json`

## Objective

Open the execution-home seam as one replayable root-owned inventory surface over real Lifeline receipt runtime and its session-manifest linkage.

## Executed Changes

- added `ops/atlas/queue_or_registry_execution_home_inventory.py`
  - inventories per-session execution-home receipt artifacts
  - compares execution-home receipt files against manifest `execution_receipt_ref` and `close_receipt_refs`
  - counts linked, missing, and unlinked receipt refs
  - counts reconciled receipt variants carrying `supersedes_receipt_ref`
  - fails closed on malformed receipt contract surfaces
- added `ops/atlas/test_queue_or_registry_execution_home_inventory.py`
  - proves linked plus reconciled receipt counting
  - proves missing manifest-link reporting
  - proves contract-version rejection

## Live Proof

- `python .\ops\atlas\queue_or_registry_execution_home_inventory.py`
- current runtime result:
  - `assignment_root_count: 11`
  - `total_receipt_file_count: 14`
  - `linked_receipt_ref_count: 10`
  - `unlinked_receipt_ref_count: 4`
  - `reconciled_receipt_file_count: 4`
  - `sessions_with_reconciled_receipts: 4`

## Test Proof

- `python -m unittest ops.atlas.test_queue_or_registry_execution_home_inventory`

## Result

- execution-home runtime truth is now replayable instead of inferred from one-off receipt inspection
- root can now prove which session families have extra reconciled receipt artifacts without yet claiming canonical supersession or manifest write-back

## Next Best Move

- select canonical execution-home receipt truth where reconciled receipts explicitly supersede the manifest-linked primary receipt
