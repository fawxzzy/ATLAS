# Manual Deploy Exception Decision Pass 1

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: docs-only decision pass
Status: recommendation ready

## Goal

Choose the first narrow burn-down package after the deploy-path inventory, without changing scripts, deploying, or mutating Vercel or Supabase.

Compared in this pass:

1. Fitness repo-local release-script authority clarification
2. Trove deploy identity hardening
3. Mazer deploy identity hardening

## Inputs

- `docs/ops/MANUAL-DEPLOY-EXCEPTION-INVENTORY-2026-05-24.md`
- `repos/_stack/package.json`
- `repos/_stack/config/release-targets.json`
- `repos/_stack/README.md`
- `repos/_stack/docs/fitness-verify.md`
- `repos/_stack/docs/ops/fitness-vercel-deploy-recovery.md`
- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/docs/COMMANDS.md`
- `repos/fawxzzy-fitness/docs/LOCAL-PROD-DATA-SYNC.md`
- `repos/fawxzzy-trove/package.json`

## Decision Criteria

Each candidate is compared by:

- risk reduced
- likely files touched
- verification needed
- rollback shape
- whether it blocks convergence
- whether it changes runtime or deploy behavior

## Candidate Comparison

| Candidate | Risk reduced | Likely files touched | Verification | Rollback | Convergence impact | Runtime or deploy behavior touched |
| --- | --- | --- | --- | --- | --- | --- |
| Fitness release-script authority clarification | High | Fitness docs, `_stack` docs, possibly Fitness command glossary wording | docs consistency plus root validation | trivial docs rollback | high; removes the main remaining human-authority ambiguity in the strongest governed deploy lane | no, if kept to docs and wording only |
| Trove deploy identity hardening | High | `_stack` config, `_stack` scripts, Trove docs, possibly new identity config or guard script | root validation plus deploy-preflight proof | moderate; touches operator scripts and contracts | medium-high; strengthens Trove production governance | yes; operator deploy path would change |
| Mazer deploy identity hardening | Medium-high | `_stack` config, `_stack` scripts, Mazer docs, possibly new identity config or guard script | root validation plus preflight proof | moderate; touches operator scripts and contracts | medium; strong but narrower repo impact | yes; operator deploy path would change |

## Candidate Analysis

### 1. Fitness release-script authority clarification

Current state:

- Fitness already has the strongest deploy governance in the stack
- `_stack` owns preview and production deploy commands
- immutable Vercel team and project identity is already pinned
- Git auto-deploy creation is already intentionally disabled

Remaining problem:

- repo-local commands such as `npm run release:patch`, `release:minor`, and `release:major` can still look like deploy authority if an operator reads them without the `_stack` deploy doctrine in view
- older or broad wording around manual Vercel CLI deploys can still be misread as normal release procedure instead of recovery-only exception handling

Risk reduced:

- directly lowers the chance that an operator treats repo-local semver or release-note commands as production deploy entrypoints
- directly addresses the historical wrong-repo or wrong-path deploy failure mode without reopening Vercel or runtime logic

Likely package shape:

- docs-only or docs-plus-command-description wording
- should not require a Vercel test or deploy run

Why it should go first:

- highest leverage for the least operational risk
- cleans up the strongest deploy lane before expanding the same doctrine to weaker lanes

### 2. Trove deploy identity hardening

Current state:

- Trove deploys already route through `_stack`
- repo-local verification exists
- release launcher exposes approved preview and prod targets

Remaining problem:

- this pass did not find immutable project-ID style proof comparable to Fitness
- current deploy governance is thinner and relies more on wrapper convention than identity contract

Risk reduced:

- would improve production trust for Trove
- would reduce the chance of wrong-project or wrong-link deploys later

Why not first:

- it changes operator deploy behavior
- it needs new guard surfaces, config, or scripts
- it is a larger package than the remaining Fitness wording ambiguity

### 3. Mazer deploy identity hardening

Current state:

- Mazer already has owner-author Git preflight and `_stack` deploy wrappers
- launch and preflight surfaces are explicit

Remaining problem:

- identity proof is focused on Git authorship, not immutable Vercel project identity

Risk reduced:

- would make Mazer deploy governance more symmetric with Fitness

Why not first:

- same reason as Trove: it likely requires new script or config work
- it does not remove the currently more likely operator misunderstanding in Fitness docs and release helpers

## Recommendation

Pick exactly one first package:

- **Fitness release-script authority clarification**

## Recommended First Package Shape

Bounded goal:

- make it impossible to read Fitness repo-local release helpers as production deploy authority

Likely scope:

- `repos/fawxzzy-fitness/docs/COMMANDS.md`
- `repos/fawxzzy-fitness/docs/LOCAL-PROD-DATA-SYNC.md`
- `repos/_stack/docs/fitness-verify.md`
- `repos/_stack/docs/ops/fitness-vercel-deploy-recovery.md`
- possibly one short ATLAS receipt if the lane needs cross-repo closeout context

Expected changes:

- explicitly label `release:patch`, `release:minor`, and `release:major` as versioning or release-prep helpers only
- explicitly restate that `_stack` `fitness:deploy:*` commands are the only approved preview and production deploy authority
- explicitly state that direct repo-local `vercel` or `vercel --prod` is recovery-only, not routine release workflow

Expected verification:

- docs consistency review
- repo-local or root validation as applicable
- no deploy run required for the clarification package itself

Expected rollback:

- revert wording if it overstates current automation reality
- no runtime or deploy rollback needed because the recommendation is intentionally docs-first

## Recommended Package Order After This Pass

1. Fitness release-script authority clarification
2. Trove deploy identity hardening
3. Mazer deploy identity hardening

## Marker Interpretation

After this decision pass:

- `Manual Deploy Exception Burn-Down`
  - `10%`

Reason:

- the lane has moved from broad inventory to a short ranked burn-down queue
- no actual deploy exception has been removed yet

## No-Deploy Confirmation

This pass did not:

- deploy any app
- change Vercel settings
- pull env
- mutate Supabase
- change package scripts

## Decision Verdict

The first burn-down package should not be new deploy automation.

It should be a narrow clarification package that makes Fitness release-script authority unambiguous:

- repo-local release helpers are not deploy authority
- `_stack` is the only approved deploy authority for Fitness preview and production
- direct repo-local Vercel deploys remain recovery-only exceptions
