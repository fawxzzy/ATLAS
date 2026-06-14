# AI Long-Run Batch Orchestration Queue-Or-Registry Canonical Execution Receipt Selection Pass 279 - 2026-06-14

- Date: `2026-06-14`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned canonical receipt read-model selection`
- Source surfaces:
  - `ops/atlas/queue_or_registry_execution_receipt_selection.py`
  - `ops/atlas/test_queue_or_registry_execution_receipt_selection.py`
  - `runtime/lifeline/worker-execution/**`
  - `runtime/atlas/sessions/**/session.manifest.json`

## Objective

Convert execution-home receipt truth from raw inventory into one deterministic selection surface when reconciled receipts explicitly supersede manifest-linked primary receipts.

## Executed Changes

- added `ops/atlas/queue_or_registry_execution_receipt_selection.py`
  - selects one canonical execution-home receipt per governed session when possible
  - prefers a reconciled receipt when its `supersedes_receipt_ref` points at the manifest-linked primary receipt
  - otherwise preserves the manifest-linked primary receipt as canonical
  - fails closed if multiple reconciled receipts supersede the same manifest-linked primary receipt
- added `ops/atlas/test_queue_or_registry_execution_receipt_selection.py`
  - proves reconciled canonical selection
  - proves primary receipt fallback when no reconciled variant exists
  - proves multiple-superseder rejection

## Live Proof

- `python .\ops\atlas\queue_or_registry_execution_receipt_selection.py`
- current runtime result:
  - `reconciled_canonical_session_count: 4`
  - `manifest_primary_canonical_session_count: 6`
  - `unresolved_session_count: 2`
- four governed sessions now have explicit canonical reconciled receipts that are stronger than the still-manifest-linked primary receipt

## Test Proof

- `python -m unittest ops.atlas.test_queue_or_registry_execution_receipt_selection`

## Result

- execution-home canonical receipt truth is now replayable instead of operator guesswork
- root can now distinguish:
  - canonical reconciled receipts
  - canonical primary receipts
  - unresolved no-receipt sessions
- this still stops below manifest mutation or receipt rewrite; it is a read-model truth surface only

## Next Best Move

- decide whether to write canonical reconciled receipt refs back into session-manifest truth, or to open a parallel canonical-selection surface for supervisor merge-request families
