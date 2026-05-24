# Fitness Discord Worker Poll Interval Tuning

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow repo-local runtime tuning
Status: complete

## Goal

Reduce visible command-response lag when the Discord Gateway worker falls back to polling instead of the immediate `MESSAGE_CREATE` wakeup path.

## What Changed

In `repos/fawxzzy-fitness`:

- `scripts/discord-feedback-gateway-worker.mjs`
  - lowered the default fallback poll interval from `15_000` ms to `5_000` ms
- `scripts/discord-feedback-gateway-worker.test.mjs`
  - updated the default interval expectation to `5_000` ms
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - documented the new `5s` default and the `DISCORD_MESSAGE_COMMAND_POLL_INTERVAL_MS` override

## Boundaries Preserved

- no deploy ran
- no Discord configuration changed
- no Vercel or Supabase state changed
- no public command surface changed
- the immediate `MESSAGE_CREATE` path remains the primary response path

## Result

The worker still behaves the same structurally:

1. immediate `MESSAGE_CREATE` wakeup when the Gateway path is active
2. interval fallback poll when event-driven wakeup is missed or unavailable

The only tuning change is that the fallback poll now wakes every `5s` by default instead of every `15s`, which reduces worst-case wait time without widening authority or changing command semantics.

## Verification

From `repos/fawxzzy-fitness`:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`

Verification outcome:

- targeted worker tests passed
- repo verify passed

## Fitness Commit

- `8a98f9f2389637d5b1182bb83aedfa13747780cb`
- `perf: tighten discord worker fallback poll`
