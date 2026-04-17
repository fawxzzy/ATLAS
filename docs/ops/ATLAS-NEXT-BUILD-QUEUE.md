# ATLAS Next Build Queue

This queue grounds the next convergence packet against the live ATLAS workspace and current Git visibility in this session.

Date grounded: `2026-04-17`

## Current Workspace Posture

- the ATLAS root checkout is clean on `main` and the stack registry in `stack.yaml` is intact.
- Root already contains the convergence roadmap, adoption matrix, initiative, and plan surfaces.
- Root also already has a Codex handoff contract, but it did not yet have a continuity handoff schema for cross-session promotion.
- The critical path is still owner-correct: Playbook exports the shared contract first, then ATLAS consumes it, then repo-local adoption becomes measurable.

## Repo And Git Visibility

### Core repos

| Repo | Local visibility | Git remote visibility | Notes |
| --- | --- | --- | --- |
| `playbook` | present at `repos/fawxzzy-playbook` | `origin` visible | existing `docs/contracts/`, `exports/`, and `packages/engine/test/` make this ready for the owner-repo export |
| `lifeline` | present at `repos/fawxzzy-lifeline` | `origin` visible | branch is `codex/startup-public-truth-reconcile`, ahead of origin; repo already has `docs/`, `.lifeline/`, and verify contract |
| `_stack` | present at `repos/_stack` | no remote visible in this workspace | local-only visibility is enough for repo-local docs work, but GitHub linkage is not currently confirmed |
| `atlas` | present at `repos/fawxzzy-atlas` | no remote visible in this workspace | local doctrine repo is available; GitHub linkage is not currently confirmed |

### Application and demo repos

| Repo | Local visibility | Git remote visibility | Notes |
| --- | --- | --- | --- |
| `fitness` | present at `repos/fawxzzy-fitness` | `origin` visible | strongest first vertical candidate because it already has both `.playbook/` and `.lifeline/` surfaces |
| `mazer` | present at `repos/fawxzzy-mazer` | `origin` visible | second vertical candidate; `.playbook/` exists but there is no `.lifeline/` surface visible |
| `stream` | present at `repos/fawxzzy-stream` | no remote visible in this workspace | incubating and locally available, but GitHub linkage is not currently confirmed |
| `playbook-demo` | nested repo present at `repos/playbook-demo/playbook-demo` | `origin` visible | valid demo repo; keep out of the critical path unless intentionally used as a contract demo surface |
| `nat1-games` | nested repo present at `repos/Nat1-Games/nat1-games` | `origin` visible | repo is visible, but it currently has untracked `AGENTS.md` in this checkout |

## Execution Order

### 1. Playbook owner-repo contract export

This remains the critical path because root should consume a real owner export, not a copied draft.

Exact target files that fit the current Playbook layout:

- `repos/fawxzzy-playbook/docs/contracts/PLAYBOOK_CONVERGENCE_CONTRACT.md`
- `repos/fawxzzy-playbook/exports/contracts/playbook-convergence-contract.v1.json`
- `repos/fawxzzy-playbook/exports/contracts/playbook-convergence-contract.schema.json`
- `repos/fawxzzy-playbook/packages/engine/test/playbookConvergenceContract.test.ts`
- update pointer in `repos/fawxzzy-playbook/docs/CONSUMER_INTEGRATION_CONTRACT.md` or `repos/fawxzzy-playbook/README.md`

Acceptance:

- one human-readable contract exists in `docs/contracts/`
- one machine-readable export exists in `exports/contracts/`
- one schema exists for downstream validation
- tests cover stable ids, required sections, and continuity requirements
- consumer docs tell downstream repos to reference the export instead of copying Playbook prose

### 2. ATLAS root consumption and continuity lane

ATLAS root should be ready to consume the Playbook export as soon as it lands.

Root-owned files now in scope:

- `schemas/atlas.continuity.handoff.v1.json`
- `docs/ops/ATLAS-CONTINUITY-LANE.md`
- `docs/ops/ATLAS-CONTINUITY-HARVEST-BACKLOG.md`

Next root follow-up after the Playbook export lands:

- update `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` to cite the published Playbook contract path and version
- update `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md` so statuses cite explicit contract-version evidence
- add or extend a read-only report surface that names `contract_version`, adoption state, and exceptions per repo

### 3. Core repo baselines

After Playbook export and root consumption:

1. `lifeline`
   - map approvals, governed writes, and receipts to exported pattern ids
   - use repo-local `pnpm run verify` as the acceptance gate
2. `_stack`
   - document merge, resume, and orchestration semantics against the exported contract
   - confirm whether this repo is intentionally local-only or missing a GitHub remote
3. `atlas`
   - align doctrine and retrieval routing to the exported contract
   - keep changes limited to docs and retrieval-facing references

### 4. First vertical tranche

Recommended order:

1. `fitness`
2. `mazer`
3. `stream`
4. `nat1-games`

Why `fitness` first:

- active repo with visible GitHub remote
- already uses both `.playbook/` and `.lifeline/`
- best candidate to prove owner-repo adoption without inventing new operator surfaces

## Do Not Do In This Wave

- do not copy Playbook owner truth into ATLAS root
- do not widen chat or cockpit execution power
- do not treat transcript history as the continuity system
- do not force incubating repos into tranche 1 without an explicit adoption or defer decision

## Q:

- Q: `_stack`, `fawxzzy-atlas`, and `fawxzzy-stream` have local git repos here, but no remote is visible in this workspace. Is local-only the intended posture, or should they be linked to GitHub repos before tranche rollout?
- Q: `fitness` is the strongest first vertical candidate from the current workspace. If you want a different tranche-1 vertical owner repo, name it explicitly before I shape repo-local adoption prompts around `fitness`.
