# Local Data Gateway Wrapper Implementation Planning Checkpoint - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway wrapper implementation planning checkpoint`
- Mode: `docs-only wrapper implementation planning`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-WRAPPER-COMMAND-CONTRACT-DRAFT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WRAPPER-BEHAVIOR-MATRIX-RECEIPT-OUTPUT-DRAFT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-FULL-WRAPPER-PLANNING-CHECKPOINT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-CONTRACT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-BOUNDARY-CHECKPOINT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-AUTHORIZATION-PREREQUISITES-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-4-2026-05-27.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@feda211`

## Objective

Freeze the first actual implementation plan for the future `stack data gateway packet <lane>` wrapper without implementing wrapper code and without widening the Local Data Gateway lane beyond its current local-first, no-send boundary.

This pass does not:

- add `_stack` wrapper code
- add helper modes
- open transport or send behavior
- authorize downstream execution
- imply that review or proof packaging is transport permission
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `feda211`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Current Proven Local Helper Chain

The wrapper plan sits on top of an already durable local-only helper family:

1. packet validation
2. dry-run local packet emission
3. local review / approval recording
4. local proof packaging
5. explicit send-boundary prohibition
6. explicit send-authorization prerequisite freeze

That means wrapper planning is now about orchestration shape only, not about inventing new packet semantics.

## First Actual Wrapper Slice

The first implementation slice should be:

- one thin no-send wrapper surface over the existing validator and dry-run emitter only

Admitted package-1 modes:

- `validate-only`
- `emit-dry-run`

Deferred from package 1:

- `review-only`
- `proof-only`
- `full-local-chain`

Why this is the smallest honest slice:

- `validate-only` alone is too small to prove real orchestration value
- `emit-dry-run` alone still depends on validation, so package 1 can prove stage chaining without opening review or proof complexity
- review and proof already exist as proven primitives, but they add reviewer/disposition semantics that do not need to land in the first wrapper cut
- `full-local-chain` would be too much surface for the first wrapper package because it would combine all stages before the thin-orchestrator boundary has been proven

## Exact Package-1 Command Shape

Recommended package-1 command surface:

- `stack data gateway packet <lane> --mode <validate-only|emit-dry-run> --source <local-path>`

Required package-1 arguments:

- `<lane>`
- `--mode <validate-only|emit-dry-run>`
- `--source <local-path>`

Allowed optional package-1 arguments:

- `--owner-surface <label>`
- `--purpose <text>`
- `--sensitivity <label>`
- `--schema-version <value>`
- `--receipt-ref <ref>`
- `--artifact-root <path>`
- `--note <text>`

Package-1 arguments explicitly not admitted:

- `--artifact-dir`
- `--reviewer`
- `--disposition`
- endpoint selectors
- remote target ids
- auth token inputs
- model/provider selectors

## Exact Package-1 Artifact Expectations

### `validate-only`

Expected behavior:

- delegate to the existing validator helper
- produce receipt-ready summary output only
- stop before any filesystem artifact write

Success expectation:

- wrapper reports validation success with explicit no-send attestation

Failure expectation:

- wrapper exits failed
- no packet artifact directory is created

### `emit-dry-run`

Expected behavior:

- delegate to the existing validator helper first
- only if validation passes, delegate to the dry-run emitter helper
- write to the canonical artifact root only:
  - `runtime/gateway-packets/<lane>/<date>/<packet-id>/`

Expected emitted artifact set:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`

Success expectation:

- wrapper reports validation success
- wrapper reports emitted artifact refs
- wrapper reports explicit no-send and no-execution state

Failure expectation:

- wrapper exits failed on any validator or emitter failure
- no review or proof stage is attempted
- if bounded partial local artifact residue remains, it must be reported as failed-stage local residue rather than successful output

## Exact Package-1 Failure Semantics

The wrapper must fail closed.

Required package-1 failure rules:

- missing or unreadable `--source` fails the invocation
- malformed packet input fails the invocation
- validation failure blocks emit
- canonical artifact-root resolution failure blocks emit
- emit write failure blocks successful completion
- no stage may downgrade a failed helper exit into a wrapper success
- no failure path may imply that later review, proof, or send work is authorized

Required package-1 exit posture:

- `validate-only` returns success only on a validator pass
- `emit-dry-run` returns success only when the canonical packet artifact trio exists
- wrapper failure must identify the failing stage:
  - `validate`
  - `emit`

## Receipt / Summary Output Plan

Package 1 should not add a second wrapper-specific artifact tree.

Instead it should emit receipt-ready summary output that later ATLAS receipts can cite.

Required summary fields for package 1:

- lane
- mode
- source path
- packet id when available
- canonical artifact directory when available
- validation state
- emitted artifact refs when present
- explicit no-send attestation:
  - `downstream_send_performed: false`
  - `downstream_execution_performed: false`
  - `remote_target_selected: false`
  - `automatic_handoff_authorized: false`
- failure stage and blocking reason when unsuccessful

## Implementation Sequencing

### What lands first

Package 1 should land only:

- thin wrapper argument parsing for `<lane>`, `--mode`, and `--source`
- delegation to the existing validator helper
- delegation to the existing dry-run emitter helper
- canonical receipt-ready summary output
- fail-closed stage handling

### What stays deferred

Deferred after package 1:

- `review-only`
- `proof-only`
- `full-local-chain`
- wrapper-managed reviewer/disposition handling
- wrapper receipt promotion into ATLAS
- any target selection, transport, or send-capable mode
- any lane-specific branching or source discovery beyond explicit local input

### What proof is required before any marker move

No marker move is justified by planning alone.

Before the wrapper can justify another Local Data Gateway ratchet, package 1 must be:

- implemented on the existing helper surface
- covered by package-1 tests for:
  - `validate-only` success
  - `validate-only` failure
  - `emit-dry-run` success
  - `emit-dry-run` blocked by validation failure
  - explicit rejection of send-capable or transport-shaped arguments
- proven on real local workflow classes at the wrapper layer, not only at the primitive-helper layer
- validated as still local-only and no-send

## What The Wrapper Must Not Do

Package 1 must never:

- choose a target system
- expand secrets
- infer business logic from `<lane>`
- open transport assumptions
- infer approval from packet validity
- run review or proof implicitly
- authorize downstream execution

This remains a thin orchestration slice, not a platform engine.

## Exact Next Package

`Local Data Gateway wrapper implementation package 1`

Scope recommendation for that package:

- implement only `validate-only`
- implement only `emit-dry-run`
- prove fail-closed local summary behavior
- stop before review/proof wrapper modes

## Marker Recommendation

- no marker move in this pass
- `Local Data Gateway` remains `40%`

Why:

- this pass freezes implementation shape only
- no new helper or wrapper proof landed here
- the next marker move, if any, belongs after wrapper package 1 implementation plus wrapper-layer proof

## Rule

Wrapper implementation planning must select the smallest safe wrapper slice, not a generic orchestration engine.

## Pattern

wrapper contract -> behavior matrix -> implementation planning -> package-1 thin no-send orchestration -> wrapper-layer proof

## Failure Mode

Planning a wrapper that quietly becomes platform-engine work instead of thin no-send orchestration.
