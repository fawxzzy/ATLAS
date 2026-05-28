# Restart And Handoff Guide

## Purpose

This chapter is the shortest path for resuming the stack from a new chat without rebuilding state from memory.

Use the book and receipts first.

Do not start by inferring current state from stray repo residue, `tmp`, remembered transcript continuity, or memory of the last conversation.

Rule:
External Context First.

Pattern:
Ephemeral Worker, Durable Substrate.

Failure Mode:
Recursive Context Rot Loop.

## How To Resume From A New Chat

Start in this order:

1. read the lane continuity manifest when one exists
2. read [Current State](01-current-state.md)
3. read [Approval Gates](04-approval-gates.md)
4. read [Current System Map / Graph](11-system-map-graph.md)
5. read [Lanes And Markers](02-lanes-and-markers.md)
6. read [Receipt Index](05-receipt-index.md)
7. only then choose the next lane

If the task is lane-specific:

- use the continuity manifest first when one exists
- use the current book chapter next
- use the governing receipt chain next
- use owner-repo truth-owner surfaces next
- use verification/adoption surfaces next
- use chat history last and only for unpromoted nuance

If durable surfaces disagree with chat recap:

- trust the durable surfaces
- repair the docs if needed
- do not treat the chat recap as authority

If no continuity manifest exists yet:

- prefer the receipt index and current system map over remembered package ordering
- prefer promoted notes over copied recap blocks
- package any critical chat-only fact into a receipt or governed note before using it as restart truth

If a lane claims `manifest-backed` continuity:

- the lane must have an active ATLAS-root continuity manifest
- active continuity manifests currently live in `docs/memory/initiatives/continuity-manifest-*.json`
- that manifest must point to the current decisive receipt
- that manifest must point to owner truth and verification/adoption surfaces rather than copying them
- that manifest must still be fresh enough that its checkpoint, marker posture, blocked work, and next package ladder match the current durable lane state
- if those conditions are not true, treat the lane as receipt-backed or operator-stitched instead

If a continuity manifest exists but is stale:

- treat it as `manifest-present only`, not fully `manifest-backed`
- use it as a hint to the lane surface, then fall through to the current decisive receipt chain
- do not trust it over newer marker or receipt surfaces

If a continuity manifest includes explicit freshness fields:

- use `freshness_state` and `freshness_checked_receipt` as the first freshness cue
- if those fields conflict with newer marker or receipt surfaces, trust the newer durable surfaces and refresh the manifest

## Required First Checks

Before doing any substantial work:

1. confirm the owner surface
2. confirm whether the lane is docs-only, approval-gated, or open for mutation
3. confirm whether the requested package is already durable
4. confirm whether the work is a proof/inventory pass or a ratchet pass
5. confirm the current marker posture from the active front-page marker set first
6. confirm whether a newer receipt already resolved the question
7. confirm whether `_stack` owns the execution command

Mandatory prompt preflight:

- is this package already durable
- is this root-owned or owner-repo-owned
- is this a proof/inventory pass, ratchet pass, or implementation pass
- which canonical shared files will be touched
- what must remain explicitly blocked after this pass

## Where The Marker Table Lives

The durable book-local marker table lives in:

- [Lanes And Markers](02-lanes-and-markers.md)

The surrounding lane posture also lives in:

- [Current State](01-current-state.md)
- [Current System Map / Graph](11-system-map-graph.md)

If a new checkpoint changes markers, update the book-local marker table rather than leaving the latest truth stranded in chat.

Marker-system hygiene rule:

- read `Active Cluster Read` first
- read the capped `Active Front-Page Marker Table` second
- use `Supporting Open Markers` only for lane-specific follow-up
- use `Closed / Locked Ratchets` only for historical boundary or restart context

Do not spend first-scan attention on closed ratchets or lower-signal supporting markers when the question is about the next active lane.

## Fast Safe Cadence

Default cadence:

1. cluster related proof or inventory passes first
2. stop and decide whether operator reality materially changed
3. run one ratchet only if that answer is yes
4. refresh shared marker or restart surfaces only when the ratchet or proof changed canonical read state

Do not default to:

- one micro receipt
- one micro ratchet
- one micro shared-surface refresh

when the underlying operator decision did not change.

## Canonical File Collision Policy

Treat these as serialized shared root spines:

- [02-lanes-and-markers.md](02-lanes-and-markers.md)
- [05-receipt-index.md](05-receipt-index.md)
- [12-restart-and-handoff-guide.md](12-restart-and-handoff-guide.md)
- [13-vision-and-endgames.md](13-vision-and-endgames.md)
- [PLAYBOOK_NOTES.md](../PLAYBOOK_NOTES.md)

Default operating split:

- one root writer
- one owner-repo writer
- one read-only scout

Rules:

- do not let two active root-writing passes touch the same shared spine at once
- if a receipt can land without an immediate shared-spine rewrite, prefer batching that rewrite with the next related ratchet or hygiene pass
- do not let a read-only scout quietly become a writer without reclassifying the lane

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

1. lane continuity manifest when one exists
2. current book chapter
3. most recent durable receipt chain
4. current owner surface
5. verification/adoption surface
6. validation output
7. chat history only for nuance that is not yet packaged

If something important only exists in chat, package it into the book or a receipt before treating it as durable truth.

Interpretation:

- GPT/Codex workers are ephemeral reasoning surfaces
- ATLAS and owner repos are the durable continuity substrate
- continuity manifests are the compact retrieval map that should point workers to the right durable surfaces before chat recap is trusted
- a restart is healthy only when the lane can be reconstructed from those external artifacts

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

Current best non-gated docs / control-plane ladder:

- Atlas-owned Repo Naming stream execution-packet preflight pass 1
- Local Data Gateway workflow adoption expansion pass 2
- targeted marker/book maintenance only when it materially improves operator read speed or restart truth

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
- the marker system is now intentionally split into active front-page markers, supporting open markers, and closed/locked ratchets so restart scans can prioritize active steering signals first
- continuity manifests, retrieval-surface taxonomy, and prompt-pack normalization are now durable enough that transcript recap should be treated as optional nuance rather than a restart substrate
- seeded continuity manifests now exist for Durable Context Externalization, Local Data Gateway, Discord OS Feedback Workflow Canonicalization, Discord OS Infrastructure Separation, Branch & Worktree Normalization, and Full Stack Re-sync, Clean & Closeout under `docs/memory/initiatives/continuity-manifest-*.json`
- the current seeded six-manifest set has now also passed a second actual refresh cycle after breadth expansion, so manifest-backed routing is broader and more operationally real than the earlier first-adoption posture
- seeded manifests must still be checked for freshness; manifest presence alone is not enough to claim the lane is still fully manifest-backed
- ATLAS root self-lock sequencing has been resolved; preview/unfurl remains approval-gated, the Playbook external `.codex/worktrees/*` stranded-directory subset and the behind-only Playbook smoke branch class are now consumed, no Playbook-only retained-surface execution subset is currently open, the Lifeline stale-merged-checkpoint trio is now consumed, the remaining retained-surface pressure is governed-retain only, `Branch & Worktree Normalization` is now closed at `100%`, `Full Stack Re-sync, Clean & Closeout` is now closed at `100%`, and the DiscordOS lookup-local boundary chain is fully ratcheted shut with both transport-aware and externally-executing openings blocked until higher-level authorization reopens them

## Non-Goals

- no runtime mutation
- no approval-gate bypass
- no use of chat memory as the primary durable system map
