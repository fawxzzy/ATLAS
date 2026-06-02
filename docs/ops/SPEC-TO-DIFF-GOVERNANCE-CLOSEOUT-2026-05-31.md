# Spec-to-Diff Governance Closeout

- date: `2026-05-31`
- scope: root closeout for the spec-to-diff governance family
- status: mechanism closed, prompt-authoring migration closed for highest-signal maintained surfaces, legacy/historical expansion intentionally deferred

## Closed Now

- `_stack` spec-to-diff verification gate
- `_stack` mutating prompt-authoring migration
- owner-repo highest-signal mutating prompt migration across:
  - `repos/playbook`
  - `repos/fawxzzy-fitness`
  - `repos/mazer`

## Durable Rule

- Mutating Codex tasks are not governed unless they declare:
  - `Acceptance Criteria`
  - `Expected Changed Paths`
  - `Expected Unchanged Paths`
  - `Blocked / Skipped Reporting Rules`

- Summary text is not proof.

## Marker Decision

- `Core Pattern Convergence: 42% -> 43%`

Why:

- one named governed pattern moved from `_stack`-only doctrine into maintained owner-repo prompt generators, templates, and prompt-authoring docs
- this is proof-backed adoption widening, not wording cleanup

Held flat:

- `_stack` Readiness stays flat because this pass widened adoption of the already-closed mechanism rather than landing a broader `_stack` execution slice

## Deferred On Purpose

- historical prompt artifacts
- archived prompt artifacts
- runtime-generated prompt residue and logs
- owner-repo prompt surfaces that were not clearly high-frequency or clearly maintained
- any legacy-coverage widening beyond the bounded surfaces above

These are deferred scope decisions, not evidence that the governance family is still architecturally open.

## Residual Repo-Local Note

- `repos/mazer` still has an unrelated repo-local verify blocker tied to an external Playbook path dependency
- that blocker is not a prompt-contract failure and does not reopen this governance family

## Reopen Conditions

Reopen only if one of these becomes true:

- a maintained mutating prompt surface ships without the acceptance-criteria contract
- a real worker path again claims mutating completion without criterion-level diff proof
- an explicit legacy-prompt expansion lane is approved

## Next Optional Slices

- small owner-repo legacy prompt migration slices when a repo has a clearly maintained mutating prompt surface still on the compatibility path
- repo-local cleanup of unrelated verify blockers such as the current Mazer external-path dependency
