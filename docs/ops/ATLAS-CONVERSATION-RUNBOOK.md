# ATLAS Conversation Runbook

`ops/atlas/converse.py` is the root conversation runtime for grounded ATLAS text and voice turns.

## Purpose

Conversation is a governed client layer above awareness, working memory, initiatives, sessions, and knowledge.

The runtime must:

- query Awareness and working-memory surfaces first
- build a deterministic turn context from the minimum relevant refs
- write durable conversation manifests and grounded turn artifacts
- author proposal-only follow-up artifacts when a turn requests action

The runtime must not:

- keep a private hidden state store
- treat raw transcripts as durable truth
- execute Lifeline or `_stack` work directly

## Artifact Roles

Conversation manifest:

- one durable identity for an ongoing text or voice thread
- tracks current status, automation ceiling, related initiatives, related sessions, recent turns, and linked memory/attention refs
- stored at `runtime/atlas/conversations/<conversation_id>/conversation.manifest.json`

Turn artifact:

- one grounded turn outcome
- stores `input_summary`, `retrieved_ref_set`, `response_summary`, proposal refs, memory refs, query trace, and provenance
- stored at `runtime/atlas/conversations/<conversation_id>/turns/<turn_id>.json`

Memory artifact:

- durable initiative / plan / decision / hypothesis state owned by working memory
- remains a separate lane from conversation turns
- may be linked from a turn, but is not replaced by the turn

## Transcript Exclusion

Raw transcript and raw audio are not part of the durable truth path.

Durable conversation truth is:

- structured turn summaries
- retrieved refs
- authored proposal refs
- authored memory refs
- deterministic provenance

## Automation Ceiling

Conversation clients are capped at `request_action`.

Rules:

- informational turns stay read-only
- action-seeking turns must emit a proposal or request artifact
- conversation turns may not execute governed work
- execution still requires approval and the existing Lifeline path

## Turn Loop

1. user turn enters `converse.py`
2. `build_turn_context.py` classifies intent and queries the minimum relevant surfaces
3. `plan_conversation_response.py` composes a grounded response with cited refs
4. optional initiative refinement and proposal-only session authoring occurs
5. turn artifact and conversation manifest are persisted
6. status, descriptors, and the world model are refreshed

## Query-First Rule

Grounding stays query-first / hydrate-later:

- metadata-only surfaces stay metadata-only
- derived-only knowledge can be cited when promotion-safe
- Verta remains visible but untrusted and metadata-only
- conversation provenance must remain reconstructable from explicit refs

## Commands

One grounded text turn:

```powershell
python .\ops\atlas\converse.py --conversation-id atlas-main --mode text --input "what needs attention"
```

Action-seeking turn that authors a proposal instead of executing:

```powershell
python .\ops\atlas\converse.py --conversation-id atlas-main --mode text --input "run read-only scan on stack status"
```

Inspect a conversation through Awareness:

```powershell
python .\ops\atlas\awareness.py fetch conversation:atlas-main
```

## Verification

Minimum checks:

- same deterministic fixture yields the same manifest shape
- `conversation:<id>` resolves through Awareness fetch
- search by initiative or proposal ref returns the related conversation artifacts
- proposal turns emit `retrieved_ref_set` and full provenance
- stack validation remains green apart from inherited unrelated debt
