# DiscordOS Feedback Contract Scaffold Package 1 - 2026-05-25

## Scope

- Repo: `repos/DiscordOS`
- Mode: contract/interface scaffold only
- No Fitness code copy
- No Supabase mutation
- No Vercel mutation
- No bot/runtime behavior
- No env files

## Goal

Create the first DiscordOS-owned feedback-domain contract surface so future Fitness-to-DiscordOS extraction can target a stable seam instead of copying Fitness-hosted implementation.

## Inputs

- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`

## Repo Readiness Decision

DiscordOS is still governance-first and does not yet have a TypeScript/runtime scaffold.

Decision:

- use the docs-only scaffold path
- do not create `src/contracts/feedback.ts` yet
- do not introduce package tooling only to hold interface files

## Files Changed

- `repos/DiscordOS/README.md`
- `repos/DiscordOS/docs/README.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`

## Contract Surface Added

The scaffold defines documentation contracts for:

- feedback card identity
- feedback status lifecycle
- feedback audit/comment event
- completion review event
- Fitness-owned report-row reference
- DiscordOS-owned future runtime state
- error/fallback response shape
- later adapter/port boundaries

## What Did Not Happen

This package intentionally did **not**:

- copy `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/**`
- copy `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- add a database client
- add Supabase schema
- add Vercel config
- add bot runtime code
- add `.env` files
- add runtime dependencies

## Verification

From `repos/DiscordOS` before changes:

- `git status --short`: clean

From `repos/DiscordOS` after changes, before commit:

- only expected changed files were:
  - `README.md`
  - `docs/README.md`
  - `docs/contracts/feedback-runtime.md`

Additional checks:

- `.env*` files present in `repos/DiscordOS`: `0`
- no Fitness application files were copied into the repo
- no package/runtime tooling was introduced

From ATLAS root:

```text
python .\ops\validation\validate_stack.py --allow-missing-locked-repos
```

Result:

- root validation passed: `critical=0 error=0 warning=289`

## Stack Metadata Decision

- no `stack.yaml` change was required
- no `stack.lock.yaml` change was required

Reason:

- `repos/DiscordOS` was already registered during the bootstrap lane
- this scaffold only adds repo-local docs and contract intent

## Result

DiscordOS now has a governed feedback-domain contract scaffold without prematurely inheriting Fitness implementation, runtime assumptions, or data ownership.

## Next Safe Move

The next clean package is still narrow:

- a small code-facing contract/interface package in `repos/DiscordOS` only if the repo is intentionally tooled for it, or
- a later extraction package that maps Fitness adapters to these contracts without copying the live runtime wholesale
