# Local Data Gateway `_stack` Helper Contract - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway _stack helper contract draft`
- Mode: `docs-only helper contract`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-PACKET-CONTRACT-DRAFT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PROOF-PACKET-EXEMPLARS-2026-05-27.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
  - `docs/PLAYBOOK_NOTES.md`
- Control-plane checkpoint: `main@be3879f`

## Objective

Define the first `_stack` helper candidate contract for Local Data Gateway so a later implementation can generate governed local-first packets without ambiguity about scope or safety.

This pass does not:

- implement `_stack` helper code
- send packets to any remote system
- export raw data
- mutate Supabase, Vercel, Discord, runtime, schema, or app code
- open any approval-gated lane
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `be3879f`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## Command Candidate

Primary helper candidate:

- `stack data gateway packet <lane>`

Examples of the intended command shape:

```text
stack data gateway packet supabase-review --source runtime/exports/... --mode preview
stack data gateway packet vercel-dependency-check --source runtime/captures/... --mode emit
stack data gateway packet discordos-boundary-handoff --source repos/DiscordOS/docs/ops/... --mode validate
```

The command name is stable enough for planning, but argument spelling may still change at implementation time.

## Helper Goal

The helper exists to:

- read local source material only
- apply the Local Data Gateway packet contract
- emit a reviewable packet artifact and summary
- stop before any downstream send
- make packet generation provable through receipts

It does not exist to:

- choose remote destinations
- send to SaaS, APIs, models, or databases
- hide export side effects behind a local command name

## Expected Inputs

The helper should accept:

- `lane`
  - bounded workflow class such as `supabase-review`, `dependency-check`, `boundary-handoff`, or `model-prompt-input`
- `source`
  - one or more local file paths or directories
- `owner-surface`
  - owning repo or lane identity
- `purpose`
  - packet purpose override when the lane needs a narrower purpose label
- `sensitivity`
  - explicit or inferred sensitivity class
- `schema-version`
  - defaults to the current packet contract version unless overridden
- `mode`
  - `preview`, `emit`, or `validate`
- `receipt-ref`
  - optional existing governing receipt or proof reference to attach

Inputs must remain local filesystem inputs or repo-local doc surfaces.

The helper must not accept:

- remote URLs as source-of-truth inputs by default
- secret values inline on the command line
- raw prompt text intended for direct model submission without packet review

## Local Source Location Rule

Local source data should live in normal governed local surfaces, for example:

- `runtime/exports/**`
- `runtime/captures/**`
- `runtime/receipts/**`
- `data/**` when durable fixtures are the source
- repo-local docs or receipts when the lane is boundary/proof oriented

The helper must treat these as input surfaces, not as proof that a remote handoff is approved.

## Artifact Output Rule

Generated packet artifacts should land under a governed local runtime path, not in repo roots or `tmp/`.

Recommended first artifact root:

- `runtime/gateway-packets/<lane>/<date>/`

Recommended first artifact set:

- `packet.json`
- `packet-summary.md`
- `packet-metadata.json`

Why:

- runtime state belongs in `runtime/`
- packet artifacts are generated local state until promoted by a receipt
- summary and metadata should be easy to reference from later receipts

## Output Shape

The helper must emit artifacts that conform to the Local Data Gateway packet contract:

- required packet fields from `LOCAL-DATA-GATEWAY-PACKET-CONTRACT-DRAFT-2026-05-27.md`
- explicit lifecycle stage completion
- explicit exclusion summary
- explicit receipt/proof reference when available

Minimum human-review outputs:

- compact packet summary
- retained versus omitted field summary
- sensitivity label
- downstream target class
- local artifact path

## Helper Modes

### `preview`

Goal:

- show what would be packetized without writing final packet artifacts

Allowed behavior:

- inspect local source paths
- infer packet shape
- report proposed output paths and field population

Forbidden behavior:

- no downstream send
- no final packet emit

### `emit`

Goal:

- write packet artifacts locally and stop there

Allowed behavior:

- generate `packet.json`
- generate packet summary and metadata
- populate exclusion and proof-reference fields

Forbidden behavior:

- no downstream send
- no mutation
- no publication

### `validate`

Goal:

- check whether an existing local packet or prospective source set satisfies the contract

Allowed behavior:

- schema/version check
- required field check
- lifecycle/invariant check

Forbidden behavior:

- no packet send
- no hidden artifact mutation beyond explicit validation output

### No downstream send

This is a hard boundary across all modes.

The first helper contract does not include any `send`, `sync`, `post`, `submit`, or `mutate` mode.

## Receipt / Proof Contract

Packet generation is not durable until it is recorded by a receipt or attached proof artifact.

The later implementation must make it easy for a receipt to capture:

- source location
- output location
- packet purpose
- schema/version
- sensitivity
- exclusion summary
- downstream target class
- validation outcome

Recommended later receipt linkage:

- packet summary path
- packet metadata path
- optional pre-existing governing receipt reference

## Hard Non-Goals

The helper must never:

- send to live SaaS or API targets
- send directly to a model
- emit a prompt directly into an AI call without review
- expand or print secret-bearing source values
- treat remote state as the first cleanup surface
- bypass owner-lane approval gates
- mutate Supabase, Vercel, Discord, or repo code

## What The Helper Must Never Imply

The existence of this helper does not imply:

- remote export is approved
- packet consumers are trusted by default
- owner boundaries are relaxed
- proof can be skipped because a packet exists

The helper creates bounded local artifacts only.

## First Implementation Boundary

If this helper is implemented later, the first implementation should stay within:

- local file reads
- local packet construction
- local validation
- local artifact writes
- receipt-ready summary generation

Anything beyond that belongs to a later, separately approved lane.

## Exact Next Package

`Local Data Gateway _stack helper implementation planning packet`

Why:

- the command boundary is now explicit enough to support implementation design
- the next missing layer is the concrete implementation packet, not more contract doctrine
- implementation can now be scoped to local reads, local emits, and no-send guarantees

## Rule

A helper contract defines the safe command boundary before any helper code exists.

## Pattern

Packet contract -> helper contract -> implementation planning packet -> local-only helper implementation -> first governed proof run

## Failure Mode

Jumping from packet doctrine to helper implementation without freezing what the helper is and is not allowed to emit.
