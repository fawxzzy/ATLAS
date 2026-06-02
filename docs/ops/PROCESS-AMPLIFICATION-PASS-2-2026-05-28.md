# Process Amplification Pass 2 - 2026-05-28

- Date: `2026-05-28`
- Lane: `ATLAS process amplification`
- Mode: `docs-only process / doctrine / execution-cadence work`
- Source surfaces:
  - `AGENTS.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/03-operating-model.md`
  - `docs/atlas-book/08-workflow-recipes.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/PROCESS-AMPLIFICATION-PASS-1-2026-05-28.md`

## Objective

Freeze a stricter execution cadence so ATLAS root stops paying repeated blocked-retry tax after a blocker class is already durable.

This pass does not:

- mutate repo code
- reopen the naming lane
- change any marker value
- change approval gates
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status before drafting: intentional untracked `archive/` only

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=311`

## Why This Pass Exists

The slowest recent failure mode was not missing architecture.

It was control-plane repetition after a blocker had already moved into owner-repo execution reality:

- blocked execution at root
- blocked proof or blocker recheck at root
- hold-flat ratchet
- another root retry anyway

That loop spends time without changing the blocker class.

## Decisions Frozen In This Pass

### 1. Two-strike blocker rule

For one blocker class:

- one blocked execution receipt is allowed
- one blocked proof or blocker-recheck receipt is allowed

After that, root is done.

Only owner-side blocker conversion work is allowed until the blocker class materially changes.

### 2. No duplicate package rule

Before any prompt or pass runs:

- check whether the exact receipt already exists durably
- if yes, do not rerun it
- open a new pass only when state changed or scope changed

### 3. Cluster execution rule

For execution-ready lanes, run this serial cluster:

1. execution
2. proof or reconciliation
3. ratchet

Do not interleave unrelated root lanes between those steps unless execution becomes blocked.

### 4. One root writer rule

At any moment:

- one root writer
- one owner-repo writer
- one optional read-only scout

This is now the default stack speed limit for write coordination.

### 5. Marker ratchet threshold

A marker only moves when one of these changed:

- executed state changed
- proof-backed adoption widened
- manifest-backed restart got broader and stayed refreshed
- one real blocker was cleared

Cleaner language alone is not enough.

## Batch Routing Frozen

### Batch A: owner-side unblock batch

Use when the blocker is real repo work:

- convert blocker
- merge or preserve or archive
- recheck blocker class

### Batch B: root execution cluster

Use only after Batch A succeeds or when no owner-side blocker exists:

- blocker recheck if needed
- execution
- proof or reconciliation
- marker ratchet

### Batch C: root read-model or doctrine batch

Use only when there is no executable owner-side work ready.

## Canonical Operator Read

Root remains:

- governance
- projection
- receipts

Owner repos remain:

- real code
- blocker conversion
- proof generation for repo-owned work

Rule:

- do not let root keep narrating a blocker that now belongs to an owner repo

## What This Pass Explicitly Does Not Mean

This pass does not mean:

- historical receipts should be rewritten
- root should stop recording genuine cross-repo consequence
- every blocked lane needs a new process document
- owner-side cleanup should widen beyond the smallest blocker slice

## Exact Next Package

Adopt this cadence as the default restart and execution rule set across ATLAS-root governance work.

Why:

- the rules are only valuable if they become the first read-model for future root work

## Rule

Once a blocker class is durable, root stops retrying and waits for owner-side class change.

## Pattern

blocked execution -> blocked proof or blocker recheck -> owner-side blocker conversion -> class change -> execution cluster -> proof -> ratchet

## Failure Mode

Root keeps opening new receipts for a blocker that only an owner repo can actually clear.
