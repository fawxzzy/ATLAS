# Stack Lock Fitness Feedback Card Detail Alignment Decision

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow stack-lock repin
Status: accepted

## Decision

Accept the canonical Fitness feedback-card detail-alignment package as current stack truth and repin `stack.lock.yaml`.

Accepted repo:

- `repos/fawxzzy-fitness`

Accepted commit:

- `a89a807d1206f2a70905dcf6b3b32bbc6e650336`
- `fix: align feedback feature card detail`

## Reason

This package closes a real workflow drift inside the governed feedback system.

It does not create a new workflow. It makes the existing one consistent by ensuring scoped feature detail survives into:

- the bounded Supabase row
- the Discord forum starter card
- the board export
- reviewed task packets

## Stack-Lock Action

`stack.lock.yaml` is repinned only for the canonical Fitness repo entry.

No full lockfile regeneration is required for this package.

## Verification

- Fitness targeted feedback tests passed
- Fitness repo verify passed
- live `37183bb9` forum starter post was fetched and confirmed after sync
- ATLAS root validation passed after repin

## What This Decision Does Not Mean

- it does not make Discord the source of truth
- it does not authorize chat-only scope changes without bounded-row updates
- it does not widen deploy, Vercel, or Discord publication authority
- it does not claim every feature card can exceed Discord body limits; it preserves as much scoped detail as the governed card budget allows
