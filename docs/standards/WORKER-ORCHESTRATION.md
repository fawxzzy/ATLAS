# Worker Orchestration

This standard defines the root-launched worker contracts for MeSeeks-style coordination.

## Contract Set

- `schemas/atlas.worker.assignment.v1.json`
- `schemas/atlas.worker.status.v1.json`
- `schemas/atlas.worker.merge-request.v1.json`

## Assignment Model

An assignment is the root-issued contract for what a worker may touch.

Required fields:

- `assignment_id`
- `worker_id`
- `task_id`
- `stack_lock_digest`
- `allowed_globs`
- `forbidden_globs`
- `input_handoff_refs`
- `expected_outputs`

Rules:

- assignments are bound to a specific `stack_lock_digest`
- allowed scope is expressed as path globs only
- forbidden globs are hard exclusions and override any broader allowance
- input handoff refs define the only approved starting context

## Status Model

Status is the only ongoing observation surface for worker progress.

Required fields:

- `worker_id`
- `assignment_id`
- `state`
- `heartbeat_at`
- `touched_ranges`
- `output_refs`
- `blocked_reason`

Each `touched_ranges` item must include:

- `repo_path`
- `repo_commit`
- `file_digest_before`
- `path`
- `start_line`
- `end_line`
- `op`

The observation surface is file and line range based, not transcript based.
Use manifest-root relative repo paths such as `.` or `repos/playbook`, not machine-specific absolute paths.

## Lifecycle

The state machine is intentionally small:

- `assigned`
- `running`
- `paused`
- `blocked`
- `merge_wait`
- `completed`
- `failed`

Flow:

1. root issues assignment
2. worker reports heartbeat and status updates
3. collisions or scope failures pause the worker
4. merge request is emitted when overlap or drift requires reconciliation
5. a merger worker receives a handoff artifact
6. paused workers resume only from the paused handoff artifacts

## Collision Policy

Collision detection must consider the commit and pre-edit digest, not just file path and line numbers.

Rules:

- same path + overlapping lines + same `file_digest_before` = conflict
- same path + different `file_digest_before` = drift conflict, pause both
- forbidden scope touch = hard fail
- merge workers consume paused handoff refs, not raw transcripts

## Additive Evolution

- new fields may be added if they are optional
- required fields should only change with a new contract version
- contract consumers must ignore unknown fields
- version bumps are required for breaking changes

## Operational Rule

Workers report touched files and line ranges. They do not report full hidden reasoning as a coordination primitive.
