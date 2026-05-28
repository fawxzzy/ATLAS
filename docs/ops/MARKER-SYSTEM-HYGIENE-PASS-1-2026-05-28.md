# Marker System Hygiene Pass 1 - 2026-05-28

- Date: `2026-05-28`
- Lane: `ATLAS marker-system hygiene`
- Mode: `docs-only control-plane read-model hygiene`
- Source surfaces:
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main@e927008`

## Objective

Reduce marker sprawl and overlapping interpretation without changing any underlying marker values or hidden lane scope.

This pass does not:

- add implementation work
- change owner-repo truth
- create a new execution lane
- change any marker percentages
- delete any historical ratchet
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `e927008`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Why This Pass Exists

The marker system is no longer blocked by missing receipts.

It is now slowed by:

- front-page marker sprawl
- overlapping interpretation across closely related markers
- too many closed or nearly-closed ratchets sharing the same first-scan space as current steering instruments
- repeated ratchet reads on surfaces that no longer change operator action

This pass is read-model hygiene only.

## Decisions Frozen In This Pass

### 1. Split active markers from closed markers

`02-lanes-and-markers.md` now separates:

- `Active Front-Page Marker Table`
- `Supporting Open Markers`
- `Closed / Locked Ratchets`

Closed ratchets remain durable and visible.

They are no longer part of the first operator scan.

### 2. Add cluster-first reading

The marker surface now begins with four cluster reads:

- continuity substrate
- execution substrate
- Discord workflow
- naming / ownership hygiene

This preserves precision while reducing mental bucket count.

### 3. Preserve all percentages

This pass changes no marker values.

It changes only how the operator should scan them.

### 4. Preserve historical ratchets

No marker was deleted.

Closed ratchets remain on the page because they still matter for:

- historical boundary interpretation
- restart truth
- governance memory

They are simply no longer front-page active.

### 5. Do not admit a new anti-drift marker yet

Candidate considered:

- `Root Projection Boundary Hygiene`

Decision:

- not admitted in this pass

Why:

- the anti-monolith posture is already well expressed as doctrine
- a new marker would add control-plane weight before existing marker hygiene is fully absorbed

## Active Front-Page Marker Set Frozen

The front-page set is now intentionally limited to the markers that still change operator routing most directly:

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
- `Discord Workflow, Publication & Docs Reliability`
- `Playbook Everywhere + Cortex Interface`
- `AI Repetition-to-Automation Pipeline`
- `AI Long-Run Batch Orchestration`

## Closed / Locked Ratchets Frozen

The following are explicitly preserved as durable but no longer front-page active:

- `Archive Normalization`
- `Foundation Alignment`
- `Fitness Source-of-Truth Reset`
- `Canonical Repo Restoration`
- `Branch & Worktree Normalization`
- `Fitness Supabase Profile/Data Hygiene`
- `Full Stack Re-sync, Clean & Closeout`

## Supporting Open Markers

Remaining open markers that still matter, but are not currently first-scan instruments, stay under `Supporting Open Markers`.

This preserves:

- visibility
- restart truth
- lane-specific follow-up value

without forcing every scan to treat them as current top-priority routing signals.

## Restart Surface Changes

`12-restart-and-handoff-guide.md` now freezes:

- a stronger first-check preflight
- a marker-scan order that starts with active cluster/front-page surfaces
- the rule that closed ratchets should not dominate first-scan attention
- a refreshed current docs/control-plane ladder after the latest durable state

## Vision Surface Changes

`13-vision-and-endgames.md` now freezes that:

- read-model hygiene is legitimate ATLAS-systems work when control-plane speed becomes the bottleneck
- ATLAS Book / Publishing work still matters when it materially improves operator routing and restart truth
- control-plane overhead itself can become a blocker even when receipts are already durable

## What This Pass Explicitly Does Not Mean

This pass does not mean:

- the removed front-page markers are unimportant
- closed ratchets should be forgotten
- marker clustering is a hidden numerical merge
- cleaner scanning is permission for looser ratchet standards

## Ratchet Discipline Frozen

The intended operator pattern from here is:

- proof or inventory passes
- one cluster-aware ratchet pass
- one marker-surface refresh only when needed

Not:

- one micro receipt
- one micro ratchet
- one micro surface refresh

when operator reality has not materially changed.

## Exact Next Package

`Atlas-owned Repo Naming bounded rewrite-order and rollback planning pass 1`

Why:

- naming execution is still blocked
- the next highest-leverage root move is freezing exact bounded rewrite order and rollback order
- that lane benefits directly from the cleaner active-marker read model created here

## Rule

Read-model hygiene must improve operator scan speed without hiding scope change, deleting history, or faking marker convergence.

## Pattern

durable receipts accumulate -> front-page marker sprawl appears -> split active vs supporting vs closed -> add cluster reads -> tighten restart scan order -> keep numerical markers unchanged

## Failure Mode

A marker hygiene pass quietly changes lane scope or marker meaning under the banner of readability.
