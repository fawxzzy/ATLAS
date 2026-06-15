# AI Long-Run Batch Orchestration Queue-Or-Registry Provenance-Alert Queue Signal Budget Restart Truth Receipt Pass 291 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned restart-truth receipt`
- Source surfaces:
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-DECISION-PASS-289-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

## Objective

Convert the pass-289 and pass-290 provenance-alert queue-signal work into durable restart truth and decide whether the active AI Long-Run marker may move from `49%` to `50%` in the published Book surfaces.

## What Pass 289 Decided

- provenance-alert-derived `attention_queue` items are capped at `3`
- the routed provenance subset keeps the same shared severity-first ordering used by the final attention queue
- overflow is represented as one `provenance_alert_overflow` item instead of spamming the governed queue
- the full top-level `provenance_alerts` payload remains intact rather than being collapsed into queue-only state

## What Pass 290 Proved

- `render_status_payload(...)` preserves all actionable provenance alerts in the top-level `provenance_alerts` summary
- the same payload routes only the highest-priority three provenance alerts into `attention_queue`
- one overflow summary item carries:
  - suppressed count
  - signal cap
  - highest suppressed severity
  - total alert count
- the queue budget therefore holds at the full payload boundary, not only inside the isolated queue helper

## Restart-Truth Decision

- yes, the queue-signal budget is now restart-safe
- yes, this clears a real blocker:
  - the active lane no longer depends on chat-held ambiguity about whether provenance alerts can safely flow into the governed attention queue
- yes, this widens proof-backed adoption:
  - the subfamily is no longer only helper-local or test-local
  - it is proven at the full `render_status_payload(...)` boundary and now published into the Book restart mirrors

## Marker Movement Decision

- `AI Long-Run Batch Orchestration: 49% -> 50%`

Basis:

- executed state changed in pass 289
- proof-backed adoption widened in pass 290
- manifest-backed restart truth is broader after this pass because the Book mirrors now publish the closed signal-budget question instead of the older unresolved decision point
- one real blocker was cleared: the provenance-alert queue-budget question is no longer an open restart ambiguity

## Updated Surfaces

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

## Proof Command

- `python -m unittest tests.test_cortex_render_status_provenance`
- `python ops/validation/validate_stack.py --ratchet`
- `python ops/atlas/marker_knockout_selector.py --format json`
- `python ops/atlas/marker_knockout_selector.py --format markdown`

## Result

- the current AI Long-Run marker value is now durably published as `50%`
- the signal-budget subfamily is restart-safe across code, proof, and Book mirrors
- the lane still remains well below closure because the broader orchestration family still lacks wider runtime-state expansion, execution-home semantics, and supervised/operator proof

## Non-Claim Boundary

- this pass does not widen runtime behavior beyond the pass-289 and pass-290 code already landed
- this pass does not change the queue signal cap, overflow structure, or severity routing contract
- this pass does not repair provenance drift sources themselves
- this pass does not mutate queue state, registry state, session state, merge state, or deployment state
- this pass does not claim progress for Vercel Hobby Cost Governance or Workstation Resource Hygiene

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry post-provenance-alert queue signal budget next-slice selection`
