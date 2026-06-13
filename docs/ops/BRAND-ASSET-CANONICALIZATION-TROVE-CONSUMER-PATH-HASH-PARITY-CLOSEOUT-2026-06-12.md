# Brand Asset Canonicalization Trove Consumer Path Hash Parity Closeout - 2026-06-12

- Date: `2026-06-12`
- Lane: `Brand Asset Canonicalization`
- Mode: `bounded root-plus-owner closeout`

## Decision

`Brand Asset Canonicalization` moves from `90%` to `100%`.

## Why This Closeout Is Honest Now

The previously open brand blocker class is now reduced to one bounded non-Fitness consumer family:

- `_stack` launcher already matched the canonical launcher asset
- all declared Fitness consumers already matched the canonical ATLAS brand outputs
- the only remaining failures were the seven Trove consumer targets still declared under stale pre-canonicalization paths `repos/fawxzzy-trove/...`

That remaining blocker belongs to brand consumer path truth plus consumer hash parity, not to deployment, preview/unfurl verification, archive/delete authority, or protected Fitness mutation.

`Preview Cache & Surface Consistency` remains the separate lane for browser-visible favicon, PWA, launcher-cache, and unfurl/cache proof.

## Path Truth Repair

Updated `branding/manifest.json` so the seven Trove consumer targets now point to canonical repo-naming paths:

- `repos/trove/public/brand/atlas-sigil-master.png`
- `repos/trove/public/app/icon-192.png`
- `repos/trove/public/app/icon-512.png`
- `repos/trove/public/icons/apple-touch-icon.png`
- `repos/trove/public/favicon-32x32.png`
- `repos/trove/public/favicon-16x16.png`
- `repos/trove/public/favicon.ico`

This consumes the stale post-rename path blocker left behind after `Atlas-owned Repo Naming Canonicalization` closed.

## Consumer Hash Parity Proof

After the manifest-path repair, `node branding/scripts/sync-brand-assets.mjs --check` and direct hash comparison confirmed:

### Already-aligned consumers

- `_stack` launcher consumer matched canonical output
- all declared Fitness consumers matched canonical source/generated outputs

### Trove consumers restored to canonical parity

| Target | Canonical source | SHA256 |
| --- | --- | --- |
| `repos/trove/public/brand/atlas-sigil-master.png` | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| `repos/trove/public/app/icon-192.png` | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| `repos/trove/public/app/icon-512.png` | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| `repos/trove/public/icons/apple-touch-icon.png` | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| `repos/trove/public/favicon-32x32.png` | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| `repos/trove/public/favicon-16x16.png` | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| `repos/trove/public/favicon.ico` | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |

## Owner-Repo Proof

The Trove owner repo remained a bounded seven-file asset package:

- repo: `repos/trove`
- branch: `codex/path-discipline-warning-slice-trove`
- commit: `cd57245b6ce4f4aa3bc35efd26f4e0551f4a4a8d`
- push: `origin/codex/path-discipline-warning-slice-trove`
- no Trove source files, docs, QA files, or vendored Fitness icon surfaces were included

Repo-local verification passed:

- `npm run verify`

## Root Truth Refresh

To keep stack-level projections honest after the accepted Trove package:

- `stack.lock.yaml` was regenerated from current stack truth
- `docs/registry/STACK-REPO-INVENTORY.json` was regenerated
- `docs/audits/STACK-REPO-INVENTORY.md` was regenerated

The previously uncommitted selector receipt

- `docs/ops/NEAR-100-MARKER-CLOSEOUT-SELECTOR-AFTER-NAMING-AND-DISCORD-CLOSEOUTS-2026-06-12.md`

is preserved in the same bounded root bundle as the immediate predecessor that selected this closeout lane.

## Validation

Commands used for brand proof:

- `node branding/scripts/sync-brand-assets.mjs --dry-run`
- `node branding/scripts/sync-brand-assets.mjs --check`
- `node branding/scripts/sync-brand-assets.mjs`
- direct `Get-FileHash` parity checks for the seven Trove targets
- `npm run verify` in `repos/trove`

Root validation after root-truth refresh:

- `python ops/validation/validate_stack.py --ratchet`

Result:

- `critical=0 error=0 warning=56 info=0`

## Boundary

This closeout does not claim:

- browser-visible favicon or PWA cache proof
- launcher cache proof
- remote preview or unfurl proof
- deploy-backed cache invalidation
- any Fitness mutation or Fitness lane release
- any archive/delete/disposition result

Those concerns remain separate, especially in `Preview Cache & Surface Consistency`.

## Marker Result

- Before: `90%`
- After: `100%`

## Reopen Conditions

Reopen this lane only if:

- a declared brand consumer path drifts from canonical repo truth
- a declared consumer file drifts from canonical source/generated asset hashes
- a new declared consumer is added without governed path/hash proof
