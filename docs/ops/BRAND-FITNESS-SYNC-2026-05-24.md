# Fitness Brand Sync

Date: 2026-05-24
Lane: Brand Asset Canonicalization
Mode: narrow asset sync only
Status: local sync complete

## Goal

Apply the canonical ATLAS brand outputs to the Fitness consumer targets from the repaired canonical repo path without using `tmp`, editing product code, or deploying.

## Preconditions

Verified before sync:

- canonical repo path exists:
  - `repos/fawxzzy-fitness`
- branch:
  - `main`
- remote:
  - `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD:
  - `7ceebde9d71564614df98e391b245a836d15c401`
- working tree:
  - clean
- `.vercel/project.json`
  - present locally
  - ignored
  - points to `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

## Drift Scope

Using a Fitness-only manifest slice with `branding/scripts/sync-brand-assets.mjs --dry-run`:

- already current:
  - `public/brand/atlas-sigil-master.png`
  - `public/app/icon-192.png`
  - `public/app/icon-512.png`
  - `public/favicon-32x32.png`
  - `public/favicon-16x16.png`
  - `public/favicon.ico`
- stale:
  - `public/icons/icon-192.png`
  - `public/icons/icon-512.png`
  - `public/icons/apple-touch-icon.png`

## Sync Applied

Synced from canonical ATLAS outputs:

| Target | Source | SHA256 |
| --- | --- | --- |
| `repos/fawxzzy-fitness/public/icons/icon-192.png` | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| `repos/fawxzzy-fitness/public/icons/icon-512.png` | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| `repos/fawxzzy-fitness/public/icons/apple-touch-icon.png` | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |

After sync, the three Fitness consumer files matched the canonical ATLAS source hashes exactly.

## Verification

Ran from `repos/fawxzzy-fitness`:

```powershell
npm run sanity:quick
npm run typecheck
npm run build
```

Result:

- all passed

Observed warnings:

- existing non-blocking React hook lint warnings remain during `sanity:quick` and `build`

## Git/Lock Outcome

No Fitness repo commit was created.

Reason:

- the synced Fitness targets are intentionally local generated outputs ignored by repo policy:
  - `.gitignore: /public/icons/*.png`
- after sync, the Fitness working tree remained clean from Git’s perspective
- since Fitness HEAD did not move, `stack.lock.yaml` did not need a repin for this package

## Guardrails Held

- no `tmp` path was used
- no product code was edited
- no Discord or Spotify code was touched
- no `.vercel/project.json` change was staged
- no deploy was performed
- no Vercel or Supabase settings were mutated

## Outcome

The canonical Fitness repo is now locally aligned with the canonical ATLAS brand outputs for the stale `public/icons/**` consumer set.

This was a valid narrow Fitness brand sync, but it is a local generated-asset alignment package rather than a committed Fitness repo history change.
