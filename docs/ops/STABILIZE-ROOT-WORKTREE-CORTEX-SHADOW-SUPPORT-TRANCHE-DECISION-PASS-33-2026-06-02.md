# Stabilize Root Worktree Cortex Shadow-Support Tranche Decision Pass 33 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing cortex shadow-support tranche decision`
- Source surfaces:
  - `git status --short .gitignore ops/cortex runtime/cortex schemas tests docs/ops`
  - direct reads of `ops/cortex/shadow_agent_registry.py`
  - direct reads of `runtime/cortex/shadow-agent-registry.seed.v1.json`
  - direct reads of `schemas/atlas.cortex.shadow-agent-registry.v1.json`
  - direct reads of `tests/test_cortex_shadow_*.py`

## Objective

Decide whether the remaining held root-owned Cortex support carry is one honest preservation tranche, and if so, define its exact boundary without widening into the later memory-path canonicalization carry, the residual QA workflow carry, or the broad retained backlog.

## Decision

- the next exact tracked and untracked candidate is one `cortex shadow-support tranche`
- this tranche includes the Wave 1 Playbook/Cortex shadow receipts, the root-owned Cortex shadow registry and consumers, the local runtime seed and schema, the shadow tests, and the `.gitignore` exception needed to preserve the runtime seed durably
- do not widen this tranche to `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`, `.github/workflows/atlas-qa-llel.yml`, unrelated `docs/ops/*` backlog, or retained `archive/*`

## Exact Cortex Shadow-Support Tranche

- `.gitignore`
- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-FIRST-AGENT-SHADOWING-PASS-1-2026-06-01.md`
- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-VALIDATION-SUMMARY-SHADOW-CONSUMPTION-PASS-2-2026-06-01.md`
- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-EXPORT-SURFACE-PASS-3-2026-06-02.md`
- `docs/ops/CORTEX-READINESS-MARKER-CHECKPOINT-SHADOW-CONSUMPTION-PASS-1-2026-06-01.md`
- `docs/ops/CORTEX-READINESS-RECEIPT-DOCTRINE-DRAFT-SHADOW-CONSUMPTION-PASS-2-2026-06-01.md`
- `docs/ops/CORTEX-READINESS-SHADOW-CONSUMPTION-READ-MODEL-PROJECTION-PASS-3-2026-06-01.md`
- `docs/ops/CORTEX-READINESS-READ-MODEL-FRESHNESS-AND-DEFERRED-LANE-PASS-4-2026-06-01.md`
- `ops/cortex/README.md`
- `ops/cortex/shadow_agent_registry.py`
- `ops/cortex/shadow_marker_checkpoint.py`
- `ops/cortex/shadow_receipt_doctrine_draft.py`
- `ops/cortex/shadow_validation_summary.py`
- `runtime/cortex/shadow-agent-registry.seed.v1.json`
- `schemas/atlas.cortex.shadow-agent-registry.v1.json`
- `tests/test_cortex_shadow_agent_registry.py`
- `tests/test_cortex_shadow_marker_checkpoint.py`
- `tests/test_cortex_shadow_receipt_doctrine_draft.py`
- `tests/test_cortex_shadow_validation_summary.py`

## Exact Later Carry Outside This Tranche

- `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json` remains later rename-aligned memory-path canonicalization carry
- `.github/workflows/atlas-qa-llel.yml` remains residual QA workflow carry
- unrelated untracked `docs/ops/*` backlog remains outside this tranche unless directly cited above
- retained `archive/*` evidence remains outside this tranche

## Why This Is Honest

1. the shadow registry, local seed, schema, consumers, and tests are one bounded Cortex support unit rather than unrelated residue
2. `.gitignore` is directly coupled because the runtime seed cannot be preserved durably without the explicit exception
3. the Wave 1 receipts are the control-plane truth that names the exact shadow families and blocked families consumed by this local root-owned support set

## Exact Next Move

- admit and stage the Cortex shadow-support tranche in isolation
- verify the targeted shadow tests and full stack validation
- only then decide commit-intent for that exact tranche

## Marker Decision

- `none`
