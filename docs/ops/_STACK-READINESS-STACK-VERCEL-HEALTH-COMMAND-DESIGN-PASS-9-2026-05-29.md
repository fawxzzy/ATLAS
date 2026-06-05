# _Stack Readiness Stack Vercel-Health Command-Design Pass 9 - 2026-05-29

- Date: `2026-05-29`
- Lane: `_stack Readiness stack vercel-health command-design pass 9`
- Mode: `docs-only root-bounded command design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/_STACK-READINESS-MARKER-PRESSURE-REOPEN-AND-REENTRY-PASS-8-2026-05-29.md`
  - `docs/ops/STACK-READINESS-HEALTH-SIGNAL-AND-LOCAL-TRUTH-GOVERNANCE-FAMILY-SHAPING-PASS-6-2026-05-29.md`
  - `docs/ops/UNIFIED-WORKFLOW-CONVERGENCE-HANDOFF-MAP-PASS-1-2026-05-29.md`
  - `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-FITNESS-QA-AUTH-SECRET-PROVISIONING-DECISION-PASS-2-2026-05-29.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`

## Objective

Freeze one compact authoritative command-design spine for a future `_stack vercel-health` operator command.

This pass does not:

- implement a command
- run Vercel operations
- mutate deploy state, env state, or project state
- reopen owner-side Fitness work
- reopen Discord implementation
- claim runtime correctness or deploy success

## Inherited Reopen Result

Pass 8 already froze:

- `_stack Readiness` is honestly reopened
- explicit marker-pressure is a valid reopen trigger here
- the prior `_stack` shaping-and-refresh subladder remains closed
- the exact next docs-only packet was `stack vercel-health command-design`

This pass consumes that next packet without replaying the reopen decision.

## Exact Command Purpose

`stack vercel-health` exists to summarize governed stack-level Vercel health posture for operator routing.

Its purpose is limited to:

- canonical project visibility
- provenance clarity between repos and Vercel surfaces
- stale or helper-surface pressure
- deploy-evidence posture at the governed boundary
- approval-gated or blocked health unknowns that change the next routing step

It does not exist to deploy, repair, verify product runtime behavior, or override owner proof.

## Exact In-Scope Inspection Surfaces

The future command may inspect only these classes of surfaces:

1. `ATLAS restart and receipt surfaces`
   - restart guide, system map, marker surfaces, and durable receipts that already classify Vercel ownership, deletion history, helper-surface pressure, and next-package posture

2. `repo-local linkage and config metadata`
   - repo-visible Vercel linkage metadata, config pointers, canonical project naming surfaces, and other non-secret local metadata needed to map repo ownership to Vercel surfaces

3. `read-only Vercel inventory metadata`
   - canonical project presence, helper or stale-surface inventory, and non-mutating project classification metadata

4. `governed deploy-boundary evidence`
   - `_stack` deploy-authority receipts, owner release-proof references, and root-side consequence receipts that show whether a health summary can describe recent governed evidence without simulating it

The command may not inspect or require:

- secret values
- product data payloads
- Discord runtime state
- Supabase mutation state
- private owner truth that is not already admitted as a health-facing evidence surface

## Exact Allowed Health Dimensions

The command may report only these health dimensions:

1. `canonical-project presence`
   - whether the expected canonical Vercel project surfaces are present for the requested scope

2. `provenance clarity`
   - whether repo ownership, helper-surface history, and current Vercel project mapping are clear versus ambiguous

3. `stale/helper-surface pressure`
   - whether there is unresolved duplicate, stale, or helper-surface churn that still matters to operator routing

4. `governed deploy-evidence posture`
   - whether recent `_stack` deploy-boundary evidence exists and is classifiable for health summary purposes

5. `approval-gated unknowns`
   - whether remote verification, protected inspection, or blocked owner evidence leaves part of the requested health picture unresolved

The command may not report:

- app-runtime correctness
- user-facing feature health
- publication truth
- shipped-proof truth by itself
- any claim stronger than the evidence surfaces already support

## Exact Inputs

The future command accepts only bounded awareness inputs:

- `--scope <stack|repo|surface-class>`
- `--repo <repo-name>` when scope is repo-bounded
- `--include-stale` to include helper or stale-surface pressure in the report
- `--format <text|json>`
- `--evidence-window <label-or-range>` to constrain which admitted evidence receipts are summarized

