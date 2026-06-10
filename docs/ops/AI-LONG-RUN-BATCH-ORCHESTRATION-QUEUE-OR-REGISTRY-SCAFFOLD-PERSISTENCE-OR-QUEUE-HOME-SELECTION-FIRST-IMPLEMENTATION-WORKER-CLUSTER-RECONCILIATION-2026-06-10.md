# AI Long-Run Batch Orchestration Queue-Or-Registry Scaffold Persistence Or Queue-Home Selection First-Implementation Worker Cluster Reconciliation - 2026-06-10

- Date: `2026-06-10`
- Owner: ATLAS root
- Mode: `docs-only root reconciliation`
- Scope: `scaffold persistence or queue-home selection first implementation worker cluster reconciliation`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-CONTRACT-FREEZE-PASS-30-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-OWNER-SURFACE-ADMISSION-PASS-31-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-SUPPORTING-LANE-ADMISSION-PASS-32-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-FIRST-IMPLEMENTATION-ADMISSION-PASS-33-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-PROMPT-PACK-AND-HANDOFF-CONTRACT-PASS-34-2026-06-10.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SCAFFOLD-PERSISTENCE-OR-QUEUE-HOME-SELECTION-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-PASS-35-2026-06-10.md`
  - `ops/atlas/scaffold_persistence_or_queue_home_selection.py`
  - `ops/atlas/test_scaffold_persistence_or_queue_home_selection.py`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/runtime-root-candidate.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/runtime-descendant-candidate.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/repo-root-candidate.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/fixture-or-import-candidate.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/scratch-or-package-candidate.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/secret-candidate.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/multi-candidate-payload.json`
  - `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/queue-or-execution-hint-payload.json`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`

## Objective

Reconcile the first root-local `scaffold persistence or queue-home selection` implementation cluster against the frozen pass-30-through-pass-35 chain, refresh the shared restart spines once, and freeze the exact post-cluster routing truth without widening into queue mutation, runtime-state discovery, concrete runtime layout, validator execution, supervisor behavior, or execution-home claims.

## Worker Ownership Check

Frozen packet ownership was:

- worker execution and proof tightening inside `ops/atlas/**` and `data/fixtures/**`
- root reconciliation only after the bounded worker cluster returned
- no owner-repo mutation, `_stack` mutation, or protected-surface mutation during execution

Observed execution stayed inside that split.

## Worker Cluster Reconciliation

Files changed across the cluster:

- `ops/atlas/scaffold_persistence_or_queue_home_selection.py`
- `ops/atlas/test_scaffold_persistence_or_queue_home_selection.py`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/runtime-root-candidate.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/runtime-descendant-candidate.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/repo-root-candidate.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/fixture-or-import-candidate.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/scratch-or-package-candidate.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/secret-candidate.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/multi-candidate-payload.json`
- `data/fixtures/ai-long-run-batch-orchestration/scaffold-persistence-or-queue-home-selection/queue-or-execution-hint-payload.json`

Reconciliation decision:

- `clean`

Why:

- packet 1 landed the already-admitted root-local storage-home slice as one helper that loads exactly one explicit candidate path, normalizes it root-relatively, classifies only the top-level home class, emits only the frozen decision payload surface, preserves the deferred-layout note, and fails closed on unsupported input
- valid runtime-root and runtime-descendant candidates are now directly proven admitted without widening into concrete runtime subpath, filename, schema, or persistence-layout choice
- forbidden repo, data, tmp, and secrets branches are now directly proven to return `forbidden-home-class` rather than being normalized into alternate storage homes
- multi-candidate and queue-or-execution-hint payloads are now directly proven to fail closed rather than being treated as partial queue-home selection or execution-home intent
- packet 1 stayed fully outside queue creation, queue mutation, registry mutation, directory creation, file creation, runtime-state discovery, concrete runtime-layout selection, validator execution, supervisor behavior, dispatch, resume, and status-transition behavior
- no protected surface, owner-repo mutation surface, `_stack` execution surface, or Playbook doctrine surface was touched

Result class:

- `executed state changed plus first-slice closeout`

Marker consequence:

- `AI Long-Run Batch Orchestration` now has one reconciled first implementation landing for the admitted `scaffold persistence or queue-home selection` slice, so one smallest honest ratchet is justified
- the move stays to one increment because no final queue home, registry home, execution home, supervised pilot, or broader operator adoption landed

## Validation And Proof

Observed proof commands:

- `python .\ops\validation\compile_python_tools.py --path .\ops\atlas`
- `python -m unittest discover -s .\ops\atlas -p "test_scaffold_persistence_or_queue_home_selection.py"`
- `python .\ops\atlas\scaffold_persistence_or_queue_home_selection.py --input .\data\fixtures\ai-long-run-batch-orchestration\scaffold-persistence-or-queue-home-selection\runtime-root-candidate.json`
- `python .\ops\atlas\scaffold_persistence_or_queue_home_selection.py --input .\data\fixtures\ai-long-run-batch-orchestration\scaffold-persistence-or-queue-home-selection\runtime-descendant-candidate.json`
- `python .\ops\atlas\scaffold_persistence_or_queue_home_selection.py --input .\data\fixtures\ai-long-run-batch-orchestration\scaffold-persistence-or-queue-home-selection\repo-root-candidate.json`
- `python .\ops\atlas\scaffold_persistence_or_queue_home_selection.py --input .\data\fixtures\ai-long-run-batch-orchestration\scaffold-persistence-or-queue-home-selection\queue-or-execution-hint-payload.json`

Observed results:

- compile helper completed cleanly
- bounded unittest proof passed at `8` tests
- valid CLI fixture runs admit the exact frozen runtime-home decision payload surface
- forbidden-home CLI fixture runs return the exact frozen `forbidden-home-class` decision
- queue-or-execution-hint CLI fixture runs fail closed at the admitted unsupported-field boundary
- root validation remained clean at `critical=0 error=0 warning=51 info=0`

## Shared Restart Spine Refresh

Shared restart spines now refresh because the worker cluster is reconciled:

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

## Marker Decision

Decision:

- `AI Long-Run Batch Orchestration: 24% -> 25%`

Why:

- the lane now has one additional real executed state change for the admitted `scaffold persistence or queue-home selection` slice
- the move stays to the smallest honest increment because no final queue home, registry home, execution home, supervised pilot, or broader operator adoption landed

## Exact Post-Cluster Routing

- `AI Long-Run Batch Orchestration queue-or-registry next-slice selection pass 36`

Why:

- the first storage-home classifier slice is now landed and reconciled
- the next honest question is which deferred later slice should advance next without widening into concrete runtime layout, validator execution, lifecycle behavior, or execution-home semantics by implication

## Health Check

- protected surfaces remained untouched
- `_stack Readiness` remained closed at `100%`
- no unrelated root lane was reopened during this execution cluster

## Rule

Land one admitted storage-home classifier slice, then select the next slice from reconciled truth rather than widening the same helper into queue-home semantics by convenience.

## Pattern

freeze storage-home seam -> freeze storage-home prompt pack -> close readiness -> land bounded worker -> reconcile once -> only then select the next slice

## Failure Mode

`Storage-Home Slice Scope Drift`

If the first storage-home landing is allowed to continue directly into queue mutation, concrete runtime-layout invention, validator execution, or lifecycle narration before reconciliation close, the lane sounds more mature than the frozen contract actually proves.
