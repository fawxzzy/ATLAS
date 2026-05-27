# Current State

## Snapshot

The stack is currently at a clean post-closeout-pass checkpoint.

What is true right now:

- Fitness remains the live app and the live Discord-hosted runtime owner.
- DiscordOS separation is planned, scaffolded, and bounded, and the canonical local repo surface now exists.
- the DiscordOS lookup-local boundary chain is fully ratcheted shut; no further repo-local lookup widening is open without higher-level authorization.
- Fitness Supabase profile/data hygiene is closed as a governed lane at `100%`.
- Discord and Music Sesh profile/data concerns are no longer Fitness hygiene debt and now belong to DiscordOS Infrastructure Separation.
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
- contract docs, typed seams, adapter stubs, and lookup boundary receipts exist
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

- remote preview/unfurl verification is approval-gated
- DiscordOS schema, runtime, and data migration remain unstarted and must stay receipt-bounded
- no helper-Vercel project deletion gate remains open after the 2026-05-25 helper-surface deletion pass
- DiscordOS lookup widening is closed at the owner-repo boundary:
  - transport-aware opening: `no`
  - externally-executing opening: `no`
  - any further DiscordOS lookup widening now requires explicit higher-level authorization
- the Playbook external `.codex/worktrees/*` stranded-directory subset and the behind-only smoke branch class are now consumed:
  - no external Playbook stranded-directory residue remains in that filesystem-only class
  - no behind-only Playbook smoke branch residue remains
  - no Playbook-only retained-surface execution subset is currently open
  - the Lifeline merged-checkpoint trio is now consumed
  - the remaining pressure is Playbook stash/manual-review governed retains plus Lifeline safety/evidence/manual-review surfaces only

## Current Closeout Read

What the latest closeout passes proved:

- branch/worktree pressure is classified and no longer blocked by the Lifeline missing-config class
- `tmp` is no longer acting as production-critical source truth
- the remaining helper Vercel project class is closed; duplicate-surface pressure is no longer centered on live helper projects
- unrelated Fitness residue is classified enough to keep it out of DiscordOS, Supabase, and stack closeout lanes
- Fitness profile-core cleanup is fully closed; no unresolved unknown-profile, never-signed-in auth-only, or legacy automation-mismatch class remains in that lane
- the remaining automation mismatch class is governed no-op and the remaining sign-in-bearing auth-only class is governed heuristic exclusion
- Discord and Music Sesh data concerns are now explicitly transferred to DiscordOS Infrastructure Separation instead of lingering as Fitness cleanup residue
- the DiscordOS lookup-local planning and boundary chain is complete enough to stop widening without an explicit new authorization
- root self-lock sequencing for `stack.lock.yaml#stack` has been resolved by policy, so the remaining pressure is retained-surface cleanup rather than root commitability
- the retained-surface lane is no longer blocked by broad ambiguity, and the Lifeline merged-checkpoint trio `lifeline-main-closeout`, `lifeline-main-closeout-2`, and `lifeline-main-closeout-3` is now consumed

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
- the two helper Fitness Vercel projects were also deleted on 2026-05-25 after a clean dependency check:
  - `fitness-deploy-green-panels`
  - `fitness-prod-rollout-20260525`
- deployment provenance is still mixed between governed Git-backed deploys and more ad hoc `HEAD` or dirty-state style deploy metadata.
- the recent 30-day Vercel overview is still polluted by the older Discord polling behavior, so short-window views matter more when checking whether the event-driven fix actually helped.

Why this matters:

- Lifeline should later classify every Vercel surface as canonical, helper, stale, scratch, or cutover-target.
- deploy provenance and stale-surface pressure should become visible health signals, not remembered context.
- DiscordOS separation and later Vercel health classification become easier once Lifeline can show service ownership and deploy health clearly.
