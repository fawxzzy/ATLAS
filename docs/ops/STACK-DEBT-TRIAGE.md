# Stack Debt Triage

Updated from `runtime/receipts/validation/stack-validation.latest.md` on 2026-04-20 after the Playbook and adjacent residual tranches landed.

## Scope

This note ranks the remaining critical validation backlog by owner surface so the next move stays aligned with current stack truth.

- Source receipt summary: `critical=345`, `error=0`, `warning=178`
- Grouping rule: rank the named core owner surfaces first, then list adjacent or excluded backlog separately
- Goal: separate completed core-owner cleanup from the remaining adjacent-surface routing decision

## Ranked Owner Surfaces

| Rank | Owner surface | Critical count | Dominant pattern | File family hotspot | Lowest-risk tranche candidate |
| --- | --- | ---: | --- | --- | --- |
| 1 | `_stack` | 0 | none | none | no active path-discipline tranche needed |
| 1 | `fawxzzy-atlas` | 0 | none | none | no active path-discipline tranche needed |
| 1 | `fawxzzy-fitness` | 0 | none | none | no active path-discipline tranche needed |
| 1 | `fawxzzy-lifeline` | 0 | none | none | no active path-discipline tranche needed |
| 1 | `fawxzzy-mazer` | 0 | none | none | no active path-discipline tranche needed |
| 1 | `fawxzzy-playbook` | 0 | none | none | no active path-discipline tranche needed |
| 1 | `root-only` | 0 | none | none | stop polishing root for this lane |

## Core-Owner Status

All named core owner surfaces are at `0` critical findings in the live receipt.

- `_stack`: `0`
- `fawxzzy-atlas`: `0`
- `fawxzzy-fitness`: `0`
- `fawxzzy-lifeline`: `0`
- `fawxzzy-mazer`: `0`
- `fawxzzy-playbook`: `0`
- `root-only`: `0`

This lane is no longer a core-owner burn-down problem.

## Adjacent And Excluded Backlog

The remaining validator total sits entirely on the quarantined Verta-Core surface.

| Surface | Critical count | Dominant pattern | File family hotspot | Note |
| --- | ---: | --- | --- | --- |
| `repos/Verta-Core` | 345 | archived path leaks and hardcoded home/workspace paths | rollback scripts, archived data exports, and legacy docs | explicitly excluded and untrusted in `stack.yaml`; route separately from the core-owner queue |

### Adjacent Hotspots

- `repos/Verta-Core/Verta-Core/data/archive/rollback/rollback_20260410_145225.sh`: `75`
- `repos/Verta-Core/Verta-Core/docs/HOMEOSTASIS_AUDIT.md`: `20`
- `repos/Verta-Core/Verta-Core/docs/PRE_CORE_HARDENING_CHECKPOINT.md`: `17`
- `repos/Verta-Core/Verta-Core/data/archive/historical_snapshots/20260410_033321/memory_consolidated/git_historical_patterns.json`: `12`
- `repos/Verta-Core/Verta-Core/data/memory/git_historical_patterns.json`: `12`

## Count Check

The grouped critical totals sum back to the validator total:

- Named owner surfaces: `0`
- Adjacent and excluded backlog: `345`
- Total: `345`

## Next Tranche Recommendation

1. Do not reopen root or named core-owner cleanup. That queue is already zeroed.
2. Treat Verta-Core as a separate routing decision, not as an automatic continuation of the core-owner stack lane. See `docs/ops/VERTA-CORE-DEBT-ROUTING.md` for the explicit ownership posture and first-tranche options.
