# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Session-Needs-Resume Contract Freeze Pass 356 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded contract freeze`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-POST-BROADER-ATTENTION-QUEUE-CLOSURE-RECEIPT-ISSUE-NEXT-SLICE-SELECTION-PASS-355-2026-06-16.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-PROVENANCE-ALERT-QUEUE-SIGNAL-BUDGET-INTEGRATION-PROOF-PASS-290-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `tests/test_atlas_run_initiative_loop.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@422c51ec`

## Objective

Freeze the exact bounded contract for the already-live `session_needs_resume` item family inside the broader root-owned `attention_queue` surface while preserving the queue behavior already landed on canonical `main`.

This pass does not:

- admit code or test changes
- widen `attention_queue` families beyond the already-frozen broader queue set
- mutate queue, registry, runtime, session, manifest, execution-receipt, trust, or owner-repo state
- reinterpret one active-session resume follow-up sentinel as resume execution, merge execution, registry repair, or owner-repo authority
- reopen broader registry-drift, failure, contradiction, or inactive payload doctrine
- infer session follow-up truth from hidden transcript state, operator memory, or uncited residue

## Inherited Chain

The following remain frozen and are inherited without change:

- pass 290 provenance-derived queue signal cap and overflow sentinel behavior
- pass 300 broader `attention_queue` contract and admitted item-family set
- the reconciled `closure_receipt_issue` slice proving the bounded closure-result follow-on already lands cleanly on canonical `main`
- pass 355 selection of `session_needs_resume` as the next bounded live active-session follow-on

## Exact Admitted Item Family

One already-live broader queue family is now frozen precisely:

- `session_needs_resume`

It qualifies only when all of these are true:

1. `attention_queue(...)` is evaluating one admitted `active_session` payload
2. that `active_session` payload is the currently selected root-local active session summary already surfaced into `render_status_payload(...)`
3. `session_state = str(active_session.get("session_state", "")).strip()`
4. `final_status = str(active_session.get("final_status", "")).strip()`
5. either `session_state == "resume_ready"` or `final_status == "resume_ready"`
6. the family is describing explicit resume-or-merge follow-up visibility only, not performing resume execution, merge execution, registry repair, or owner-repo mutation

If those conditions do not hold, this family is not emitted.

## Exact Admitted Source Surfaces

Allowed producing surfaces are root-local only:

- the admitted `active_session` payload already supplied to `attention_queue(...)`
- `active_session.session_state`
- `active_session.final_status`
- `active_session.source_ref`
- `active_session.session_id`
- `active_session.task_id`

Allowed consuming surfaces already visible from the same root-owned contract are:

- `ops/cortex/render_status.py` inside `render_status_payload(...)`
- `ops/cortex/render_status.py` inside `attention_queue(...)`
- root ATLAS-side consumers that read `attention_kinds` or `attention_queue` output without changing this family contract

## Forbidden Source Surfaces

This family is not allowed to originate from:

- closure-receipt descriptors or unresolved close-receipt refs
- registry digest comparison alone
- merge-request, trust-posture, initiative, or conversation request payloads
- owner-repo proof, deploy, or publication surfaces
- hidden transcript-state inference about whether a resume should happen
- resume execution commands, merge execution commands, session mutation, or live operator intervention state

## Exact Admitted Payload Fields

The emitted `attention_queue` item stays inside the already-frozen top-level item shape:

- `kind`
- `severity`
- `summary`
- `source_ref`
- `details`

For this family specifically, the admitted values are:

- `kind = "session_needs_resume"`
- `severity = "medium"`
- `summary = "The active session is waiting for an explicit resume or merge follow-up."`
- `source_ref` remains the admitted active-session source reference
- `details` is admitted exactly as:
  - `session_id`
  - `task_id`

No other `details` fields are admitted for this family from this contract freeze alone.
No additional top-level queue fields are admitted.

Important non-admitted active-session fields include:

