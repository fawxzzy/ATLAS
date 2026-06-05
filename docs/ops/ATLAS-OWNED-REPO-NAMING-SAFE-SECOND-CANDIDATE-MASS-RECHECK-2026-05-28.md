# Atlas-Owned Repo Naming Safe-Second Candidate Mass Recheck - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only batched candidate decision pass`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 74%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-6-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-FIRST-EXECUTION-APPROVAL-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-INVENTORY-DEPENDENCY-MAP-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Re-evaluate the full remaining admitted internal naming-candidate family together, pick one exact safe-second candidate if one exists, and avoid another one-repo-at-a-time control-plane loop.

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
- status before drafting: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, and `PROCESS-AMPLIFICATION-PASS-2-2026-05-28.md`, plus intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=311`

## Remaining Candidate Family Reconfirmed

Remaining admitted internal prefixed candidates after the landed `stream` execution family:

- `repos/fawxzzy-foundation -> repos/foundation`
- `repos/fawxzzy-lifeline -> repos/lifeline`
- `repos/fawxzzy-mazer -> repos/mazer`
- `repos/fawxzzy-playbook -> repos/playbook`
- `repos/fawxzzy-trove -> repos/trove`

Explicit preserved exception:

- `repos/fawxzzy-fitness`

Not part of the remaining candidate family:

- `repos/stream` because the first bounded packet already executed and reconciled
- `repos/_stack` and `repos/DiscordOS` because they are already canonical in this lane
- `repos/Nat1-Games/nat1-games` and `repos/playbook-demo/playbook-demo` because they are admitted stack surfaces but do not carry the `fawxzzy-` local-prefix problem this lane is solving
- adjacent, excluded, recovery, and archive surfaces because they are not admitted naming candidates here

## Batch Scan Method

This pass scanned the full remaining family together using:

- current stack registry truth
- current stack-lock truth
- current repo inventory publication
- current system-map and restart-guide path references
- repo-local branch, dirty, remote, and worktree posture

Rule:

- second-candidate selection must be based on one family-wide read, not rediscovered repo by repo

## Family-Wide Read

The family-wide read changes one important fact relative to the older planning order:

- no remaining candidate is blocked only by generic dependency-mapping uncertainty

That class is now consumed.

What remains is candidate-local execution readiness versus candidate-local active-state pressure.

## Candidate Classification

| Candidate | Classification | Why |
| --- | --- | --- |
| `foundation` | `safe-second candidate` | clean, on `main`, only one registered worktree, no related initiative link in the published inventory, remote-name assumptions still stay out of scope, and the current-truth local-path rewrite footprint is bounded to stack registry plus inventory publication plus `11-system-map-graph.md` |
| `mazer` | `blocked by local active state` | not on `main`, published inventory still carries an active related initiative, and the repo currently has multiple additional worktrees including active temp worktrees and retained detached/prunable registrations |
| `trove` | `blocked by local active state` | not on `main` and the repo still carries additional deploy/release-isolation worktrees and retained detached/prunable registrations, so rename pressure would stack onto an active local surface family |
| `lifeline` | `blocked by local active state` | dirty, not on `main`, and currently carries a dense operator-worktree family across active branches, making this a live local-operator lane rather than a clean naming packet |
| `playbook` | `blocked by local active state` | dirty, not on `main`, and currently carries a dense governance/worktree family across multiple active branches, making this a live governance-runtime lane rather than a clean naming packet |
| `fitness` | `preserved / not admitted` | explicit preserved exception remains durable and this pass does not reopen product-facing or remote-identity surfaces |

## Candidate Notes

### `foundation`

Current durable posture:

- `stack.lock.yaml`: clean and pinned on `main`
- published inventory: no related initiative refs
- worktree posture: only the main worktree is registered
- remote posture: `origin` exists, but remote-name and GitHub-side rename assumptions remain prohibited
- current-truth path references:
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/11-system-map-graph.md`
- current no-op read:
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

Interpretation:

- the only reason `foundation` was not previously the first packet was deliberate ordering behind the smaller `stream` footprint
- that ordering reason is now consumed because `stream` has already executed and reconciled

### `mazer`

Current durable posture:

- clean, but not on `main`
- inventory still carries `initiative:initiative-mazer-d2-learning-scorer`
- worktree posture includes multiple extra branch worktrees plus retained detached/prunable registrations

Interpretation:

- this is not blocked by path-mapping ambiguity anymore
- it is blocked by active local state

### `trove`

Current durable posture:

- clean, but not on `main`
- worktree posture includes deploy/release-isolation worktrees plus retained detached/prunable registrations

Interpretation:

- this is not blocked by path-mapping ambiguity anymore
- it is blocked by active local state

### `lifeline`

Current durable posture:

- dirty
- not on `main`
- multiple active operator-oriented worktrees remain

Interpretation:

- this remains a live owner-lane surface, not a clean naming packet

### `playbook`

Current durable posture:

- dirty
- not on `main`
- multiple active governance-oriented worktrees remain

Interpretation:

- this remains a live owner-lane surface, not a clean naming packet

## Safe-Second Decision

Yes, one exact safe-second candidate exists now.

Selected safe-second candidate:

- `repos/fawxzzy-foundation -> repos/foundation`

Why this is the honest batched result:

- `stream` already consumed the smaller-footprint first-packet slot
- `foundation` is now the only remaining admitted prefixed candidate that is:
  - clean
  - on `main`
  - single-worktree in current registered posture
  - free of published initiative entanglement
  - not currently carrying owner-lane active-state pressure comparable to `lifeline`, `playbook`, `trove`, or `mazer`

## What This Decision Does Not Approve

This pass does not approve:

- the actual `foundation` rename
- any remote rename
- any GitHub-side rename
- any widening into `mazer`, `trove`, `lifeline`, or `playbook`
- any change to the `fawxzzy-fitness` preserved exception

Execution still requires a separate bounded approval or preflight pass for `foundation`.

## Batch Result If No Safe-Second Candidate Existed

That fallback was not needed.

This pass did not freeze a family-wide hold because one exact candidate is honestly ready for the next bounded decision step.

## Marker Read

No numeric marker move is justified from this pass alone.

Hold:

- `Atlas-owned Repo Naming Canonicalization`: `74% -> 74%`

Why:

- the pass improves candidate-family routing and removes rediscovery waste
- but no second executed and reconciled packet has landed yet

## Exact Next Package

`Atlas-owned Repo Naming foundation safe-second execution approval`

Why:

- the batched family recheck now leaves one exact candidate
- the next honest move is to freeze the bounded `foundation` execution packet explicitly instead of reopening another general naming loop

## Rule

Second-candidate selection should be batched across the admitted family, not rediscovered repo by repo.

## Pattern

first executed packet lands -> remaining family is rechecked together -> one exact safe-second candidate is selected -> bounded approval or preflight opens for that candidate only

## Failure Mode

The second naming candidate gets selected through another long serial chain of micro-passes that could have been decided in one batched recheck.
