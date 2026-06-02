# Atlas-Owned Repo Naming Lifeline Safe-Next Execution Approval - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only governance / execution approval`
- Candidate: `lifeline`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-REMAINING-FAMILY-DELTA-RECHECK-PASS-3-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Freeze the exact safe-next approval packet for the already-selected candidate only:

- `repos/fawxzzy-lifeline -> repos/lifeline`

This pass does not:

- rename any repo directory
- rename any remote
- assume any GitHub-side rename
- reopen `mazer`, `playbook`, or `fawxzzy-fitness`
- mutate owner-repo content
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- validation before approval drafting: `critical=0 error=0 warning=376`

## Candidate Reconfirm

`lifeline` remains the exact honest safe-next candidate because:

- active repo path is `repos/fawxzzy-lifeline`
- target path `repos/lifeline` does not yet exist
- active repo branch posture is now `main`
- active repo dirty state is `clean`
- registered extra lifeline worktrees are gone
- repo-local verification already passed during owner-side blocker compression pass 2

## Exact Approved Local Rename

Approved local-only rename:

- source: `repos/fawxzzy-lifeline`
- target: `repos/lifeline`

Remote posture remains unchanged:

- remote URL stays `https://github.com/fawxzzy/fawxzzy-lifeline.git`
- no remote rename
- no GitHub rename

## Exact Rewrite Surface Set

Execution must stay within this frozen rewrite set:

1. local directory rename under `repos/`
2. `stack.yaml`
3. `stack.lock.yaml`
4. `docs/registry/STACK-REPO-INVENTORY.json`
5. `docs/audits/STACK-REPO-INVENTORY.md`
6. current-truth book surfaces only if they still imply the old active path
7. candidate execution receipt
8. `docs/atlas-book/05-receipt-index.md`
9. validation

Current expected path-truth check surfaces:

- `docs/atlas-book/11-system-map-graph.md`: expected no-op for old-path truth unless a canonical path mention appears during execution review
- `docs/atlas-book/12-restart-and-handoff-guide.md`: expected no-op for old-path truth during execution; ladder wording may still change later in proof or ratchet

Additional frozen current-truth surface tied to the registered lifeline family:

- `stack.yaml` excluded surface `lifeline_operator_evidence_worktree`

Reason:

- it is a current stack-owned manifest surface naming a lifeline-prefixed worktree path and should stay canonically aligned with the registered repo naming family

## Exact Rollback Order

If execution fails after mutation begins, rollback must use the frozen reverse order:

1. revert current-truth book-surface and execution-receipt/index updates
2. revert `docs/audits/STACK-REPO-INVENTORY.md`
3. revert `docs/registry/STACK-REPO-INVENTORY.json`
4. revert `stack.lock.yaml`
5. revert `stack.yaml`
6. rename `repos/lifeline` back to `repos/fawxzzy-lifeline`
7. rerun `python .\ops\validation\validate_stack.py`

## Explicitly Blocked Scope

This approval does not widen to:

- `mazer`
- `playbook`
- `fawxzzy-fitness`
- any remote rename
- any GitHub-side rename
- any multi-repo rename packet

## Exact Next Package

- `Atlas-owned Repo Naming lifeline local rename execution pass 1`

## Rule

Safe-next naming approval must freeze one exact candidate and one exact rewrite surface set, not reopen general rename exploration.

## Failure Mode

Approval wording becomes broad enough that later execution silently widens into `mazer`, `playbook`, remote rename assumptions, or unrelated book maintenance.
