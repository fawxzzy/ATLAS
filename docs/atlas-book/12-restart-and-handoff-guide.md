# Restart And Handoff Guide

## Purpose

This chapter is the shortest path for resuming the stack from a new chat without rebuilding state from memory.

Use the book and receipts first.

Do not start by inferring current state from stray repo residue, `tmp`, or memory of the last conversation.

## How To Resume From A New Chat

Start in this order:

1. read [Current State](01-current-state.md)
2. read [Approval Gates](04-approval-gates.md)
3. read [Current System Map / Graph](11-system-map-graph.md)
4. read [Lanes And Markers](02-lanes-and-markers.md)
5. read [Receipt Index](05-receipt-index.md)
6. only then choose the next lane

If the task is lane-specific:

- use the book chapter first
- use the lane receipt chain second
- use chat history last

## Required First Checks

Before doing any substantial work:

1. confirm the owner surface
2. confirm whether the lane is docs-only, approval-gated, or open for mutation
3. confirm the current marker posture
4. confirm whether `_stack` owns the execution command
5. confirm whether a newer receipt already resolved the question

## Where The Marker Table Lives

The durable book-local marker table lives in:

- [Lanes And Markers](02-lanes-and-markers.md)

The surrounding lane posture also lives in:

- [Current State](01-current-state.md)
- [Current System Map / Graph](11-system-map-graph.md)

If a new checkpoint changes markers, update the book-local marker table rather than leaving the latest truth stranded in chat.

## How To Choose The Next Lane

Use this decision order:

1. if the requested lane is approval-gated, do not reopen it by implication
2. if a safe non-gated closeout package exists, continue with that package instead of holding globally
3. if the user explicitly approves a gated lane, use the exact bounded approval packet
4. if the question is cross-system, start from ATLAS root
5. if the work is single-repo product work, route into the owner repo

## Approval-Gated Lanes And Exact Approval Phrases

### Fitness Supabase mutation

Approval requirement:

- explicit approval of the exact Pass 1 row subset and `create profile` scope
- historical note: this gate chain is now closed by the 2026-05-25 final closeout receipt and should not be reopened without a new lane-specific reason

### Remote preview / unfurl verification

Approval requirement:

- explicit deploy-backed verification lane opening

### Vercel stale surface deletion

Approval requirement:

- final dependency check plus explicit deletion approval

If the approval is not present, the lane stays closed.

## How To Avoid `tmp` Source Truth

Rules:

- `tmp` is scratch, not durable truth
- runtime truth belongs to the owner repo or governed runtime surface
- receipts belong in ATLAS docs when the consequence is cross-repo

Resume pattern:

1. identify the owner surface
2. identify the durable receipt if cross-repo
3. use `tmp` only as disposable evidence

## How To Avoid Wrong Repo / Wrong Branch Work

Before editing anything:

1. identify the owner repo from the book
2. confirm whether the work belongs in ATLAS root or a repo root
3. confirm current branch and whether the lane is docs-only or implementation
4. confirm deploy authority is `_stack`, not “whoever has the terminal open”

Never start product implementation from ATLAS root just because the conversation started there.

## Branch / Worktree Safety Rules

- branch name is metadata, not truth by itself
- preserve or classify before delete
- do not clean up stale-looking worktrees until retention posture is known
- do not assume a dirty repo means the current task owns those changes
- do not reopen old worktree state as current truth without verification

## Deploy / Update / Proof Safety Rules

- repo-local prep is not deploy approval
- `_stack` owns governed deploy execution
- release proof comes before Discord publication
- no Discord post before proof
- remote preview checks do not reopen themselves just because local proof succeeded

## How To Use The ATLAS Book And Receipts Instead Of Chat Memory

Use this hierarchy:

1. current owner surface
2. current book chapter
3. most recent durable receipt
4. validation output
5. chat history only for nuance that is not yet packaged

If something important only exists in chat, package it into the book or a receipt before treating it as durable truth.

## Expected Status Block Format

When handing off or resuming, use this format:

```text
Done:
- what became durable
- commit if relevant
- validation result

Now:
- current lane posture
- approval gates still in force

Next:
- single best next package
- whether it is docs-only, approval-gated, or open execution
```

For approval-gated lanes, append the exact approval phrase or approval requirement.

## Current Recommended Next Packages

Current best non-gated closeout ladder:

- Branch & Worktree Normalization Final Closeout
- Full Stack Re-sync Final Closeout
- Local Data Gateway _stack packet field validator package 1

If reopening an approved gated lane:

- remote preview / unfurl verification only after explicit deploy-backed lane opening
- external smoke or retained-surface deletion only after an explicit dependency-cleared decision packet
- any DiscordOS runtime/schema/data or transport-aware reopening only after explicit higher-level authorization beyond the closed lookup lane boundary

## Current Fast Resume Summary

At this checkpoint:

- Fitness Supabase profile/data hygiene is closed at `100%`
- DiscordOS bootstrap and scaffold work are complete and `repos/DiscordOS` now exists locally
- DiscordOS separation planning is durable, but runtime migration has not started
- Discord and Music Sesh profile/data concerns remain open only under `Discord OS Infrastructure Separation`
- the ATLAS Book is the primary restart surface
- `_stack` remains deploy authority
- normal stack validation is green in the current working state
- ATLAS root self-lock sequencing has been resolved; preview/unfurl remains approval-gated, the Playbook external `.codex/worktrees/*` stranded-directory subset and the behind-only Playbook smoke branch class are now consumed, no Playbook-only retained-surface execution subset is currently open, the Lifeline stale-merged-checkpoint trio is now consumed, the remaining retained-surface pressure is Playbook stash/manual-review governed retains plus Lifeline evidence/safety/manual-review surfaces, and the DiscordOS lookup-local boundary chain is fully ratcheted shut with both transport-aware and externally-executing openings blocked until higher-level authorization reopens them

## Non-Goals

- no runtime mutation
- no approval-gate bypass
- no use of chat memory as the primary durable system map
