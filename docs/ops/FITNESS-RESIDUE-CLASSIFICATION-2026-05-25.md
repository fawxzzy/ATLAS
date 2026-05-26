## Fitness Residue Classification - 2026-05-25

### Scope

- Repo inspected: `repos/fawxzzy-fitness`
- Mode: inventory and classification only
- No Fitness files were modified, reverted, staged, or committed in this pass

### Root Context

- ATLAS root branch: `main`
- Fitness branch: `main`
- Fitness remote state: `origin/main` in sync
- Root retained residue: untracked `archive/` remains intentionally untouched

### Recent Fitness Context

Recent durable Discord-focused commits confirm the current dirty state is outside the just-finished DiscordOS preparation lane:

- `3f48f9c2` `fix: restrict computa setup commands to owner`
- `623089bb` `feat: add discord operator repair paths`
- `b2e60634` `fix: harden discord feedback interactions`
- `46d5862c` `fix: delete duplicate completed feedback cards`
- `52cdb7e3` `feat: archive duplicate completed feedback cards`
- `7ceb6d66` `feat: repair discord feedback board state`
- `508ca5d2` `feat: complete discord feedback board restore`
- `c2546734` `feat: recover completed feedback board`
- `a71269b0` `feat: move discord feedback intake to dedicated channel`
- `7a89bb4d` `refactor: isolate discord feedback runtime boundary`

### Fitness Worktree Status

`git status --short` reported 11 modified tracked files and no repo-local untracked files:

- `public/app/icon-192.png`
- `public/app/icon-512.png`
- `public/favicon-16x16.png`
- `public/favicon-32x32.png`
- `public/favicon.ico`
- `public/sw.js`
- `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- `src/generated/appBuildManifest.json`
- `src/lib/stretch-library-details.ts`
- `src/lib/stretch-library-summaries.ts`

### Residue Classification Table

| Path | Git State | Classification | Owner Lane | Preserve Now | Later Action | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `public/app/icon-192.png` | modified | brand/preview residue | Brand Asset Canonicalization + Preview Cache & Surface Consistency | yes | package or revert in dedicated brand/preview lane | Binary asset drift; tied to icon generation scripts, not DiscordOS work |
| `public/app/icon-512.png` | modified | brand/preview residue | Brand Asset Canonicalization + Preview Cache & Surface Consistency | yes | package or revert in dedicated brand/preview lane | Binary asset drift; tied to icon generation scripts, not DiscordOS work |
| `public/favicon-16x16.png` | modified | brand/preview residue | Brand Asset Canonicalization + Preview Cache & Surface Consistency | yes | package or revert in dedicated brand/preview lane | Generated favicon output, not current Discord lane scope |
| `public/favicon-32x32.png` | modified | brand/preview residue | Brand Asset Canonicalization + Preview Cache & Surface Consistency | yes | package or revert in dedicated brand/preview lane | Generated favicon output, not current Discord lane scope |
| `public/favicon.ico` | modified | brand/preview residue | Brand Asset Canonicalization + Preview Cache & Surface Consistency | yes | package or revert in dedicated brand/preview lane | Generated favicon bundle output, not current Discord lane scope |
| `public/sw.js` | modified | generated residue | Preview Cache & Surface Consistency | no | safe revert candidate later or regenerate in dedicated cache/build lane | Only `APP_BUILD_ID` changed; no functional DiscordOS or product intent proven here |
| `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc` | modified | generated residue | Fitness QA/LLEL Workflow | no | safe revert candidate later | Python bytecode cache file; generated residue only |
| `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc` | modified | generated residue | Fitness QA/LLEL Workflow | no | safe revert candidate later | Python bytecode cache file; generated residue only |
| `src/generated/appBuildManifest.json` | modified | generated residue | Preview Cache & Surface Consistency | no | safe revert candidate later or regenerate in dedicated cache/build lane | Only `buildId` / `generatedAt` timestamp changed |
| `src/lib/stretch-library-details.ts` | modified | stale/manual review | Active product work (Stretch library) | yes | review or revert in its own product lane | Blob id unchanged; no content diff proven; likely line-ending/worktree noise |
| `src/lib/stretch-library-summaries.ts` | modified | stale/manual review | Active product work (Stretch library) | yes | review or revert in its own product lane | Blob id unchanged; no content diff proven; likely line-ending/worktree noise |

### Untracked Item Table

No repo-local untracked files were present in `repos/fawxzzy-fitness` during this pass.

### Classification Summary By Lane

- Brand/preview residue
  - `public/app/icon-192.png`
  - `public/app/icon-512.png`
  - `public/favicon-16x16.png`
  - `public/favicon-32x32.png`
  - `public/favicon.ico`
- Generated residue
  - `public/sw.js`
  - `src/generated/appBuildManifest.json`
  - `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
  - `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`
- Stale/manual review or product-lane residue
  - `src/lib/stretch-library-details.ts`
  - `src/lib/stretch-library-summaries.ts`

### What Must Be Preserved

- The five icon/favicon assets should stay preserved until a dedicated brand/preview pass decides whether they are intended brand updates or accidental generator drift.
- The two `stretch-library-*` files should stay preserved until a product-lane review confirms whether they are pure line-ending noise or part of separate stretch-library work.

### Safe Revert Candidates Later

These should not be reverted in this pass, but they are strong future safe-revert candidates if no dedicated lane claims them:

- `public/sw.js`
- `src/generated/appBuildManifest.json`
- `scripts/mobile_regression/__pycache__/__init__.cpython-313.pyc`
- `scripts/mobile_regression/__pycache__/board_builder.cpython-313.pyc`

### Items That Should Become Their Own Package

- Brand/preview asset drift
  - package in a dedicated Fitness brand/preview lane
- Stretch library residue
  - package in a dedicated Fitness product/stretches lane if substantive changes are later proven
- Generated build/cache residue
  - package with preview/cache/build hygiene, not with DiscordOS, Supabase, or product feature work

### Explicit Non-Ownership

This residue does **not** belong to:

- DiscordOS extraction
- Discord feedback runtime boundary work
- Supabase profile/data hygiene pass
- Vercel helper surface review
- root stack-lock reconciliation

### Validation

- `python .\ops\validation\validate_stack.py`
  - `critical=0 error=0 warning=307`

Scoped validation was not needed because normal validation is green in the current working state.

### Files Changed In This Pass

- `docs/ops/FITNESS-RESIDUE-CLASSIFICATION-2026-05-25.md`

### Remaining Blockers

- Fitness still carries unrelated residue, but it is now classified enough to avoid contaminating future DiscordOS, Supabase, and closeout lanes.
- ATLAS root still has pending stack truth / receipt working-state changes from earlier queue passes, and a new root commit would re-stale the self-lock-tracked `stack` pin unless that policy is addressed separately.

### Next Package

- `Branch / Tmp / Vercel Closeout Consolidation`

### Marker Recommendation

- `Full Stack Re-sync, Clean & Closeout`: `52% -> 56%`
- `Inventory & Truth Map`: `45% -> 48%`
- `Fitness Branch Cleanup / Main-Only Governance`: stays `96%`
