# Current System Map / Graph

## Purpose

This chapter is the compact cross-system map for the current stack.

It shows:

- which repos exist and who owns them
- which runtime and data surfaces are live today
- which future surfaces are planned but not active
- which contracts and approval gates block the next mutations

## Repo Map

### Current canonical repo surfaces

- `ATLAS`
  - stack coordination, receipts, markers, and book truth
- `repos/_stack`
  - governed deploy authority and shared operator execution
- `repos/fawxzzy-fitness`
  - Fitness app/runtime truth
  - current Discord-hosted runtime truth
- `repos/fawxzzy-trove`
  - Trove repo-local runtime truth
- `repos/fawxzzy-mazer`
  - Mazer repo-local runtime truth
- `repos/fawxzzy-foundation`
  - Foundation repo-local runtime truth
- `repos/DiscordOS`
  - canonical DiscordOS repo surface now exists locally
  - governance scaffold only
  - no migrated runtime code yet

## Runtime Map

### Current live runtime shape

- Fitness Vercel hosts:
  - Fitness app runtime
  - current Discord interaction/runtime
  - current feedback/update/moderation runtime
  - current Music Sesh runtime
- `_stack` remains the governed deploy authority
- ATLAS root does not host product runtime

### Future runtime shape

- Fitness runtime stays Fitness-owned
- Discord runtime moves to DiscordOS-owned surfaces later
- `_stack` remains shared deploy and execution authority

## Supabase Project Map

### Current

- Fitness Supabase: `lpswxoyfniocuhljgzbc`
  - live Fitness auth/profile truth
  - verification issuance truth
  - current live Discord/Music Sesh operational tables

### Future

- DiscordOS Supabase: `nwexsktuuenfdegzrbut`
  - healthy
  - empty
  - no schema landing implemented yet
  - future home for Discord-owned runtime/workflow tables

## Vercel Project Map

### Canonical active surfaces

- `fawxzzy-fitness`
  - current live operational hotspot
  - canonical Fitness runtime truth
- `fawxzzy-trove`
  - active product surface
- `fawxzzy-mazer`
  - quieter active product surface
- `fawxzzy-foundation`
  - quieter systems/product surface

### Known stale or duplicate-pressure surfaces

No helper Vercel project remains in the active live set after the 2026-05-25 helper-surface deletion pass.

Historical note:

- the stale Spotify-era Vercel projects were deleted on 2026-05-25 after dependency clearance
- the helper projects `fitness-deploy-green-panels` and `fitness-prod-rollout-20260525` were also deleted on 2026-05-25 after a clean dependency check

## DiscordOS / Fitness Shared-Seam Map

### Current shared seams

- verification bridge
- `discord_member_links`
- member-number sync
- deploy-to-update handoff
- current Discord/Music Sesh tables inside Fitness Supabase

### Future target posture

- Fitness keeps:
  - verification issuance
  - Fitness auth/profile truth
  - Fitness release proof
- DiscordOS later owns:
  - feedback runtime
  - update draft/publication runtime
  - moderation runtime
  - Music Sesh runtime

## `_stack` Command Ownership Map

`_stack` currently owns or should later own:

- governed deploy authority
- validation and receipt packaging helpers
- release-prep to deploy handoff
- stale-surface audit helpers
- future Vercel health classification helper

`_stack` does not own product or Discord runtime truth.

## Playbook Doctrine Flow

Current doctrine flow:

1. repeated receipt-backed rule appears in owner workflows
2. ATLAS records the pattern and convergence consequence
3. doctrine routing classifies it
4. Playbook later owns the reusable governance framing

Playbook does not become runtime owner at any step.

## Cortex Planning-Context Flow

Current planning-context flow:

1. ATLAS and receipt surfaces record durable state
2. ownership and seam docs create planning context
3. Cortex can later consume that planning context
4. Cortex does not currently mutate runtime or govern deploys

## Receipt / Proof Flow

Canonical flow:

1. owner repo or owner lane creates proof
2. `_stack` performs governed deploy where needed
3. owner repo records release or runtime proof
4. Discord publication consumes proof only after that
5. ATLAS records the cross-repo checkpoint
6. Playbook later extracts reusable doctrine

## Approval-Gated Lanes

Current approval-gated lanes:

- remote preview / unfurl verification

Historical note:

- the Fitness Supabase mutation gate chain was fully exercised and then closed by `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-FINAL-CLOSEOUT-2026-05-25.md`
- any future Fitness Supabase work must reopen as a new, narrower lane instead of treating profile/data hygiene as still generally open

