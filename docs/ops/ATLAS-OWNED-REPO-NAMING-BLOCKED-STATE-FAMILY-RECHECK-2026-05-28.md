# Atlas-Owned Repo Naming Blocked-State Family Recheck - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only family-wide blocked-state recheck`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 75%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-SECOND-CANDIDATE-MASS-RECHECK-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-NEXT-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Re-evaluate the remaining naming family together in one batch, classify each repo by current execution posture, and decide whether one exact safe-third candidate exists.

This pass does not:

- rename any repo directory
- rename any remote
- assume any GitHub-side rename
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status before drafting: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, naming receipts, `PROCESS-AMPLIFICATION-PASS-2-2026-05-28.md`, and intentional untracked `archive/`
- validation before drafting: `critical=0 error=0 warning=311`

## Remaining Family Recomputed Together

Remaining admitted prefixed naming family after the executed-and-reconciled `stream` and `foundation` packets:

- `repos/fawxzzy-trove -> repos/trove`
- `repos/fawxzzy-mazer -> repos/mazer`
- `repos/fawxzzy-lifeline -> repos/lifeline`
- `repos/fawxzzy-playbook -> repos/playbook`

Explicit preserved exception:

- `repos/fawxzzy-fitness`

Rule:

- third-candidate selection must be family-batched, not rediscovered repo by repo

## Batch Scan Method

This pass scanned the full remaining family together using:

- current stack registry truth
- current stack-lock truth
- current repo inventory publication
- current restart-guide posture
- repo-local branch and dirty posture
- registered worktree and retained-surface posture

## Family-Wide Read

The remaining family no longer has a clean later candidate comparable to `stream` or `foundation`.

What remains is not path-mapping uncertainty.

What remains is a family-wide mix of:

- branch / non-`main` posture
- active local owner-lane state
- retained-surface or worktree-review pressure

That means the honest question is no longer which repo should be rediscovered next.

The honest question is whether any repo has actually changed class into execution-readiness.

## Candidate Classification

| Candidate | Classification | Why |
| --- | --- | --- |
| `trove` | `blocked by branch / non-main posture` | pinned and current branch are both `codex/trove-brand-asset-sync`, not `main` |
| `trove` | `blocked by retained-surface / manual-review posture` | registered worktrees still include deploy/release isolation lanes and prunable retained registrations |
| `mazer` | `blocked by branch / non-main posture` | pinned and current branch are both `codex/mazer-remove-pwa-install-surface`, not `main` |
| `mazer` | `blocked by retained-surface / manual-review posture` | current worktree family includes multiple extra branch worktrees and a prunable retained registration |
| `mazer` | `blocked by local active state` | published inventory still carries `initiative:initiative-mazer-d2-learning-scorer` as an active related initiative |
| `lifeline` | `blocked by local active state` | dirty repo plus dense active operator-worktree family make this a live owner lane, not a bounded naming packet |
| `lifeline` | `blocked by branch / non-main posture` | pinned and current branch are both `codex/lifeline-release-replay-verification`, not `main` |
| `playbook` | `blocked by local active state` | dirty repo plus dense active governance/worktree family make this a live owner lane, not a bounded naming packet |
| `playbook` | `blocked by branch / non-main posture` | pinned and current branch are both `codex/playbook-sustain-docs-audit`, not `main` |
| `fitness` | `preserved / not yet admissible` | explicit preserved exception remains durable and this pass does not reopen product-facing or remote-identity surfaces |

## Repo Notes

### `trove`

Current durable posture:

- clean
- not on `main`
- additional registered worktrees still exist:
  - `tmp/deploy/fawxzzy-trove-prod`
  - `tmp/release-isolation/fawxzzy-trove-pwa-release`
  - prunable retained `r18` registrations
- stack inventory still carries excluded `trove_release_cutover_worktree` provenance

Interpretation:

- `trove` is not yet a safe-third candidate
- owner-side branch and retained-surface pressure must clear first

### `mazer`

Current durable posture:

- clean
- not on `main`
- published inventory still carries `initiative:initiative-mazer-d2-learning-scorer`
- current worktree family still includes multiple extra branch worktrees plus a prunable retained registration

Interpretation:

- `mazer` is not yet a safe-third candidate
- branch posture and active/local review pressure still block bounded rename execution

### `lifeline`

Current durable posture:

- dirty
- not on `main`
- active local-operator worktree family remains dense across multiple branches, including a retained `main` closeout worktree
- stack inventory still carries excluded `lifeline_operator_evidence_worktree` provenance

Interpretation:

- `lifeline` remains an owner-side live lane, not a naming packet

### `playbook`

Current durable posture:

- dirty
- not on `main`
- active governance/worktree family remains dense across multiple branches
- adjacent helper surface `repos/fawxzzy-playbook-codex` still remains visible in the excluded-surface set

Interpretation:

- `playbook` remains an owner-side live governance lane, not a naming packet

## Safe-Third Decision

No exact safe-third candidate exists on current facts.

Why:

- `trove` is still blocked by non-`main` branch posture and retained-surface/worktree pressure
- `mazer` is still blocked by non-`main` branch posture, initiative entanglement, and retained-surface/worktree pressure
- `lifeline` is still blocked by dirty owner-lane state and non-`main` branch posture
- `playbook` is still blocked by dirty owner-lane state and non-`main` branch posture

## Family Freeze Result

This pass freezes one durable family-wide result:

- no safe-third naming candidate is currently ready
- no more root-side naming execution or approval packets should open for this family until blocker class changes in one of the remaining repos

This avoids another one-repo-at-a-time control-plane loop.

## What This Pass Does Not Approve

This pass does not approve:

- any `trove` rename
- any `mazer` rename
- any `lifeline` rename
- any `playbook` rename
- any remote rename
- any GitHub-side rename
- any widening beyond the current remaining family

## Marker Read

No numeric marker move is justified from this pass alone.

Hold:

- `Atlas-owned Repo Naming Canonicalization`: `75% -> 75%`

Why:

- the pass clarifies the remaining family and freezes the no-safe-third result
- but no new executed-and-reconciled packet landed and no later blocker class actually cleared

## Exact Next Package

No new root naming package is open.

Next honest move:

- owner-side blocker conversion in one of `trove`, `mazer`, `lifeline`, or `playbook`
- then one exact family or candidate blocker-class recheck only after that owner-side reality changes

## Rule

Third-candidate selection must be family-batched, not rediscovered repo by repo.

## Failure Mode

The next naming candidate gets selected through another long serial chain of micro-passes that could have been decided in one family recheck.
