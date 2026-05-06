# Cortex Surface Reconciliation

- Status: Active reconciliation note
- Date: 2026-05-06
- Scope: Reconcile the 2026-04-26 MVP notes with the currently landed ATLAS-root Cortex surface

## Purpose

The April 26 Cortex MVP spec and inventory were useful as a bounded snapshot, but the implementation surface moved ahead quickly. This note records the current truth so Cortex does not become untrustworthy about its own posture.

## Confirmed Landed Surface

The following surfaces are already implemented in the ATLAS root and should be treated as landed:

- `ops/cortex/context_assembler.py` builds a deterministic `atlas.cortex.context-packet.v1` artifact under `runtime/cortex/context/**`.
- `ops/cortex/current_state.py` persists `runtime/cortex/current-state/latest.json` and `latest.md`.
- `ops/cortex/rail_state.py` and `ops/cortex/rail_state_reader.py` classify posture and publish the current rail-state view.
- `ops/cortex/worker_plan.py` emits `atlas.cortex.worker-plan.v1` prompts with rule, pattern, and failure-mode trace.
- `ops/cortex/proof_receipt.py` drafts advisory proof receipts and separates ambient debt from current-tranche debt.
- `ops/cortex/verification_ingest.py` classifies targeted verification and stack validation outcomes into proof-ready inputs.
- `ops/cortex/loop.py` produces `atlas.cortex.run-result.v1` artifacts that join rail state, worker plan, proof draft, and applied rule trace.
- `ops/cortex/run_ledger.py` summarizes persisted run artifacts into a current run-ledger view.
- `ops/cortex/lifeline_write_adapter.py` prepares approval-gated Lifeline write-ready artifacts without widening Cortex into final receipt authority.
- `ops/cortex/world_model.py` remains the broader read-model and attention synthesis lane.

This landed surface is covered by targeted tests including:

- `tests/test_cortex_context_assembler.py`
- `tests/test_cortex_worker_plan.py`
- `tests/test_cortex_proof_receipt.py`
- `tests/test_cortex_verification_ingest.py`
- `tests/test_cortex_loop.py`
- `tests/test_cortex_run_ledger.py`
- `tests/test_cortex_lifeline_write_adapter.py`

## Reconciled Gaps

The following April 26 gap statements are no longer accurate if read as current status:

- "No planner that emits bounded worker lanes" is closed by `ops/cortex/worker_plan.py`.
- "No receipt writer / proof receipt layer owned by Cortex" is closed at the advisory draft layer by `ops/cortex/proof_receipt.py`, `ops/cortex/verification_ingest.py`, and `ops/cortex/loop.py`.
- "No explicit state ledger for latest-clean-step / blocked-lane tracking" is only partially accurate now that `ops/cortex/run_ledger.py`, `ops/cortex/current_state.py`, and `ops/cortex/context_assembler.py` exist.

## Gaps That Still Matter

The remaining problems are now about coherence and operating surface design, not raw feature existence:

1. There is still no single operator entrypoint.
   The seeded next action should now move to `promote-cortex-operator-surface-wave4`, because operators still consume multiple artifact families instead of one promoted default surface.
2. Final Lifeline receipt emission remains gated.
   `ops/cortex/lifeline_write_adapter.py` intentionally stops at write-ready artifacts when mapped receipt inputs are incomplete or ambiguous.
3. The `_stack` consumption loop is still under-promoted.
   Cortex can emit context and planning artifacts, but the productized `_stack` consumer path is not yet the default operating lane.

## Recommended Order

The next safe tranche should stay inside ATLAS root ownership and proceed in this order:

1. Reconcile the seed, rail-state, current-state, and dependent tests so the next action reflects the current implementation frontier.
2. Promote one canonical operator surface that joins posture, blockers, selected lane, latest run summary, and receipt readiness.
3. Finish the narrow Lifeline mapping required for an approval-gated final receipt candidate.
4. Run one bounded `_stack` pilot that consumes Cortex context and planning artifacts without transcript scraping.

## Boundary Reminder

Cortex remains a root-owned, read-only coordination runtime under `runtime/cortex/**`.
It may observe, interpret, plan, classify proof, and prepare handoff artifacts.
It must not become owner truth for governance, orchestration, product state, or final receipt authority.
