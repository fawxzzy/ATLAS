# Discord OS Runtime / Vercel Cutover Plan

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: docs-only planning
Status: first runtime and Vercel cutover plan recorded

## Goal

Plan how Discord OS moves from the current Fitness-hosted runtime into governed DiscordOS-owned runtime surfaces without breaking live Discord operations, losing state continuity, or collapsing the explicit Fitness-facing contracts already defined in the separation lane.

This pass does not:

- create `repos/DiscordOS`
- move code
- create or mutate a Vercel project
- mutate either Supabase project
- restart the bot
- retarget the gateway worker
- post to Discord
- pull env
- print secrets
- change Fitness code

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`
- `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
- `docs/ops/UNIFIED-RELEASE-DEPLOY-UPDATE-HANDOFF-2026-05-24.md`

## Target Future Surfaces

- GitHub repo: `https://github.com/fawxzzy/DiscordOS.git`
- local target repo: `repos/DiscordOS`
- Supabase project: `DiscordOS`
- Supabase ref: `nwexsktuuenfdegzrbut`
- future runtime owner: DiscordOS, not Fitness

## Governing Rules

- Fitness remains canonical for Fitness auth, profiles, verification-token issuance, and release proof.
- DiscordOS later becomes canonical for Discord-first runtime and workflow state.
- No Discord post may publish before Fitness proof exists.
- Discord command, panel, forum, update, moderation, and Music Sesh continuity outrank convenience during cutover.
- No hidden shared runtime should remain after cutover; shared seams must become explicit contracts.
- No live change is the default until repo bootstrap, schema landing, dual-run proof, and rollback posture are all complete.

## 1. Current Fitness-Hosted Runtime Shape

Discord OS is currently hosted inside the Fitness stack in one bundled runtime shape:

- repo:
  - `repos/fawxzzy-fitness`
- Vercel/runtime host:
  - Fitness-owned Vercel project and routes
- interaction entrypoint:
  - `src/app/api/discord/interactions/route.ts`
- verification issue/consume surfaces:
  - `src/app/api/discord/verification-token/route.ts`
  - `src/app/api/discord/verify/route.ts`
- worker surface:
  - `scripts/discord-feedback-gateway-worker.mjs`
- current runtime data host:
  - Fitness Supabase `lpswxoyfniocuhljgzbc`

This current host shape owns, in one system:

- feedback panel and forum lifecycle
- update draft and publish flow
- moderation and purgatory flow
- greeting and message-command runtime
- Music Sesh runtime and provider orchestration
- Discord verification consume behavior

## 2. Future DiscordOS Repo / Runtime Shape

The future DiscordOS runtime should split by owner, not by temporary convenience.

### Future DiscordOS-owned runtime

- canonical repo:
  - `repos/DiscordOS`
- remote:
  - `https://github.com/fawxzzy/DiscordOS.git`
- runtime host:
  - DiscordOS-owned Vercel project
- canonical DiscordOS runtime responsibilities:
  - Discord interaction webhook handling
  - gateway worker target/runtime behavior
  - feedback board runtime state
  - update drafting and Discord publication runtime
  - moderation runtime
  - Music Sesh runtime
  - command dedupe/runtime claims

### Future Fitness-retained runtime

- Fitness app routes
- authenticated Fitness account/product surfaces
- verification-token issuance
- canonical profile and member-number truth
- release-proof and deployment truth

## 3. Vercel Ownership And Project Identity Plan

### Current posture

- Fitness currently owns the live Discord interaction runtime and deploy webhook ingestion under the Fitness Vercel project.
- The gateway worker currently targets the Fitness interaction route.

### Future posture

- Fitness Vercel should remain the canonical host for Fitness app and Fitness proof surfaces.
- DiscordOS should later own its own Vercel project for Discord runtime and workflow handling.

### Vercel identity plan

The future cutover should establish one governed DiscordOS Vercel identity only after:

1. local `repos/DiscordOS` exists
2. DiscordOS schema landing is ready
3. env ownership is split
4. runtime cutover artifacts are approved

### No-live-change rule

This plan does not authorize:

