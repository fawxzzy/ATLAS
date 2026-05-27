# Local Data Gateway Wrapper Behavior Matrix And Receipt-Output Draft - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway wrapper behavior matrix and receipt-output draft`
- Mode: `docs-only wrapper behavior freeze`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-WRAPPER-COMMAND-CONTRACT-DRAFT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-FULL-WRAPPER-PLANNING-CHECKPOINT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-CONTRACT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-BOUNDARY-CHECKPOINT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-AUTHORIZATION-PREREQUISITES-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-4-2026-05-27.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@7a6e0e6`

## Objective

Freeze the exact wrapper behavior matrix and receipt-output shape for the future `stack data gateway packet <lane>` surface without implementing wrapper code and without opening any transport boundary.

This pass does not:

- implement helper or wrapper code
- add a send-capable mode
- infer a remote target from `<lane>`
- authorize downstream execution
- expand secrets
- widen the wrapper into lane-specific business logic
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `7a6e0e6`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed before drafting:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Current Proven Local Chain

The wrapper matrix is constrained to the already durable local-only chain:

1. validate packet structure
2. emit dry-run local packet artifacts
3. record explicit local review disposition
4. package local proof artifacts
5. stop below the send boundary

Each stage remains:

- explicit-input only
- local-artifact only
- no-send by contract
- no-execution by contract

## Wrapper Modes Frozen

The future wrapper contract stays bounded to these modes only:

- `validate-only`
- `emit-dry-run`
- `review-only`
- `proof-only`
- `full-local-chain`

No other mode names are admitted here.

Modes not admitted:

- `send`
- `sync`
- `submit`
- `post`
- `mutate`
- `handoff`
- `transport`

## Behavior Matrix

### `validate-only`

Required inputs:

- `<lane>`
- explicit local packet source
- schema/version value when not already embedded

Prerequisite artifacts:

- none

Artifacts produced:

- none required on disk
- validation may emit console or receipt-ready summary only

Receipt/proof outputs:

- invocation summary
- source path
- packet identifier when derivable
- validation state
- explicit no-send attestation

Failure conditions:

- missing source
- unreadable local source
- malformed packet shape
- required contract field missing
- invalid field value or enum

Forbidden behavior:

- no artifact emit
- no review record
- no proof package
- no remote target selection

### `emit-dry-run`

Required inputs:

- `<lane>`
- explicit local packet source

Prerequisite artifacts:

- source must validate in the current invocation

Artifacts produced:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`

Receipt/proof outputs:

- invocation summary
- artifact directory
- packet id
- validation state
- emitted artifact refs
- explicit no-send attestation

Failure conditions:

- any validation failure
- artifact root creation failure
- packet metadata write failure
- missing canonical artifact path components

Forbidden behavior:

- no review record
- no proof bundle
- no target or endpoint argument
- no hidden export

### `review-only`

Required inputs:

- `<lane>`
- explicit `--artifact-dir`
- explicit `--reviewer`
- explicit `--disposition <approved|rejected|needs-revision|no-decision>`

Prerequisite artifacts:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`

Artifacts produced:

- `packet-review.md`
- `packet-review-metadata.json`

Receipt/proof outputs:

- invocation summary
- artifact directory
- review state
- review artifact refs
- validation snapshot from existing artifacts
- explicit no-send attestation

Failure conditions:

- missing emitted packet directory
- unreadable packet artifact
- missing reviewer
- unsupported disposition
- packet revalidation failure

Forbidden behavior:

- no proof package
- no implicit approval
- no automatic downstream handoff
- no treating `approved` as transport permission

### `proof-only`

Required inputs:

- `<lane>`
- explicit `--artifact-dir`

Prerequisite artifacts:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`
- `packet-review.md`
- `packet-review-metadata.json`

Artifacts produced:

- `proof-summary.md`
- `proof-metadata.json`

Receipt/proof outputs:

- invocation summary
- artifact directory
- validation snapshot
- review snapshot
- proof state
- proof artifact refs
- explicit no-send attestation

Failure conditions:

- missing review artifacts
- unreadable review metadata
- invalid or absent disposition snapshot
- proof metadata write failure

Forbidden behavior:

- no new review disposition inference
- no transport authorization field
- no downstream execution marker

