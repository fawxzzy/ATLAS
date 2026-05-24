# Vercel Stale Surface Decommission Inventory

Date: 2026-05-24
Lane: Duplicate Surface Decommission + Manual Deploy Exception Burn-Down
Mode: inventory only
Status: stale-surface inventory recorded

## Goal

Classify stale Spotify and board-related Vercel projects and aliases so they can later be removed, retained, or archived without breaking canonical Fitness or live Discord operations.

This pass does not:

- delete Vercel projects
- remove aliases or domains
- disconnect Git
- mutate deployments
- change DNS
- change Discord OAuth or Spotify OAuth callback state
- change Fitness app code
- change Supabase

## Canonical Comparison Surface

Current canonical Fitness Vercel surface:

- project name: `fawxzzy-fitness`
- project ID: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- team ID: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- current production alias: `fawxzzy-fitness-local.vercel.app`
- current latest deployment: `dpl_ETwuRu3E2YWjgpRVJUrE9siQs8kT`

Local `.vercel/project.json` for Fitness also confirms:

- `projectId = prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- `orgId = team_CMJn7MvzFZZBnhNnjVUZF2RD`
- `projectName = fawxzzy-fitness`

## Local Reference Check

Workspace-wide search results show:

- no current local code, docs, or scripts referencing:
  - `spotify-club-phase-7-interaction-re.vercel.app`
  - `spotify-board-hygiene-main.vercel.app`
  - the two stale project names
- current Fitness Discord, update, webhook, OAuth, and bot-facing docs point to canonical Fitness production surfaces instead
- current Spotify OAuth docs and code use the Fitness-hosted callback pattern:
  - `https://<fitness-host>/api/spotify/oauth/callback`
  - current canonical examples and defaults point at `fawxzzy-fitness-local.vercel.app`

Operational implication:

- no current governed workspace artifact proves these stale Vercel aliases are still part of the intended live Fitness or Discord OS surface
- if they are still needed, that need is not visible in current code or docs

## Inventory Table

| Surface | Project ID | Latest deployment | Aliases | Status | Source branch/SHA | Git linkage signal | Why stale or risky | Deletion risk | Owner | Recommended action | Verification required before deletion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `spotify-club-phase-7-interaction-reliability` | `prj_RGLW6lMbxlBbbltdzLHVGpyejI9h` | `dpl_8Tjn5Y6rGU6z7Fw2GsBFhYbeZNDR` | `spotify-club-phase-7-interaction-re.vercel.app`, `spotify-club-phase-7-interaction-reliability-fawxzzy.vercel.app` | READY production deployment, project `live=false` | ref `codex/spotify-club-phase-7-connect-short-oauth-link`, sha `9b756b16cdb389b255a2bc9101df637c85bbcfa9` | deployment source is `cli`; metadata shows old Spotify Club branch work merged into Fitness `main` | creates a second public Vercel surface for old Spotify Club work outside canonical Fitness naming and deploy authority; can be mistaken for current Music Sesh or Fitness production truth | Medium: could still be bookmarked or manually visited, but no current governed workspace reference was found | ATLAS + Fitness + Vercel team owner | delete later | confirm no live Discord post, OAuth provider config, or external bookmark/runbook still references the alias; confirm canonical Fitness project already covers the same behavior; optionally archive deployment metadata receipt first |
| `spotify-board-hygiene-main` | `prj_UB4thVPyHdZdZdtTC8lDggWauTZE` | `dpl_BnpVXEYJUPNXTNQ2ruGeEgNLsRBF` | `spotify-board-hygiene-main.vercel.app`, `spotify-board-hygiene-main-fawxzzy.vercel.app`, `spotify-board-hygiene-main-zachariahredfield-fawxzzy.vercel.app` | READY production deployment, project `live=false` | ref `HEAD`, sha `ea199a886d596d93779dfe7856962fe86542b489` | deployment source is `cli`; metadata shows one-off board hygiene deployment from Fitness history | creates a separate project and public aliases for a narrow board-hygiene slice that now belongs under canonical Fitness/Discord workflow surfaces; strongest risk is operator confusion and shadow-public history | Medium: lower chance of being a required OAuth surface, but still a real public deployment alias family that could confuse current docs or operators | ATLAS + Fitness + Vercel team owner | delete later | confirm no Discord setup/update post, no automation script, and no manual operator doc still points to the aliases; capture final metadata receipt before deletion if historical evidence is desired |

