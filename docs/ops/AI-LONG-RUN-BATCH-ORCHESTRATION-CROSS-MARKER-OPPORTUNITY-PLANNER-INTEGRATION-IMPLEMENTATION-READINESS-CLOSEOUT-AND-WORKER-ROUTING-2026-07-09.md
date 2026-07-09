# AI Long-Run Batch Orchestration cross-marker opportunity planner-integration implementation-readiness closeout and worker routing

- Date: `2026-07-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `ATLAS-root docs-only implementation-readiness closeout`
- Marker movement: none

## Objective

Close the remaining root-only design question for planner-side cross-marker advisory consumption and route one bounded worker.

## Source Chain

The readiness decision rests on this durable chain:

- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-OPPORTUNITY-PLANNER-INTEGRATION-SELECTION-2026-07-09.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-OPPORTUNITY-PLANNER-INTEGRATION-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-OPPORTUNITY-PLANNER-INTEGRATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-OPPORTUNITY-PLANNER-INTEGRATION-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md`

## Readiness Decision

The planner-integration slice is `implementation_ready`.

Why:

- the helper/test touch surface is frozen
- the non-actionable hold branch is explicit
- the bounded uplift branch is explicit
- the proof commands are explicit
- no remaining root-only ambiguity blocks one bounded worker

## Exact Worker Objective

Implement one bounded planner/test update that consumes cross-marker helper output as advisory candidate context, proves both the non-actionable hold branch and the bounded uplift branch, and preserves all existing authority denials and protected-surface rejection behavior.

## Exact Allowed Touch Surfaces

The worker may touch only:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

## Exact Post-Worker Package

If the worker lands cleanly, the exact next package is:

```text
AI Long-Run Batch Orchestration cross-marker opportunity planner-integration first-implementation worker-cluster reconciliation
```

That reconciliation may add one bounded receipt plus continuity and ATLAS Book mirrors only after focused proof, live planner output, and clean stack validation succeed.

## Marker Decision

No marker moves.

`AI Long-Run Batch Orchestration` remains `70%`.
