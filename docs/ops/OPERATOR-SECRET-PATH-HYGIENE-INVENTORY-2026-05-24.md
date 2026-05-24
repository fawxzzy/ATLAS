# Operator Secret Path Hygiene Inventory

Date: 2026-05-24
Lane: Operator Secret Path Hygiene
Mode: inventory only
Status: first hygiene inventory recorded

## Goal

Classify local secret, env, auth, Vercel-link, and Supabase-related residue across operator workflows before opening Fitness Supabase Profile/Data Hygiene or Discord OS Infrastructure Separation.

This pass does not:

- pull env
- print secret values
- delete files
- mutate Vercel, Supabase, or Discord
- change Fitness, `_stack`, Trove, or Mazer runtime code

## Scope Inspected

- ATLAS root
- `repos/_stack`
- `repos/fawxzzy-fitness`
- `repos/fawxzzy-trove`
- `repos/fawxzzy-mazer`
- local `secrets/**`
- local Vercel link surfaces
- local env-file surfaces
- local Supabase-config surfaces
- recovery and operator docs that reference secret/env/auth paths

## High-Level Findings

1. The root `secrets/` lane is active and correctly ignored.
   It contains the strongest current local-only secret material and remains the only clearly allowed canonical secret location under ATLAS policy.

2. Secret-bearing env mirrors still exist inside repo roots.
   The strongest current repo-root residue is in:
   - `repos/fawxzzy-fitness/.env.discord-worker`
   - `repos/fawxzzy-mazer/.env.local`
   - `.vercel/.env.preview.local` and `.vercel/.env.production.local` under Trove and Mazer

3. `.vercel/project.json` should not be treated like a secret file.
   These files contain local Vercel identity metadata only, are ignored, and are actively used by deploy-identity guardrails. They are local/ignored but non-secret.

4. No inspected repo currently has a local `supabase/config.toml`.
   That means current Supabase operator flows are env/secret driven rather than CLI-linked local config driven.

5. No local `repos/DiscordOS` repo exists yet.
   Discord OS Infrastructure Separation is still a future lane, not a local source surface today.

## Key Path Inventory

