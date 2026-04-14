# Cortex Supervisor Runbook

The Cortex supervisor is a root-owned, read-only subsystem under `runtime/cortex/`. It is not an executor.

## Ownership Decision

Cortex is now modeled as a root-owned subsystem, not as a managed child repo. The active runtime surface is:

- `runtime/cortex/**`

The historical `repos/cortex` path is adjacent context only. It is not a release-eligible repo surface and it is not the active owner of supervisor behavior.

## Scope

The supervisor reads `_stack` worker artifacts and emits merge-request artifacts when deterministic conflicts are observed.

Inputs:

- `atlas.worker.assignment.v1`
- `atlas.worker.status.v1`

Outputs:

- `atlas.worker.merge-request.v1`

## Non-Goals

- no task execution
- no repo mutation
- no status rewriting
- no second orchestration model
- no hidden transcript-based conflict detection

## Observation Surface

Conflict checks are anchored to:

- `stack_lock_digest`
- `repo_commit`
- `file_digest_before`
- `path`
- `start_line`
- `end_line`
- `op`

## Conflict Rules

- same path + overlapping lines + same `file_digest_before` => `line_overlap`
- same path + different `file_digest_before` => `file_digest_drift`
- forbidden scope touches are reported separately as hard-fail observations

## Run

Dry-run against `_stack` examples:

```powershell
python ops/cortex/supervise_workers.py --artifact-path repos/_stack/docs/examples/stack-worker-artifacts --dry-run
```

Emit merge requests into the runtime supervisor lane:

```powershell
python ops/cortex/supervise_workers.py --artifact-path tmp/scratch/cortex-supervisor-fixtures --output-dir runtime/cortex/supervisor
```

## Merge-Request Emission Flow

1. load worker assignment and status artifacts
2. validate contract versions
3. require assignment-backed `stack_lock_digest` to match the current root lock
4. compare touched ranges pairwise
5. emit deterministic `atlas.worker.merge-request.v1` artifacts for overlap or drift conflicts

Forbidden-scope violations are reported in the supervisor summary output even when they do not produce a pairwise merge request.
