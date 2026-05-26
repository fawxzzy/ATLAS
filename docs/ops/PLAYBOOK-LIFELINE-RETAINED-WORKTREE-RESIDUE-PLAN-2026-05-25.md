# Playbook And Lifeline Retained Worktree / Residue Plan - 2026-05-25

- Date: `2026-05-25`
- Lane: `Playbook And Lifeline Retained Worktree / Residue Disposal Planning Pass`
- Mode: `inventory and disposal planning only`

## Scope

Classify the remaining retained Playbook and Lifeline dirty/worktree residue so the closeout ladder can continue toward `100%` without mixing feature work, disposal, and mutation.

This pass does not:

- delete `archive/`
- mutate `tmp/`
- delete branches
- remove worktrees
- drop stashes
- mutate Supabase
- mutate Vercel
- touch Discord runtime
- start Lifeline feature work
- start Playbook feature work
- run broad formatters
- regenerate `stack.lock.yaml`

## Inputs

- `docs/ops/QUEUED-WORK-REVIEW-PACKET-2026-05-25.md`
- `docs/ops/FULL-STACK-RESYNC-CLEAN-CLOSEOUT-BASELINE-PASS-2-2026-05-25.md`
- `docs/ops/BRANCH-TMP-VERCEL-CLOSEOUT-CONSOLIDATION-2026-05-25.md`
- `stack.yaml`
- `stack.lock.yaml`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/atlas-book/14-lane-split-execution.md`

## Stack-Lock Reference

Current lock truth for the two managed repos:

- `lifeline`
  - path: `repos/fawxzzy-lifeline`
  - branch: `codex/lifeline-release-replay-verification`
  - commit: `4589b4f332247b32e01931907f803e5ea5991e34`
  - dirty: `true`
- `playbook`
  - path: `repos/fawxzzy-playbook`
  - branch: `codex/playbook-sustain-docs-audit`
  - commit: `eeddaf75e59a6202c12bcf268221c5b469ac2b3a`
  - dirty: `true`

## Lifeline Residue Table

| Surface | Branch | HEAD | Remote | Ahead/Behind | Dirty tracked files | Untracked files | Generated residue | Classification | Required verification before disposal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `repos/fawxzzy-lifeline` | `codex/lifeline-release-replay-verification` | `4589b4f` | `origin/codex/lifeline-release-replay-verification` | in sync | 7 tracked changes | `docs/history/` | tracked `.codex/archive/**`, `.codex/logs/**`, `.codex/environments/environment.toml` deletions | active lane work plus retained local history/runtime residue | `pnpm run verify` before any cleanup; separate docs/history decision before deleting untracked history |
| `repos/fawxzzy-lifeline-operator-evidence` | `codex/lifeline-operator-evidence` | `bdb50fc` | `origin/codex/lifeline-operator-evidence` | in sync | none observed in worktree list pass | none observed | no current generated residue signal | retained evidence worktree | verify no current receipt depends on direct path before disposal |
| `tmp/fawxzzy-lifeline-rollback-rehearsal-evidence` | `codex/lifeline-rollback-rehearsal-evidence` | `e4de3eb` | `origin/codex/lifeline-rollback-rehearsal-evidence` | in sync | none observed in worktree list pass | none observed | no current generated residue signal | local-only safety checkpoint / retained evidence | verify rollback evidence is fully receipted before disposal |
| `tmp/lifeline-closeout-checkpoint` | `codex/lifeline-release-safety-closeout-checkpoint` | `a607986` | `origin/codex/lifeline-release-safety-closeout-checkpoint` | in sync | none observed | none observed | none observed | local-only safety checkpoint | verify closeout checkpoint is superseded by later receipts |
| `tmp/lifeline-main-closeout` | `codex/lifeline-main-closeout` | `c3b2d79` | no upstream shown in `branch -vv` | manual review | none observed | none observed | none observed | stale-but-not-safe merge checkpoint | compare against merged PR state before disposal |
| `tmp/lifeline-main-closeout-2` | `codex/lifeline-main-closeout-2` | `445c9ac` | no upstream shown in `branch -vv` | manual review | none observed | none observed | none observed | stale-but-not-safe merge checkpoint | compare against merged PR state before disposal |
| `tmp/lifeline-main-closeout-24` | `main` | `31ef3ad` | `origin/main` | in sync at captured branch state | none observed | none observed | none observed | local-only safety checkpoint | verify no newer root-of-main checkpoint is required |
| `tmp/lifeline-main-closeout-3` | `codex/lifeline-main-closeout-3` | `654b2f7` | no upstream shown in `branch -vv` | manual review | none observed | none observed | none observed | stale-but-not-safe merge checkpoint | compare against merged PR state before disposal |
| `tmp/lifeline-pr24-refresh` | `codex/lifeline-release-receipt-schema-parity` | `d3d8496` | `origin/codex/lifeline-release-receipt-schema-parity` | in sync | none observed | none observed | none observed | retained branch worktree | verify whether PR24 refresh branch still has open review value |
| `tmp/lifeline-release-cli-guardrails-worktree` | `codex/lifeline-release-cli-guardrails` | `e3a28be` | `origin/codex/lifeline-release-cli-guardrails` | in sync | none observed | none observed | none observed | retained branch worktree | verify branch is merged or superseded before disposal |
| `tmp/lifeline-release-replay-verification-clean` | `codex/lifeline-wave1-release-safety` | `34ce04c` | `origin/codex/lifeline-wave1-release-safety` | in sync | none observed | none observed | none observed | retained branch worktree / safety checkpoint | verify wave1 safety evidence is fully represented in receipts |
| `tmp/lifeline-wave2-scout` | `codex/lifeline-wave2-release-safety` | `ecce13c` | `origin/codex/lifeline-wave2-release-safety` | in sync | none observed | none observed | none observed | retained branch worktree / safety checkpoint | verify wave2 evidence is superseded |
| `tmp/lifeline-wave3-scout` | `codex/lifeline-wave3-rollback-confidence` | `cee62ab` | `origin/codex/lifeline-wave3-rollback-confidence` | in sync | none observed | none observed | none observed | retained branch worktree / safety checkpoint | verify wave3 rollback confidence evidence is superseded |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline` | detached | `89357af` | none | prunable | inaccessible broken worktree registration | n/a | broken gitdir registration | safe-delete candidate later | verify no receipt still expects the prunable path |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline-operator-evidence` | detached | `89357af` | none | prunable | inaccessible broken worktree registration | n/a | broken gitdir registration | safe-delete candidate later | verify no receipt still expects the prunable path |

### Lifeline residue item classification

- already merged / safe to remove later
  - prunable `r18-main-merge-20260511` broken worktree registrations after receipt check
- generated residue
  - tracked `.codex/archive/**`
  - tracked `.codex/logs/**`
  - tracked `.codex/environments/environment.toml`
- active lane work
  - `README.md`
  - untracked `docs/history/`
  - root worktree `repos/fawxzzy-lifeline`
- local-only safety checkpoint
  - `tmp/lifeline-closeout-checkpoint`
  - `tmp/lifeline-main-closeout-24`
  - `tmp/fawxzzy-lifeline-rollback-rehearsal-evidence`
- manual-review
  - `tmp/lifeline-main-closeout`
  - `tmp/lifeline-main-closeout-2`
  - `tmp/lifeline-main-closeout-3`
- should be retained until later
  - `repos/fawxzzy-lifeline-operator-evidence`
  - `tmp/lifeline-pr24-refresh`
  - `tmp/lifeline-release-cli-guardrails-worktree`
  - `tmp/lifeline-release-replay-verification-clean`
  - `tmp/lifeline-wave2-scout`
  - `tmp/lifeline-wave3-scout`

## Playbook Residue Table

| Surface | Branch | HEAD | Remote | Ahead/Behind | Dirty tracked files | Untracked files | Generated residue | Classification | Required verification before disposal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `repos/fawxzzy-playbook` | `codex/playbook-sustain-docs-audit` | `eeddaf75` | `origin/codex/playbook-sustain-docs-audit` | behind `5` | broad runtime and docs tracked changes | `packages/cli-wrapper/runtime/commands/patterns/verta.js`, `verta.js.map` | validator still flags `.playbook`, `.lifeline`, `node_modules`, `dist` as generated/mutable residue families | active lane work plus generated residue | repo-local verify/test contract before any cleanup or disposal plan |
| `tmp/fawxzzy-playbook-finding-identity` | `codex/playbook-baseline-finding-identity` | `90217f42` | `origin/codex/playbook-baseline-finding-identity` | in sync | none observed | none observed | none observed | retained branch worktree | verify branch value or merge state before disposal |
| `tmp/fawxzzy-playbook-sarif-output` | `codex/playbook-sarif-output` | `6d893d02` | `origin/codex/playbook-sarif-output` | in sync | none observed | none observed | none observed | retained branch worktree | verify SARIF lane is superseded |
| `tmp/fawxzzy-playbook-verify-baseline` | `codex/playbook-verify-baseline-hygiene` | `136779b6` | `origin/codex/playbook-verify-baseline-hygiene` | in sync | none observed | none observed | none observed | retained branch worktree | verify baseline hygiene work is merged or superseded |
| `tmp/playbook-fawx-den-os-doctrine` | `codex/fawx-den-os-doctrine` | `d3feb3af` | `origin/main` as tracking base | ahead `1`, behind `17` | none observed | none observed | none observed | manual-review / should become small PR or explicit closeout | compare divergence before disposal |
| `tmp/playbook-lint-debt-closeout` | `codex/playbook-lint-debt-closeout` | `0a562d33` | `origin/codex/playbook-lint-debt-closeout` | in sync | none observed | none observed | none observed | retained branch worktree | verify if lane still needed |
| `tmp/playbook-main-closeout` | detached | `aab5ad5b` | none | detached | none observed | none observed | none observed | local-only safety checkpoint | compare against `main` before disposal |
| `tmp/playbook-pr9-worktree` | `codex/pattern-discord-verification-gates` | `6c11edae` | `origin/codex/pattern-discord-verification-gates` | in sync | none observed | none observed | none observed | retained branch worktree | verify PR9 doctrine work is fully merged or superseded |
| `tmp/playbook-research-phase-grid-evidence` | `codex/research-phase-grid-boolean-functions-evidence` | `a196e6da` | `origin/codex/research-phase-grid-boolean-functions-evidence` | in sync | none observed | none observed | none observed | retained branch worktree | verify research lane retention need |
| `tmp/playbook-research-phase-grid-math` | `codex/research-phase-grid-boolean-functions-math-core` | `49df506e` | `origin/codex/research-phase-grid-boolean-functions-math-core` | in sync | none observed | none observed | none observed | retained branch worktree | verify research lane retention need |
| `tmp/playbook-sustain-pr19-refresh` | `codex/playbook-sustain-pr19-refresh` | `4f1d9552` | `origin/codex/playbook-sustain-docs-audit` | likely diverged from non-matching upstream branch | none observed | none observed | none observed | manual-review / stale-but-not-safe | verify branch lineage before disposal |
| `tmp/r18-main-merge-20260511/repos/fawxzzy-playbook` | detached | `bdd80eb1` | none | prunable | inaccessible broken worktree registration | n/a | broken gitdir registration | safe-delete candidate later | verify no receipt still expects the prunable path |
| external Playbook smoke worktree (`home-smoke`) | `codex/home-smoke` | `11859f21` | `origin/main` | behind `74` | none observed | none observed | external Codex smoke worktree | stale-but-not-safe / external manual-review | verify external smoke lane no longer needed before disposal |
| external Playbook `.codex/worktrees/**` registrations | multiple codex smoke branches | mixed | mostly `origin/main` | mostly behind `74`, some ahead `1` | prunable gitdir file points to non-existent location | n/a | broken external Codex worktree registrations | safe-delete candidate later | verify no local tooling still expects those smoke worktrees |

### Playbook residue item classification

- already merged / safe to remove later
  - prunable `tmp/r18-main-merge-20260511/repos/fawxzzy-playbook`
  - prunable external `.codex/worktrees/**` registrations after external tooling check
- generated residue
  - `.playbook`
  - `.lifeline`
  - `node_modules`
  - `dist`
- active lane work
  - `repos/fawxzzy-playbook` current tracked modifications
  - untracked `verta.js` and `verta.js.map`
- local-only safety checkpoint
  - `tmp/playbook-main-closeout`
- manual-review
  - `tmp/playbook-fawx-den-os-doctrine`
  - `tmp/playbook-sustain-pr19-refresh`
  - external `smoke-home`
- should become a small PR/package
  - `tmp/playbook-fawx-den-os-doctrine` if still valuable
  - any ahead-by-1 external smoke worktree branches if they contain intentional proof-only work
- should be retained until later
  - `tmp/fawxzzy-playbook-finding-identity`
  - `tmp/fawxzzy-playbook-sarif-output`
  - `tmp/fawxzzy-playbook-verify-baseline`
  - `tmp/playbook-lint-debt-closeout`
  - `tmp/playbook-pr9-worktree`
  - `tmp/playbook-research-phase-grid-evidence`
  - `tmp/playbook-research-phase-grid-math`

## Retained Worktree Table

| Family | Surface count | Current posture | Disposal posture |
| --- | --- | --- | --- |
| Lifeline ATLAS-root and tmp worktrees | 13 active + 2 prunable broken registrations | mixed active lane work, checkpoints, evidence, and stale checkpoints | no broad delete; split into prunable first, then checkpoint review, then active-lane retention review |
| Playbook ATLAS tmp worktrees | 10 active + 1 prunable broken registration | mostly retained branch worktrees and one detached checkpoint | no broad delete; retain active branch worktrees until repo-local review |
| Playbook external Codex worktrees | 1 live external smoke worktree + many prunable registrations | external manual-review and historical smoke residue | separate disposal package after confirming no local tooling dependence |

## Stash Posture

### Lifeline

- no stashes present

### Playbook

- `stash@{0}` `On main: codex-temp-playbook-agents-noise`
- `stash@{1}` `On main: codex-temp-local-hygiene-playbook-docs`
- `stash@{2}` `On main: qa residue before syncing main after PR 8`

Decision:

- do not drop or reinterpret stashes in this pass
- treat all Playbook stashes as manual-review retained safety surfaces until an explicit repo-local stash disposition lane runs

## Safe-Delete Candidate List

Strongest later candidates, once a disposal execution pass opens:

- `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline`
- `tmp/r18-main-merge-20260511/repos/fawxzzy-lifeline-operator-evidence`
- `tmp/r18-main-merge-20260511/repos/fawxzzy-playbook`
- prunable external Playbook `.codex/worktrees/**` registrations that point at non-existent locations
- detached closeout checkpoints after verification:
  - `tmp/lifeline-main-closeout`
  - `tmp/lifeline-main-closeout-2`
  - `tmp/lifeline-main-closeout-3`
  - `tmp/playbook-main-closeout`

## Do-Not-Delete List

Do not delete in the first disposal execution pass:

- `repos/fawxzzy-lifeline`
- `repos/fawxzzy-playbook`
- `repos/fawxzzy-lifeline-operator-evidence`
- `tmp/fawxzzy-lifeline-rollback-rehearsal-evidence`
- `tmp/lifeline-pr24-refresh`
- `tmp/lifeline-release-cli-guardrails-worktree`
- `tmp/lifeline-release-replay-verification-clean`
- `tmp/lifeline-wave2-scout`
- `tmp/lifeline-wave3-scout`
- `tmp/fawxzzy-playbook-finding-identity`
- `tmp/fawxzzy-playbook-sarif-output`
- `tmp/fawxzzy-playbook-verify-baseline`
- `tmp/playbook-lint-debt-closeout`
- `tmp/playbook-pr9-worktree`
- `tmp/playbook-research-phase-grid-evidence`
- `tmp/playbook-research-phase-grid-math`
- Playbook stashes

## Recommended Disposal Order

1. Prunable broken worktree registrations only
   - Lifeline `r18-main-merge-20260511` broken registrations
   - Playbook `r18-main-merge-20260511` broken registration
   - external prunable `.codex/worktrees/**` registrations
2. Detached checkpoint review
   - Lifeline `main-closeout*`
   - Playbook `playbook-main-closeout`
3. Generated residue cleanup planning inside repo roots
   - Lifeline `.codex/archive/**`, `.codex/logs/**`, `.codex/environments/**`
   - Playbook generated mutable-state residue already flagged by validation
4. Active branch worktree retention review
   - only after confirming branch merge/supersession state
5. Stash disposition
   - Playbook only, explicit manual-review lane

## Verification Required Per Repo

### Lifeline

- run `pnpm run verify` before any repo-root residue cleanup or branch/worktree removal affecting the active repo root
- verify receipts do not require any retained evidence worktree path before deleting evidence/checkpoint worktrees

### Playbook

- run repo-local verify/test contract before any repo-root cleanup or worktree disposal affecting current active branch state
- verify any ahead-by-1 or doctrine/research branch still has value before disposal
- inspect stash contents in a dedicated repo-local lane before dropping any stash

## Marker Movement Recommendation

Planning-only recommendation:

- `Branch & Worktree Normalization`: stays `98%`
  - no disposal executed yet, but remaining pressure is now bounded enough for a safe-delete lane
- `Full Stack Re-sync, Clean & Closeout`: `60% -> 64%`
  - ambiguity reduced again by explicit disposal ordering
- `Inventory & Truth Map`: `50% -> 53%`
  - Lifeline and Playbook retained-surface truth is now packageable
- `Knowledge Capture & Transfer`: `78% -> 80%`
  - residue/worktree knowledge is now durable enough for a later execution lane

## Files Changed In This Pass

- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-WORKTREE-RESIDUE-PLAN-2026-05-25.md`

## Next Package

- `Playbook And Lifeline Retained Residue Disposal Execution Pass`

Constraint:

- execution should remove only items proven safe in this receipt
- repo-root active work, retained checkpoints, and stashes remain out of scope until explicitly reopened
