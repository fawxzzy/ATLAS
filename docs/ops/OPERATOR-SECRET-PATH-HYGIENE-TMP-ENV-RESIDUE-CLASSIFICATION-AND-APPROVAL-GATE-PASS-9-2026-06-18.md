# Operator Secret Path Hygiene Tmp Env Residue Classification And Approval Gate Pass 9 - 2026-06-18

- Date: `2026-06-18`
- Lane: `Operator Secret Path Hygiene`
- Mode: `docs-only root-bounded residue classification`
- Scope: `live tmp env residue, key-name-only inventory, and approval-gated next-step freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-LOCAL-SECRET-BOUNDARY-AND-QUARANTINE-POSTURE-PASS-8-2026-06-02.md`
  - `docs/atlas-book/10-failure-modes-and-recovery.md`
  - `.gitignore`
  - name-only local inspection of `tmp/*.env`
  - key-name-only inventory of the live `tmp/*.env` files with no value capture
  - `git -C . check-ignore -v -- tmp/fitness-outbox-retry.env tmp/fitness-pr61-production.env tmp/fitness-preview.env tmp/fitness-prod-discord.env`
  - `python ops/validation/validate_stack.py --ratchet`

## Objective

Freeze the newly re-opened secret-path residue class now that live `.env` files exist under ignored `tmp/**` instead of governed `secrets/**`, while staying on the safe side of the approval boundary for any real secret-handling mutation.

## Durable Starting Truth

Already frozen before this packet:

- `Operator Secret Path Hygiene` sits at `64%`
- governed active local secret paths still belong only under ignored `secrets/**`
- quarantine remains a special governed posture under `secrets/local/archive-quarantine/**`, not a general excuse for secret-bearing residue elsewhere
- the pass-8 posture explicitly said to reopen this lane only if new ambiguous secret-bearing local paths appear outside the governed classes, if archive secret-handling reopens, or if operator approval work opens

## New Reopen Condition

That reopen condition is now real.

Name-only local inspection found these live ignored files outside governed `secrets/**`:

- `tmp/fitness-outbox-retry.env`
- `tmp/fitness-pr61-production.env`
- `tmp/fitness-preview.env`
- `tmp/fitness-prod-discord.env`

`git check-ignore -v` confirms they are ignored only because `.gitignore` contains `tmp/**`.

That ignore posture prevents accidental tracking, but it does not make `tmp/**` a governed secret lane.

## Key-Name-Only Inventory

No values were copied into this receipt. Only variable names were inventoried.

### `tmp/fitness-outbox-retry.env`

- Discord/auth/runtime keys include `DISCORD_BOT_TOKEN`, `DISCORD_MEMBER_SYNC_SECRET`, `DISCORD_VERIFICATION_BOT_SECRET`, `DISCORD_VERIFICATION_TOKEN_PEPPER`
- Supabase keys include `SUPABASE_SERVICE_ROLE_KEY`, `LEGACY_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Vercel/deploy keys include `VERCEL_DEPLOYMENT_WEBHOOK_SECRET`, `VERCEL_OIDC_TOKEN`, `VERCEL_PROJECT_ID`

### `tmp/fitness-pr61-production.env`

- Discord/auth/runtime keys include `DISCORD_BOT_TOKEN`, `DISCORD_MEMBER_SYNC_SECRET`, `DISCORD_VERIFICATION_BOT_SECRET`, `DISCORD_VERIFICATION_TOKEN_PEPPER`
- Spotify keys include `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_OAUTH_STATE_SECRET`, `SPOTIFY_TOKEN_ENCRYPTION_KEY`
- Supabase keys include `SUPABASE_SERVICE_ROLE_KEY`, `LEGACY_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Vercel/deploy keys include `VERCEL_DEPLOYMENT_WEBHOOK_SECRET`, `VERCEL_OIDC_TOKEN`, `VERCEL_PROJECT_ID`

### `tmp/fitness-preview.env`

- Supabase keys include `SUPABASE_SERVICE_ROLE_KEY`, `LEGACY_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Vercel/deploy keys include `VERCEL_OIDC_TOKEN` plus the `VERCEL_*` runtime/deploy metadata family

### `tmp/fitness-prod-discord.env`

- Cron and Discord/auth/runtime keys include `CRON_SECRET`, `DISCORD_BOT_TOKEN`, `DISCORD_MEMBER_SYNC_SECRET`, `DISCORD_VERIFICATION_BOT_SECRET`, `DISCORD_VERIFICATION_TOKEN_PEPPER`
- Spotify keys include `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_OAUTH_STATE_SECRET`, `SPOTIFY_TOKEN_ENCRYPTION_KEY`
- Supabase keys include `SUPABASE_SERVICE_ROLE_KEY`, `LEGACY_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Vercel/deploy keys include `VERCEL_DEPLOYMENT_WEBHOOK_SECRET`, `VERCEL_OIDC_TOKEN`, `VERCEL_PROJECT_ID`

## Classification Result

- these files are a live secret-bearing local residue class
- they are not valid governed active secret paths because they live under `tmp/**` rather than `secrets/**`
- their ignored status reduces git exposure but does not satisfy the lane's placement rule
- this packet intentionally does not open file-value review, movement, deletion, or retention-policy mutation

## Marker Decision

- `none`

Why:

- no secret-bearing file was moved into a governed secret lane yet
- no source residue was removed yet
- no broader adoption or proof-backed cleanup execution widened yet
- the lane is clearer, but the blocking work is still an approval-gated mutation rather than a completed cleanup

## Exact Next Package

The exact next honest move is now explicit rather than generic:

1. obtain operator approval for the governed destination and retention posture of these four `tmp/*.env` files
2. after approval, run one bounded cleanup pass that:
   - keeps inventory at key-name-only level
   - moves the files into an approved governed `secrets/**` lane or approved quarantine-only secret lane
   - verifies source removal from `tmp/**`
   - verifies resulting ignore posture
   - refreshes root restart truth and marker posture only if one real residue class is actually cleared

Without that approval, the lane may classify and hold but not claim `100%`.

## Validation

- `python ops/validation/validate_stack.py --ratchet`
- final snapshot: `critical=0 error=0 warning=3 info=0`

## Rule

Ignored `tmp/**` is not a secret lane.

## Pattern

detect live secret-bearing residue outside governed `secrets/**` -> inventory key names only -> freeze approval gate before mutation -> move only after explicit operator consent

## Failure Mode

Secret residue normalization theater: ignored temp files get treated as "good enough" and keep living outside the governed secret boundary because they are not tracked, even though the lane doctrine says placement matters as much as git exposure.
