# Workstation Resource Hygiene Paste-Ready Markdown Closeout Surface - 2026-06-18

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
  - `docs/ops/WORKSTATION-RESOURCE-HYGIENE-MACHINE-READABLE-RESIDUE-SUMMARY-SURFACE-2026-06-17.md`
  - `docs/ops/WORKSTATION-RESOURCE-HYGIENE-MACHINE-READABLE-CLOSEOUT-ARTIFACT-SURFACE-2026-06-18.md`
  - `ops/atlas/workstation_resource_snapshot.ps1`
  - `tests/test_atlas_workstation_resource_snapshot.py`
- Control-plane checkpoint: `main@7da1fd52`

## Objective

Reduce one remaining manual adoption seam after the machine-readable closeout artifact landed.

Before this pass, the helper could already emit one governed JSON closeout artifact, but a real chat closeout still required the operator to manually restate the exact contract headings or hand-translate the JSON artifact into paste-ready handoff text.

## What Landed

`ops/atlas/workstation_resource_snapshot.ps1` now supports one bounded `-MarkdownCloseout` mode.

That mode:

- renders the exact governed closeout headings already required by the restart guide:
  - `Processes started`
  - `Processes still running`
  - `Dev server status`
  - `Browser/Playwright status`
  - `Watch/test status`
  - `Stop commands run`
  - `Anything left intentionally running`
  - `Should the next chat inherit or restart local services`
  - `Next chat service note`
- appends the same sanitized residue summary already governed by `atlas.workstation_resource_snapshot.summary.v1`
- appends the same review guidance already carried by the summary surface
- stays path-safe and share-safe by rejecting `-IncludePath`
- fails closed on the same required status fields as `-JsonCloseout`

This keeps the helper read-only while making the governed closeout contract directly usable in real chat closeouts without forcing one extra manual translation step from JSON to handoff prose.

## Proof

Paste-ready closeout proof command:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -MarkdownCloseout -WorkflowOnly -Top 5 -ProcessesStarted codex -ProcessesStillRunning none -DevServerStatus stopped -BrowserPlaywrightStatus stopped -WatchTestStatus stopped -StopCommandsRun "Stop-Process codex" -AnythingLeftIntentionallyRunning none -NextChatServiceAction restart -NextChatServiceNote "restart services only if needed"`

Sanitized live read from that proof:

- heading: `# Workstation Closeout`
- closeout contract section present
- `Processes started: codex`
- `Browser/Playwright status: stopped`
- `Should the next chat inherit or restart local services: restart`
- residue summary contract: `atlas.workstation_resource_snapshot.summary.v1`
- workflow names: `codex(4), msedge(1)`

Privacy-boundary proof command:

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -MarkdownCloseout -IncludePath -DevServerStatus stopped -BrowserPlaywrightStatus stopped -WatchTestStatus stopped`

Result:

- fails closed with the explicit `cannot be combined with -IncludePath` guard

Required-field proof:

- `-MarkdownCloseout` returns non-zero when one of the required status fields is omitted

Automated proof:

- `python -m unittest tests.test_atlas_workstation_resource_snapshot -v`

Coverage:

- markdown closeout output includes the governed closeout section and sanitized residue summary
- markdown closeout stays privacy-bounded
- markdown closeout fails closed when required status fields are missing
- existing JSON summary and JSON closeout behavior remain green

## Marker Movement

- `Workstation Resource Hygiene` stays at `85%`

Why the marker stays flat:

- this is a real operator-surface improvement, but it is still adoption enablement rather than repeated real-chat adoption proof
- no preserved relief cycle proves actual resource-pressure reduction yet
- no repeated later closeouts are preserved yet using the governed closeout surface

Why the pass is still useful:

- the helper no longer stops at a machine-readable artifact only
- one exact paste-ready governed closeout surface now exists for handoff use
- the remaining blocker is narrower and more honest: preserved repeated use rather than missing shape or missing safety guards

## Non-Goals

- no process termination policy
- no service mutation
- no automatic artifact writing
- no secret inspection
- no committed raw machine-private logs

## Validation

Commands:

- `python -m unittest tests.test_atlas_workstation_resource_snapshot -v`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -MarkdownCloseout -WorkflowOnly -Top 5 -ProcessesStarted codex -ProcessesStillRunning none -DevServerStatus stopped -BrowserPlaywrightStatus stopped -WatchTestStatus stopped -StopCommandsRun "Stop-Process codex" -AnythingLeftIntentionallyRunning none -NextChatServiceAction restart -NextChatServiceNote "restart services only if needed"`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\atlas\workstation_resource_snapshot.ps1 -MarkdownCloseout -IncludePath -DevServerStatus stopped -BrowserPlaywrightStatus stopped -WatchTestStatus stopped`

Result:

- workstation helper test suite passed
- paste-ready governed markdown closeout emitted successfully
- path-bearing markdown closeout mode failed closed as designed
