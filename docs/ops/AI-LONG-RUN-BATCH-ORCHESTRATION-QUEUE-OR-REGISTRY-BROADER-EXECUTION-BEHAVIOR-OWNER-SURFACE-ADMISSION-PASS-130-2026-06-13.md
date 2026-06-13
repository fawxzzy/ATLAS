# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Execution Behavior Owner-Surface Admission Pass 130 - 2026-06-13

- Date: `2026-06-13`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-EXECUTION-BEHAVIOR-CONTRACT-FREEZE-PASS-129-2026-06-13.md`
  - `repos/_stack/docs/dispatcher-protocol.md`
  - `repos/_stack/ops/stack/StackWorkerArtifacts.ps1`
  - `repos/_stack/queue/README.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@1e92804c`

## Objective

Admit one owner-facing home for `broader execution behavior` without implying queue mutation, worker-artifact emission, or launch behavior.

## Owner-Surface Candidates Considered

### `ATLAS root`

Why it does not win:

- root owns explicit-input truth and doctrine
- root does not own the shared operator command surface
- keeping wrapper-home ownership in root would collapse truth ownership and shared execution-home ownership again

### `Playbook`

Why it does not win:

- this seam is a shared operator behavior wrapper, not a doctrine export surface
- Playbook is not the right home for `_stack`-facing packaging commands

### owner repos

Why they do not win:

- no product repo should own stack-level explicit-input execution packaging
- the seam sits above product repos and below real worker launch

### `_stack`

Why it wins:

- `_stack` already owns shared operator command and worker-artifact contracts
- the wrapper belongs beside the queue, dispatcher, and worker-artifact surfaces it must stay compatible with
- `_stack` can host the shared command without displacing ATLAS as the truth owner

## Admission Decision

- truth owner remains:
  - `ATLAS root`
- execution home admitted now:
  - `_stack`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader execution behavior supporting-lane admission pass 131`

## Marker Decision

- `none`

## Rule

Keep broader execution-behavior truth in ATLAS and shared wrapper-home ownership in `_stack`.