### `full-local-chain`

Required inputs:

- `<lane>`
- explicit local packet source
- explicit `--reviewer`
- explicit `--disposition <approved|rejected|needs-revision|no-decision>`

Prerequisite artifacts:

- none before invocation

Artifacts produced:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`
- `packet-review.md`
- `packet-review-metadata.json`
- `proof-summary.md`
- `proof-metadata.json`

Receipt/proof outputs:

- invocation summary
- artifact directory
- packet id
- validation state
- review state
- proof state
- artifact refs for all generated outputs
- explicit no-send attestation

Failure conditions:

- any failure from validation
- any failure from emit
- missing explicit reviewer/disposition
- any failure from review
- any failure from proof packaging

Forbidden behavior:

- no stage skipping
- no implicit review
- no automatic send after proof
- no lane-derived business logic beyond artifact placement

## Stage Orchestration Rules

The wrapper may orchestrate only these stage edges:

1. `validate-only`
   - validator only
2. `emit-dry-run`
   - validator -> dry-run emitter
3. `review-only`
   - emitted packet -> local review
4. `proof-only`
   - reviewed packet -> proof package
5. `full-local-chain`
   - validator -> dry-run emitter -> local review -> proof package

Stage rules:

- emit never runs before validation succeeds
- review never runs without canonical emitted packet artifacts
- proof packaging never runs without canonical review artifacts
- `full-local-chain` never bypasses review
- failure in any stage halts the wrapper with no implied downstream continuation

## Canonical Artifact Root

The wrapper must preserve the existing artifact root:

- `runtime/gateway-packets/<lane>/<date>/<packet-id>/`

The wrapper must not:

- create a parallel runtime tree
- place packet artifacts in `tmp/`
- scatter receipt inputs across multiple hidden directories

## Receipt-Output Contract

Each wrapper invocation should emit a receipt-ready local summary shape even when the operator later promotes the result into an ATLAS receipt.

Required summary sections:

### Invocation Summary

- lane
- mode
- source path or artifact directory
- wrapper start timestamp
- wrapper end timestamp
- packet id when available

### Artifact Refs

- canonical artifact directory
- packet artifact refs when present
- review artifact refs when present
- proof artifact refs when present

### Validation State

- `not-run` or `passed` or `failed`
- failing field list when failed
- schema/version evaluated

### Review State

- `not-run` or `approved` or `rejected` or `needs-revision` or `no-decision`
- reviewer label when present
- review timestamp when present

### Proof State

- `not-run` or `packaged` or `failed`
- proof artifact refs when present

### No-Send Attestation

- `downstream_send_performed: false`
- `downstream_execution_performed: false`
- `remote_target_selected: false`
- `automatic_handoff_authorized: false`

### Failure Summary

- `success: true|false`
- failing stage when false
- blocking reason
- artifact state at failure boundary

## No-Send Invariants By Mode

Across all wrapper modes:

- no remote send occurs
- no transport target is selected
- no downstream execution is authorized
- no secret expansion occurs
- no endpoint or auth input is accepted

Mode-specific no-send preservation:

- `validate-only`
  - cannot emit or export
- `emit-dry-run`
  - can write local packet artifacts only
- `review-only`
  - can record disposition only
- `proof-only`
  - can package proof only
- `full-local-chain`
  - can complete the full local sequence only

## What Remains Separate

The wrapper behavior draft does not admit:

- send-capable wrapper extensions
- target selection flags
- owner-repo mutation behavior
- transport-aware retries
- lane-specific workflow branching
- receipt promotion into ATLAS as an automatic side effect

Those remain separate because they require a different authorization class than this local wrapper surface.

## Exact Next Package

`Local Data Gateway wrapper implementation planning checkpoint`

Why:

- the wrapper command contract is now frozen
- the mode behavior and receipt-output shape are now frozen
- the next smallest safe layer is an implementation-planning pass that maps these docs surfaces onto the existing helper family without adding send behavior

## Rule

Wrapper behavior matrix work must stay local-first and no-send.

## Pattern

explicit local input -> validate -> emit dry-run -> local review -> proof package -> receipt-ready local summary

## Failure Mode

A wrapper mode matrix quietly smuggles in implicit execution or target-selection semantics.
