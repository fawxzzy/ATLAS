# Stabilize Root Worktree Mixed Tracked Support Tranche Split Decision Pass 23 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing mixed tracked support split`
- Source surfaces:
  - `git status --short`
  - `git diff --stat -- .github/workflows/atlas-qa-llel.yml .gitignore data/fixtures/atlas.playbook.adoption.report.example.v1.json docs/architecture/STACK-STANDARDS.md docs/architecture/atlas-current-tree.md docs/memory/README.md docs/memory/initiatives docs/ops/ATLAS-NEXT-BUILD-QUEUE.md docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-2026-05-24.md docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md docs/ops/PLAYBOOK-ADOPTION-MATRIX.md ops/atlas ops/validation/stack-validation.baseline.json tests/test_atlas_codex_context.py tests/test_stack_repo_inventory.py`
  - `git diff -- data/fixtures/atlas.playbook.adoption.report.example.v1.json docs/architecture/STACK-STANDARDS.md docs/architecture/atlas-current-tree.md docs/ops/ATLAS-NEXT-BUILD-QUEUE.md docs/ops/PLAYBOOK-ADOPTION-MATRIX.md docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-2026-05-24.md docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md ops/atlas/build_codex_context.py ops/atlas/continuity.py ops/atlas/qa/adapters/playbook.docs.json ops/atlas/qa/scenarios/playbook.docs-governance.json ops/atlas/qa/templates/docs-only/template.docs-only.json ops/atlas/qa/templates/docs-only/template.docs-only.verify.json ops/validation/stack-validation.baseline.json tests/test_atlas_codex_context.py tests/test_stack_repo_inventory.py`

## Objective

Split the remaining mixed tracked support backlog into the next honest exact tranche without reopening already-preserved tranches or blurring tracked support, continuity backlog, and Cortex support carry.

## Decision

- the next exact tracked candidate is a `canonicalization-support tranche`
- this tranche is coherent because it preserves delayed root support surfaces that all reconcile canonical repo-path truth after the executed `mazer` and `playbook` local rename packets
- do not widen this tranche to the continuity-manifest refresh backlog, the residual QA workflow cleanup pair, or the untracked Cortex and archive backlogs

## Exact Canonicalization-Support Tranche

- `data/fixtures/atlas.playbook.adoption.report.example.v1.json`
- `docs/architecture/STACK-STANDARDS.md`
- `docs/architecture/atlas-current-tree.md`
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
- `docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-2026-05-24.md`
- `docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md`
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`
- `ops/atlas/build_codex_context.py`
- `ops/atlas/continuity.py`
- `ops/atlas/qa/adapters/playbook.docs.json`
- `ops/atlas/qa/scenarios/playbook.docs-governance.json`
- `ops/atlas/qa/templates/docs-only/template.docs-only.json`
- `ops/atlas/qa/templates/docs-only/template.docs-only.verify.json`
- `ops/validation/stack-validation.baseline.json`
- `tests/test_atlas_codex_context.py`
- `tests/test_stack_repo_inventory.py`

## Later Carry Outside This Tranche

- `docs/memory/README.md` and the tracked continuity-manifest refresh set remain a later continuity-support tranche
- `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json` remains with the later memory and continuity-support tranche
- `.github/workflows/atlas-qa-llel.yml` remains a later QA-workflow support decision
- `.gitignore` remains coupled to the still-held root-owned Cortex support backlog rather than this path-canonicalization tranche
- all untracked `docs/memory/initiatives/*`, `docs/ops/*`, `ops/cortex/*`, `runtime/cortex/*`, `schemas/*`, `tests/test_cortex_shadow_*`, and `archive/*` surfaces remain outside this tracked tranche

## Exact Next Move

- admit and stage the canonicalization-support tranche in isolation
- run the targeted ATLAS support tests plus stack validation
- only then decide commit-intent for that exact tranche

## Marker Decision

- `none`
