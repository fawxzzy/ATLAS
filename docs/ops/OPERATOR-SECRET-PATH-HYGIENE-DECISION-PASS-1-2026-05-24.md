# Operator Secret Path Hygiene Decision Pass 1

Date: 2026-05-24
Lane: Operator Secret Path Hygiene
Mode: decision-only
Status: first decision routing recorded

## Goal

Decide how the current secret-bearing and auth-path residue should be handled before opening Fitness Supabase Profile/Data Hygiene or Discord OS Infrastructure Separation.

This pass does not:

- print secret values
- pull env
- move files
- delete files
- rotate credentials
- mutate Vercel, Supabase, or Discord

## Decision Labels

- `keep in governed secrets lane`
- `move to governed secrets lane later`
- `delete later after backup/receipt`
- `rotate/revoke needed`
- `document only`
- `manual owner review`

Interpretation rule:

- each finding gets one primary next action
- a later cleanup command, backup need, and rotation need are recorded separately
- `.vercel/project.json` files are treated as identity metadata, not secret material

## Governing Decision Rule

Use root `secrets/**` as the only default secret-bearing local lane.

That means:

- repo-root `.env*` files with real secret material are exceptions that should be retired or relocated
- ignored `.vercel/.env*.local` files are still secret-bearing auth residue even when Vercel generated them locally
- tracked example files that contain placeholders only are not secret leaks, but their naming should avoid looking like live operator env truth
- ignored `.vercel/project.json` files remain acceptable because they are identity-only and support deploy guardrails

## Decision Matrix

| Path | Contains actual secret material? | Git status | Primary decision | Blocks Fitness Supabase cleanup | Blocks Discord OS separation | Later cleanup command needed? | Rollback/export requirement | Rotation requirement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `secrets/fitness-doctor.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/fitness-lps-dev.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/fawxzzy-fitness-discord-bot.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/fawxzzy-fitness-discord-prod.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/fawxzzy-fitness-discord-worker.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/fawxzzy-fitness-preview-gate.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/fawxzzy-fitness-prod-db.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/fitness-prod-to-local.env` | yes | ignored | keep in governed secrets lane | no | no | no immediate change | none beyond current local-only retention | no immediate rotation from this pass |
| `secrets/local/spotify-club-prod.env` | yes | ignored | manual owner review | no | yes | yes, later rename or split under current Music Sesh/Discord OS naming once owner and target runtime are explicit | keep until replacement secret path is created and referenced | maybe later, only if separation changes provider/app ownership |
| `repos/fawxzzy-fitness/.env.discord-worker` | yes | ignored | move to governed secrets lane later | yes | yes | yes, later remove repo-root mirror after root `secrets/` path is confirmed as the only runtime source | root secret file must exist and worker/runtime must be proven on replacement path before deletion | no immediate rotation required if file is relocated without exposure |
| `repos/fawxzzy-fitness/.env.prod-local-mirror.example` | no, placeholder/example only | tracked | document only | no | no | yes, later rename away from `.env*` shape or move to a docs/examples contract path | no backup needed; git history is already rollback | no |
| `repos/fawxzzy-mazer/.env.local` | yes | ignored | delete later after backup/receipt | no | yes | yes, later export key-name contract if still needed and remove repo-root secret file | record whether any local workflow still depends on it before deletion | maybe later; if token value is stale or replaced, revoke as part of cleanup |
| `repos/fawxzzy-trove/.vercel/.env.preview.local` | yes | ignored | move to governed secrets lane later | no | no | yes, later either relocate auth dependency or delete local Vercel env residue after proof | verify no local deploy workflow still relies on the file | maybe later; depends on whether Vercel token remains active and user wants revocation |
| `repos/fawxzzy-trove/.vercel/.env.production.local` | yes | ignored | move to governed secrets lane later | no | no | yes | verify no local deploy workflow still relies on the file | maybe later |
| `repos/fawxzzy-mazer/.vercel/.env.preview.local` | yes | ignored | move to governed secrets lane later | no | yes | yes | verify no local deploy workflow still relies on the file | maybe later |
| `repos/fawxzzy-mazer/.vercel/.env.production.local` | yes | ignored | move to governed secrets lane later | no | yes | yes | verify no local deploy workflow still relies on the file | maybe later |
| `repos/fawxzzy-fitness/.vercel/project.json` | no, identity only | ignored | document only | no | no | no | none | no |
| `repos/fawxzzy-trove/.vercel/project.json` | no, identity only | ignored | document only | no | no | no | none | no |
| `repos/fawxzzy-mazer/.vercel/project.json` | no, identity only | ignored | document only | no | no | no | none | no |

## Primary Decisions

### Keep In Governed Secrets Lane

The current root `secrets/**` files are the strongest current posture and should remain there for now.

Reason:

- they follow ATLAS root policy
- they are ignored
- they already act as the local-only secret lane for multiple operator workflows

Current decision:

- keep them
- do not rename or split them in this pass
- let later lanes narrow them only when the replacement contract is explicit