## Detailed Findings

### 1. Both targets are real current Vercel surfaces, not doc ghosts

Confirmed by live Vercel project and deployment metadata:

- both projects exist under team `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- both have READY latest deployments
- both deployments target `production`
- both were created from `cli`
- both still carry public `.vercel.app` aliases

### 2. Both targets point to older Fitness-hosted Spotify/board work, not separate product roots

Evidence:

- both deployments use `framework = nextjs`
- both deployment metadata point to Fitness repo history:
  - `9b756b16...` is present on current Fitness `main`
  - `ea199a88...` is present on current Fitness `main`
- one deployment explicitly records the old branch ref:
  - `codex/spotify-club-phase-7-connect-short-oauth-link`
- the other records `HEAD`, which is typical of a one-off CLI deployment rather than a governed product deployment contract

Operational implication:

- these are not independent app families
- they are stale public deployment surfaces spun out of Fitness history

### 3. Canonical current OAuth and bot-facing surfaces point to Fitness, not the stale projects

Current local evidence points to canonical Fitness surfaces for:

- Discord verification login links
- Discord updates webhook guidance
- bot-facing production URLs
- Spotify OAuth redirect examples and code paths

No current governed workspace reference points at:

- `spotify-club-phase-7-interaction-re.vercel.app`
- `spotify-board-hygiene-main.vercel.app`

### 4. Main remaining risk is operator/public confusion, not immediate source-truth takeover

Current risk profile:

- low evidence of active code dependency
- medium risk of human confusion from lingering public aliases and extra projects
- medium risk of future wrong-surface troubleshooting or mistaken deploy authority assumptions

This means the surfaces are best treated as:

- stale duplicate public/deploy surfaces
- likely safe-delete-later candidates
- not delete-now candidates until one more verification pass confirms no live external dependency

## Overlap With Canonical Fitness Project

Canonical Fitness project:

- `fawxzzy-fitness`
- `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

Stale surfaces do overlap the canonical project in purpose history:

- both came from Fitness-hosted Discord/Spotify-related work
- both are now outside the approved canonical naming and deploy authority path
- neither should remain ambiguous beside the canonical Fitness project long term

They do not appear to overlap current canonical runtime linkage in local docs/code:

- current docs/code do not reference their aliases
- current worker/update/OAuth surfaces reference canonical Fitness instead

## Recommended Disposition

### Recommended action now

Do not delete yet.

Next safe package:

- `Vercel Stale Surface Decommission Decision Pass`

### Expected likely final action

For both surfaces:

- `delete later`

Reason:

- they are real public deployment surfaces
- they are not current canonical project surfaces
- no active local governed reference was found
- they materially increase duplicate-surface and deploy-authority confusion

### Archive-evidence recommendation

Before any deletion:

- preserve project metadata
- preserve latest deployment metadata
- preserve alias list
- preserve source commit/ref linkage

That can live as one ATLAS receipt rather than keeping the Vercel projects alive forever.

## Verification Required Before Deletion

Before deleting either project or alias set, verify:

1. no current local docs, scripts, or repo code reference the alias or project name
2. no current Discord update/setup/community surface points users to these aliases
3. no current OAuth provider config uses either alias as callback or origin
4. canonical Fitness project still owns the intended live Discord/Spotify behavior
5. deletion is recorded in a dedicated disposal receipt

## Lane Interpretation

This inventory moves the stale Vercel work out of vague concern and into explicit governed cleanup scope.

It supports:

- Duplicate Surface Decommission
- Manual Deploy Exception Burn-Down

It does not yet justify:

- deleting the Vercel projects
- deleting aliases
- changing OAuth or Discord runtime configuration
- changing Fitness deploy authority

## Marker Interpretation

This package justifies:

- Duplicate Surface Decommission: `88%`
- Manual Deploy Exception Burn-Down: `70%`
