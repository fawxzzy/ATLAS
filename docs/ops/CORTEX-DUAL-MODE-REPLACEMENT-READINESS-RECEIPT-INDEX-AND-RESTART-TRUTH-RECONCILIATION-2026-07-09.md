# Cortex Dual-Mode Replacement Readiness Receipt-Index And Restart-Truth Reconciliation

## Purpose

Reconcile the already-published `Cortex Dual-Mode Replacement Readiness: 20%` ratchet into the ATLAS restart mirrors without reopening implementation work or widening authority.

## Current Durable State

- Marker: `Cortex Dual-Mode Replacement Readiness`
- Current percent: `20%`
- Ratchet receipt: `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-MARKER-SURFACE-RATCHET-DECISION-2026-07-09.md`
- Durable commit: `cd7bf307`
- Published branch state: `main` and `origin/main` at parity

## Surfaces Reviewed

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json`
- `ops/atlas/marker_knockout_selector.py`
- `tests/test_atlas_marker_knockout_selector.py`

## Stale Surfaces

1. `docs/atlas-book/01-current-state.md` still described the July 8 owner-truth adoption checkpoint as the top snapshot and still named the AI Long-Run `70% -> 71%` move as the latest ATLAS marker movement.
2. `docs/atlas-book/05-receipt-index.md` listed the dual-mode operating-model and role-inventory chain, but it did not yet include the published dual-mode marker-surface ratchet decision or this reconciliation receipt.

## Reconciled

1. `docs/atlas-book/01-current-state.md`
   - refreshed the top snapshot to the current published checkpoint `main@cd7bf307`
   - recorded that `Cortex Dual-Mode Replacement Readiness` is durably at `20%`
   - replaced the stale "latest marker movement" note with the published dual-mode `0% -> 20%` ratchet
2. `docs/atlas-book/05-receipt-index.md`
   - added the missing dual-mode marker-surface ratchet decision
   - indexed this reconciliation receipt

## Intentionally Left Untouched

1. `docs/atlas-book/12-restart-and-handoff-guide.md`
   - the current local diff is an unrelated AI Long-Run planner-facing update
   - it was not required for dual-mode restart safety in this packet
2. unrelated existing dirty root files outside the exact reconciliation slice
   - `AGENTS.md`
   - `README-STACK.md`
   - `stack.yaml`
   - `stack.lock.yaml`
   - `docs/ops/discordos-mazer-board-correction-2026-07-09.md`
3. selector, manifest, and test files
   - current routing truth for those surfaces was already coherent and required no change

## Validation

- `python ops\validation\validate_stack.py`
  - `critical=0 error=0 warning=0 info=0`
- `python ops\atlas\continuity_manifest_health.py`
  - `status=ok`
  - `manifest_count=21`
  - `ok_count=21`
- `python ops\atlas\continuity_open_marker_restart_index.py`
  - `status=ok`
  - `eligible_open_marker_count=7`
  - `restart_ready_count=7`
- `python ops\atlas\continuity_coverage.py`
  - `status=structured`
  - `initiative_manifest_count=21`
  - `open_marker_restart_ready_count=7`
  - `maintained_manifest_restart_ready_count=21`
- `python ops\atlas\marker_knockout_selector.py --format json`
  - `operator_action=hold_current_lane`
  - `active_lane=Sandbox Simulation Readiness`
- `python -m unittest tests.test_atlas_marker_knockout_selector -v`
  - `14/14` passing

## Marker Decision

- No new marker movement.
- Preserve `Cortex Dual-Mode Replacement Readiness: 20%`.
- Preserve held-root selector truth on `Sandbox Simulation Readiness: 99%`.

## Exact Next Packet

- Operator-selected strategic next packet: `Cortex Simulation Substrate Readiness Fable/generative-agent research contract freeze`

## Authority / Scope

- owner repos not mutated
- Fitness not mutated
- Mazer not mutated
- Vercel, Supabase, deploy, workflow, and secret surfaces not touched
