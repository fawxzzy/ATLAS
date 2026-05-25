# Current State

## Snapshot

The stack is currently at a clean docs-first convergence checkpoint.

What is true right now:

- Fitness remains the live app and the live Discord-hosted runtime owner.
- DiscordOS separation is planned and bounded, but not implemented.
- Fitness Supabase cleanup is fully planned and approval-gated, but not mutated.
- `_stack` remains the governed deploy authority for approved app lanes.
- ATLAS root remains the coordination, receipt, and marker layer.
- Playbook remains the reusable governance and doctrine owner.

## Canonical Source Truth By Surface

### Fitness

- product runtime and UX
- QA/LLEL and local/mobile proof
- Fitness auth and profiles
- Fitness release proof
- current live Discord runtime hosting

### DiscordOS

- future Discord-first runtime owner
- future feedback/update/moderation/Music Sesh runtime owner
- future DiscordOS Supabase owner for Discord-owned tables

Current status:

- planned only
- no local repo yet
- no code moved
- no runtime cutover

### `_stack`

- governed deploy authority
- shared operator execution
- deploy wrappers and preflights

### ATLAS root

- markers and lane state
- cross-repo receipts
- truth-map and convergence mapping
- stack validation and coordination posture

### Playbook

- reusable governance doctrine
- rules, patterns, and failure-mode promotion
- contract semantics

## Current Paused Or Gated Work

- DiscordOS bootstrap is approval-gated
- Fitness Supabase mutation is approval-gated
- remote preview/unfurl verification is approval-gated
- stale Vercel surface deletion is still blocked on final dependency check and explicit approval

## Current Direction

The stack is moving from convergence and cleanup toward explicit lane separation:

1. Fitness app lane
2. Discord work lane
3. ATLAS systems lane
