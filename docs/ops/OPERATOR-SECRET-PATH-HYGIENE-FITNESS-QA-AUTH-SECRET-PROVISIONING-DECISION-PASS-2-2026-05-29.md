# Operator Secret Path Hygiene Fitness QA Auth Secret Provisioning Decision Pass 2 - 2026-05-29

- Date: `2026-05-29`
- Lane: `Operator Secret Path Hygiene`
- Mode: `docs-only root-bounded decision`
- Inherited package:
  - `root-bounded lane-selection pass after Unified Workflow Convergence consequence pass 2 closeout`
- Inherited blocker shift:
  - `release-readiness evidence freshness blocker`: cleared
  - `linked migration chain drift blocker`: cleared
  - `qa auth secrets blocker`: active, primary
- Root health baseline:
  - `critical=0 error=0 warning=489 info=0`

## Objective

Freeze one compact authoritative decision for how Fitness QA auth secrets are owned, stored, sourced, consumed, and recorded when absent.

This pass does not:

- provision live secrets
- print secret values
- reopen Discord implementation
- reopen Durable Context Externalization, Post-Convergence Lane Split Readiness, `_stack`, Knowledge Capture & Transfer, Inventory & Truth Map, or Dependency Untangling docs ladders
- open any owner-repo implementation lane
- claim authenticated QA is already green

## Exact Surfaces Read

- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/ops/ROOT-BOUNDED-LANE-SELECTION-AFTER-UNIFIED-WORKFLOW-CONVERGENCE-CONSEQUENCE-PASS-2-CLOSEOUT-2026-05-29.md`
- `docs/ops/UNIFIED-WORKFLOW-CONVERGENCE-RELEASE-LEDGER-PUBLISH-BOUNDARY-AND-ROOT-PACKAGING-CONSEQUENCE-PASS-2-2026-05-29.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-APP-LINKED-MIGRATION-CHAIN-REPAIR-AND-REVALIDATION-PASS-3-2026-05-29.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`
- `README-STACK.md`
- `stack.yaml`
- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/scripts/env-file.mjs`
- `repos/fawxzzy-fitness/scripts/qa/fitness-qa-config.mjs`
- `repos/fawxzzy-fitness/scripts/qa/fitness-auth-state.mjs`
- `repos/fawxzzy-fitness/scripts/qa/bootstrap-fitness-auth-state.mjs`
- `repos/fawxzzy-fitness/scripts/qa/fitness-ui-checkpoint.mjs`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-LLEL-CHECKLIST.md`
- key-name-only local inspection of:
  - `secrets/fitness-doctor.env`
  - `secrets/fitness-lps-dev.env`
  - `repos/fawxzzy-fitness/.env.local`
  - `repos/fawxzzy-fitness/.env.prod-local-mirror.example`

## Exact Secret-Bearing Surface Classification

### Authoritative owner and storage surface

`secrets/fitness-lps-dev.env`

This file is the authoritative local secret-bearing storage surface for:

- `FITNESS_QA_EMAIL`
- `FITNESS_QA_PASSWORD`

Why:

- ATLAS root policy says secrets live only in `secrets/`
- the file already exists in the governed root secret lane
- key-name-only inspection confirmed it already carries the QA auth pair
- Fitness env resolution already knows how to read governed root secret files when the repo-default env file is not the active source

### Related but non-authoritative secret surface

`secrets/fitness-doctor.env`

This file remains an allowed governed secret surface, but it is not the authoritative owner for the QA auth pair in this packet.

Observed distinction:

- it carries `FITNESS_ZAC_EMAIL`
- it does not carry `FITNESS_QA_EMAIL`
- it should stay scoped to doctor or Zac-owned local flows unless a later owner-side change proves otherwise

### Allowed consumer surfaces

The QA auth pair may be consumed by the Fitness owner-side QA flow only through the existing local env loading chain:

- `repos/fawxzzy-fitness/scripts/env-file.mjs`
- `repos/fawxzzy-fitness/scripts/qa/fitness-qa-config.mjs`
- `repos/fawxzzy-fitness/scripts/qa/fitness-auth-state.mjs`
- `repos/fawxzzy-fitness/scripts/qa/bootstrap-fitness-auth-state.mjs`
- package scripts:
  - `qa:auth:bootstrap`
  - `qa:auth:check`
  - `qa:fitness:ui-checkpoint`

Interpretation:

- the owner repo may consume the pair
- the owner repo is not the canonical storage owner
- the shell may also provide the pair transiently for a local run, but shell exports are consumption-only and not canonical storage

### Derivative or mirror surfaces

These surfaces may describe or route the secret path without holding live values:

- this decision receipt
- restart or handoff surfaces under `docs/atlas-book/**`
- owner-side blocked-state receipts that record missing env key names only
- tracked example files that stay redacted and non-secret

Tracked example-file caveat:

- `repos/fawxzzy-fitness/.env.prod-local-mirror.example` may remain a placeholder contract only
- it must never become a live mirror for `FITNESS_QA_EMAIL` or `FITNESS_QA_PASSWORD`

### Forbidden live storage or mirror surfaces

Live values for the QA auth pair are forbidden in:

- `repos/fawxzzy-fitness/.env.local`
- `repos/fawxzzy-fitness/.env.production.local`
- `repos/fawxzzy-fitness/.env.prod-local-mirror`
- `repos/fawxzzy-fitness/.env.prod-local-mirror.example`
- any tracked repo file under `repos/fawxzzy-fitness/**`
- ATLAS docs, receipts, runtime, tmp, packages, or data surfaces

Why:

- repo-root `.env*` files are excluded by stack policy and remain non-canonical secret mirrors
- ATLAS root is allowed to classify and route secret posture, not absorb live credentials into committed or exported surfaces

### Blocked or gated surfaces

When the effective env chain does not include the QA auth pair:

- `npm run qa:auth:bootstrap` remains blocked
- `npm run qa:fitness:ui-checkpoint` remains blocked because it shells into `qa:auth:bootstrap`
- owner-side receipts may record the missing env key names
- root may record blocked state only

## Exact Consumer-Path Decision

The current blocker is not canonical storage ambiguity anymore.

The canonical local storage surface already exists:

- `secrets/fitness-lps-dev.env`

The current ambiguity was consumer-path ambiguity:

- `repos/fawxzzy-fitness/.env.local` exists
- key-name-only inspection confirmed that file includes:
  - `FITNESS_ZAC_EMAIL`
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- key-name-only inspection confirmed that file does not include:
  - `FITNESS_QA_EMAIL`
  - `FITNESS_QA_PASSWORD`

Because `repos/fawxzzy-fitness/scripts/env-file.mjs` prefers repo `.env.local` before falling back to root `secrets/`, the active local run path can miss the QA pair even while the governed root secret lane already contains them.

That means:

- ownership is root-governed
- consumption is owner-side
- the remaining unblock work is owner-side consumer-path alignment and proof rerun, not root-side secret storage expansion

## Exact Authoritative Decision

1. `secret ownership`
   - the Fitness QA auth pair is governed by ATLAS root secret-lane policy
   - the authoritative local storage surface is `secrets/fitness-lps-dev.env`

2. `secret storage`
   - live values belong only in ignored local secret files under `secrets/`
   - this packet names `secrets/fitness-lps-dev.env` as the canonical local store for the QA pair

3. `secret consumption`
   - Fitness owner-side QA scripts may consume the pair through:
     - the active shell env
     - or the existing env-file resolution path when it is pointed at the governed root secret file
   - consumer access does not make the repo the storage owner

4. `forbidden live mirrors`
   - repo-root `.env*` files are not the canonical home for the QA pair
   - tracked example files may not carry live values
   - receipts may name missing keys, but may not disclose values

5. `root role when secrets are missing`
   - root may classify the blockage
   - root may name the canonical storage and consumer boundaries
   - root may route the exact next owner-side package
   - root may not provision, copy, mirror, invent, or print live secret values

## Exact Owner-Side Prerequisites Before Authenticated QA May Run

Before authenticated QA runs honestly, the owner-side effective env chain must expose:

- `FITNESS_QA_EMAIL`
- `FITNESS_QA_PASSWORD`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

If repo `.env.local` remains the first-resolved env file and still omits the QA pair, the owner-side run must do one of the allowed consumer actions:

- point `FITNESS_ENV_FILE` at the governed root secret file
- or export the QA pair in the local shell for that run

This pass does not choose between those owner-side consumption mechanics.
It only freezes the canonical ownership and storage rule:

- the QA pair belongs in `secrets/fitness-lps-dev.env`
- not in repo-local `.env*` mirrors

## Exact Blocked-State Behavior When Secrets Are Absent

When the QA pair is absent from the effective env chain:

1. owner-side QA commands may fail with missing env key names only
2. the owner-side repo remains not green for authenticated QA proof
3. root may record the blocked class as `qa auth secrets blocker`
4. `_stack` does not gain authority to bypass the missing local QA secret path
5. Discord implementation and publication remain closed from this packet

## Exact Next Package

`Fitness app QA auth governed secret-lane consumption and authenticated UI checkpoint pass 4`

Why this exact package:

- canonical storage is now frozen
- root no longer needs another docs-only secret-path packet for this blocker class
- the remaining ambiguity is owner-side: make the consumer path use the governed root secret lane or an allowed transient shell source, then rerun authenticated QA proof honestly

This packet supersedes the looser earlier next-package wording that implied fresh provisioning might still be the main question.

## Recommendation Type

`durable with bounded inference`

Durable:

- stack policy explicitly constrains secret storage to `secrets/`
- key-name-only inspection confirmed the QA pair already exists in `secrets/fitness-lps-dev.env`
- repo QA code explicitly names the QA env vars and the env-resolution precedence that can hide them

Inference-bounded:

- the exact owner-side pass label is newly compressed here from the now-frozen storage versus consumption split

## Ratchet Decision

Ratchet:

- `Operator Secret Path Hygiene: 60% -> 61%`

Why:

- this pass materially reduces ambiguity for one active blocker class
- the lane now has an exact authoritative storage surface, an exact consumer chain, an exact forbidden-mirror set, and an exact root blocked-state role for the Fitness QA auth pair
- the move stays to the smallest honest increment because no live secret provisioning was performed, no owner-side consumer rerun happened here, and no broader stack cleanup execution widened

## What This Pass Proves

This pass proves:

- the current Fitness QA auth blocker can be reduced from broad secret-path ambiguity to one exact canonical storage and consumption rule
- ATLAS root already has the governed local secret lane needed for the QA pair
- the remaining next move is owner-side consumer-path alignment plus proof rerun, not another root-only secret policy pass

This pass does not prove:

- that the owner-side effective env chain is already aligned
- that the values in the governed secret lane are current and valid
- that `qa:auth:bootstrap` now passes
- that Fitness is already release-ready

## Rule

When a governed root secret file already owns the needed auth pair, do not reopen storage doctrine or create repo-local mirrors; route the next package into owner-side consumer-path alignment and proof rerun.

## Pattern

active secrets-bound blocker -> confirm governed root owner exists -> separate storage from consumption -> forbid repo-local mirrors -> return the next move to owner-side proof

## Failure Mode

Root sees a missing secret error, assumes storage is still undefined, and opens more doctrine or repo-local mirror work even though the governed root file already owns the keys and the real gap is owner-side consumption precedence.
