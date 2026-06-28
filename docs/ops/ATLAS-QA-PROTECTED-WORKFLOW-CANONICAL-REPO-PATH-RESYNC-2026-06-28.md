# ATLAS QA Protected Workflow Canonical Repo Path Re-Sync

- Date: `2026-06-28`
- Lane: `ATLAS QA protected workflow canonical path closeout`
- Scope:
  - `.github/workflows/atlas-qa-llel.yml`
  - `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `tests/test_atlas_qa_pipeline.py`

## Why This Pass Was Needed

The protected `release_refresh` workflow was still installing release-repo dependencies from historical local paths:

- `repos/fawxzzy-playbook`
- `repos/fawxzzy-foundation`
- `repos/fawxzzy-lifeline`

That no longer matched canonical stack governance. `stack.yaml`, `stack.lock.yaml`, and the current bootstrap receipt all resolve those repos at:

- `repos/playbook`
- `repos/foundation`
- `repos/lifeline`

Because the protected workflow is the live blocker-facing orchestrator for trusted release refreshes, the old path literals were a real executable drift rather than a docs-only mismatch.

## Landed

1. Updated `.github/workflows/atlas-qa-llel.yml` so the protected release-refresh dependency installs now run from:
   - `repos/playbook`
   - `repos/foundation`
   - `repos/lifeline`
2. Added one explicit runbook rule to `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`:
   protected-dispatch repo-local installs must use the exact canonical repo path declared by `stack.lock.yaml` after bootstrap, not historical `repos/fawxzzy-*` aliases.
3. Added a regression test in `tests/test_atlas_qa_pipeline.py` that fail-closes if the workflow file drifts back to the old `repos/fawxzzy-*` install paths.
4. Refreshed the current-state, restart, and receipt-index Book surfaces so the protected-QA handoff now includes the fixed workflow-path truth.

## Validation

- Confirmed the root worktree was clean before the patch.
- Confirmed `runtime/atlas/qa/bootstrap-release-repos.latest.json` already resolves protected bootstrap targets to canonical paths:
  - `foundation -> repos/foundation`
  - `lifeline -> repos/lifeline`
- Re-ran the QA/root verification cluster after the patch:
  - `python -m unittest tests.test_atlas_qa_pipeline`
  - `python ops/validation/validate_stack.py`

## Outcome

- The last known protected release-refresh path mismatch is cleared.
- Protected workflow orchestration, stack-lock bootstrap truth, and restart documentation are aligned again.
- No Fitness mobile release blocker was cleared by this pass; the remaining blocker is still current-run Android/iPhone physical or manual proof, or one protected BrowserStack run with real credentials.
