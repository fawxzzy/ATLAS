# Stack Debt Ledger

## Purpose

This ledger separates inherited ATLAS stack debt from the now-stable governed core.

Use it to keep validation noise explicit, owned, and ratcheted instead of mixing old residue with new regressions.

Current source reports:

- `runtime/receipts/validation/stack-validation.latest.json`
- `runtime/receipts/validation/stack-validation.latest.md`
- `ops/validation/stack-validation.baseline.json`

Current ratchet state from the latest root run:

- blocking findings: `494`
- new blocking findings vs baseline: `0`
- inherited blocking classes only:
  - `path-discipline-leaks`: `492`
  - `repo-local-config-gaps`: `2`

## Debt Classes

| Class | Current total | Blocking | Owner | Blocking level | Closure plan |
| --- | ---: | ---: | --- | --- | --- |
| `path-discipline-leaks` | 649 | 492 | stack root + owning repo for each file | inherited blocking | burn down by repo slice; do not rewrite quarantined or legacy evidence just to zero the count |
| `repo-local-config-gaps` | 2 | 2 | stack root | inherited blocking | keep explicit as legacy missing repo paths until archived or path mapping is intentionally changed in `stack.yaml` |
| `historical-stack-baseline-residue` | 34 | 0 | owning repo | non-blocking tracked residue | move mutable residue to stack buckets when worth the churn; otherwise keep visible and out of new baselines |
| `lock-registry-hygiene` | 1 | 0 | stack root | non-blocking tracked residue | decide whether to register or explicitly exclude `repos/ZachariahRedfield` |
| `missing-agents-codex-defaults` | 0 | 0 | stack root + repo owner | should stay zero | keep repo-local `AGENTS.md` and `.codex/config.toml` present where policy expects them |
| `governed-surface-contracts` | 0 | 0 | stack root, `_stack`, Lifeline, Cortex | must stay zero | never trade core governed correctness for debt cleanup progress |

## Remediation Matrix

| Bucket | Treatment | Current intent |
| --- | --- | --- |
| `execution-receipt-repair-invalid` | repair through canonical builders | fix with root reconcile or Lifeline truthful supersession and keep current governed failures red until repaired |
| `mutable-state-warnings` | classify as retained residue / historical debt | keep visible, move only when it improves operations, and never present residue as fresh truth |
| `repo-local-config-gaps` | move into the debt ledger as inherited debt | explicit legacy debt until repo mapping is repaired, archived, or removed |
| `path-discipline-leaks` | move into the debt ledger as inherited debt | close by repo slice without turning validation into blanket suppression |
| `retained-runtime-residue` | classify as retained residue / historical debt | keep residue queryable while status and world model prefer canonical current artifacts only |

## Named Findings

### Repo-local config gaps

The remaining blocking repo-path findings are legacy entries declared in `stack.yaml`:

- `playbook-v1` -> `repos/playbook-old/playbookv1`
- `mazer-unreal` -> `repos/mazer-legacy-unreal/Mazer`

These are classified debt, not active governed-surface failures.

### Path-discipline leaks

This remains the dominant inherited blocker. The highest-volume categories are:

- `windows-user-path`
- `atlas-root-path`
- `unix-home-path`
- `windows-user-path-alt`
- `atlas-root-path-alt`

Owner rule:

- root-owned docs and scripts: stack root closes them
- repo-owned docs and code: owning repo closes them
- quarantined or explicitly untrusted material: do not normalize opportunistically; track and contain instead

### Historical baseline residue

Tracked but non-blocking examples:

- repo-local mutable state directories such as `.playbook`, `.lifeline`, `node_modules`, `dist`, `.next`
- repo-local secret-material warnings for real `.env*` files
- mutable root-level logs retained inside repo roots

Low-risk false positives were already reduced by excluding `.env.example` and similar templates from the secret-material warning path.

### Lock and registry hygiene

The current non-blocking finding is:

- unregistered git root: `repos/ZachariahRedfield`

Closure options:

1. add it to `repo_registry` if it becomes managed
2. add it to an explicit exclusion list if it stays adjacent
3. remove the checkout if it is not part of the stack

## Current Runtime Rule

- ATLAS current-state reads ignore retained runtime residue unless that artifact is the canonical current artifact.
- History may be incomplete, but it may not be invisible.
- New governed artifacts fail closed.
- Old artifacts get classified, superseded, or ledgered. They do not get silently “fixed.”

## Completed Low-Risk Closures In This Baseline

- added missing repo-local `AGENTS.md` where policy expected it
- added missing repo-local `.codex/config.toml` where policy expected it
- regenerated `stack.lock.yaml` to the current intended working set
- fixed root-runbook stale path references in stack docs
- reduced repo-local `.env` false positives for template/example files
- split ratchet reporting into explicit inherited-vs-new blocking classes

## Ratchet Policy

Rules:

- new blocking findings fail the ratchet immediately
- inherited blocking findings remain visible by debt class
- non-blocking residue still appears in reports and stays available for closure planning
- governed-surface correctness is not negotiable debt

Operator rule:

- if a finding is old and unavoidable today, classify it
- if a finding is new, remove it or intentionally baseline it with review
- never hide inherited debt by broad report suppression
