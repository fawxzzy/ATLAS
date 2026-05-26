# Vercel Helper Surface Deletion Decision

- Date: `2026-05-25`
- Lane: `Duplicate Surface Decommission / Manual Deploy Exception Burn-Down`
- Mode: `decision first, live deletion after dependency clearance`
- Status: `delete approved and executed`

## Goal

Resolve the two remaining non-canonical Fitness helper Vercel projects after the brand/generator and closeout passes proved the canonical Fitness runtime is already owned by `fawxzzy-fitness`.

Known helper targets:

- `fitness-deploy-green-panels`
- `fitness-prod-rollout-20260525`

Canonical Fitness project:

- `fawxzzy-fitness`
- `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

## Live Metadata

| Project | Project ID | Latest deployment | Latest deployment URL | Production aliases | Status | Created at |
| --- | --- | --- | --- | --- | --- | --- |
| `fitness-deploy-green-panels` | `prj_pDHtigVQI2m3RWswnq3q7rJ890UT` | `dpl_GxNANEzc6EsrbK7PBNv1eiiNVmdu` | `https://fitness-deploy-green-panels-e8dlyhspq-fawxzzy.vercel.app` | `fitness-deploy-green-panels.vercel.app`, `fitness-deploy-green-panels-fawxzzy.vercel.app`, `fitness-deploy-green-panels-zachariahredfield-fawxzzy.vercel.app` | `Ready / Production` | `2026-05-24 14:59:55 -0400` |
| `fitness-prod-rollout-20260525` | `prj_FR600ERe6GtvnNsb7EeDt0O5oX8u` | `dpl_57T5sTFC6MyjGfssteCAtgq4rbHn` | `https://fitness-prod-rollout-20260525-7rf85sore-fawxzzy.vercel.app` | `fitness-prod-rollout-20260525.vercel.app`, `fitness-prod-rollout-20260525-fawxzzy.vercel.app`, `fitness-prod-rollout-20260525-zachariahredfield-fawxzzy.vercel.app` | `Ready / Production` | `2026-05-25 04:14:54 -0400` |

Canonical comparison surface confirmed live during the same pass:

- project: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

## Dependency Search Result

Dependency search covered:

- Fitness app code and docs
- DiscordOS repo code and docs
- `_stack` scripts
- release ledger surfaces
- ATLAS docs and book surfaces

What was found:

- no current Fitness app code dependency
- no DiscordOS code dependency
- no `_stack` deploy-script dependency
- no Spotify/OAuth callback dependency
- no update publishing workflow dependency
- no release-ledger dependency
- current references existed only in historical ATLAS receipts and current-state/system-map style status notes

Operational interpretation:

- the helper projects were not current runtime truth
- they were only surviving as helper evidence and duplicate-surface pressure
- deleting them would require updating current-status docs, not preserving live runtime behavior

## Decision Per Surface

### `fitness-deploy-green-panels`

- decision: `delete now`

Why:

- no runtime or workflow dependency was found
- the canonical Fitness project was confirmed live and untouched
- this helper no longer carried unique evidence value once the pass recorded live metadata and deletion proof

### `fitness-prod-rollout-20260525`

- decision: `delete now`

Why:

- no runtime or workflow dependency was found
- its only remaining role was historical rollout evidence
- that evidence is better preserved in receipts than as a live production Vercel project

## Rejected Options

### Retain temporarily

Rejected because:

- the helper surfaces were already narrowed and dependency-cleared
- historical evidence does not justify keeping live production aliases indefinitely

### Remove alias only

Rejected because:

- project-level pressure was the real issue
- alias-only cleanup would still leave duplicate Vercel projects alive

### Manual-review only

Rejected because:

- the dependency search was already clean enough to make a bounded decision
- the canonical Fitness project was directly re-confirmed during this pass

## Canonical Safety Confirmation

The pass explicitly re-confirmed:

- `fawxzzy-fitness` still exists
- `prj_rtlFVOMFAWCRoJ3SQjHloi89881K` was not touched
- no app code, Supabase, Discord, or runtime behavior was changed

## Files Changed

- `docs/ops/VERCEL-HELPER-SURFACE-DELETION-DECISION-2026-05-25.md`
- `docs/ops/VERCEL-HELPER-SURFACE-DELETION-2026-05-25.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/13-vision-and-endgames.md`

## Remaining Vercel Pressure

This closes the helper-project class.

Remaining Vercel pressure is now:

- deploy provenance clarity
- remote preview / unfurl verification gate
- longer-horizon Vercel health classification work

## Marker Recommendation

If deletion proof remains clean through validation:

- `Duplicate Surface Decommission`: `94% -> 98%`
- `Manual Deploy Exception Burn-Down`: `78% -> 84%`
- `Full Stack Re-sync, Clean & Closeout`: `72% -> 76%`
- `Inventory & Truth Map`: `60% -> 62%`
