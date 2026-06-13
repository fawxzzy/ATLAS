# _Stack Readiness Stack Queue-Or-Registry Live Direct-Json-Read Follow-On Command-Design Pass 108 - 2026-06-13

- Date: `2026-06-13`
- Lane: `_stack Readiness stack queue-or-registry live direct-json-read follow-on command-design pass 108`
- Mode: `docs-only root-bounded command design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LIVE-DIRECT-JSON-READ-FOLLOW-ON-CONTRACT-FREEZE-PASS-105-2026-06-13.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LIVE-DIRECT-JSON-READ-FOLLOW-ON-OWNER-SURFACE-ADMISSION-PASS-106-2026-06-13.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-LIVE-DIRECT-JSON-READ-FOLLOW-ON-SUPPORTING-LANE-ADMISSION-PASS-107-2026-06-13.md`
  - `ops/atlas/runtime_state_execution_ready_transition_semantics.py`
  - `repos/_stack/scripts/queue-or-registry-follow-on.mjs`
  - `repos/_stack/README.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@f19ea141`

## Objective

Freeze one compact command spine for the future `_stack` helper that performs one bounded direct-json read after classifier recheck and nothing broader.

## Exact Command Purpose

`stack queue-or-registry live-direct-json-read-follow-on` exists to:

- accept one explicit `candidate_path`
- invoke the authoritative ATLAS execution-transition classifier
- continue only when the candidate remains in `blocked-pending-live-direct-json-read`
- perform one exact utf-8 JSON file read at that same bounded path
- emit one bounded read report or one bounded contradiction

It does not exist to:

- discover directories or sibling files
- infer queue or registry semantics from content
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
- `direct_json_read_status`
- `artifact_value_kind`
- `artifact_top_level_keys`
- `classifier_ref`
- `routing_note`

## Exact Failure Exits

- `invalid-input`
- `classifier-failed`
- `unsupported-transition`
- `artifact-missing`
- `artifact-malformed`

## Exact No-Mutation Guard

The command may only:

- recheck the authoritative classifier
- read one exact json file
- render one bounded report

The command may not:

- write files
- scan directories
- widen beyond the supplied candidate path
- imply execution-ready movement or owner-readiness proof

## Exact Next Package

- `_Stack Readiness stack queue-or-registry live direct-json-read follow-on evidence-admission and contradiction-discipline pass 109`

## Marker Decision

- `none`

## Rule

Freeze the read-only command spine before admitting evidence or contradiction wording.
