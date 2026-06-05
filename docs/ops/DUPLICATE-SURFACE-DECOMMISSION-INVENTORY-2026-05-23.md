# Duplicate Surface Decommission Inventory

Date: 2026-05-23
Lane: Duplicate Surface Decommission
Mode: Inventory only
Status: Initial classification complete

## Purpose

This inventory classifies duplicate, orphaned, stale, or non-canonical source surfaces across and adjacent to ATLAS without deleting, moving, or re-linking anything.

The main governance goal is to ensure every source-like surface outside the intended canonical `repos/` layout or documented retained evidence/archive surfaces has an explicit reason to exist.

## Current framing

- Canonical Fitness source truth now lives at `repos/fawxzzy-fitness`.
- Canonical Fitness verify and `_stack` preflight no longer require `tmp/`.
- `tmp/` still contains retained reference and historical evidence surfaces that need demotion/retention governance, not blind deletion.
- `archive/` remains intentional retained preservation material and is out of scope for decommission in this pass.
- Branding lane edits under `branding/**` are separate and out of scope for this pass.

## Classification legend

- `canonical owner`: governed primary owner surface
- `retained evidence`: intentionally preserved recovery or operator evidence
- `historical archive`: intentionally retained historical snapshot or archive artifact
- `stale duplicate`: duplicate or non-canonical source surface that should not remain ambiguous
- `tmp residue`: temporary or orphaned residue outside the active canonical path
- `manual review`: not safe to decommission without a focused follow-up decision
- `safe delete later`: appears removable later, but not in this inventory pass
- `do-not-delete`: explicitly retained for governance, rollback, or archive reasons

## Primary surface inventory

| Surface | Exists | Git root | Branch / HEAD | Remote | Dirty | Approx size | Purpose / owner | Current classification | Risk | Recommended disposition | Blocks Tmp Dependency Elimination | Blocks Full Stack Re-sync, Clean & Closeout |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `repos/fawxzzy-lifeline-operator-evidence` | yes | yes | `codex/lifeline-operator-evidence` / `bdb50fc` | `fawxzzy-lifeline.git` | clean | 58.2 MB | Lifeline evidence lane already documented as temporary non-canonical evidence surface | retained evidence | Medium: source-like surface outside primary canonical repo path for the Lifeline family | Keep until a dedicated Lifeline evidence decommission or migration pass classifies whether it should be archived or folded into a canonical repo/evidence structure | no | no |
| `repos/fawxzzy-trove-release-cutover` | yes | yes | `codex/trove-preview-deploy-pipeline` / `eff0182` | `fawxzzy-trove.git` | clean | 451.8 MB | Trove release cutover lane already documented as temporary non-canonical cutover surface | retained evidence | Medium: large non-canonical Trove surface could drift if left ambiguous | Keep for now; review under Trove-specific duplicate-surface or cutover-governance lane before deletion | no | yes, until its cutover role is explicitly closed |
| `repos/Verta-Core` | yes | no detectable git root in current directory | n/a | n/a | n/a | 247.4 MB | Quarantined raw Verta surface documented as untrusted/non-release | do-not-delete | High if mistaken for canonical ATLAS or promoted into active source truth | Keep quarantined; only touch in a dedicated Verta lane with explicit trust-gate handling | no | yes, because ambiguous raw Verta surfaces remain outside canonical governance |
| `repos/Verta-Core.zip` | yes | no | n/a | n/a | n/a | 97.8 MB | Raw compressed Verta import/archive artifact | historical archive | Medium if treated as active source instead of retained archive material | Keep as historical archive until duplicate-surface policy decides whether it stays as retained import evidence | no | yes, for the same Verta governance reason |
| `<ATLAS_WORKTREES>` | yes | no container root | n/a | n/a | n/a | 4.6 MB | External worktree container for ATLAS | manual review | Medium: outer container is not itself canonical source, but it still hosts live and stale worktree surfaces | Keep container until each contained surface is individually classified and resolved | indirect | yes |
| `<ATLAS_WORKTREES>/pr1-stack-lock-refresh` | yes | yes | `codex/pr1-stack-lock-refresh` / `50b8b45` | `ATLAS.git` | clean | 3.9 MB | Active/stale external ATLAS worktree surface | stale duplicate | Medium: extra ATLAS worktree outside root keeps duplicate source lineage alive | Review against current branch/worktree closeout state; likely removable later if no unique work remains | indirect | yes |
| `<ATLAS_WORKTREES>/remove-stale-cortex-contract-v2` | yes | no detectable git root | n/a | n/a | n/a | 0.7 MB | Residual external worktree directory no longer registered as active worktree | tmp residue | Low to Medium: filesystem residue can confuse later audits | Confirm contents and later delete as residue if no retained evidence value exists | no | no, unless left undocumented |
| `<ATLAS_STANDALONE>` | yes | no container root | n/a | n/a | n/a | 1.10 GB | External standalone container outside governed stack root | manual review | High: large outside-root source container can become hidden operator path or duplicate truth | Keep for now; classify its child surfaces before any deletion or retention call | yes | yes |
| `<ATLAS_STANDALONE>/fitness-release-main` | yes | yes | `main` / `c557282` | none visible | dirty (`1`) | 1.10 GB | Standalone Fitness checkout outside canonical `repos/fawxzzy-fitness` | stale duplicate | High: repo-like Fitness surface outside canonical path can recreate wrong-repo confusion | Manual review first; determine whether it is historical release evidence, stale duplicate, or requires archival before later deletion | yes | yes |
| `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` | yes | yes | `main` / `7ceebde9` | `fawxzzy-fitness.git` | clean | 1.39 GB | Former production-linked Fitness fallback checkout | retained evidence | Medium: no longer production-critical, but still a large duplicate of canonical Fitness | Keep as retained reference only until later tmp decommission pass explicitly archives or removes it | yes, until formally demoted/retained | yes |
| `tmp/fitness-main-post-merge` | yes | yes | detached / `710c7f20` | `fawxzzy-fitness.git` | clean | 731.4 MB | Historical Fitness post-merge snapshot | historical archive | Low to Medium: not active, but still a source-like historical surface | Keep as historical evidence until a later archival/delete schedule is approved | no | no |
| `tmp/atlas-qa-release-refresh-pr` | yes | no detectable git root | n/a | n/a | n/a | 1.2 MB | Windows-deletion residue from removed ATLAS worktree | tmp residue | Low: no longer active worktree or branch blocker, but still confusing residue | Leave documented for now; later manual filesystem cleanup only | no | no |

