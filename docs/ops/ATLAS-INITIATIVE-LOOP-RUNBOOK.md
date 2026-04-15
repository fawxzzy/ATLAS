# ATLAS Initiative Loop Runbook

`ops/atlas/run_initiative_loop.py` is the root-owned initiative proposal engine.

## Purpose

The initiative loop sits above sessions and below approval.

Its job is to:

- read current attention, plans, decisions, hypotheses, existing initiatives, and recent governed sessions
- update one durable initiative instead of spawning duplicate portfolio objects
- emit proposed sessions as non-executing artifacts only
- keep proposal provenance explicit and queryable

It does not:

- call Lifeline
- auto-dispatch `_stack`
- request approval
- perform execution

## Operating Loop

The current root loop is:

1. awareness
2. attention
3. initiative
4. proposed session
5. approval
6. execution
7. receipt
8. memory refinement

Proposal is not execution. Sessions remain the only execution gateway.

## Artifact Lanes

- initiatives: `docs/memory/initiatives/*.json`
- proposed sessions: `runtime/atlas/proposed-sessions/<session_id>/session.manifest.json`

Proposed sessions reuse `atlas.session.v1` with:

- `session_role: proposed_session`
- `session_state: proposed`
- `scenario: proposed_session`
- a required `proposal` provenance block

## Proposal Provenance

Every proposed session must carry:

- `proposal.initiative_ref`
- `proposal.triggering_attention_refs`
- `proposal.supporting_evidence_refs`
- `proposal.related_plan_refs`
- `proposal.related_decision_refs`
- `proposal.related_hypothesis_refs`
- `proposal.related_prior_session_refs`

Malformed provenance is a blocking validation failure.

Durability rule:

- `proposal.triggering_attention_refs` may use stable attention ids
- every other proposal provenance ref must resolve as a durable stack path
- conversation-derived proposals must not store `knowledge:<id>` or `session:<id>` placeholders inside the proposal provenance block

## Dedupe And Idempotency

The loop is deterministic and idempotent.

Rules:

- reuse the existing initiative when attention or session evidence clearly maps to it
- prefer task-scoped clustering over spawning a new initiative
- only materialize new initiatives for existing initiative threads, attention-backed work, hypothesis-backed work, or repeated-session threads
- use one stable proposed-session id per initiative thread
- identical inputs must write the same proposal payload twice

## Execution Boundary

A proposed session must stay non-executing.

Required boundaries:

- `refs.request_ref`, `refs.approval_receipt_ref`, `refs.execution_receipt_ref`, and `refs.bridge_record_ref` stay null
- status, merge, and resume refs stay empty unless the proposal has actually become a governed session later
- `completion.final_status` stays null

If those fields appear in a proposal artifact, the proposal is out of contract.

## Commands

Dry run:

```powershell
python .\ops\atlas\run_initiative_loop.py --dry-run
```

Write initiatives and proposals:

```powershell
python .\ops\atlas\run_initiative_loop.py
```

Validate the stack:

```powershell
python .\ops\validation\validate_stack.py --ratchet
```
