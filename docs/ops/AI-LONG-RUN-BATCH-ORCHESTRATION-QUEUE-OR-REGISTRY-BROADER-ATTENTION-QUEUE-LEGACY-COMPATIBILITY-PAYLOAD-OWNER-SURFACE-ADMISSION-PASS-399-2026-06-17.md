# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Legacy-Compatibility-Payload Owner-Surface Admission Pass 399 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `docs/ops/GOVERNED-ARTIFACT-EPOCHS.md`
  - `docs/ops/LEGACY-RUNTIME-BACKFILL-RUNBOOK.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-CONTRACT-FREEZE-PASS-398-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze the exact owner-facing home for the bounded `legacy_compatibility_payload` queue seam after the contract itself is explicit.

This pass decides ownership only.

It does not:

- widen the queue contract
- admit implementation
- admit support-lane or owner-repo execution
- mutate legacy backfill descriptors, runtime evidence, queue state, registry state, archive posture, or owner-repo state

## Admitted Owner-Facing Home

The exact owner-facing home for this queue seam remains inside ATLAS root only.

Producing and consuming truth stays inside:

- descriptor-backed legacy backfill truth already admitted into `legacy_compatibility_surfaces(descriptors)`
- root-local legacy-epoch compatibility classification already carried by `legacy_compatibility_payload`
- the status helper seam inside `ops/cortex/render_status.py`
- `attention_queue(...)`
- `render_status_payload(...)`
- root ATLAS-side queue consumers that observe `attention_queue` or `attention_kinds` output without redefining this family contract
- root restart mirrors:
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

## Why Ownership Stays Root-Local

- the family is still one bounded projection of root-owned descriptor-backed compatibility records plus root-owned status and queue helpers
- the admitted queue payload is still control-plane visibility truth rather than governed-v1 blocker doctrine, archive doctrine, repair authority, or owner-repo product truth
- the producing helper and consuming queue code already live together in `ops/cortex/render_status.py`
- restart and routing truth for this family remains rooted in ATLAS-side receipt and restart surfaces

## Explicit Non-Owners

The following remain outside the admitted owner-facing home:

- `_stack`
- Playbook
- owner repos
- archive doctrine
- legacy repair doctrine
- governed-v1 blocker doctrine
- governed-identity resolution doctrine beyond the already-admitted queue payload

They may later consume consequences from this family, but they do not own its contract or current control-plane projection.

## Boundary Clarification

Admitting ATLAS root ownership means only:

- the family contract is defined here
- the family implementation seam is owned here
- the family restart narration is owned here

It does not mean:

- root may rewrite original legacy evidence
- root may promote legacy history into governed-v1 completeness
- root may claim archive, deletion, or repair authority
- root may claim owner-repo authority

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue legacy_compatibility_payload supporting-lane admission pass 400`

Why:

- the contract and owner-facing home are now explicit
- the next honest question is whether this family reopens any shared support dependency or still honestly holds at `none yet`

## Marker Decision

- `none`

Why:

- this pass clarifies owner placement only
- no new implementation, proof, or blocker conversion landed

## Rule

If one legacy-compatibility queue family is still produced and consumed entirely inside ATLAS-root descriptor, status, and restart helpers, keep ownership root-local until a real shared helper, archive, repair, or owner-repo dependency actually appears.
