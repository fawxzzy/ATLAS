# Stabilize Root Worktree Canonicalization-Support Staging Admission Decision Pass 24 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing canonicalization-support staging admission`
- Source surfaces:
  - `docs/ops/STABILIZE-ROOT-WORKTREE-MIXED-TRACKED-SUPPORT-TRANCHE-SPLIT-DECISION-PASS-23-2026-06-02.md`
  - `git status --short`
  - `git diff -- data/fixtures/atlas.playbook.adoption.report.example.v1.json docs/architecture/STACK-STANDARDS.md docs/architecture/atlas-current-tree.md docs/ops/ATLAS-NEXT-BUILD-QUEUE.md docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-2026-05-24.md docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md docs/ops/PLAYBOOK-ADOPTION-MATRIX.md ops/atlas/build_codex_context.py ops/atlas/continuity.py ops/atlas/qa/adapters/playbook.docs.json ops/atlas/qa/scenarios/playbook.docs-governance.json ops/atlas/qa/templates/docs-only/template.docs-only.json ops/atlas/qa/templates/docs-only/template.docs-only.verify.json ops/validation/stack-validation.baseline.json tests/test_atlas_codex_context.py tests/test_stack_repo_inventory.py`

## Objective

Decide whether the canonicalization-support tranche is honest to admit for selective staging without widening into the rest of the mixed tracked support backlog.

## Decision

- admit the exact canonicalization-support tranche for selective staging only
- do not widen staging admission to continuity-manifest refresh surfaces, `.github/workflows/atlas-qa-llel.yml`, `.gitignore`, or any untracked backlog

## Why This Is Honest

1. the tranche is internally coherent around delayed canonical repo-path support refreshes
2. the tranche does not rely on the still-held continuity refresh or Cortex support carry
3. the tranche preserves support surfaces for already-durable rename truth rather than reopening execution or marker claims

## Exact Next Move

- stage the exact canonicalization-support tranche in isolation
- prove the cached set stays exact
- verify the touched support code and stack posture boundedly before commit-intent

## Marker Decision

- `none`
