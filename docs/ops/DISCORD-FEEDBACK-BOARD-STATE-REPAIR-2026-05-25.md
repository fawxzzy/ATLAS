# Discord Feedback Board State Repair — 2026-05-25

## Scope

- Repair Discord feedback card board-state hygiene across live source boards and the recovered `completed` board.
- Normalize starter-post reactions so unresolved/non-completed cards show the configured failure emoji and resolved/completed cards show the configured success emoji.
- Normalize forum thread tags and titles where needed.
- Do not move Fitness runtime ownership.
- Do not mutate Supabase schema.
- Do not deploy, restart bots, or post to `#updates`.

## Why this package was needed

- Completed-board copies were missing final state reactions.
- Some completed cards were missing the final tag set.
- The existing `feedback:sync-resolved-reactions` flow only handled success reactions for resolved rows and did not cover unresolved failure reactions or completed-board mirror threads.
- Repo-local Supabase env resolution is currently pointed at `hcjbdxrekkbfbngrfvcv.supabase.co`, while the canonical Fitness project remains `lpswxoyfniocuhljgzbc`. Because the local env path failed to load `discord_feedback_reports`, this repair used the canonical Fitness row set from Supabase MCP and fed that into the new repair script through a local `tmp/` rows snapshot.

## Implementation

Fitness repo changes:

- Added `repos/fawxzzy-fitness/scripts/repair-feedback-board-state.mjs`
- Added `repos/fawxzzy-fitness/scripts/repair-feedback-board-state.test.mjs`
- Added `npm run feedback:repair-board-state`
- Updated `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`

The repair script now:

- scans linked feedback threads plus `completed` board copies
- skips private testing canaries by default
- repairs tag/title/reaction state across both surfaces
- applies `fawxzzy:1507384094424694785` to unresolved/non-completed cards
- applies `fawxzzy:1507384062166302851` to fixed/closed cards
- removes stale opposite reactions and legacy `✅`
- supports `--rows-file` so authoritative row snapshots can be supplied when local Supabase env resolution is not usable
- supports `--sync-body` for future full starter-post body rewrites when a full row payload is available

## Canonical input used for this repair

- Supabase project: `lpswxoyfniocuhljgzbc`
- Row snapshot written to local disposable path:
  - `tmp/discord-feedback-board-state-rows-2026-05-25.json`

This file is runtime residue only and is not a committed source artifact.

## Commands run

In `repos/fawxzzy-fitness`:

```txt
node --test scripts/repair-feedback-board-state.test.mjs
npm run feedback:repair-board-state -- --dry-run --rows-file tmp/discord-feedback-board-state-rows-2026-05-25.json
npm run feedback:repair-board-state -- --apply --rows-file tmp/discord-feedback-board-state-rows-2026-05-25.json
npm run feedback:repair-board-state -- --dry-run --rows-file tmp/discord-feedback-board-state-rows-2026-05-25.json
npm run verify
```

In the ATLAS root (`.`):

```txt
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

## Result

Apply pass:

- `Rows scanned: 35`
- `Rows after testing filter: 31`
- `Thread targets: 38`
- `Repaired threads: 25`
- `Failures: 0`

Follow-up dry-run:

- `Dry-run threads: 0`
- `Failures: 0`

Meaning:

- every reachable non-testing live feedback target is now in the expected title/tag/reaction state
- completed-board copies are also saturated
- old withdrawn rows whose Discord threads no longer exist are treated as skipped missing-thread residue, not active board failures
- one confirmed row (`23af7663-1279-4c84-a275-50140e31b66c`) still has no linked forum thread and therefore had no board target to repair

## Board-state outcome

- non-completed public cards now carry the configured failure emoji on the starter post
- completed public cards now carry the configured success emoji on the starter post
- completed-board copies now align with their final tag sets
- legacy `✅` is removed where present

## Verification

- `node --test scripts/repair-feedback-board-state.test.mjs`: passed
- `npm run verify`: passed
- root validation: [stack-validation.latest.md](../../runtime/receipts/validation/stack-validation.latest.md)
  - `critical=0 error=0 warning=289`

## Non-goals / unchanged

- no Fitness code was copied into DiscordOS
- no DiscordOS runtime migration
- no Supabase schema mutation
- no Vercel mutation
- no bot restart
- no `#updates` post
- no change to unrelated tracked Fitness residue
- no change to `archive/`
