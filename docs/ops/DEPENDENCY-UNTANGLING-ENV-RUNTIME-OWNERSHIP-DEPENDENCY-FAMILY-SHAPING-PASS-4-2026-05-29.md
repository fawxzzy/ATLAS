# Dependency Untangling Env/Runtime Ownership Dependency Family Shaping Pass 4 - 2026-05-29

- Date: `2026-05-29`
- Lane: `Dependency Untangling env/runtime ownership dependency family shaping pass 4`
- Mode: `docs-only root-bounded family shaping`
- Source surfaces:
  - `docs/ops/STACK-LANE-0-TRUTH-MAP-2026-05-22.md`
  - `docs/ops/POST-CONVERGENCE-LANE-SPLIT-READINESS-2026-05-24.md`
  - `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
  - `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
  - `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
  - `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
  - `docs/ops/DEPENDENCY-UNTANGLING-SHARED-CONTRACT-SEAM-DEPENDENCY-FAMILY-SHAPING-PASS-3-2026-05-29.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Turn the exact current next blocker family, `env/runtime ownership dependency family`, into one operator-usable ownership map, one ownership-family blocked-work ladder, and one exact downstream next package without executing any runtime, schema, repo, or secret-lane change.

This pass does not:

- move code
- mutate repos
- create runtime, schema, or Vercel state
- execute env splitting
- execute runtime cutover
- move the marker

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status: shared root spine already dirty from adjacent durable work; this pass stays within bounded restart and continuity surfaces
- validation: green before shaping at `critical=0 error=0 warning=478`

## Exact Ownership Ambiguity Before This Pass

Before this pass, the upstream seam family was already shaped, but the ownership family still was not operator-usable enough for restart.

The unresolved ambiguity was:

- the direct ownership matrix already named many env, host, and project classes
- but restart truth still mixed:
  - canonical owner-boundary classes
  - downstream runtime-cutover staging consequences
  - repo extraction consequences

That made the family directionally correct but still too broad for exact restart.

## Direct Ownership-Definition Surfaces

The direct ownership-definition surfaces are:

1. `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
   - canonical env/runtime ownership matrix
   - canonical move-later, stay-owned, and paired-seam ownership classes
   - canonical no-move-yet rules
2. `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
   - strongest concrete evidence that the current host and env surfaces are still bundled in `repos/fawxzzy-fitness`
   - exact `src/lib/env.ts`, route, worker, and host assumptions still carrying mixed ownership

## Supporting Seam-Linked Surfaces

The supporting seam-linked surfaces are:

1. `docs/ops/DEPENDENCY-UNTANGLING-SHARED-CONTRACT-SEAM-DEPENDENCY-FAMILY-SHAPING-PASS-3-2026-05-29.md`
   - proves which contract-first seams the ownership map must protect
2. `docs/ops/POST-CONVERGENCE-LANE-SPLIT-READINESS-2026-05-24.md`
   - proves owner lanes must stay explicit
3. `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
   - proves runtime cutover is downstream of the ownership split rather than part of it

## Exact Ownership Map Frozen In This Pass

The `env/runtime ownership dependency family` is now frozen as exactly six ownership classes:

1. `Fitness-retained app/proof ownership class`
   - current and future owner:
     - Fitness
   - includes:
     - Fitness app auth/public Supabase env
     - Fitness service/admin DB auth
     - verification-token issuance secrets
     - release-proof and deploy-truth env
   - family meaning:
     - stays Fitness-owned
2. `DiscordOS-later Discord runtime env ownership class`
   - future owner:
     - DiscordOS
   - includes:
     - Discord bot token and app ids
     - Discord workflow channel and role ids
     - Discord workflow flags and runtime controls
     - Discord runtime worker env
   - family meaning:
     - move later with Discord runtime ownership
3. `DiscordOS-later Music Sesh provider ownership class`
   - future owner:
     - DiscordOS
   - includes:
     - Spotify client and OAuth env
     - Music Sesh provider/runtime secrets
   - family meaning:
     - move later with the Music Sesh runtime slice, not before
