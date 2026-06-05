# Duplicate Surface Retention Governance

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Docs-only governance
Status: Initial retained-surface governance complete

## Purpose

This receipt converts the remaining retained duplicate or non-canonical surfaces into explicit governance states. The goal is to remove ambiguity without deleting, moving, or normalizing any retained surface in this pass.

## Governance rules

1. A retained duplicate surface must have an explicit owner and reason to exist.
2. A retained duplicate surface must name what it must never be used for.
3. A retained duplicate surface must name the prerequisite for later deletion, archival, or deeper routing.
4. Canonical repo truth remains under `repos/` unless a dedicated trust-gate or archive policy says otherwise.

## Retained surface governance table

| Surface | Current status | Owner | Why retained | Must never be used for | Deletion or archive prerequisite | Blocks Full Stack Re-sync, Clean & Closeout | Blocks Tmp Dependency Elimination | Blocks Duplicate Surface Decommission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<ATLAS_STANDALONE>/fitness-release-main` | Exists, standalone git root, local `main`, dirty in `src/generated/appBuildManifest.json` | Fitness / ATLAS recovery governance | Standalone snapshot or release-evidence surface outside canonical `repos/fawxzzy-fitness`; not yet proven safe to discard | Must never be treated as canonical Fitness source, deploy root, or active operator workspace | Verify whether its single snapshot commit carries retained evidence value beyond canonical Fitness and retained `tmp` evidence; if not, reclassify to stale duplicate and later-delete candidate | yes | yes | yes |
| `repos/fawxzzy-trove-release-cutover` | Exists, clean git root, branch `codex/trove-preview-deploy-pipeline` tracking origin | Trove | Temporary non-canonical cutover lane already documented as retained evidence | Must never be treated as canonical Trove repo root or the default deploy workspace | Confirm cutover evidence is either still referenced by Trove recovery/deploy docs or archive it deeper and mark delete-later | yes | no | yes |
| `repos/fawxzzy-lifeline-operator-evidence` | Exists, clean git root, branch `codex/lifeline-operator-evidence` tracking origin | Lifeline | Temporary non-canonical operator evidence lane already documented as retained evidence | Must never be treated as canonical Lifeline source or default operator workspace | Confirm evidence still supports active Lifeline recovery/operator flows; if not, archive deeper or fold into governed retained-evidence structure | no | no | yes |
| `repos/Verta-Core` | Exists as quarantined non-canonical directory; not a current git root from this root session | Verta trust-gate governance | Raw quarantined Verta surface already documented as untrusted and non-release | Must never be treated as canonical ATLAS source, release repo, or ordinary cleanup target | Dedicated Verta trust-gate review only | yes | no | yes |
| `repos/Verta-Core.zip` | Exists as quarantined archive artifact | Verta trust-gate governance | Raw compressed Verta import artifact retained as quarantined historical archive | Must never be treated as source repo, unpack target by default, or canonical release artifact | Dedicated Verta trust-gate review only | yes | no | yes |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | Exists, clean git root on `main...origin/main` | Fitness recovery governance | Former production-linked fallback checkout; now retained reference only after canonical repo restoration | Must never be treated as active Fitness source truth, default verify root, or required `_stack` path | Explicit archive-or-delete schedule after downstream receipts confirm no active operator workflow references it | no | yes | yes |
| `tmp/fitness-main-post-merge` | Exists, detached historical git surface, origin remote present, current object/read state not healthy enough for active use | Fitness recovery governance | Historical evidence only | Must never be treated as active source, deploy root, or verification workspace | Archive-or-delete schedule after confirming no current workflow references it for active source truth | no | no | yes |
| `tmp/atlas-qa-release-refresh-pr` | Exists as non-git filesystem residue only | ATLAS cleanup governance | Stale Windows residue from removed worktree | Must never be treated as active worktree, canonical root, or retained source truth | Manual filesystem cleanup pass only | no | no | yes |
| `archive/fitness-source-reset` | Exists as intentional preserved archive mass under `archive/` | Archive normalization / ATLAS preservation governance | Retained preservation material with existing archive retention receipt | Must never be treated as canonical repo root, live source truth, or ad hoc scratch storage | Final archive retention/deletion schedule after broader clean/resync closeout | yes | no | yes |

## Surface-specific notes

### `fitness-release-main`

- Highest-risk retained duplicate still left in the lane.
- Its combination of no configured remote, one snapshot commit, generated state, and large app-shaped layout means it is more likely evidence or stale duplicate than active source truth.
- It remains retained only because deletion safety is not yet fully documented.

### `fawxzzy-trove-release-cutover` and `fawxzzy-lifeline-operator-evidence`

- These are retained-for-now evidence lanes, not active repo confusion bugs.
- Their remaining work is evidence governance, not source-truth restoration.

### `Verta-Core` and `Verta-Core.zip`

- These remain outside ordinary duplicate cleanup.
- Their unresolved state is quarantine by policy, not accidental drift.

### `tmp` Fitness surfaces

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` is now a reference-only retention surface after canonical repo restoration, Vercel link restoration, and `_stack` proof from `repos/fawxzzy-fitness`.
- `tmp/fitness-main-post-merge` remains historical evidence only.
- `tmp/atlas-qa-release-refresh-pr` is residue only and should be handled by later filesystem cleanup, not governance confusion.

### `archive/`

- `archive/fitness-source-reset` already has an archive retention receipt.
- It still blocks full clean closeout because retained preservation material has not reached final archive lifecycle resolution yet.

## What none of these surfaces may do now

No surface in this receipt may now serve as:

- canonical repo truth for Fitness, Trove, Lifeline, or ATLAS
- implicit deploy root
- implicit verification root
- justification for bypassing `_stack` or canonical repo paths
- ad hoc scratch space without a retention class

## Governance conclusion

The remaining duplicate surfaces are no longer ambiguous. They now fall into four explicit buckets:

1. retained evidence:
   - `repos/fawxzzy-trove-release-cutover`
   - `repos/fawxzzy-lifeline-operator-evidence`
   - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
   - `tmp/fitness-main-post-merge`

2. retained snapshot pending safe-delete proof:
   - `<ATLAS_STANDALONE>/fitness-release-main`

3. quarantined trust-gate surfaces:
   - `repos/Verta-Core`
   - `repos/Verta-Core.zip`

4. residue or archive governance surfaces:
   - `tmp/atlas-qa-release-refresh-pr`
   - `archive/fitness-source-reset`

## Recommended next lane

Do not mix the next steps.

1. Keep duplicate-surface governance on retained surfaces only until `fitness-release-main` gets its final evidence vs stale-duplicate ruling.
2. Start a separate branding-lane packaging pass for the current `branding/**` residue under:
   - `Brand Asset Canonicalization`
   - `Preview Cache & Surface Consistency`
