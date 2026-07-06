# Playbook Everywhere + Cortex Interface Authority-Safe Cortex Interface Widening First-Implementation Admission

- CODEX-MSG-ID: `CODEX-2026-07-06-PLAYBOOK-CORTEX-AUTHORITY-SAFE-INTERFACE-WIDENING-FIRST-IMPLEMENTATION-ADMISSION`
- Date: `2026-07-06`
- Mode: `docs-only first-implementation admission`
- Scope: `admit the smallest future helper slice for authority-safe Cortex interface widening without implementing it`
- Branch basis: `main@0324d75073b57ddc94fa0a435b6cd9330d0daa51`
- Contract basis: `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-CONTRACT-FREEZE-2026-07-06.md`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Admit one future implementation slice:

`authority_safe_interface_handoff`

This slice may become a root-owned, read-only advisory Cortex handoff helper. It may convert already-approved ATLAS, Playbook, and Cortex source surfaces into one bounded Codex-style handoff artifact.

This packet does not create the helper. It only freezes the smallest admissible implementation boundary and proof matrix.

## 1. Admitted Implementation Slice

The admitted future slice is a read-only helper with this purpose:

> Produce an advisory Cortex interface handoff from explicit root-owned source refs, preserving authority denials and owner-lane separation.

The helper must be inert by default: no repo mutation, no platform mutation, no secret reads, no deploys, no `_stack` dispatch, no transcript scraping, and no final receipt emission.

## 2. Why This Is The Smallest Honest Step

The previous contract freeze defined what authority-safe interface widening means. The smallest implementation step is therefore not a worker, queue, model, or repo mutation. It is one deterministic helper that proves Cortex can package existing truth into an advisory handoff without gaining authority.

Anything broader would collapse too many concerns:

- owner-repo scanning would reopen the Fitness/Mazer coupling problem
- runtime writeback would widen Cortex before path guards are proven
- final receipt drafting would confuse advisory output with Lifeline authority
- `_stack` dispatch would turn a handoff into execution
- platform or secret access would exceed the root-owned docs-only lane

## 3. Source Surfaces That May Be Consumed

The future helper may consume only explicit root-owned source refs from the contract freeze:

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

The helper must not discover or scan `repos/**`.

## 4. Output Surface That May Be Produced

The future helper may emit:

- stdout human summary
- deterministic JSON to stdout through `--json`
- one root-relative optional output path under `tmp/**` through explicit `--output`

The helper must reject absolute paths, parent traversal, protected roots, and implicit writes.

## 5. Authority That Remains Forbidden

Cortex remains denied:

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

The helper may recommend a next packet. It must not perform that packet.

## 6. Future Implementation File

Admitted future file:

`ops/cortex/authority_safe_interface_handoff.py`

This name is narrower and clearer than the earlier generic `interface_widening_handoff.py` placeholder because it encodes the non-negotiable authority-safe boundary directly in the file name.

## 7. Future Test File

Admitted future test file:

`tests/test_cortex_authority_safe_interface_handoff.py`

The test file must prove the helper is read-only, deterministic, and authority-denying before any marker movement is considered.

## 8. Future Proof Matrix

The future implementation must prove:

- root branch/parity are reported without requiring mutation
- source refs are explicit and root-relative
- owner repo paths under `repos/**` are rejected
- protected output roots are rejected
- absolute output paths are rejected
- `--output` is required for file writes
- default mode writes no files
- JSON field ordering is deterministic
- `authority_denials` include every denied authority from the contract
- `forbidden_surfaces` include owner repos, protected roots, secrets, deploy outputs, and final receipts
- `safe_to_use` is false when validation has critical or error counts
- transcript/chat state is not consumed
- `_stack` is not dispatched
- final receipts are not emitted

## 9. Non-Goals

This packet does not:

- implement the helper
- create tests
- mutate owner repos
- mutate Fitness
- mutate Mazer
- mutate the Playbook owner repo
- mutate Supabase or Vercel
- deploy or publish
- read or write secrets
- touch `.env*`, `.vercel/`, `.playwright-mcp/`, `archive/`, or `secrets/`
- move markers
- claim Cortex execution readiness

## 10. Exact Next Packet

Next exact packet:

`Playbook Everywhere + Cortex Interface authority-safe Cortex interface widening prompt-pack and worker handoff contract`

That packet should prepare the prompt pack and worker handoff contract for implementing `ops/cortex/authority_safe_interface_handoff.py` with `tests/test_cortex_authority_safe_interface_handoff.py`.

It still must not implement the helper.

## Future CLI Contract

Expected future command forms:

- `python ops/cortex/authority_safe_interface_handoff.py`
- `python ops/cortex/authority_safe_interface_handoff.py --json`
- `python ops/cortex/authority_safe_interface_handoff.py --scope root`
- `python ops/cortex/authority_safe_interface_handoff.py --scope research`
- `python ops/cortex/authority_safe_interface_handoff.py --source <path>`
- `python ops/cortex/authority_safe_interface_handoff.py --output <root-relative-path>`
- `python ops/cortex/authority_safe_interface_handoff.py --strict`

Expected future JSON fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `consumed_surfaces`
- `handoff_payload`
- `authority_denials`
- `forbidden_surfaces`
- `warnings`
- `blockers`
- `safe_to_use`

## Marker Decision

No marker moves from this admission receipt.

- `Playbook Everywhere + Cortex Interface`: remains `30%`
- `Cortex Readiness`: remains `41%`
- `AI Work Session Stability & Auto-Sync Loop`: remains `85%`

Reason: this packet admits a future implementation slice, but no helper, tests, or implementation-backed proof have landed.

## Current ATLAS Marker Board, Excluding Mazer

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
- No owner repo was mutated.
- Supabase was not touched.
- Vercel was not touched.
- Deployment was not touched.
- Secrets and `.env*` files were not touched.
- Protected surfaces were not touched.
- Cortex remains read-only advisory.
