# Local Data Gateway Wrapper Command Contract Draft - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway wrapper command contract draft`
- Mode: `docs-only wrapper contract`
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
  - `docs/ops/LOCAL-DATA-GATEWAY-FULL-WRAPPER-PLANNING-CHECKPOINT-2026-05-27.md`

## Objective

Freeze the future command contract for `stack data gateway packet <lane>` without implementing wrapper code and without widening the Local Data Gateway lane beyond its current local-first, no-send posture.

This pass does not:

- implement a wrapper
- add helper modes
- open transport or send behavior
- authorize downstream execution
- change helper code in `_stack`
- mutate `archive/`

## Root State

- branch: `main`
- status: clean except intentional untracked `archive/`
- validation: green before contract drafting

## Durable Local-Only Chain Confirmed

The wrapper contract sits on top of an already durable local-only chain:

1. packet validation
2. dry-run local packet emission
3. local review / approval recording
4. local proof packaging
5. explicit send-boundary prohibition
6. explicit send-authorization prerequisites freeze

Each stage is already:

- locally implemented
- proven on real workflow classes
- constrained below any transport or send boundary

## Wrapper Command Recommendation

Recommend:

- one future thin orchestrating no-send command

Command candidate:

- `stack data gateway packet <lane>`

Why this is the right recommendation:

- the helper family already exists and is proven
- operators need one stable contract for the full local-only chain
- a thin wrapper can standardize arguments, mode semantics, artifact paths, and receipt-ready output
- leaving orchestration purely informal would keep too much operator ceremony after the helper chain is already stable

Why this is still safe:

- the wrapper remains below the send boundary
- the wrapper delegates to existing bounded helpers
- the wrapper does not gain lane-specific workflow authority
- the wrapper does not treat review or proof as transport permission

## Planned Command Shape

Base form:

- `stack data gateway packet <lane> --mode <mode> --source <local-path>`

Planned explicit arguments:

- positional:
  - `<lane>`
- required flags:
  - `--mode <validate-only|emit-only|review-only|proof-only|full-local>`
  - `--source <local-file-or-directory>`
- conditionally required flags:
  - `--artifact-dir <path>`
  - `--reviewer <label>`
  - `--disposition <approved|rejected|needs-revision|no-decision>`
- optional flags:
  - `--owner-surface <label>`
  - `--purpose <text>`
  - `--sensitivity <label>`
  - `--schema-version <value>`
  - `--receipt-ref <ref>`
  - `--artifact-root <path>`
  - `--note <text>`

Argument rules:

- `--source` must stay local-only
- `--artifact-dir` must point to an existing local emitted packet directory when review or proof modes are used
- `--reviewer` and `--disposition` are mandatory for review-capable flows
- no argument may identify a remote endpoint, model target, queue, webhook, or SaaS destination

## Mode Matrix

### `validate-only`

- input:
  - explicit packet source
- behavior:
  - run validator only
- output:
  - validation result only
- stop condition:
  - no artifact write

### `emit-only`

- input:
  - explicit packet source
- behavior:
  - validate, then dry-run emit
- output:
  - packet artifact set under the gateway artifact root
- stop condition:
  - no review, no proof package

### `review-only`

- input:
  - existing emitted packet artifact directory
  - explicit reviewer/disposition
- behavior:
  - re-check packet presence, then record local review
- output:
  - review artifacts only
- stop condition:
  - no proof package, no send

### `proof-only`

- input:
  - existing reviewed packet artifact directory
- behavior:
  - verify review artifacts, then package proof
- output:
  - local proof bundle only
- stop condition:
  - no handoff, no send

### `full-local`

- input:
  - explicit packet source
  - explicit reviewer/disposition
- behavior:
  - validate
  - emit dry-run packet
  - record local review
  - package local proof
- output:
  - full local artifact set plus receipt-ready summary output
- stop condition:
  - stop before any transport or downstream execution

