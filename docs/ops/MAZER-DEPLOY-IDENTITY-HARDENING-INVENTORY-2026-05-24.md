# Mazer Deploy Identity Hardening Inventory

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: docs-only inventory
Status: inventory complete

## Goal

Determine whether Mazer already has immutable Vercel project identity guardrails comparable to Fitness and Trove, and define the smallest safe hardening package.

This pass does not deploy, run `vercel link`, pull env, mutate Vercel, mutate Supabase, or change Mazer files.

## Evidence Surfaces

- `repos/mazer/package.json`
- `repos/mazer/README.md`
- `repos/mazer/docs/ops/MAZER_HOSTED_PREVIEW_PROOF.md`
- `repos/mazer/.vercel/project.json`
- `repos/_stack/package.json`
- `repos/_stack/README.md`
- `repos/_stack/config/release-targets.json`
- `repos/_stack/ops/Test-MazerDeployIdentity.ps1`
- `repos/_stack/ops/Invoke-MazerDeploy.ps1`
- `docs/ops/MANUAL-DEPLOY-EXCEPTION-INVENTORY-2026-05-24.md`
- `docs/ops/MANUAL-DEPLOY-EXCEPTION-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/TROVE-DEPLOY-IDENTITY-HARDENING-2026-05-24.md`

## Current Mazer Deploy Shape

### Repo-local state

- Canonical repo path is present at `repos/mazer`
- Git remote is `https://github.com/fawxzzy/fawxzzy-mazer.git`
- Current branch is `codex/mazer-remove-pwa-install-surface`
- Current HEAD is `021291d` (`Remove PWA install surface`)
- Working tree is clean in this session

### Repo-local scripts

Mazer does not declare repo-local deploy scripts in its own `package.json`.

Repo-local scripts stay on app verification and preview:

- `dev`
- `build`
- `preview`
- `verify`
- `lint`
- `test`

That means deploy authority is already centralized in `_stack`, not split across repo-local app scripts.

### `_stack` operator surfaces

Current Mazer deploy commands in `_stack`:

- `mazer:deploy:preflight`
- `mazer:deploy:preview`
- `mazer:deploy-preview`
- `mazer:deploy:prod`
- `mazer:deploy-prod`

Current launcher targets in `_stack/config/release-targets.json`:

- `mazer-preview`
- `mazer-prod`
- `mazer-deploy-preflight`

## Local Vercel Identity Evidence

Mazer already has local Vercel link evidence:

- `orgId`: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `projectId`: `prj_t3zothbtj9DExrh3FjMsH98hwwSZ`
- `projectName`: `fawxzzy-mazer`

Source:

- `repos/mazer/.vercel/project.json`

This is stronger than “identity unknown.” The repo is already locally linked to a concrete Vercel project.

## Current Guardrails

### What is already enforced

`_stack` currently enforces author identity before any Mazer deploy:

- required Git author name: `Zachariah Redfield`
- required Git author email: `zjhredfield@icloud.com`

`repos/_stack/ops/Test-MazerDeployIdentity.ps1` checks:

- `git config user.name`
- `git config user.email`
- latest commit author name
- latest commit author email

This is a real fail-closed preflight, but it governs repo authorship rather than immutable Vercel project identity.

### What is not yet enforced

This pass did **not** find:

- a checked-in Mazer deploy identity config in `_stack/config/`
- an `_stack` preflight that validates `repos/mazer/.vercel/project.json`
- an immutable Mazer Vercel `projectId` contract enforced before preview/prod deploy
- documented Git auto-deploy state for the Mazer Vercel project

So the gap is the same category Trove had before hardening, but with one extra existing safeguard: Mazer already checks commit-author identity.

## Direct Manual Deploy Risks

Current risk is not “no governed path exists.” The governed path already exists in `_stack`.

Current risk is:

- local `.vercel/project.json` could drift to the wrong project without `_stack` noticing
- an operator could still run a Mazer deploy wrapper from `_stack` and satisfy author identity while targeting the wrong linked Vercel project

That makes Mazer weaker than Fitness and now weaker than hardened Trove on project-identity safety.

## Repo-Local Script Ambiguity

This pass did not find repo-local deploy authority ambiguity inside `repos/mazer/package.json`.

Unlike Fitness:

- Mazer does not carry repo-local release or deploy helper scripts that can be mistaken for production deploy authority
- deploy authority is already routed through `_stack`

So the next burn-down package should focus on identity hardening, not wording cleanup.

## Git Auto-Deploy State

Documented Git auto-deploy state was **not** found in the inspected Mazer repo or `_stack` surfaces.

Classification:

- `unknown / not yet pinned in governance docs`

This is not treated as failure in this pass because the inventory is read-only and does not inspect live Vercel settings.

## Comparison to Fitness and Trove

### Fitness

Fitness has:

- immutable Vercel project identity config
- fail-closed `_stack` preflight against `.vercel/project.json`
- documented Git auto-deploy `disabled`

### Trove

Trove now has:

- immutable Vercel project identity config
- fail-closed `_stack` preflight against `.vercel/project.json`

### Mazer

Mazer currently has:

- local `.vercel/project.json` evidence
- fail-closed author-identity preflight
- no pinned immutable Vercel project identity contract in `_stack`

## Recommended Hardening Package

Smallest safe package:

1. add `_stack` config for pinned Mazer Vercel identity
2. add `_stack` preflight that reads `repos/mazer/.vercel/project.json`
3. fail closed if `orgId`, `projectId`, or `projectName` differ from the pinned values
4. wire that preflight before `_stack` Mazer preview/prod deploy wrappers reach Vercel
5. update `_stack` docs and launcher metadata to reflect the stronger preflight

Expected pinned identity from current local evidence:

- `orgId`: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `projectId`: `prj_t3zothbtj9DExrh3FjMsH98hwwSZ`
- `projectName`: `fawxzzy-mazer`

## Recommended Classification

- canonical Mazer Vercel project identity: `known from local link evidence`
- Git auto-deploy state: `unknown / not documented in current governed surfaces`
- `_stack` immutable project identity enforcement: `missing`
- direct manual deploy risk: `present if local Vercel link drifts`
- repo-local script ambiguity: `low`

## Recommendation

The next clean package is:

- `Manual Deploy Exception Burn-Down — Mazer Deploy Identity Hardening`

That package should mirror the Trove hardening shape, while preserving the existing Mazer author-identity preflight as a second guard rather than replacing it.

## No-Deploy Confirmation

This pass did not:

- deploy any app
- run `vercel link`
- pull env
- mutate Vercel
- mutate Supabase
- change Mazer files
