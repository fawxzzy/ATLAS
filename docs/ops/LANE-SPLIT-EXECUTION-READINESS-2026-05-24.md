# Lane Split Execution Readiness

## Purpose

This checklist turns the post-convergence lane split from a planning model into an actionable reopen checklist.

This is still docs-only.

It does not reopen any lane by implication.

## Goal

Make the future three-lane model executable with:

- clear start conditions
- required first checks
- required receipts
- approval-gated blockers
- forbidden shortcuts
- explicit first safe packages

## Three-Lane Execution Model

The stack should reopen through three major lanes:

1. Fitness app lane
2. Discord work lane
3. ATLAS systems lane

Each lane must reopen by owner boundary, not by convenience.

## 1. Fitness App Lane Start Conditions

The Fitness app lane may start when:

- the work is product, UX, QA/LLEL, local/mobile proof, release prep, or explicitly approved Fitness data hygiene
- the work belongs in `repos/fawxzzy-fitness`
- no DiscordOS runtime extraction is being smuggled in under a product label
- any data mutation scope is already bounded by approval receipts

### Required first checks

1. confirm the task belongs in Fitness product/runtime truth
2. confirm whether the task is normal product work or approval-gated data hygiene
3. confirm deploy authority remains `_stack`
4. confirm no newer Fitness receipt already resolved the task

### Required receipts

- repo-local proof or release evidence where applicable
- Fitness Supabase approval packet if the task is approved data hygiene
- ATLAS receipt only if the work changes cross-repo state or markers

### Approval-gated blockers

- Fitness Supabase mutation remains blocked without explicit approval
- remote preview/unfurl work remains blocked without explicit lane opening

### First safe package

- explicit Fitness product/QA/LLEL package
or
- approved Fitness Supabase Mutation Pass 1 only

## 2. Discord Work Lane Start Conditions

The Discord work lane may start when:

- the work is Discord runtime, feedback/update/moderation workflow, Music Sesh, or DiscordOS-owned infrastructure
- the work is treated as Discord-owned scope, not hidden Fitness overflow
- contract seams with Fitness are respected
- any bootstrap or migration step has explicit approval where required

### Required first checks

1. confirm the work belongs to future DiscordOS ownership
2. confirm whether the task is docs-only, bootstrap, schema, or runtime cutover work
3. confirm whether the exact approval gate has been opened
4. confirm no newer DiscordOS separation receipt already superseded the plan

### Required receipts

- DiscordOS inventory / contract / env-runtime / schema / cutover receipts as prerequisites
- DiscordOS bootstrap approval receipt if bootstrap is being reopened
- later cutover receipts only when those lanes explicitly open

### Approval-gated blockers

- DiscordOS repo bootstrap remains blocked without the exact approval phrase
- no schema or runtime cutover opens by implication from planning

### First safe package

- approved DiscordOS repo bootstrap only into `repos/DiscordOS`, no code migration

## 3. ATLAS Systems Lane Start Conditions

The ATLAS systems lane may start when:

- the work is governance, validation, markers, receipts, book work, `_stack`, Playbook-facing routing, Cortex context, or systems-planning work
- the work belongs at ATLAS root instead of an owner repo
- no owner-repo implementation is being done from root by convenience

### Required first checks

1. confirm the work is stack-coordination or governance work
2. confirm the owner repo is not the correct execution surface
3. confirm whether the work changes markers or approval-gate posture
4. confirm whether a newer book chapter or receipt already answers the question

### Required receipts

- ATLAS receipt or book update when durable stack posture changes
- validation receipt after substantial docs/policy work

### Approval-gated blockers

- ATLAS systems work itself is not blocked for docs-only continuation
- but it must not bypass repo, data, or service approval gates owned elsewhere

### First safe package

- additional ATLAS governance, doctrine-routing, or `_stack` design work

## Required First Checks Per Lane

Across every lane, the minimum reopen checks are:

1. confirm owner surface
2. confirm whether the lane is docs-only, open execution, or approval-gated
3. confirm the current marker posture
4. confirm the last durable receipt in that lane
5. confirm whether `_stack` or another governed owner controls execution

## Required Receipts Per Lane

### Fitness app lane

- repo-local proof or release receipt
- ATLAS receipt only for cross-repo consequence

### Discord work lane

- DiscordOS planning chain receipts first
- bootstrap / schema / cutover receipts only as the lane reopens in bounded steps

### ATLAS systems lane

- ATLAS receipt or book update for durable state changes
- validation receipt after significant docs/governance changes

## Approval-Gated Blockers Per Lane

### Fitness app lane

- Fitness Supabase mutation approval
- remote preview/unfurl verification approval

### Discord work lane

- DiscordOS bootstrap approval
- later schema, runtime, and cutover approvals as those lanes open

### ATLAS systems lane

- no direct blockers for docs-only work
- may not bypass another lane’s gate

## Forbidden Cross-Lane Shortcuts

- do not do DiscordOS platform work inside Fitness by default
- do not treat Discord board state as deploy or repo truth
- do not treat ATLAS root as a product implementation surface
- do not bypass `_stack` deploy authority
- do not reopen approval-gated lanes because “the prep is done anyway”
- do not turn shared seams into hidden coupling again

## Shared Contract Handoff Rules

- Fitness proof stays upstream of Discord publication
- Discord consumes proof; it does not create proof
- Fitness auth/profile truth remains Fitness-owned
- Discord runtime state moves later only through explicit contracts and cutover planning
- ATLAS records cross-repo consequence, not owner-repo runtime truth
- Playbook promotes reusable doctrine only after receipt-backed evidence

## Marker Update Rules

When a lane completes a durable package:

1. update the book-local marker table if the checkpoint changes marker truth
2. record the lane movement in the final status block
3. do not inflate marker progress for planning that does not materially reduce ambiguity
4. keep approval-gated lanes flat unless the gate itself or its readiness materially changed

## First Safe Package Per Lane

### Fitness app lane

- bounded Fitness product/QA/LLEL package
or
- approved Fitness Supabase Mutation Pass 1 only

### Discord work lane

- approved DiscordOS repo bootstrap only

### ATLAS systems lane

- `_stack` or Lifeline-facing command/health design
or
- doctrine promotion / governance continuation

## Execution Readiness Summary

The split is execution-ready only when:

- the owner lane can be chosen quickly from the book
- the approval gates are explicit
- the first package in each lane is bounded
- cross-lane handoffs are contract-based
- markers update from durable state, not memory

## Non-Goals

- no repo mutation
- no data mutation
- no Vercel mutation
- no Discord runtime cutover
- no gate bypass
