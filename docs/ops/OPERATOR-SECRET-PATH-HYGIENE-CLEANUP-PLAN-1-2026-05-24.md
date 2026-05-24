# Operator Secret Path Hygiene Cleanup Plan 1

Date: 2026-05-24
Lane: Operator Secret Path Hygiene
Mode: docs-only cleanup plan
Status: first cleanup plan recorded

## Goal

Define the safe cleanup path for local secret-bearing residue that blocks:

- Fitness Supabase Profile/Data Hygiene mutation
- Discord OS Infrastructure Separation

This plan does not:

- print secret values
- move secret files
- delete secret files
- rename secret files
- rotate keys
- pull env
- mutate Supabase
- mutate Vercel
- deploy code

## Inputs

- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-INVENTORY-2026-05-24.md`
- `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-CLEANUP-PLAN-1-2026-05-24.md`

## Governing Rule

Use root `secrets/**` as the default and preferred local secret-bearing lane.

That means:

- repo roots should not remain long-term secret spill surfaces
- ignored `.vercel/.env*.local` files are still secret-bearing residue even when generated locally
- ignored `.vercel/project.json` files are acceptable identity metadata and should not be lumped into secret cleanup
- any exception to the governed secret lane must be explicit, temporary, and receipt-backed

## Cleanup Targets In Scope

Primary scope for Cleanup Plan 1:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `secrets/local/spotify-club-prod.env`
- repo-local `.vercel/.env*.local` files under Trove and Mazer

Supporting distinction in scope:

- `.vercel/project.json` identity files remain documented non-secret surfaces

## Destination For `.env.discord-worker`

Planned destination:

- `secrets/local/fawxzzy-fitness-discord-worker.env`

Reason:

- that file already exists in the governed root secret lane
- it matches the operator intent more clearly than a repo-root `.env.discord-worker`
- it keeps Discord worker runtime auth inside the root secret lane instead of the Fitness repo root

Planned cleanup outcome later:

1. confirm the governed root file is the only needed runtime source
2. verify the worker/runtime reads from the governed root path
3. retire `repos/fawxzzy-fitness/.env.discord-worker`
4. record receipt that the repo root no longer acts as a live secret mirror

## Backup And Export Posture Before Secret Mutation

Before any future secret-path move or delete:

### Artifact set A: key-name-only inventory snapshot

For each secret-bearing file selected for cleanup, capture:

- file path
- owner lane
- whether it is repo-root, `.vercel`, or governed `secrets/**`
- key names only
- whether the file is currently expected as live runtime input

Do not capture secret values in the receipt.

### Artifact set B: runtime dependency check

For each selected file, capture:

- which script, worker, or local operator flow still depends on it
- whether a governed root secret replacement already exists
- whether the file is active, fallback-only, or stale

### Artifact set C: cleanup manifest

For the approved cleanup pass, create a manifest that names:

- exact file(s) in scope
- destination if moving
- delete-later candidates
- proof command or proof path after cleanup
- rollback path if cleanup breaks runtime behavior

## Rotation Guidance

Default posture:

- no rotation is required just because a secret file is being relocated inside governed local-only surfaces

Rotation becomes required later only if:

- a secret value is discovered outside the governed lane unexpectedly
- a file was copied into a tracked or externally exposed surface
- ownership changes during Discord OS Infrastructure Separation make old credentials inappropriate

Current conclusion for Cleanup Plan 1:

- relocation and retirement planning can proceed without mandatory immediate rotation
- any actual rotation should be its own explicit follow-up decision, not bundled into the first placement cleanup

## Manual Owner Review

The following remain manual owner review items:

### `secrets/local/spotify-club-prod.env`

Reason:

- the file is already in the correct governed root secrets lane
- the issue is naming and ownership ambiguity, not bad placement
- it still reflects legacy Spotify Club naming after the Music Sesh rename and before Discord OS Infrastructure Separation

Planned treatment later:

1. decide whether the secret belongs to Fitness, Music Sesh, or future DiscordOS
2. decide the replacement name
3. update references
4. retire the legacy-named file with receipt

### `repos/fawxzzy-fitness/.env.prod-local-mirror.example`

Reason:

- it is not secret-bearing
- but its `.env*` shape still creates operator confusion

Planned treatment later:

- rename or relocate as a clearer example contract, not as a secret cleanup task

## Safe To Delete Later

Planned delete-later candidates after backup/receipt:

### `repos/fawxzzy-fitness/.env.discord-worker`

Safe to delete later only after:

- root `secrets/local/fawxzzy-fitness-discord-worker.env` is confirmed as the active source
- runtime proof is captured
- rollback path is named

### `repos/fawxzzy-mazer/.env.local`

Safe to delete later only after:

- local workflow dependency is checked
- key-name-only export is captured
- any still-needed local auth path is replaced or explicitly retired

### repo-local `.vercel/.env*.local` files

Safe to delete later only after:

- each repo confirms whether the local Vercel auth residue is still needed
- any retained local auth dependency is moved into the governed root secret lane or explicitly excepted
- `.vercel/project.json` remains intact for deploy identity proof

## Must Stay In Governed Secrets Lane

The following should remain in `secrets/**` unless a later lane creates a better governed local-only contract:

- `secrets/fitness-doctor.env`
- `secrets/fitness-lps-dev.env`
- `secrets/local/fawxzzy-fitness-discord-bot.env`
- `secrets/local/fawxzzy-fitness-discord-prod.env`
- `secrets/local/fawxzzy-fitness-discord-worker.env`
- `secrets/local/fawxzzy-fitness-preview-gate.env`
- `secrets/local/fawxzzy-fitness-prod-db.env`
- `secrets/local/fitness-prod-to-local.env`
- `secrets/local/spotify-club-prod.env` until owner/naming review is complete

Reason:

- these are already in the correct local-only lane
- the immediate problem is residue outside that lane, not the existence of the lane itself

## `.vercel/project.json` Versus Secret-Bearing Env Files

### `.vercel/project.json`

Status:

- keep
- document only
- non-secret identity metadata

Reason:

- used by deploy-identity guardrails
- should not be retired as part of secret cleanup

### `.vercel/.env*.local`

Status:

- secret-bearing residue
- subject to later cleanup or relocation

Reason:

- contain local auth/deploy material
- blur the boundary between repo identity linkage and secret runtime state

## What Blocks Fitness Supabase Mutation

Primary blocker:

- `repos/fawxzzy-fitness/.env.discord-worker`

Why:

- it leaves secret-bearing runtime material inside the Fitness repo root
- Fitness Supabase mutation should not begin while operator auth truth is still split between repo root and governed root secret lane

Cleanup implication:

- either clear this blocker first
- or explicitly approve a temporary exception for a later mutation pass

Default recommendation:

- clear it first

## What Blocks Discord OS Infrastructure Separation

Primary blockers or prep issues:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `secrets/local/spotify-club-prod.env`
- `repos/fawxzzy-mazer/.env.local`
- `repos/fawxzzy-mazer/.vercel/.env.preview.local`
- `repos/fawxzzy-mazer/.vercel/.env.production.local`

Secondary prep issues:

- Trove `.vercel/.env*.local` files reflect the same residue pattern even if they are not the first separation blockers

Cleanup implication:

- Discord OS separation should not start moving runtime or ownership while legacy secret placement and naming still blur responsibility

## Verification That Repo Roots Are Not Secret Spill Surfaces

After any future cleanup pass, verification should prove:

1. no live secret-bearing Discord worker file remains in `repos/fawxzzy-fitness`
2. no repo-root secret-bearing env file remains where a governed root replacement exists
3. `.vercel/project.json` still exists where deploy identity proof needs it
4. repo-local `.vercel/.env*.local` files are either:
   - removed, or
   - explicitly excepted with receipt and owner rationale
5. `git status` and root policy still show `secrets/**` as the active local-only secret lane

Proof shape later:

- path-level verification only
- key-name-only confirmation where needed
- no secret-value printing

## Approval Required Before Any Secret Mutation

The following require explicit approval before action:

- moving `repos/fawxzzy-fitness/.env.discord-worker`
- deleting `repos/fawxzzy-fitness/.env.discord-worker`
- renaming or replacing `secrets/local/spotify-club-prod.env`
- deleting `repos/fawxzzy-mazer/.env.local`
- deleting any repo-local `.vercel/.env*.local` file
- any secret rotation or revocation

Reason:

- these are operational auth surfaces, not just docs cleanup

## Recommended First Secret Cleanup Scope Later

When approved, the first narrow cleanup pass should be:

1. prove `secrets/local/fawxzzy-fitness-discord-worker.env` is the governed destination
2. verify the Discord worker/runtime uses that governed root path
3. retire `repos/fawxzzy-fitness/.env.discord-worker`
4. record receipt and rollback posture

Why first:

- it is the direct blocker for Fitness Supabase mutation
- it is cleaner and lower-risk than mixing multiple secret lanes in one pass

## Recommended Sequence After This Plan

1. review and approve the `.env.discord-worker` cleanup scope
2. run that narrow cleanup pass with receipt
3. decide whether `spotify-club-prod.env` gets renamed now or waits for Discord OS separation planning
4. review repo-local `.vercel/.env*.local` cleanup separately by repo
5. only then reopen the approval-gated Fitness Supabase mutation path

## Non-Goals

Cleanup Plan 1 does not:

- authorize secret mutation by itself
- rename legacy secret files yet
- clean all repo-local Vercel auth residue in one batch
- open Discord OS Infrastructure Separation implementation
- change Supabase or Vercel state

## Marker Interpretation

This package justifies:

- Operator Secret Path Hygiene: `40%`

It does not yet justify movement for:

- Fitness Supabase Profile/Data Hygiene
- Discord OS Infrastructure Separation
