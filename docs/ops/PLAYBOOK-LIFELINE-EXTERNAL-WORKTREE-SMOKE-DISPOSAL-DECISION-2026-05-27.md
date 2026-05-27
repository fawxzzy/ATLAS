# Playbook / Lifeline External Worktree / Smoke Surface Disposal Decision - 2026-05-27

- Date: `2026-05-27`
- Lane: `Playbook / Lifeline External Worktree / Smoke Surface Disposal Decision Pass`
- Mode: `decision-only`
- Control-plane checkpoint: `main@a80eb50`

## Objective

Decide the safe disposition of the remaining external Playbook smoke/prunable surfaces and retained Lifeline external worktree/checkpoint surfaces after the earlier 2026-05-26 disposal chain.

This pass does not:

- delete worktrees
- remove branches
- drop stashes
- delete files or directories
- mutate owner-repo tracked content
- mutate Supabase, Vercel, Discord, runtime, schema, or data surfaces

## Root State

- branch: `main`
- HEAD: `a80eb50c0302d0527876b2c4a05d6dd6fb71db93`
- status: clean except intentional untracked `archive/`

## Inputs

- `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-CONSOLIDATION-2026-05-27.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-WORKTREE-RESIDUE-PLAN-2026-05-25.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-RESIDUE-DISPOSAL-2026-05-25.md`
- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-SMOKE-DISPOSAL-DECISION-2026-05-26.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-SURFACE-DISPOSAL-EXECUTION-PASS-2-2026-05-26.md`
- `docs/ops/PLAYBOOK-PRESERVED-PROOF-TEST-BRANCH-DISPOSAL-EXECUTION-2026-05-26.md`
- `docs/ops/PLAYBOOK-SMOKE-HOME-STRANDED-CHECKOUT-DISPOSAL-EXECUTION-2026-05-26.md`
- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-CLOSEOUT-PASS-2-2026-05-25.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `stack.yaml`
- `stack.lock.yaml`

## Current Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## Current Surface Inventory

## Playbook external smoke / prunable surfaces

### Already consumed by the 2026-05-26 chain

These are no longer live remaining questions:

- `smoke-home` stranded checkout: already disposed
- the four preserved proof/test branch refs:
  - `codex/codex-inbox-proof-docs-touch-2`
  - `codex/mock-stdin-smoke-nine`
  - `codex/mock-watcher-smoke-five`
  - `codex/mock-watcher-smoke-six`
  - branch refs and stale `.git/worktrees/*` admin entries already removed
- the 14 behind-only broken `.git/worktrees/*` admin entries already removed

What remains from that family is different:

- stranded filesystem directories under `repos/fawxzzy-playbook/.codex/worktrees/*`
- some matching local branches still exist for the behind-only family
- no current Playbook `.git/worktrees/*` admin entry remains for those external-smoke names

### Remaining stranded Playbook `.codex/worktrees/*` directories

Observed current state:

- `repos/fawxzzy-playbook/.codex/worktrees/` still contains 18 top-level directories
- each directory has a `.git` file
- each `.git` file points to a missing historical user-home Playbook gitdir target under the old external checkout's `.git/worktrees/<name>` location
- none of those names appear as live entries under:
  - `repos/fawxzzy-playbook/.git/worktrees/`

Current remaining directory set:

- `codex-inbox-proof-docs-touch`
- `codex-inbox-proof-docs-touch-2`
- `codex-inbox-smoke-four`
- `codex-inbox-smoke-one`
- `codex-inbox-smoke-one-2`
- `codex-inbox-smoke-three`
- `codex-inbox-smoke-two`
- `codex-inbox-smoke-two-2`
- `mock-stdin-smoke-eight`
- `mock-stdin-smoke-nine`
- `mock-stdin-smoke-seven`
- `mock-watcher-smoke-five`
- `mock-watcher-smoke-four`
- `mock-watcher-smoke-one`
- `mock-watcher-smoke-six`
- `mock-watcher-smoke-three`
- `mock-watcher-smoke-two`
- `tmp-check`

### Related Playbook local branch state

Still present locally:

- `codex/codex-inbox-proof-docs-touch`
- `codex/codex-inbox-smoke-four`
- `codex/codex-inbox-smoke-one`
- `codex/codex-inbox-smoke-one-2`
- `codex/codex-inbox-smoke-three`
- `codex/codex-inbox-smoke-two`
- `codex/codex-inbox-smoke-two-2`
- `codex/mock-stdin-smoke-eight`
- `codex/mock-stdin-smoke-seven`
- `codex/mock-watcher-smoke-four`
- `codex/mock-watcher-smoke-one`
- `codex/mock-watcher-smoke-three`
- `codex/mock-watcher-smoke-two`
- `codex/tmp-check`

Already absent locally:

- `codex/codex-inbox-proof-docs-touch-2`
- `codex/mock-stdin-smoke-nine`
- `codex/mock-watcher-smoke-five`
- `codex/mock-watcher-smoke-six`

Interpretation:

- the four preserved proof/test branches were already fully consumed as branch surfaces
- the remaining fourteen behind-only branch refs still exist, but they are no longer attached to a live worktree/admin entry
- branch deletion is a separate question from filesystem cleanup of the stranded directories

### Playbook stashes

Still present:

- `stash@{0}` `On main: codex-temp-playbook-agents-noise`
- `stash@{1}` `On main: codex-temp-local-hygiene-playbook-docs`
- `stash@{2}` `On main: qa residue before syncing main after PR 8`

Interpretation:

- still manual-review retained safety surfaces
- not part of any safe execution subset in this pass

## Lifeline retained worktrees / checkpoints

Current retained Lifeline family:

- `repos/fawxzzy-lifeline`
- `repos/fawxzzy-lifeline-operator-evidence`
- `tmp/fawxzzy-lifeline-rollback-rehearsal-evidence`
- `tmp/lifeline-closeout-checkpoint`
- `tmp/lifeline-main-closeout`
- `tmp/lifeline-main-closeout-2`
- `tmp/lifeline-main-closeout-24`
- `tmp/lifeline-main-closeout-3`
- `tmp/lifeline-pr24-refresh`
- `tmp/lifeline-release-cli-guardrails-worktree`
- `tmp/lifeline-release-replay-verification-clean`
- `tmp/lifeline-wave2-scout`
- `tmp/lifeline-wave3-scout`

No current Lifeline stash was found.

## Disposition Table

| Surface / class | Current truth | Classification | Dependency keeping it alive | Verification required before disposal |
| --- | --- | --- | --- | --- |
| Playbook `.codex/worktrees/*` stranded directories with no matching local branch: `codex-inbox-proof-docs-touch-2`, `mock-stdin-smoke-nine`, `mock-watcher-smoke-five`, `mock-watcher-smoke-six` | broken filesystem-only directories; matching branches already deleted; no current `.git/worktrees/*` admin entry remains | safe-delete candidate | historical receipts only; no current book/restart surface depends on them | confirm `.git/worktrees/<name>` admin entry is absent, branch ref is absent, and no current receipt requires live on-disk preservation beyond the already-created patch artifacts |
| Playbook `.codex/worktrees/*` stranded directories whose matching behind-only local branch still exists: `codex-inbox-proof-docs-touch`, `codex-inbox-smoke-four`, `codex-inbox-smoke-one`, `codex-inbox-smoke-one-2`, `codex-inbox-smoke-three`, `codex-inbox-smoke-two`, `codex-inbox-smoke-two-2`, `mock-stdin-smoke-eight`, `mock-stdin-smoke-seven`, `mock-watcher-smoke-four`, `mock-watcher-smoke-one`, `mock-watcher-smoke-three`, `mock-watcher-smoke-two`, `tmp-check` | broken filesystem-only directories; no live worktree/admin entry remains; matching branch ref still exists locally | safe-delete candidate | only the local behind-only branch refs remain; no current worktree/admin metadata or current book surface depends on the directories | confirm `.git/worktrees/<name>` admin entry is absent and keep branch refs out of scope; do not delete the branch in the same pass |
| Playbook behind-only local smoke branch refs matching the 14 names above | local refs still exist; behind-only; not attached to live worktree/admin entries | retain pending manual review | local git branch metadata only | verify whether a later branch-only disposal lane wants to prune behind-only refs after confirming no receipt or operator workflow still names them |
| Playbook stashes | still present exactly as retained in prior receipts | retain pending manual review | explicit residue-plan rule and no later stash-disposition receipt | inspect stash contents in a dedicated repo-local stash lane before any drop |
| Lifeline active repo root | current active owner-repo lane | blocked by unknown dependency | active owner-repo work | out of scope for ATLAS-root disposal; use repo-local verification and owner-lane review only |
| Lifeline operator-evidence worktree | intact evidence-bearing worktree | stale but evidence-bearing | prior receipts still frame it as evidence surface | verify no current receipt, release proof, or rollback posture still expects the evidence path before disposal |
| Lifeline rollback rehearsal evidence | retained evidence worktree | stale but evidence-bearing | rollback-evidence posture from prior receipts | verify rollback evidence is fully receipted and no later rollback-confidence lane depends on the live path |
| Lifeline closeout checkpoints: `lifeline-closeout-checkpoint`, `lifeline-main-closeout-24`, `lifeline-release-replay-verification-clean`, `lifeline-wave2-scout`, `lifeline-wave3-scout` | intact checkpoint/safety worktrees with upstream lineage | retain as safety checkpoint | earlier residue plan explicitly classifies them as local-only or safety checkpoints | verify a later receipt supersedes the safety evidence and that repo-local verification passes before removal |
| Lifeline stale merge checkpoints: `lifeline-main-closeout`, `lifeline-main-closeout-2`, `lifeline-main-closeout-3` | named merged checkpoint branches with no current upstream tracking line | stale but evidence-bearing | only manual-review receipts keep them alive now | compare each checkpoint commit against merged PR/release state and confirm no unique evidence remains before disposal |
| Lifeline retained branch worktrees: `lifeline-pr24-refresh`, `lifeline-release-cli-guardrails-worktree` | intact retained branch worktrees with upstream lineage | retain pending manual review | earlier residue plan still treats them as retained branch surfaces | verify branch is merged, superseded, or still needed for review before disposal |

## Unknown-Dependency Check

No remaining surface in this pass is blocked by a newly unknown dependency.

What remains is explicit:

- safe-delete filesystem residue in the Playbook external `.codex/worktrees/*` family
- retained/manual-review/safety Lifeline surfaces
- retained Playbook branch refs and stashes

## Safe Execution Subset

One narrow safe execution subset now exists.

Allowed next execution class:

- remove the 18 stranded directories under `repos/fawxzzy-playbook/.codex/worktrees/*`

Boundary:

- filesystem removal only
- no branch deletion
- no stash drop
- no Lifeline worktree removal
- no Playbook `.git/worktrees/*` admin mutation beyond confirming those entries are already absent

Why this subset is safe:

- the directories are no longer live worktrees
- every `.git` file points at a missing historical user-home gitdir target
- the four proof/test branch surfaces are already preserved and branch-disposed
- the fourteen behind-only names still have branch refs, but those refs do not require keeping the broken directories on disk

## No-Delete Subset

Do not delete in the next execution pass:

- any Lifeline retained worktree/checkpoint
- any Playbook stash
- any Playbook behind-only local branch ref
- `repos/fawxzzy-playbook`
- `repos/fawxzzy-lifeline`
- `archive/`

## Marker Recommendation

No marker movement is justified by this pass.

Reason:

- this is a decision packet only
- ambiguity is reduced, but no retained surface has been removed yet

Recommended unchanged markers:

- `Branch & Worktree Normalization`: `99%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Inventory & Truth Map`: `74%`
- `Discord OS Infrastructure Separation`: `95%`

## Next Package Recommendation

`Playbook external Codex worktree stranded-directory disposal execution pass`

Scope for that package:

- remove only the 18 stranded directories under `repos/fawxzzy-playbook/.codex/worktrees/*`
- leave branches, stashes, Lifeline surfaces, and active repo roots untouched

## Outcome

The remaining Playbook/Lifeline pressure is no longer one mixed retained-surface family.

Current truth:

- Playbook has a narrow filesystem-only external-smoke residue subset that can now be consumed safely
- Lifeline still does not have a safe delete-now subset in this lane
- branch, stash, and safety-checkpoint questions remain explicitly bounded for later owner-safe review
