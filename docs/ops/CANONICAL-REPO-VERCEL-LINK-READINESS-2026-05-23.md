# Canonical Repo Vercel Link Readiness

Date: 2026-05-23
Lane: Canonical Repo Restoration + Tmp Dependency Elimination
Status: local operator config checkpoint

## Goal

Restore local Vercel operator linkage at `repos/fawxzzy-fitness` so Vercel-aware local operator flows no longer need the `tmp` production-linked checkout as the active linked repo surface.

## Canonical Repo Preconditions

Verified at `repos/fawxzzy-fitness` before link restore:

- branch: `main`
- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`
- working tree: clean

## Expected Vercel Identity

- project: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- team id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`

Remote confirmation came from:

- Vercel project lookup for `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`

Observed project details:

- name: `fawxzzy-fitness`
- framework: `nextjs`
- latest production deployment: `dpl_2VhJGuxw76qwienem4HwVqB7uGsG`
- latest deployment URL: `fawxzzy-fitness-82o7s2k62-fawxzzy.vercel.app`
- current domains include:
  - `fawxzzy-fitness-local.vercel.app`
  - `fawxzzy-fitness-fawxzzy.vercel.app`
  - `fawxzzy-fitness-zachariahredfield-fawxzzy.vercel.app`

## Local Link Restore

Command used:

- `vercel link --project fawxzzy-fitness --scope fawxzzy --yes`

Result:

- passed
- local `.vercel` directory created at the canonical repo root
- local project metadata now points to the expected canonical Vercel identity

Created local metadata:

- `.vercel/project.json`

Current contents:

```json
{"projectId":"prj_rtlFVOMFAWCRoJ3SQjHloi89881K","orgId":"team_CMJn7MvzFZZBnhNnjVUZF2RD","projectName":"fawxzzy-fitness"}
```

## Hygiene Checks

### Was `.vercel/project.json` restored locally?

- yes

### Is local `.vercel` ignored?

- yes

Verification:

- `git check-ignore .vercel/project.json .vercel`

Result:

- `.vercel/project.json`
- `.vercel`

### Did linking pull env or secrets?

- no env pull was run
- no `.env*` files were created
- no secret material was added to the repo root during this pass

### Did the repo stay clean?

- yes
- after linking, `git status --short` remained empty

## Non-Deploying Sanity Checks

### Local Vercel CLI presence

- `vercel --version` -> `Vercel CLI 50.41.0`

### Local identity check

- `vercel whoami --scope fawxzzy` -> `zachariahredfield`

### Remote project identity check

- Vercel project lookup matched the expected project id and team id

No deploy, env pull, or project mutation was performed.

## Tmp Dependency Assessment

What this pass removes:

- the need to rely on `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` as the only locally linked Vercel-aware Fitness repo surface

What may still keep `tmp` around for now:

- retained fallback/reference value until `_stack` deploy and verify lanes are proven against the restored canonical repo root
- any historical receipts or operator notes still written around the earlier `tmp` lane

Current verdict:

- `tmp` is no longer required for canonical repo source verification
- `tmp` is no longer required for local Vercel link presence
- `tmp` may still remain as a temporary fallback/reference surface until `_stack` operator path verification is completed

## Remaining Blockers Before Canonical Repo Restoration Reaches 100%

1. prove `_stack` Fitness operator flows resolve cleanly against `repos/fawxzzy-fitness`
2. verify no production-critical Fitness workflow still defaults to the `tmp` checkout
3. classify when the `tmp` production-linked checkout can be demoted from active dependency to retained fallback/evidence only

## Closeout Verdict

Canonical Fitness repo operator linkage is now restored locally without committing local config, env files, or secrets.

The remaining work is not source restoration or local Vercel link recovery. It is final operator-path proof and `tmp` dependency burn-down.
