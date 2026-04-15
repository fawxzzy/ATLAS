# ATLAS Initiative Runbook

This runbook defines the initiative layer above governed sessions.

## Purpose

Initiatives are the durable portfolio objects that keep ongoing work owned over time.

- attention says what needs a choice now
- an initiative says who owns the durable thread of work
- a proposed session says what governed work should happen next
- a session still remains the only execution gateway

The initiative layer is structure only in this wave. It does not grant execution authority.

## Storage

Store initiative artifacts under:

- `docs/memory/initiatives/`

Each initiative is a JSON document validated against `schemas/atlas.initiative.v1.json`.

## Required Fields

Every initiative must include:

- `contract_version`
- `id`
- `title`
- `status`
- `owner`
- `created_at`
- `updated_at`
- `related_plan_refs`
- `related_decision_refs`
- `related_hypothesis_refs`
- `related_session_refs`
- `related_attention_refs`
- `evidence_refs`
- `proposed_next_session_refs`
- `supersedes`
- `superseded_by`

`summary` is optional but recommended when the title alone is not enough.

## Lifecycle

The intended initiative lifecycle is:

1. attention surfaces a durable issue, risk, or opportunity
2. an initiative is created or refined instead of spawning duplicate session-local intent
3. proposed sessions attach to the initiative as non-executing next work
4. governed sessions execute only after approval through the normal path
5. receipts and closure evidence refine the initiative, plans, decisions, and hypotheses
6. the initiative is completed, superseded, or dismissed explicitly

## Relationship Rules

- `related_plan_refs` links the initiative to durable plans that shape the work
- `related_decision_refs` links to governing decisions that constrain or authorize the work
- `related_hypothesis_refs` links to active hypotheses that still need evidence
- `related_session_refs` links to governed sessions already run for the initiative
- `related_attention_refs` links to the attention items or attention-source refs that keep the initiative alive
- `evidence_refs` links to the supporting artifacts, receipts, manifests, or docs that justify the initiative
- `proposed_next_session_refs` links to proposed session artifacts only; proposals are not execution

Use refs to durable artifacts or stable awareness identifiers. Do not use transient chat text as the contract.

## Transcript-Exclusion Rule

Transcript residue is not initiative memory.

Do not put the following into initiative artifacts:

- raw chat dumps
- terminal scrollback
- unstructured "what we talked about" notes
- hidden private context summaries

If an initiative depends on a fact, cite the explicit artifact, receipt, status surface, or document ref instead.

## Ownership Rule

Nothing meaningful stays unowned.

If an attention item persists across sessions, it should either:

- attach to an existing initiative
- become a new initiative
- or be explicitly dismissed with supporting evidence

## Indexing And Status

Refresh the initiative-aware working-memory catalog with:

```powershell
python .\ops\cortex\index_working_memory.py
```

Awareness and status should expose initiatives as first-class searchable objects. Search must be able to find them by:

- initiative id
- initiative status
- related session refs
- related attention refs

## Governance Boundary

- initiatives do not execute work
- proposed sessions do not execute work
- sessions remain the approval and execution boundary
- receipts remain the evidence boundary