## Future Split

### Fitness app lane

- product and UX
- QA/LLEL
- local/mobile proof
- Fitness profile/data hygiene when approved

### Discord work lane

- DiscordOS
- bot/runtime
- feedback/update/moderation workflows
- Music Sesh
- DiscordOS Supabase

### ATLAS systems lane

- ATLAS root
- `_stack`
- Foundation
- Lifeline
- Playbook
- Cortex planning surfaces
- markers, receipts, validation, and governance automation

## System Graph

```mermaid
flowchart LR
  ATLAS["ATLAS Root\nReceipts, markers, book, coordination"]
  STACK["_stack\nGoverned deploy authority\nOperator execution"]
  PLAYBOOK["Playbook\nDoctrine and governance"]
  CORTEX["Cortex\nPlanning-context consumer"]
  FITNESS_REPO["Fitness Repo\nrepos/fawxzzy-fitness"]
  FITNESS_VERCEL["Fitness Vercel\nLive app + current Discord runtime"]
  FITNESS_DB["Fitness Supabase\nlpswxoyfniocuhljgzbc"]
  DISCORDOS_REPO["DiscordOS Repo\nrepos/DiscordOS\nbootstrapped scaffold"]
  DISCORDOS_VERCEL["DiscordOS Vercel\nfuture runtime owner"]
  DISCORDOS_DB["DiscordOS Supabase\nnwexsktuuenfdegzrbut\nhealthy, empty"]
  DISCORD["Discord Surfaces\nFeedback, updates, moderation,\nMusic Sesh"]
  STALE["Historical stale/helper Vercel cleanup\nclosed on 2026-05-25"]

  FITNESS_REPO --> FITNESS_VERCEL
  FITNESS_VERCEL --> DISCORD
  FITNESS_REPO --> FITNESS_DB
  STACK --> FITNESS_VERCEL
  FITNESS_REPO --> ATLAS
  FITNESS_VERCEL --> ATLAS
  ATLAS --> PLAYBOOK
  ATLAS --> CORTEX

  FITNESS_DB -. "verification bridge,\nmember links,\nmember-number sync,\ndeploy-update handoff" .- DISCORDOS_DB
  DISCORDOS_REPO -. "future code + runtime landing" .- DISCORDOS_VERCEL
  DISCORDOS_VERCEL -. "future cutover" .- DISCORD
  DISCORDOS_REPO -. "future schema + runtime move" .- DISCORDOS_DB

  FITNESS_VERCEL -. "helper-surface pressure" .- STALE
```

## Machine-Readable Appendix

| Lane / surface | Owner | Source of truth | Current status | Blocker | Next package |
| --- | --- | --- | --- | --- | --- |
| Fitness app lane | Fitness | `repos/fawxzzy-fitness` plus Fitness release proof | active | none for normal product work | explicit Fitness lane reopen |
| Discord work lane | Fitness-hosted now, DiscordOS later | Fitness repo/runtime now; `repos/DiscordOS` plus ATLAS separation receipts as future target | scaffold complete, runtime migration not started | no runtime-shadow or adapter implementation package yet | next narrow DiscordOS scaffold or runtime-shadow plan |
| ATLAS systems lane | ATLAS root plus `_stack` and Playbook boundaries | ATLAS docs and receipts | active closeout and governance lane | retained worktree, helper-surface, and residue cleanup pressure | closeout planning or bounded retained-surface package |
| Fitness Supabase hygiene | Fitness | Fitness Supabase plus ATLAS closeout and governance receipts | closed at `100%`; remaining Discord/Music Sesh concerns transferred out of lane scope | none inside Fitness profile-core cleanup scope | defer any Discord/Music Sesh follow-on to Discord OS Infrastructure Separation |
| DiscordOS bootstrap | DiscordOS | `repos/DiscordOS` | completed with governance scaffold only | no migrated code yet | bounded post-bootstrap implementation plan |
| Helper Vercel decommission | ATLAS systems lane with owner confirmation | Vercel inventory and deletion receipts | stale Spotify-era and helper Fitness projects deleted | provenance clarity and future health classification only | preview/unfurl verification or Vercel health-design lane |
| Lifeline health projection | Lifeline later, `_stack` first | current Vercel and stack health receipts | pressure identified, not implemented | no command surface yet | docs or command-design lane for `stack vercel-health` |

## Non-Goals

- no repo creation
- no code movement
- no data migration
- no Vercel mutation
- no Discord runtime change
