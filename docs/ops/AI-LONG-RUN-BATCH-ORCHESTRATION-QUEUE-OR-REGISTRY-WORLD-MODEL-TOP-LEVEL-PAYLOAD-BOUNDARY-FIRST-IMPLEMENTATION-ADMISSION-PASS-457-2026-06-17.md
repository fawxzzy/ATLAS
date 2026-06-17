# AI Long-Run Batch Orchestration Queue-Or-Registry World-Model Top-Level Payload Boundary First-Implementation Admission Pass 457 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded first-implementation admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-CONTRACT-FREEZE-PASS-454-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-OWNER-SURFACE-ADMISSION-PASS-455-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-WORLD-MODEL-TOP-LEVEL-PAYLOAD-BOUNDARY-SUPPORTING-LANE-ADMISSION-PASS-456-2026-06-17.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@c957009a`

## Objective

Freeze one compact authoritative first implementation slice for the root-owned top-level `world_model` payload boundary plus one proof matrix for validating that slice without crossing the no-builder-mutation, no-snapshot-generation, no-attention-generation, no-top-level-registry-change, no-top-level-artifact-inventory-change, and no-runtime-mutation boundary.

## Exact First Admitted Implementation Slice

The first admitted implementation slice is:

1. one direct `world_model_state()` ref-and-presence layer that:
   - resolves the snapshot path to `runtime/state/atlas/world-model.snapshot.latest.json`
   - resolves the attention path to `runtime/state/atlas/world-model.attention.latest.json`
   - emits top-level `snapshot_ref` and `attention_ref` through `atlas_relative(...)`
   - emits top-level `snapshot_present` and `attention_present` through `Path.exists()`
2. one snapshot dict branch that, for a present readable JSON object payload only:
   - preserves `snapshot_content_digest` as `payload.get("content_digest")`
   - preserves `inventory_entry_count` as `len(inventory_entries)` when `inventory_entries` is a list, else `0`
   - preserves `observation_count` as `len(observations)` when `observations` is a list, else `0`
3. one attention dict branch that, for a present readable JSON object payload only:
   - preserves `attention_content_digest` as `payload.get("content_digest")`
   - preserves `attention_item_count` as `len(attention_items)` when `attention_items` is a list, else `0`
4. one fail-closed loader layer where:
   - absent files skip all content-derived fields for that file
   - unreadable or undecodable files skip all content-derived fields for that file
   - non-dict decoded payloads skip all content-derived fields for that file
5. one unchanged top-level `render_status_payload(...)` handoff through `payload["world_model"]`
6. one preserved separation layer where top-level `world_model` meaning remains distinct from top-level `artifact_inventory` and top-level `registry`

## Exact Preserved Payload Surface

The worker must preserve only:

- `snapshot_ref`
- `attention_ref`
- `snapshot_present`
- `attention_present`
- `snapshot_content_digest`
- `inventory_entry_count`
- `observation_count`
- `attention_content_digest`
- `attention_item_count`

Top-level payload rules remain:

- `snapshot_ref` and `attention_ref` are always present
- `snapshot_present` and `attention_present` are always present
- absent files preserve the refs plus `False` presence booleans without content-derived fields for that file
- present readable JSON object payloads may emit:
  - digest fields through direct `payload.get("content_digest")`
  - bounded count fields through list-length checks or `0` fallback
- unreadable, undecodable, or non-dict present payloads preserve refs and presence booleans while omitting content-derived fields for that file
- no snapshot body hydration, observation-body hydration, attention-item hydration, descriptor inventory widening, or registry-summary widening may leak into top-level `world_model`
- `render_status_payload(...)` preserves the same bounded helper output under top-level `world_model` only
- top-level `artifact_inventory` and top-level `registry` remain separate read-model consequences rather than part of the top-level `world_model` payload

## Exact Mandatory Proof Cases

1. no world-model files present
   - `world_model_state()` emits only refs and `False` presence booleans
   - no content-derived fields appear

2. snapshot populated dict branch
   - a readable snapshot dict preserves `snapshot_content_digest`
   - `inventory_entry_count` equals the snapshot `inventory_entries` list length
   - `observation_count` equals the snapshot `observations` list length

3. attention populated dict branch
   - a readable attention dict preserves `attention_content_digest`
   - `attention_item_count` equals the attention `attention_items` list length

4. bounded count fallback
   - snapshot count fields fall back to `0` when `inventory_entries` or `observations` are missing or not lists
   - attention count falls back to `0` when `attention_items` is missing or not a list

5. fail-closed content omission
   - present unreadable, undecodable, or non-dict files preserve refs and `True` presence booleans
   - content-derived fields for the failed file stay omitted

6. render-status handoff preservation
   - `render_status_payload(...)` preserves the helper result under top-level `world_model`
   - the handoff does not widen into top-level `artifact_inventory` or top-level `registry` semantics

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry world_model top-level payload boundary prompt-pack and handoff contract pass 458`

## Marker Decision

- `none`

Why:

- this pass freezes the smallest exact implementation slice and proof matrix only
- no code landing, proof execution, or broader operator adoption occurs here

## Rule

Freeze the smallest top-level world-model payload slice and proof matrix before admitting implementation or widening into builder semantics, snapshot generation, attention generation, registry semantics, artifact inventory semantics, or runtime mutation.
