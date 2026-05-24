# Stack Lock Fitness Feedback Effort Points Decision

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow stack-lock repin
Status: accepted

## Decision

Accept the canonical Fitness feedback-card sizing package as current stack truth and repin `stack.lock.yaml`.

Accepted repo:

- `repos/fawxzzy-fitness`

Accepted commit:

- `de775e02ef4bee9a190689494890e43b7ce4a45f`
- `feat: add feedback effort points`

## Reason

This package tightens the canonical Fitness feedback workflow without widening deploy authority or creating a second feedback truth surface.

This commit:

- adds one bounded `effort_points` field to Fitness feedback rows
- keeps Bug and Feature cards on one shared deterministic card contract
- carries the same sizing signal into forum cards, board exports, and reviewed task packets
- preserves Discord forum as display surface and Supabase as bounded source truth

## Stack-Lock Action

`stack.lock.yaml` is repinned only for the canonical Fitness repo entry.

No full lockfile regeneration is required for this package.

## Verification

- Fitness repo-local feedback tests passed
- Fitness repo-local lint, typecheck, and build passed
- ATLAS root validation passed after repin

## What This Decision Does Not Mean

- it does not create a second planning system outside the feedback board/export path
- it does not authorize Discord card edits as engineering truth by themselves
- it does not widen deploy or Vercel authority
