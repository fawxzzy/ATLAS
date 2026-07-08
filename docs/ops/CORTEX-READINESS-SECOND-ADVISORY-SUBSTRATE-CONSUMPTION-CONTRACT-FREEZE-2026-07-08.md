# Cortex Readiness Second Advisory Substrate Consumption Contract Freeze - 2026-07-08

- CODEX-MSG-ID: `CODEX-2026-07-08-CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-CONTRACT-FREEZE`
- Date: `2026-07-08`
- Mode: `docs-only contract freeze`
- Scope: `freeze the second Cortex advisory substrate consumption contract without implementing a worker`
- Selector basis: `docs/ops/CORTEX-READINESS-POST-SANDBOX-FINAL-BLOCKER-NEXT-SLICE-SELECTION-2026-07-08.md`
- Branch basis: `main@e36b8095f5232660b09a1a2be91e0a647a231e53`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Cortex may define a second advisory substrate consumer class, distinct from the existing authority-safe handoff consumer, for explicit root-owned substrate only.

This contract does not implement that consumer. It freezes the allowed evidence classes, schema expectations, authority denials, future proof matrix, and next implementation-admission packet.

## Admitted Advisory Substrate Source Classes

The future consumer may read only explicit ATLAS-root sources from these classes:

- Cortex manifests and restart mirrors:
  - `docs/memory/initiatives/continuity-manifest-cortex-readiness.json`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Cortex and Playbook/Cortex authority receipts:
  - `docs/ops/CORTEX-READINESS-*.md`
  - `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-*.md`
- Existing Cortex advisory runtime artifacts:
  - `runtime/cortex/current-state/latest.json`
  - `runtime/cortex/operator-surface/latest.json`
  - `runtime/cortex/context/latest.json`
  - `runtime/cortex/worker-prompts/latest.json`
- Validation and continuity proof:
  - `runtime/receipts/validation/stack-validation.latest.json`
  - output from `ops/atlas/continuity_manifest_health.py`
  - output from `ops/atlas/continuity_open_marker_restart_index.py`
  - output from `ops/atlas/continuity_coverage.py`
- Existing Cortex helpers and tests as read-only contract references:
  - `ops/cortex/authority_safe_interface_handoff.py`
  - `ops/cortex/authority_safe_handoff_consumption.py`
  - `ops/cortex/worker_prompt.py`
  - `tests/test_cortex_authority_safe_interface_handoff.py`
  - `tests/test_cortex_authority_safe_handoff_consumption.py`
  - `tests/test_cortex_worker_prompt.py`

## Excluded Source Classes

The future consumer must reject:

- `repos/**`
- Fitness owner-lane sources
- Mazer owner-lane sources
- owner-repo receipts as truth inputs
- hidden transcript, chat, or session state
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- deploy or platform output
- any source outside the ATLAS root
- any absolute path source
- any parent-traversal source

## Schema Expectations

The future implementation should use:

- script: `ops/cortex/second_advisory_substrate_consumption.py`
- tests: `tests/test_cortex_second_advisory_substrate_consumption.py`
- schema version: `atlas.cortex.second-advisory-substrate-consumption.v1`

Expected deterministic JSON fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `consumed_surfaces`
- `substrate_summary`
- `preserved_authority_denials`
- `advisory_payload`
- `forbidden_surfaces`
- `warnings`
- `blockers`
- `safe_to_use`

Expected statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Authority Denials

The future consumer must preserve explicit denials for:

- execution
- approval
- owner-truth
- final-receipt
- deploy
- secret-handling
- transcript-scraping
- automatic `_stack` dispatch
- repo mutation
- platform mutation
- owner-repo mutation
- protected-surface mutation
- marker movement

## Output Contract

Default output is stdout only.

Optional writes are admitted only after explicit CLI request and only under `tmp/**`. The future helper must reject output paths under protected or owner surfaces, including:

- `repos/**`
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- runtime latest files by default
- final Lifeline receipts

## Proof Matrix

The future implementation must prove:

- accepts default admitted root-owned substrate
- accepts explicit admitted root-owned source refs
- rejects owner-repo source refs
- rejects Fitness and Mazer source refs
- rejects protected source refs
- rejects transcript/session source refs
- rejects absolute paths and parent traversal
- rejects non-`tmp/**` output
- emits deterministic JSON ordering
- preserves all authority denials
- reports validation critical/error state before `safe_to_use=true`
- writes only when an explicit safe `tmp/**` output is supplied
- does not move markers itself

## Marker Decision

No marker moves.

Reason: this is a docs-only contract freeze. `Cortex Readiness` remains `45%` until a second implementation-backed authority-false consumer lands and proves safe advisory consumption.

## Exact Next Packet

`Cortex Readiness second advisory substrate consumption first-implementation admission`
