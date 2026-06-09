# AI Long-Run Batch Orchestration Queue-Or-Registry Contract Freeze Pass 1 - 2026-06-09

- Date: `2026-06-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-SURFACE-PASS-52-2026-06-09.md`
  - `docs/ops/ROOT-NON-FITNESS-MARKER-KNOCKOUT-CAMPAIGN-2026-06-09.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one exact storage-agnostic queue-or-registry contract for long-run batch entries so the newly reopened `AI Long-Run Batch Orchestration` lane becomes restart-safe and bounded without implying unattended execution, queue-home selection, `_stack` execution admission, Playbook doctrine admission, or owner-repo mutation.

This pass does not:

- admit a live queue, registry, supervisor, or worker dispatcher
- choose `runtime/`, `_stack`, Playbook, or any owner repo as the contract home
- admit unattended multi-lane batching, one giant root session, or cross-repo write widening
- reopen Fitness, `archive/`, `.vercel`, `.env`, secrets, deployment, publication, or `_stack Readiness` surfaces
- claim that contract freeze alone earns marker movement

## Root Health Baseline

- fresh operator authorization already reopened ATLAS root for bounded non-Fitness work
- the non-Fitness marker knockout selector from pass 52 already proved `AI Long-Run Batch Orchestration` is the first honest `admissible after current lane` candidate
- the baseline long-run doctrine already says the approved future direction is job-oriented supervision with bounded jobs, isolated worktrees, durable checkpoints, explicit verification gates, and human-readable lane or job manifests
- the current root validation surface is clean at `critical=0 error=0 warning=50 info=0`
- local `HEAD` is in parity with `origin/main` at `b651db3701143d8ff2bc0aa889e36b0fabaec0b2`

## Frozen Contract

### `family_name`

- `queue-or-registry batch entry contract`

### `trigger`

- one bounded long-run batch lane is now admitted at ATLAS root, but the operator still lacks one durable machine-readable batch-entry contract
- repeated manual reconstruction of owner repo, worktree, checkpoint, verification, and stop conditions across chats is already too lossy for safe batching
- implementation, `_stack` home admission, and supervised pilot design should not proceed until the batch-entry contract is exact first

### `stable_inputs`

- the baseline long-run doctrine in `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
- the automation-and-command ordering rule in `docs/atlas-book/09-automation-and-command-candidates.md`
- the current root path, protected-surface, and stop-condition truth in:
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- the current lane-selection and authorization basis in:
  - `docs/ops/ROOT-NON-FITNESS-MARKER-KNOCKOUT-CAMPAIGN-2026-06-09.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-SURFACE-PASS-52-2026-06-09.md`

### `expected_contract_artifact`

- one exact storage-agnostic batch-entry contract that can back either a future queue or a future registry without changing field meaning
- every admitted entry must name:
  - `entry_id`
  - `lane_name`
  - `job_scope`
  - `owner_repo`
  - `target_branch_or_worktree`
  - `allowed_write_scope`
  - `checkpoint_surface`
  - `verification_gate`
  - `closeout_artifact`
  - `park_or_escalation_rule`
  - `protected_surface_exclusions`
  - `status`
  - `created_from_receipt`
  - `last_reconciled_receipt`
- allowed status vocabulary is now exactly:
  - `proposed`
  - `admitted`
  - `execution-ready`
  - `running-supervised`
  - `parked`
  - `blocked`
  - `complete`
- optional fields may exist only when triggered:
  - `blocking_class`
  - `human_review_hold`
  - `notes`
- fail closed if an entry omits owner repo, target branch or worktree, allowed write scope, checkpoint surface, verification gate, closeout artifact, or park rule
- fail closed if one entry spans multiple owner repos, hidden write surfaces, or protected surfaces

### `failure_boundary`

- the contract allows a batch entry to exist without explicit owner repo, worktree, write scope, checkpoint, verification, closeout, or park truth
- queue wording starts implying unattended execution approval, merge approval, or publish approval by default
- one batch entry becomes a second truth store that overrides owner-repo verification, proof, or mutation authority
- the contract hides protected-surface exclusions or lets one entry blur root doctrine with owner-repo execution truth
- the contract chooses storage or execution semantics by implication rather than by a later explicit owner-surface pass

### `safe_fallback`

- keep long-run batching as doctrine plus receipts only
- allow only a docs-only field map or one partial proposed entry with explicit missing-field markers
- stop below owner-surface admission if the contract home is still ambiguous
- route back to manual lane receipts rather than inventing live queue or registry behavior

### `owner_boundary`

- ATLAS root owns the contract freeze, canonical field rules, restart projection, and non-claim boundaries
- `_stack` may later own execution-oriented orchestration semantics, worker flow, and supervisor behavior, but not from this pass
- Playbook may later own reusable verification or closeout doctrine, but not from this pass
- owner repos keep repo-local mutation truth, verification truth, and implementation truth

### `non_claim_boundary`

- no live supervisor claim
- no queue-home or registry-home claim
- no `_stack` execution-home claim
- no Playbook doctrine-admission claim
- no owner-repo implementation claim
- no unattended execution, deploy, publication, archive/delete, `.env`, secret, or Fitness claim

## Deferred Placement Decision

- the contract is now storage-agnostic on purpose
- `runtime/`, `_stack`, Playbook, and owner-repo placement remain separate later questions
- implementation talk stays blocked until one exact owner-facing home is admitted first

## Supporting Dependency Decision

- `none yet`

Why:

- this pass freezes the entry contract only
- the next honest question is where that contract truth should live and who may advance its state transitions
- support or implementation admission would be premature before that placement question is explicit

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry owner-surface admission pass 2`

Why:

- the batch-entry contract is now exact
- the next honest question is whether the first durable home belongs in ATLAS root control-plane surfaces, `_stack`, or another already-named surface
- implementation or pilot-design work would be premature before that owner-surface question is frozen

## Marker Decision

- `none`

Why:

- this pass freezes one exact batch-entry contract only
- it does not widen supervised adoption, admit an execution home, or land a repeatable pilot proof

## Rule

`Batch Entries Must Name Their Truth Boundary`

No long-run batch entry is honest unless it names owner repo, worktree, write scope, checkpoint, verification, closeout, and park truth before any supervisor or queue behavior is discussed.

## Pattern

`Storage-Agnostic Batch Entry Contract`

freeze one bounded entry contract first -> keep storage and execution-home placement deferred -> admit the owner-facing home separately -> only then discuss pilot or supervisor implementation

## Failure Mode

`Queue-As-Execution-Approval Drift`

This family becomes fake progress when a queue or registry entry starts acting like permission for unattended execution, hidden multi-repo writes, or owner-truth replacement instead of staying a bounded pre-execution contract.

## What This Pass Proves

This pass proves:

- `AI Long-Run Batch Orchestration` now has one exact queue-or-registry batch-entry contract
- that contract is restart-safe without choosing storage, execution home, or supervisor semantics
- the next honest question is owner-surface admission rather than implementation

This pass does not prove:

- that any queue or registry home is admitted
- that `_stack` now owns long-run orchestration execution
- that any supervised pilot, worker dispatch, or multi-lane batching is now approved
