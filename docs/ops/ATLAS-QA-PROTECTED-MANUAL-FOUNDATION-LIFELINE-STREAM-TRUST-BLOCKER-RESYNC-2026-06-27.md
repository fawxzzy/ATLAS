# ATLAS QA Protected Manual Foundation Lifeline Stream Trust Blocker Re-Sync - 2026-06-27

- Date: `2026-06-27`
- Lane: `ATLAS QA trusted-origin conversion / read-model re-sync`
- Owner: `ATLAS/root`
- Mode: `owner-side unblock batch plus root execution cluster`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`
  - `ops/atlas/qa/release_policy.v1.json`
  - `ops/atlas/qa/_common.py`
  - `ops/atlas/qa/bootstrap_release_repos.py`
  - `ops/atlas/qa/protected_release_refresh.py`
  - `ops/atlas/qa/release_readiness.py`
  - `ops/atlas/qa/release_rehearsal.py`
  - `stack.lock.yaml`
  - `runtime/atlas/qa/bootstrap-release-repos.latest.json`
  - `runtime/atlas/qa/protected-release-refresh.latest.json`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `runtime/atlas/qa/release-rehearsal.latest.json`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@42656789`

## Objective

Convert the package-tier trusted-origin blocker where the current topology actually permits protected execution, then re-sync the root read model so the remaining blocker list stays truthful instead of overreporting `foundation` and `lifeline`.

## Execution

Owner-side unblock work landed first:

- `foundation` path and QA adoption repairs were verified with:
  - `pnpm build`
  - `pnpm verify:local`
  - commit `fd1cf06` on `main`
- `lifeline` QA path-contract repairs were verified with:
  - `pnpm install --frozen-lockfile`
  - `pnpm run verify`
  - commit `538f623` on `codex/path-discipline-warning-slice-lifeline`

Root-side protected refresh then executed:

- `python ops/stack/generate_lockfile.py`
- `python ops/atlas/qa/bootstrap_release_repos.py --repo foundation --repo lifeline`
- `$env:ATLAS_QA_ORIGIN_TYPE='protected_manual'`
- `python ops/atlas/qa/protected_release_refresh.py --repo foundation --repo lifeline --mode promotion --max-receipt-age-hours 168`

That produced fresh protected-manual receipts:

- `foundation-contract-smoke-20260627T073944280887Z`
- `lifeline-contract-smoke-20260627T074002700297Z`

After the bootstrap detached both repos to exact SHAs, the local branches were restored, the lockfile was regenerated, and stack validation was rerun so root truth matched the live workspace again.

Cleanup in the same pass removed regenerateable install/build residue from:

- `repos/foundation/node_modules`
- `repos/lifeline/node_modules`
- `repos/lifeline/dist`
- `repos/stream/node_modules`

## Read-Model Result

Current protected-QA truth is now:

- `foundation` is release-ready with `receipt_origin_type: protected_manual`
- `lifeline` is release-ready with `receipt_origin_type: protected_manual`
- `playbook` is release-ready
- `trove` is release-ready
- `fitness` is `manual_review` only, with the remaining release gate narrowed to `android.chrome.real` and `iphone.webkit.real`
- `stream` remains blocked by trusted-origin enforcement

The important narrowing is that `stream` is no longer grouped with `foundation` and `lifeline` as the same blocker shape.

Current `stream` blocker truth is structurally different:

- `stack.lock.yaml` still records `remote: null`
- `stack.lock.yaml` still records `release_eligible: false`
- the latest `stream` receipt is fresh and SHA-aligned, but its origin is still `local_dev`
- no protected-manual or CI-backed release path is currently available from the root topology for `stream`

## Validation Boundary

Root validation is clean at the blocking level:

- `critical=0 error=0 warning=1 info=0`

The single remaining warning is retained mutable state:

- `repos/lifeline/.lifeline`

`stack.lock.yaml` is now re-synced to the live owner commits:

- `foundation`: `fd1cf0650cdbb732f1231aa47a6e43138dab9062`, `dirty: false`
- `lifeline`: `538f623a84b003e70dadd234e6ea3af642446a5f`, `dirty: false`

## Exact Next Honest Move

- physical-device proof or manual attestation for `fitness` on `android.chrome.real` and `iphone.webkit.real`
- explicit `stream` governance resolution:
  - either add a protected remote-backed release path so trusted-origin enforcement can be satisfied
  - or keep `stream` intentionally outside release gating instead of treating it like a blocked release-ready repo
