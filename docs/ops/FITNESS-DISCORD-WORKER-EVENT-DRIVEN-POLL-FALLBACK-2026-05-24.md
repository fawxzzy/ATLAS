## Fitness Discord Worker Event-Driven Poll Fallback

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: narrow repo-local runtime optimization
Status: complete

### Goal

Reduce Vercel Fluid Active CPU driven by the Fitness-hosted Discord OS worker without widening authority or changing the command surface.

### Root Cause

The Fitness Discord Gateway worker was still running an always-on fallback poll against `GET /api/discord/interactions` every `5s`, even when the Discord Gateway session was healthy.

Observed stack shape during investigation:

- the Vercel route was the dominant sampled runtime traffic path
- the local worker log showed repeated `reason: 'interval'` polls after `gateway ready`
- two local long-lived worker-shaped Node processes were present:
  - one gateway-connected worker
  - one stale poll-only worker still driving repeated Vercel traffic

This meant Vercel CPU was being consumed by Discord OS polling behavior inside Fitness rather than by normal product browsing.

### What Changed

In `repos/fawxzzy-fitness`:

- `scripts/discord-feedback-gateway-worker.mjs`
  - raised the default fallback interval from `5s` to `30s`
  - removed steady-state startup interval polling
  - added a gateway-ready watchdog
  - runs one startup catch-up poll
  - clears fallback polling as soon as the Discord Gateway reports `READY`
  - enables fallback polling only when the gateway never becomes ready or later disconnects
- `scripts/discord-feedback-gateway-worker.test.mjs`
  - updated the default interval expectation to `30s`
  - added lifecycle tests for:
    - startup catch-up without steady-state fallback polling
    - `READY` clearing fallback polling
    - disconnect re-enabling fallback polling
- `docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - updated the runtime contract to match the new event-driven behavior

### Runtime Repair

Local Discord worker runtime was normalized after the code change:

- stopped the gateway-connected worker that was still running the old script
- stopped the stale poll-only worker that continued to hit the Vercel route
- relaunched one clean worker using a local secret env snapshot at:
  - `secrets/local/fawxzzy-fitness-discord-worker.env`

Post-restart behavior at idle:

- env file loads successfully
- gateway connects successfully
- one startup poll runs
- no repeated interval polling occurs while the gateway stays healthy

### Boundaries Preserved

- no Discord command semantics changed
- no new Discord role or channel authority was introduced
- no Vercel project settings changed
- no Supabase schema or data changed
- no deploy was required because the optimization lives in the local worker script

### Verification

From `repos/fawxzzy-fitness`:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`

Live local runtime proof:

- worker log shows:
  - env load
  - gateway socket open
  - gateway ready
  - one startup poll completion
- worker log does not continue with repeated `reason: 'interval'` entries after the gateway becomes healthy

### Result

The Fitness Discord OS worker is now event-driven during normal healthy operation.

Expected CPU effect:

- the old idle shape could hit the Vercel route about every `5s`
- the new idle shape performs:
  - one startup catch-up poll
  - one optional gateway-ready catch-up if startup is not already in flight
  - no steady-state polling unless the gateway fails

This removes the constant idle Vercel poll load while preserving a safe fallback path when the gateway is unhealthy.

### Fitness Commit

- `cd1eb19cea15156697d4564364c10c91ba7f965d`
- `perf: prefer event-driven discord worker polling`
