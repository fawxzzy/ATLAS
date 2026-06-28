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

### CI gate CLI support

Updated:

- `ops/atlas/qa/ci_gate.py`

Changes:

- added CLI flags:
  - `--allow-missing-locked-repos`
  - `--require-present-repo-id`
- passed those flags through to the existing sparse validator path already used by protected release refresh logic

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

## Next Move

Push the root workflow/tooling changes to `origin/main`, then re-dispatch the protected Fitness provider-backed run for SHA:

- `b5f29793eb87dc7538a15160180f159688acd1b4`

That rerun should prove whether the remaining blocker is now only provider/mobile evidence rather than missing hosted-runner topology.
