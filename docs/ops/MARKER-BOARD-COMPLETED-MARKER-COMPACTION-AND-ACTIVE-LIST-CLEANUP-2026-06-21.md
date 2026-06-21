# Marker Board Completed Marker Compaction And Active List Cleanup - 2026-06-21

- Date: `2026-06-21`
- Owner: `ATLAS root`
- Mode: `docs-only root-bounded marker-board cleanup`
- Scope: `remove already-closed 100% markers from live active/open display while preserving restart truth, parser compatibility, and compact closed-ratchet discoverability`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/memory/initiatives/continuity-manifest-ai-long-run-batch-orchestration.json`
  - `ops/atlas/marker_knockout_selector.py`
  - `tests/test_atlas_marker_knockout_selector.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main`

## Objective

Compact the live marker board so completed `100%` markers no longer sit in active/open display positions unless they still need active carry-forward visibility, keep them discoverable as one-line entries in `Closed / Locked Ratchets`, and preserve the current parser and restart story without reopening any closed ratchet.

## Inventory

Completed markers still displayed in live active/open sections before cleanup were:

- `Knowledge Capture & Transfer: 100%`
- `Durable Context Externalization: 100%`
- `DiscordOS Runtime & Product Hardening: 100%`
- `Dependency Untangling: 100%`
- `Tmp Dependency Elimination: 100%`

The live active/open markers that remain below `100%` and stay visible are:

- `Truth Map & ATLAS Book: 97%`
- `Inventory & Truth Map: 85%`
- `AI Repetition-to-Automation Pipeline: 35%`
- `AI Long-Run Batch Orchestration: 63%`
- `Cortex Readiness: 41%`
- `Playbook Everywhere + Cortex Interface: 22%`
- `Sandbox Simulation Readiness: 0%`

## Cleanup Decision

### Removed From Active/Open Display

- `Knowledge Capture & Transfer`
  - closed for its admitted scope and restart-relevant through receipts plus closed ratchets rather than live active display
- `Durable Context Externalization`
  - closed for its admitted scope and restart-relevant through receipts plus closed ratchets rather than live active display
- `DiscordOS Runtime & Product Hardening`
  - closed on owner proof and future Discord work must open as new owner scope rather than stay on the live board
- `Dependency Untangling`
  - closed on live owner-state absorption and no immediate bounded root-only follow-on is open
- `Tmp Dependency Elimination`
  - already closed at `100%` and no longer belongs under supporting open markers

### Held As Closed Carry-Forward Context Only

- `Discord Workflow, Publication & Docs Reliability`
  - already absent from the front-page and supporting-open tables, so no additional marker-table move was required
  - its carry-forward prose remains in the cluster read without consuming an active/open marker slot

## Final Live Marker Surfaces

### Active Front-Page Marker Table

- `Truth Map & ATLAS Book: 97%`
- `Inventory & Truth Map: 85%`
- `AI Repetition-to-Automation Pipeline: 35%`
- `AI Long-Run Batch Orchestration: 63%`

### Supporting Open Markers

- `Cortex Readiness: 41%`
- `AI Repetition-to-Automation Pipeline: 35%`
- `AI Long-Run Batch Orchestration: 63%`
- `Playbook Everywhere + Cortex Interface: 22%`
- `Sandbox Simulation Readiness: 0%`

### Closed / Locked Ratchets Additions

- `Dependency Untangling: 100%`
- `Knowledge Capture & Transfer: 100%`
- `Durable Context Externalization: 100%`
- `DiscordOS Runtime & Product Hardening: 100%`
- `Tmp Dependency Elimination: 100%`

## Parser And Restart Compatibility

- `ops/atlas/marker_knockout_selector.py` still reads only `Active Front-Page Marker Table`, `Supporting Open Markers`, and `Closed / Locked Ratchets`
- grouping prose remains outside the parser-controlled one-line marker entries
- the active/open field now contains only genuinely open markers, so selector output and restart routing stay cleaner without changing parser shape
- closed ratchets remain discoverable as compact one-line entries, with evidence still routed through receipts and the receipt index

## Marker Decision

- `none`

Why:

- this bundle changes display hygiene only
- no executed state, proof-backed adoption, manifest-backed restart breadth, or blocker-clearance class changed

## Validation

Executed validation and proof commands:

- `python -m unittest tests.test_atlas_marker_knockout_selector`
- `python .\ops\atlas\marker_knockout_selector.py --format json`
- `python .\ops\atlas\marker_knockout_selector.py --format markdown`
- `python .\ops\validation\validate_stack.py --ratchet`
- `git status --short`
- `git diff --name-only`

Observed results:

- selector tests stayed green
- selector json and markdown still rendered cleanly from the compacted board
- root validation stayed at `critical=0 error=0 warning=11 info=0`
- unrelated broad root residue remained untouched

## Rule

Keep completed markers out of the live active/open display unless one exact carry-forward reason still requires them there as active read-model anchors; keep their proof detail in receipts and the receipt index, not duplicated on the live board.
