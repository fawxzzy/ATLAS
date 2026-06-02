# Stabilize Root Worktree Continuity-Support Tranche Decision Pass 28 - 2026-06-02

- Date: `2026-06-02`
- Lane: `stabilize-root-worktree`
- Mode: `blocker-facing continuity-support tranche decision`
- Source surfaces:
  - `git status --short docs/memory docs/memory/initiatives`
  - `git diff -- docs/memory/README.md docs/memory/initiatives/continuity-manifest-*.json`
  - direct reads of the seeded continuity manifests
  - direct comparison against `docs/atlas-book/02-lanes-and-markers.md` and `docs/atlas-book/12-restart-and-handoff-guide.md`

## Objective

Decide whether the remaining continuity-support bucket is one honest preservation tranche, and if so, define its exact boundary without widening into unrelated memory-path or QA/Cortex support carry.

## Decision

- the next exact tracked and untracked candidate is one `continuity-support tranche`
- this tranche includes the memory README, the twelve seeded continuity manifests, the `_stack Readiness` manifest repair to current `70%` truth, and the exact untracked root receipt support files those manifests cite
- do not widen this tranche to `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`, `.github/workflows/atlas-qa-llel.yml`, `.gitignore`, held Cortex support surfaces, or the broad `archive/*` backlog

## Exact Continuity-Support Tranche

- `docs/memory/README.md`
- every `docs/memory/initiatives/continuity-manifest-*.json` file currently present
- exact untracked `docs/ops/*` support receipts cited by those continuity manifests and not yet preserved

## Exact Later Carry Outside This Tranche

- `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json` remains a later memory-path canonicalization carry
- `.github/workflows/atlas-qa-llel.yml` remains later QA workflow support carry
- `.gitignore` remains coupled to held root-owned Cortex support carry
- untracked `ops/cortex/*`, `runtime/cortex/*`, `schemas/*`, `tests/test_cortex_shadow_*`, and `archive/*` surfaces remain outside this continuity-support packet

## Why This Is Honest

1. the continuity-support files are coupled by explicit manifest-backed restart claims rather than just shared directory location
2. the modified and new manifests need the cited untracked root receipts to remain valid after preservation
3. `_stack Readiness` was repaired to current restart truth before admission, so this tranche no longer preserves stale continuity

## Exact Next Move

- admit and stage the continuity-support tranche in isolation
- verify JSON integrity, referenced-file presence, and full stack validation
- only then decide commit-intent for that exact tranche

## Marker Decision

- `none`
