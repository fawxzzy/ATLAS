# Stack Lock Fitness Release-Script Authority Clarification Decision

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: narrow stack-lock repin
Status: accepted

## Decision

Accept the canonical Fitness docs-only clarification commit as current stack truth and repin `stack.lock.yaml`.

Accepted repo:

- `repos/fawxzzy-fitness`

Accepted commit:

- `8c94933de07f87b9abb9f0cf174b0229b5be91da`
- `docs: clarify fitness deploy authority`

## Reason

The repo-local clarification package is in scope for the stack because it tightens deploy-authority doctrine in the canonical Fitness repo without changing runtime behavior.

This commit:

- reduces deploy-authority ambiguity
- keeps `_stack` as the only approved Fitness preview and production deploy path
- does not alter Vercel settings, deploy mechanics, or product behavior

## Stack-Lock Action

`stack.lock.yaml` is repinned only for the canonical Fitness repo entry.

No full lockfile regeneration is required for this package.

## Verification

- Fitness repo-local verification passed before repin
- ATLAS root validation passed after repin

## What This Decision Does Not Mean

- it does not authorize direct repo-local Vercel deploys
- it does not rename Fitness release scripts
- it does not change `_stack` deploy mechanics
