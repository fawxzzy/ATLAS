## Trove Vendored Fitness Icon Package

Date: 2026-05-24
Repo: `repos/fawxzzy-trove`
Branch: `codex/trove-brand-asset-sync`
Commit: `3a60a7cb64e4d5979988bdd444a75157bb4cfc42`

### Purpose

Isolate the vendored Fitness icon lane from the remaining Trove consumer-brand drift before the Trove brand sync package.

### Scope

Included:
- `public/apps/fitness/icon-192.png`
- `public/apps/fitness/icon-512.png`

Excluded:
- `public/brand/**`
- `public/app/**`
- `public/icons/**`
- `public/favicon*`
- Trove source files
- Trove docs and QA files

### Result

The vendored Fitness icon lane was packaged as its own Trove-local commit:

- `3a60a7c` `assets: package vendored fitness icons`

### Verification

Ran from `repos/fawxzzy-trove`:

```powershell
npm run verify
```

Result:
- pass

### Hashes

- `public/apps/fitness/icon-192.png`
  - `SHA256 C68F295F8B5CF6328A7E28FBA4AEC6A685CB0ADC0D7A667DF74D0B72DDE83CFD`
- `public/apps/fitness/icon-512.png`
  - `SHA256 775B367038BD92E608032CF30D84259AAC9179A878D41DB17A2FE7345CEAA093`

### Remaining Trove Drift

After this package, the Trove working tree still contains only the deferred public brand consumer targets:

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/brand/atlas-sigil-master.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/icons/apple-touch-icon.png`

### Next Step

Trove brand sync may proceed only after this remaining public brand target bucket is handled as its own isolated package.