4. `paired seam auth ownership class`
   - future owner:
     - paired seam rather than one broad shared env surface
   - includes:
     - verification consume auth
     - member-sync auth
     - release-proof handoff auth
   - family meaning:
     - stays narrow and seam-specific
5. `split project and runtime host ownership class`
   - future owner:
     - split by system and table/runtime class
   - includes:
     - Supabase project ownership split by table class
     - Vercel/runtime host ownership split by system responsibility
   - family meaning:
     - split by owner boundary, not temporary convenience
6. `governed secret-lane destination class`
   - canonical local destination:
     - root `secrets/**`
   - prohibits:
     - repo-root `.env*` as the long-term DiscordOS pattern
   - family meaning:
     - secret destination policy is part of ownership shape, not an afterthought

## Exact Ambiguity Resolution

The ambiguity is now resolved as follows:

- the ownership family includes only owner-boundary classes and their no-move-yet rules
- the ownership family does not include:
  - runtime slice cutover order
  - dual-run or shadow-run proof
  - webhook retargeting
  - repo extraction sequencing
  - code movement

Those are downstream consequences, not part of the ownership family itself.

## Exact Ownership-Family Blocked-Work Ladder

The ownership-family blocked-work ladder is now:

1. `paired seam auth ownership class`
   - because the seam family already proved contract-first boundaries, and the narrow auth keys those seams need must now be owned explicitly before broader runtime split is honest
2. `DiscordOS-later Discord runtime env ownership class`
   - because the main Discord runtime still sits in one mixed Fitness-owned env surface and must be classified before cutover planning can tighten
3. `split project and runtime host ownership class`
   - because Supabase and Vercel host ownership must follow the env split rather than outrun it
4. `DiscordOS-later Music Sesh provider ownership class`
   - because Music Sesh provider ownership is still real, but remains later and bounded by the broader runtime split
5. `governed secret-lane destination class`
   - because the local destination policy must remain fixed across the other four classes rather than becoming a separate migration lane

Why this order is honest:

- it follows the ownership matrix from seam-specific auth outward to broader runtime classes
- it keeps the main Discord runtime ownership split ahead of Music Sesh-specific provider ownership
- it treats secret-lane destination as a cross-cutting policy inside the family, not a separate downstream lane

## Exact Downstream Dependency Consequences

Once the ownership family is shaped, the downstream family order is:

1. `runtime cutover dependency family`
2. `repo bootstrap and extraction dependency family`

Why this order is stable:

- runtime cutover is the first downstream family because the cutover plan depends directly on the now-frozen ownership classes
- repo bootstrap and extraction remains later because it is still the most execution-adjacent consequence and depends on the earlier family order staying fixed

## Exact Shaping Decision

`one decisive ownership-family shaping move completed`

Completed result:

- one exact ownership map now exists
- one ownership-family blocked-work ladder now exists
- one exact downstream family order now exists

## Exact Next Package

`Dependency Untangling runtime cutover dependency family shaping pass 5`

Purpose:

- keep the lane root-bounded
- shape the next downstream family using the frozen seam map and ownership map
- define the exact cutover-order and no-live-change boundaries without executing runtime, schema, or repo changes

## Marker Decision

Hold:

- `Dependency Untangling: 70% -> 70%`

Why:

- the family is clearer
- no live coupling class was cleared
- this is family shaping, not untangling execution

## What This Pass Proves

This pass proves:

- the ownership family is now operator-usable
- owner-boundary classes are now separated cleanly from downstream cutover work
- the runtime-cutover family can now reopen without re-arguing env ownership

This pass does not prove:

- that any env class is moved
- that any host or project split is executed
- that cutover or extraction can begin now

## Exact Recommended Next Move

`Dependency Untangling runtime cutover dependency family shaping pass 5`

## Rule

Shape ownership boundaries first; do not confuse ownership clarity with cutover readiness.

## Pattern

shape seam family -> shape ownership family -> freeze downstream cutover order -> only then shape cutover itself

## Failure Mode

The lane treats runtime cutover staging as if it were ownership clarity, so owner boundaries stay fuzzy and the cutover family inherits mixed assumptions.
