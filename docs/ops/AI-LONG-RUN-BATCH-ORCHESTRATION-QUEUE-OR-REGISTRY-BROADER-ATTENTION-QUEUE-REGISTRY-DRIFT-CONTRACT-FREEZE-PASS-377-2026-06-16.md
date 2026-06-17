# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Registry-Drift Contract Freeze Pass 377 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-SESSION-FAILED-NEXT-SLICE-SELECTION-PASS-376-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@0368e595`

## Objective

Freeze the exact bounded contract for the already-live `registry_drift` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate registry, runtime, session, manifest, merge, trust, or owner-repo state
- reinterpret registry digest mismatch as repair authority, retry authority, resume authority, merge authority, or supervisor proof
- reopen governed-surface contradiction, inactive payload, or owner-repo doctrine
- infer registry or session truth from hidden transcript state, operator memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `session_failed` slice proving one compact root-local active-session follow-on can land cleanly
- pass 376 selection of `registry_drift` as the next bounded live active-session digest-mismatch follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `registry_drift`

It qualifies only when all of these are true:

1. `attention_queue(...)` is evaluating one admitted `active_session` payload
2. `registry_state.ok` is truthy
3. `registry_digest = active_session.get("registry_digest")` is truthy
4. `current_digest = registry_state.get("registry_digest")` is truthy
5. `registry_digest != current_digest`
6. the family is describing active-session registry digest mismatch visibility only, not performing registry repair, retry dispatch, resume execution, merge execution, or owner-repo mutation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- the admitted `active_session` payload already supplied to `attention_queue(...)`
- `active_session.registry_digest`
- `active_session.source_ref`
- `active_session.session_id`
- the admitted `registry_state.ok` payload
- `registry_state.registry_digest`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`
- root ATLAS-side consumers that read `attention_kinds` or `attention_queue` output without changing this family contract

## Forbidden Source Surfaces

This family is not allowed to originate from:

- falsey or unavailable registry-health payloads alone
- active-session `session_state` or `final_status` alone
- governed-surface tool or extension validation branches alone
- closure-receipt, merge-request, trust-surface, or owner-repo payloads
- hidden transcript-state inference about whether mismatch should trigger repair, retry, resume, merge, or deployment behavior
- registry-repair commands, mutation receipts, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "registry_drift"`
- `severity = "high"`
- `summary = "The active session was created against a different registry digest."`
- `source_ref` remains the admitted active-session source reference
- `details` is admitted exactly as:
  - `session_id`
  - `session_registry_digest`
  - `current_registry_digest`

No additional top-level queue fields, no new status values, and no extra detail keys are admitted from this contract freeze alone.

Important non-admitted active-session and registry fields include:

- `task_id`
- `session_state`
- `final_status`
- `resume_failure_reason`
- `worker_id`
- `assignment_id`
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

This means `registry_drift` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Exact Qualification Split

The digest-mismatch family coexists with neighboring active-session and registry families exactly as follows:

- only `registry_drift` emits active-session digest mismatch visibility
- `session_needs_resume` remains a separate `resume_ready` family
- `resume_failed` remains a separate resume-path failure family
- `session_failed` remains a separate terminal-failure family
- `registry_error` remains the separate unhealthy-registry sentinel
- if either digest is missing or registry health is unavailable, this family stays silent

This contract freeze names that split only.
It does not freeze the separate resume, failure, or contradiction families themselves.

## Exact Registry-Interaction Guard

This family requires healthy registry state and two truthy digest values to qualify.

The exact coexistence guard remains:

- `registry_drift` does not emit when `registry_state.ok` is falsey
- `registry_error` may emit separately when registry health is unavailable
- `registry_drift` may coexist with `session_needs_resume`, `resume_failed`, or `session_failed` when those admitted active-session state families also qualify
- `registry_drift` may coexist with `unknown_tool_surface` or `unknown_extension_surface` when registry health is available and governed-surface validation separately fails
- no contradiction or validation follow-on is required for this family itself

This contract freeze names that split only.
It does not freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `registry_drift` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret digest mismatch as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned active-session and registry-state summaries already surfaced inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers and root-side attention readers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Registry digest mismatch visibility is not:

- registry repair authority
- retry authority
- resume execution authority
- merge execution authority
- session mutation authority
- governed-surface contradiction authority
- owner-repo mutation authority

This family only surfaces one bounded active-session digest mismatch sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what severity is admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue registry_drift owner-surface admission pass 378`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact digest-mismatch qualifier, admitted detail boundary, fixed `high` severity, and separation-from-repair-or-retry-or-resume-or-merge rule before reopening ownership, support, or implementation questions.

## Pattern

post-family next-slice selection -> exact family contract freeze -> owner-surface admission

## Failure Mode

`Registry Drift Contract Drift`

If the lane leaves the already-live `registry_drift` seam informal, later workers can reopen qualification, payload shape, severity, or contradiction coexistence questions that should have been frozen before governed-surface contradiction families advance.
