# Discord OS Infrastructure Separation Owner-Side Schema And Vercel Linkage - 2026-06-12

- Date: `2026-06-12`
- Lane: `Discord OS Infrastructure Separation`
- Supporting lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `owner-side setup execution and root reconciliation`
- DiscordOS repo checkpoint: `codex/path-discipline-warning-slice-discordos@b9a22ef`
- ATLAS root lock target: `stack.lock.yaml#discordos -> b9a22ef371b17fad7f4a412b0948dd81497beaba`

## Objective

Execute the approved DiscordOS owner-side setup packet across Supabase, Vercel, GitHub, and ATLAS without widening into deploy, bot runtime activation, Fitness runtime mutation, or live workflow parity claims.

## Live Execution

GitHub:

- confirmed `fawxzzy/DiscordOS` exists
- confirmed writable/admin connector access
- committed and pushed DiscordOS setup documentation and schema mirror to `codex/path-discipline-warning-slice-discordos`

Supabase:

- confirmed project `DiscordOS`
- project ref: `nwexsktuuenfdegzrbut`
- status: `ACTIVE_HEALTHY`
- applied migration `20260612082758 discordos_feedback_runtime_schema_v1`
- applied migration `20260612082854 discordos_set_updated_at_search_path`
- verified private schema `discordos`
- verified RLS-enabled tables:
  - `discordos.discord_feedback_reports`
  - `discordos.discord_feedback_audit_events`
  - `discordos.discord_feedback_completion_reviews`
- verified the security advisor no longer reports the trigger-function search-path warning

Vercel:

- created project `fawxzzy-discordos`
- project id: `prj_C2RSEa34OblHfhuEpVChRQQZSjuG`
- team: `fawxzzy`
- team id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- linked local `repos/DiscordOS` through `.vercel/project.json`
- connected the Vercel project to `https://github.com/fawxzzy/DiscordOS.git`
- added non-secret metadata env vars:
  - `DISCORDOS_SUPABASE_URL` for production and development
  - `DISCORDOS_SUPABASE_PROJECT_REF` for production and development
  - current-branch preview values for `codex/path-discipline-warning-slice-discordos`

ATLAS:

- regenerated `stack.lock.yaml`
- regenerated `docs/registry/STACK-REPO-INVENTORY.json`
- regenerated `docs/audits/STACK-REPO-INVENTORY.md`

## Decision

`Discord OS Infrastructure Separation` moves from `95%` to `98%`.

Why:

- the inactive Supabase setup blocker was already cleared
- the Supabase schema-landing blocker is now materially cleared for the feedback runtime contract
- the Vercel project-linkage blocker is now materially cleared
- GitHub/Vercel/Supabase/ATLAS setup state now agrees at the owner-side setup layer
- root lock and inventory now pin the new DiscordOS owner-repo truth

`Discord OS Feedback Workflow Canonicalization` holds at `72%`.

Why:

- schema and Vercel setup are infrastructure proof, not live workflow parity
- no Discord bot/runtime activation occurred
- no Fitness-to-DiscordOS workflow traffic moved
- no live same-event workflow proof widened

## Exact Remaining Blocker Class

`runtime ownership and live workflow parity proof`

More specifically:

- server-side secret provisioning for an executing runtime is not proven
- no DiscordOS deployment exists
- no Edge Function exists
- no bot/runtime activation exists
- no Fitness-to-DiscordOS cutover exists
- no rollback packet exists
- no live workflow parity proof exists after cutover

## Marker Decision

- `Discord OS Infrastructure Separation: 98%`
- `Discord OS Feedback Workflow Canonicalization: 72%`

## Health Check

- no Fitness runtime code was touched
- no Fitness deployment state was changed
- no DiscordOS deployment was created
- no Discord bot/runtime was activated
- no service-role secret was read, printed, invented, or committed
- no `.env` file was created
- local `.vercel/project.json` remains ignored local project linkage metadata
- existing unrelated root screenshots/archive residue stayed untracked

## Rule

Setup linkage plus schema landing can clear infrastructure blockers, but only runtime ownership transfer plus live parity can close the lane at `100%`.

## Pattern

approved owner-side setup -> create/link Vercel -> land private Supabase schema -> pin owner repo -> root lock refresh -> infrastructure marker ratchets -> workflow marker holds until live parity

## Failure Mode

`Infrastructure-As-Parity Overclaim`

If Vercel linkage and private schema landing are treated as a live Discord workflow cutover, the DiscordOS lane falsely reaches `100%` while Fitness still owns live behavior.
