# ATLAS System Guardian

ATLAS System Guardian is a Windows-only, root-owned operator lane for safe background process review and cleanup.

It is policy-driven, dry-run-first, and biased toward visibility before action.

## Scope

- root-owned surface under `ops/scripts/system-guardian/`
- runtime state under `runtime/atlas/system-guardian/`
- no repo-local mutation
- no surprise process termination

This keeps the lane aligned with `stack.yaml` and the ATLAS root path policy without introducing a new top-level `config/` surface.

## Entry Points

Run from `C:\ATLAS`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\install-system-guardian.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\uninstall-system-guardian.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\system-guardian-status.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\system-guardian-run.ps1 -DryRun
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\system-guardian-run.ps1 -Apply
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\system-guardian-switch-profile.ps1 -Name focus
```

Extra control surfaces:

- `system-guardian-kill-switch.ps1 -Disable|-Enable`
- `system-guardian-rollback.ps1`

## Architecture

The lane has four control layers:

1. Policy: `ops/scripts/system-guardian/system-guardian.policy.json`
2. Entry points: install, uninstall, status, run, profile switch, kill switch, rollback
3. Runtime state: profile state, breach counters, last run, rollback snapshot
4. Scheduler: a lightweight Task Scheduler registration that runs only in the interactive user session

The installed scheduled task always invokes the run surface with `-Apply`.

That does not mean it always kills processes. Actual behavior is still gated by:

- the active profile mode
- rule action
- repeated-breach thresholds
- browser safety rules
- the global kill switch

Default posture:

- `normal` profile is `observe`
- `focus` and `stream` are `notify`
- `build` is the only shipped `cleanup` profile

## Policy Fields

`system-guardian.policy.json` defines:

- `defaults.profile`: default active profile
- `defaults.mode`: fallback mode if a profile omits one
- `defaults.thresholds`: shared thresholds for working set, CPU, age, and repeated breaches
- `defaults.scheduledTask`: task name and repetition interval
- `protected.processNames`: hard skip list
- `protected.commandLineContains`: skip patterns for sensitive commands
- `protected.browserProcessNames`: browser family list used for extra cleanup guards
- `profiles.*`: profile-specific mode and threshold overrides
- `candidates[*]`: candidate rule list

Candidate rules support:

- `id`
- `description`
- `processNames`
- `commandLineContains`
- `defaultAction`
- `cleanupAllowed`
- `browserCleanupAllowed`
- `requireNoMainWindow`
- `thresholds.workingSetMb`
- `thresholds.cpuSeconds`
- `thresholds.ageMinutes`
- `thresholds.repeatedBreaches`

## Protected Vs Candidate Rules

Protected rules always win.

Examples of protected defaults:

- shell and editor session surfaces that should never be auto-cleaned by this lane
- Codex-linked commands
- the guardian process itself

Candidate rules are review or cleanup targets only after they cross the configured thresholds.

Shipped examples:

- browsers: notify-only by default
- communication clients: review-only by default
- launcher/background helpers: cleanup candidates only in cleanup mode and only when headless
- safe test marker: explicit command-line marker for apply-mode verification

## Modes

- `observe`: log only
- `notify`: log and surface cleanup recommendations, but do not terminate
- `cleanup`: allow termination for cleanup-enabled rules that cross the repeated-breach gate

The run surface still distinguishes `-DryRun` from `-Apply`.

- `-DryRun` never terminates anything
- `-Apply` only terminates in effective cleanup mode

## Scheduled Task Lifecycle

`install-system-guardian.ps1` registers a repeating interactive task with Task Scheduler.

Current lifecycle:

- runs on a repeating interval while the user session is active
- uses the current policy path
- writes JSON logs and text summaries into `runtime/atlas/system-guardian/`
- can be removed cleanly with `uninstall-system-guardian.ps1`

`system-guardian-status.ps1` reports:

- active profile
- kill-switch state
- policy path
- runtime root
- scheduled-task state
- latest run summary

## Logs And Runtime State

Runtime files stay out of repo roots and are intentionally untracked.

Current state surfaces:

- `runtime/atlas/system-guardian/state/active-profile.json`
- `runtime/atlas/system-guardian/state/breaches.json`
- `runtime/atlas/system-guardian/state/latest-run.json`
- `runtime/atlas/system-guardian/state/rollback-latest.json`
- `runtime/atlas/system-guardian/state/disabled.flag`
- `runtime/atlas/system-guardian/logs/run-*.json`
- `runtime/atlas/system-guardian/reports/run-*.txt`

## Rollback And Emergency Disable

The kill switch is the emergency stop.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\system-guardian\system-guardian-kill-switch.ps1 -Disable
```

Rollback restores the most recent control-plane snapshot:

- active profile
- kill-switch state
- scheduled-task install state

Rollback does not restart processes that were already terminated. Process cleanup is intentionally one-way.

## Manual Cleanup Checklist

Use this before enabling cleanup on a new profile:

1. Run `system-guardian-run.ps1 -DryRun`.
2. Review `latest-run.json` and the matching text report.
3. Confirm protected processes were skipped.
4. Confirm browsers stayed notify-only unless policy explicitly allows headless cleanup.
5. Verify the candidate rule list matches the machine’s real background profile.
6. Switch to a cleanup-capable profile only after the dry-run output looks sane.
