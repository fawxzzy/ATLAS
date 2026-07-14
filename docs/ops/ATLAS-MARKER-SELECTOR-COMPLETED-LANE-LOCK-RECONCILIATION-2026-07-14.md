# Atlas Marker Selector Completed-Lane Lock Reconciliation

## Outcome

The root marker selector now treats every marker at `100%` as `already closed / locked` before applying lane-specific policy, active-lane routing, or explanatory prose.

## Defect converted

After `Cortex Dual-Mode Replacement Readiness` closed at `100%`, the selector read the new percentage but reused its stale 90% policy and selected the already-completed dispatch packet as the first fallback. That could reopen completed work and duplicate an accepted execution cluster.

The generic rule is now:

> A 100% marker cannot be routed by stale policy text. Reopening requires a new capability denominator or a material regression.

## Proof

- implementation: `ops/atlas/marker_knockout_selector.py`
- regression coverage: `tests/test_atlas_marker_knockout_selector.py`
- focused selector tests: `16 / 16` passed
- live selector classification: Cortex Dual-Mode and GitHub Control-Plane are `already closed / locked`
- live fallback: `Cortex Simulation Substrate Readiness Fable/generative-agent research contract freeze`

No marker moves in this reconciliation. Sandbox Simulation Readiness remains the held active lane at `99%`; this repair only prevents completed-lane rerouting.
