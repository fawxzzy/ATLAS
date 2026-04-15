# ATLAS Voice Runbook

## Purpose

`ops/atlas/talk.py` is the local explicit-command voice shell for ATLAS.

It is a client on top of the Awareness API and the conversation runtime. It is not a second orchestrator.

## Boundary

Rules:

- chat, voice, CLI, and dashboards are clients
- ATLAS root remains the source of truth
- voice reads through the Awareness API first
- voice routes commands through `ops/atlas/converse.py`
- any action still routes through governed session artifacts and receipts

Current lane posture:

- push-to-talk or explicit typed command only
- grounded conversation turns over a stable conversation id
- read-only first with proposal-only action handling
- spoken notifications only
- no ambient hotword
- no streaming STT/TTS or barge-in yet
- no bypass around governed request or approval artifacts
- no broader machine mutation than the bounded workspace write class

## Supported Intents

- `what needs attention`
- `what changed today`
- `what initiatives are active`
- `summarize initiative mazer d2 learning scorer`
- `propose next work for initiative mazer d2 learning scorer`
- `what repo work is waiting on blessing review`
- `show blocked sessions`
- `resume paused session`
- `run read-only scan on <target>`
- `summarize current Verta posture`
- `create a plan`
- `create a decision`

## Intent Semantics

### Attention and change summary

These query the Awareness API read model and speak back concise summaries.

### Read-only scan

This now authors a proposal-only next step through the conversation runtime.

The voice client does not start execution directly.

### Bounded workspace write

When voice eventually requests the first truthful write class, it must still route through the same governed session and approval chain.

The write remains limited to:

- one bounded file apply
- inside the declared session workspace root
- receipt-backed with rollback metadata where available
- visible through root status and awareness

### Resume paused session

Current behavior is root-owned and governed:

- locate the relevant resume context through grounded conversation retrieval
- author a proposal-only follow-up instead of resuming directly
- keep approval and execution on the existing governed path

Voice issues a governed `request_action`. It does not invent a private resume path and it does not execute Lifeline directly.

### Plan and decision authoring

These call `ops/atlas/author_working_memory.py` against the active governed session.

## Notifications

Watch mode polls the Awareness API and speaks when:

- a session state changes
- a blocked worker appears
- a merge request remains open
- a session needs resume follow-up
- a governed resume fails
- a conversation turn leaves proposal-only follow-up in attention
- an initiative advertises open attention such as the Mazer soak-and-review follow-up

## Commands

One-shot command:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what needs attention" --mute
```

Push-to-talk:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --push-to-talk
```

Watch mode:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --watch
```

## Safety Boundary

- voice never reaches around the Awareness API for private state
- voice never bypasses `converse.py` for grounded command handling
- voice never mutates Lifeline directly
- voice never treats transcript residue as memory
- voice notifications are advisory only

## Verification

Minimum checks:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what needs attention" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what initiatives are active" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "summarize initiative mazer d2 learning scorer" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "propose next work for initiative mazer d2 learning scorer" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what repo work is waiting on blessing review" --mute
```

Expected properties:

- voice queries return current awareness data
- proposal-seeking turns author proposal artifacts instead of executing
- the same conversation id can accumulate grounded turns over time
- each grounded turn remains fetchable through Awareness as `conversation_turn:<turn_id>`
- no voice path bypasses session or approval flow
