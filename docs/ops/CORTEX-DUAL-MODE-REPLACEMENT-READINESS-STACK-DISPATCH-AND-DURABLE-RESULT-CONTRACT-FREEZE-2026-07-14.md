# Cortex Dual-Mode Replacement Readiness _stack dispatch and durable result contract freeze

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `docs-only cross-plane dispatch and durable-result contract freeze`
- Marker movement: none; remains `90%`

## Decision

Cortex primary-operator admission and replay parity are implemented. The next threshold is one bounded real dispatch through the existing `_stack` operator plane with durable acceptance-to-result correlation.

No new queue, scheduler, agent runtime, or execution backend is authorized.

Machine-readable doctrine:

- `docs/registry/CORTEX-PRIMARY-OPERATOR-STACK-DISPATCH-CONTRACT.v1.json`

## Existing execution spine

The contract adopts existing `_stack` surfaces:

- command: `codex:stack:task`;
- runner: `repos/_stack/ops/codex/Invoke-CodexRepoTask.ps1`;
- preflight and terminal contracts: `repos/_stack/ops/codex/AtlasContractsV2Producer.ps1`;
- durable runner manifest: `.codex/logs/<run-id>/run.json`;
- preflight `atlas.job-envelope.v2`;
- terminal `atlas.execution-receipt.v2` and EvidenceBundle.

`_stack` already validates Atlas Contracts v2 before Codex launch, denies external authority, and produces terminal receipts for success and failure.

## Correlation chain

```text
acceptance_id
-> dispatch_request.session_id
-> JobEnvelope.correlations.parent_job_id
-> JobEnvelope.job_id
-> run.json run identity
-> ExecutionReceipt.job_id
-> Cortex result-correlation identity
```

The terminal result is accepted only when the complete chain matches and both Atlas Contracts v2 artifacts validate.

## First canary

The first runtime proof is a verified no-change `_stack` task:

- `Allow No Changes: true`;
- explicit temporary proof under the task worktree `.codex/`;
- no accepted mutation criteria or changed paths;
- `-NoCommit` and manual-only push;
- full local capability, no external-action authority;
- terminal status `success_no_changes`;
- zero changed paths, commits, pushes, deployments, Discord writes, board writes, or data mutations.

This is a real Codex dispatch, not a fake runner fixture, but it is deliberately non-mutating.

## Implementation boundary

Allowed root implementation:

- `ops/cortex/primary_operator_stack_dispatch.py`
- `tests/test_cortex_primary_operator_stack_dispatch.py`

Owner-repository changes are not presumed. The implementation must first prove whether the existing `_stack` handoff and Atlas Contracts v2 surfaces are sufficient. Any exact owner-side gap requires a separate bounded `_stack` packet.

## Marker decision

The marker remains `90%`.

The contract does not prove dispatch. Marker movement is available only after the real verified no-change canary, durable correlation, and independent endgame review.

## Exact next packet

```text
Cortex Dual-Mode Replacement Readiness _stack dispatch and durable result first implementation
```

## Reusable knowledge

**RULE - Reuse the registered operator plane**

An internal reasoning system must enter execution through the existing governed runner rather than creating a parallel process manager.

**PATTERN - Correlation by parent job**

Carry the acceptance identity into the operator JobEnvelope as `parent_job_id`, then reconcile the terminal receipt against both job and run identities.

**FAILURE MODE - Dispatch without durable parentage**

A worker runs successfully, but its result cannot be proven to belong to the accepted Cortex decision that launched it.
