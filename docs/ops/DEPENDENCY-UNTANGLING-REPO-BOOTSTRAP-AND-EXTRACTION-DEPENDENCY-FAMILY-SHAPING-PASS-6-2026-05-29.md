# Dependency Untangling Repo Bootstrap And Extraction Dependency Family Shaping Pass 6 - 2026-05-29

- Date: `2026-05-29`
- Lane: `Dependency Untangling repo bootstrap and extraction dependency family shaping pass 6`
- Mode: `docs-only root-bounded family shaping`
- Source surfaces:
  - `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-PLAN-2026-05-24.md`
  - `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-RECEIPT-2026-05-25.md`
  - `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
  - `docs/ops/DEPENDENCY-UNTANGLING-SHARED-CONTRACT-SEAM-DEPENDENCY-FAMILY-SHAPING-PASS-3-2026-05-29.md`
  - `docs/ops/DEPENDENCY-UNTANGLING-ENV-RUNTIME-OWNERSHIP-DEPENDENCY-FAMILY-SHAPING-PASS-4-2026-05-29.md`
  - `docs/ops/DEPENDENCY-UNTANGLING-RUNTIME-CUTOVER-DEPENDENCY-FAMILY-SHAPING-PASS-5-2026-05-29.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Turn the exact current next blocker family, `repo bootstrap and extraction dependency family`, into one operator-usable extraction map, one extraction-family blocked-work ladder, and one exact downstream next package without moving code, mutating repos, or starting runtime cutover execution.

This pass does not:

- move code
- mutate repos
- mutate Supabase
- mutate Vercel
- retarget the worker
- execute runtime cutover
- execute cleanup
- move the marker

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status: shared root spine already dirty from adjacent durable work; this pass stays within bounded restart and continuity surfaces
- validation: green before shaping at `critical=0 error=0 warning=478`

## Exact Bootstrap/Extraction Ambiguity Before This Pass

Before this pass, the upstream seam, ownership, and cutover families were already shaped, but the repo bootstrap and extraction family still was not operator-usable enough for restart.

The unresolved ambiguity was:

- the original bootstrap plan still contained pre-bootstrap creation logic that is no longer current
- the post-bootstrap inventory already named candidate extraction order
- but restart truth still mixed:
  - already-complete bootstrap creation
  - bounded extraction sequencing
  - later cleanup consequences

That made the family directionally correct but still too broad for exact restart.

## Direct Bootstrap/Extraction-Definition Surfaces

The direct bootstrap/extraction-definition surfaces are:

1. `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-PLAN-2026-05-24.md`
   - canonical original bootstrap-first repo plan
   - canonical governance-first repo structure and no-secret rules
2. `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-RECEIPT-2026-05-25.md`
   - strongest proof that bootstrap creation is already complete at `repos/DiscordOS`
   - strongest proof that the repo is still scaffold-only rather than partially extracted
