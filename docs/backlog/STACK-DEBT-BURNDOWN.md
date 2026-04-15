# Stack Debt Burndown

## Objective

Burn down inherited stack debt without reopening healthy governed surfaces.

The core platform boundary is now stable enough that debt work should proceed as a separate program:

- classify inherited blockers
- ratchet new regressions to zero
- close low-risk stack-root items first
- then close repo-owned debt in repo-local lanes

## Near-Term Queue

1. Close stack-root path-discipline leaks in root docs and scripts.
2. Decide the fate of legacy repo entries `playbook-v1` and `mazer-unreal`.
3. Decide the fate of unregistered git root `repos/ZachariahRedfield`.
4. Move or clean repo-root mutable residue where the owning repo agrees.
5. Keep all new repos compliant on `AGENTS.md`, `.codex/config.toml`, and relative-path discipline.

## Bucket Order

1. Repair current governed runtime buckets with canonical builders or truthful receipt supersession.
2. Classify retained runtime residue so current-state reads stop treating old artifacts as live truth.
3. Keep mutable-state warnings visible as historical debt until relocation is worth the churn.
4. Burn down repo-local config gaps only through intentional repo mapping changes.
5. Burn down path-discipline leaks repo by repo without weakening the validator.

## Owner Map

| Area | Primary owner | Notes |
| --- | --- | --- |
| root docs and validation policy | stack root | can be fixed from the stack root |
| repo-local config defaults | stack root with repo owner review | stack policy, repo-local file |
| repo-owned path leaks | owning repo | fix inside repo root, not opportunistically from stack root |
| `_stack` worker-flow docs and artifacts | `_stack` | only touch from stack root when the change is explicitly cross-repo |
| Lifeline execution contracts | Lifeline | out of debt scope unless directly required for stack validation |
| Verta quarantined material | quarantined / trust gate owner | containment first, not cleanup vanity |

## Closure Order

### Wave 1

- root-runbook path fixes
- repo-local config defaults
- validator false-positive reduction
- debt ledger publication

### Wave 2

- root-owned path leak cleanup
- explicit decisions on legacy missing repo paths
- explicit decision on unregistered git root

### Wave 3

- repo-by-repo path cleanup through repo-local sessions
- mutable residue relocation where it has real operator value

## Non-Goals

- no schema churn to disguise operational debt
- no broad suppression of validation classes
- no opportunistic edits across unrelated repos from the stack root
- no Verta trust-boundary weakening in the name of cleanup
