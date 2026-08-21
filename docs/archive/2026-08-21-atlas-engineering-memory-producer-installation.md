# Atlas Engineering Memory Producer Installation

Date: 2026-08-21

Final status: complete

Execution truth: installed

## Bounded objective

Install the source-proven Atlas Engineering Memory gate at the existing shared
`_stack` producer seam, keep rough user input simple, fail closed before Codex
mutation, prove the local trigger-to-successor chain, and carry the evidence
through the existing ExecutionReceipt without creating another task or result
protocol.

## Repository identity

- Atlas root branch: `main`
- Atlas root starting commit: `1f7a9141cd329866bb3ec45602e335e1c725bb23`
- `_stack` branch: `main`
- `_stack` starting commit: `7aed5495d2702a653e461549877d8fa77b3a33d2`
- No commit, push, merge, deployment, provider mutation, or production action
  was performed.

## Installed behavior

The shared repo-task and canonical-workspace producers now execute this order
before Codex starts:

```text
rough prompt
  -> stable CardRecord identity
  -> normalized EngineeringMemoryProfile in the existing JobEnvelope
  -> deterministic current-workspace and Atlas-doc precedent search
  -> schema and semantic validation
  -> root-owned mutation gate
  -> Codex invocation
```

The worker receives exact paths for the rough-note source, CardRecord,
precedent-search record, and passed mutation-gate receipt. The terminal
ExecutionReceipt retains those evidence refs. Accepted integration-fixture work
continues into the existing prompt archive, proving successor processing.

## Files changed

### Atlas root

- `ops/atlas/prepare_engineering_memory_job.mjs`
- `tests/test_atlas_engineering_memory_intake.mjs`
- `docs/architecture/ATLAS-ENGINEERING-MEMORY-ENFORCEMENT.md`
- `docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json`
- this completion archive

### `_stack`

- `ops/codex/AtlasContractsV2Producer.ps1`
- `ops/codex/Invoke-CodexRepoTask.ps1`
- `ops/codex/Test-AtlasContractsV2Producer.ps1`
- `ops/codex/Test-StackOperatorSurface.ps1`
- `ops/codex/Test-AtlasWorkspaceWriter.ps1`
- `README.md`
- `docs/codex-orchestration.md`
- `docs/dispatcher-protocol.md`
- `workspace.manifest.json`
- the versioned `tests/fixtures/ci-workspace/**` Atlas contract, gate, normalizer,
  and manifest snapshots required by hosted `_stack` verification

## Decisions and reusable learning

Decision: Producer enforcement belongs at the existing
`atlas.job-envelope.v2` / `atlas.card-record.v2` seam. `_stack` remains a facts
producer and invokes Atlas-root normalization and gate logic instead of owning a
second schema engine.

Pattern: A rough note can receive a retry-stable card identity derived from the
project, owner repository, and original source text while each execution keeps
its own JobEnvelope identity.

Failure Mode: Prompt-only precedent guidance is bypassable. Prevent it by
requiring a content-bound gate receipt before the process invocation exists.

Rule: Producer installation does not widen source, Git, provider, deployment,
production, live-data, or destructive authority.

## Verification performed

- `node --test tests/test_atlas_engineering_memory_gate.mjs tests/test_atlas_engineering_memory_intake.mjs`
  - 10 passed, 0 failed
- `npm --prefix packages/atlas-contracts run validate`
  - contract fixtures passed
  - artifact-validator tests passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File repos/_stack/ops/codex/Test-AtlasContractsV2Producer.ps1`
  - passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File repos/_stack/ops/codex/Test-StackOperatorSurface.ps1`
  - passed, including rough-note trigger, pre-worker gate, fake Codex execution,
    terminal receipt, and accepted prompt archive
- `powershell -NoProfile -ExecutionPolicy Bypass -File repos/_stack/ops/codex/Test-AtlasWorkspaceWriter.ps1`
  - passed
- `pnpm --dir repos/_stack run codex:stack:verify`
  - authoritative local `_stack` verification passed
  - included inbox, operator, canonical writer, worker-artifact, adoption,
    board-export, and board-export test surfaces
- root and `_stack` `git diff --check`
  - passed; line-ending warnings only
- Node syntax checks for both root engineering-memory scripts
  - passed

## Verification not performed

- No GitHub-hosted workflow was dispatched. Its versioned fixture and the exact
  local authoritative command passed.
- No real Codex worker was launched against an owner repository; integration
  proof uses the existing deterministic fake-worker harness.
- No owner-repository UI was changed or visually verified in this phase.
- The unrelated full `tests.test_atlas_codex_context` topology-proposal blocker
  was not repaired or broadened into this task.

## Known risks and remaining boundaries

- Deterministic precedent discovery is lexical and intentionally conservative.
  The worker must inspect the bound matches; a filename or token match is not
  automatic reuse authority.
- The shared `_stack` repo-task and canonical-workspace producers are installed.
  The current producer inventory proves that every other admitted engineering
  entrypoint delegates to one of them.
- Terminal verify/archive enforcement is now installed and independently
  reconciled by the runner. See
  `docs/archive/2026-08-21-atlas-engineering-memory-terminal-enforcement.md`.
- Changes remain local and uncommitted in Atlas root and `_stack`.

## Follow-up resolution

1. Terminal producer closeout is installed and fail closed.
2. The exact current producer boundary is inventoried with zero uninstalled
   admitted mutating executors.
3. Hosted `_stack` CI remains a later commit/push/PR lifecycle boundary; its
   versioned fixture is covered by the authoritative local suite.
4. The unrelated topology proposal reference remains outside this task.
