# ATLAS Memory Authoring Runbook

## Purpose

`ops/atlas/author_working_memory.py` converts governed session state into durable structured working memory.

It authors only typed memory objects:

- plan
- decision
- initiative
- hypothesis

It does not store transcript text and it does not create a second private memory store.

Manual profile slots are a separate durable memory surface.

Current canonical operator profile:

- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/memory/profiles/zachariah_workflow_profile.json`

Rule:

- use manual profile slots for durable operator and assistant bootstrap context
- use authored working memory for session-derived plans, decisions, initiatives, and hypotheses
- do not collapse both surfaces into one undocumented blob

## Inputs

Authoring reads from governed root state:

- completed or active session manifests under `runtime/atlas/sessions/**`
- session-local status snapshots when present
- working-memory catalog state under `runtime/cortex/catalog/memory/working-memory.latest.json`
- clustered session history for repeated objectives

## Outputs

Source artifacts:

- `docs/memory/plans/*.json`
- `docs/memory/decisions/*.json`
- `docs/memory/initiatives/*.json`
- `docs/memory/hypotheses/*.json`

Derived catalog:

- `runtime/cortex/catalog/memory/working-memory.latest.json`

Current sample authored artifacts linked to governed sessions:

- `docs/memory/plans/plan-atlas-wave6-readonly.json`
- `docs/memory/decisions/decision-session-atlas-wave6-readonly-20260414t080653z.json`
- `docs/memory/initiatives/initiative-atlas-session-readonly.json`
- `docs/memory/hypotheses/hypothesis-atlas-session-conflict.json`

## Rules

### Transcript exclusion

Never author raw transcript text into working memory.

Allowed content:

- concise summary
- rationale
- evidence refs
- artifact refs
- supersession links
- stable ids and timestamps

Disallowed content:

- pasted chat logs
- copied terminal scrollback
- freeform private notes with no source refs

### Dedupe and idempotence

Authoring must update the same object when the same governed input is reprocessed.

Current stable ids:

- plans: `plan-<task-id>`
- decisions: `decision-<session-id>`
- initiatives: `initiative-<task-id>`
- hypotheses: `hypothesis-<task-id>`

Effect:

- identical inputs produce identical output
- reruns refine the existing memory object instead of creating duplicates

### Supersession

Supersession is explicit and link-based:

- use `supersedes`
- use `superseded_by`
- do not silently delete prior durable memory

## Commands

Author all default memory kinds for one session:

```powershell
python .\ops\atlas\author_working_memory.py --session-id session-atlas-wave6-readonly-20260414t080653z
```

Author a subset:

```powershell
python .\ops\atlas\author_working_memory.py --session-id session-atlas-wave6-readonly-20260414t080653z --memory-kind plan --memory-kind decision
```

Dry run:

```powershell
python .\ops\atlas\author_working_memory.py --session-id session-atlas-wave6-readonly-20260414t080653z --dry-run
```

Rebuild the catalog only:

```powershell
python .\ops\cortex\index_working_memory.py
```

## Verification

Minimum checks:

```powershell
python .\ops\atlas\author_working_memory.py --session-id session-atlas-wave6-readonly-20260414t080653z
python .\ops\atlas\author_working_memory.py --session-id session-atlas-wave6-readonly-20260414t080653z
python .\ops\cortex\index_working_memory.py
python .\ops\validation\validate_stack.py --ratchet
```

Expected properties:

- the second identical authoring run reports no content change
- malformed memory artifacts fail catalog validation
- the catalog stays rebuildable from `docs/memory/**`
- awareness and status surfaces can retrieve authored items by id and related session ref

## Operator Notes

- working memory is structured operator cognition, not promoted knowledge
- promoted knowledge remains under `docs/knowledge/promotions/**`
- receipts and observations remain the auditable event source