## Artifact Landing Paths

The wrapper must preserve the existing canonical artifact root:

- `runtime/gateway-packets/<lane>/<date>/<packet-id>/`

Expected artifact set after `full-local`:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`
- `packet-review.md`
- `packet-review-metadata.json`
- `proof-summary.md`
- `proof-metadata.json`

The wrapper must not:

- create a second parallel artifact tree
- spread artifacts across hidden temp locations
- write to repo-local runtime state outside the canonical gateway root

## Invariant Checks

The wrapper contract must enforce:

- emit cannot succeed if validation fails
- review cannot succeed if emitted packet artifacts are missing
- proof packaging cannot succeed if review artifacts are missing
- `full-local` cannot skip review
- no mode may downgrade a failed stage into a silent success
- no mode may mark transport as authorized

Required preserved invariants:

- raw data stays local-first
- minimum useful payload remains the packet boundary
- downstream systems do not receive raw input by default
- packet lifecycle remains replayable and auditable

## Receipt / Proof Outputs

The wrapper should produce receipt-ready local output, but should not write ATLAS receipts itself.

Expected receipt-ready summary content:

- lane
- mode
- source path
- artifact directory
- packet id
- validation result
- review disposition when present
- proof bundle paths when present
- explicit no-send and no-execution state

Receipt ownership remains separate:

- helper chain writes local artifacts
- operator or later receipt tooling promotes durable ATLAS receipts

## Operator Review Placement

Operator review remains a real checkpoint inside the wrapper contract.

The wrapper must not:

- auto-fill `approved`
- treat review as optional in `full-local`
- infer approval from lane type, owner surface, or packet class

Operator review belongs:

- after dry-run emit
- before proof packaging is considered complete

That preserves the current safe chain:

- structure gate
- local artifact generation
- explicit human-visible review
- local proof packaging

## What The Wrapper Must Not Do

The wrapper must never:

- send data to a remote target
- select a model, API, SaaS, queue, webhook, database, or endpoint
- hide export behavior behind a local-only command name
- perform automatic downstream execution
- expand secrets
- infer lane-specific business logic from `<lane>`
- treat proof existence as send authorization

Forbidden command-surface classes:

- `send`
- `sync`
- `post`
- `submit`
- `mutate`

Forbidden argument classes:

- endpoint selectors
- remote target ids
- auth token inputs
- model/provider selectors
- hidden transport toggles

## What Remains Explicitly Separate

The wrapper remains separate from:

- any send-capable lane
- any transport-aware handoff surface
- any owner-repo mutation flow
- any lane-specific workflow automation
- any source discovery beyond explicit local input
- any rollback/fail-closed send package

Those surfaces remain separate because they require:

- higher-level authorization
- explicit target typing
- sensitivity constraints
- rollback and fail-closed posture
- audit and receipt obligations beyond the local helper chain

## Recommendation On Orchestration

Recommendation:

- the wrapper should orchestrate the existing helper family

but only as:

- a thin no-send command contract

It should not remain documentation-only orchestration forever because:

- the helper primitives are already proven
- one explicit contract surface will reduce operator ambiguity
- the orchestration boundary can stay reusable without widening into transport

It must still preserve the split primitive layer because:

- validator, emitter, review, and proof-packager need to remain independently callable
- later send-capable work, if ever opened, must not be able to hide inside the local wrapper

## Exact Next Package

`Local Data Gateway wrapper behavior matrix and receipt-output draft`

Why:

- the command shape is now frozen
- the next smallest safe layer is to detail behavior by mode, failure exit, and summary-output semantics
- that still stays docs-only and below any send-capable lane

## Rule

Wrapper command contract work must stay local-first and no-send.

## Pattern

explicit local input -> validate -> emit dry-run -> local review -> proof package -> receipt-ready local summary

## Failure Mode

Turning the wrapper concept into implicit orchestration that already assumes downstream transport or lane-specific execution.
