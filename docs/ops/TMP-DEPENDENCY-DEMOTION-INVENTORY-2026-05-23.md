# Tmp Dependency Demotion Inventory

Date: 2026-05-23
Lane: Tmp Dependency Elimination
Status: inventory

## Goal

Identify the remaining `tmp` surfaces tied to Fitness and recent normalization work, classify their current role, and distinguish retained reference/evidence from any still-active production-critical dependency.

## Executive Verdict

The dangerous `tmp` dependency has been reduced substantially.

Current state:

- `_stack` package scripts and runbooks resolve Fitness through `repos/fawxzzy-fitness`
- `_stack` Fitness deploy preflight passes against the canonical repo root
- canonical Fitness verification passes from `repos/fawxzzy-fitness`
- the remaining highlighted `tmp` surfaces are no longer required for the proven Fitness verify/preflight path

Remaining `tmp` work is now demotion and governance, not recovery.

## Focus Surface Classification

| Surface | Current state | Current role | Classification | Production-critical dependency? | Recommended next action |
| --- | --- | --- | --- | --- | --- |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | present, git repo, `main`, clean, same HEAD as canonical repo | previously live production-linked fallback checkout with local Vercel link and documented Supabase identity | retained reference / fallback surface | no, not for the proven canonical verify + `_stack` preflight path | retain temporarily, then demote explicitly in final closeout docs |
| `tmp/fitness-main-post-merge` | present, detached snapshot at `710c7f20`, linked to same GitHub remote/Vercel metadata family | historical snapshot used during restoration comparison | historical evidence | no | retain as recovery evidence until duplicate-surface review decides archive vs removal |
| `tmp/atlas-qa-release-refresh-pr` | present on disk, not a git root, no longer an active worktree, branch already gone | filesystem residue after Windows denied deletion during worktree cleanup | stale filesystem residue | no | manual review / safe delete later once Windows lock cause is cleared |

## `_stack` And Root Path Proof

### Active canonical references

Confirmed active stack/operator references point to `repos/fawxzzy-fitness`:

- `stack.yaml`
- `README-STACK.md`
- `repos/_stack/package.json`
- `repos/_stack/docs/fitness-verify.md`
- `repos/_stack/docs/runbooks/FITNESS-QA-LOCAL-LOOP.md`
- `repos/_stack/docs/dispatcher-protocol.md`
- `repos/_stack/queue/README.md`
- `repos/_stack/templates/child-task-handoff.md`

### Active tmp references

No active `_stack` package script or current operator proof in this pass required:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
- `tmp/fitness-main-post-merge`

The remaining references to those surfaces are documentary:

- canonical restoration inventory/receipt/readiness/path-proof docs
- historical recovery and normalization receipts

That means `tmp` is still named, but not still driving the active operator path.

## Surface Notes

### `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`

Observed facts:

- git repo on `main`
- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`
- local `.vercel/project.json` present
- canonical repo now matches it exactly on branch and HEAD

Interpretation:

- this surface is no longer the only viable local linked checkout
- its remaining value is fallback/reference and restoration evidence
- it should not be deleted blindly because it still carries linked local operator history and recovery receipts may depend on it as evidence

Recommended demotion:

- demote from active fallback to retained reference
- keep until Duplicate Surface Decommission explicitly decides archive vs removal timing

### `tmp/fitness-main-post-merge`

Observed facts:

- detached snapshot at `710c7f20fbe9eeb631690754747e9c82d0202323`
- same GitHub remote family as canonical Fitness
- not required by `_stack` path proof or canonical repo verification

Interpretation:

- this is a historical comparison surface, not a live source-of-truth surface
- it should remain documented as a snapshot and reviewed later in duplicate-surface cleanup

Recommended demotion:

- classify as historical evidence
- later archive or remove only after Duplicate Surface Decommission decides it is no longer needed

### `tmp/atlas-qa-release-refresh-pr`

Observed facts:

- directory still exists on disk
- not listed in current `git worktree list`
- not a git root
- branch was already removed in prior disposal passes
- prior receipts already classify it as Windows deletion residue

Interpretation:

- this is not a repo truth problem
- this is not an active worktree blocker anymore
- this is later filesystem cleanup residue

Recommended demotion:

- classify as stale filesystem residue
- safe delete later after a manual/Windows-aware cleanup pass

## Broader Tmp Risk Note

The broader `tmp` tree still contains many historical Fitness-related folders.

Examples already documented in earlier normalization work include:

- `tmp/fitness-discord-update-bot-clean`
- `tmp/history-ui-archaeology/fawxzzy-fitness`
- `tmp/fitness-discord-main-rollout`

This inventory does not attempt to classify every historical Fitness `tmp` surface. It only resolves the immediate canonical-repo and active-operator question. A fuller duplicate-surface or tmp-surface closeout pass is still needed later.

## Demotion Decision Matrix

| Category | Meaning in this lane | Current examples |
| --- | --- | --- |
| retained reference | still useful as fallback/comparison/evidence, but not active canonical execution | `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` |
| historical evidence | snapshot/recovery surface kept for documentation or archaeology | `tmp/fitness-main-post-merge` |
| stale source path | path that used to matter operationally but should no longer be used | `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` after formal demotion |
| production-critical dependency | required by active source, verify, deploy, or operator proofs | none proven in this pass |
| safe delete candidate | removable later without losing active truth or required evidence | `tmp/atlas-qa-release-refresh-pr` directory only, after manual filesystem cleanup |
| manual review | needs a separate retention or Windows cleanup decision | `tmp/atlas-qa-release-refresh-pr` |

## Current Tmp Dependency Verdict

What `tmp` is no longer needed for:

- canonical Fitness source location
- canonical Fitness local verification
- canonical Fitness local Vercel link presence
- `_stack` Fitness deploy preflight

What `tmp` is still doing:

- holding retained fallback/reference value
- preserving restoration evidence
- preserving one known Windows cleanup residue path

## Remaining Work Before Tmp Dependency Elimination Reaches 100%

1. formally demote `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` from active fallback to retained reference only
2. decide archive vs removal timing for `tmp/fitness-main-post-merge`
3. clear the `tmp/atlas-qa-release-refresh-pr` filesystem residue in a separate manual-safe cleanup pass
4. extend duplicate-surface review across the broader Fitness-related `tmp` tree
5. confirm no manual deploy or undocumented operator lane still bypasses `_stack` and re-enters a `tmp` repo surface

## Closeout Verdict

The remaining `tmp` problem is no longer “Fitness still runs from tmp.”

The remaining `tmp` problem is:

- retained fallback/reference surfaces still need formal demotion
- historical snapshots still need archive/removal decisions
- one Windows cleanup residue path still needs manual cleanup
