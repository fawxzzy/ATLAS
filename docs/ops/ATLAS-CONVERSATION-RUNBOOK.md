# ATLAS Conversation Runbook

`ops/atlas/converse.py` is the root conversation runtime for grounded ATLAS text and voice turns.

## Purpose

Conversation is a governed client layer above awareness, working memory, initiatives, sessions, and knowledge.

The runtime must:

- query Awareness and working-memory surfaces first
- build a deterministic turn context from the minimum relevant refs
- write durable conversation manifests and grounded turn artifacts
- author proposal-only follow-up artifacts when a turn requests action
- answer generic text turns from initiative / proposal / trust slices before falling back to stale `active_session`

The runtime must not:

- keep a private hidden state store
- treat raw transcripts as durable truth
- execute Lifeline or `_stack` work directly

Voice and text use the same runtime.

The voice client may interrupt spoken delivery, but it still writes the same durable conversation and turn artifacts as text mode.

Weak voice fallback is now explicit:

- if a voice utterance collapses into an ungrounded generic `status_overview` guess, the runtime prefers no committed turn
- short filler turns such as one-word or weak two-word residue do not mutate the conversation manifest
- explicit status requests still remain allowed voice turns

## Artifact Roles

Conversation manifest:

- one durable identity for an ongoing text or voice thread
- tracks current status, automation ceiling, related initiatives, related sessions, recent turns, and linked memory/attention refs
- stored at `runtime/atlas/conversations/<conversation_id>/conversation.manifest.json`

Turn artifact:

- one grounded turn outcome
- stores `input_summary`, `retrieved_ref_set`, `response_summary`, proposal refs, memory refs, query trace, and provenance
- CLI responses also expose `response_segments`, `intent`, and `action_mode` for local voice delivery
- uses a conversation-scoped `turn_id` so Awareness can fetch a turn by id without hidden lookup state
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

Voice validation logs may retain grounded turn summaries under `runtime/atlas/voice/runs/**`, but they must not retain raw transcript or raw audio.

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
4. proposal-seeking turns rebuild the world model early so attention can see the new request before proposal authoring
5. optional initiative refinement and proposal-only session authoring occurs
6. turn artifact and conversation manifest are persisted
7. status, descriptors, and the world model are refreshed

## Voice Delivery Model

`ops/atlas/talk.py --stream` is only a client layer above this runtime:

- continuous local STT finalizes one utterance at a time
- each finalized utterance becomes one grounded turn on the shared `conversation_id`
- except for weak voice fallback turns, which now return a no-commit response instead of persisting bogus status residue
- response delivery may be interrupted locally by barge-in
- interrupt stops TTS only; it does not alter the durable turn or manifest

## Query-First Rule

Grounding stays query-first / hydrate-later:

- metadata-only surfaces stay metadata-only
- derived-only knowledge can be cited when promotion-safe
- Verta remains visible but untrusted and metadata-only
- conversation provenance must remain reconstructable from explicit refs

## Initiative-First Ordering

Generic text answers should prefer this order:

- `waiting_on_review`
- `pending_proposals`
- `active_initiatives`
- `trust_posture`
- `active_session` only when the prompt is session-centric or the higher slices are empty

That prevents stale session truth from outranking live initiative truth such as:

- Mazer waiting on `fixed-blessed-id soak smoke`
- then `manual blessing review`
- with the proposal still non-executing

## Explicit Text Paths

The text planner now has direct grounded paths for:

- `what is active`
- `what needs attention`
- `what repo work is waiting on blessing review`
- `what proposal is pending`
- `summarize initiative <name>`
- `propose next work for initiative <name>`

Proposal-seeking turns remain proposal-only. They may author or reuse a proposal artifact, but they do not execute governed work.

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

Inspect a grounded turn through Awareness:

```powershell
python .\ops\atlas\awareness.py fetch conversation_turn:<turn_id>
```

Inspect the voice read model for one conversation:

```powershell
Invoke-WebRequest "http://127.0.0.1:8765/atlas/voice?conversation_id=atlas-main" -Headers @{ Authorization = "Bearer local-test" }
```

## Verification

Minimum checks:

- same deterministic fixture yields the same manifest shape
- repeated identical text turns yield the same `retrieved_ref_set` when the underlying world model is unchanged
- `conversation:<id>` resolves through Awareness fetch
- `conversation_turn:<turn_id>` resolves through Awareness fetch
- `/atlas/voice` surfaces recent grounded turns and voice-relevant notifications without private state
- search by initiative or proposal ref returns the related conversation artifacts
- `what repo work is waiting on blessing review` resolves to the Mazer initiative slice before any stale session headline
- `what proposal is pending` resolves from the pending-proposal slice
- `propose next work for initiative mazer d2 learning scorer` stays proposal-only
- proposal turns emit `retrieved_ref_set` and full provenance
- weak voice fallback turns do not append `recent_turn_refs` or overwrite the last grounded thread summary
- stack validation remains green apart from inherited unrelated debt
