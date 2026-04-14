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

## Canonical Repair Coverage

The root reconcile utility currently rebuilds:

- session manifests
- capability profiles
- worker assignments
- worker status artifacts
- privileged action requests
- approval receipts
- supervisor merge-request artifacts

The root lane does not currently rebuild Lifeline execution receipts. Those remain `replay_required`.

## Command

Audit without writing:

```powershell
python .\ops\atlas\reconcile_governed_runtime_artifacts.py
```

Apply rebuildable repairs:

```powershell
python .\ops\atlas\reconcile_governed_runtime_artifacts.py --apply
```

The utility writes its latest report to:

- `runtime/state/atlas/governed-runtime-repair/latest.json`

## Expected Outcomes

- Rebuildable post-cutover artifacts are restamped against the current registry digest and canonical tool surface.
- The world model and status snapshot are refreshed after apply.
- Remaining red should represent replay-required receipts or unrelated historical repo debt, not stale governed runtime derivatives.

## Non-Goals

- Do not mutate pre-cutover `legacy_pre_registry` evidence.
- Do not fabricate governed identity for artifacts that lack trustworthy source evidence.
- Do not suppress failing post-cutover receipts by reclassifying them as legacy.