## Supplementary non-canonical repo-like surfaces already visible under `repos/`

These were not the primary target set, but they are source-like surfaces worth flagging now so later decommission work does not miss them.

| Surface | Exists | Git root | Branch / HEAD | Remote | Dirty | Approx size | Initial note | Initial classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `repos/fawxzzy-playbook-codex` | yes | yes | `codex/pattern-discord-verification-gates` / `2e32bd00` | `fawxzzy-playbook.git` | clean | 93.8 MB | Already documented as adjacent non-canonical helper surface outside governed stack member set | manual review |
| `repos/repo-backups` | yes | no | n/a | n/a | n/a | 5.9 MB | Package-layer backup infrastructure, not an app repo | do-not-delete |
| `repos/fawxzzy-fitness-discord-bot` | yes | no detectable git root | n/a | n/a | n/a | 0 MB | Empty or placeholder surface that should not remain ambiguous | stale duplicate |
| `repos/fawxzzy-trove` | yes | yes | `codex/trove-brand-asset-sync` / `bce14fc` | `fawxzzy-trove.git` | dirty (`13`) | 624.0 MB | Canonical Trove repo family surface, but currently carrying branding lane edits | canonical owner |
| `repos/playbook-demo` | yes | no detectable git root | n/a | n/a | n/a | 0.3 MB | Small demo/example surface | manual review |
| `repos/ZachariahRedfield` | yes | yes | `main` / `bad2002` | `ZachariahRedfield/ZachariahRedfield.git` | clean | 22.1 MB | Adjacent personal/repo surface outside current stack convergence focus | manual review |

## Key findings

1. The Fitness canonical-source problem is no longer a duplicate-truth emergency.
   `repos/fawxzzy-fitness` is canonical, verified, Vercel-linked locally, and `_stack`-proven. The remaining Fitness-related `tmp` surfaces are governance-retention surfaces, not active source-of-truth blockers.

2. The largest remaining duplicate-surface risk is outside canonical `repos/` governance.
   `<ATLAS_STANDALONE>/fitness-release-main`, `<ATLAS_WORKTREES>/pr1-stack-lock-refresh`, and the Verta surfaces remain outside the intended canonical layout and need explicit later decisions.

3. `Verta-Core` and `Verta-Core.zip` must stay in a dedicated Verta governance bucket.
   They are already documented as quarantined/untrusted and must not be silently normalized into ordinary repo cleanup.

4. Not every outside-root surface is deletable just because it is non-canonical.
   Several surfaces are already retained evidence, historical archive, or temporary operator/cutover lanes that need explicit retention or archival policy first.

## Added Stale Vercel Cleanup Targets

This lane now explicitly includes stale Vercel project/deployment surfaces when they create duplicate or confusing public/deploy surfaces outside the canonical product path.

Inventory targets to classify in a dedicated follow-up pass:

- `spotify-club-phase-7-interaction-reliability`
- `spotify-club-phase-7-interaction-re.vercel.app`
- `spotify-board-hygiene-main`
- `spotify-board-hygiene-main.vercel.app`

These targets overlap with `Manual Deploy Exception Burn-Down` because they are both:

- duplicate public/deploy surfaces
- potential deploy-authority confusion

No deletion or Vercel mutation occurs from this inventory update alone.

## Initial decommission priority

### Highest priority follow-up

- `<ATLAS_STANDALONE>/fitness-release-main`
- `<ATLAS_WORKTREES>/pr1-stack-lock-refresh`
- `repos/fawxzzy-trove-release-cutover`
- `repos/fawxzzy-lifeline-operator-evidence`

These are the most likely to prolong duplicate-source ambiguity if left without a next-step decision.

### Lower-risk residue

- `tmp/atlas-qa-release-refresh-pr`
- `<ATLAS_WORKTREES>/remove-stale-cortex-contract-v2`
- `repos/fawxzzy-fitness-discord-bot`

These look more like residue or placeholder surfaces than active governance blockers, but they still should not remain undocumented.

## Recommended next package

Run a focused `Duplicate Surface Decommission Decision Pass` that does not delete anything yet, but assigns one of the following explicit outcomes to each high-priority surface:

- keep as retained evidence
- archive as historical surface
- route into canonical repo governance
- mark safe delete later
- hold for manual review with blocking reason

That decision pass should update this inventory rather than starting from scratch.
