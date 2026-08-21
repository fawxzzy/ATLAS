# Atlas Engineering Memory Terminal Enforcement

Date: 2026-08-21

Final status: complete

Execution truth: installed

## Bounded objective

Close the remaining Atlas Engineering Memory enforcement gap so a worker cannot
claim success from summary text alone. Every currently admitted engineering
source-mutation executor must bind rough intake and precedent evidence before
mutation, then reconcile runner-owned technical proof, required visual/manual
proof, and a repository-visible completion archive before commit or terminal
success.

## Installed lifecycle

```text
rough note
  -> existing JobEnvelope + stable CardRecord
  -> precedent search + mutation gate
  -> bounded worker mutation
  -> runner verification + worker closeout
  -> verify gate
  -> repository docs archive
  -> archive gate
  -> archived JobEnvelope + CardRecord
  -> ExecutionReceipt + prompt archive
```

The worker writes only the closeout input and required repository completion
record. `_stack` owns technical verification and invokes the Atlas-root terminal
reconciler. The reconciler validates the exact job/card identity, merges runner
and worker evidence, applies the verify and archive gates, and is the only path
that advances the correlated JobEnvelope and CardRecord to terminal state.

Verified no-change runs use a narrowly bounded runner-generated closeout under
the run log and require validated no-change proof. That path cannot authorize a
source mutation or substitute for the `docs/` archive required after mutation.

## Producer boundary

The inventory at
`docs/registry/ATLAS-ENGINEERING-MEMORY-PRODUCER-INVENTORY.v1.json` classifies
the two current admitted mutating executors:

- `stack.repo-task`
- `stack.canonical-workspace`

The inbox runner, scheduled inbox sweep, Atlas session resume, and Cortex stack
dispatch delegate to those executors. Lifeline privileged execution,
thread-lifecycle recovery, and evidence-only canaries are explicitly excluded
because they do not launch Codex source implementation. The inventory contains
zero uninstalled admitted mutating executors. Any future direct launcher starts
uninstalled until the same mutation, verify, and archive gates are proven in CI.

## Contract and implementation surface

Atlas root owns:

- `ops/atlas/prepare_engineering_memory_job.mjs`
- `ops/atlas/engineering_memory_gate.mjs`
- `ops/atlas/complete_engineering_memory_job.mjs`
- the Engineering Memory profile, closeout, and runner-verification schemas
- policy, producer inventory, architecture, fixtures, and focused tests

`_stack` owns:

- producer integration in `ops/codex/AtlasContractsV2Producer.ps1`
- repo-task and canonical-workspace terminal invocation
- operator, producer, and workspace-writer integration fixtures
- versioned CI snapshots of the root-owned helpers and schemas
- operator documentation and workspace-manifest artifact declarations

No second task protocol, result protocol, queue, board, scheduler, or schema
engine was introduced.

## Verification performed

- Engineering Memory focused Node suite:
  - 15 passed, 0 failed
  - covers intake, precedent, mutation, visual, closeout, terminal reconciliation,
    and producer inventory behavior
- `npm --prefix packages/atlas-contracts run validate`:
  - contract fixture validation passed
  - artifact-validator tests passed
- `_stack` operator surface:
  - passed, including mutating closeout and validated no-change closeout paths
- `pnpm --dir repos/_stack run codex:stack:verify`:
  - authoritative local suite passed
  - covered branding, inbox lifecycle, producer, operator, canonical writer,
    worker artifacts, adoption contracts, board export, and board-export tests
- Node syntax checks for the gate and terminal reconciler passed.
- Policy, inventory, and workspace-manifest JSON parse checks passed.

Expected negative-path fixtures emitted their stable errors and were accepted
by the suite. They cover invalid worker Git mutation, unsupported setup,
unapproved or malformed no-change proof, failed verification, missing visual
surface proof, and invalid terminal archival evidence.

## Verification not performed

- No GitHub-hosted workflow was dispatched. The versioned CI fixture and exact
  authoritative local command passed.
- No real owner-repository Codex task was launched. Integration proof uses the
  deterministic fake-worker harness.
- Lifeline bridge execution fixtures were skipped because
  `repos/lifeline/dist/cli.js` is absent in this checkout. The worker-artifact and
  owner-adoption checks still passed.
- No owner UI changed, so no new route-aware visual capture was required.
- The unrelated Atlas Codex-context topology-proposal blocker was not changed.

## Decisions and reusable learning

Decision: Terminal lifecycle advancement is runner-owned. A worker may propose
evidence but cannot mark its own JobEnvelope/CardRecord verified or archived.

Rule: A mutating engineering task cannot commit or emit successful terminal
truth until both verify and archive gate receipts pass for the exact job/card
identity.

Pattern: Merge worker-owned visual/manual evidence with runner-owned technical
exit evidence at one root-owned reconciliation seam.

Failure Mode: Worker summary truth can drift from executed proof. Treat the
summary as input, not terminal authority.

Failure Mode: A runtime closeout can disguise missing documentation. Allow the
runtime archive form only for a validated no-change run; mutations require a
completion record inside the bound workspace `docs/` tree.

## Authority and repository health

- Atlas root remained on `main`, behind `origin/main` by 30 commits, with
  extensive pre-existing dirty and untracked state preserved.
- `_stack` remained on current `main`; only the bounded task files are modified
  or untracked there.
- No stage, commit, push, branch creation, PR, review request, merge, provider
  mutation, deployment, live-data mutation, production action, or destructive
  cleanup was performed.

## Completion boundary

The originally requested rough-note-to-archive enforcement chain is locally
installed and source-proven for every currently admitted engineering mutation
executor. No required implementation follow-up remains. Hosted CI, commit,
review, merge, and deployment stay separate lifecycle gates.
