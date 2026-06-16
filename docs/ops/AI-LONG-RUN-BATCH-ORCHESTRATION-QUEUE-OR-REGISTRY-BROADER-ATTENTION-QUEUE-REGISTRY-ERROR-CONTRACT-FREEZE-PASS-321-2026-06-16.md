# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Registry-Error Contract Freeze Pass 321 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-QUARANTINED-TRUST-SURFACE-NEXT-SLICE-SELECTION-PASS-320-2026-06-16.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@4b0fe921`

## Objective

Freeze the exact bounded contract for the already-live `registry_error` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate registry, runtime, session, manifest, merge, trust-promotion, archive, or owner-repo state
- reinterpret registry failure as repair authority, deploy authority, or supervisor proof
- reopen active-session, blocked-worker, merge-request, closure-receipt, or governed-surface contradiction families
- infer registry truth from hidden state, owner memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `quarantined_trust_surface` slice proving one compact root-local follow-on family can land cleanly
- pass 320 selection of `registry_error` as the next bounded live sentinel follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `registry_error`

It qualifies only when all of these are true:

1. `attention_queue(...)` receives a `registry_state` payload whose `ok` field is falsey
2. the item is emitted directly from the root-local `attention_queue(...)` helper as a read-model registry failure sentinel
3. the family is describing registry load failure only, not performing registry repair, mutation, or remediation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- `load_registry_state()`
- the derived `registry_state.ok` result
- the derived `registry_state.error` value when present
- the fixed queue-local `source_ref` constant `docs/registry`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`

## Forbidden Source Surfaces

This family is not allowed to originate from:

- active-session manifests or governed-session state
- blocked-worker, merge-request, closure-receipt, or trust-surface payloads
- owner-repo evidence or deploy surfaces
- inferred registry health that is not present in the root-local `registry_state` payload
- repair commands, mutation receipts, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "registry_error"`
- `severity = "critical"`
- `summary = "The governed tool registry could not be loaded."`
- `source_ref = "docs/registry"`
- `details` may contain only:
  - `error`

No additional top-level queue fields, no new status values, and no extra detail keys are admitted from this contract freeze alone.

## Exact Severity And Ordering Rule

This family does not define its own routing priority class beyond the frozen queue-wide sort discipline.

The exact rule remains:

- emit the item at fixed severity `critical`
- merge it into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `registry_error` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Coexistence Decision

The family coexists with current admitted queue behavior exactly as follows:

- `initiative_open_attention` remains admitted and unchanged
- provenance-derived queue items remain admitted and unchanged
- `conversation_action_request` remains admitted and unchanged
- `quarantined_trust_surface` remains admitted and unchanged
- active-session, blocked-worker, merge-request, closure, and registry-surface contradiction families remain separate broader queue seams

No special family precedence is admitted here beyond the inherited deterministic sort.

## Exact Non-Coexistence Guard

When `registry_state.ok` is falsey:

- `validate_surface_ref(...)` fails closed to no `unknown_tool_surface` or `unknown_extension_surface` items
- `registry_drift` does not emit because it remains gated behind truthy registry health

This contract freeze names that fail-closed split only.
It does not yet freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `registry_error` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret registry failure as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from the root-owned `load_registry_state()` helper already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue registry_error owner-surface admission pass 322`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact sentinel trigger and payload before reopening ownership, support, or implementation questions.

## Pattern

next-slice selection -> exact family contract freeze -> owner-surface admission -> support check -> first-implementation admission

## Failure Mode

`Registry Error Sentinel Drift`

If `registry_error` is allowed to expand beyond one bounded root-local load-failure sentinel, later work can smuggle registry repair semantics, session contradiction handling, or operator-routing doctrine into the queue without a separately admitted packet.
