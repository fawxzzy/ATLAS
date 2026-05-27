# Local Data Gateway Full Wrapper Planning Checkpoint - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway full wrapper planning checkpoint`
- Mode: `docs-only wrapper planning`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-CONTRACT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-PACKET-FIELD-VALIDATOR-PACKAGE-1-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-VALIDATOR-PROOF-PASS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-DRY-RUN-PACKET-EMITTER-PACKAGE-2-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-DRY-RUN-EMITTER-PROOF-PASS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PACKET-REVIEW-APPROVAL-SURFACE-PACKAGE-3-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REVIEW-SURFACE-PROOF-PASS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PROOF-PACKAGER-PACKAGE-4-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PROOF-PACKAGER-PROOF-PASS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-BOUNDARY-CHECKPOINT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-AUTHORIZATION-PREREQUISITES-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-4-2026-05-27.md`
- Control-plane checkpoint: `main@03c6e16`

## Objective

Freeze the shape of the future `stack data gateway packet <lane>` wrapper without implementing it and without widening beyond the current local-first, no-send boundary.

This pass does not:

- implement wrapper code
- add helper modes
- open transport behavior
- authorize downstream execution
- imply that a wrapper is a send surface
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `03c6e16`
- status: clean except intentional untracked `archive/`

## Durable Local-Only Chain Confirmed

The current Local Data Gateway chain is now durable through:

1. packet validation
2. dry-run local packet emission
3. local review / approval recording
4. local proof packaging
5. explicit send-boundary prohibition
6. explicit send-authorization prerequisites freeze

Each stage is both:

- implemented locally
- proven on real workflow classes

The wrapper therefore plans over a real helper family rather than over speculative future pieces.

## Wrapper Recommendation

Recommend:

- a single orchestrating no-send command

with one strict condition:

- it must remain a thin orchestrator over the existing split helper family rather than becoming a new smart workflow runner

Why this is the better choice:

- the current helper family is already proven and reusable
- operators now need one stable command surface for the full local-only chain
- a thin orchestrator can standardize artifact paths, stage ordering, and receipt linkage without duplicating business logic
- keeping only documented manual orchestration would preserve too much operator ceremony after the helper chain is already stable

Why this is still safe:

- the wrapper stays no-send only
- the wrapper delegates to the already-bounded helper stages
- the wrapper does not get to invent lane-specific logic
- the wrapper does not get to collapse review/proof into transport authority

## Planned Wrapper Boundary

The future wrapper is a local orchestration boundary only.

It exists to:

- accept explicit local source input
- chain the existing local-only helper stages in a governed order
- stop before any downstream send
- produce local artifacts plus receipt-ready summary output

It does not exist to:

- choose or contact remote targets
- infer business logic from lane names
- bypass review checkpoints
- authorize send, transport, sync, post, submit, or mutate behavior

## Planned Wrapper Inputs

The wrapper should accept only explicit, local-first inputs:

- `lane`
- `source`
- `owner-surface`
- `purpose`
- `sensitivity`
- `schema-version`
- `receipt-ref`
- `artifact-root`
- `reviewer`
- `disposition`
- `note`
- `mode`

Input rules:

- `source` must remain a local file or local directory path
- `lane` must remain a bounded classification label, not a business-logic switch
- review inputs must remain explicit; no default `approved`
- proof packaging must require reviewed local artifacts

The wrapper must not accept:

- remote URLs as source-of-truth input
- inline secret values
- direct model prompt text for immediate submission
- any target or endpoint selection argument

## Planned Wrapper Modes

Recommended wrapper modes:

- `validate-only`
- `emit-only`
- `review-only`
- `proof-only`
- `full-local`

Mode meanings:

### `validate-only`

- run the validator only
- stop before any artifact write

### `emit-only`

- require explicit packet input
- run validator then dry-run emit
- stop before review

### `review-only`

- require explicit emitted artifact directory
- run review only
- stop before proof packaging

### `proof-only`

- require explicit reviewed artifact directory
- run proof packager only

### `full-local`

- orchestrate:
  - validate
  - emit dry-run
  - local review
  - proof package
- stop there

No mode may include:

- `send`
- `sync`
- `post`
- `submit`
- `mutate`

## Planned Artifact Paths

The wrapper should preserve the existing artifact root:

- `runtime/gateway-packets/<lane>/<date>/<packet-id>/`

Expected local artifact set at full-local completion:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`
- `packet-review.md`
- `packet-review-metadata.json`
- `proof-summary.md`
- `proof-metadata.json`

The wrapper should not create a second parallel artifact tree.

## Planned Stage Chaining

The wrapper should chain the existing helpers in this order only:

1. validate packet structure
2. emit dry-run local packet artifacts
3. record explicit local review disposition
4. package local proof bundle

Required stage invariants:

- emit cannot run if validation fails
- review cannot run if emitted artifacts are missing
- proof packaging cannot run if review artifacts are missing
- all stages must preserve no-send and no-execution state

## Operator Review Placement

Operator review remains a real checkpoint inside the wrapper flow.

The wrapper must not:

- skip review in `full-local` mode
- auto-fill `approved`
- treat `reviewer` as optional when running review

Operator review belongs:

- after dry-run emit
- before proof package is treated as complete

That preserves the current chain:

- structure gate
- artifact generation
- human-visible review
- proof packaging

## Receipt Production Shape

The wrapper should make receipt production easier, but should not itself write ATLAS receipts.

The wrapper should emit receipt-ready local summaries that capture:

- source location
- lane
- mode
- artifact directory
- packet id
- review disposition when present
- proof artifact paths when present
- explicit no-send/no-execution state

Receipt ownership remains separate:

- helper writes local artifacts
- operator or later receipt tooling promotes durable ATLAS receipts

## What Remains Explicitly Separate From The Wrapper

The wrapper must remain separate from:

- any send-capable lane
- any transport selection
- any remote target selection
- any model/API/SaaS handoff
- any queue or webhook publication
- any lane-specific business logic
- any source discovery beyond explicit local input
- any owner-repo mutation behavior

Those remain separate because:

- they require higher-level authorization
- they require rollback/fail-closed posture
- they require audit obligations beyond the local helper chain

## Wrapper Non-Goals

The future wrapper must never:

- send data anywhere
- hide export side effects behind a local command name
- expand secrets
- auto-derive approval from lane type
- encode lane-specific workflow semantics
- assume transport just because proof exists

## Safe-Orchestration Rule

The wrapper should be implemented later only as:

- a thin orchestrator over the current helper family

not as:

- a new all-knowing packet engine

Implementation consequence:

- validator, emitter, review, and proof-packager stay as separable primitives
- the wrapper coordinates them
- the wrapper does not replace their boundaries

## Exact Next Package

`Local Data Gateway wrapper command contract draft`

Why:

- the wrapper shape is now frozen at the planning level
- the next smallest safe layer is a command-contract draft for arguments, mode semantics, and output summary shape
- that can still stay docs-only and no-send

## Rule

Wrapper planning must stay local-first and no-send.

## Pattern

explicit local input -> validate -> emit dry-run -> local review -> proof package -> receipt-ready summary

## Failure Mode

Turning the wrapper concept into implicit orchestration that already assumes downstream transport or lane-specific execution.
