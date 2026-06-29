# Inventory And Truth Map And ATLAS Book Fitness Auth Return And QA Proof Hardening Re-Sync

## Scope

- preserve the current owner truth after the latest Fitness auth-recovery and protected-route proof hardening landed on a clean pushed head
- capture the exact distinction between governed QA proof state and ad hoc in-app browser state so future passes do not misclassify auth-context drift as a product regression
- record the current DiscordOS operator posture for this lane without claiming a live feature-card mutation that did not occur in this pass

## Why

The latest Fitness lane changed real proof behavior again:

- `repos/fawxzzy-fitness` advanced to pushed clean head `7d8163d2` on `codex/fitness-main-progression-summary-reapply`
- auth recovery now preserves protected-route return targets instead of dropping users back onto generic entry paths
- the visual proof runner now prefers fresh QA session state over stale cached browser storage, which removes a false proof path where protected suites silently fell back into the wrong local-dev user

Without a root receipt, future chats can easily confuse three different states:

1. the real product behavior on the protected route
2. the governed QA runner behavior with a seeded QA session
3. an unrelated in-app browser tab that is not seeded with the same auth state

## Executed Proof

### Owner-side preserve recheck

- repo: `repos/fawxzzy-fitness`
- branch: `codex/fitness-main-progression-summary-reapply`
- current pushed clean head: `7d8163d2`
- preserve chain landed:
  - `5c93a128` - `Preserve auth return targets across login recovery`
  - `7d8163d2` - `Prefer live QA session auth in visual runner`

### Verified command proof

From `repos/fawxzzy-fitness`:

- `node --import ./scripts/register-test-aliases.mjs --test src/app/auth/session-recovery/route.test.ts src/lib/auth-session.test.ts`
- `npm run typecheck`
- `npm run verify`
- `npm run qa:dev:fresh`
- `npm run visual:fitness:session`
- `npm run visual:fitness:today`
- `npm run visual:fitness:routines`
- `npm run visual:fitness:workout-plans`
- `npm run visual:fitness:history`

Result:

- focused auth tests passed
- repo typecheck passed
- repo verify passed
- protected visual suites captured successfully under the governed QA user instead of drifting into the default local-dev profile

### Proof captures

Governed QA proof artifacts:

- session
  - `tmp/captures/fitness/session/2026-06-29-07-48-44/session.png`
- today
  - `tmp/captures/fitness/today/2026-06-29-07-49-25/today.png`
- routines
  - `tmp/captures/fitness/routines/2026-06-29-07-49-59/routines.png`
- workout plans
  - `tmp/captures/fitness/workout-plans/2026-06-29-07-50-35/workout-plans.png`
- history
  - `tmp/captures/fitness/history/2026-06-29-07-51-09/history.png`

### In-app browser cross-check

Live in-app browser inspection on `127.0.0.1:3002` showed:

- public or broadly reachable surfaces like `/today`, `/routines`, and `/routines/workout-plans` render normally
- a direct in-app browser navigation to the protected session route did not stay on the protected session surface because that browser tab was not seeded with the governed QA auth state used by the proof runner

Interpretation:

- this is not current evidence of a product regression in the preserved auth-return path
- it is evidence that ad hoc in-app browser state and governed QA-runner state are different proof environments and must not be conflated

## Current Truth

- Fitness auth recovery now preserves safe `returnTo` targets through:
  - session recovery
  - login entry
  - local-dev auto-login handoff
- the protected-route auth path now keeps users pointed at the original requested destination instead of dropping them onto a generic post-login screen
- the visual proof runner now prefers the fresh QA session artifact over stale cached browser storage, preventing silent user-context drift during protected-route proof
- the clean pushed owner head for this lane is `7d8163d2`
- the owner worktree is clean and synced to origin

## DiscordOS Operator Posture

- live DiscordOS operator readiness was re-proved from `repos/DiscordOS` with:
  - `npm run ops:production-env:run -- npm run ops:discordos:env-readiness:json`
- result remained `status: ready`
- this pass did not perform a live feature-card mutation or updates-channel publication because the current slice was proof and auth hardening, not a user-facing shipped feature-state transition

## Marker Decision

- `Inventory & Truth Map` stays ratcheted by current June 29 owner truth and absorbs this receipt as the latest Fitness proof-hardening checkpoint
- `Truth Map & ATLAS Book` stays open because this pass tightened proof reliability and restart truth, but it did not widen broader operator automation or clear a standing cross-lane blocker family

## Next Honest Moves

1. Reuse the governed QA runner, not an unseeded browser tab, when proving protected Fitness routes.
2. If future work needs live in-app browser proof on protected routes, bootstrap that browser with the same admitted QA auth state first.
3. Reopen Discord thread mutation work only when there is a real feature-card state change or user-facing release note worth publishing.
