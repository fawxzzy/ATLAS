# Operator Secret Path Hygiene Warning Delta

Date: 2026-05-24
Lane: Operator Secret Path Hygiene
Mode: read-only / docs-only
Status: warning delta inspected after Cleanup Pass 1

## Goal

Confirm whether the validation warning increase observed immediately after `OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md` reflects:

- expected documentation/path-discipline debt
- or a real secret-handling regression

This pass does not:

- move or delete secrets
- print secret values
- mutate Supabase
- mutate Vercel
- deploy code

## Inputs

- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`
- `runtime/receipts/validation/stack-validation.latest.md`
- `runtime/receipts/validation/stack-validation.latest.json`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`

## Summary

The warning delta was clean in the narrow sense requested:

- no secret values were surfaced by validation
- no new `repo-local-secret-material` finding was created by the cleanup
- the moved governed secret file and backup remain ignored and untracked
- the repo-root source secret is gone

The immediate warning increase from `289` to `296` was explained by path-discipline debt in the new cleanup receipt, not by secret leakage. After normalizing the new docs back to ATLAS-root-relative paths, validation dropped to `288`.

## Current Validation State

Current validation summary after normalization:

- critical: `0`
- error: `0`
- warning: `288`

Current debt-class totals after normalization:

- `historical-stack-baseline-residue`: `43`
- `lock-registry-hygiene`: `6`
- `path-discipline-leaks`: `239`

Current warning category counts after normalization:

- `atlas-root-path`: `59`
- `atlas-root-path-alt`: `180`
- `gitdir-hygiene-prunable-worktree-entry`: `3`
- `gitdir-hygiene-stale-worktree-gitdir-pointer`: `3`
- `mutable-artifact-in-repo-root`: `12`
- `mutable-state-in-repo`: `29`
- `repo-local-secret-material`: `2`

## Which Warning Codes Increased

Direct comparison is partially inferred because `stack-validation.latest.json` is runtime state and not versioned in git history.

However, the cleanup sequence is explicit enough to classify the delta:

1. `repo-local-secret-material` for `repos/fawxzzy-fitness/.env.discord-worker` is no longer present.
2. the first cleanup receipt initially contributed `8` `atlas-root-path` warnings because it used absolute local paths.
3. this inspection doc initially added more of the same path-discipline warnings until both docs were normalized to root-relative paths.

Net interpretation:

- one repo-root secret-material warning was removed
- the transient absolute-path documentation warnings were avoidable and are now removed
- overall warning count is now `1` lower than the pre-cleanup baseline

Observed sequence:

- before cleanup pass: `289`
- immediately after cleanup pass: `296`
- after this inspection plus path normalization: `288`

## New Warnings Introduced By The Cleanup Pass

The following warnings were initially all in:

- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-CLEANUP-PASS-1-2026-05-24.md`

All were category:

- `atlas-root-path`

They originally occurred at lines:

- `16`
- `20`
- `24`
- `29`
- `114`
- `115`
- `116`
- `132`

They pointed to:

- the old repo-root source path
- the governed destination path
- the governed backup path
- the destination directory
- the repo path used in the verification summary

Operational interpretation:

- these were documentation path references only
- they are not secret-value exposure findings
- they were consistent with existing inherited absolute-path debt across ATLAS docs
- they have now been normalized away in the two new docs

## Secret-Reference Check

### Findings referencing moved secret surfaces

Current validation findings do **not** contain:

- `repo-local-secret-material` for `repos/fawxzzy-fitness/.env.discord-worker`

The immediate post-cleanup validation findings did contain absolute-path references to:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `secrets/local/fawxzzy-fitness-discord-worker.env`
- `secrets/local/fawxzzy-fitness-discord-worker.pre-pass-1.backup.env`

Important distinction:

- these appeared only inside committed receipts as path references
- they do not expose values
- they were path-discipline warnings, not secret-material warnings
- they are no longer present after normalization

### Findings referencing repo-root `.env` or `.vercel/.env*.local`

Current validation still flags unrelated repo-local secret material in:

- `repos/fawxzzy-mazer/.env.local`
- `repos/Nat1-Games/nat1-games/.env`

Current validation does **not** separately flag:

- the moved Fitness repo-root `.env.discord-worker`

Current validation also continues to include generic mutable-state warnings for repo-local `.vercel` directories, but the secret-bearing `.vercel/.env*.local` issue remains governed by the operator-secret docs rather than appearing as a new post-cleanup warning spike here.

## Secret Value Exposure Check

No warning in the current validation report shows:

- secret values
- token bodies
- OAuth payloads
- raw env contents

The new warnings only show path strings and line previews from committed docs.

## Git And Ignore Verification

Confirmed:

- `repos/fawxzzy-fitness/.env.discord-worker` is gone
- `secrets/local/fawxzzy-fitness-discord-worker.env` exists
- `secrets/local/fawxzzy-fitness-discord-worker.pre-pass-1.backup.env` exists
- both governed secret files are ignored by root `.gitignore` under `secrets/**`

## Fitness Repo Status Check

The Fitness repo root is still not clean, but for unrelated preexisting tracked changes only.

Observed tracked modifications remain:

- `package.json`
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

This cleanup did not introduce a new tracked Fitness repo change.

## Conclusion

The warning delta is expected and acceptable for the current lane:

- the moved secret is not tracked
- the moved secret is not flagged as repo-local secret material anymore
- the source repo-root secret is gone
- the transient warning increase came from committed absolute path references in the cleanup receipt and this inspection doc before normalization

So the delta does **not** indicate:

- secret leakage
- tracked secret residue
- repo-root secret spill

It **does** indicate:

- continued inherited path-discipline debt in older docs
- and a need to keep new secret-handling receipts root-relative by default

## Recommended Next Move

Proceed to:

- `Fitness Supabase Profile/Data Hygiene Export Packet 1`

No additional secret cleanup is required before that export-packet planning step, as long as mutation remains approval-gated.

## Marker Interpretation

This inspection does not justify a marker move by itself.

It confirms:

- `Operator Secret Path Hygiene` remains valid at `55%`
- `Fitness Supabase Profile/Data Hygiene` remains valid at `35%`
