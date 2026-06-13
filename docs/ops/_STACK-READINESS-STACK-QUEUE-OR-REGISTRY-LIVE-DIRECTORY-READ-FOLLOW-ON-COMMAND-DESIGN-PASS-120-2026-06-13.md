# _Stack Readiness Stack Queue-Or-Registry Live Directory-Read Follow-On Command-Design Pass 120 - 2026-06-13

- Date: `2026-06-13`
- Lane: `_stack Readiness stack queue-or-registry live directory-read follow-on command-design pass 120`
- Mode: `docs-only root-bounded command design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LIVE-DIRECTORY-READ-FOLLOW-ON-CONTRACT-FREEZE-PASS-117-2026-06-13.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LIVE-DIRECTORY-READ-FOLLOW-ON-OWNER-SURFACE-ADMISSION-PASS-118-2026-06-13.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LIVE-DIRECTORY-READ-FOLLOW-ON-SUPPORTING-LANE-ADMISSION-PASS-119-2026-06-13.md`
  - `ops/atlas/runtime_state_execution_ready_transition_semantics.py`
  - `repos/_stack/scripts/queue-or-registry-follow-on.mjs`
  - `repos/_stack/README.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@5065766d`

## Objective

Freeze one compact command spine for the future `_stack` helper that performs one bounded shallow directory read after classifier recheck and nothing broader.

## Exact Command Purpose

`stack queue-or-registry live-directory-read-follow-on` exists to:

- accept one explicit `candidate_path`
- invoke the authoritative ATLAS execution-transition classifier
- continue only when the candidate remains in `blocked-pending-live-directory-read`
- perform one exact shallow directory read at that same bounded path
- emit one bounded read report or one bounded contradiction

It does not exist to:

- recurse into nested directories
- infer queue or registry semantics from child names
- emit queue drops
- mutate any repo, receipt, lock, or book surface
- launch, resume, or route workers automatically

## Exact Inputs

- `--format <text|json>`
- `--candidate-path <relative-path>`

## Exact Success Surface

- `normalized_candidate_path`
- `destination_class`
- `execution_transition_class`
- `directory_read_status`
- `child_entry_count`
- `child_entry_names`
- `classifier_ref`
- `routing_note`

## Exact Failure Exits

- `invalid-input`
- `classifier-failed`
- `unsupported-transition`
- `artifact-missing`
- `artifact-not-directory`

## Exact No-Mutation Guard

The command may only:

- recheck the authoritative classifier
- perform one shallow directory read
- render one bounded report

The command may not:

- write files
- recurse below the supplied candidate path
- widen beyond the supplied candidate path
- imply execution-ready movement or owner-readiness proof

## Exact Next Package

- `_Stack Readiness stack queue-or-registry live directory-read follow-on evidence-admission and contradiction-discipline pass 121`

## Marker Decision

- `none`

## Rule

Freeze the read-only command spine before admitting evidence or contradiction wording.
