# Stack Lockfile

This document defines the pinned working-set contract for root-driven ATLAS orchestration.

## Purpose

`stack.yaml` remains the human-authored stack manifest.

`stack.lock.yaml` is the generated, pinned working-set snapshot that lets root-launched workflows name an exact set of repo refs without turning child repos into submodules.

Root rule:

- the manifest declares
- the lockfile pins
- the repo inventory publishes visible topology
- receipts and validation prove

## File

- `stack.lock.yaml`

Generator:

- `ops/stack/generate_lockfile.py`

Validation:

- `ops/validation/validate_stack.py`
- debt reporting: `runtime/receipts/validation/stack-validation.latest.json`
- visibility export: `ops/stack/export_repo_inventory.py`
- published surfaces:
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`

Shared comparison contract:

- generator normalization and validator drift comparison both flow through the same canonical payload diff helpers in `ops/stack/generate_lockfile.py`
- generator writes the canonical lockfile bytes from that shared path, and validation compares the on-disk file against those exact canonical bytes
- lock refresh bugs are treated as normalization bugs first, not as operator excuses to repin blindly

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
- `adjacent`: known surface that exists beside the managed set but is not treated as a release candidate by default; use this for deferred local checkouts, recovery clones, or sibling repos that should stay visible without becoming governed stack members
- `untrusted`: quarantined or unsafe surface that must stay out of release sets and privileged orchestration

Release rule:

- only `trusted` components may be `release_eligible: true`

Current explicit exclusions may include:

- trusted temporary worktrees
- adjacent deferred local checkouts such as recovery clones or sibling repos that are present locally but not admitted
- untrusted Verta surfaces

`repos/Verta-Core` and `repos/Verta-Core.zip` remain `untrusted` and `release_eligible: false` until scrub and rotation are complete.

## Refresh Workflow

Regenerate the committed lockfile only after an intentional pinned-working-set change:

- a repo HEAD moved and the new commit/ref is now the intended stack truth
- a repo changed branches or detached/tag pinning changed intentionally
- a component dirty/clean state changed and that new state should become the pinned truth
- stack registry or trust-policy inputs changed in `stack.yaml`

Do not regenerate just because validation is red. Refresh is allowed only when the current live state is the intended pinned truth.

Regenerate in place:

```powershell
python .\ops\stack\generate_lockfile.py
```

Validate the refreshed lock against the current working set:

```powershell
python .\ops\validation\validate_stack.py --ratchet
```

Certification/preflight exception:

- `stack.lock.yaml` may remain as the sole uncommitted root delta only when that file already equals the canonical generated lockfile for the current live working set
- this exception applies only to stack-root preflight and certification gates
- it does not excuse any second modified root file, any stale or non-canonical `stack.lock.yaml`, or any dirty child repo

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
- byte-identical canonical output is part of the contract; a semantically similar but non-canonical render still fails validation

Debt classification:

- `stack-lock-pin-drift`: ref, commit, membership, or other pinned metadata differs from current intended truth
- `stack-lock-worktree-drift`: the only mismatch is `dirty`; this is a worktree-state drift, not a repin of execution truth
- inherited baseline debt: unrelated ratchet blockers remain ledgered by class and must not be hidden by lock refresh

Ratchet rule:

- lock refresh is allowed for intentional working-set changes
- lock refresh must not be used to hide unrelated inherited debt
- inherited debt is tracked through the debt ledger and ratchet classes, not by changing the lock alone

Operational rule:

- regenerate when the intended pinned state changed
- fail closed when the live state is unexpected
- fix the diff contract when generation and validation disagree on unchanged state

## Dirty State Policy

Dirty state is pinned as part of the working-set truth.

- a repo may be intentionally locked as `dirty: true`
- if a repo flips between dirty and clean, validation should fail until the stack owner either restores the prior state or intentionally regenerates the lockfile
- sole exception: for the stack control repo only, preflight/cert treats `stack.dirty_effective = false` when `stack.lock.yaml` is the only modified root file and its on-disk bytes exactly match the canonical generated lockfile for the current live working set
- this is not a general dirty-worktree exemption; it does not apply to any other root file, any second root delta, any non-canonical lockfile bytes, or any child repo

## Scope

The lockfile pins the current root working set across the stack control repo and the explicitly included child repos.

The pinned set now includes the `_stack` workflow operator repo so root sessions do not treat `_stack` as an ambient unchecked dependency.

It does not:

- convert child repos to submodules
- make the root repo a second source checkout for child repos
- promote untrusted checkouts into managed release surfaces
- replace the repo registry or topology audit

## Inventory Relationship

Use the lockfile and repo inventory together:

- `stack.yaml` declares which repo ids and paths exist
- `stack.lock.yaml` pins the intended managed working set
- `STACK-REPO-INVENTORY` publishes the live, searchable visibility surface for root status, chat, and cockpit clients

Policy:

- the lockfile is a pinning contract
- the inventory is a visibility contract
- neither changes the independent topology of child repos
- `repos/**` stays untracked by the root repo as source; only stack-owned docs and audits outside that tree are committed here
