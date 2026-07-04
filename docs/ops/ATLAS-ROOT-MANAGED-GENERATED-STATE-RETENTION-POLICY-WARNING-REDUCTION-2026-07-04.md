# ATLAS Root Managed Generated-State Retention Policy Warning Reduction

Date: 2026-07-04

## Purpose

Reduce root validation warning noise without deleting generated dependency or build state and without touching Mazer or Fitness owner-lane work.

## Decision

ATLAS root now classifies three managed generated-state folders as retained policy surfaces:

- `_stack`: `node_modules` retained as `active_dependency_install`
- `playbook`: `dist` retained as `generated_build_output`
- `foundation`: `node_modules` retained as `active_dependency_install`

This is a validation-policy clarification, not a source mutation in those repos.

## Boundary

No Mazer files were edited.

No Fitness files were edited.

No generated dependency/build directories were deleted.

The cleanup wrapper writes non-committed runtime reports under `runtime/state/repo-cleanup/**` and uses `suppress_validation_warning: true` only for explicitly retained paths.

## Proof

Command:

```powershell
python ops/validation/validate_stack.py
```

Observed result after the policy update and `_stack` mainline resync:

```text
critical=0 error=0 warning=17 info=0
```

The pass suppresses three managed generated-state warnings that otherwise came from retained dependency/build state:

- `_stack/node_modules`
- `playbook/dist`
- `foundation/node_modules`

The remaining `17` warnings are inherited path/mutable-state warning-floor items:

- `repos/mazer/.playbook`
- `repos/mazer/.vercel`
- `repos/mazer/node_modules`
- `repos/mazer/dist`
- six committed absolute-path references in Mazer docs
- seven committed absolute-path references in `_stack` receipts/docs

## Marker Decision

No marker moves from this pass.

The pass reduces validation noise and improves owner-lane separation, but it does not widen adoption, land a new automation family, or clear the active Sandbox hold.

## Next

Keep Mazer warning cleanup inside the Mazer owner lane.

Keep future generated-state cleanup for trusted repos policy-backed through `stack.yaml` plus `runtime/state/repo-cleanup/**` reports.
