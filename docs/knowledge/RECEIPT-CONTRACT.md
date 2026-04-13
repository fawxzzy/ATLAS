# Knowledge Receipt Contract

This document defines the receipt contract for the stack-owned knowledge pipeline.

## Receipt Lane

Receipts are written under:

- `runtime/receipts/knowledge/<archive_id>/`

Each lane stores timestamped receipts plus `latest.json`.

## Contract

- `receipt_version`: `atlas.knowledge.receipt.v1`
- `pipeline_version`: `atlas.knowledge.pipeline.v2`
- `archive_id`
- `action`
- `recorded_at`
- `promotion_blocked`
- `promotion_block_reason`
- `paths`
- `inputs`
- `digests`
- `no_execute_guarantee`
- `evaluation`
- `promotion`
- `runtime_outputs`
- `validation_results`
- `tooling`

## Receipt Digests

Each receipt records digests for the current pipeline state when present:

- manifest JSON
- evaluation JSON
- runtime catalog JSON
- promotion doc markdown
- validation result payload when validation data was attached

`inputs.artifact_digests` continues to carry the raw archive or raw tree digests, and `inputs.extracted_snapshot_digest` carries the extracted snapshot digest.

## Tooling Metadata

Each receipt records the current operator entrypoint and shared pipeline metadata:

- entrypoint path
- entrypoint digest
- `_pipeline.py` path
- `_pipeline.py` digest
- Python version

## Purpose

The receipt is the durable machine-readable handoff for knowledge-pipeline state. Console output is not the contract.
The receipt shape is intended to be provenance-ready, but this pass does not add signing or external attestation.

## Actions

Current receipt actions may include:

- `import`
- `evaluate`
- `promote`
- `normalize`
- `backfill-v2`
