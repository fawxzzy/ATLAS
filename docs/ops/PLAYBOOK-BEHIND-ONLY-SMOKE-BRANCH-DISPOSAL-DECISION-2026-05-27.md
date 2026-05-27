# Playbook Behind-Only Smoke Branch Disposal Decision - 2026-05-27

- Date: `2026-05-27`
- Lane: `Playbook behind-only smoke branch disposal decision pass`
- Mode: `decision-only`
- Source checkpoint: `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-WORKTREE-SMOKE-CLOSEOUT-RECHECK-2026-05-27.md`
- Control-plane checkpoint: `main@0ba8a5b`

## Objective

Decide whether the remaining Playbook behind-only smoke branch refs have a safe disposal subset without widening into stash disposal, Lifeline evidence disposal, or branch/worktree cleanup by implication.

This pass does not:

- delete branches
- remove worktrees
- drop stashes
- delete files or directories
- mutate repo code
- mutate Supabase, Vercel, Discord, runtime, schema, or data surfaces
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `0ba8a5b84dcf8a9e2dc7b8d87f6f57ec0f31acbf`
- status: clean except intentional untracked `archive/`

## Inputs

- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-WORKTREE-SMOKE-DISPOSAL-DECISION-2026-05-27.md`
- `docs/ops/PLAYBOOK-EXTERNAL-CODEX-WORKTREE-STRANDED-DIRECTORY-DISPOSAL-2026-05-27.md`
- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-WORKTREE-SMOKE-CLOSEOUT-RECHECK-2026-05-27.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-WORKTREE-RESIDUE-PLAN-2026-05-25.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-RESIDUE-DISPOSAL-2026-05-25.md`
- `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-CONSOLIDATION-2026-05-27.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `stack.yaml`
- `stack.lock.yaml`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## Branch Inventory

The remaining behind-only Playbook smoke branch refs are:

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

Reconfirmed current truth for the entire class:

- every branch tracks `origin/main`
- every branch is `behind 74`
- no branch is `ahead`
- no live git worktree is attached to any branch in this class
- the deleted Playbook `.codex/worktrees/*` directory family is already gone and no longer keeps any branch alive

## Reference / Dependency Check

### Live worktree dependency

None of the 14 branch refs appears in the current Playbook worktree list.

### Current restart-surface dependency

No current ATLAS Book restart surface depends on any specific branch in this class as an active checkpoint.

### Receipt dependency

The branches still appear in historical receipts, but only as:

- the behind-only smoke residue family named in the earlier external-smoke decision chain
- the branch family left intentionally untouched by the filesystem-only deletion pass
- the branch-only class explicitly named for this decision pass

Those historical mentions do not require keeping the live branch refs themselves once this decision is durable.

### Safety / manual-review dependency

None of the 14 branches is currently framed as:

- a safety checkpoint
- an evidence-bearing surface
- a manual-review branch with unique ahead-of-main work

The branches all resolve to the same behind-only merge-base style subject and have no distinct retention signal beyond stale smoke residue.

## Per-Branch Classification

| Branch | Upstream relation | Live worktree attached | Current dependency class | Classification |
| --- | --- | --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/codex-inbox-smoke-four` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/codex-inbox-smoke-one` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/codex-inbox-smoke-one-2` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/codex-inbox-smoke-three` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/codex-inbox-smoke-two` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/codex-inbox-smoke-two-2` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/mock-stdin-smoke-eight` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/mock-stdin-smoke-seven` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/mock-watcher-smoke-four` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/mock-watcher-smoke-one` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/mock-watcher-smoke-three` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/mock-watcher-smoke-two` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |
| `codex/tmp-check` | `origin/main`, behind `74` | no | historical residue reference only | safe-delete candidate |

## Unknown-Dependency Check

No branch in this class is blocked by a newly unknown dependency.

No branch in this class needs to remain live because of:

- a current worktree attachment
- a current restart-surface dependency
- a safety-checkpoint role
- an ahead-of-main proof or evidence role

## Safe Execution Subset

One exact safe execution subset exists.

Allowed next execution class:

- delete only the 14 behind-only Playbook smoke branch refs listed in this receipt

Boundary:

- branch deletion only
- no stash drop
- no worktree removal
- no filesystem cleanup
- no Lifeline mutation
- no Playbook manual-review worktree mutation

## What Remains Out Of Scope

Still explicitly out of scope after this decision:

- Playbook stashes
- Playbook manual-review worktrees
- Playbook detached checkpoint `playbook-main-closeout`
- Lifeline evidence-bearing worktrees
- Lifeline safety checkpoints
- Lifeline manual-review worktrees

## Marker Reassessment

Keep markers unchanged in this decision pass.

Recommended unchanged markers:

- `Branch & Worktree Normalization`: `99%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Inventory & Truth Map`: `74%`

Reason:

- this pass only opens a narrow branch-only execution subset
- it does not itself consume the branch class

## Exact Next Package

`Playbook behind-only smoke branch disposal execution pass`

That package should:

- delete only the 14 branch refs listed here
- leave stashes, worktrees, checkpoints, and Lifeline surfaces untouched
- rerun stack validation and then recheck whether any retained branch/worktree blocker still prevents `Branch & Worktree Normalization` from reaching `100%`

## Outcome

The Playbook behind-only smoke branch class is now decision-cleared.

Current truth:

- the deleted Playbook external `.codex/worktrees/*` residue no longer blocks anything in this class
- all 14 remaining behind-only smoke branch refs are safe-delete candidates
- the next correct move is a narrow branch-only execution pass, not a broader retained-surface cleanup lane