- `registry_digest`
- `worker_id`
- `assignment_id`
- `final_receipt_id`
- `merge_request_ref`
- `resume_reason`
- `failure_reason`

Those fields may remain source-side active-session context, but they are not admitted queue-item payload fields for this family.

## Exact Severity And Ordering Rule

This family does not define its own queue-wide routing model beyond the already-frozen deterministic sort discipline.

The exact rule remains:

- emit `medium` severity only
- do not create a `high` or `critical` branch for this family from this contract freeze alone
- merge the item into the same `attention_queue` item list as the other admitted families
- preserve final deterministic ordering via `attention_item_sort_key(...)`
- preserve queue-level `highest_severity` as the first sorted item severity

This means `session_needs_resume` coexists under the same severity-first then `kind` then `source_ref` then `summary` ordering already frozen for the broader queue.

## Exact Qualification Split

The session-needs-resume family coexists with neighboring active-session families exactly as follows:

- only `resume_ready` emits `session_needs_resume`
- `resume_failed` remains a separate higher-severity family
- `failed` session outcomes remain a separate higher-severity family
- registry-digest mismatch remains a separate `registry_drift` family
- if neither admitted state field equals `resume_ready`, this family stays silent

This contract freeze names that split only.
It does not freeze the separate failure or contradiction families themselves.

## Exact Registry-Interaction Guard

The `session_needs_resume` item does not require healthy registry state to qualify once the admitted active-session state already exists.

The exact coexistence guard remains:

- `session_needs_resume` may emit even when registry health is unavailable
- `session_needs_resume` may coexist with `registry_drift` when registry health is available and the active-session digest differs from the current registry digest
- no registry-surface contradiction or validation follow-on is required for this family itself
- registry-health-dependent contradiction or drift follow-ons remain a separate family concern and are not admitted queue payload fields for this family

This contract freeze names that split only.
It does not freeze the separate contradiction families themselves.

## Overflow And Budget Interaction

The pass-290 overflow boundary remains unchanged and still applies only to the provenance-derived queue subset.

Exact interaction:

- `session_needs_resume` does not alter `PROVENANCE_ALERT_QUEUE_SIGNAL_CAP`
- it does not emit or suppress `provenance_alert_overflow`
- it does not widen the top-level queue payload
- it does not reinterpret resume-follow-up visibility as queue-budget metadata

This family therefore joins the derived queue without reopening budget or overflow redesign.

## Root-Locality Decision

This item family remains root-local only.

Why:

- its producing truth comes from root-owned active-session status already summarized inside ATLAS-root control-plane code
- its visible downstream consumers also remain inside ATLAS-root control-plane helpers and root-side attention readers
- no `_stack`, Playbook, owner-repo, deploy, or external runtime authority is required to define the contract boundary

## Separation Decision

Session resume follow-up visibility is not:

- resume execution authority
- merge execution authority
- registry repair authority
- session mutation authority
- failure adjudication authority
- owner-repo mutation authority

This family only surfaces one bounded active-session follow-up sentinel inside the broader operator-review queue.

## Implementation Decision

This pass does not admit implementation yet.

Even though current root-local code already emits this family, the only result of this pass is to freeze the contract boundary around what counts, what fields are admitted, what severity is admitted, what surfaces may produce or consume it, and what must remain forbidden.

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue session_needs_resume owner-surface admission pass 357`

Why:

- the contract boundary is now explicit
- the next honest question is whether the producing and consuming surfaces stay entirely inside ATLAS-root control-plane ownership or reopen any shared support or owner-repo boundary

## Marker Decision

- `none`

Why:

- this pass is docs-only contract clarification
- no new implementation, proof-backed adoption, blocker clearance, or broadened restart ratchet landed

## Rule

When a broader `attention_queue` family is already live and root-local, freeze the exact active-session qualifier, admitted detail boundary, fixed severity, and separation-from-resume-execution rule before reopening ownership, support, or implementation questions.
