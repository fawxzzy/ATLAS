# Manual Deploy Exception Burn-Down Checkpoint

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: docs-only checkpoint
Status: checkpoint recorded

## Goal

Record the current deploy-authority state after the Fitness, Trove, and Mazer hardening slices, then pause this lane before broader workflow convergence.

This checkpoint does not deploy, mutate Vercel, mutate Supabase, or change deploy scripts.

## Current Deploy-Authority State

### Fitness

- `_stack` owns the approved Fitness preview and production deploy path.
- Fitness repo-local release helpers are now explicitly release-prep or verification surfaces, not deploy authority.
- Direct repo-local `vercel` or `vercel --prod` remains recovery-only and exceptional, not the default operator path.
- Fitness immutable Vercel project identity remains pinned and enforced before deploy.
- Fitness Git auto-deploy is documented as intentionally disabled.

### Trove

- `_stack` owns the approved Trove preview and production deploy path.
- `_stack` now validates pinned local Trove Vercel identity before deploy wrappers can reach Vercel.
- Trove deploy wrappers fail closed if `repos/fawxzzy-trove/.vercel/project.json` is missing or does not match the pinned identity.
- No repo-local Trove app or brand files were needed for this deploy hardening lane.

### Mazer

- `_stack` owns the approved Mazer preview and production deploy path.
- Existing Mazer author-identity preflight remains in place.
- `_stack` now also validates pinned local Mazer Vercel identity before deploy wrappers can reach Vercel.
- Mazer deploy wrappers now fail closed on either:
  - author-identity mismatch, or
  - local `.vercel/project.json` identity drift

## What Is Explicitly Not Approved

- No new manual deploy path is approved by this lane.
- Direct `vercel --prod` remains recovery-only or exceptional, not the default workflow.
- Repo-local release helpers do not become deploy authority by implication.
- No deploy authority moved into `tmp`.

## Hardening Outcomes

This lane materially reduced operator ambiguity and wrong-target deploy risk:

- Fitness deploy authority is explicitly separated from repo-local release-prep helpers.
- Trove deploy wrappers no longer rely on local convention alone; they prove pinned Vercel project identity first.
- Mazer deploy wrappers no longer rely on author identity alone; they now prove pinned Vercel project identity first as well.

## Remaining Gaps

The lane is improved, but not closed:

- Git auto-deploy state for Trove is still not documented in governed surfaces.
- Git auto-deploy state for Mazer is still not documented in governed surfaces.
- `_stack` still has no remote, so `_stack` operator-truth commits remain local-only and must be accepted into ATLAS root lock truth manually.
- Broader workflow convergence has not started.
- Discord update or release-ledger automation is still not unified across deploy lanes.

## Validation State

At this checkpoint:

- no deploy was run
- no Vercel settings were mutated
- no Supabase settings were mutated
- ATLAS root validation is green

Validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## Lane Interpretation

Manual Deploy Exception Burn-Down is no longer in discovery mode and no longer in active narrow hardening mode.

It is now at a governed pause point:

- the strongest current deploy-authority ambiguities were burned down
- the main remaining deploy risks are operational documentation and longer-horizon convergence work
- the next clean move is not another deploy hardening slice by default
- the next clean move is a broader convergence lane when explicitly opened
