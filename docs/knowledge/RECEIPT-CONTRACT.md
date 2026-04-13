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
- `paths`
- `inputs`
- `no_execute_guarantee`
- `evaluation`
- `promotion`
- `runtime_outputs`
- `validation_results`

## Purpose

The receipt is the durable machine-readable handoff for knowledge-pipeline state. Console output is not the contract.

## Actions

Current receipt actions may include:

- `import`
- `evaluate`
- `promote`
- `normalize`
- `backfill-v2`
