# Discord OS Repo Bootstrap Plan

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: docs-only planning
Status: first DiscordOS repo bootstrap plan recorded

## Goal

Plan the canonical local and remote DiscordOS repo bootstrap before any code movement, Supabase migration, Vercel cutover, or bot-runtime cutover begins.

This pass does not:

- create `repos/DiscordOS`
- clone or initialize a repo
- move code
- mutate Supabase
- mutate Vercel
- restart the bot
- post to Discord
- pull env
- print secrets

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`
- `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`

## Target

- GitHub repo: `https://github.com/fawxzzy/DiscordOS.git`
- local canonical path: `repos/DiscordOS`
- Supabase project: `DiscordOS`
- Supabase ref: `nwexsktuuenfdegzrbut`

## Governing Rules

- `repos/DiscordOS` becomes the canonical source surface for Discord-first runtime code only after bootstrap is complete.
- Fitness remains canonical for Fitness-owned account, auth, profile, verification-issuance, and release-proof surfaces.
- No repo bootstrap step may imply code movement, env splitting, schema creation, or runtime cutover by itself.
- Root `secrets/**` remains the canonical local secrets lane; DiscordOS bootstrap must not reintroduce repo-root `.env*` usage as the long-term pattern.
- Bootstrap should minimize hidden coupling by forcing contract seams to exist before extraction packages begin.

## 1. Local Clone / Bootstrap Sequence

The future DiscordOS repo bootstrap should happen in one governed sequence.

### Step 1: verify target path is unused or intentionally empty

Check:

- `repos/DiscordOS` does not already contain unrelated residue
- no existing local repo is silently being repurposed

Rule:

- do not bootstrap over an existing active repo without explicit owner confirmation

### Step 2: verify remote identity before clone/init

Confirm:

- remote URL is `https://github.com/fawxzzy/DiscordOS.git`
- default branch is expected to be `main`
- remote is the intended canonical DiscordOS owner surface

Rule:

- remote verification happens before any local source surface is created

### Step 3: create local canonical repo surface

Future implementation lane should:

- clone or initialize into `repos/DiscordOS`
- set `origin` to `https://github.com/fawxzzy/DiscordOS.git`
- establish `main` as the canonical branch

Rule:

- bootstrap should produce one clean local repo, not a temporary scratch extraction area

### Step 4: land repo-local governance before code movement

Before moving any code, the repo should have:

- repo-local `AGENTS.md`
- repo `README` or equivalent orientation doc
- initial docs/ops surface
- verify command contract
- environment policy notes

Rule:

- governance lands before extraction

## 2. Remote Identity Verification

Before repo bootstrap is treated as valid:

- remote URL must exactly match `https://github.com/fawxzzy/DiscordOS.git`
- local repo root must resolve to `repos/DiscordOS`
- branch default must be `main`
- the repo must not be accidentally linked to Fitness, `_stack`, or another app surface

### Verification checklist

- Git remote inspection
- current branch inspection
- empty or intended baseline tree inspection
- no accidental Vercel link file imported from another repo
- no copied `.env*` residue

## 3. Initial Repo Structure

The initial DiscordOS repo should start narrow and governance-first.

### Minimum bootstrap structure

```txt
repos/DiscordOS/
  AGENTS.md
  README.md
  docs/
    ops/
  scripts/
  src/
  package.json
```

### Recommended early directories

- `src/lib/discord/`
- `src/lib/contracts/`
- `src/lib/runtime/`
- `src/app/api/` only if DiscordOS runtime will mirror the current route-based host shape
- `scripts/` for:
  - worker/runtime helpers
  - sync/export utilities
  - bootstrap/doctor commands

### Structure rule

- start with the runtime and contract seams that are known to move
- do not copy Fitness product surfaces just to make the repo feel complete

## 4. What Code Is Allowed To Move Later

The repo bootstrap plan authorizes these classes as future move candidates only after bootstrap:

- Discord interaction command/runtime handlers
- gateway worker
- feedback board logic and sync/export helpers
- update draft/publication runtime
- moderation runtime
- message-command claim runtime logic
- Music Sesh runtime and Spotify orchestration
- Discord REST helpers
- Discord diagnostics/doctor flows

### Move-later examples

- `src/lib/discord/bug-reports.ts`
- `src/lib/discord/update-drafts.ts`
- `src/lib/discord/moderation.ts`
- `src/lib/discord/rest.ts`
- `src/lib/discord/message-command-claims.ts`
- `scripts/discord-feedback-gateway-worker.mjs`
- Music Sesh runtime libs under `src/lib/spotify/**`

Rule:

