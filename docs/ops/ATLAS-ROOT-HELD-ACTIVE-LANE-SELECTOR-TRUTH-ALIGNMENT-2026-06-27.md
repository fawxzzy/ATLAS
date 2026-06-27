# ATLAS Root Held-Active-Lane Selector Truth Alignment - 2026-06-27

- Date: `2026-06-27`
- Owner: `ATLAS/root`
- Mode: `docs-plus-root-control-surface truth alignment`
- Scope: `remove the false admissible-now classification when the active ATLAS-root lane is already manifest-held and the selector emits no_immediate_root_packet`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/ATLAS-ROOT-NO-IMMEDIATE-PACKET-HOLD-AND-STACK-RESYNC-2026-06-27.md`
  - `ops/atlas/marker_knockout_selector.py`
  - `tests/test_atlas_marker_knockout_selector.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main`

## Objective

Keep the published root selector honest after the no-immediate-packet hold by ensuring the active lane is no longer emitted as `admissible now` once its own manifest-backed ladder says no immediate same-lane packet is open.

## Done

- added one explicit selector category: `held active lane`
- changed the active-lane policy so a manifest-held active lane no longer reuses the `admissible now` bucket
- preserved the existing `hold_current_lane` and `no_immediate_root_packet` operator-action behavior
- added test coverage for the held active-lane category in both held-current-lane and no-immediate-root-packet cases
- refreshed the ATLAS Book current-state line so live read-model prose matches the selector contract

## Current Read

- the latest ATLAS-root family can still remain the active restart truth while also being held
- if that active family is held, the selector now reports `held active lane` instead of `admissible now`
- if every eligible open marker is manifest-held, the selector still emits `no_immediate_root_packet`
- root validation posture remains `critical=0 error=0 warning=0 info=0`

## Rule

`Held-Active-Lane Is Not Admissible-Now`

If the active ATLAS-root family is already manifest-held, keep it visible as current restart truth but do not classify it as `admissible now`.

## Failure Mode

`No-Immediate With Ghost Admissible-Now`

If root says no immediate packet is open while the same selector still emits one `admissible now` row for the held active lane, the control surface reintroduces fake motion and weakens restart honesty.
