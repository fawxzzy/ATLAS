# Operator Secret Path Hygiene Cleanup Pass 1

Date: 2026-05-24
Lane: Operator Secret Path Hygiene
Mode: approval-gated local secret cleanup
Status: completed

## Goal

Move the repo-root Discord worker env residue out of the Fitness repo root and into the governed local secrets lane without printing or committing secrets.

## Scope

Source:

- `C:\ATLAS\repos\fawxzzy-fitness\.env.discord-worker`

Governed destination:

- `C:\ATLAS\secrets\local\fawxzzy-fitness-discord-worker.env`

Governed backup created during pass:

- `C:\ATLAS\secrets\local\fawxzzy-fitness-discord-worker.pre-pass-1.backup.env`

## Preconditions Verified

- source file existed before cleanup
- destination directory existed: `C:\ATLAS\secrets\local`
- governed destination already existed before cleanup
- source and destination had the same key-name inventory
- source and destination were not byte-identical, so the preexisting governed destination was backed up before overwrite

## Key-Name-Only Inventory

The source and destination carried the same key set.

No secret values are recorded here.

Keys:

- `CRON_SECRET`
- `DISCORD_APPLICATION_ID`
- `DISCORD_BOT_TOKEN`
- `DISCORD_BUG_REPORT_FORUM_CHANNEL_ID`
- `DISCORD_EMOJI_MODE`
- `DISCORD_FAWXZZY_LOGO_EMOJI_ID`
- `DISCORD_FAWXZZY_LOGO_WHITE_EMOJI_ID`
- `DISCORD_FEEDBACK_BUG_EMOJI_ID`
- `DISCORD_FEEDBACK_FEATURE_EMOJI_ID`
- `DISCORD_FEEDBACK_PANEL_CHANNEL_ID`
- `DISCORD_GUILD_ID`
- `DISCORD_MAIN_CHANNEL_ID`
- `DISCORD_MEMBER_SYNC_SECRET`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_SPOTIFY_CLUB_CHANNEL_ID`
- `DISCORD_UPDATE_BOT_ENABLED`
- `DISCORD_UPDATES_CHANNEL_ID`
- `DISCORD_VERIFICATION_BOT_SECRET`
- `DISCORD_VERIFICATION_TOKEN_PEPPER`
- `DISCORD_VERIFIED_ROLE_ID`
- `DISCORD_VERIFY_CHANNEL_ID`
- `FITNESS_ZAC_EMAIL`
- `LEGACY_SUPABASE_ANON_KEY`
- `LEGACY_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NX_DAEMON`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_OAUTH_STATE_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `SPOTIFY_TOKEN_ENCRYPTION_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `TURBO_CACHE`
- `TURBO_DOWNLOAD_LOCAL_ENABLED`
- `TURBO_REMOTE_ONLY`
- `TURBO_RUN_SUMMARY`
- `VERCEL`
- `VERCEL_DEPLOYMENT_WEBHOOK_SECRET`
- `VERCEL_ENV`
- `VERCEL_GIT_COMMIT_AUTHOR_LOGIN`
- `VERCEL_GIT_COMMIT_AUTHOR_NAME`
- `VERCEL_GIT_COMMIT_MESSAGE`
- `VERCEL_GIT_COMMIT_REF`
- `VERCEL_GIT_COMMIT_SHA`
- `VERCEL_GIT_PREVIOUS_SHA`
- `VERCEL_GIT_PROVIDER`
- `VERCEL_GIT_PULL_REQUEST_ID`
- `VERCEL_GIT_REPO_ID`
- `VERCEL_GIT_REPO_OWNER`
- `VERCEL_GIT_REPO_SLUG`
- `VERCEL_OIDC_TOKEN`
- `VERCEL_PROJECT_ID`
- `VERCEL_TARGET_ENV`
- `VERCEL_URL`

## Cleanup Actions Performed

1. verified the repo-root source file existed
2. verified the governed destination directory existed
3. verified the governed destination file already existed
4. captured a key-name-only inventory from source and destination
5. detected differing file content between source and destination without printing values
6. copied the preexisting governed destination to a governed backup path
7. copied the repo-root source file over the governed destination
8. verified the governed destination existed after copy
9. removed the repo-root source file only after destination verification

## Post-Pass Verification

Verified:

- `C:\ATLAS\repos\fawxzzy-fitness\.env.discord-worker` no longer exists
- `C:\ATLAS\secrets\local\fawxzzy-fitness-discord-worker.env` exists
- `C:\ATLAS\secrets\local\fawxzzy-fitness-discord-worker.pre-pass-1.backup.env` exists
- destination is ignored by Git under root `.gitignore`
- backup is ignored by Git under root `.gitignore`

## Git Tracking Status

### Root secret-lane status

- destination file is not tracked
- backup file is not tracked
- both are covered by `secrets/**` ignore rules

### Fitness repo status

Important note:

- `C:\ATLAS\repos\fawxzzy-fitness` was not clean before or after this pass because of unrelated preexisting tracked modifications outside the scope of this cleanup
- this cleanup did not introduce a new tracked diff in the Fitness repo
- the removed source file was ignored local residue, not a tracked file

Observed unrelated preexisting repo residue included:

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

## Rotation Requirement

Current result:

- no immediate rotation needed

Reason:

- this pass moved secret-bearing material into the governed root secrets lane
- no evidence in this pass suggests exposure outside ignored local-only surfaces
- the cleanup was a placement correction, not a compromise response

## Fitness Supabase Profile/Data Hygiene Unblock Status

Immediate blocker result:

- the specific repo-root blocker `repos/fawxzzy-fitness/.env.discord-worker` is cleared

Interpretation:

- Fitness Supabase Profile/Data Hygiene is no longer blocked by this exact repo-root secret residue
- Supabase mutation is still not open by default

Mutation remains gated by:

- export artifact preparation
- rollback posture
- explicit approval for the first mutation pass

## Remaining Secret-Path Blockers

### Still relevant for Discord OS Infrastructure Separation

- `secrets/local/spotify-club-prod.env`
- `repos/fawxzzy-mazer/.env.local`
- `repos/fawxzzy-mazer/.vercel/.env.preview.local`
- `repos/fawxzzy-mazer/.vercel/.env.production.local`

### Still relevant for broader operator hygiene

- repo-local `.vercel/.env*.local` residue under Trove and Mazer
- naming cleanup for `repos/fawxzzy-fitness/.env.prod-local-mirror.example`

## Non-Goals

This pass did not:

- print secret values
- commit any secret file
- rotate credentials
- mutate Supabase
- mutate Vercel
- deploy code
- change Discord runtime behavior directly

## Marker Interpretation

This package justifies:

- Operator Secret Path Hygiene: `55%`
- Fitness Supabase Profile/Data Hygiene: `35%`

It does not yet justify movement for:

- Discord OS Infrastructure Separation
