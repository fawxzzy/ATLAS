# Local Data Gateway `_stack` Helper Implementation Planning - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway _stack helper implementation planning packet`
- Mode: `docs-only implementation planning`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-2026-05-25.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-IMPLEMENTATION-PLAN-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PACKET-CONTRACT-DRAFT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PROOF-PACKET-EXEMPLARS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-CONTRACT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-DOCTRINE-CHECKPOINT-2026-05-27.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@f433197`

## Objective

Freeze the first `_stack` helper implementation slice for Local Data Gateway without widening into a broad gateway system or any downstream send behavior.

This pass does not:

- implement `_stack` helper code
- emit final packet artifacts
- send any packet downstream
- expand secrets
- mutate Supabase, Vercel, Discord, runtime, schema, or app code
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `f433197`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## Command Candidate Still Frozen

The helper command candidate remains:

- `stack data gateway packet <lane>`

The planning question in this pass is not whether the command exists, but what the first safe implementation slice inside that command should be.

## Selected First Target Class

Pick exactly one smallest safe target:

- `local packet manifest generator`

This is smaller and safer than:

- `packet validator only`
  - too narrow to prove source discovery, field population, landing paths, and receipt/proof linkage
- `dry-run packet emitter only`
  - too close to final artifact emission before the manifest/planning layer is proven

Why `local packet manifest generator` is the smallest honest first slice:

- it discovers local inputs without consuming remote state
- it resolves packet field population without emitting a final downstream-ready packet
- it freezes landing paths and proof references before later artifact generation
- it proves the helper can stay local-only and reviewable

## What The First Slice Must Do

The first implementation slice should:

1. accept `lane`, `source`, `owner-surface`, and optional `receipt-ref`
2. inspect local source paths only
3. classify the source set into the packet contract fields
4. generate a local manifest describing:
   - proposed packet purpose
   - schema/version
   - sensitivity
   - source provenance
   - transformation steps expected
   - validation expectations
   - omission/exclusion summary
   - downstream target class
   - planned artifact paths
   - receipt/proof linkage
5. stop before final packet emit

## What The First Slice Must Not Do

The first implementation slice must not:

- write `packet.json`
- send to any remote target
- call a model
- post to Discord
- call Supabase or Vercel APIs
- expand or print secret-bearing values
- perform hidden transformations not recorded in the manifest
- hardcode one lane's source schema as the universal packet generator

## Dry-Run / No-Send Boundary

The selected first slice is effectively a hardened dry-run planner.

Allowed behavior:

- local input discovery
- local field inference
- local manifest generation
- local validation of required planning fields
- local proof-summary generation

Forbidden behavior:

- no remote send
- no prompt emission
- no hidden export
- no packet emit beyond the manifest/planning artifacts

## Local Input Discovery Rules

The first slice may discover source inputs from:

- explicit `--source` paths
- governed local roots already named by doctrine:
  - `runtime/exports/**`
  - `runtime/captures/**`
  - `runtime/receipts/**`
  - `data/**`
  - repo-local receipt/doc surfaces

The first slice must not:

- crawl remote URLs as source-of-truth
- infer secrets from env or secret stores
- merge unrelated repo-local surfaces without the lane being named explicitly

## Packet Field Population Boundary

The manifest generator must populate or pre-populate all contract fields except the final emitted payload body.

Required manifest fields:

- `packet_purpose`
- `packet_schema_version`
- `downstream_target_class`
- `sensitivity_label`
- `source_provenance`
- `transformation_record`
- `validation_result`
- `redaction_status`
- `dedupe_status`
- `payload_summary`
- `export_exclusion_summary`
- `receipt_or_proof_ref`
- `planned_artifacts`

The manifest may include:

- `minimal_useful_payload_outline`

The manifest must not include:

- raw sensitive payload
- final transformed export body
- secret-expanded content

## Artifact Landing Paths

The first slice should land artifacts under:

- `runtime/gateway-packets/<lane>/<date>/<packet-id>/`

First planning artifacts:

- `packet-manifest.json`
- `packet-plan.md`
- `packet-proof-summary.json`

Why these are enough:

- `packet-manifest.json` freezes the helper-readable planning state
- `packet-plan.md` gives a human-review surface for receipts
- `packet-proof-summary.json` gives later receipts a compact machine-readable proof hook

## Receipt / Proof Output

The first slice should make later receipts easy to write by exposing:

- source paths used
- excluded source classes
- inferred packet purpose
- inferred downstream target class
- sensitivity class
- planned output root
- contract fields still unresolved, if any
- validation blockers, if any

The first slice should therefore prove packet generation readiness without claiming packet emission already occurred.

## First Implementation Boundary

The smallest safe implementation boundary is:

- local manifest generation only

Not yet included:

- final packet emit
- packet replay tooling
- lane-specific transformers
- downstream handoff
- mutation or publication flows

## Non-Goals

- no live send mode
- no sync mode
- no mutation mode
- no direct AI/model prompt packaging
- no automatic receipt creation
- no lane-specific hardcoding beyond the manifest examples needed for proof

## Marker Recommendation

Keep `Local Data Gateway` flat at `10%` in this pass.

Why:

- doctrine, exemplars, and helper boundary are durable
- implementation scope is now clearer
- but no helper code or first manifest-proof run exists yet

## Exact Next Package

`Local Data Gateway _stack helper local manifest prototype package 1`

Why:

- the next missing proof is an actual local-only prototype of the selected smallest slice
- it can validate discovery, field population, planned artifact paths, and no-send guarantees
- it still avoids widening into final packet emit or remote behavior

## Rule

Helper implementation planning must select one smallest safe helper slice, not a broad gateway system.

## Pattern

Packet contract -> exemplar proof -> helper contract -> implementation planning -> local manifest prototype -> later packet emit proof

## Failure Mode

Planning a helper that mixes local packet shaping with remote send behavior, hidden transformations, or lane-specific execution hardcoding.
