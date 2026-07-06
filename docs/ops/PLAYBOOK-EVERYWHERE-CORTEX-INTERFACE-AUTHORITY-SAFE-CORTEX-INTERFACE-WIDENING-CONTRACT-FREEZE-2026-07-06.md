# Playbook Everywhere + Cortex Interface Authority-Safe Cortex Interface Widening Contract Freeze

- CODEX-MSG-ID: `CODEX-2026-07-06-PLAYBOOK-CORTEX-AUTHORITY-SAFE-INTERFACE-WIDENING-CONTRACT-FREEZE`
- Date: `2026-07-06`
- Mode: `docs-only contract freeze`
- Scope: `define the next safe Cortex interface-widening contract without implementing Cortex or changing authority`
- Branch basis: `main@ac3bba582a4c85a31c8d5b7548f9883ed79fc483`
- Selector basis: `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-POST-ADOPTION-MATRIX-NEXT-SLICE-SELECTION-2026-07-06.md`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Freeze one authority-safe Cortex interface-widening contract.

In this lane, interface widening means Cortex may gain a better structured advisory handoff contract over existing ATLAS/Playbook/Codex truth. It does not mean Cortex may execute work, approve work, mutate repos, issue final receipts, scrape transcripts, deploy systems, change secrets, or become owner-truth authority.

## Contract Name

`authority_safe_cortex_interface_widening.v1`

## Purpose

The contract defines how a future root-owned helper may convert current ATLAS/Playbook/Cortex truth into one bounded advisory handoff for Codex-style execution planning.

The handoff may recommend a next packet and explain why. It must not perform the packet.

## Allowed Input Surfaces

A future implementation may read these root-owned surfaces:

- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/standards/WORKER-ORCHESTRATION.md`
- `docs/PLAYBOOK_NOTES.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json`
- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-*.md`
- `ops/atlas/playbook_adoption_matrix.py`
- `ops/cortex/worker_prompt.py`
- `runtime/cortex/worker-prompts/latest.json`
- `runtime/receipts/validation/stack-validation.latest.json`
- `stack.lock.yaml`

Owner repo files under `repos/**` are not admitted input surfaces for this contract.

## Allowed Output Surfaces

A future implementation may emit:

- stdout summary
- deterministic JSON with `--json`
- one root-relative optional output file under `tmp/**`
- a future docs-only receipt under `docs/ops/**` after human/Codex review

The JSON output must be advisory and must include:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `parity`
- `input_refs`
- `selected_interface_contract`
- `recommended_next_packet`
- `authority_grants`
- `authority_denials`
- `owner_lane_boundaries`
- `cortex_allowed_actions`
- `cortex_forbidden_actions`
- `codex_handoff`
- `evidence`
- `blockers`
- `warnings`
- `safe_to_continue`

## Forbidden Output Surfaces

A future implementation must not write:

- `repos/**`
- `runtime/**`, except an explicitly admitted runtime read-model in a later packet
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- deployment outputs
- owner-repo receipts
- final Lifeline receipts

## Authority Denials

This contract explicitly denies Cortex:

- execution authority
- approval authority
- owner-truth authority
- final-receipt authority
- deploy authority
- secret-handling authority
- transcript-scraping authority
- automatic `_stack` dispatch authority
- repo mutation authority
- platform mutation authority

## Authority Grants

This contract grants only:

- read-only interpretation of admitted root-owned surfaces
- advisory packet recommendation
- bounded Codex handoff drafting
- explicit source-ref citation inside the advisory handoff

The grant is advisory only.

## Implementation-Backed Evidence Threshold

A future marker movement requires more than this contract.

The next implementation-backed threshold would require:

- a root-owned helper or prompt surface that consumes this contract
- direct tests for authority grants and denials
- proof that owner repos are not scanned or mutated
- proof that forbidden output paths are rejected
- proof that final-receipt authority remains outside Cortex
- a reconciliation receipt that records the exact evidence

## Future Worker/Test Files That May Be Admitted Later

Future implementation may be routed to one of these root-owned surfaces, if a later readiness packet admits it:

- `ops/cortex/interface_widening_handoff.py`
- `tests/test_cortex_interface_widening_handoff.py`

These files are not admitted by this packet. They are named only to make the future routing explicit.

## Marker Decision

No marker moves from this contract freeze.

`Playbook Everywhere + Cortex Interface` remains `30%`.

Reason: this packet freezes the authority boundary, but does not yet implement or prove a new consumer class.

`Cortex Readiness` remains `41%`.

Reason: Cortex authority is not widened. The packet defines a safe future widening path, not a live Cortex capability.

## Exact Next Packet

Next exact packet:

`Playbook Everywhere + Cortex Interface authority-safe Cortex interface widening first-implementation admission`

That packet should decide whether the future helper is admissible and freeze its first proof matrix. It should still not mutate owner repos or grant Cortex execution authority.

Current ATLAS marker board, excluding Mazer:

- `Sandbox Simulation Readiness`: `99%`
- `AI Work Session Stability & Auto-Sync Loop`: `85%`
- `AI Repetition-to-Automation Pipeline`: `38%`
- `AI Long-Run Batch Orchestration`: `66%`
- `Inventory & Truth Map`: `99%`
- `Playbook Everywhere + Cortex Interface`: `30%`
- `Cortex Readiness`: `41%`

## Boundaries Preserved

- Fitness was not mutated.
- Mazer was not mutated.
- Playbook owner repo was not mutated.
- Supabase was not touched.
- Vercel was not touched.
- Deployment was not touched.
- Secrets and `.env*` files were not touched.
- Protected surfaces were not touched.
- Cortex remains read-only advisory.
