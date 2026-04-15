# Stack Lockfile

This document defines the pinned working-set contract for root-driven ATLAS orchestration.

## Purpose

`stack.yaml` remains the human-authored stack manifest.

`stack.lock.yaml` is the generated, pinned working-set snapshot that lets root-launched workflows name an exact set of repo refs without turning child repos into submodules.

Root rule:

- the manifest declares
- the lockfile pins
- receipts and validation prove

## File

- `stack.lock.yaml`

Generator:

- `ops/stack/generate_lockfile.py`

Validation:

- `ops/validation/validate_stack.py`
- debt reporting: `runtime/receipts/validation/stack-validation.latest.json`

## Schema

- `schema_version`: `atlas.stack.lock.v1`
- `stack_manifest_path`
- `stack_manifest_digest`
- `component_count`
- `components`
- `excluded_surfaces`
- `lock_digest`

Each `components.<repo_id>` entry records:

- `path`
- `role`
- `status`
- `remote`
- `ref_type`
- `ref`
- `commit`
- `dirty`
- `trust_class`
- `release_eligible`

Each `excluded_surfaces.<surface_id>` entry records:

- `path`
- `present`
- `trust_class`
- `release_eligible`
- `reason`

## Trust Class Policy

- `trusted`: normal managed repo surface that may participate in root-driven workflows
- `adjacent`: known surface that exists beside the managed set but is not treated as a release candidate by default
- `untrusted`: quarantined or unsafe surface that must stay out of release sets and privileged orchestration

Release rule:

- only `trusted` components may be `release_eligible: true`

Current explicit exclusions:

- `repos/Verta-Core`
- `repos/Verta-Core.zip`

Both remain `untrusted` and `release_eligible: false` until scrub and rotation are complete.

## Refresh Workflow

Regenerate the committed lockfile only after an intentional pinned-working-set change:

- a repo HEAD moved and the new commit/ref is now the intended stack truth
- a repo changed branches or detached/tag pinning changed intentionally
- a component dirty/clean state changed and that new state should become the pinned truth
- stack registry or trust-policy inputs changed in `stack.yaml`

Regenerate in place:

```powershell
python .\ops\stack\generate_lockfile.py
```

Validate the refreshed lock against the current working set:

```powershell
python .\ops\validation\validate_stack.py --ratchet
```

Validate a non-default or temporary lockfile:

```powershell
python .\ops\validation\validate_stack.py --lock-file .\tmp\scratch\stack.lock.test.yaml --ratchet
```

## Determinism

The lockfile is stable when the pinned working set is unchanged.

Stability rules:

- no wall-clock timestamp in the file
- generation and validation both compare the same canonicalized payload
- component keys sorted by repo id
- excluded surfaces sorted by surface id
- scalar values normalized before digesting and comparison
- `lock_digest` computed from the stable payload

## Drift Semantics

The validator reports lock drift when the committed file no longer matches the generated canonical payload for the current stack state.

It reports specific blockers when:

- a pinned component path is missing
- a pinned ref no longer exists
- a pinned commit no longer matches the live repo state
- a pinned dirty/clean state no longer matches the live worktree state
- a pinned component or excluded surface field no longer matches the generated canonical payload
- an untrusted or adjacent component is marked `release_eligible`

Policy:

- intentional stack-state change: regenerate `stack.lock.yaml`, then rerun validation
- unintentional drift or unknown repo movement: fail validation and reconcile the repo state first
- identical repo state with differing lock output: treat that as a generator/validator bug and fix normalization before refreshing the file

Ratchet rule:

- lock refresh is allowed for intentional working-set changes
- lock refresh must not be used to hide unrelated inherited debt
- inherited debt is tracked through the debt ledger and ratchet classes, not by changing the lock alone

## Dirty State Policy

Dirty state is pinned as part of the working-set truth.

- there are currently no dirty-state exceptions
- a repo may be intentionally locked as `dirty: true`
- if a repo flips between dirty and clean, validation should fail until the stack owner either restores the prior state or intentionally regenerates the lockfile

## Scope

The lockfile pins the current root working set across the stack control repo and the explicitly included child repos.

The pinned set now includes the `_stack` workflow operator repo so root sessions do not treat `_stack` as an ambient unchecked dependency.

It does not:

- convert child repos to submodules
- promote untrusted checkouts into managed release surfaces
- replace the repo registry or topology audit
