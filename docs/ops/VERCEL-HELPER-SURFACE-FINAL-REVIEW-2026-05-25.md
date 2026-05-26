# Vercel Helper Surface Final Review

- Date: `2026-05-25`
- Lane: `Duplicate Surface Decommission / Manual Deploy Exception Burn-Down`
- Mode: `read-only dependency review`

## Scope

Review the two remaining Vercel helper surfaces after the stale Spotify-era project cleanup:

- `fitness-deploy-green-panels`
- `fitness-prod-rollout-20260525`

This pass does not:

- delete the canonical `fawxzzy-fitness` project
- mutate Supabase
- deploy
- touch Discord
- change app code
- remove aliases from the canonical active project

## Inputs

- `docs/ops/VERCEL-STALE-SURFACE-DECOMMISSION-INVENTORY-2026-05-24.md`
- `docs/ops/VERCEL-STALE-SURFACE-DELETION-READINESS-2026-05-25.md`
- `docs/ops/VERCEL-STALE-SURFACE-DELETION-2026-05-25.md`
- `docs/ops/FULL-STACK-RESYNC-CLEAN-CLOSEOUT-BASELINE-PASS-2-2026-05-25.md`
- local Fitness / ATLAS / DiscordOS docs and code reference search
- live Vercel CLI metadata

## Tooling Note

The Vercel MCP connector token was expired during this pass.

Live metadata was gathered instead through the authenticated local Vercel CLI:

- `vercel --version`
- `vercel whoami`
- `vercel project ls --scope team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `vercel project inspect <project> --scope team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `vercel list <project> --scope team_CMJn7MvzFZZBnhNnjVUZF2RD`

Deletion tooling does exist locally:

```powershell
vercel project remove <name> --scope team_CMJn7MvzFZZBnhNnjVUZF2RD
```

## Canonical Active Comparison Surface

Canonical Fitness project:

- name: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- team id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- latest production alias: `https://fawxzzy-fitness-local.vercel.app`
- latest production deployment inspected: `dpl_HkG1JZyXqH6fMmFnuG2gMWk9N69z`
- latest production deployment age at review time: `1h`

## Helper Surface Table

| Project | Project ID | Latest deployment | Latest deployment URL | Production alias set | Status | Age at review | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fitness-deploy-green-panels` | `prj_pDHtigVQI2m3RWswnq3q7rJ890UT` | `dpl_GxNANEzc6EsrbK7PBNv1eiiNVmdu` | `https://fitness-deploy-green-panels-e8dlyhspq-fawxzzy.vercel.app` | `fitness-deploy-green-panels.vercel.app`, `fitness-deploy-green-panels-fawxzzy.vercel.app`, `fitness-deploy-green-panels-zachariahredfield-fawxzzy.vercel.app` | Ready / Production | `23h` | retain temporarily |
| `fitness-prod-rollout-20260525` | `prj_FR600ERe6GtvnNsb7EeDt0O5oX8u` | `dpl_57T5sTFC6MyjGfssteCAtgq4rbHn` | `https://fitness-prod-rollout-20260525-7rf85sore-fawxzzy.vercel.app` | `fitness-prod-rollout-20260525.vercel.app`, `fitness-prod-rollout-20260525-fawxzzy.vercel.app`, `fitness-prod-rollout-20260525-zachariahredfield-fawxzzy.vercel.app` | Ready / Production | `9h` | retain temporarily |

## Local Reference Check

Workspace search results:

- no current code or docs references were found for:
  - `fitness-deploy-green-panels`
  - `fitness-deploy-green-panels.vercel.app`
  - `fitness-prod-rollout-20260525.vercel.app`
- `fitness-prod-rollout-20260525` **is** still named in current ATLAS closeout receipts as a helper/pressure surface
- no current Fitness or DiscordOS code path uses these helper project names as canonical runtime truth

Operational interpretation:

- neither helper surface is current canonical app truth
- one helper surface (`fitness-prod-rollout-20260525`) is still part of the current closeout evidence chain
- the other (`fitness-deploy-green-panels`) appears unused by current code/docs, but is still part of the same recent helper-surface family and is only `23h` old

## Findings

### 1. Both helper projects exist and are recent

Confirmed via live CLI:

- both projects exist under owner `fawxzzy`
- both have a single recent production deployment
- both are Next.js projects at root `.`
- both were created in the last `24h`

### 2. Canonical Fitness is already the active owner surface

Canonical active surface remains:

- `fawxzzy-fitness`
- `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- `https://fawxzzy-fitness-local.vercel.app`

It also has multiple recent production deployments that overlap the same time window as the helper projects.

### 3. No current local code/doc dependency was found for the helper aliases

There is no current workspace evidence that:

- OAuth callbacks point at either helper alias
- Discord runtime or bot-facing docs point at either helper alias
- current Fitness app code expects either helper project as canonical runtime

### 4. The helper surfaces still read as same-day rollout evidence

Even though local dependency evidence is clean, these helpers are too recent to treat as ordinary abandoned stale surfaces:

- `fitness-prod-rollout-20260525` is explicitly named in current closeout receipts
- `fitness-deploy-green-panels` belongs to the same recent helper-deploy cluster and is not yet superseded by a dedicated helper-surface consolidation receipt

## Decision

### `fitness-prod-rollout-20260525`

- decision: `retain temporarily`

Reason:

- same-day rollout evidence surface
- still named in current ATLAS closeout receipts
- not current app truth, but not yet fully aged out of the active closeout evidence chain

### `fitness-deploy-green-panels`

- decision: `retain temporarily`

Reason:

- no local runtime dependency was found
- deletion tooling exists
- but it is still part of the same recent helper-surface cluster and is only `23h` old
- safer to close helper-surface policy in one later consolidation step rather than mutate one helper project opportunistically mid-closeout

### Alias-only removal

- decision: `not chosen`

Reason:

- neither helper surface proved alias-only pressure distinct from project-level pressure
- deleting aliases without the project would not materially simplify the current closeout story

## Why Deletion Was Deferred

Deletion is technically possible, but it is not the best current package boundary because:

1. both helper projects are very recent
2. one helper is still explicitly named in current closeout receipts
3. this queue still has a later consolidation pass intended to resolve branch/tmp/Vercel closure together
4. root receipt durability is currently awkward because `stack` is self-lock-tracked, so a bounded review-only decision is safer than a same-turn helper-project mutation

## Remaining Pressure

Remaining helper-surface pressure after this review:

- `fitness-deploy-green-panels`
- `fitness-prod-rollout-20260525`

Both are now clearly classified as:

- non-canonical helper surfaces
- retain-temporarily candidates
- later deletion candidates after the closeout consolidation pass confirms they are no longer needed as active rollout evidence

## Files Changed

- `docs/ops/VERCEL-HELPER-SURFACE-FINAL-REVIEW-2026-05-25.md`

## Next Package

`Fitness Residue Classification Pass`

Why:

- Vercel helper pressure is no longer unknown
- tmp pressure is already classified
- the next narrow closeout lane is the remaining dirty Fitness residue classification pass

## Closeout Verdict

The two remaining helper projects are not canonical runtime truth.

But they are still too recent to delete casually in this pass.

Current best disposition:

- keep both temporarily
- carry them into the later branch/tmp/Vercel consolidation package
- delete only after that consolidation receipt confirms they are no longer needed as retained rollout evidence
