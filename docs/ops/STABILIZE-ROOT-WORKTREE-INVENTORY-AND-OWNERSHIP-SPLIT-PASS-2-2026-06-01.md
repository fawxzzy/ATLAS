# Stabilize Root Worktree Inventory And Ownership Split Pass 2 - 2026-06-01

- Date: `2026-06-01`
- Lane: `stabilize-root-worktree`
- Mode: `docs-only root inventory and ownership split`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-BLOCKER-CLASSIFICATION-AND-HOLD-PASS-1-2026-06-01.md`
  - `runtime/cortex/current-state/latest.json`
  - `runtime/cortex/rail-state/latest.json`
  - `runtime/cortex/context/latest.json`
  - `runtime/receipts/validation/stack-validation.latest.json`
  - `git status --porcelain=v1 --untracked-files=all`

## Objective

Split the current dirty-root blocker into restart-safe ownership buckets so later stabilization work does not confuse active governed work, durable-but-uncommitted receipt backlog, retained archive evidence, and unresolved mixed root residue.

## Root Health Baseline

- validation remains `critical=0 error=0 warning=493 info=0`
- tracked modified paths: `52`
- untracked paths: `192`
- the immediate lane remains `stabilize-root-worktree`
- the deferred Cortex lane remains `promote-cortex-receipt-interpretation-consumption-feedback-wave11`

## Inventory Split

### 1. Active current-tranche restart surfaces

These are live root-owned control-plane surfaces actively touched by the current ATLAS/Cortex tranche:

- `docs/PLAYBOOK_NOTES.md`
- `docs/atlas-book/*`
- `ops/cortex/*`
- `tests/test_cortex*`

Observed count:

- tracked paths in this bucket: `18`

Interpretation:

- keep treated as active governed work, not cleanup residue

### 2. Root registry / stack-policy mirrors

These are root-owned projection or policy surfaces whose dirty state affects restart truth directly:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/*`
- `docs/audits/*`
- `AGENTS.md`
- `README-STACK.md`

Observed count:

- tracked paths in this bucket: `7`

Interpretation:

- treat as root truth mirrors or policy surfaces; later stabilization must classify whether they belong to the same active tranche or a separate preserve/commit decision

### 3. Mixed tracked governance / memory / QA support surfaces

Representative files:

- `.github/workflows/atlas-qa-llel.yml`
- `.gitignore`
- `data/fixtures/atlas.playbook.adoption.report.example.v1.json`
- `docs/architecture/*`
- `docs/memory/*`
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
- `ops/atlas/*`
- `ops/validation/stack-validation.baseline.json`
- `tests/test_atlas_codex_context.py`
- `tests/test_stack_repo_inventory.py`

Observed count:

- tracked paths in this bucket: `27`

Interpretation:

- this is the largest tracked mixed bucket and should not be treated as one cleanup action
- later stabilization needs an explicit preserve/disposition decision for this mixed support surface before any broad worktree-cleanliness claim is honest

### 4. Durable-but-uncommitted receipt backlog

Observed count:

- untracked `docs/ops/*` receipt paths: `170`

Interpretation:

- this is not scratch output
- this is durable control-plane evidence currently living as uncommitted backlog
- later stabilization should decide whether the backlog is intentionally held, partially staged, or awaiting classification, rather than pretending it is generic residue

### 5. Untracked continuity-manifest backlog

Observed count:

- untracked `docs/memory/initiatives/*` paths: `5`

Interpretation:

- these belong to durable continuity truth, not disposable runtime state
- later stabilization must classify them alongside the receipt backlog, not with archive or scratch deletion candidates

### 6. Untracked Cortex runtime / schema / test support

Observed count:

- untracked `ops/cortex/*`, `runtime/cortex/*`, `schemas/*`, and `tests/*` paths: `11`

Interpretation:

- these are active bounded Cortex shadow-lane support surfaces
- keep classified as active work until the stabilization lane explicitly decides how they are preserved or committed

### 7. Retained archive evidence surface

Observed count:

- untracked `archive/*` paths: `7`

Representative paths:

- `archive/fitness-source-reset/20260522-final-cleanup/fawxzzy-fitness-real/`
- `archive/fitness-source-reset/20260522-final-cleanup/fitness-feedback-completion-review-workflow/.env.local`
- `archive/fitness-source-reset/20260522-final-cleanup/fitness-pr61-merge/.playbook/last-run.json`

Interpretation:

- this bucket is retained evidence or preserved residue, not auto-cleanup material
- AGENTS rules apply directly here: no delete or move is honest before retention class is confirmed

## What This Pass Proves

- the dirty-root blocker is not a single cleanup item; it is at least four materially different classes:
  - active governed root work
  - root truth mirrors and policy surfaces
  - durable-but-uncommitted control-plane backlog
  - retained archive evidence
- the highest-volume untracked class is durable receipt backlog under `docs/ops/*`, not transient runtime output
- the archive surface is small but high-risk because it includes preserved residue and secret-bearing historical paths
- any later root-worktree stabilization claim must name which bucket is being preserved, committed, retained, or dispositioned

## What This Does Not Prove

This pass does not prove:

- that any bucket is safe to delete
- that any bucket is ready to stage or commit together
- that the root checkout is stable enough to resume deferred Cortex work
- that any marker movement is earned

## Exact Next Slice Inside This Lane

Still inside `stabilize-root-worktree`, the next honest slice is:

- explicit preserve/disposition decisioning for the dirty-root buckets, starting with:
  - durable-but-uncommitted `docs/ops/*` receipt backlog
  - untracked continuity manifests
  - retained `archive/*` evidence surface

Why this is next:

1. those buckets are durable truth or retained evidence, not generic residue
2. they dominate the untracked pressure
3. no cleanup move is honest before their retention and ownership posture is frozen explicitly

## Marker Decision

- `none`

Why:

- this pass reduces ambiguity inside the blocker
- it does not stabilize the checkout yet
- it does not clear a blocker or widen capability