The command may not accept:

- mutation flags
- repair flags
- deploy flags
- delete flags
- secret or auth-value inputs
- target selectors that imply action rather than inspection

## Exact Outputs And States

The future command emits one bounded health report containing:

- requested scope
- inspected surface classes
- admitted evidence references
- one health class
- exact reasons for that class
- one routing recommendation only

Non-health exits may include:

- `invalid-input`
- `surface-unavailable`

Those are command failures, not health claims.

## Exact Healthy / Degraded / Blocked Classes

### `healthy`

Use only when:

- canonical project mapping is clear for the requested scope
- no unresolved stale/helper ambiguity materially affects the requested routing question
- governed deploy-boundary evidence is present and recent enough for summary
- no approval-gated unknown is needed to answer the requested health question

### `degraded`

Use when:

- the command can inspect enough admitted surfaces to summarize posture
- but provenance drift, stale/helper pressure, or aging evidence still weakens operator confidence
- and the correct next move is still a bounded follow-on packet rather than a hard block

### `blocked`

Use when:

- required admitted evidence is missing
- the requested health question would force simulation or overclaim
- approval-gated or owner-side truth is still needed before the question can be answered honestly
- or the requested scope crosses from control-plane summary into execution-side inspection

## Exact Routing After Each Output Class

### After `healthy`

ATLAS root may:

- package the summary into a receipt or restart mirror
- keep the result at awareness level
- route to the next bounded docs-only implementation-admission packet

ATLAS root may not:

- treat the result as deploy authority
- treat the result as runtime verification

### After `degraded`

ATLAS root must:

- package degraded posture only
- name the exact ambiguity still open
- route to one bounded docs-only clarification or inventory packet

### After `blocked`

ATLAS root must:

- package blocked posture only
- identify the missing evidence, gate, or owner-side surface
- route either to owner-side evidence refresh, approval-gated inspection, or a narrower root-only evidence packet

## Exact Evidence Rule

`stack vercel-health` may summarize only admitted evidence already present in:

- ATLAS receipts and restart surfaces
- repo-local non-secret linkage metadata
- read-only Vercel inventory metadata
- governed deploy-boundary evidence

It may not:

- simulate deploy success
- infer runtime correctness from project existence
- restate publication or shipped truth as if it were Vercel health
- replace owner proof with a root summary

## Exact Out-Of-Scope Boundary

Still out of scope:

- command implementation
- live command execution policy
- deploy or rollback execution
- project deletion
- env mutation
- secret access beyond normal read-only command auth
- runtime debugging
- preview or production verification by itself

## Exact Next Package

`_stack Readiness stack vercel-health evidence-admission and freshness pass 10`

Why:

- the command semantics are now frozen
- the next open ambiguity is which exact receipts, inventories, and read-only metadata are admitted evidence for the command
- and how stale evidence downgrades health class without letting the command simulate missing truth

## Recommendation Type

`durable with bounded inference`

Durable because:

- the command seam was already explicitly named in restart surfaces
- the source receipts already freeze the owner boundary, health-signal boundary, and deploy-evidence boundary that the command must respect

Bounded inference because:

- the exact pass-10 label is newly compressed here from the remaining evidence-admission ambiguity rather than inherited from a prior landed receipt

## Ratchet Decision

Ratchet:

- `_stack Readiness: 61% -> 62%`

Why:

- this pass materially reduces one real operator-surface ambiguity class
- `_stack` now has one exact command-purpose, inspection-boundary, input/output, health-class, and routing spine for the first Vercel-facing command seam
- the move stays to the smallest honest increment because no implementation, live execution, or broader automation adoption happened

## Validation Note

The inherited root-health baseline for this lane was `critical=0 error=0 warning=489 info=0`.

Live validation at the end of this pass was:

- `critical=0 error=0 warning=493 info=0`

This is an unexpected warning-count increase relative to the older baseline, but `critical` and `error` remain green.

## Rule

Freeze awareness semantics, evidence boundaries, and routing before any `_stack` health command is admitted for implementation.

## Pattern

reopen by valid marker-pressure -> freeze command purpose -> freeze inspection surfaces -> freeze health classes and routing -> only then freeze evidence admission and freshness

## Failure Mode

`stack vercel-health` becomes a disguised deploy or runtime command, so root-side health summaries start sounding stronger than the admitted evidence and owner boundaries allow.
