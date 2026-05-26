# Vercel Helper Surface Deletion

- Date: `2026-05-25`
- Lane: `Duplicate Surface Decommission / Manual Deploy Exception Burn-Down`
- Mode: `bounded helper-project deletion`
- Status: `completed`

## Goal

Delete the two remaining non-canonical Fitness helper Vercel projects after the dependency check confirmed they were not part of current runtime truth.

Deleted targets:

- `fitness-deploy-green-panels`
- `fitness-prod-rollout-20260525`

Canonical active project left untouched:

- `fawxzzy-fitness`
- `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

## Commands Run

```powershell
vercel project inspect fitness-deploy-green-panels
vercel inspect fitness-deploy-green-panels.vercel.app
vercel project inspect fitness-prod-rollout-20260525
vercel inspect fitness-prod-rollout-20260525.vercel.app
vercel project inspect fawxzzy-fitness
cmd /c "echo y| vercel project remove fitness-deploy-green-panels"
vercel project inspect fitness-deploy-green-panels
vercel inspect fitness-deploy-green-panels.vercel.app
cmd /c "echo y| vercel project remove fitness-prod-rollout-20260525"
vercel project inspect fitness-prod-rollout-20260525
vercel inspect fitness-prod-rollout-20260525.vercel.app
vercel project inspect fawxzzy-fitness
```

## Deletion Proof

### 1. `fitness-deploy-green-panels`

Before deletion:

- project id: `prj_pDHtigVQI2m3RWswnq3q7rJ890UT`
- latest deployment: `dpl_GxNANEzc6EsrbK7PBNv1eiiNVmdu`

Deletion result:

- `Success! Project fitness-deploy-green-panels removed`

Post-delete proof:

- `vercel project inspect fitness-deploy-green-panels` -> `There is no project for "fitness-deploy-green-panels"`
- `vercel inspect fitness-deploy-green-panels.vercel.app` -> `Can't find the deployment`

### 2. `fitness-prod-rollout-20260525`

Before deletion:

- project id: `prj_FR600ERe6GtvnNsb7EeDt0O5oX8u`
- latest deployment: `dpl_57T5sTFC6MyjGfssteCAtgq4rbHn`

Deletion result:

- `Success! Project fitness-prod-rollout-20260525 removed`

Post-delete proof:

- `vercel project inspect fitness-prod-rollout-20260525` -> `There is no project for "fitness-prod-rollout-20260525"`
- `vercel inspect fitness-prod-rollout-20260525.vercel.app` -> `Can't find the deployment`

### 3. Canonical Fitness Project Untouched

Post-delete confirmation:

- `vercel project inspect fawxzzy-fitness` still returns:
  - project id `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
  - owner `fawxzzy`
  - active Next.js project metadata

## What Did Not Change

- no canonical Fitness project deletion
- no Vercel deploy
- no Supabase mutation
- no Discord/runtime mutation
- no app-code change
- no `tmp/` mutation
- no `archive/` mutation

## Remaining Vercel Pressure

Helper-project pressure is closed.

Open Vercel-adjacent pressure now narrows to:

- provenance clarity and release/governance signals
- remote preview / unfurl verification gate
- future Vercel health classification automation

## Marker Recommendation

This deletion pass justifies:

- `Duplicate Surface Decommission`: `94% -> 98%`
- `Manual Deploy Exception Burn-Down`: `78% -> 84%`
- `Full Stack Re-sync, Clean & Closeout`: `72% -> 76%`
- `Inventory & Truth Map`: `60% -> 62%`

## Next Package

`Fitness Supabase Mutation Pass 1`
