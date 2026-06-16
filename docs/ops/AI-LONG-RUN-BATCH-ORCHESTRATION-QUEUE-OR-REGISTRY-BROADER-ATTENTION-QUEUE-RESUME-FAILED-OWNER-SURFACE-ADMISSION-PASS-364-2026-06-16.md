# AI Long-Run Batch Orchestration Queue-Or-Registry Broader Attention-Queue Resume-Failed Owner-Surface Admission Pass 364 - 2026-06-16

- Date: `2026-06-16`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded owner-surface admission`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION-QUEUE-RESUME-FAILED-CONTRACT-FREEZE-PASS-363-2026-06-16.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@3cea7d2d`

## Objective

Freeze the exact owner-facing home for the bounded `resume_failed` queue seam after the contract itself is explicit.

This pass decides ownership only.

It does not:

- widen the queue contract
- admit implementation
- admit support-lane or owner-repo execution
- mutate queue, registry, runtime, session, manifest, execution-receipt, or owner-repo state

## Admitted Owner-Facing Home

The exact owner-facing home for this queue seam remains inside ATLAS root only.

Producing and consuming truth stays inside:

- active-session state already admitted into `render_status_payload(...)`
- `attention_queue(...)`
- `render_status_payload(...)`
- root ATLAS-side queue consumers that observe `attention_queue` or `attention_kinds` output without redefining this family contract
- root restart mirrors:
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`

## Why Ownership Stays Root-Local

- the family is still one bounded projection of root-owned active-session summary truth
- the admitted queue payload is still control-plane review truth rather than retry authority, resume execution, merge execution, repair, or owner-repo product truth
- the producing helper and consuming queue code already live together in `ops/cortex/render_status.py`
- restart and routing truth for this family remains rooted in ATLAS-side receipt and restart surfaces

## Explicit Non-Owners

The following remain outside the admitted owner-facing home:

- `_stack`
- Playbook
- owner repos
- retry doctrine
- resume-execution doctrine
- merge-execution doctrine
- broader session-failure, registry-drift, and contradiction-family ownership

They may later consume consequences from this family, but they do not own its contract or current control-plane projection.

## Boundary Clarification

Admitting ATLAS root ownership means only:

- the family contract is defined here
- the family implementation seam is owned here
- the family restart narration is owned here

It does not mean:

- root may retry failed resume flows
- root may execute session resume flows
- root may execute merge follow-up flows
- root may repair registry state
- root may claim owner-repo authority
- root may widen failure or contradiction semantics from this pass alone

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue resume_failed supporting-lane admission pass 365`

Why:

- the contract and owner-facing home are now explicit
- the next honest question is whether this family reopens any shared support dependency or still honestly holds at `none yet`

## Marker Decision

- `none`

Why:

- this pass clarifies owner placement only
- no new implementation, proof, or blocker conversion landed

## Rule

If a resume-path failure queue family is still produced and consumed entirely inside ATLAS-root status helpers and restart surfaces, keep ownership root-local until a real shared helper or owner-repo dependency actually appears.
