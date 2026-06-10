# AI Long-Run Batch Orchestration Queue-Or-Registry Batch-Entry Validator First-Slice Admission Pass 5 - 2026-06-09

- Date: `2026-06-09`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-slice admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-2026-05-22.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-CONTRACT-FREEZE-PASS-1-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-OWNER-SURFACE-ADMISSION-PASS-2-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-SUPPORTING-LANE-ADMISSION-PASS-3-2026-06-09.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-FIRST-IMPLEMENTATION-SLICE-SELECTION-PASS-4-2026-06-09.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned `batch-entry validator`, plus one proof matrix for validating that slice without crossing the no-storage, no-entry-mutation, or no-supervisor boundary.

This pass does not:

- implement code
- choose queue or registry storage placement
- create live queue or registry entries
- admit `_stack` execution semantics
- admit supervisor behavior
- mutate runtime state, owner repos, Fitness, `archive/`, deploy/publication surfaces, `.env`, or secrets

## Inherited State

Pass 1 froze:

- required batch-entry fields
- bounded status vocabulary
- protected-surface exclusion expectations
- storage-agnostic contract meaning

Pass 2 froze:

- `ATLAS root control-plane surfaces` as the owner-facing home
- deferral of `_stack`, Playbook, owner-repo, and `runtime/` ownership

Pass 3 froze:

- no separate support lane honestly reopens yet
- the family remains root-local contract truth at this stage

Pass 4 selected:

- `batch-entry validator`
- as the smallest reusable implementation slice

This pass consumes those boundaries and freezes the narrowest first code slice plus the exact proof behavior expected from that slice.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. `one explicit candidate-entry input loader`
   - accept exactly one candidate batch-entry description
   - read only an explicitly provided local input path or inline object payload
   - do not discover entries from directories, registries, or runtime state

2. `one required-field enforcement layer`
   - require exactly:
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

3. `one bounded status and optional-field discipline layer`
   - allow only:
     - `proposed`
     - `admitted`
     - `execution-ready`
     - `running-supervised`
     - `parked`
     - `blocked`
     - `complete`
   - allow optional fields only when triggered:
     - `blocking_class`
     - `human_review_hold`
     - `notes`

4. `one single-owner and single-target boundary layer`
   - reject candidate entries that imply:
     - multiple owner repos
     - multiple target branches or worktrees
     - hidden cross-repo write scope

5. `one protected-surface exclusion and cited-receipt layer`
   - require explicit protected-surface exclusion reporting
   - fail closed when the candidate would touch:
     - Fitness
     - `archive/`
     - deploy/publication surfaces
     - `.env`
     - secrets
   - require the cited receipt refs to be present as fields
   - stop before any deeper receipt-story parsing or storage lookup

6. `one bounded result renderer`
   - emit only:
     - `valid`
     - `invalid-missing-field`
     - `invalid-status`
     - `invalid-optional-field`
     - `invalid-owner-boundary`
     - `invalid-target-boundary`
     - `invalid-protected-surface-exclusion`
     - `invalid-input`
   - include only missing, invalid, and blocked-field reporting needed to explain the fail-closed result

7. `one fail-closed unsupported-input handler`
   - reject unsupported modes, unsupported extra storage hints, or unsupported multi-entry payloads
   - do not silently coerce broader behavior into this slice

This first slice may:

- validate exactly one candidate entry
- classify only against the already-frozen contract rules
- return pass or fail plus bounded field-error reporting
- use only explicit local input

This first slice may not:

- create, mutate, or persist a queue or registry
- infer default owner repo, branch, worktree, checkpoint, or verification fields
- read live runtime state to find candidate entries
- dispatch work
- change entry status as a side effect
- widen into supervisor, prompt, or storage-path planning behavior

## Exact Deferred Later Slices

Deferred to later slices are:

- prompt-pack and worker handoff packaging
- richer fixture tooling beyond the minimum first-slice harness
- draft entry scaffold rendering
- entry status summary rendering
- storage-path planning or queue-home selection
- execution-ready transition semantics
- any `_stack` execution-home follow-on

Deferred does not mean admitted now.
Those slices require later bounded packets.

## Exact Forbidden First-Slice Elements

Forbidden from the first slice are:

- directory crawling for entries
- registry or queue mutation
- runtime storage placement
- multi-entry batch validation
- storage-path invention
- entry generation under draft language
- supervisor, dispatch, or resume behavior
- protected-surface bypass
- owner-boundary rewriting by convenience

## Exact Proof Matrix

### Valid single candidate entry

Expected behavior:

- emit the bounded `valid` result
- report no missing required fields
- report no protected-surface violations

### Missing required field

Expected behavior:

- fail closed to `invalid-missing-field`
- report the exact missing field set
- do not downgrade to warning-only behavior

### Invalid status value

Expected behavior:

- fail closed to `invalid-status`
- report the offending value
- do not coerce to the nearest admitted status

### Optional-field misuse

Expected behavior:

- fail closed to `invalid-optional-field`
- reject optional fields that appear without their triggering condition

### Multi-owner or hidden cross-repo scope

Expected behavior:

- fail closed to `invalid-owner-boundary`
- do not accept one entry that implies more than one owner repo or hidden write surface

### Multi-target branch or worktree implication

Expected behavior:

- fail closed to `invalid-target-boundary`
- do not accept one entry that blurs more than one target branch or worktree

### Protected-surface exclusion failure

Expected behavior:

- fail closed to `invalid-protected-surface-exclusion`
- reject entries that omit exclusion reporting or imply protected-surface writes

### Unsupported input mode

Expected behavior:

- fail closed to `invalid-input`
- reject multi-entry payloads, unsupported storage hints, or unsupported mode flags

### Optional-field discipline

Expected behavior:

- success payloads do not carry failure-only diagnostics
- failure payloads do not claim `valid`
- no unsupported storage or dispatch fields are silently accepted

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry batch-entry validator prompt-pack and handoff contract pass 6`

Why:

- the first slice and proof matrix are now explicit
- the next remaining docs-only ambiguity is how that exact slice is handed to a future implementation worker without widening into storage, supervisor, or execution semantics

## Marker Decision

- `none`

Why:

- this pass freezes the first-slice boundary and proof matrix only
- no implementation, proof of execution, or operator adoption landed yet

## Rule

Do not authorize validator implementation work until the slice accepts only one explicit candidate entry, fails closed on field and boundary violations, and stays fully outside queue state and supervisor semantics.

## Pattern

contract freeze -> owner admission -> support check -> first-slice selection -> first-slice admission and proof matrix -> prompt-pack -> implementation

## Failure Mode

Letting the first validator quietly become a queue reader, queue writer, or storage planner under the name of validation.
