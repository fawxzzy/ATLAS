# Fitness Discord Worker Message Checkpoint

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow repo-local workflow hardening
Status: complete

## Goal

Tighten the Fitness Discord Gateway worker so it can react quickly to new qualifying Discord messages without relying only on in-memory message ids during the current process lifetime.

This package does not deploy, mutate Discord configuration, mutate Vercel, or change public Discord workflow boundaries.

## What Changed

In `repos/fawxzzy-fitness`:

- `scripts/discord-feedback-gateway-worker.mjs`
  - added persisted message-activity state normalization
  - added recent handled message id trimming
  - added per-channel last seen message checkpoint support
  - added checkpoint comparison logic so older or already-seen qualifying messages are skipped after restart
  - persisted checkpoint updates into the existing worker state file after qualifying message handling
- `scripts/discord-feedback-gateway-worker.test.mjs`
  - added focused tests for persisted message-activity normalization
  - added focused tests for recent-message trimming
  - added focused tests for checkpoint comparison behavior
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - documented that the worker now triggers an immediate secured poll on qualifying `MESSAGE_CREATE` events
  - documented that recent handled message ids plus last seen timestamp/id per channel are persisted in `runtime/state/discord-feedback-worker-state.json`

## Result

The Fitness Discord worker already had two useful response paths:

1. interval fallback poll of the secured message-command endpoint
2. immediate `MESSAGE_CREATE` trigger that wakes the poll path early

Before this package, duplicate protection was split between:

- in-memory `seenMessageIds` inside the live worker process
- processed reactions inside the poll endpoint

That meant restart behavior still leaned on runtime memory plus downstream idempotency.

After this package:

- the worker still uses the existing fast `MESSAGE_CREATE` trigger
- the worker still keeps the interval fallback poll
- the worker now persists recent handled message ids and per-channel last seen timestamp/id checkpoints
- restart behavior is cleaner because the worker no longer starts from an empty in-memory trigger history

## Boundaries Preserved

- no Discord post was published by this package
- no bot command surface changed
- no deploy authority changed
- no Vercel or Supabase state changed
- no Discord board/review/update doctrine changed

## Verification

From `repos/fawxzzy-fitness`:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `node scripts/playbook-runtime.mjs --install-official-fallback`
- `npm run verify`
- `npm run sanity:quick`

Verification outcome:

- targeted worker tests passed
- repo verify passed after installing the canonical official Playbook fallback runtime
- `sanity:quick` completed with the repo's existing lint-warning set and no new failures

## Fitness Commit

- `2f07fcb5325dadb303e19431ee7326540db90c77`
- `feat: persist discord worker message checkpoints`

## Why This Matters

This keeps the Discord workflow lane aligned with the same fail-closed and explicit-handoff posture used elsewhere in the stack:

- faster response remains event-driven
- fallback polling still exists
- restart behavior no longer depends purely on process memory
- duplicate command handling stays bounded instead of ad hoc
