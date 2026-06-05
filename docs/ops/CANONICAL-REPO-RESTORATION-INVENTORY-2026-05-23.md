# Canonical Repo Restoration Inventory

Date: 2026-05-23
Lane: Canonical Repo Restoration + Tmp Dependency Elimination
Status: inventory

## Goal

Determine the real canonical Fitness repo surface, confirm the production GitHub/Vercel/Supabase linkage, identify where `_stack` and ATLAS still assume the old canonical path, and document what must change before Fitness can run again from `repos/fawxzzy-fitness`.

## Executive Verdict

- `repos/fawxzzy-fitness` does not exist on disk today.
- The production-linked Fitness checkout currently lives at `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`.
- `_stack`, `stack.yaml`, and ATLAS planning/docs still contract against `repos/fawxzzy-fitness` as the canonical owner repo.
- The live production GitHub remote, Vercel project, and production Supabase target are still internally consistent.
- The current failure is not identity drift between GitHub/Vercel/Supabase. The failure is canonical path drift: the trusted owner repo root is missing, so production-critical work is being forced through `tmp/`.

## Current Surface Inventory

| Surface | Current state | Git posture | Production linkage | Canonical verdict |
| --- | --- | --- | --- | --- |
| `repos/fawxzzy-fitness` | missing | none | none because the path is absent | intended canonical root, currently broken |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | present | `main` at `7ceebde9` tracking `origin/main` | GitHub remote `fawxzzy/fawxzzy-fitness`; Vercel project `fawxzzy-fitness` / `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`; prod URL `https://fawxzzy-fitness-local.vercel.app` | current live canonical candidate stranded under `tmp/` |
| `tmp/fitness-main-post-merge` | present | detached snapshot at `710c7f20` | same GitHub remote and same Vercel project metadata | historical snapshot, not a canonical target |
| `repos/fawxzzy-fitness.reclone.20260502-195639` | missing | none | none | historical recovery surface named in `stack.yaml`, absent on disk |
| `repos/fawxzzy-fitness-recovered` | missing | none | none | historical recovery surface named in `stack.yaml`, absent on disk |
| `repos/fawxzzy-fitness-parity-recovery` | missing | none | none | historical recovery surface named in `stack.yaml`, absent on disk |

## Canonical Linkage Evidence

### GitHub

- Current live repo remote:
  - `https://github.com/fawxzzy/fawxzzy-fitness.git`
- Verified in:
  - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
  - `tmp/fitness-main-post-merge`

### Vercel

- Canonical project config in the live checkout:
  - project name: `fawxzzy-fitness`
  - project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
  - org id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- Matching `_stack` deploy identity:
  - `repos/_stack/config/fitness-deploy.identity.json`
- Current production URL observed in the live release ledger:
  - `https://fawxzzy-fitness-local.vercel.app`

### Supabase

- Production-aligned Fitness project ref:
  - `lpswxoyfniocuhljgzbc`
- Production-aligned host:
  - `lpswxoyfniocuhljgzbc.supabase.co`
- Evidence:
  - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/.env.prod-local-mirror.example`
  - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/README.md`
  - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/scripts/env-file.mjs`
  - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7/src/lib/dev-supabase-target.ts`

## Contract Drift

### ATLAS stack contract still points to the missing repo root

- `stack.yaml` still declares:
  - `fitness.path: repos/fawxzzy-fitness`
- `README-STACK.md` still states:
  - Fitness is normalized on disk at `repos/fawxzzy-fitness`
- Numerous docs, audits, runbooks, and QA maps still point at `repos/fawxzzy-fitness` as the owner repo surface.

This means the official contract is still correct in intent, but broken in reality because the canonical path is absent.

### `_stack` operator surfaces still assume the missing canonical root

Current `_stack` examples:

