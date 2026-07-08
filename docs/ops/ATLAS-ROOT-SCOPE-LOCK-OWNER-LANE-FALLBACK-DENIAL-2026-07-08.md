# ATLAS Root Scope Lock Owner-Lane Fallback Denial - 2026-07-08

## Summary

This receipt hardens the ATLAS-root execution boundary after owner-lane work repeatedly bled into root-governance sessions.

ATLAS root may continue to observe owner-lane repository status for inventory and restart truth, but Fitness, Mazer, Stripe/Vercel launch work, game work, and owner-repo cleanup are not fallback work lanes from ATLAS root.

## Changes

- `AGENTS.md` now states that ATLAS-root sessions are root-governance sessions by default.
- `ops/atlas/codex_hour_block_queue_prompt.py` now emits a `SCOPE LOCK` header in generated hour-block prompts.
- `docs/atlas-book/12-restart-and-handoff-guide.md` now documents the same scope-lock rule for restart use.
- `tests/test_atlas_codex_hour_block_queue_prompt.py` now asserts that generated prompts deny Fitness/Mazer fallback routing.
- `stack.lock.yaml` and published stack inventory were refreshed to match current stack truth after detecting DiscordOS worktree drift.

## Boundary Decision

When selector or planner state reports no immediate ATLAS-root packet:

- stop and report the held root state;
- do not switch to Fitness or Mazer;
- do not select owner-repo dirty cleanup;
- do not discuss Fitness live launch or Mazer game work as active root work;
- mention Fitness and Mazer only as read-only advisory owner-lane inventory status unless the operator explicitly selects that owner lane.

## Validation

- `python -m unittest tests.test_atlas_codex_hour_block_queue_prompt`: passed.
- `python ops/atlas/codex_hour_block_queue_prompt.py --json --output tmp/codex-hour-block.scope-lock-check.json --prompt-output tmp/codex-hour-block.scope-lock-check.md`: passed and emitted the `SCOPE LOCK` header.
- `python ops/validation/validate_stack.py`: passed with `critical=0 error=0 warning=0 info=0` after stack lock resync.
- `python ops/atlas/marker_knockout_selector.py --format json`: reports `operator_action=no_immediate_root_packet`.

## Marker Decision

No marker moves.

Reason: this is a routing and prompt-boundary hardening packet. It prevents owner-lane bleed and preserves restart truth, but it does not land new marker implementation breadth beyond the already-admitted helper family.

## Current Root Posture

- ATLAS root remains the governance/projection/receipts lane.
- Fitness remains a separate owner lane.
- Mazer remains a separate owner lane.
- DiscordOS dirty state is visible in stack truth; it was not mutated by this packet.
