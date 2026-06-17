# AI Long-Run Batch Orchestration Queue-Or-Registry Legacy-Compatibility Top-Level Payload Boundary Contract Freeze Pass 405 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-CONTRACT-FREEZE-PASS-398-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-FIRST-IMPLEMENTATION-ADMISSION-PASS-401-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-PROMPT-PACK-AND-HANDOFF-CONTRACT-PASS-402-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-PASS-403-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-NEXT-SLICE-SELECTION-PASS-404-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `stack.yaml`
  - `AGENTS.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze one exact root-bounded contract for the top-level `legacy_compatibility` payload so the post-queue legacy status surface becomes restart-safe without reopening broader `attention_queue` semantics, legacy repair work, archive action, governed-v1 blocker doctrine, or runtime mutation.

This pass does not implement code, change queue routing, widen legacy classification, or move any marker.

## Root Health Baseline

- pass 404 already selected `legacy_compatibility` top-level payload boundary as the smallest honest follow-on after the broader queue family was exhausted
- passes 398 through 403 already froze and proved:
  - the bounded `legacy_compatibility_signal` queue seam
  - the separation between the richer top-level legacy payload and the lower-severity queue signal
  - the preserved top-level handoff through `render_status_payload(...)`
- `ops/cortex/render_status.py` already expresses the unfrozen adjacent seam in `legacy_compatibility_surfaces(...)`
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`

## Frozen Family Contract

### `family_name`

- `legacy_compatibility top-level payload boundary`

### `trigger`

- the queue-side `legacy_compatibility_signal` seam is already decided, integrated, and restart-safe
- the status payload still retains a separate top-level `legacy_compatibility` array whose contract is only implicit in `legacy_compatibility_surfaces(...)`
- the smallest remaining bounded seam is the explicit meaning of that top-level legacy payload, not broader queue semantics and not legacy remediation behavior

### `stable_inputs`

- the bounded queue-side legacy signal contract and proof from passes 398 through 404
- the current helper and test surfaces in:
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
- the retained stack-governance doctrine in:
  - `stack.yaml`
  - `AGENTS.md`

### `expected_artifact`

- one exact bounded top-level `legacy_compatibility` payload contract only
- the contract may freeze only:
  - the top-level payload surface as one array of descriptor-backed compatibility records
  - the item qualifier:
    - only descriptors with `artifact_type = "legacy_runtime_backfill"` participate
    - only records with truthy trimmed `source_ref` survive into the top-level payload
  - the top-level item fields:
    - `session_id`
    - `source_ref`
    - `original_session_ref`
    - `epoch`
    - `cutover_at`
    - `observed_at`
    - `recorded_at`
    - `missing_governed_requirements`
    - `governed_identity`
  - the deterministic ordering rule:
    - `observed_at`
    - then `session_id`
    - then `source_ref`
  - the top-level meaning rule:
    - this payload remains the fuller legacy compatibility status surface
    - it may preserve richer historical timing and governed-identity context than the queue signal
  - the separation rule:
    - top-level `legacy_compatibility` remains the fuller bounded status payload
    - `attention_queue` remains the separate derived operator-signal surface that may emit only the smaller `legacy_compatibility_signal` subset

### `failure_boundary`

- the top-level payload starts acting like a broader `attention_queue` contract
- the top-level payload collapses into the lower-severity queue signal and loses the richer timing or governed-identity context already present on canonical `main`
- the top-level payload starts implying archive action, repair action, governed-v1 blocker semantics, or runtime mutation instead of bounded status reporting
- the item contract widens beyond descriptor-backed `legacy_runtime_backfill` records with truthy `source_ref`

### `safe_fallback`

- keep the top-level payload separate from queue routing
- keep the payload descriptor-backed and deterministic
- preserve the existing richer legacy fields only
- fail closed to an empty list when no qualifying descriptor-backed legacy records exist
- stop below archive, repair, governed-v1 blocker, or mutation claims

### `owner_boundary`

- ATLAS root owns this contract freeze, restart projection, and non-claim boundaries
- exact code-level helper changes or proof-hardening changes remain a separate next-pass owner-surface question
- owner repos keep mutation truth, verification truth, and implementation truth

### `non_claim_boundary`

- no code or test implementation change
- no queue-ordering, queue-budget, or queue-family change
- no archive action, repair action, governed-v1 blocker widening, or runtime mutation claim
- no queue, registry, session, merge, deployment, or runtime mutation claim
- no supervisor/operator proof claim

## Supporting Dependency Decision

- `none yet`

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry legacy_compatibility top-level payload boundary owner-surface admission pass 406`

## Marker Decision

- `none`

## Rule

Freeze the top-level `legacy_compatibility` payload boundary before reopening broader legacy remediation, archive, blocker, or redesign families.
