# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Legacy-Compatibility-Payload Contract Freeze Pass 398 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `docs/ops/GOVERNED-ARTIFACT-EPOCHS.md`
  - `docs/ops/LEGACY-RUNTIME-BACKFILL-RUNBOOK.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-UNKNOWN-EXTENSION-SURFACE-NEXT-SLICE-SELECTION-PASS-397-2026-06-17.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@72ea4145`

## Objective

Freeze the exact bounded contract for the not-yet-consumed `legacy_compatibility_payload` seam inside the broader root-owned `attention_queue` surface while preserving the already-rendered top-level `legacy_compatibility` status payload and the current queue behavior on canonical `main`.

This pass does not:

- admit code or test changes
- claim that `legacy_compatibility_payload` is already live inside `attention_queue(...)`
- widen `attention_queue` families beyond the already-frozen broader queue set plus one exact future legacy-compatibility family
- mutate original runtime evidence, backfill descriptors, registry state, session state, manifests, merges, trust surfaces, or owner-repo state
- reinterpret legacy compatibility as repair authority, archive authority, blocker escalation, or deploy authority
- reopen governed-surface contradiction, registry-health, resume, merge, closure, or trust families as part of the same packet
- infer governed identity from hidden transcript state, raw logs, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the runbook and architecture rule that `legacy_pre_registry` history may be incomplete but may not be invisible
- pass 397 selection of `legacy_compatibility_payload` as the next bounded broader queue seam after the live item families were exhausted

## Exact Admitted Item Family

One not-yet-live broader queue family is now frozen precisely:

- `legacy_compatibility_signal`

It qualifies only when all of these are true:

1. `render_status_payload(...)` has already derived `legacy_compatibility_payload` from `legacy_compatibility_surfaces(descriptors)`
2. one entry in that payload has a truthy `source_ref`
3. that same entry carries `epoch = "legacy_pre_registry"`
4. the family is describing explicit historical compatibility visibility only, not governed-v1 failure, repair, archive deletion, or mutation follow-through

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- `legacy_runtime_backfill` descriptors
- `legacy_compatibility_surfaces(descriptors)`
- per-entry `session_id`
- per-entry `source_ref`
- per-entry `original_session_ref`
- per-entry `epoch`
- per-entry `missing_governed_requirements`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`
- root ATLAS-side consumers that read `attention_kinds` or `attention_queue` output without changing this family contract

This family must be derived from the existing `legacy_compatibility_payload` seam rather than by re-reading raw runtime evidence directly inside queue logic.

## Forbidden Source Surfaces

This family is not allowed to originate from:

- raw historical manifests, logs, or receipts bypassing the descriptor-backed backfill payload
- active-session `session_state`, `final_status`, or `registry_digest` alone
- current registry-health failures or governed-surface contradiction payloads
- hidden inference that legacy history should be upgraded into governed-v1 completeness
- repair commands, archive deletion decisions, or live operator intervention state
- `governed_identity` nested identity-resolution details as first-class queue payload fields

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "legacy_compatibility_signal"`
- `severity = "low"`
- `summary = "Historical session '{session_id}' remains in legacy_pre_registry compatibility mode."`
- `source_ref` remains the admitted legacy-compatibility descriptor source reference
- `details` is admitted exactly as:
  - `session_id`
  - `epoch`
  - `original_session_ref`
  - `missing_governed_requirements`

No additional top-level queue fields, no new status values, and no extra detail keys are admitted from this contract freeze alone.

Important non-admitted payload fields include:

- `cutover_at`
- `observed_at`
- `recorded_at`
- `governed_identity`

Those fields may remain source-side context in the top-level `legacy_compatibility` payload, but they are not admitted queue-item payload fields for this family.

## Exact Severity And Ordering Rule

This family does not define its own routing priority class beyond the already-frozen deterministic sort discipline.

The exact rule remains:

- emit `low` severity only
- do not create a `medium`, `high`, or `critical` branch for this family from this contract freeze alone
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This keeps the compatibility signal explicit without misclassifying historical exception visibility as a current blocking defect.

## Exact Compatibility Split

The legacy compatibility family coexists with neighboring queue doctrine exactly as follows:

- only `legacy_compatibility_signal` emits explicit `legacy_pre_registry` visibility from the legacy payload seam
- governed-v1 failure families remain separate and unchanged
- `legacy_pre_registry` history may remain incomplete without being upgraded into governed-v1 blocker semantics
- if the payload entry is missing `source_ref` or does not carry `epoch = "legacy_pre_registry"`, this family stays silent

This contract freeze names that split only.
It does not reopen governed-v1 completeness doctrine or archive policy.

## Exact Non-Blocking Guard

This family is an attention-layer compatibility signal, not a blocker family.

The exact guard remains:

- the family must stay explicit in the attention layer
- the family must stay non-blocking for impossible modern governed-v1 fields
- the family does not satisfy or suppress current blocking families when those separate families also qualify
- the family does not require registry repair, session repair, receipt repair, archive action, or owner-repo follow-through by itself

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `legacy_compatibility_signal` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret historical compatibility as queue-budget metadata

This family therefore joins the broader queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned descriptor-backed backfill records already summarized inside ATLAS-root status helpers
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers and root-side attention readers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Historical legacy compatibility visibility is not:

- governed-v1 blocker authority
- registry repair authority
- session repair authority
- receipt repair authority
- archive or deletion authority
- owner-repo mutation authority

This family only surfaces one bounded explicit compatibility signal so legacy history is not invisible.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already renders `legacy_compatibility` at the top level, the only result of this pass is to freeze the future queue-family boundary around what counts, what fields are admitted, what severity is admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue legacy_compatibility_payload owner-surface admission pass 399`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When one status payload is already descriptor-backed and explicitly required to stay visible in the attention layer, freeze one exact non-blocking compatibility signal before reopening ownership, support, or implementation questions.

## Pattern

post-family next-slice selection -> exact future-family contract freeze -> owner-surface admission

## Failure Mode

`Legacy Compatibility Signal Drift`

If the lane leaves the `legacy_compatibility_payload` seam informal, later workers can reopen whether legacy history should be invisible, blocking, or mutation-authorizing before the attention-layer compatibility signal is frozen.