- each extraction package must be bounded by owner seam, not by file-count convenience

## 5. What Code Must Remain Fitness-Owned

Even after DiscordOS bootstrap, these classes remain outside the extraction-first scope:

- Fitness auth/session ownership
- Fitness profiles and `user_number`
- verification-token issuance
- Fitness account settings / Discord Connector UX
- core workout/product tables and product logic
- QA/LLEL and Fitness app verification flows
- Fitness release-proof truth

Rule:

- bootstrap must not imply that DiscordOS is a replacement Fitness app repo

## 6. Contracts That Must Exist Before Code Moves

No code movement should begin before these seams are either documented and approved or implemented in a bounded later lane:

- verification bridge
- `discord_member_links` ownership seam
- member-number sync contract
- deploy-to-update handoff contract
- shared id / immutable key policy

### Contract requirement

If a DiscordOS runtime slice still depends on hidden direct access to a Fitness-owned surface, that slice is not ready to move.

## 7. Env / Secrets Rule: No Repo-Root Env

DiscordOS bootstrap must adopt the current root secret-path discipline from the start.

### Rules

- no committed secret files
- no long-term repo-root `.env`
- no long-term repo-root `.env.*`
- no copying Fitness env files into the new repo
- local secret-bearing files stay under `secrets/**`

### Allowed bootstrap posture

- example env files may exist if they are explicitly non-secret templates
- real DiscordOS runtime secrets should later live under a governed root secret lane

### Bootstrap implication

The first DiscordOS repo package should include secret-lane guidance, not actual pulled secrets.

## 8. Supabase MCP Setup As Prep Only

The future DiscordOS repo should record Supabase operational prep without treating it as permission to mutate the project.

Operational prep note:

```txt
codex mcp add supabase --url https://mcp.supabase.com/mcp?project_ref=nwexsktuuenfdegzrbut
codex mcp login supabase
optional: npx skills add supabase/agent-skills
```

### Rule

- this setup note is prep only
- bootstrap does not authorize schema creation or row movement

## 9. Vercel Project Creation / Linking Prerequisites

DiscordOS repo bootstrap must not immediately create or link a Vercel project.

Vercel creation/linking should wait for:

1. local repo bootstrap complete
2. env ownership split accepted
3. schema landing accepted
4. runtime/Vercel cutover plan accepted
5. explicit owner approval for the runtime cutover lane

### Rule

- repo bootstrap is not runtime activation

## 10. First Safe PR / Package After Bootstrap

After `repos/DiscordOS` exists, the first safe package should still be narrow and non-disruptive.

### Recommended first package

- bootstrap-only repo skeleton
- repo-local docs and verify contract
- shared contract type stubs
- no live code movement yet

### Alternative first bounded extraction package

If bootstrap is already accepted and the owner wants a first code-moving package, prefer one narrow slice:

- feedback export/sync helpers first
or
- command-claim/runtime helper slice first

Avoid first-package extraction of:

- verification consume flow
- Music Sesh runtime
- full interaction route
- Vercel webhook runtime

Those are later, higher-risk slices.

## 11. Rollback / No-Op Posture

Bootstrap must be reversible and low-risk.

### No-op rule

If bootstrap is prepared but not approved:

- nothing changes
- Fitness remains canonical host
- DiscordOS remains a planned future lane only

### Rollback rule after future bootstrap

If a later bootstrap implementation proves wrong:

- remove or archive the unused local repo only with explicit approval
- keep remote untouched unless owner explicitly requests cleanup
- do not treat partial repo existence as approval to proceed with extraction

### Safe rollback posture

- bootstrap should not carry runtime state
- bootstrap should not own live secrets
- bootstrap should not own active webhook identity

That keeps rollback cheap.

## Bootstrap Readiness Checklist

Before a later implementation lane creates `repos/DiscordOS`, require:

1. shared contract seams accepted
2. env/runtime ownership accepted
3. schema landing plan accepted
4. runtime/Vercel cutover plan accepted
5. target remote verified
6. local target path confirmed safe
7. bootstrap structure agreed
8. no repo-root secret pattern allowed

## Recommended Next Package

After this bootstrap plan, the next clean move is an approval-gated implementation plan for creating `repos/DiscordOS` as an empty governed repo surface, still before any production code extraction.

That later package should name:

- exact bootstrap commands
- exact initial files
- exact verify command
- exact secret-lane guidance
- explicit no-code-move boundary

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `60%`
- Dependency Untangling: `25%`

It does not justify:

- repo creation
- code movement
- Supabase mutation
- Vercel mutation
- bot restart
- runtime cutover
