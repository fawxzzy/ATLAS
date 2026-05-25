# Current State

## Snapshot

The stack is currently at a clean docs-first convergence checkpoint.

What is true right now:

- Fitness remains the live app and the live Discord-hosted runtime owner.
- DiscordOS separation is planned and bounded, and the canonical local repo surface now exists.
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

- local repo now exists at `repos/DiscordOS`
- governance scaffold only
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

- Fitness Supabase mutation is approval-gated
- remote preview/unfurl verification is approval-gated
- DiscordOS schema, runtime, and data migration remain unstarted and must stay receipt-bounded
- remaining stale-Vercel cleanup is narrowed to the surviving duplicate-pressure surface, not the deleted Spotify-era projects

## Current Direction

The stack is moving from convergence and cleanup toward explicit lane separation:

1. Fitness app lane
2. Discord work lane
3. ATLAS systems lane

## Current Vercel Pressure

The live Vercel surface is still showing the same structural pressure that justifies accelerating Lifeline work later.

What is true right now:

- `fawxzzy-fitness` remains the highest-churn operational project and is still carrying both product runtime and Discord-hosted runtime responsibilities.
- the two stale Spotify-era Vercel projects were deleted on 2026-05-25 after dependency clearance.
- one known duplicate-pressure Vercel surface still remains and can blur deploy authority:
  - `fitness-deploy-green-panels`
- deployment provenance is still mixed between governed Git-backed deploys and more ad hoc `HEAD` or dirty-state style deploy metadata.
- the recent 30-day Vercel overview is still polluted by the older Discord polling behavior, so short-window views matter more when checking whether the event-driven fix actually helped.

Why this matters:

- Lifeline should later classify every Vercel surface as canonical, stale, scratch, or cutover-target.
- deploy provenance and stale-surface pressure should become visible health signals, not remembered context.
- DiscordOS separation and stale-surface decommission become easier once Lifeline can show service ownership and deploy health clearly.
