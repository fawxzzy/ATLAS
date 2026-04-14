# Legacy Runtime Backfill Runbook

This runbook defines how ATLAS backfills pre-cutover runtime history into descriptor-backed compatibility records without mutating historical evidence.

## Objective

Backfill `legacy_pre_registry` runtime artifacts into queryable compatibility records so awareness, status, and Playbook can reason about historical sessions through one governed read model.

Backfill does not promote historical artifacts into `governed_v1`.

## Inputs

The backfill tool reads legacy evidence from:

- `runtime/atlas/sessions/**`
- `runtime/lifeline/worker-execution/**`
- `runtime/cortex/supervisor/**`

The original manifests, receipts, and status artifacts remain immutable source evidence.

## Outputs

Backfill writes compatibility records to:

- `runtime/state/atlas/legacy-backfill/<session_id>.json`

Backfill registers descriptor surfaces under:

- `runtime/cortex/artifacts/runtime/state/atlas/legacy-backfill/*.descriptor.json`

Backfill emits compatibility observations under:

- `runtime/state/atlas/observations/legacy-backfill/governed_compatibility/**`

## Command

Run the deterministic backfill pass:

```powershell
python .\ops\atlas\backfill_legacy_runtime_artifacts.py
```

Rebuild the root world model after backfill:

```powershell
python -m ops.atlas.awareness
```

## Provenance Rules

- Never overwrite original runtime manifests, receipts, or worker status artifacts.
- Every backfill record must carry:
  - `original_session_ref`
  - `source_refs`
  - `source_ref_digests`
  - `observed_at`
  - `recorded_at`
  - `tool_version`
  - `inference_basis`
- Backfill output must be deterministic on unchanged inputs.

## Inference Rules

- Infer governed identity only from explicit values present in legacy sources.
- If no explicit value is provable, record the field as `unknown_legacy`.
- If legacy sources conflict, record the field as `conflict_legacy`.
- Do not synthesize `tool_id`, `extension_id`, or `registry_digest` from guesswork.

## Query Surface

Backfilled sessions become queryable through descriptor-backed world-model inventory and `governed_compatibility` observations.

Status and awareness must read the backfill descriptors, not re-derive compatibility directly from raw manifests.

## Verification

- Running the backfill tool twice on unchanged inputs produces no record changes.
- Historical sessions appear in `legacy_compatibility` through descriptor-backed records.
- Unknown governed identity surfaces remain `unknown_legacy`.
- Original runtime evidence remains untouched.
- `pnpm -C repos/fawxzzy-playbook playbook verify --json` no longer reports legacy no-dark-state failures once the world model is rebuilt.
