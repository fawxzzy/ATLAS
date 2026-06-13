# _Stack Readiness Stack Queue-Or-Registry Live Directory-Read Follow-On First-Implementation Prompt-Pack And Handoff Contract Pass 126 - 2026-06-13

- Date: `2026-06-13`
- Lane: `_stack Readiness stack queue-or-registry live directory-read follow-on first-implementation prompt-pack and handoff contract pass 126`
- Mode: `docs-only root-bounded prompt-pack contract`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/_STACK-READINESS-STACK-QUEUE-OR-REGISTRY-LIVE-DIRECTORY-READ-FOLLOW-ON-FIRST-IMPLEMENTATION-SLICE-AND-PROOF-MATRIX-ADMISSION-PASS-125-2026-06-13.md`
  - `repos/_stack/scripts/queue-or-registry-follow-on.mjs`
  - `repos/_stack/package.json`
  - `repos/_stack/README.md`
- Control-plane checkpoint: `main@5065766d`

## Objective

Freeze the exact worker packet for the first `_stack` implementation slice.

## Worker Packet

### Objective

- implement one read-only helper for the admitted directory-read seam only

### Files to modify

- `repos/_stack/scripts/queue-or-registry-live-directory-read-follow-on.mjs`
- `repos/_stack/scripts/queue-or-registry-live-directory-read-follow-on.test.mjs`
- `repos/_stack/package.json`
- `repos/_stack/README.md`

### Verification

- `pnpm run stack:queue-or-registry:live-directory-read-follow-on:test`
- `pnpm run codex:stack:verify`

### Guardrails

- no writes outside `_stack`
- no queue or registry mutation
- no live-runtime proof claim
- no front-book edits

## Exact Next Package

- `_Stack Readiness stack queue-or-registry live directory-read follow-on implementation-readiness closeout and worker-routing pass 127`

## Marker Decision

- `none`

## Rule

Freeze the worker packet before opening execution.
