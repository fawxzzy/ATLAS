# FawxzzyFitness Feedback Board Ownership Check - 2026-06-10

- Date: `2026-06-10`
- Owner: ATLAS root
- Mode: `docs-only governance receipt`
- Scope: `feedback board ownership check across fawxzzy-fitness and DiscordOS`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `repos/fawxzzy-fitness/AGENTS.md`
  - `repos/fawxzzy-fitness/AGENT.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - `repos/fawxzzy-fitness/package.json`
  - `repos/fawxzzy-fitness/scripts/export-feedback-board.mjs`
  - `repos/fawxzzy-fitness/scripts/sync-feedback-forum-posts.mjs`
  - `repos/fawxzzy-fitness/scripts/generate-feedback-task-packets.mjs`
  - `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
  - `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
  - `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
  - `repos/fawxzzy-fitness/supabase/migrations/20260515150000_059_discord_feedback_reports.sql`
  - `repos/DiscordOS/AGENTS.md`
  - `repos/DiscordOS/docs/contracts/feedback-runtime.md`
  - `repos/DiscordOS/src/contracts/feedback.ts`
  - `repos/DiscordOS/src/adapters/feedback/README.md`

## Objective

Determine whether the FawxzzyFitness feedback board is currently owned by `repos/DiscordOS`, `repos/fawxzzy-fitness`, or a transitional split between both, and freeze the safe routing decision before any card-schema or board-card mutation work happens.

## Repo And Branch Check

Inspected repos:

- `repos/fawxzzy-fitness`
  - remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
  - branch: `main`
  - worktree: `dirty`
- `repos/DiscordOS`
  - remote: `https://github.com/fawxzzy/DiscordOS.git`
  - branch: `codex/path-discipline-warning-slice-discordos`
  - worktree: `clean`

Current ATLAS root session:

- repo context: `ATLAS root`
- this receipt is a cross-repo governance read, not a board mutation pass

## Ownership Decision

Decision:

- canonical board owner is still `repos/fawxzzy-fitness`
- `repos/DiscordOS` is still transitional for this domain
- safe classification is `Fitness-owned live board plus DiscordOS future contract scaffold`

Why:

- Fitness still owns the live board docs, export scripts, sync scripts, task-packet generator, forum-body formatter, feedback runtime helpers, and feedback persistence table
- Fitness docs explicitly state the current model as `Discord Feedback Forum = user-visible board` and `Supabase = bounded source index`
- Fitness package scripts still expose the live operator command surface:
  - `feedback:board:export`
  - `feedback:sync-forum-posts`
  - `feedback:sync-resolved-reactions`
  - `feedback:repair-board-state`
- Fitness runtime code still formats and syncs live feedback cards through:
  - `src/lib/discord/bug-reports.ts`
  - `src/lib/discord/runtime/feedback/forum.ts`
  - `scripts/sync-feedback-forum-posts.mjs`
- Fitness persistence still lands in `public.discord_feedback_reports` and related feedback migrations
- DiscordOS explicitly says feedback runtime is scaffold-only and still Fitness-owned for:
  - live feedback persistence
  - live forum thread/message sync
  - live audit comment posting
  - canonical `discord_feedback_reports` rows
- DiscordOS currently exposes only contract and adapter scaffolds, not a replacement board source of truth or sync pipeline

## Source-Of-Truth Decision

Canonical source of truth today:

- board/card operational truth: `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
- bounded indexed card data: Fitness-owned `public.discord_feedback_reports`
- board export and reviewed planning artifacts: `repos/fawxzzy-fitness/scripts/export-feedback-board.mjs`
- Discord forum render/sync target: `repos/fawxzzy-fitness/scripts/sync-feedback-forum-posts.mjs`
- reviewed Codex packet generation: `repos/fawxzzy-fitness/scripts/generate-feedback-task-packets.mjs`

Render targets only:

- Discord forum threads and starter messages
- generated export artifacts under Fitness runtime output paths

Future-only, not current source of truth:

- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/**`

## Safe-To-Proceed Decision

Safe to proceed in this ATLAS-root chat:

- `yes` for governance-only ownership classification and routing
- `no` for board-card, schema, sync, or Discord mutation work

Safe to proceed in a repo mutation chat right now:

- `no` in `repos/DiscordOS` for board ownership migration work because the repo still declares scaffold-only contract surfaces
- `not yet` in `repos/fawxzzy-fitness` until the current dirty worktree is intentionally classified, preserved, or moved to the exact active implementation branch that should own the board change

Exact routing decision:

- if the Clean/Re-sync board work is still active, continue inside that same active Codex lane in `repos/fawxzzy-fitness`
- if that lane is merged later, rerun this ownership check before moving work to `repos/DiscordOS`
- do not start dependency metadata or monetization-card mutation in `repos/DiscordOS` from the current evidence set

## Exact Files To Modify Later

Primary likely files for later board-card or dependency work, if routed into Fitness:

- `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
- `repos/fawxzzy-fitness/scripts/export-feedback-board.mjs`
- `repos/fawxzzy-fitness/scripts/sync-feedback-forum-posts.mjs`
- `repos/fawxzzy-fitness/scripts/generate-feedback-task-packets.mjs`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.test.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.test.ts`

Conditional later-touch files only if persistence shape must widen:

- `repos/fawxzzy-fitness/supabase/migrations/*discord_feedback*`
- any Fitness feedback validation or repair script proven to enforce the card shape

## Exact Files Not To Modify Yet

Do not modify yet because they are future-facing, transitional, or not the current canonical owner:

- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/**`

Do not treat these as source-of-truth mutation targets:

- Discord forum threads or starter messages by hand
- generated export outputs under Fitness runtime folders
- any stale or duplicate planning copy outside the canonical board docs and bounded index

Do not start from the current dirty Fitness worktree without explicit branch/worktree handling:

- the checked-out `repos/fawxzzy-fitness` `main` already carries unrelated tracked and untracked work

## Rule

`Board Item Source-Of-Truth Rule`

The repo-owned board/card source and the bounded indexed data must remain canonical. Discord forum posts are render targets, not the source of truth.

## Pattern

owner repo board docs plus bounded persistence -> export and sync scripts -> Discord forum render target -> reviewed Codex work

## Failure Mode

`Cross-Repo Drift During Extraction`

If DiscordOS extraction is not complete and board-card mutation starts in a separate repo or stale branch, cards, schema changes, and sync behavior drift into the wrong owner surface.
