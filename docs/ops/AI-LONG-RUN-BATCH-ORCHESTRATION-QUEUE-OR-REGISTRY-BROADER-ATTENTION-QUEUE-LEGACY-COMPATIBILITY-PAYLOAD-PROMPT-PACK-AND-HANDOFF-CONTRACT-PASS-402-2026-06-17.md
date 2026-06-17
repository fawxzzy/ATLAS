# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Legacy-Compatibility-Payload Prompt-Pack And Handoff Contract Pass 402 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded handoff-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-CONTRACT-FREEZE-PASS-398-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-OWNER-SURFACE-ADMISSION-PASS-399-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-SUPPORTING-LANE-ADMISSION-PASS-400-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-LEGACY-COMPATIBILITY-PAYLOAD-FIRST-IMPLEMENTATION-ADMISSION-PASS-401-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze one compact authoritative prompt-pack and handoff contract for the already-admitted first implementation slice of the root-local `legacy_compatibility_signal` family inside the broader `attention_queue` render-status surface.

This pass does not:

- implement or widen code
- change queue-budget, overflow, or provenance-derived family behavior
- mutate queue, registry, runtime, session, merge, manifest, archive, repair, or owner-repo state
- reopen `_stack`, Playbook, archive doctrine, repair doctrine, governed-v1 blocker doctrine, or owner-repo support
- widen into archive action, repair action, governed-v1 blocker semantics, or top-level `legacy_compatibility` payload redesign
- infer legacy compatibility truth from hidden transcript state instead of cited durable surfaces
- touch protected backlog under `archive/`, `.vercel`, `.env*`, `secrets/`, screenshots, captures, or broad untracked root docs and media

## Root Health Baseline

- pass 398 already froze the exact `legacy_compatibility_signal` contract around `legacy_pre_registry` plus truthy-`source_ref` qualification, bounded queue payload only, fixed non-blocking severity, deterministic ordering, and separation from governed-v1 blocker, repair, archive, or owner-repo authority
- pass 399 already admitted `ATLAS root control-plane surfaces` as the owner-facing home for this seam
- pass 400 already proved separate support still honestly holds at `none yet`
- pass 401 already froze the exact first implementation slice around `legacy_compatibility_payload` iteration, bounded signal emission, inherited deterministic queue merge, unchanged top-level `legacy_compatibility` handoff, and the exact proof matrix
- pass 290 already proves the bounded provenance-derived queue path that this slice must preserve without redesigning overflow or queue-budget behavior
- root validation is currently clean at `critical=0 error=0 warning=3 info=0`
- local `HEAD` is in parity with `origin/main`

## Inherited Contract Spine

The future worker must inherit exactly:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 398 exact `legacy_compatibility_signal` contract
- pass 399 root control-plane owner admission
- pass 400 supporting-lane hold at `none yet`
- pass 401 exact first implementation slice and exact proof matrix

No worker may reinterpret those seams as suggestions.
They are contract inputs.

## Exact Worker Objective

The next worker is allowed to pursue one exact implementation objective only:

- implement or narrowly reconcile the already-admitted root-local `legacy_compatibility_signal` first slice inside `ops/cortex/render_status.py` and `tests/test_cortex_render_status_provenance.py` so it iterates only over the already-derived `legacy_compatibility_payload`, emits one fixed `low` compatibility signal only when a payload entry has truthy `source_ref` and `epoch = "legacy_pre_registry"`, preserves admitted `session_id`, `epoch`, `original_session_ref`, and `missing_governed_requirements` detail fields only, preserves inherited deterministic `attention_item_sort_key(...)` queue ordering against the already-admitted broader queue families, preserves omission when `source_ref` is missing or empty or the payload entry does not carry `epoch = "legacy_pre_registry"`, preserves the unchanged top-level `attention_queue` and `legacy_compatibility` handoffs through `render_status_payload(...)`, preserves non-admission of `cutover_at`, `observed_at`, `recorded_at`, and `governed_identity` into queue details, and proves behavior against the frozen pass-401 matrix

The worker is not allowed to pursue:

- broader `attention_queue` redesign
- queue-budget or overflow changes
- archive action, repair action, or governed-v1 blocker widening
- queue, registry, runtime, session, merge, manifest, archive, repair, or owner-repo mutation
- broader legacy payload redesign or doctrine semantics
- any new item family, status value, payload field, or ordering rule outside the frozen seam

## Exact Preserved Payload Surface

The worker must preserve exactly these bounded payload surfaces:

- queue payload:
  - `status`
  - `item_count`
  - `highest_severity`
  - `items`
- `legacy_compatibility_signal` item payload:
  - `kind`
  - `severity`
  - `summary`
  - `source_ref`
  - `details.session_id`
  - `details.epoch`
  - `details.original_session_ref`
  - `details.missing_governed_requirements`
- top-level legacy payload:
  - `legacy_compatibility`

The worker may render these payload surfaces only.
The worker may not widen them into archive metadata, repair metadata, governed-v1 blocker narration, queue-budget metadata, or broader operator semantics.

## Exact Mandatory Proof Cases

The worker must satisfy exactly these proof cases:

1. `legacy_pre_registry` emission
   - emit one `legacy_compatibility_signal` when one legacy payload entry has truthy `source_ref` and `epoch = "legacy_pre_registry"`
   - preserve admitted detail fields only
   - preserve fixed `low` severity

