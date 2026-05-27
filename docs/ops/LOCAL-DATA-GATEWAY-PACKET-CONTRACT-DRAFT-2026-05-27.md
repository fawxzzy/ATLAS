# Local Data Gateway Packet Contract Draft - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway packet contract draft`
- Mode: `docs-only contract draft`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-2026-05-25.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-IMPLEMENTATION-PLAN-2026-05-27.md`
  - `docs/ops/CORE-PATTERN-CONVERGENCE-MATRIX-2026-05-24.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/10-failure-modes-and-recovery.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@d5fd386`

## Objective

Define the first reusable packet contract for `Local Data Gateway` so later helpers, receipts, and review flows share one concrete local-first boundary.

This pass does not:

- implement `_stack` helpers
- implement Playbook helpers
- export raw data
- mutate Supabase, Vercel, Discord, runtime, schema, or app code
- open any approval-gated lane
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `d5fd386`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## Contract Goal

Every packet emitted by the Local Data Gateway must:

- start from local source material
- preserve source ownership and provenance
- record the exact local reductions applied
- carry only the minimum useful payload for the downstream target
- remain replayable and auditable after handoff

## Required Packet Fields

Every packet must include:

- `packet_purpose`
- `packet_schema_version`
- `downstream_target_class`
- `sensitivity_label`
- `source_provenance`
- `transformation_record`
- `validation_result`
- `redaction_status`
- `dedupe_status`
- `minimal_useful_payload`

Recommended supporting fields:

- `packet_id`
- `owner_surface`
- `capture_timestamp`
- `operator_or_process`
- `payload_summary`
- `export_exclusion_summary`
- `handoff_constraints`
- `receipt_or_proof_ref`

## Contract Field Definitions

### `packet_purpose`

Why this packet exists.

Examples:

- `supabase-review`
- `boundary-handoff`
- `dependency-check`
- `model-prompt-input`
- `publication-draft-input`

### `packet_schema_version`

Explicit packet schema/version stamp.

First draft value:

- `ldg.packet.v1`

### `downstream_target_class`

What kind of consumer is allowed to receive the packet.

Examples:

- `human-review`
- `model`
- `api`
- `saas-tool`
- `remote-database`
- `automation-helper`
- `cross-repo-handoff`

### `sensitivity_label`

Sensitivity classification after local review.

Allowed values:

- `public`
- `internal`
- `sensitive`
- `restricted`

### `source_provenance`

Where the packet came from and what local evidence produced it.

Minimum fields:

- `owner_surface`
- `source_type`
- `source_refs`
- `captured_at`
- `capture_method`

### `transformation_record`

Local processing record applied before export.

Minimum fields:

- `normalized`
- `validated`
- `redacted`
- `sensitivity_classified`
- `deduped`
- `extracted`
- `notes`

### `validation_result`

Whether the packet passed the local contract checks.

Allowed values:

- `pass`
- `fail`

### `redaction_status`

Whether sensitive or noisy fields were removed, masked, or intentionally retained.

Allowed values:

- `not_needed`
- `applied`
- `required_but_missing`

### `dedupe_status`

Whether repeated content was collapsed before handoff.

Allowed values:

- `not_needed`
- `applied`
- `required_but_missing`

### `minimal_useful_payload`

The actual compact payload that the downstream target is allowed to receive.

Rule:

- this payload is the exported unit
- raw local input is never the exported unit by default

### `export_exclusion_summary`

Explicit summary of what intentionally stayed local or was omitted from the packet.

Why:

- real review and boundary workflows depend on proving not only what was sent, but what was intentionally not exported

### `receipt_or_proof_ref`

Link or identifier for the governing receipt, proof artifact, or approval packet that records packet use.

Why:

- real stack handoffs are only durable when the packet can be tied back to a receipt or proof chain

## Packet Lifecycle

Every Local Data Gateway packet follows this lifecycle:

1. `raw_capture`
   - local-only source landing
2. `local_normalize`
   - shape standardization and noise framing
3. `local_validate`
   - required field and ambiguity checks
4. `local_redact_classify`
   - sensitivity labeling and secret/noise removal
5. `local_dedupe_extract`
   - repeated-content collapse and useful-signal extraction
6. `packet_emit`
   - contract-compliant packet creation
7. `downstream_handoff`
   - bounded handoff to the allowed target class
8. `receipt_or_proof`
   - packet usage captured in a receipt, proof artifact, or governed log

## Required Invariants

### Local-first invariant

Raw data stays local-first.

Remote systems do not become the initial cleanup surface.

### Minimum-necessary invariant

The packet must be the minimum necessary payload for its declared purpose.

If a field does not help the next bounded step, it should not leave local control.

### No messy raw input by default

Downstream systems do not receive noisy raw source material by default.

Any exception requires an explicit reason and should still preserve provenance and sensitivity labeling.

### Replayability invariant

A packet must be reproducible from its recorded local source inputs and transformation record.

### Auditability invariant

A reviewer must be able to answer:

- where the packet came from
- what was removed
- what was retained
- why the downstream target received this payload

### Owner-boundary invariant

The packet does not rewrite ownership.

It packages data for handoff or review, but does not convert ATLAS root into the owner of repo-local runtime truth.

## First Generic Shape

```yaml
packet_id: ldg-2026-05-27-example
packet_purpose: supabase-review
packet_schema_version: ldg.packet.v1
downstream_target_class: human-review
sensitivity_label: sensitive
owner_surface: repos/fawxzzy-fitness
capture_timestamp: 2026-05-27T00:00:00Z
operator_or_process: codex
source_provenance:
  source_type: export
  source_refs: []
  captured_at: 2026-05-27T00:00:00Z
  capture_method: local-script
transformation_record:
  normalized: true
  validated: true
  redacted: true
  sensitivity_classified: true
  deduped: true
  extracted: true
  notes: []
validation_result: pass
redaction_status: applied
dedupe_status: applied
payload_summary:
  record_count: 0
  retained_fields: []
  dropped_fields: []
export_exclusion_summary:
  omitted_classes: []
  reason: minimum-necessary
handoff_constraints:
  remote_write_allowed: false
  onward_share_allowed: false
receipt_or_proof_ref: docs/ops/example.md
minimal_useful_payload: {}
```

## Reuse Targets

This contract is intentionally generic enough for:

- Supabase export/review packets
- Vercel helper/dependency-check packets
- DiscordOS boundary handoff packets
- AI/model prompt input packets
- publication-draft input packets

## What This Contract Is Not

It is not:

- a helper implementation
- a remote sync format
- a direct mutation format
- a permission to export raw data
- a substitute for receipt/proof after handoff

## Replay / Audit Posture

To be considered governed, a packet should be auditable after the fact through:

- source references
- schema/version
- transformation record
- validation result
- downstream target class
- export exclusion summary
- receipt or proof link

Recommended later helper behavior:

- emit a packet file
- emit a compact packet summary
- emit a receipt-ready metadata block

## Exact Next Package

`Local Data Gateway helper contract and `_stack` CLI shape draft`

Why:

- the packet contract is now specific enough to constrain helper design
- the next missing layer is the helper interface, not more doctrine
- helper planning can now target one shared packet shape instead of ad hoc lane-by-lane payloads

## Rule

A Local Data Gateway packet contract defines the reusable boundary, not the first helper implementation.

## Pattern

Local source -> packet lifecycle -> contract-compliant packet -> bounded downstream handoff -> receipt/proof

## Failure Mode

Turning the gateway into vague doctrine without a concrete packet shape that later helpers and receipts can actually follow.