- `repos/_stack/templates/child-task-handoff.md`
- `repos/_stack/queue/README.md`
- `repos/_stack/docs/dispatcher-protocol.md`
- `repos/_stack/docs/fitness-verify.md`
- `repos/_stack/docs/runbooks/FITNESS-QA-LOCAL-LOOP.md`

These surfaces still route Fitness work to `repos/fawxzzy-fitness`, which is the right long-term contract. The immediate problem is that the filesystem no longer satisfies that contract.

### `_stack` manual deploy policy is internally consistent but blocked by path drift

`repos/_stack/docs/ops/fitness-vercel-deploy-recovery.md` says:

- do not deploy Fitness directly from `repos/fawxzzy-fitness`
- use `_stack` deploy commands instead

That deploy governance is still valid. The path drift problem is separate: Fitness source, verify, and QA lanes still assume the canonical repo exists on disk even though the live checkout is currently under `tmp/`.

## Tmp Dependency Inventory

### What is currently forced through `tmp/`

- the live production-linked Fitness checkout
- branding refresh work already applied to Fitness
- current repo-local deploy and release metadata
- current Discord update workflow code and tests
- current production-aligned Supabase target guards

### What is not yet governed as canonical

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` is live and linked, but its path class is still temporary
- `tmp/fitness-main-post-merge` remains a detached snapshot and should not become canonical by accident
- many other `tmp/fitness*` folders exist as historical, QA, deploy, or scratch surfaces and create hidden source-of-truth risk until the canonical root is restored

### Important nuance

There is not yet strong evidence that `_stack` has been officially repointed to `tmp/`.

The current risk is worse:

- governed docs still point to the intended canonical root
- operator reality has drifted into `tmp/` because the intended canonical root disappeared

That is why both `Canonical Repo Restoration` and `Tmp Dependency Elimination` need separate markers.

## Release And Recovery Drift Signals

The strongest regression signal is the current live Fitness release ledger inside the `tmp` checkout.

It records that the standalone Fitness clone had already been promoted into `repos/fawxzzy-fitness`, but that path is now missing. That means:

- the GitHub/Vercel/Supabase identity was successfully stabilized earlier
- the canonical owner-repo root later regressed out of place
- restoration now needs to re-establish the on-disk canonical root without treating the `tmp` checkout as the long-term home

## What Must Change Before Deploy Or Verify Can Run From `repos/fawxzzy-fitness`

1. Recreate `repos/fawxzzy-fitness` as the canonical owner-repo root from the trusted live checkout, not from a detached snapshot.
2. Confirm the restored repo is on `main` and points to `https://github.com/fawxzzy/fawxzzy-fitness.git`.
3. Confirm the restored repo keeps the same Vercel project linkage:
   - `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
   - project `fawxzzy-fitness`
4. Confirm the restored repo keeps the production-aligned Supabase target guards:
   - project ref `lpswxoyfniocuhljgzbc`
   - expected host `lpswxoyfniocuhljgzbc.supabase.co`
5. Update any active operator notes or receipts that still imply the `tmp` path is an acceptable long-term production lane.
6. Re-run Fitness verify and deploy from the restored canonical repo path through `_stack` governance.
7. Only after the restored repo is proven good should the live `tmp` production checkout stop being a production dependency.

## Immediate Follow-Up Inventory Questions

- Is `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` clean enough to promote directly into `repos/fawxzzy-fitness`, or does it require a preservation checkpoint first?
- Which additional `tmp/fitness*` directories are active work surfaces versus retained evidence only?
- Which receipts, QA scripts, or deploy notes now need explicit canonical-path updates after restoration?
- Does any current operator lane still pull secrets or env material into `tmp` paths because the canonical repo root is missing?

## Non-Goals Of This Inventory

- moving the live Fitness repo
- deleting any `tmp/fitness*` surfaces
- deleting duplicate roots
- changing Vercel linkage
- changing Supabase linkage
- running deploy or verify from a new path yet

This inventory only establishes the current truth map for the restoration lane.
