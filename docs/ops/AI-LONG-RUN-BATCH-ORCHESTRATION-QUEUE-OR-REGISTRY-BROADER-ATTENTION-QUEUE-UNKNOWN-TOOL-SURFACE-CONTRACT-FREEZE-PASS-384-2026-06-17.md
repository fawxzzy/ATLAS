# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Unknown-Tool-Surface Contract Freeze Pass 384 - 2026-06-17

- Date: `2026-06-17`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-REGISTRY-DRIFT-NEXT-SLICE-SELECTION-PASS-383-2026-06-17.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@1a189b74`

## Objective

Freeze the exact bounded contract for the already-live `unknown_tool_surface` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate registry, runtime, session, manifest, merge, trust, or owner-repo state
- reinterpret governed-surface tool-id contradiction as repair authority, registry mutation authority, retry authority, resume authority, merge authority, or supervisor proof
- freeze the sibling `unknown_extension_surface` family as part of the same packet
- reopen inactive legacy payload, owner-repo doctrine, or hidden transcript inference

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `registry_drift` slice proving one compact root-local active-session digest-mismatch follow-on landed cleanly
- pass 383 selection of `unknown_tool_surface` as the next bounded live governed-surface contradiction follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `unknown_tool_surface`

It qualifies only when all of these are true:

1. `attention_queue(...)` is evaluating one admitted governed-surface entry from `active_session.governed_surfaces`
2. `registry_state.ok` is truthy
3. the governed-surface `scope` key is present as the per-entry source label
4. `tool_id` is a non-empty string after trim
5. the trimmed `tool_id` is not present in `registry_state.tool_ids`
6. the family is describing governed-surface tool-id contradiction visibility only, not performing registry repair, registry mutation, retry dispatch, resume execution, merge execution, or owner-repo mutation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- the admitted `active_session` payload already supplied to `attention_queue(...)`
- `active_session.governed_surfaces`
- the governed-surface `scope` key used during iteration
- per-scope `tool_id`
- per-scope `extension_id` only as carried context
- the admitted `registry_state.ok` payload
- `registry_state.tool_ids`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside the governed-surface contradiction helper
- `ops/cortex/render_status.py` inside `attention_queue(...)`
- root ATLAS-side consumers that read `attention_kinds` or `attention_queue` output without changing this family contract

## Forbidden Source Surfaces

This family is not allowed to originate from:

- falsey or unavailable registry-health payloads alone
- active-session `session_state`, `final_status`, or `registry_digest` alone
- extension-id contradiction alone without the unknown-tool branch qualifying
- blocked-worker, merge-request, closure-receipt, trust-surface, or owner-repo payloads
- hidden transcript-state inference about whether contradiction should trigger repair, retry, resume, merge, or deployment behavior
- registry-repair commands, mutation receipts, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "unknown_tool_surface"`
- `severity = "high"`
- `summary = "{scope} references unknown tool_id '{tool_id}'."`
- `source_ref` remains the admitted active-session source reference
- `details` is admitted exactly as:
  - `scope`
  - `tool_id`
  - `extension_id`

For this family, `details.extension_id` may be either the trimmed extension id string or `null` when no extension id is present.

No additional top-level queue fields, no new status values, and no extra detail keys are admitted from this contract freeze alone.

Important non-admitted governed-surface and registry fields include:

- `session_id`
- `task_id`
- `session_state`
- `final_status`
- `registry_digest`
- `tool_ids`
- `extension_ids`

Those fields may remain source-side context, but they are not admitted queue-item payload fields for this family.

## Exact Severity And Ordering Rule

This family does not define its own routing priority class beyond the already-frozen deterministic sort discipline.

The exact rule remains:

- emit `high` severity only
- do not create a `medium` or `critical` branch for this family from this contract freeze alone
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `unknown_tool_surface` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Exact Qualification Split

The governed-surface tool contradiction family coexists with neighboring registry and contradiction families exactly as follows:

- only `unknown_tool_surface` emits tool-id contradiction visibility
- `unknown_extension_surface` remains the separate sibling extension-id contradiction family
- `registry_error` remains the separate unhealthy-registry sentinel
- `registry_drift` remains the separate active-session digest-mismatch sentinel
- if `tool_id` is missing, empty after trim, or already present in `registry_state.tool_ids`, this family stays silent

This contract freeze names that split only.
It does not freeze the sibling extension contradiction family itself.

## Exact Registry-Interaction Guard

This family requires healthy registry state and one unknown trimmed `tool_id` value to qualify.

The exact coexistence guard remains:

- `unknown_tool_surface` does not emit when `registry_state.ok` is falsey
- `registry_error` may emit separately when registry health is unavailable
- `unknown_tool_surface` may coexist with `unknown_extension_surface` when the same governed surface carries both an unknown tool id and an unknown extension id
- `unknown_tool_surface` may coexist with `registry_drift`, `session_needs_resume`, `resume_failed`, or `session_failed` when those admitted active-session families also qualify
- no governed-surface repair, registry mutation, or contradiction follow-on is required for this family itself

This contract freeze names that split only.
It does not freeze the sibling extension contradiction family itself.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `unknown_tool_surface` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret governed-surface contradiction as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned active-session governed-surface summaries plus root-loaded registry tool ids already surfaced inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers and root-side attention readers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Governed-surface tool-id contradiction visibility is not:

- registry repair authority
- registry mutation authority
- retry authority
- resume execution authority
- merge execution authority
- session mutation authority
- extension contradiction authority
- owner-repo mutation authority

This family only surfaces one bounded governed-surface unknown-tool sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what severity is admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue unknown_tool_surface owner-surface admission pass 385`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact governed-surface contradiction qualifier, admitted detail boundary, fixed `high` severity, and separation-from-repair-or-registry-mutation-or-retry-or-resume-or-merge rule before reopening ownership, support, or implementation questions.

## Pattern

post-family next-slice selection -> exact family contract freeze -> owner-surface admission

## Failure Mode

`Unknown Tool Surface Contract Drift`

If the lane leaves the already-live `unknown_tool_surface` seam informal, later workers can reopen qualification, payload shape, severity, or sibling-contradiction coexistence questions that should have been frozen before ownership or implementation routing advances.
