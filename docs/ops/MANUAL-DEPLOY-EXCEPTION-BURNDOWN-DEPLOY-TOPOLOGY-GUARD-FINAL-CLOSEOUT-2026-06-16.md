# Manual Deploy Exception Burn-Down Deploy Topology Guard Final Closeout - 2026-06-16

- Date: `2026-06-16`
- Lane: `Manual Deploy Exception Burn-Down`
- Owner: `ATLAS/root`
- Mode: `final bounded closeout`
- Supersedes as final blocker receipt:
  - `docs/ops/MANUAL-DEPLOY-EXCEPTION-BURNDOWN-CHECKPOINT-2026-05-24.md`
  - `docs/ops/REMAINING-CLOSEOUT-QUEUE-RESELECTION-AFTER-DUPLICATE-SURFACE-CLOSEOUT-2026-06-13.md`
- Source surfaces:
  - `docs/ops/MANUAL-DEPLOY-EXCEPTION-BURNDOWN-CHECKPOINT-2026-05-24.md`
  - `docs/ops/REDUCED-NEAR-100-MARKER-CLOSEOUT-SELECTOR-AFTER-BRAND-CLOSEOUT-2026-06-12.md`
  - `docs/ops/REMAINING-CLOSEOUT-QUEUE-RESELECTION-AFTER-DUPLICATE-SURFACE-CLOSEOUT-2026-06-13.md`
  - `repos/_stack/package.json`
  - `repos/_stack/workspace.manifest.json`
  - `repos/_stack/README.md`
  - `repos/_stack/docs/dispatcher-protocol.md`
  - `repos/_stack/docs/fitness-verify.md`
  - `repos/_stack/docs/ops/fitness-vercel-deploy-recovery.md`
  - `repos/_stack/ops/Test-FitnessDeployLink.ps1`
  - `repos/_stack/ops/Test-TroveDeployLink.ps1`
  - `repos/_stack/ops/Test-MazerDeployLink.ps1`
  - `repos/_stack/ops/Test-MazerDeployIdentity.ps1`
  - `repos/_stack/ops/Invoke-MazerDeploy.ps1`
  - `repos/_stack/ops/codex/Test-StackOperatorSurface.ps1`
  - live verification commands in `repos/_stack`
  - `python ops/validation/validate_stack.py --ratchet`

## Objective

Clear the last exact blocker holding `Manual Deploy Exception Burn-Down` below completion:

- remove stale deploy-topology assumptions from governed `_stack` deploy surfaces
- prove Fitness deploy authority admits the current canonical workspace layout
- prove Trove and Mazer fail closed from the canonical repo paths rather than from stale or `tmp` checkouts
- prove active governed deploy, QA, and recovery surfaces no longer re-enter any `tmp` checkout

## Executed Owner-Side Closeout

The decisive mutation landed in `repos/_stack` and is already durable upstream:

- branch: `codex/queue-or-registry-broader-execution-behavior`
- commit: `e4fcd7c`
- subject: `Fix deploy topology guards`
- parity proof: `git -C repos/_stack rev-list --left-right --count origin/codex/queue-or-registry-broader-execution-behavior...HEAD` returned `0 0`

This closeout does not depend on unpublished local `_stack` drift.

## Governed Deploy-Topology Proof

### Trove and Mazer now target the canonical repos

Governed `_stack` deploy surfaces no longer point at stale renamed paths:

- Trove defaults now resolve to `repos/trove`
- Mazer defaults now resolve to `repos/mazer`
- stale `fawxzzy-trove` and `fawxzzy-mazer` path assumptions were removed from governed package, manifest, wrapper, and runbook surfaces

### Fitness now admits the current canonical workspace topology

The Fitness deploy-link preflight no longer requires `repos/fawxzzy-fitness` to be an independent git toplevel.

It now admits either:

- a standalone `repos/fawxzzy-fitness` clone, or
- the canonical ATLAS-rooted workspace layout where `repos/fawxzzy-fitness` lives under the shared ATLAS git toplevel

That is the exact topology in the live workspace, so current governed Fitness deploy authority no longer depends on an outdated repo-boundary model.

## Verification Proof

These live `_stack` verification commands were rerun against the current workspace:

- `pnpm run fitness:deploy:preflight`
- `pnpm run trove:deploy:preflight`
- `pnpm run mazer:deploy:preflight`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\Test-StackOperatorSurface.ps1`
- `git diff --check`

Current result set:

- Fitness preflight passes from the canonical repo path and reports pinned Vercel project `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- Fitness preflight also reports `Git auto-deploy createDeployments: disabled`
- Trove preflight no longer fails on stale path drift; it now fails closed only because local `repos/trove/.vercel/project.json` is absent
- Mazer preflight no longer fails on stale path drift; it now fails closed only because local `repos/mazer/.vercel/project.json` is absent
- `_stack` operator-surface proof now accepts that fail-closed Mazer relink state as valid governed behavior
- `git diff --check` passes in `repos/_stack`

## No-`tmp` Re-entry Proof

The old selector receipts held this lane open because root truth did not yet prove that governed manual deploy, QA, and recovery surfaces had stopped re-entering `tmp` checkouts.

That proof now exists:

- active governed `_stack` package, manifest, wrapper, and operator-surface files point at canonical repo paths only
- active deploy and recovery docs now match those canonical repo paths
- the live governed Fitness deploy path works from `repos/fawxzzy-fitness`, not from a retained `tmp` checkout
- Trove and Mazer governed preflights now fail closed from `repos/trove` and `repos/mazer`, not from stale renamed directories or `tmp` mirrors

Residual `tmp` references are now limited to historical receipts, test fixtures, or runtime captures rather than active governed deploy authority.

## Why The Lane Closes At `100%`

The old blocker was no longer "someone still needs to run manual relink work."

The real blocker was:

- governed `_stack` deploy surfaces still encoded stale repo-topology assumptions, and
- root truth still lacked proof that active governed manual deploy, QA, and recovery surfaces no longer re-entered `tmp`

Those exact blockers are now cleared:

- governed deploy authority is again rooted in the current canonical repo topology
- Fitness deploy authority admits the current workspace boundary model
- Trove and Mazer fail closed for the right reason from the right paths
- active governed deploy, QA, and recovery surfaces no longer depend on `tmp` repo checkouts

## Validation Posture

`python ops/validation/validate_stack.py --ratchet` now reports:

- `critical=0`
- `error=0`
- `warning=3`

These warnings remain inherited non-blocking residue outside this lane's closeout claim:

- `repos/fawxzzy-fitness`: nested child-repo pinning warning
- `repos/fawxzzy-fitness/.vercel`: mutable local-state warning
- `repos/_stack/ops/codex/Test-StackOperatorSurface.ps1`: inherited absolute-path leak warning

## Marker Decision

- `Manual Deploy Exception Burn-Down`: `84% -> 100%`

## Non-Claim Boundary

- this pass does not relink Trove or Mazer locally
- this pass does not mutate any Vercel linkage, secrets, or deploy settings
- this pass does not perform a deploy
- this pass does not claim every historical `tmp` mention must be deleted from old receipts
- this pass does not reopen publication, release-ledger, or preview-surface lanes

## Exact Next Move

- none for `Manual Deploy Exception Burn-Down`
- future deploy mutations, relink work, or publication-facing proof should route to their owning lanes rather than reopening this closed marker