| Path | File type | Git status | Secret-bearing or identity-only | Owner repo/lane | Allowed location? | Cleanup needed? | Blocks Fitness Supabase Profile/Data Hygiene | Blocks Discord OS Infrastructure Separation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `secrets/fitness-doctor.env` | env file | ignored | secret-bearing | ATLAS root / operator auth lane | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/fitness-lps-dev.env` | env file | ignored | secret-bearing | ATLAS root / Fitness local-dev lane | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/fawxzzy-fitness-discord-bot.env` | env file | ignored | secret-bearing | ATLAS root / Discord bot ops | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/fawxzzy-fitness-discord-prod.env` | env file | ignored | secret-bearing | ATLAS root / Discord verification prod secrets | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/fawxzzy-fitness-discord-worker.env` | env file | ignored | secret-bearing | ATLAS root / Discord worker runtime | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/fawxzzy-fitness-preview-gate.env` | env file | ignored | secret-bearing | ATLAS root / Fitness preview proof lane | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/fawxzzy-fitness-prod-db.env` | env file | ignored | secret-bearing | ATLAS root / Fitness DB auth lane | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/fitness-prod-to-local.env` | env file | ignored | secret-bearing | ATLAS root / Fitness prod-to-local mirror lane | yes | no immediate cleanup; keep local-only | no | no |
| `secrets/local/spotify-club-prod.env` | env file | ignored | secret-bearing | ATLAS root / legacy Spotify/Music Sesh ops | yes | later review under Discord OS separation; name still reflects legacy surface | no | yes, because it preserves pre-separation legacy coupling |
| `repos/fawxzzy-fitness/.env.discord-worker` | env file | ignored | secret-bearing | Fitness repo / Discord worker lane | no | yes; secrets should move to root `secrets/` only and repo-root mirror should be retired or clearly replaced | yes | yes |
| `repos/fawxzzy-fitness/.env.prod-local-mirror.example` | env-like example file | ignored | non-secret example / project mapping only | Fitness repo / prod-to-local docs lane | ambiguous | yes, low-priority cleanup; rename away from `.env*` shape later to reduce operator confusion | no | no |
| `repos/fawxzzy-mazer/.env.local` | env file | ignored | secret-bearing (`VERCEL_OIDC_TOKEN`) | Mazer repo / local Vercel auth residue | no | yes; repo-root secret residue should be moved out or removed later | no | yes, because it shows repo-root auth spillage that future separation work should avoid |
| `repos/fawxzzy-trove/.vercel/.env.preview.local` | Vercel local env file | ignored | secret-bearing (`VERCEL_OIDC_TOKEN` plus deploy metadata) | Trove repo / Vercel local auth residue | no for long-term secret posture | yes; keep inventoried now, later retire or move to explicit secret lane if workflow still needs it | no | no |
| `repos/fawxzzy-trove/.vercel/.env.production.local` | Vercel local env file | ignored | secret-bearing (`VERCEL_OIDC_TOKEN` plus deploy metadata) | Trove repo / Vercel local auth residue | no for long-term secret posture | yes | no | no |
| `repos/fawxzzy-mazer/.vercel/.env.preview.local` | Vercel local env file | ignored | secret-bearing (`VERCEL_OIDC_TOKEN` plus deploy metadata) | Mazer repo / Vercel local auth residue | no for long-term secret posture | yes | no | yes, because it is another repo-root secret/auth residue pattern |
| `repos/fawxzzy-mazer/.vercel/.env.production.local` | Vercel local env file | ignored | secret-bearing (`VERCEL_OIDC_TOKEN` plus deploy metadata) | Mazer repo / Vercel local auth residue | no for long-term secret posture | yes | no | yes |
| `repos/fawxzzy-fitness/.vercel/project.json` | Vercel identity file | ignored | identity-only | Fitness repo / deploy authority | yes, local ignored identity metadata is acceptable | no immediate cleanup | no | no |
| `repos/fawxzzy-trove/.vercel/project.json` | Vercel identity file | ignored | identity-only | Trove repo / deploy authority | yes, local ignored identity metadata is acceptable | no immediate cleanup | no | no |
| `repos/fawxzzy-mazer/.vercel/project.json` | Vercel identity file | ignored | identity-only | Mazer repo / deploy authority | yes, local ignored identity metadata is acceptable | no immediate cleanup | no | no |

## Secret Key Classes Observed

Without printing values, the current local secret-bearing surfaces include keys from these classes:

- Supabase service-role and database auth
- Discord bot, verification, member-sync, and poll secrets
- Spotify client, redirect, encryption, and OAuth state secrets
- Vercel deployment webhook secret
- Vercel OIDC token and local deployment metadata
- local QA or operator credentials

Operational interpretation:

- the stack is not leaking these values into tracked files from this inventory pass
- but it is still allowing multiple repo-root or `.vercel` local env files to act as convenience secret mirrors

That is the core hygiene issue to fix later.

## Safe Non-Secret Identity Surfaces

The following local files are not treated as secret leaks in this pass:

- `repos/fawxzzy-fitness/.vercel/project.json`
- `repos/fawxzzy-trove/.vercel/project.json`
- `repos/fawxzzy-mazer/.vercel/project.json`

Reason:

- they contain project identity only
- they are ignored locally
- they are actively used by `_stack` fail-closed deploy identity checks
- removing them without a replacement would weaken deploy-identity verification

## Absent Or Missing Surfaces

The following expected future or optional surfaces are not present locally right now:

- `repos/DiscordOS`
- `repos/fawxzzy-fitness/supabase/config.toml`
- `repos/fawxzzy-trove/supabase/config.toml`
- `repos/fawxzzy-mazer/supabase/config.toml`
- `repos/_stack/supabase/config.toml`
- any `_stack` repo-local `.env*` or `.vercel/project.json` file from the current inventory scope

Interpretation:

- Discord OS Infrastructure Separation has not started as a local repo lane yet
- Supabase CLI local project linkage is not the current dominant operator pattern in these repos

## Documentation And Operator-Flow Findings

Current docs explicitly reinforce some good posture:

- root policy says secrets belong only in `secrets/`
- Fitness docs repeatedly say local-only secrets must remain uncommitted
- `_stack` runbooks document required env keys without storing values
- release docs explicitly say not to store secrets in release artifacts

Current docs also reveal where later cleanup pressure will land:

- Fitness local/prod data sync depends on local secret/env lanes
- Discord feedback, updates, verification, and Music Sesh docs rely on many env-backed runtime surfaces
- legacy Spotify naming still appears in at least one root secret file name: `spotify-club-prod.env`

## Risk Classification

### Low-risk / acceptable current posture

- root `secrets/**` ignored local-only files
- ignored `.vercel/project.json` identity files
- doc-only references to env variable names without values

### Medium-risk hygiene residue

- repo-root env files with secrets
- ignored `.vercel/.env.*.local` files containing Vercel auth material
- legacy file naming that preserves old platform coupling after product renames

### No evidence found in this pass

- tracked committed secret files in the inspected scope
- local `supabase/config.toml` files in the inspected repos
- local DiscordOS repo or standalone secret surface yet

## Blocking Interpretation

### Blocks Fitness Supabase Profile/Data Hygiene

Direct blockers from this inventory:

- `repos/fawxzzy-fitness/.env.discord-worker`

Reason:

- it keeps secret-bearing runtime material inside the Fitness repo root
- a Supabase profile/data hygiene pass should not start while secret-bearing repo-root mirrors still blur where operator auth truth belongs

### Blocks Discord OS Infrastructure Separation

Direct blockers or preparatory hygiene issues from this inventory:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `secrets/local/spotify-club-prod.env`
- `repos/fawxzzy-mazer/.env.local`
- `repos/fawxzzy-mazer/.vercel/.env.preview.local`
- `repos/fawxzzy-mazer/.vercel/.env.production.local`

Reason:

- the first two preserve Fitness-hosted/legacy Discord or Spotify coupling in naming and placement
- the Mazer files show the broader hygiene pattern that future standalone Discord OS infrastructure should avoid repeating

Trove `.vercel/.env.*.local` is also a hygiene finding, but it does not directly block Discord OS separation sequencing as strongly as the Fitness/legacy Spotify surfaces do.

## Recommended Next Package

After this inventory:

1. do not start Fitness Supabase Profile/Data Hygiene mutations yet
2. run a narrow `Operator Secret Path Hygiene Decision Pass`
3. decide which repo-root env mirrors and `.vercel/.env.*.local` files should be:
   - moved to root `secrets/`
   - renamed as non-secret examples
   - retained temporarily with explicit exception
   - deleted later after replacement

Priority targets for that decision pass:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `repos/fawxzzy-fitness/.env.prod-local-mirror.example`
- `repos/fawxzzy-mazer/.env.local`
- `repos/fawxzzy-trove/.vercel/.env.preview.local`
- `repos/fawxzzy-trove/.vercel/.env.production.local`
- `repos/fawxzzy-mazer/.vercel/.env.preview.local`
- `repos/fawxzzy-mazer/.vercel/.env.production.local`
- `secrets/local/spotify-club-prod.env`

## Non-Goals

This inventory does not:

- delete any file
- print or verify secret values
- mutate Vercel or Supabase
- open the Fitness Supabase cleanup lane
- open the Discord OS separation lane
- replace current worker/runtime auth loading

## Marker Interpretation

This package justifies:

- Operator Secret Path Hygiene: `20%`

It does not yet justify movement for:

- Fitness Supabase Profile/Data Hygiene
- Discord OS Infrastructure Separation
