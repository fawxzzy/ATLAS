# Governed Runtime Repair Runbook

This runbook defines how ATLAS repairs post-cutover `governed_v1` runtime artifacts that no longer satisfy the current governed registry contract.

## Objective

Repair rebuildable governed runtime artifacts through canonical builders.

Do not hide or reclassify real post-cutover contract failures as legacy compatibility.

## Scope

The reconcile pass audits post-cutover runtime artifacts under:

- `runtime/atlas/sessions/**`
- `runtime/lifeline/worker-execution/**`
- `runtime/cortex/supervisor/**`

It repairs only artifacts that can be regenerated truthfully from root-owned canonical builders.

## Repair Policy

- Rebuildable derived runtime artifacts may be regenerated in place.
- Immutable evidence that cannot be rebuilt truthfully must remain visible and failing until replay replaces it.
- Do not hand-patch JSON when a canonical builder already exists.

## Remediation Matrix

| Validator bucket | Treatment | Rule |
| --- | --- | --- |
| `execution-receipt-repair-invalid` | repair through canonical builders | use canonical rebuilders or truthful Lifeline receipt supersession; do not hand-edit historical receipts |
| `mutable-state-warnings` | classify as retained residue / historical debt | keep residue visible and separate from current governed truth |
| `repo-local-config-gaps` | move into the debt ledger as inherited debt | keep explicit until the repo path or contract is intentionally closed |
| `path-discipline-leaks` | move into the debt ledger as inherited debt | burn down by repo slice without reopening healthy governed surfaces |
| `retained-runtime-residue` | classify as retained residue / historical debt | preserve history, prefer the canonical current artifact, and never silently rewrite old evidence |

## Repair, Supersede, Or Classify

- Repair when the artifact is derived runtime state and the current governed stack can rebuild it truthfully from canonical inputs.
- Supersede when the original receipt is immutable evidence but the current stack can prove the same outcome under the current registry digest.
- Classify as retained residue when the old artifact is historical, audit-relevant, or no longer the canonical current artifact.
- Move to the debt ledger when the finding is inherited stack debt rather than a live governed-path defect.

## Repair Vs Replay

- Repair is allowed only when the original execution outcome can be proven from existing governed evidence.
- Replay is required when the current stack can no longer prove what actually executed.
- Repair emits a new artifact and preserves the original evidence.
- Replay does not mutate the old receipt. It creates a new governed execution event later.

## Execution Receipt Supersession

Post-cutover Lifeline execution receipts are immutable evidence. When a receipt carries stale governed identity but the execution outcome can still be proven, Lifeline emits a new superseding receipt instead of rewriting the old file.

The superseding receipt must carry:

- `supersedes_receipt_ref`
- `repair_basis_refs`
- `reconciled_at`
- `reconciled_by_tool_version`
- the current truthful `registry_digest`

The original receipt remains visible for audit and history. Status, world-model generation, and Playbook verify should prefer the superseding receipt when present.

## Truthful Reconstruction Boundary

Execution receipts may be repaired only when ATLAS can prove the result from explicit artifacts such as:

- the original receipt
- the original privileged-action request
- the approval receipt
- the session manifest
- worker assignment, worker context, and worker status artifacts

ATLAS may reconstruct governed identity from the canonical request and approval artifacts. ATLAS may not invent:

- a result that was never evidenced
- a command result or inspection payload that is not supported by existing artifacts
- governed identity for an execution with missing or contradictory source evidence

## Canonical Repair Coverage

The root reconcile utility currently rebuilds:

- session manifests
- capability profiles
- worker assignments
- worker status artifacts
- privileged action requests
- approval receipts
- supervisor merge-request artifacts

The root lane does not currently rebuild Lifeline execution receipts in place.

Those receipts are handled by the Lifeline repair utility, which emits superseding receipts when truthful repair is possible and emits `replay_required` attention when it is not.

## Command

Audit without writing:

```powershell
python .\ops\atlas\reconcile_governed_runtime_artifacts.py
```

Apply rebuildable repairs:

```powershell
python .\ops\atlas\reconcile_governed_runtime_artifacts.py --apply
```

Repair privileged-action receipts truthfully:

```powershell
pnpm -C .\repos\fawxzzy-lifeline repair:privileged-receipts -- --atlas-root .
```

The utility writes its latest report to:

- `runtime/state/atlas/governed-runtime-repair/latest.json`

## Expected Outcomes

- Rebuildable post-cutover artifacts are restamped against the current registry digest and canonical tool surface.
- The world model and status snapshot are refreshed after apply.
- Repairable Lifeline execution receipts gain superseding receipts without mutating the originals.
- Remaining red should represent replay-required receipts or unrelated historical repo debt, not stale governed runtime derivatives.

## Non-Goals

- Do not mutate pre-cutover `legacy_pre_registry` evidence.
- Do not fabricate governed identity for artifacts that lack trustworthy source evidence.
- Do not suppress failing post-cutover receipts by reclassifying them as legacy.
