# Discord OS Infrastructure Separation Post-99 Bot Token Copy And Service-Role Mismatch - 2026-06-12

- Date: `2026-06-12`
- Lane: `Discord OS Infrastructure Separation`
- Supporting lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `approved one-way secret copy plus blocker recheck`
- Marker posture: `hold at 99% / 72%`
- Vercel project: `fawxzzy-discordos`
- Vercel project id: `prj_C2RSEa34OblHfhuEpVChRQQZSjuG`
- Supabase project: `DiscordOS`
- Supabase ref: `nwexsktuuenfdegzrbut`
- Latest production deployment: `dpl_37XtqBCUmCbwW6vdz6d1jGuvnbYr`

## Objective

Continue the DiscordOS post-99 closeout after explicit operator admission to copy Fitness-scoped secrets into DiscordOS as long as Fitness is not modified, while preserving the boundary that a Fitness Supabase service-role key cannot be treated as a DiscordOS service-role key when its project ref does not match.

## Operator Admission

The operator explicitly allowed copying Fitness-scoped secret values into DiscordOS for this pass, with the constraint that Fitness must not be modified.

Applied boundary:

- one-way copy into DiscordOS/Vercel only
- no Fitness file edits
- no Fitness runtime edits
- no Fitness deployment mutation
- no secret values printed
- no `.env` file created
- no committed secret material

## Secret Handling Result

Copied:

- source key name: `DISCORD_BOT_TOKEN`
- source class: Fitness Discord worker local secret file
- target key name: `DISCORDOS_BOT_TOKEN`
- target surface: Vercel sensitive environment variable for `fawxzzy-discordos`
- target scopes applied: `production` and current preview branch `codex/path-discipline-warning-slice-discordos`

Not copied:

- source key name: `SUPABASE_SERVICE_ROLE_KEY`
- reason: JWT metadata identifies the key as project ref `lpswxoyfniocuhljgzbc`, which is the Fitness Supabase project
- required DiscordOS ref: `nwexsktuuenfdegzrbut`

Vercel rejected a sensitive development-target write for `DISCORDOS_BOT_TOKEN`, so no development sensitive env target is claimed.

## Live Proof

Vercel deployment:

- production deployment: `dpl_37XtqBCUmCbwW6vdz6d1jGuvnbYr`
- state: `READY`
- alias: `https://fawxzzy-discordos.vercel.app`
- serverless function: `api/readiness`

Readiness endpoint:

- endpoint: `https://fawxzzy-discordos.vercel.app/api/readiness`
- `ok: true`
- `runtime: vercel-serverless-function`
- `supabaseProjectRefConfigured: true`
- `supabaseUrlConfigured: true`
- `serviceRoleConfigured: false`
- `discordBotTokenConfigured: true`
- `liveCutover: false`
- `fitnessTrafficMoved: false`

## Decision

`Discord OS Infrastructure Separation` holds at `99%`.

`Discord OS Feedback Workflow Canonicalization` holds at `72%`.

Why no `100%`:

- the DiscordOS bot token is now provisioned for production and current preview, but a DiscordOS Supabase service-role key is still absent
- the available service-role candidates are Fitness project keys, not DiscordOS project keys
- no secret-backed DiscordOS writer has been proven with service-role access to project `nwexsktuuenfdegzrbut`
- no Fitness-to-DiscordOS traffic transfer occurred
- no rollback packet was executed
- no live workflow parity proof exists after transfer

## Exact Remaining Blocker Class

`DiscordOS Supabase service-role key for nwexsktuuenfdegzrbut plus secret-backed writer activation / Fitness-to-DiscordOS traffic transfer / rollback and live workflow parity proof`

## Next Executable Packet

`DiscordOS service-role provisioning and cutover parity packet`

Required proof:

- exact DiscordOS Supabase service-role key exists in Vercel sensitive env as `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY`
- readiness endpoint reports `serviceRoleConfigured: true` and keeps `discordBotTokenConfigured: true`
- DiscordOS writer activation remains bounded to DiscordOS
- rollback route is documented before traffic moves
- one Fitness-to-DiscordOS traffic transfer proof exists
- one live workflow parity proof exists after transfer

## Health Check

- no secret values were printed
- no secret values were committed
- no `.env` file was created
- no Fitness files were modified
- no Fitness deployment was changed
- no Fitness traffic was moved
- DiscordOS Vercel production and current-preview bot-token env were updated
- DiscordOS production readiness was redeployed and verified
- the Fitness Supabase service-role key was rejected as a DiscordOS substitute because its project ref does not match

## Rule

An admitted one-way bot-token copy can clear bot-token configuration, but it does not clear a Supabase service-role blocker when the only available service-role key belongs to the wrong project.

## Pattern

operator-admitted secret copy -> copy only matching runtime secret -> decode service-role metadata without printing values -> reject wrong-project service-role substitute -> redeploy readiness -> preserve exact remaining blocker

## Failure Mode

`Wrong-Project Service-Role Overclaim`

If a Fitness Supabase service-role key is installed as DiscordOS service-role proof, the marker falsely reaches `100%` while DiscordOS still lacks a writer credential for its own Supabase project.
