# Atlas-Owned Repo Naming Remaining-Family Delta Recheck - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only family delta recheck`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 75%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BLOCKED-STATE-FAMILY-RECHECK-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-THIRD-CANDIDATE-DECISION-2026-05-28.md`
  - `repos/fawxzzy-trove/docs/naming-blocker-conversion-assessment-pass-1.md`
  - `repos/fawxzzy-trove/docs/naming-blocker-conversion-closeout-pass-2.md`
  - `repos/fawxzzy-mazer/docs/naming-blocker-conversion-assessment-pass-1.md`
  - `repos/fawxzzy-lifeline/docs/naming-blocker-conversion-assessment-pass-1.md`
  - `repos/fawxzzy-playbook/docs/naming-blocker-conversion-assessment-pass-1.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Re-evaluate `trove`, `mazer`, `lifeline`, and `playbook` after the owner-side blocker conversion batch and decide whether exactly one honest safe-third candidate now exists.

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
- status before drafting: existing ATLAS docs-only changes in `AGENTS.md`, atlas-book surfaces, naming receipts, `stack.yaml`, `stack.lock.yaml`, inventory surfaces, and intentional untracked `archive/`
- validation before drafting: `critical=0 error=4 warning=366`

Current blocking validation errors are limited to lock-registry drift:

- `stack.lock.yaml`: working set mismatch
- `stack.lock.yaml`: canonical generated payload mismatch
- `stack.lock.yaml#mazer`: pinned `ref` differs from generated working set
- `stack.lock.yaml#trove`: pinned `ref` differs from generated working set

This pass does not resolve those lockfile errors.

## Delta Read

The prior remaining-family state froze `none ready`.

The owner-side conversion batch materially changed that result:

- `trove` advanced from one remaining blocker to zero blockers
- `mazer` collapsed from multiple abstract blockers to one exact owner-side blocker class
- `lifeline` collapsed from multiple abstract blockers to one exact owner-side blocker class
- `playbook` collapsed from multiple abstract blockers to one exact owner-side blocker class, but remains the broadest blocked lane in the family

That means this is no longer a `none ready` family.

It is now a one-candidate family with three still-blocked members.

## Candidate Classification

| Candidate | Classification | Exact blocker / reason |
| --- | --- | --- |
| `trove` | `safe-third candidate` | active repo is clean on local `main`; no registered extra trove worktrees remain; owner-side blocker class is `none` |
| `mazer` | `still blocked` | `blocked by active owner-side multi-worktree lane` |
| `lifeline` | `still blocked` | `blocked by active owner-side release lane closeout` |
| `playbook` | `still blocked` | `blocked by active owner-side release-governance multi-worktree lane` |

Explicit preserved exception remains unchanged:

- `fawxzzy-fitness`: `preserved / not yet admissible`

## Repo Notes

### `trove`

Current durable posture:

- active repo branch: `main`
- active repo dirty state: `clean`
- registered extra trove worktrees: `none`
- owner-side blocker class: `none`

Interpretation:

- `trove` is now the exact honest safe-third candidate
- no additional owner-side trove blocker conversion remains open

### `mazer`

Current durable posture:

- active repo branch: `main`
- active repo dirty state: `clean`
- remaining blocker class: `blocked by active owner-side multi-worktree lane`

Interpretation:

- `mazer` is materially clearer than before
- `mazer` is not yet safe-third because the remaining worktree family is still too broad for a bounded rename packet

### `lifeline`

Current durable posture:

- active repo branch: `codex/lifeline-release-replay-verification`
- active repo dirty state: narrow local docs and `.codex` residue
- remaining blocker class: `blocked by active owner-side release lane closeout`

Interpretation:

- `lifeline` is closer than before
- `lifeline` is not yet safe-third because the active release lane still needs an explicit preserve-or-closeout decision

### `playbook`

Current durable posture:

- active repo branch: `codex/playbook-sustain-docs-audit`
- active repo dirty state: broad staged and unstaged release/runtime/test surface
- remaining blocker class: `blocked by active owner-side release-governance multi-worktree lane`
- repo-local verify currently fails on `verify.failure.release.requiredVersionBump.missing`

Interpretation:

- `playbook` remains the broadest blocked member
- `playbook` is not near safe-third readiness yet

## Exact Safe-Third Result

Exactly one honest safe-third candidate now exists:

- `trove`

Why this is the honest selection:

- `trove` is the only remaining family member with zero owner-side naming blockers
- `mazer`, `lifeline`, and `playbook` all remain blocked by exact owner-side lane classes
- this result comes from owner-side class changes, not from looser wording or speculative readiness

## What This Pass Freezes

This pass freezes:

- `trove` as the exact safe-third candidate
- `mazer`, `lifeline`, and `playbook` as still blocked
- the remaining family as no longer `none ready`, but not yet broader than one exact candidate

## What This Pass Does Not Approve

This pass does not approve:

- the `trove` rename execution itself
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

- the family delta is materially stronger
- but no third executed-and-reconciled naming packet has landed yet

## Exact Next Package

Exact next naming package:

- `Atlas-owned Repo Naming trove safe-third execution approval`

Separate control-plane note:

- stack validation is not green on current root state because `stack.lock.yaml` still lags the current `trove` and `mazer` working-set refs
- that lock-registry drift should be reconciled, but it does not change the safe-third classification itself

## Rule

Remaining-family delta rechecks must select one exact candidate or hold `none ready`, not reopen serial per-repo rediscovery loops.

## Failure Mode

A family delta pass sees a real class change, but still reports several vague "maybes" instead of freezing the one exact candidate that actually became ready.
