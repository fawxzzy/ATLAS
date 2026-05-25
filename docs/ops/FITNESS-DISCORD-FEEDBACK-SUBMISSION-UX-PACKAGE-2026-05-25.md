# Fitness Discord Feedback Submission UX Package - 2026-05-25

## Scope

- Repo: `repos/fawxzzy-fitness`
- Mode: bounded Fitness-owned feedback UX implementation
- No DiscordOS migration
- No Supabase mutation
- No Vercel config mutation
- No bot/runtime ownership change

## Goal

Improve the live Fitness-owned Discord feedback intake so general members submit through a dedicated low-noise launcher surface instead of relying on main-chat command flow, while also making both bug and feature card forms easier to understand.

## Files Changed

- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
- `repos/fawxzzy-fitness/scripts/discord-noise-audit.test.mjs`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions-route.test.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions.test.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions.ts`

## What Changed

- changed the canonical launcher channel target from `submit-feedback` to `feedback-submission`
- taught setup flow to:
  - reuse a configured dedicated launcher channel
  - rename legacy `submit-feedback` channels to `feedback-submission`
  - create `feedback-submission` next to the setup source channel when no dedicated launcher exists
- stopped treating the invoking channel as the default member-facing launcher surface
- improved launcher panel copy so it clearly says:
  - this is for bug reports and feature requests
  - this reduces main-chat clutter
  - public cards remain visible for examples and discussion
  - `Acceptance Criteria` means a plain-language checklist of the outcome wanted
- improved both bug and feature modal guidance, including:
  - better section examples
  - clearer expectations for acceptance criteria
  - cleaner picker wording
  - more explicit optional area/screen labeling
- updated tests and noise-audit coverage to enforce the new dedicated launcher contract
- updated Fitness Discord feedback ops docs to match the new launcher behavior

## Behavior Preservation

Behavior was intentionally preserved by:

- keeping the existing Discord interaction route entrypoint stable
- keeping Fitness as the live runtime owner
- not changing Discord command ownership or moving any runtime into `repos/DiscordOS`
- not changing feedback persistence schema or introducing new Supabase contracts
- not introducing env-file, Vercel-config, or bot-runtime changes

## Verification

From `repos/fawxzzy-fitness`:

```text
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions.test.ts
node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts
node --test scripts/discord-noise-audit.test.mjs
npm run sanity:quick
npm run typecheck
npm run build
```

Results:

- `interactions.test.ts`: passed
- `interactions-route.test.ts`: passed
- `discord-noise-audit.test.mjs`: passed
- `npm run sanity:quick`: passed with the same preexisting lint warnings only
- `npm run typecheck`: passed
- `npm run build`: passed with the same preexisting lint warnings only

## Why No DiscordOS Migration Happened

This package is intentionally Fitness-owned UX work:

- live Discord runtime remains in Fitness
- DiscordOS remains paused at contract/adapter scaffolding only
- this package improves the current submission surface without opening runtime migration, data migration, or ownership cutover

## Live-State Note

This package only changes the code and docs path. It does **not** by itself prove that production has already refreshed the live launcher message in Discord.

Before claiming the member-facing change is live, the stack still needs:

- the Fitness repo commit pushed to the canonical remote
- the production deployment path confirmed healthy
- the feedback launcher refreshed through the existing setup flow in Discord if the prior launcher message is still using older copy

## Unrelated Repo State

The Fitness repo still contains unrelated preexisting tracked changes outside this package, including:

- `package.json`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/sw.js`
- `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `src/generated/appBuildManifest.json`
- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

Those changes remained separate from this feedback-submission package.

## Next Step

The next clean step after this package is proof-backed rollout confirmation:

- push the Fitness repo change
- confirm the deploy path is healthy
- refresh the launcher through the existing Discord setup flow if needed
- then update the live feedback card and post the announcement only after the change is actually live
