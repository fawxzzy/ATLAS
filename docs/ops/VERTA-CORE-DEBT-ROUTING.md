# Verta-Core Debt Routing

Updated from `runtime/receipts/validation/stack-validation.latest.md` and `stack.yaml` on 2026-04-20.

## Decision

`repos/Verta-Core` should remain a separate adjacent backlog, not the next default core-owner lane.

The reason is already encoded in stack truth:

- `stack.yaml` marks `repos/Verta-Core` as an `excluded_surface`
- the trust class is `untrusted`
- the reason says the checkout remains quarantined until scrub and rotation are complete

That means the current `345` validator findings are real, but they are not evidence that the main stack program should automatically pivot into broad Verta-Core cleanup.

## Validation Policy

Validation receipts must keep Verta-Core path-leak evidence visible without presenting that quarantine backlog as active stack-owned contract breakage.

- quarantined excluded surfaces stay in the receipt
- the receipt must preserve surface label, file path, category, and count data
- quarantined excluded-surface path leaks are quarantine debt, not active critical ownership debt

## Live Backlog Shape

- Live Verta-Core validator finding total: `345`
- These findings remain visible as quarantined excluded-surface debt instead of active stack-owned critical debt

This is no longer mixed with core-owner debt. It is a single quarantined surface.

## Pattern Clusters

The current Verta-Core criticals are concentrated in a few file families:

| Cluster | Critical count | Dominant file types | Interpretation |
| --- | ---: | --- | --- |
| `data/archive` | 90 | `.sh`, `.json`, `.txt`, `.bat` | historical rollback scripts and archived exports with embedded machine paths |
| `docs/Archive` | 38 | `.md` | archived migration and consolidation notes |
| `docs/claude_docs` | 29 | `.md` | legacy operator and setup docs |
| live top-level docs | 82 | `.md` | current status/audit docs with hardcoded home/workspace paths |
| `data/memory` | 15 | `.json` | retained memory exports with embedded local paths |
| `scripts/intelligence` | 13 | `.md` | operator-facing setup docs bundled with scripts |
| `.claude` | 17 | `.json`, docs | local tool settings and plugin artifacts |

## Top Hotspots

These files dominate the current Verta-Core receipt:

- `repos/Verta-Core/Verta-Core/data/archive/rollback/rollback_20260410_145225.sh`: `75`
- `repos/Verta-Core/Verta-Core/docs/HOMEOSTASIS_AUDIT.md`: `20`
- `repos/Verta-Core/Verta-Core/docs/PRE_CORE_HARDENING_CHECKPOINT.md`: `17`
- `repos/Verta-Core/Verta-Core/data/archive/historical_snapshots/20260410_033321/memory_consolidated/git_historical_patterns.json`: `12`
- `repos/Verta-Core/Verta-Core/data/memory/git_historical_patterns.json`: `12`
- `repos/Verta-Core/Verta-Core/docs/CUTOVER_GATE_STATUS.md`: `10`
- `repos/Verta-Core/Verta-Core/.claude/settings.local.json`: `9`
- `repos/Verta-Core/Verta-Core/docs/claude_docs/verta-optimization-implementation-guide.md`: `9`

## Ownership Posture

This backlog is best treated as adjacent-surface debt with explicit admission criteria.

- It is not in the named core-owner queue.
- It is not release-eligible in current stack truth.
- The quarantine rationale is stronger than the raw count signal.

Unless that posture changes, the correct control-plane behavior is to track Verta-Core separately and avoid broad cleanup churn inside an untrusted checkout.

## First Tranche Options If Admitted

If you explicitly open a Verta-Core scrub lane, the lowest-risk first slices are:

1. docs-only cleanup in `docs/Archive`, `docs/claude_docs`, and the top-level `.md` status files
2. settings/docs cleanup under `.claude` that does not alter runtime behavior
3. archive/data normalization only after confirming retention and quarantine handling for historical exports

The rollback shell script cluster should not be the first tranche unless the goal is an intentional scrub program, because it is both the largest hotspot and the most likely to intersect with retained historical evidence.

## Recommendation

Recommendation: keep Verta-Core as a separate backlog for now.

- Do not automatically route active stack cleanup into Verta-Core just because it dominates the validator count.
- Open a dedicated Verta-Core lane only if you want to do one of these deliberately:
  - quarantine scrub and path sanitization
  - retention review for archived artifacts
  - explicit admission of selected Verta-Core doc surfaces into an active cleanup program

## Count Check

The clustered routing view still sums back to the live Verta-Core total:

- Verta-Core validator finding total: `345`
- Receipt policy: keep the evidence visible, but classify it as quarantined excluded-surface debt
