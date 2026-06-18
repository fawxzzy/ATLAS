# Workstation Resource Hygiene Machine-Readable Residue Summary Surface - 2026-06-17

- Date: `2026-06-17`
- Lane: `Workstation Resource Hygiene`
- Owner: `ATLAS/root`
- Mode: `root support-lane helper extension plus proof`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/WORKSTATION-RESOURCE-HYGIENE-BASELINE-AND-CODEX-QALLL-CLOSEOUT-CONTRACT-PASS-1-2026-06-11.md`
  - `docs/ops/WORKSTATION-RESOURCE-HYGIENE-REPLAY-AND-SNAPSHOT-HELPER-HARDENING-2026-06-17.md`
  - `ops/atlas/workstation_resource_snapshot.ps1`
  - `tests/test_atlas_workstation_resource_snapshot.py`
- Control-plane checkpoint: `main@d915a021`

## Objective

Advance the lane from replay-only helper hardening to one durable machine-readable residue-summary surface that later closeouts can consume without exposing machine-private paths.

## Implementation

`ops/atlas/workstation_resource_snapshot.ps1` now supports one bounded `-JsonSummary` mode.

That mode:

- emits contract version `atlas.workstation_resource_snapshot.summary.v1`
- preserves the existing read-only posture
- keeps `include_path` fixed to `false`
- emits one structured `workflow_summary`
- emits bounded `workflow_processes`
- emits `top_cpu_processes` and `top_memory_processes` only when not using `-WorkflowOnly`
- preserves the same review guidance in machine-readable form

Privacy guard:

- `-JsonSummary` now fails closed when combined with `-IncludePath`
- this prevents a later closeout from accidentally turning the machine-readable surface into a committed path leak

## Proof

Machine-readable proof command:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonSummary -WorkflowOnly -Top 5`

Sanitized live read from that proof:

- `workflow_process_count: 5`
- `distinct_workflow_names: 2`
- `workflow_working_set_mb: 1284.5`
- `workflow_names: codex(4), msedge(1)`

Privacy-boundary proof command:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonSummary -IncludePath`

Result:

- fails closed with the explicit `cannot be combined with -IncludePath` guard

Automated proof:

- `python -m unittest tests.test_atlas_workstation_resource_snapshot -v`

Coverage:

- JSON summary parses and carries the expected bounded fields
- workflow-only JSON omits top CPU and top memory sections
- JSON process records do not expose `path`
- the privacy guard returns non-zero when `-JsonSummary` is combined with `-IncludePath`

## Marker Movement

- `Workstation Resource Hygiene` moves from `22%` to `50%`

Why `50%` is honest:

- the lane now has one bounded machine-readable residue-summary surface
- that surface is durable in the governed helper rather than chat-only narration
- the privacy boundary is explicit and test-backed
- later closeout adoption can now reference one reusable structured result instead of only prose

Why the lane still stops here:

- no broader later-closeout adoption proof exists yet
- no preserved before/after relief cycle proves actual resource-pressure reduction
- the helper remains read-only and does not itself enforce closeout compliance

## Exact Next Honest Moves

- `65%`: at least one preserved relief cycle proves the helper led to real resource-pressure reduction
- `75%`: two or more later lane closeouts explicitly cite the JSON summary surface or a derivative governed closeout artifact that consumes it
- `85%`: one durable machine-readable closeout artifact ties the required closeout fields to the bounded residue summary without widening into path or secret exposure

## Non-Goals

- no process termination
- no service mutation
- no secret inspection
- no committed raw machine-private logs
- no automatic cleanup policy

## Validation

Commands:

- `python -m unittest tests.test_atlas_workstation_resource_snapshot -v`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonSummary -WorkflowOnly -Top 5`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonSummary -IncludePath`

Result:

- test suite passed
- sanitized JSON summary emitted successfully
- path-bearing JSON mode failed closed as designed
