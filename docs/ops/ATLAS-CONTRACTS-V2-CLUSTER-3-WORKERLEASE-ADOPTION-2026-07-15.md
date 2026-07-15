# ATLAS Contracts v2 Cluster 3 WorkerLease Adoption

## Deterministic Evidence

`_stack` PR `fawxzzy/_stack#8` merged the governed WorkerLease producer at merge commit `40ab40f`. The terminal canary `20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2` ran from published `_stack/main` with Sol/high, full local access, live web search, and no approvals. It completed as `success_no_changes`, changed no tracked paths, and produced a released WorkerLease with canonical validation and receipt binding.

The independent Atlas-root consumer canonically validated exactly seven declared artifacts:

| Family | Atlas-relative artifact | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| ComponentManifest | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.component-manifest.v2.json` | `sha256:66b818993c7ec50167f0f2cb7724e72289f05494da774e7e4e9f37a64038a553` | 1,396 |
| JobEnvelope | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.job-envelope.v2.json` | `sha256:0eabf3075b76eebadf956ce3a1efa5b734b12217fef862150b7285ec71e0f9a9` | 4,217 |
| ContextPacket | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.context-packet.v2.json` | `sha256:7d9331d896e2f2a937a0ecbc55d2b4120358d35bd8fd21b57131fa07414937e6` | 4,092 |
| ApprovalRecord | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.approval-record.v2.json` | `sha256:2fa6fd3f51a5a6a3239aa0ae00898b421fd4f6e4fdfaff0719809e5569cc9ffe` | 1,223 |
| WorkerLease | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.worker-lease.v2.json` | `sha256:05d0ad1d37549f17b4155ad49cde562200d000a6fe54bc803562ca9e6c8ca3e8` | 2,775 |
| EvidenceBundle | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.evidence-bundle.v2.json` | `sha256:5ba69374446ac8a991a48e13ff91a7dcf8aeb79d8a8c8dbdc44b9f29757e09d8` | 1,645 |
| ExecutionReceipt | `repos/_stack/.codex/logs/20260715T134932158Z-atlas-contracts-v2-cluster-3-workerlease-no-change-canary-2/atlas.execution-receipt.v2.json` | `sha256:3dba1a4e2db1c38f0b1692c9df75f50ed71f97066ef8eae671496b41680d13a1` | 13,033 |

## WorkerLease Admission

The accepted lease correlates the exact job, component, run, worker, native thread, task branch, and isolated worktree. Its exclusive claims match the actual worktree and branch. The same artifact transitions from validated `active` preflight state to validated `released` terminal state with monotonic timestamps, `release_proven: true`, and a durable run-manifest recovery checkpoint. The ExecutionReceipt binds the lease ID, released status, artifact path, terminal SHA-256 digest, and both validation evidence references.

The root rejection matrix fails closed on lease/job drift, a stale active terminal lease, false resource identity, malformed terminal validation evidence, and digest drift. Existing path, schema, identity, authority, verification, blocker, and Git-integrity rejection cases remain green.

## Ratchet

Seven families are accepted: ComponentManifest, JobEnvelope, ContextPacket, ApprovalRecord, WorkerLease, EvidenceBundle, and ExecutionReceipt. Four remain unaccepted: CardRecord, BoardEvent, MarkerEvidence, and KnowledgeCandidate.

The Atlas Contracts Mesh therefore moves from `6/11` (`55%`) to `7/11` (`64%`). This receipt does not claim adoption for the remaining families or completion of the full-system closing audit.

## Verification and Boundaries

- `pnpm run codex:stack:verify`: passed on `_stack` commit `8e9fea3` before merge.
- `powershell -NoProfile -ExecutionPolicy Bypass -File ops/codex/Test-AtlasContractsV2Producer.ps1`: passed independently.
- `node ops/atlas/test_validate_contracts_v2_adoption.mjs`: passed the real seven-artifact canary and Cluster 1-3 rejection matrix.
- `npm --prefix packages/atlas-contracts run validate`: passed.
- `git diff --check`: passed.

No deployment, Discord mutation, board mutation, or production-data mutation occurred. The `_stack` producer landed separately through PR `#8`; the Atlas-root reconciliation did not mutate another owner repository. The first canary attempt was interrupted after preflight by the command wrapper and is retained as recovery evidence; only the terminal `-2` run is adoption evidence.
