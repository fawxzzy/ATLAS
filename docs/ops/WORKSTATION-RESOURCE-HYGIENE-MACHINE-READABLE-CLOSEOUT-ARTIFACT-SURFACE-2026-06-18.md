# Workstation Resource Hygiene Machine-Readable Closeout Artifact Surface - 2026-06-18

- Date: `2026-06-18`
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
  - `docs/ops/WORKSTATION-RESOURCE-HYGIENE-MACHINE-READABLE-RESIDUE-SUMMARY-SURFACE-2026-06-17.md`
  - `ops/atlas/workstation_resource_snapshot.ps1`
  - `tests/test_atlas_workstation_resource_snapshot.py`
- Control-plane checkpoint: `main@feccf60a`

## Objective

Advance the lane from one machine-readable residue summary to one machine-readable closeout artifact that binds the required closeout fields to the bounded residue summary without exposing machine-private paths.

## Implementation

`ops/atlas/workstation_resource_snapshot.ps1` now supports one bounded `-JsonCloseout` mode.

That mode emits:

- contract version `atlas.workstation_resource_closeout.v1`
- one explicit `closeout` object with:
  - `closeout_fields_version`
  - `processes_started`
  - `processes_still_running`
  - `dev_server_status`
  - `browser_playwright_status`
  - `watch_test_status`
  - `stop_commands_run`
  - `anything_left_intentionally_running`
  - `next_chat_service_action`
  - `next_chat_service_note`
- one nested `residue_summary` object that preserves the existing bounded `atlas.workstation_resource_snapshot.summary.v1` surface

Guardrails:

- `-JsonCloseout` cannot be combined with `-JsonSummary`
- JSON output modes cannot be combined with `-IncludePath`
- `-JsonCloseout` fails closed unless:
  - `-DevServerStatus`
  - `-BrowserPlaywrightStatus`
  - `-WatchTestStatus`
  are all provided

This keeps the artifact useful for later governed closeout consumption without letting the machine-readable surface drift into path leakage or half-filled status stubs.

## Proof

Machine-readable closeout proof command:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonCloseout -WorkflowOnly -Top 5 -ProcessesStarted codex -ProcessesStillRunning none -DevServerStatus not-run-in-this-pass -BrowserPlaywrightStatus not-run-in-this-pass -WatchTestStatus not-run-in-this-pass -StopCommandsRun none -AnythingLeftIntentionallyRunning none -NextChatServiceAction restart -NextChatServiceNote "restart services only if needed"`

Sanitized live read from that proof:

- `closeout.contract_version: atlas.workstation_resource_closeout.v1`
- `closeout.processes_started: [codex]`
- `closeout.next_chat_service_action: restart`
- `residue_summary.include_path: false`
- `residue_summary.workflow_process_count: 5`
- `residue_summary.distinct_workflow_names: 2`
- `residue_summary.workflow_working_set_mb: 1271.2`
- `residue_summary.workflow_names: codex(4), msedge(1)`

Privacy-boundary proof command:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonCloseout -IncludePath -DevServerStatus stopped -BrowserPlaywrightStatus stopped -WatchTestStatus stopped`

Result:

- fails closed with the explicit `JSON output modes cannot be combined with -IncludePath` guard

Required-field proof:

- `-JsonCloseout` returns non-zero when one of the required status fields is omitted

Automated proof:

- `python -m unittest tests.test_atlas_workstation_resource_snapshot -v`

Coverage:

- JSON closeout output parses and carries the expected closeout plus nested residue-summary contracts
- workflow-only closeout output omits top CPU and top memory sections inside the nested residue summary
- JSON process records in the nested residue summary do not expose `path`
- the privacy guard returns non-zero when `-JsonCloseout` is combined with `-IncludePath`
- the closeout mode fails closed when required status fields are missing

## Marker Movement

- `Workstation Resource Hygiene` moves from `50%` to `85%`

Why `85%` is honest:

- the lane now has one durable machine-readable closeout artifact instead of one machine-readable residue summary only
- the required closeout contract fields now travel in the same governed artifact as the bounded residue summary
- the privacy boundary remains explicit and test-backed
- later closeouts can now emit one structured governed closeout result instead of stitching prose plus separate residue reads by hand

Why the lane still stops here:

- no preserved before/after relief cycle proves actual resource-pressure reduction yet
- no repeated real-chat adoption proof exists yet across later closeouts
- the helper remains read-only and does not itself enforce cleanup

## Exact Next Honest Move

- `100%`: at least one preserved relief cycle plus repeated real-chat closeout use prove the artifact is not only well-formed but actually used to reduce and report local residue safely

## Non-Goals

- no process termination
- no service mutation
- no secret inspection
- no committed raw machine-private logs
- no automatic cleanup policy

## Validation

Commands:

- `python -m unittest tests.test_atlas_workstation_resource_snapshot -v`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonCloseout -WorkflowOnly -Top 5 -ProcessesStarted codex -ProcessesStillRunning none -DevServerStatus not-run-in-this-pass -BrowserPlaywrightStatus not-run-in-this-pass -WatchTestStatus not-run-in-this-pass -StopCommandsRun none -AnythingLeftIntentionallyRunning none -NextChatServiceAction restart -NextChatServiceNote "restart services only if needed"`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -JsonCloseout -IncludePath -DevServerStatus stopped -BrowserPlaywrightStatus stopped -WatchTestStatus stopped`

Result:

- workstation helper test suite passed
- sanitized machine-readable closeout artifact emitted successfully
- path-bearing JSON closeout mode failed closed as designed