3. `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
   - canonical extraction inventory
   - canonical first safe extraction order
   - canonical explicit no-move-yet boundaries

## Supporting Seam/Ownership/Cutover-Linked Surfaces

The supporting seam/ownership/cutover-linked surfaces are:

1. `docs/ops/DEPENDENCY-UNTANGLING-SHARED-CONTRACT-SEAM-DEPENDENCY-FAMILY-SHAPING-PASS-3-2026-05-29.md`
   - proves which Fitness-facing seams must stay explicit during extraction
2. `docs/ops/DEPENDENCY-UNTANGLING-ENV-RUNTIME-OWNERSHIP-DEPENDENCY-FAMILY-SHAPING-PASS-4-2026-05-29.md`
   - proves which owner-boundary classes the extraction sequence must preserve
3. `docs/ops/DEPENDENCY-UNTANGLING-RUNTIME-CUTOVER-DEPENDENCY-FAMILY-SHAPING-PASS-5-2026-05-29.md`
   - proves extraction remains downstream of shaped cutover stages rather than a substitute for them

## Exact Bootstrap/Extraction Map Frozen In This Pass

The `repo bootstrap and extraction dependency family` is now frozen as exactly seven extraction stages:

1. `scaffold-only canonical repo hold stage`
   - `repos/DiscordOS` remains the canonical local landing surface
   - the repo stays governance-first and scaffold-only until bounded extraction packages begin
   - family meaning:
     - bootstrap creation is complete, but extraction has not started
2. `interaction-route decomposition stage`
   - decompose the current monolithic Fitness interaction route into named domain handler surfaces before repo copy
   - family meaning:
     - route decomposition precedes extraction
3. `core runtime utility extraction stage`
   - bounded low-risk DiscordOS-owned helpers move first:
     - message-command claims
     - Discord REST transport
     - selected interaction constants and builders that are not Fitness-owned seams
   - family meaning:
     - smallest clean runtime utilities lead
4. `feedback runtime extraction stage`
   - feedback lifecycle and panel or forum sync helpers become the first domain extraction package after route decomposition and core utilities are stable
   - family meaning:
     - feedback leads the larger domain moves
5. `update publication runtime extraction stage`
   - Discord publication runtime may extract later while Fitness deploy-proof truth stays upstream
   - family meaning:
     - publish runtime moves without relocating release proof
6. `moderation runtime extraction stage`
   - moderation case storage and Discord action adapters move only after earlier runtime slices are bounded
   - family meaning:
     - moderation stays after feedback and updates
7. `Music Sesh bounded extraction stage`
   - Music Sesh moves as one bounded runtime slice rather than scattered table or helper copies
   - family meaning:
     - highest-coupling runtime slice remains later and whole

## Exact Ambiguity Resolution

The ambiguity is now resolved as follows:

- the bootstrap/extraction family includes only extraction order, repo-local landing logic, and explicit no-move-yet boundaries
- the bootstrap/extraction family no longer includes:
  - bootstrap creation
  - runtime cutover staging
  - worker or webhook retargeting
  - cleanup execution after cutover

Bootstrap creation is already complete, cutover order is already frozen upstream, and cleanup remains downstream of any future extraction or cutover execution.

## Explicit No-Move-Yet Boundary Frozen In This Pass

Do not move yet:

- `src/app/api/discord/verification-token/route.ts`
- `src/app/api/discord/verify/route.ts`
- `src/app/api/discord/member-numbers/sync/route.ts`
- `src/app/api/vercel/deployment-webhook/route.ts`
- Spotify OAuth, token, and provider state as a standalone slice
- the monolithic interaction route as a wholesale file copy

Why this boundary is durable:

- each surface still depends on a Fitness-owned or shared-contract seam that is not honest to extract as a first bounded move
- these are boundary statements inside the extraction family, not later cleanup chores

## Exact Bootstrap/Extraction-Family Blocked-Work Ladder

The bootstrap/extraction-family blocked-work ladder is now:

1. `interaction-route decomposition stage`
   - because the monolithic route is still the highest extraction-pressure surface and must be split before any honest repo-local move
2. `core runtime utility extraction stage`
   - because low-risk runtime utilities are the first bounded repo-local move after route decomposition
3. `feedback runtime extraction stage`
   - because feedback is the first large domain already named as safest after the utility slice
4. `update publication runtime extraction stage`
   - because publish runtime can move later while Fitness proof stays upstream
5. `moderation runtime extraction stage`
   - because moderation continuity remains real but later than feedback and updates
6. `Music Sesh bounded extraction stage`
   - because Music Sesh remains the highest-coupling runtime slice and should move last as one bounded domain

Why this order is honest:

- it follows the existing post-bootstrap extraction inventory
- it preserves the frozen seam, ownership, and cutover boundaries
- it keeps the highest-risk Music Sesh slice last
- it treats no-move-yet shared-contract surfaces as explicit boundaries rather than pretending they are ordinary extraction slices

## Exact Downstream Dependency Consequences

Once the bootstrap/extraction family is shaped, no additional blocker family remains inside the current `Dependency Untangling` shaping ladder.

The next honest package is:

1. `Dependency Untangling continuity-manifest refresh and ratchet decision pass 7`

Why this order is stable:

- all four blocker families are now shaped
- the next honest question is no longer “which blocker family is next”
- the next honest question is whether the fully shaped lane now justifies a lane-level refresh and ratchet decision from root-visible restart reality

## Exact Shaping Decision

`one decisive bootstrap/extraction-family shaping move completed`

Completed result:

- one exact extraction map now exists
- one extraction-family blocked-work ladder now exists
- one exact downstream lane-level next package now exists

## Exact Next Package

`Dependency Untangling continuity-manifest refresh and ratchet decision pass 7`

Purpose:

- keep the lane root-bounded
- evaluate the fully shaped Dependency Untangling lane as one manifest-backed control-plane unit
- decide whether the lane now warrants a refresh-only hold or the smallest honest marker ratchet

## Marker Decision

Hold:

- `Dependency Untangling: 70% -> 70%`

Why:

- the family is clearer
- no live coupling class was cleared
- this is final family shaping, not untangling execution

## What This Pass Proves

This pass proves:

- the repo bootstrap and extraction family is now operator-usable
- bootstrap creation is now separated cleanly from extraction order
- the lane no longer has another unresolved blocker family below the current control-plane layer

This pass does not prove:

- that any extraction package executed
- that any runtime slice moved
- that any cleanup is ready now
- that the marker should ratchet yet

## Exact Recommended Next Move

`Dependency Untangling continuity-manifest refresh and ratchet decision pass 7`

## Rule

Shape extraction order first; do not confuse extraction clarity with extraction execution.

## Pattern

shape seam family -> shape ownership family -> shape runtime cutover family -> shape repo extraction family -> only then evaluate the lane for refresh or ratchet

## Failure Mode

The lane treats repo extraction planning as if it were live untangling progress, so marker movement outruns actual coupling clearance.
