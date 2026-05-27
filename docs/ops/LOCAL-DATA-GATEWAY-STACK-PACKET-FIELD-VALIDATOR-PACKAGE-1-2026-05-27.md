# Local Data Gateway `_stack` Packet Field Validator Package 1 - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway _stack packet field validator package 1`
- Mode: `smallest real implementation slice`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-2026-05-25.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-IMPLEMENTATION-PLAN-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PACKET-CONTRACT-DRAFT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PROOF-PACKET-EXEMPLARS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-CONTRACT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-DOCTRINE-CHECKPOINT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-FIRST-IMPLEMENTATION-SELECTION-2026-05-27.md`
- Control-plane checkpoint: `main@c91da43`

## Objective

Implement the smallest real Local Data Gateway helper slice:

- packet field validator only

This package does not:

- emit packets
- send packets downstream
- call models, APIs, or SaaS targets
- expand secrets
- scan arbitrary filesystem state beyond explicit input
- mutate Supabase, Vercel, Discord, runtime, schema, or app code
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `c91da43`
- status: clean except intentional untracked `archive/`

## Selected Implementation Path

The smallest existing `_stack` helper location that already fits current command layout is:

- `repos/_stack/scripts/`

Selected implementation files:

- `repos/_stack/scripts/data-gateway-packet-validator.mjs`
- `repos/_stack/scripts/data-gateway-packet-validator.test.mjs`

This path fits because:

- `_stack` already uses repo-local Node helper scripts in `scripts/`
- colocated `node:test` coverage already exists there
- adding the validator here avoids inventing a new top-level helper surface

## Helper Entry Shape

Current package-script wrapper:

- `pnpm --dir repos/_stack run data-gateway:packet:validate -- --input <packet.json>`

Current test entry:

- `pnpm --dir repos/_stack run data-gateway:packet:validate:test`

Current behavior:

- explicit JSON packet file input only
- local field validation only
- pass/fail JSON summary to stdout/stderr
- exit `0` on valid packet
- exit `1` on missing or malformed fields

## Contract Coverage Implemented

The validator now enforces the first required packet-structure boundary for:

- `packet_purpose`
- `packet_schema_version`
- `sensitivity_label`
- `source_provenance`
- `transformation_record`
- `validation_result`
- `redaction_status`
- `dedupe_status`
- `minimal_useful_payload`
- `downstream_target_class`

It also validates the later contract additions when present:

- `export_exclusion_summary`
- `receipt_or_proof_ref`

## Validation Semantics Implemented

### Required field checks

Fail closed when a required field is missing or empty.

### Enumerated value checks

Fail closed on malformed values for:

- `sensitivity_label`
- `downstream_target_class`
- `validation_result`
- `redaction_status`
- `dedupe_status`
- `source_provenance.source_type`

### Nested object checks

Fail closed when:

- `source_provenance` is malformed
- `transformation_record` is malformed
- required nested fields are missing

### Explicit-input-only boundary

The validator reads only the packet file path passed through `--input`.

It does not:

- scan directories
- infer remote sources
- construct packets
- emit artifacts

## Test Coverage Added

Added narrow proof for:

- valid packet passes
- missing required field fails
- malformed field value fails
- explicit packet file-path read succeeds

Executed:

- `pnpm --dir repos/_stack run data-gateway:packet:validate:test`

Result:

- `4` tests passed

## What Remains Deferred

Still intentionally deferred:

- dry-run packet emitter
- packet manifest/artifact generation
- lane proof packager
- full `stack data gateway packet <lane>` wrapper
- downstream send or sync behavior
- remote/model/API handoff

## Marker Recommendation

Keep `Local Data Gateway` at `10%` in this package.

Why:

- the first helper slice now exists
- but no emitted packet artifact proof exists yet
- no downstream-safe packet generation run has been proven
- the lane still needs the next implementation slice before another marker move is honest

## Exact Next Package

`Local Data Gateway dry-run packet emitter package 2`

Why:

- the validator is now the reusable contract gate
- the next smallest safe layer is preview-only packet shaping
- dry-run emit can stay local-only while proving field population and artifact-plan semantics without opening send behavior

## Validation

Executed:

- `pnpm --dir repos/_stack run data-gateway:packet:validate:test`
- `python .\ops\validation\validate_stack.py`

Result:

- validator tests passed
- `critical=0 error=0 warning=307`

## Rule

Packet field validator package 1 validates packet structure only; it must not send, transform broadly, or perform downstream execution.

## Failure Mode

Turning the first helper slice into a hidden packet emitter or remote transport surface.
