## Fitness Discord Setup Panel Green Embed Alignment

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow live format cleanup
Status: complete

### Goal

Bring the Feedback and Music Sesh setup posts back onto the same green embed contract used by governed Discord updates and command cards.

### Root Cause

The two setup surfaces were not using the same embed color rules:

- the Feedback launcher embed did not set a color at all
- the Music Sesh panel used green only when the room was open and blue when closed

That created visible drift in `#main` even though the intended Discord OS format is the standard green left strip.

### What Changed

In `repos/fawxzzy-fitness`:

- `src/lib/discord/interactions.ts`
  - Feedback launcher embed now sets `DISCORD_EMBED_COLOR_SUCCESS`
  - Music Sesh public panel now always sets `DISCORD_EMBED_COLOR_SUCCESS`
- `src/lib/discord/interactions.test.ts`
  - added a Feedback panel color assertion
  - added a closed-lobby Music Sesh color assertion

### Live Deploy

Fitness production was deployed on the canonical Vercel project:

- deployment id: `dpl_ETwuRu3E2YWjgpRVJUrE9siQs8kT`
- production alias: `https://fawxzzy-fitness-local.vercel.app`

### Live Discord Cleanup

Existing live posts were refreshed to the green embed color:

- Feedback setup post
  - channel: `1504674484068552784`
  - message: `1508177094415220848`
- Music Sesh setup post
  - channel: `1504674484068552784`
  - message: `1508171437549289542`

Verification by Discord API readback:

- both setup posts now report embed color `2278750` (`0x22c55e`)

### Update Post

Published community update:

- channel: `1504671871512346695`
- message: `1508184313253073037`
- title: `Discord Community Update`
- embed color: `2278750` (`0x22c55e`)

### Verification

From `repos/fawxzzy-fitness`:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions.test.ts`
- `npm run verify`

Live checks:

- deployed route is live on the production alias
- Feedback setup post reports green embed color
- Music Sesh setup post reports green embed color
- updates post reports green embed color

### Fitness Commit

- `072fb3c04db1d84717ca1635895fed27ea7373da`
- `fix: keep discord setup panels on green embeds`
