# Marker System Hygiene Pass 2 - 2026-05-28

- Date: `2026-05-28`
- Lane: `ATLAS marker-system hygiene`
- Mode: `docs-only control-plane read-model hygiene`
- Source surfaces:
  - `docs/ops/MARKER-SYSTEM-HYGIENE-PASS-1-2026-05-28.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main@5f55e8e`

## Objective

Further tighten the canonical marker read model so first-scan operator attention goes to the smallest useful live set while preserving all historical ratchets and all existing percentages.

This pass does not:

- add implementation work
- change owner-repo truth
- create a new execution lane
- change any marker percentages
- delete any historical ratchet
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `5f55e8e`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Why This Pass Exists

Pass 1 separated:

- active front-page markers
- supporting open markers
- closed / locked ratchets

That split was correct, but the front-page set was still broader than the fastest useful first scan.

Pass 2 exists to finish the tightening step without changing any underlying lane meaning.

## Decisions Frozen In This Pass

### 1. Keep cluster reads rich

The four cluster reads remain the first operator view:

- continuity substrate
- execution substrate
- Discord workflow
- naming / ownership hygiene

They remain descriptive, not numerical rollups.

### 2. Cap the front-page table to the smallest useful set

`Active Front-Page Marker Table` is now capped to the ten markers that most directly change current routing decisions:

- `_stack` Readiness
- `Atlas-owned Repo Naming Canonicalization`
- `Local Data Gateway`
- `Dependency Untangling`
- `Truth Map & ATLAS Book`
- `Inventory & Truth Map`
- `Knowledge Capture & Transfer`
- `Durable Context Externalization`
- `Discord OS Infrastructure Separation`
- `Discord OS Feedback Workflow Canonicalization`

### 3. Move low-signal open markers to supporting

The following remain open and durable, but are no longer first-scan markers:

- `Discord Workflow, Publication & Docs Reliability`
- `Playbook Everywhere + Cortex Interface`
- `AI Repetition-to-Automation Pipeline`
- `AI Long-Run Batch Orchestration`

Why:

- they still matter
- they still belong in the read model
- they do not currently change next-step routing as often as the capped front-page set

### 4. Preserve closed ratchets exactly

Closed / locked ratchets remain preserved and visible for:

- restart truth
- historical boundary interpretation
- governance continuity

No historical marker was removed or hidden.

### 5. Do not invent composite percentages

This pass keeps the explicit rule that cluster reads are interpretive summaries only.

They do not authorize:

- merged percentages
- fake aggregate scores
- silent marker consolidation

## Front-Page Read Frozen

The intended first-scan order is now:

1. read `Active Cluster Read`
2. read the capped `Active Front-Page Marker Table`
3. use `Supporting Open Markers` only when the lane is outside the capped set
4. use `Closed / Locked Ratchets` only for history or restart questions

## Restart And Vision Surface Effect

This pass sharpens the durable rule that:

- ATLAS root should optimize operator routing speed when receipts are already strong
- front-page marker space is scarce and should be reserved for active steering instruments
- supporting markers remain durable follow-up surfaces, not deleted context

## What This Pass Explicitly Does Not Mean

This pass does not mean:

- supporting markers are unimportant
- cluster reads are replacing individual markers
- cleaner scanning is permission for softer ratchet discipline
- a smaller front page changes any lane value or gate

## Exact Next Package

`Atlas-owned Repo Naming bounded rewrite-order and rollback planning pass 1`

Why:

- the naming lane now has policy, gates, dependency mapping, and a durable no-safe-first decision
- the next real blocker is exact bounded rewrite and rollback order
- that is still the best high-leverage root governance move after marker hygiene

## Rule

Marker hygiene should reduce operator scan time without hiding still-important markers or silently changing marker semantics.

## Pattern

split active vs supporting vs closed -> keep cluster reads explicit -> cap front-page markers to the smallest useful steering set -> preserve all historical ratchets and values

## Failure Mode

A hygiene pass makes the page cleaner by quietly burying still-important open markers or by implying hidden numerical consolidation.