- creating a new Vercel project
- linking a local repo
- changing webhook URLs
- switching Discord interaction endpoints

## 4. Bot Process Hosting Plan

### Current bot-process shape

- the always-on gateway worker is still a governed local/runtime process
- it currently targets the Fitness-hosted interaction route
- fallback polling and event-driven handling are already stabilized on the current host

### Future bot-process shape

- the worker should eventually target DiscordOS-owned interaction/runtime surfaces
- bot-process ownership should move with:
  - Discord bot env ownership
  - DiscordOS Vercel ownership
  - DiscordOS Supabase runtime ownership

### Bot-process cutover rule

- do not retarget the worker before DiscordOS webhook/runtime proof exists
- do not run two uncontrolled writers against the same command/runtime tables
- if shadow runtime is needed, only one canonical responder may answer live Discord commands

## 5. Env Ownership Handoff

The env ownership matrix already defines the split. Runtime cutover must follow that split in order:

### Fitness keeps

- Fitness app auth and Supabase env
- verification-token issuance secrets
- release-proof and deploy-truth env

### DiscordOS later owns

- Discord bot token and app ids
- Discord workflow channel/role ids
- feedback/update/moderation runtime env
- Music Sesh provider env
- DiscordOS Supabase env

### Shared-contract env classes

- verification consume auth
- member-sync auth
- release-proof handoff auth

### Handoff rule

- no secret class moves before its runtime consumer exists
- no new repo-root `.env*` pattern is allowed for DiscordOS
- root `secrets/**` remains the canonical local secret lane

## 6. Supabase Ownership Handoff

### Fitness-owned classes that stay

- Fitness auth
- Fitness profiles
- verification-token issuance truth
- Fitness release-proof truth

### DiscordOS-later classes

- feedback runtime state
- update draft/publish runtime state
- moderation runtime state
- message-command claim runtime state
- Music Sesh runtime state

### Handoff rule

- schema landing precedes runtime cutover
- read-only dual-read proof precedes canonical writer move
- runtime cutover should not happen while DiscordOS schema is still hypothetical

## 7. Fitness-Facing Contract Dependencies

Runtime cutover is blocked on explicit contract seams already identified:

- verification bridge
- `discord_member_links`
- member-number sync
- deploy-to-update handoff
- shared ids and immutable keys

These seams are required because DiscordOS runtime cannot cut over cleanly if it still relies on hidden direct access to Fitness-owned truth.

### Contract rule

- Fitness proof stays upstream
- DiscordOS runtime consumes only the minimum needed contract fields
- no DiscordOS runtime should become an informal second Fitness identity system

## 8. Discord Command / Panel / Interaction Continuity

The cutover plan must preserve live Discord continuity for:

- feedback `Submit`, `Edit`, update, withdraw, and completion-review flows
- setup panels and command cards
- greeting and approved message-command responses
- update-draft review and publish controls
- moderation actions
- verification consume behavior
- Music Sesh controls and public panel state

### Continuity requirement

At no point should users experience:

- duplicate responses from two runtimes
- disappearing setup panels
- broken modal submissions
- broken command dedupe
- broken feedback thread sync

### Safe cutover default

- if DiscordOS runtime is not yet proven end-to-end, Fitness remains the live responder

## 9. Spotify Club / Music Sesh Continuity

Music Sesh continuity is one of the highest-risk cutover classes because it combines:

- Discord interaction state
- provider OAuth/runtime state
- room/lobby continuity
- queue ordering
- public panel continuity

### Cutover rule

Do not split Music Sesh across mixed canonical writers.

### Required continuity invariants

- panel channel/message continuity
- room slug continuity
- queue order continuity
- member-room continuity
- Spotify connection uniqueness continuity
- no duplicate approval or playback actions

### Safe migration implication

Music Sesh should move as one bounded runtime slice after schema landing and dual-read proof, not as scattered table-by-table improvisation.

## 10. Feedback / Updates / Moderation Continuity

These Discord workflow surfaces must remain stable through cutover:

### Feedback continuity

- forum starter posts remain editable and syncable
- report ids remain stable
- thread ids and message ids remain stable
- card formatting contract remains stable

