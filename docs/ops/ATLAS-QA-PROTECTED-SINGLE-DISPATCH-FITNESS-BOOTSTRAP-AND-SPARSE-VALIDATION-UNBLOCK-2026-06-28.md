# ATLAS QA Protected Single Dispatch Fitness Bootstrap And Sparse Validation Unblock - 2026-06-28

- Date: `2026-06-28`
- Owner: `ATLAS/root`
- Lane: `ATLAS QA protected dispatch unblock`

## Objective

Unblock the protected Fitness `workflow_dispatch` lane that still required provider-backed mobile proof after local desktop closeout.

## Observed Blockers

The first protected dispatch against ATLAS `main` exposed two execution blockers:

1. `dispatch_scope=single` ran on a hosted runner that only had the tracked ATLAS snapshot, so ignored child repos under `repos/**` were absent and the Fitness adapter repo was not bootstrapable.
2. `atlas-release-readiness` validated the full workstation topology on the hosted runner and failed in `validate_stack.py` because the runner does not carry the complete local child-repo set.

## Executed Root Changes

### Protected single-dispatch adapter bootstrap

Added:

- `ops/atlas/qa/bootstrap_adapter_repo.py`

This bootstrap path now:

- resolves the adapter repo from `ops/atlas/qa/adapters/<adapter>.json`
- resolves the canonical child-repo remote from `docs/registry/STACK-REPO-INVENTORY.json`
- clones the missing child repo when required
- fetches and checks out an exact requested `target_sha`
- fails closed on missing `remote_url`, missing commit, non-git targets, or dirty post-bootstrap state
- emits `runtime/atlas/qa/bootstrap-adapter-repo.latest.json` and `.md`

### Workflow integration

Updated:

- `.github/workflows/atlas-qa-llel.yml`

Changes:

- `Resolve adapter context` now exports `repo_id`
- `workflow_dispatch` with `dispatch_scope=single` now runs adapter bootstrap before browser install and QA execution
- uploaded artifacts now include `bootstrap-adapter-repo.latest.json` and `.md`
- the protected single-dispatch `ci_gate.py` invocation now runs in sparse stack-validation mode and requires the bootstrapped adapter repo to be present
- `atlas-release-readiness` now uses `python ops/validation/validate_stack.py --allow-missing-locked-repos` on the hosted runner
- provider-requested workflow runs now execute `provider_readiness.py` before browser/runtime startup so missing BrowserStack credentials fail at the correct seam

### CI gate CLI support

Updated:

- `ops/atlas/qa/ci_gate.py`

Changes:

- added CLI flags:
  - `--allow-missing-locked-repos`
  - `--require-present-repo-id`
- passed those flags through to the existing sparse validator path already used by protected release refresh logic
- provider-requested runs now fail immediately when the requested provider is unavailable instead of silently falling back to local execution

### Runbook update

Updated:

- `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`

The runbook now states that protected `dispatch_scope=single` must bootstrap ignored child repos from the tracked stack repo inventory and use `target_sha` for exact-SHA proof.

## Verification

Executed locally after the changes:

- `python -m unittest tests.test_atlas_qa_pipeline`
- `python ops/validation/validate_stack.py`

Results:

- QA unit suite: `71` tests passed
- stack validation: `critical=0 error=0 warning=0 info=0`

## Live GitHub Proof

Protected dispatches executed after publish:

- `28315893818` on ATLAS commit `9dc9f872c556a0812595b7987fb3c19a17656f72`
- `28316073769` on ATLAS commit `ab08e0f8ee1a1f8e62a0716bb7548c6d4a60ef6e`

Observed live outcomes:

- hosted `atlas-qa-llel` passed:
  - adapter repo bootstrap
  - sparse stack validation path
  - browser/runtime install
- hosted `atlas-release-readiness` passed:
  - stack validation
  - evidence index refresh
  - release readiness build
  - adoption drift
  - release rehearsal
- hosted `atlas-release-readiness` still failed at final enforce, which is expected until a new protected/manual/provider-backed physical-proof receipt exists

Final live blocker after the last hardened dispatch:

- `Validate provider readiness` failed before QA execution because GitHub exposed:
  - `BROWSERSTACK_USERNAME: missing`
  - `BROWSERSTACK_ACCESS_KEY: missing`
- follow-on local repo audit `python ops/atlas/qa/github_secret_readiness.py --repo fawxzzy/ATLAS --require-secret BROWSERSTACK_USERNAME --require-secret BROWSERSTACK_ACCESS_KEY` wrote:
  - `runtime/atlas/qa/github-secret-readiness.latest.json`
  - `runtime/atlas/qa/github-secret-readiness.latest.md`
  - `available_secret_count: 0`
  - required-secret status:
    - `BROWSERSTACK_USERNAME: missing`
    - `BROWSERSTACK_ACCESS_KEY: missing`

That means the protected lane is no longer blocked by ATLAS workflow topology or validator posture. It is now blocked only by missing BrowserStack credentials on the ATLAS GitHub Actions side.

## Next Move

Provide the missing ATLAS GitHub Actions secrets, then re-dispatch the protected Fitness provider-backed run for SHA:

- `b5f29793eb87dc7538a15160180f159688acd1b4`

Required secrets:

- `BROWSERSTACK_USERNAME`
- `BROWSERSTACK_ACCESS_KEY`

Once those are present, the next protected dispatch should enter real provider execution instead of failing at preflight.
