# Fitness Discord Live Repair And ATLAS Status Post

Date: 2026-05-25
Owner: Codex
Scope: Fitness production deploy-backed Discord repair and governed ATLAS status post

## Objective

Close the live Discord feedback repair lane by:

- deploying the feedback interaction hardening to production
- correcting the stale feedback launcher channel env drift
- refreshing the live feedback launcher in the canonical `#feedback-submission` channel
- publishing the updated `ATLAS Cleanup & Re-sync Status` post with governed formatting

## Problem Summary

Two operator-facing failures were present:

1. Feedback board buttons were failing live interaction handling.
2. The governed `Update:`/status post path was not preserving the intended section formatting.

An additional drift issue was discovered during closeout:

- production `DISCORD_FEEDBACK_PANEL_CHANNEL_ID` still pointed at a deleted legacy channel, which meant future launcher refresh/setup operations could continue to drift even after the code fix.

## Implementation

### Fitness production hardening

Fitness source changes were already landed in:

- repo: `repos/fawxzzy-fitness`
- commit: `b2e60634049ada23020d7208693c223cbaae7f5d`
- message: `fix: harden discord feedback interactions`

That lane replaced the fragile modal interaction shape with a conservative Discord-compatible modal/action-row flow.

### Direct operator repair paths

Additional Fitness operator hardening was landed in:

- commit: `623089bb06b5245a663557b60b3a09eafb313946`
- message: `feat: add discord operator repair paths`

Files added/updated:

- `repos/fawxzzy-fitness/src/lib/discord/update-post-format.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/scripts/refresh-discord-feedback-launcher.mjs`
- `repos/fawxzzy-fitness/scripts/post-discord-update.mjs`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`

These changes established:

- one shared formatter for governed Discord update posts
- one direct operator launcher refresh path
- one direct operator update-post path

### Production deployments

Clean rollout worktrees were used because the main Fitness worktree contained unrelated tracked residue.

Deployments:

- `dpl_GPhvQKbEkJYFhJzAe5doctYDfCe3`
  - preview/production rollout for the initial live interaction fix
  - commit line: `b2e60634049ada23020d7208693c223cbaae7f5d`
- `dpl_HVQzsgskjj1uWn1zpLfpHT2V9LFc`
  - production rollout for the committed operator repair paths
  - inspected as `Ready`
  - current production target during closeout

Canonical production alias remained:

- `https://fawxzzy-fitness-local.vercel.app`

### Production env drift correction

The production value for `DISCORD_FEEDBACK_PANEL_CHANNEL_ID` was corrected to:

- `1508391092662567013`

This matches the canonical `#feedback-submission` launcher channel.

## Live Discord Actions

### Launcher refresh

First repair run created/updated the launcher and later dry-runs exposed one stale launcher message still present in the canonical channel.

Final live launcher refresh result:

- channel id: `1508391092662567013`
- channel name: `feedback-submission`
- removed stale launcher count: `1`
- created launcher message id: `1508504769470267483`

Final dry-run after refresh:

- source: `configured-env`
- stale launcher messages: `0`

### ATLAS cleanup status post

Governed public post was published to the updates channel with shared formatter output.

Post details:

- title: `ATLAS Cleanup & Re-sync Status`
- updates channel id: `1504671871512346695`
- message id: `1508502768569159854`

Posted sections:

- `What changed`
- `Current markers`
- `Why it matters`

This replaced the prior formatting drift case where the status body could collapse into plain text instead of governed embed sections.

## Verification

### Fitness repo verification

Executed in `repos/fawxzzy-fitness`:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `npm run typecheck`
- `npm run sanity:quick`
- `npm run build`

Result:

- passed
- same preexisting lint warnings remained

### Production verification

Executed with production env pulled from Vercel:

- `vercel inspect https://fawxzzy-fitness-ayotjja8w-fawxzzy.vercel.app`
- `vercel env pull .env.local --environment=production --yes`
- `node --import ./scripts/register-test-aliases.mjs scripts/refresh-discord-feedback-launcher.mjs`
- `node --import ./scripts/register-test-aliases.mjs scripts/refresh-discord-feedback-launcher.mjs --apply`
- `node --import ./scripts/register-test-aliases.mjs scripts/post-discord-update.mjs --title "ATLAS Cleanup & Re-sync Status" --body-file ...`

Result:

- production deployment inspected as `Ready`
- pulled production env resolved the canonical feedback launcher channel
- final launcher dry-run reported `stale launcher messages: 0`
- update post rendered through the governed formatter path

## Outcome

Resolved:

- feedback board button interactions failing in production
- stale launcher duplication in `#feedback-submission`
- governed status/update formatting drift for the ATLAS cleanup post
- stale production feedback panel channel env drift

Not changed:

- no DiscordOS runtime migration
- no Supabase schema or data mutation
- no Vercel stale-surface deletion
- no bot restart
- no archive retention change

## Follow-up

Recommended next package if this surface regresses again:

- run `discord:feedback:launcher:refresh`
- confirm production env channel id first
- use the shared update formatter for any governed post rather than ad hoc Discord body formatting

## State Notes

- root worktree remained on `main`
- only intentional root untracked residue remained: `archive/`
- `archive/` stayed untouched
