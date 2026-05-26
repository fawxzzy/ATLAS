# Current State

## Snapshot

The stack is currently at a clean post-closeout-pass checkpoint.

What is true right now:

- Fitness remains the live app and the live Discord-hosted runtime owner.
- DiscordOS separation is planned, scaffolded, and bounded, and the canonical local repo surface now exists.
- Fitness Supabase cleanup is fully planned and approval-gated, but not mutated.
- `_stack` remains the governed deploy authority for approved app lanes.
- ATLAS root remains the coordination, receipt, and marker layer.
- Playbook remains the reusable governance and doctrine owner.
- normal stack validation is green in the current working state.
- `--allow-missing-locked-repos` is no longer needed for current validation.

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
- contract docs, typed seams, and adapter stubs exist
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
- remaining helper-Vercel cleanup is narrowed to two retain-temporarily helper surfaces, not the deleted Spotify-era projects

## Current Closeout Read

What the latest closeout passes proved:

- branch/worktree pressure is classified and no longer blocked by the Lifeline missing-config class
- `tmp` is no longer acting as production-critical source truth
- helper Vercel pressure is narrowed to recent retain-temporarily helper projects
- unrelated Fitness residue is classified enough to keep it out of DiscordOS, Supabase, and stack closeout lanes
- root self-lock sequencing for `stack.lock.yaml#stack` has been resolved by policy, so the remaining pressure is retained-surface cleanup rather than root commitability

## Current Direction

The stack is moving from convergence and cleanup toward explicit lane separation:

1. Fitness app lane
2. Discord work lane
3. ATLAS systems lane

## Current Vercel Pressure

The live Vercel surface is materially cleaner than the earlier convergence checkpoint, but not fully closed.

What is true right now:

- `fawxzzy-fitness` remains the highest-churn operational project and is still carrying both product runtime and Discord-hosted runtime responsibilities.
- the two stale Spotify-era Vercel projects were deleted on 2026-05-25 after dependency clearance.
- two known helper surfaces still remain and can blur deploy authority if left ungoverned:
  - `fitness-deploy-green-panels`
  - `fitness-prod-rollout-20260525`
- deployment provenance is still mixed between governed Git-backed deploys and more ad hoc `HEAD` or dirty-state style deploy metadata.
- the recent 30-day Vercel overview is still polluted by the older Discord polling behavior, so short-window views matter more when checking whether the event-driven fix actually helped.

Why this matters:

- Lifeline should later classify every Vercel surface as canonical, helper, stale, scratch, or cutover-target.
- deploy provenance and stale-surface pressure should become visible health signals, not remembered context.
- DiscordOS separation and helper-surface decommission become easier once Lifeline can show service ownership and deploy health clearly.
