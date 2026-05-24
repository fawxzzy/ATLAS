## Trove Brand Sync

Date: 2026-05-24
Repo: `repos/fawxzzy-trove`
Branch: `codex/trove-brand-asset-sync`
Commit: `0f5f9fe55bd21aa7f017173f1950d0bd063470c1`

### Purpose

Sync the Trove public brand consumer targets from the governed ATLAS branding outputs after the Trove product, docs/QA, and vendored Fitness icon buckets were isolated.

### Readiness Check

Before sync, the Trove working tree was confirmed to contain only these seven remaining dirty public brand targets:

- `public/brand/atlas-sigil-master.png`
- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/icons/apple-touch-icon.png`
- `public/favicon-32x32.png`
- `public/favicon-16x16.png`
- `public/favicon.ico`

No remaining dirty paths were present under:

- `src/**`
- `docs/**`
- `qa/**`
- `public/apps/fitness/**`
- package or lock files

### Sync Scope

Synced from ATLAS canonical branding sources:

| Target | Source | SHA256 |
| --- | --- | --- |
| `repos/fawxzzy-trove/public/brand/atlas-sigil-master.png` | `branding/source/atlas-sigil-master.png` | `E20A9FE2E42585ED1EC818D13EC80AA8CED89F15F82A35C51269C1B794F07F51` |
| `repos/fawxzzy-trove/public/app/icon-192.png` | `branding/generated/app/icon-192.png` | `829F6539B8821C24710D06C42B54DD1CC5CC2FC273A5094502C4E040ED452070` |
| `repos/fawxzzy-trove/public/app/icon-512.png` | `branding/generated/app/icon-512.png` | `70BF6051A83DA294FF87738D843D8A533D7FBFB1608AF78D800A56F90D83005B` |
| `repos/fawxzzy-trove/public/icons/apple-touch-icon.png` | `branding/generated/favicon/apple-touch-icon.png` | `EF27FF93A31C24F88BF86A9AB4E45B5222CAB7AA882F2FE35BB32612BE3A3E0C` |
| `repos/fawxzzy-trove/public/favicon-32x32.png` | `branding/generated/favicon/favicon-32x32.png` | `4CD4BF7818A3E975B12D7675E9225C61C34E205FCD9EDAD1CF0C7F5AE8A64138` |
| `repos/fawxzzy-trove/public/favicon-16x16.png` | `branding/generated/favicon/favicon-16x16.png` | `01548BCBEAA9DD7F73844AD38D7D68EFCC1543AD96A546DB85CBFA779D1D7916` |
| `repos/fawxzzy-trove/public/favicon.ico` | `branding/generated/favicon/favicon.ico` | `EC98FD07B3CBDF1E649419F616721641BF0903EBB2B49AA3DCDEA1AC18523F87` |

### Result

The Trove public brand consumer package was committed as:

- `0f5f9fe` `branding: sync trove public brand assets`

### Verification

Ran from `repos/fawxzzy-trove`:

```powershell
npm run verify
```

Result:
- pass

### Guardrails Held

- Trove source files were not changed.
- Vendored Fitness icons were not changed in this package.
- Fitness repo brand targets were not touched.
- `_stack` was not touched.
- `tmp/` was not used as a fallback consumer surface.

### Outcome

Trove brand sync is complete as an isolated consumer package.
