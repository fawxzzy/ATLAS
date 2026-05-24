# Trove Deploy Identity Hardening Inventory

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: docs-only inventory
Status: inventory complete

## Goal

Determine whether Trove already has immutable Vercel project identity guardrails comparable to Fitness, and define the smallest safe hardening package.

This pass does not deploy, run `vercel link`, pull env, mutate Vercel, mutate Supabase, or change Trove files.

## Evidence Surfaces

- `repos/fawxzzy-trove/package.json`
- `repos/fawxzzy-trove/README.md`
- `repos/fawxzzy-trove/.vercel/project.json`
- `repos/_stack/package.json`
- `repos/_stack/README.md`
- `repos/_stack/config/release-targets.json`
- `docs/ops/MANUAL-DEPLOY-EXCEPTION-INVENTORY-2026-05-24.md`
- `docs/ops/MANUAL-DEPLOY-EXCEPTION-DECISION-PASS-1-2026-05-24.md`

## Current Trove Deploy Surface

Repo-local Trove scripts:

- `npm run verify`
- no repo-local deploy scripts

`_stack` Trove wrapper scripts:

- `pnpm run trove:build:vercel`
- `pnpm run trove:deploy:preview`
- `pnpm run trove:deploy:prebuilt`
- `pnpm run trove:deploy:prod`
- `pnpm run trove:deploy:prebuilt:prod`

`_stack` release launcher targets:

- `trove-preview`
- `trove-preview-prebuilt`
- `trove-prod`
- `trove-prod-prebuilt`

## Known Vercel Identity Evidence

Local Trove Vercel linkage exists at:

- `repos/fawxzzy-trove/.vercel/project.json`

Observed values:

- `projectId`: `prj_vhUyajI4AL6BgCF40VnKtdxrBLuV`
- `orgId`: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `projectName`: `fawxzzy-trove`

Known deployed host evidence in repo docs and metadata:

- `https://fawxzzy-trove.vercel.app`

Remote repo identity:

- `https://github.com/fawxzzy/fawxzzy-trove.git`

Current branch in this local session:

- `codex/trove-brand-asset-sync`

## Comparison Against Fitness

Fitness currently has:

- checked-in immutable deploy identity config in `_stack`
- dedicated `_stack` preflight
- dedicated `_stack` doctor command
- explicit Git auto-deploy disable guard
- explicit recovery runbook keyed to immutable `teamId` and `projectId`

Trove currently has:

- approved `_stack` deploy wrappers
- approved release-launcher targets
- repo-local verification before deploy
- local `.vercel/project.json` proving a concrete project link

Trove does not yet show:

- checked-in immutable `_stack` identity config comparable to Fitness
- `_stack` preflight script that validates Trove `orgId` and `projectId`
- `_stack` doctor command for Trove Vercel identity drift
- documented Git auto-deploy state
- a Trove-specific Vercel recovery runbook keyed to immutable IDs

## Current Risk Assessment

### What is already good

- Trove production-capable deploys already flow through `_stack`
- `_stack` release launcher already treats Trove as an approved deploy target
- direct repo-local deploy authority is already weaker than the `_stack` path because Trove has no repo-local deploy scripts

### What is still risky

- `_stack` currently shells into the Trove repo and runs Vercel deploys without proving immutable project identity first
- local `.vercel/project.json` exists, but this pass found no `_stack` guard that treats its `orgId` and `projectId` as enforced deploy truth
- the current local Trove branch is not `main`, so direct repo-local Vercel deploys could bypass any future branch-sensitive release discipline
- Git auto-deploy state is not documented in this pass, so deploy-source ambiguity is not fully burned down

## Direct Manual Deploy Risk

Direct repo-local `vercel` or `vercel --prod` use in `repos/fawxzzy-trove` is still risky because:

- it bypasses `_stack` as the operator surface
- it bypasses launcher-level typed confirmation for production
- it does not currently appear to run an immutable-project-ID preflight
- it could be launched from a non-main working branch like `codex/trove-brand-asset-sync`

Current doctrine should therefore remain:

- use `_stack` `trove:deploy:*` as the approved deploy path
- treat direct repo-local Vercel deploys as a bypass until identity hardening exists

## Repo-Local Script Ambiguity

Trove has less repo-local ambiguity than Fitness because:

- there are no repo-local release bump or deploy scripts that look like production authority
- repo-local scripts are limited to dev, build, lint, smoke, and verify

So the next Trove burn-down slice is not wording clarification first.

It is identity enforcement.

## Recommended Hardening Package

Smallest safe next package:

- add a checked-in Trove deploy identity contract under `_stack`
- add a Trove preflight script under `_stack` that validates:
  - Trove repo path resolves correctly
  - `.vercel/project.json` exists
  - `orgId` matches the expected team ID
  - `projectId` matches the expected project ID
  - `projectName` matches the expected Trove project name
- update `_stack` Trove deploy wrappers to require that preflight before any preview or production deploy
- add a short Trove deploy recovery or identity note in `_stack` docs

Likely file surfaces for that follow-up:

- `repos/_stack/config/trove-deploy.identity.json`
- new `_stack` preflight script for Trove
- `_stack/package.json`
- `_stack/README.md`
- optional `_stack` Trove deploy recovery doc

## Suggested Verification For The Hardening Package

When the hardening package is implemented later, verify with:

- Trove repo-local `npm run verify`
- `_stack` Trove preflight
- root validation

No production deploy should be required for the hardening package itself.

## No-Deploy Confirmation

This pass did not:

- deploy Trove
- run `vercel link`
- mutate `.vercel/project.json`
- pull env
- mutate Vercel
- mutate Supabase
- change Trove or `_stack` scripts

## Inventory Verdict

Trove is not missing project identity entirely.

It already has a real local Vercel project link:

- team `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- project `prj_vhUyajI4AL6BgCF40VnKtdxrBLuV`
- name `fawxzzy-trove`

What is missing is the governance layer that makes `_stack` prove that identity before deploy.

That makes the next correct package:

- **Trove deploy identity hardening implementation**

not another inventory pass.