### Move To Governed Secrets Lane Later

These files should stop living inside repo roots or repo-local `.vercel` folders and should eventually move to the governed root secret lane or disappear after the runtime path is simplified:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `repos/fawxzzy-trove/.vercel/.env.preview.local`
- `repos/fawxzzy-trove/.vercel/.env.production.local`
- `repos/fawxzzy-mazer/.vercel/.env.preview.local`
- `repos/fawxzzy-mazer/.vercel/.env.production.local`

Reason:

- they contain real auth or secret-bearing material
- they live in repo-root or repo-adjacent paths that should not remain the default trust lane
- they increase ambiguity around where operator auth truth belongs

### Delete Later After Backup/Receipt

Current candidate:

- `repos/fawxzzy-mazer/.env.local`

Reason:

- it is repo-root secret residue
- current value class is narrow enough that this looks more like local auth spillage than a governed reusable lane
- keeping it in place teaches the wrong pattern for later separation work

Prerequisite:

- capture a small receipt confirming whether any local Mazer workflow still relies on it

### Manual Owner Review

Current candidate:

- `secrets/local/spotify-club-prod.env`

Reason:

- it is in the right root secret lane
- but it preserves legacy Spotify Club naming after the Music Sesh rename
- and it is likely to be part of the eventual Discord OS separation conversation

This is not a secret-placement failure. It is a naming and ownership-routing ambiguity that needs an owner decision before cleanup.

### Document Only

Current candidates:

- all three `.vercel/project.json` files
- `repos/fawxzzy-fitness/.env.prod-local-mirror.example`

Reason:

- `.vercel/project.json` is identity metadata and currently useful
- the tracked Fitness example file is not a secret file, but it does need later naming cleanup because `.env*` suggests live operator truth

## Direct Blocking Decisions

### Blocks Fitness Supabase Profile/Data Hygiene

Primary blocker:

- `repos/fawxzzy-fitness/.env.discord-worker`

Decision consequence:

- do not open Fitness Supabase Profile/Data Hygiene until this file has a later cleanup plan with an explicit replacement runtime path in root `secrets/**`

### Blocks Discord OS Infrastructure Separation

Primary blockers or prep issues:

- `repos/fawxzzy-fitness/.env.discord-worker`
- `secrets/local/spotify-club-prod.env`
- `repos/fawxzzy-mazer/.env.local`
- `repos/fawxzzy-mazer/.vercel/.env.preview.local`
- `repos/fawxzzy-mazer/.vercel/.env.production.local`

Decision consequence:

- Discord OS separation may plan around these now
- but should not start mutation or movement work until the secret-lane cleanup plan is explicit

## Later Cleanup Command Shapes

These are not to be run now. They exist only to make the later cleanup tractable.

### Repo-root env retirement

Likely later pattern:

1. confirm root `secrets/**` replacement exists
2. verify runtime/worker reads from the governed root secret lane
3. delete repo-root mirror
4. record receipt

### `.vercel/.env*.local` residue cleanup

Likely later pattern:

1. confirm whether local Vercel workflow still needs the file
2. if needed, move documented auth dependency to governed local secret lane
3. delete `.vercel/.env*.local`
4. rerun deploy-identity preflight to confirm `.vercel/project.json` remains enough

### Legacy secret-lane rename

Likely later pattern for `spotify-club-prod.env`:

1. decide whether it belongs to Fitness, Music Sesh, or future DiscordOS
2. create replacement file name in `secrets/local/`
3. update any live local-only references
4. keep deletion/rename receipt

## Rollback And Export Requirements

Before any future deletion or move:

- capture key-name-only metadata in the receipt if the file is not already inventoried
- confirm the replacement runtime path works
- avoid moving multiple secret-bearing files in one pass unless they share the same owner and runtime

Tracked example-file exception:

- `repos/fawxzzy-fitness/.env.prod-local-mirror.example` already has git history
- it does not need a secret backup
- it only needs a later naming or placement cleanup decision

## Rotation Guidance

No immediate rotation or revocation is required from this decision pass alone.

Rotate or revoke later only when:

- a secret leaves the governed local lane unexpectedly
- a file is discovered to have been copied into the wrong surface
- a separation lane changes ownership enough that old credentials should no longer remain valid

Most current findings are placement and clarity problems, not evidence of exposure.

## Recommended Next Package

Do not start Fitness Supabase Profile/Data Hygiene mutation work yet.

Next clean package:

- `Fitness Supabase Profile/Data Hygiene Inventory`

That inventory can now proceed with the blocker and preparation boundaries explicit:

- no mutation yet
- canonical AI automation identity still to be defined
- auth/profile/data inventory first

## Non-Goals

This pass does not:

- modify secret files
- rename files
- delete files
- rotate credentials
- update workers
- update Vercel local config
- open the Discord OS separation implementation lane

## Marker Interpretation

This package justifies:

- Operator Secret Path Hygiene: `30%`

It does not yet justify movement for:

- Fitness Supabase Profile/Data Hygiene
- Discord OS Infrastructure Separation
