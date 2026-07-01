# Fitness Discord Live Update Workflow Surfacing - 2026-06-30

## Scope

- make the already-correct Fitness Discord live-update path discoverable at session start
- stop future Codex chats from repeatedly misclassifying Fitness Discord work as blocked just because no generic Discord connector is surfaced

## Why

The canonical live-update path already existed in:

- `docs/ops/FITNESS-DISCORD-ACCESS-PATH-2026-06-18.md`

But future sessions were still falling into the same failure mode:

- treating `no first-class Discord connector` as `no live Discord update path exists`
- defaulting to browser-control reasoning before proving the DiscordOS bot path

That was a retrieval and startup-guidance failure, not a missing capability.

## Executed Proof

Re-proved the canonical live path from `repos/DiscordOS`:

- `npm run ops:production-env:run -- npm run ops:discordos:env-readiness:json`

Result:

- readiness returned `status: ready`
- updates target is ready
- alerts target is ready
- no blocked readiness checks remained

## Changes

Surfaced the rule into the files future sessions actually read first:

1. `AGENTS.md`
   - now explicitly routes Fitness Discord forum-card and `#updates` work through the DiscordOS readiness proof before any browser fallback claim

2. `AGENTS.md`
   - root startup guidance now points Fitness Discord work at the DiscordOS readiness proof and the canonical access-path doc

3. `repos/fawxzzy-fitness/AGENTS.md`
   - now explicitly tells repo-local sessions to read the Fitness Discord access doc and run the DiscordOS readiness proof before claiming a browser-control blocker

4. `repos/DiscordOS/AGENTS.md`
   - now declares this repo as the canonical admitted bot-publication path for live Fitness Discord mutations when readiness is `ready`

5. `docs/ops/FITNESS-DISCORD-ACCESS-PATH-2026-06-18.md`
   - now carries a fresh `2026-06-30` verified-state note tying the rule to the latest readiness proof and the startup-guidance surfaces above

## Result

The durable rule is now:

1. Need live Fitness Discord mutation
2. Read the Fitness Discord access path doc
3. Enter `repos/DiscordOS`
4. Run the readiness proof
5. If `status: ready`, use the repo-owned DiscordOS bot command path
6. Only after that fails may browser or desktop fallback be treated as the blocker path

## Boundaries

- This pass did not invent a new generic Discord connector
- this pass did not mutate live Discord content by itself
- this pass fixed the repeated workflow/doctrine failure so future sessions stop claiming the wrong blocker first
