# Discord OS Infrastructure Separation Post-99 Connector-Backed Service-Role Blocker Proof - 2026-06-12

- Date: `2026-06-12`
- Lane: `Discord OS Infrastructure Separation`
- Supporting lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `connector-backed live blocker proof`
- Marker posture: `hold at 99% / 72%`
- Supabase project: `DiscordOS`
- Supabase ref: `nwexsktuuenfdegzrbut`
- Vercel project: `fawxzzy-discordos`
- Vercel project id: `prj_C2RSEa34OblHfhuEpVChRQQZSjuG`
- GitHub repo: `fawxzzy/DiscordOS`

## Objective

Continue the DiscordOS closeout path using the Supabase, Vercel, and GitHub connected surfaces to determine whether the lane can honestly move to `100%` after the bot-token copy, without using a Fitness Supabase service-role key as a DiscordOS substitute.

## Live Connector Proof

Supabase:

- project `DiscordOS` exists and is `ACTIVE_HEALTHY`
- project ref is `nwexsktuuenfdegzrbut`
- project URL exists at the DiscordOS ref
- private schema `discordos` exists
- RLS-enabled feedback runtime contract tables exist:
  - `discordos.discord_feedback_reports`
  - `discordos.discord_feedback_audit_events`
  - `discordos.discord_feedback_completion_reviews`
- migrations exist:
  - `20260612082758 discordos_feedback_runtime_schema_v1`
  - `20260612082854 discordos_set_updated_at_search_path`
- Edge Function `discordos-readiness` exists and is `ACTIVE`
- Edge Function `verify_jwt` is `true`
- publishable/anon keys are available, but no service-role key was exposed by the connected app

Vercel:

- project `fawxzzy-discordos` exists
- latest production deployment is `dpl_37XtqBCUmCbwW6vdz6d1jGuvnbYr`
- latest production deployment state is `READY`
- production env contains:
  - `DISCORDOS_BOT_TOKEN`
  - `DISCORDOS_SUPABASE_PROJECT_REF`
  - `DISCORDOS_SUPABASE_URL`
- production env does not contain `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY`
- runtime logs show successful `GET /api/readiness` responses with status `200`

Readiness endpoint:

- endpoint: `https://fawxzzy-discordos.vercel.app/api/readiness`
- `ok: true`
- `supabaseProjectRefConfigured: true`
- `supabaseUrlConfigured: true`
- `serviceRoleConfigured: false`
- `discordBotTokenConfigured: true`
- `liveCutover: false`
- `fitnessTrafficMoved: false`

GitHub:

- repo `fawxzzy/DiscordOS` exists
- connector reports admin, maintain, pull, push, and triage permissions
- repo is public and not archived

Local redacted key-name scan:

- no `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY` key name was found under the admitted local search surfaces
- only Fitness-scoped `SUPABASE_SERVICE_ROLE_KEY` entries were found
- no secret values were printed

## Decision

`Discord OS Infrastructure Separation` holds at `99%`.

`Discord OS Feedback Workflow Canonicalization` holds at `72%`.

Why:

- the DiscordOS bot token is configured, but the DiscordOS Supabase service-role key is not
- Supabase connector proof verifies the DiscordOS project is healthy and schema-ready, but exposes only publishable/anon key classes, not service-role secret material
- Vercel production env confirms `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY` is absent
- a publishable or anon key is not an acceptable service-role substitute
- no DiscordOS writer activation exists
- no Fitness-to-DiscordOS traffic transfer occurred
- no rollback packet was executed
- no live workflow parity proof exists after transfer

## Exact Remaining Blocker Class

`DiscordOS-owned Supabase service-role provisioning for project nwexsktuuenfdegzrbut, followed by secret-backed writer activation, Fitness-to-DiscordOS traffic transfer, rollback proof, and live workflow parity proof`

## Next Executable Packet

`DiscordOS service-role provisioning and cutover parity packet`

The packet becomes executable only after one safe secret path provides the exact DiscordOS service-role value:

- Vercel dashboard sensitive env write for `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY`, or
- one local process env value named `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY` for a Codex turn, or
- a Supabase management path that can mint or retrieve the DiscordOS project service-role secret without printing it

Required proof after provisioning:

- Vercel production env contains `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY`
- readiness endpoint reports `serviceRoleConfigured: true`
- readiness endpoint keeps `discordBotTokenConfigured: true`
- writer activation is bounded to DiscordOS
- rollback route is documented before traffic moves
- one Fitness-to-DiscordOS traffic transfer proof exists
- one live workflow parity proof exists after transfer

## Health Check

- no Fitness files were modified
- no Fitness deployment changed
- no Fitness traffic moved
- no secret values were printed
- no `.env` file was created
- no repo code was changed
- DiscordOS setup surfaces stayed healthy
- ATLAS root remains the receipt and marker surface only

## Rule

Connector-backed setup proof cannot substitute for a missing service-role secret.

## Pattern

bot token configured -> connector-backed project health proof -> Vercel env absence proof -> publishable-key non-substitution -> exact blocker preserved

## Failure Mode

`Publishable-Key Last-Percent Overclaim`

If an anon or publishable key is treated as service-role evidence, DiscordOS appears to reach `100%` while the service cannot perform the privileged writer work required for cutover.