### Updates continuity

- Fitness deploy proof remains upstream
- draft creation and publish behavior remain curated
- public `#updates` format remains governed

### Moderation continuity

- existing case ids remain stable
- purgatory release logic does not lose active state
- moderator audit continuity remains intact

## 11. Staged Migration Plan

### Stage 1: code inventory

Bound the exact DiscordOS extraction surface inside Fitness:

- route handlers
- Discord libs
- worker code
- Music Sesh runtime
- feedback/update/moderation helpers

Output:

- approved extraction inventory

### Stage 2: repo bootstrap

After explicit approval in a later lane:

- create `repos/DiscordOS`
- link it to `https://github.com/fawxzzy/DiscordOS.git`
- establish repo-local docs, verify commands, and governed env expectations

Output:

- canonical local repo exists

### Stage 3: schema landing

Land DiscordOS target schema after explicit approval:

- no live canonical writer move yet
- no runtime retarget yet

Output:

- DiscordOS Supabase landing zone exists

### Stage 4: read-only dual-run proof

Prove DiscordOS runtime can:

- read required contract seams from Fitness
- read required DiscordOS-owned state safely
- render equivalent results without becoming the live writer

Output:

- read-only proof package

### Stage 5: runtime shadow

Only if needed:

- DiscordOS runtime may shadow selected flows without becoming the live public responder
- shadow mode must not create duplicate Discord replies or duplicate canonical writes

Output:

- shadow comparison evidence

### Stage 6: cutover

Bounded cutover should proceed by runtime slice, not by vague “move DiscordOS now” intent.

Recommended runtime order:

1. feedback and command-claim runtime
2. update draft/publication runtime
3. moderation runtime
4. Music Sesh runtime
5. verification consume runtime if later approved by contract

Output:

- DiscordOS becomes canonical runtime owner for the approved slice

### Stage 7: Fitness cleanup

Only after successful cutover and rollback-safe observation:

- retire old Fitness-hosted canonical writes for moved slices
- remove obsolete Fitness runtime code in bounded packages
- keep Fitness-owned contracts and proof surfaces intact

Output:

- reduced Fitness/Discord coupling

## 12. Rollback Plan

Every runtime slice needs explicit rollback answers before live cutover:

- which runtime becomes canonical again
- how worker target is reverted
- how webhook target is reverted
- how data writers are restored
- how public Discord continuity is preserved
- how exported state is restored if row movement accompanied cutover

### Minimum rollback rule

If DiscordOS runtime proves unstable during cutover:

1. restore Fitness as canonical responder
2. restore prior canonical writer for the moved slice
3. preserve Discord-facing ids and visible continuity
4. record the failed cutover as a bounded incident or migration receipt

## 13. No-Live-Change Default

Until later approval packages land, the default remains:

- Fitness is the live Discord runtime owner
- Fitness Vercel remains the active Discord interaction host
- Fitness Supabase remains the active Discord runtime data host
- the gateway worker remains pointed at the current Fitness runtime

No cutover should be inferred from:

- documentation progress
- schema readiness alone
- repo bootstrap alone
- env ownership planning alone

## First Safe Runtime Cutover Preconditions

Before any live runtime change, require all of:

1. `repos/DiscordOS` exists and is the canonical local source surface
2. DiscordOS Vercel ownership plan is accepted
3. DiscordOS schema landing exists
4. explicit contract seams are implemented or otherwise proven
5. env classes are split into governed owner lanes
6. export and rollback artifacts are prepared
7. read-only dual-run proof is accepted
8. bounded runtime slice for cutover is named
9. explicit owner approval is recorded

## Recommended Next Package

The next clean move after this cutover plan is a docs-only repo bootstrap plan for `repos/DiscordOS`, not implementation yet.

That package should define:

- initial repo skeleton
- verify commands
- doc surfaces
- env contract stubs
- no-code-move bootstrap rules

## Marker Interpretation

This package justifies:

- Discord OS Infrastructure Separation: `50%`
- Dependency Untangling: `20%`

It does not justify:

- repo creation
- code movement
- Supabase mutation
- Vercel mutation
- bot restart
- live runtime cutover
