# Workstation Resource Hygiene Replay And Snapshot Helper Hardening - 2026-06-17

- Date: `2026-06-17`
- Lane: `Workstation Resource Hygiene`
- Owner: `ATLAS/root`
- Mode: `root support-lane replay plus helper hardening`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/WORKSTATION-RESOURCE-HYGIENE-BASELINE-AND-CODEX-QALLL-CLOSEOUT-CONTRACT-PASS-1-2026-06-11.md`
  - `ops/atlas/workstation_resource_snapshot.ps1`
- Control-plane checkpoint: `main@7079e83d`

## Objective

Advance the workstation hygiene lane with real later-session evidence instead of baseline-only narration:

1. replay the helper in a later session
2. harden the helper where the replay exposes a real defect
3. preserve a sanitized closeout read without committing raw machine-private output

## Replay Findings

The helper was replayed in two modes:

- `-WorkflowOnly`
- default full snapshot mode

The first replay showed:

- `-WorkflowOnly` succeeded
- the default full snapshot mode failed on the `Top CPU processes` path because `Sort-Object CPU` was not fail-safe across all returned process objects

That means the baseline helper was useful, but not yet durable enough for the fuller closeout check it claimed to support.

## Helper Hardening

`ops/atlas/workstation_resource_snapshot.ps1` now:

- uses guarded CPU and working-set accessors instead of assuming every process sorts cleanly by raw `CPU`
- uses those guarded accessors for workflow sorting, top CPU sorting, and top memory sorting
- emits a compact `Workflow summary` section before the raw workflow table

The new summary keeps the helper read-only and privacy-bounded:

- workflow process count
- distinct workflow names
- total workflow working set in MB
- grouped workflow process names with counts

No process paths are included unless `-IncludePath` is explicitly requested.

## Post-Fix Sanitized Snapshot Read

After hardening, both replay modes succeeded.

Sanitized later-session read:

- workflow process count: `10`
- distinct workflow names: `3`
- workflow names seen: `codex`, `msedge`, `node`
- workflow working set: about `1791.9 MB`

This is enough to prove the lane is about real local operator pressure rather than abstract etiquette: multiple Codex and browser processes can accumulate quickly even when only one chat is supposed to stay hot.

## Marker Movement

- `Workstation Resource Hygiene` moves from `10%` to `22%`

Why `22%` is honest:

- the helper was replayed in a later session
- the replay exposed a real defect
- the helper was hardened and rerun successfully in both modes
- the lane now has one better reusable operator surface, not just a baseline rule

Why the lane stays low:

- no broader cross-lane adoption proof exists yet
- no machine-readable closeout hook exists yet
- no preserved reduction cycle proves resource pressure actually dropped after intervention
- no multi-session trend or relief history exists yet

## Exact Next Honest Moves

- `35%`: two or more later lane closeouts explicitly use the hygiene contract and sanitized helper read
- `50%`: one bounded machine-readable closeout or residue-summary surface exists without exposing machine-private paths
- `65%`: at least one preserved relief cycle proves the helper led to a real resource-pressure reduction

## Non-Goals

- no process termination
- no service mutation
- no secret inspection
- no committed raw machine-private logs
- no automatic cleanup policy

## Validation

Commands:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -WorkflowOnly`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1`

Result:

- both commands now succeed after the helper hardening
