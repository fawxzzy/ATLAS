# AI Long-Run Batch Orchestration Queue-Or-Registry Post-Live-Directory-Read Follow-On Next-Slice Selection Pass 128 - 2026-06-13

- Date: `2026-06-13`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded next-slice selection`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/_STACK-READINESS-STACK-QUEUE-OR-REGISTRY-LIVE-DIRECTORY-READ-FOLLOW-ON-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-13.md`
  - `docs/ops/ROOT-SIDE-STACK-LOCK-REFRESH-AFTER-_STACK-QUEUE-OR-REGISTRY-LIVE-DIRECTORY-READ-FOLLOW-ON-FIRST-IMPLEMENTATION-2026-06-13.md`
  - `repos/_stack/scripts/queue-or-registry-live-directory-read-follow-on.mjs`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@5065766d`

## Objective

Choose the strongest remaining bounded post-worker next slice now that the directory-read seam is implemented and lock truth is refreshed.

## Candidate Comparison

The strongest honest remaining next-slice candidates are:

1. `broader queue or registry execution behavior`
2. queue-home-only or registry-home-only mutation semantics

## Selection

Select exactly one next slice:

- `broader queue or registry execution behavior`

## Why `Broader Queue Or Registry Execution Behavior` Wins

- the retained-state read family is now exhausted across direct-json and directory branches
- the next real open seam is the execution-behavior boundary that still sits above mutation, queue-drop emission, and worker-launch claims
- choosing a narrower queue-home-only or registry-home-only mutation packet now would skip the still-unfrozen shared execution-behavior contract

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader execution behavior contract-freeze pass 129`

## Marker Decision

- `none`

## Rule

Exhaust retained-state read seams before reopening mutation or worker-behavior questions.
