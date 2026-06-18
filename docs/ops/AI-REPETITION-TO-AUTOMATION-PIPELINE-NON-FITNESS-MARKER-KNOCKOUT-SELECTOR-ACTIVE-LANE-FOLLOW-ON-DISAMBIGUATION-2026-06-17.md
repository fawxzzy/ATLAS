# AI Repetition-to-Automation Pipeline Non-Fitness Marker Knockout Selector Active-Lane Follow-On Disambiguation - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Repetition-to-Automation Pipeline`
- Mode: `root-owned selector-surface refinement`
- Scope: `remove the current-lane self-reference from the non-Fitness marker knockout helper by separating the active packet from the first admissible downstream follow-on`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-SURFACE-PASS-52-2026-06-09.md`
  - `docs/ops/ROOT-BOUNDED-LANE-SELECTION-AFTER-AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-FAMILY-EXHAUSTION-CLOSEOUT-2026-06-17.md`
  - `ops/atlas/marker_knockout_selector.py`
  - `tests/test_atlas_marker_knockout_selector.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@b766aebb`

## Objective

Keep the current active AI-pipeline selector surface useful after the `AI Long-Run Batch Orchestration` family exhausts.

The problem was narrow but real:

- current durable truth now makes `AI Repetition-to-Automation Pipeline` the active immediate lane again
- the selector helper already respected that active-lane truth
- but its old next-packet reporting collapsed the active lane and the downstream follow-on into one self-referential result

That made the helper less useful exactly when it became the current operator surface again.

## What Landed

In `ops/atlas/marker_knockout_selector.py`:

- one explicit `packet_for_marker(...)` mapper for the bounded marker surfaces the helper currently knows how to route
- one separate `selected_current_packet` field for the active lane packet
- one separate downstream follow-on read:
  - `next_after_current_marker`
  - `next_after_current_percentage`
  - `next_after_current_reason`
  - `next_after_current_expected_evidence`
  - `next_after_current_packet`
- one markdown rendering split between:
  - `Current Active Marker`
  - `First Admissible After Current Lane`

In `tests/test_atlas_marker_knockout_selector.py`:

- updated JSON expectations for active-lane selection
- one additional markdown-output proof that current packet and downstream follow-on now render separately

## Current Proven Output

On current durable truth, the helper now renders:

- current active marker: `AI Repetition-to-Automation Pipeline`
- current packet: `AI Repetition-to-Automation Pipeline non-Fitness marker knockout selector surface`
- first admissible after current lane: `AI Long-Run Batch Orchestration`
- next packet after current lane: `AI Long-Run Batch Orchestration queue-or-registry active follow-on`

That is a real operator-surface improvement because it removes the need to manually interpret a self-referential selector result.

## Marker Movement

- `AI Repetition-to-Automation Pipeline` moves from `32%` to `33%`

Why `33%` is honest:

- one additional root-owned operator helper refinement is now real on canonical `main`
- the current active selector surface now distinguishes present-lane work from the first downstream admissible follow-on
- the helper remains bounded, fail-closed, and proof-backed

Why the lane stays low:

- no new automation family is admitted
- no owner-repo or `_stack` execution widening happened here
- no repeat multi-operator adoption class is proven yet

## Non-Goals

- no Fitness mutation
- no deploy, publication, archive/delete, `.env`, or secret work
- no marker movement outside `AI Repetition-to-Automation Pipeline`
- no reopening of `_stack Readiness`

## Verification

Commands run:

- `python -m unittest tests.test_atlas_marker_knockout_selector -v`
- `python .\ops\atlas\marker_knockout_selector.py --format markdown`
- `python .\ops\atlas\marker_knockout_selector.py --format json`
- `python .\ops\validation\validate_stack.py --ratchet`

Results:

- selector tests: `5 tests OK`
- markdown output now shows separate `Current Active Marker` and `First Admissible After Current Lane` sections
- JSON output now carries separate `selected_current_packet` and `next_after_current_*` fields
- stack validation remains `critical=0 error=0 warning=3 info=0`