2. non-qualifying omission
   - omit `legacy_compatibility_signal` when the payload entry has missing or empty `source_ref`
   - omit `legacy_compatibility_signal` when the payload entry does not carry `epoch = "legacy_pre_registry"`

3. mixed legacy-compatibility plus higher-severity broader queue families
   - preserve all admitted families in one queue
   - preserve final item ordering by `attention_item_sort_key(...)`
   - preserve queue-level `highest_severity` from the first sorted item
   - preserve the non-blocking `low` severity placement for legacy compatibility

4. top-level render-status handoff
   - preserve the bounded `attention_queue` payload at top-level `render_status_payload(...)`
   - preserve the unchanged top-level `legacy_compatibility` payload
   - do not widen those handoffs into archive, repair, governed-v1 blocker, or doctrine semantics

5. non-admitted legacy fields stay out of queue payload
   - do not project `cutover_at`
   - do not project `observed_at`
   - do not project `recorded_at`
   - do not project `governed_identity`

6. pass-290 overflow noninteraction
   - preserve `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP` behavior for provenance items only
   - do not let `legacy_compatibility_signal` emit, suppress, or reinterpret `provenance_alert_overflow`

## Exact No-Mutation / No-Archive / No-Repair Boundary

The worker must carry this wording forward verbatim:

`No-mutation guard: this packet may admit future implementation or bounded reconciliation of one root-local iteration layer inside attention_queue(...) over the already-derived legacy_compatibility_payload, one legacy_compatibility_signal emission branch using admitted session_id plus source_ref plus epoch plus original_session_ref plus missing_governed_requirements only, one inherited deterministic attention_item_sort_key(...) queue merge layer, and one unchanged top-level render_status_payload(...) handoff for attention_queue plus legacy_compatibility, but it may not mutate queue, registry, runtime, session, merge, manifest, archive, repair, or owner-repo state, change queue-budget or overflow behavior, widen into archive action, repair action, governed-v1 blocker semantics, broader legacy payload redesign, or imply supervisor/operator proof.`

## Exact No Hidden Transcript-State Inference Boundary

The worker must carry this rule forward:

- use only the cited durable surfaces in this receipt chain plus the admitted root-local helper and test files
- do not infer payload meaning, proof scope, blocker state, or next-step authority from uncited transcript memory, hidden operator state, or broad root residue

## Exact Allowed Future Implementation Surfaces

The worker may touch only:

- `ops/cortex/render_status.py`
- `tests/test_cortex_render_status_provenance.py`

## Exact Forbidden Future Implementation Surfaces

The worker must not touch:

- queue or registry mutation surfaces
- session-manifest, runtime-state, merge, archive, repair, or owner-repo mutation surfaces
- `_stack` helper-runtime or command-design surfaces
- Playbook doctrine-export surfaces
- `ops/atlas/*`
- `archive/`, `.vercel`, `.env*`, `secrets/`, screenshot or capture residue, `.playwright-mcp/`, or broad untracked root docs/media backlog
- broader archive-doctrine, repair-doctrine, governed-v1 blocker, contradiction, supervision, dispatch, or execution-home surfaces

## Exact Stop Conditions

The worker must stop and return immediately if the slice requires:

- queue-budget changes or queue-signal overflow changes
- queue, registry, runtime, session, merge, manifest, archive, repair, or owner-repo mutation
- archive action, repair action, or governed-v1 blocker widening
- `_stack` helper-runtime ownership
- owner-repo edits
- protected-surface touch or backlog cleanup
- new payload fields, new status values, reordered item families, or non-deterministic sort behavior
- hidden transcript-state inference to resolve ambiguity

If one of those triggers appears, the work is no longer valid first-slice implementation work.

## Exact Handoff Prompt-Pack Spine

Any future worker prompt-pack must include:

1. the exact implementation objective
2. the inherited pass 290 plus passes 398 through 401 as frozen inputs
3. the exact preserved payload surfaces
4. the exact proof matrix
5. the exact no-mutation guard verbatim
6. the exact no-hidden-transcript-state boundary
7. the exact allowed-touch and forbidden-touch surfaces
8. the exact stop-and-return conditions

Mirror surfaces may restate this spine.
They may not redefine it.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue legacy_compatibility_payload implementation-readiness closeout and worker-routing pass 403`

Why:

- the contract freeze, owner admission, support decision, first implementation slice, and worker handoff are now all explicit
- the next remaining root-only ambiguity is whether any control-plane prerequisite still blocks leaving docs-only mode for one bounded worker packet on the already-admitted helper and proof surfaces

## Marker Decision

- `none`

Why:

- this pass narrows the worker handoff contract only
- no new executed state, broader proof-backed adoption, or blocker clearance landed

## Rule

Freeze the worker handoff contract before authorizing bounded implementation work for a root-local `legacy_compatibility_signal` queue seam that already has its contract, owner, support posture, and first slice admitted.

## Pattern

contract freeze -> owner admission -> support check -> first-implementation admission -> prompt-pack and handoff contract -> implementation-readiness closeout -> bounded implementation

## Failure Mode

`Legacy Compatibility Handoff Drift`

If the worker handoff contract stays implicit, the already-admitted compatibility seam expands through prompt wording into archive doctrine, repair doctrine, governed-v1 blocker semantics, broader legacy payload redesign, overflow, hidden-state, protected-backlog, or broader runtime semantics that the durable chain has not admitted.
