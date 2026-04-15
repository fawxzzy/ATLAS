# ATLAS Voice Runbook

## Purpose

`ops/atlas/talk.py` is the local explicit-command voice shell for ATLAS.

It is a client on top of the Awareness API and session runner. It is not a second orchestrator.

## Boundary

Rules:

- chat, voice, CLI, and dashboards are clients
- ATLAS root remains the source of truth
- voice reads through the Awareness API first
- any action still routes through governed session artifacts and receipts

Current lane posture:

- push-to-talk or explicit typed command only
- read-only first
- spoken notifications only
- no ambient hotword
- no bypass around governed request or approval artifacts
- no broader machine mutation than the bounded workspace write class

## Supported Intents

- `what needs attention`
- `what changed today`
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

This creates a governed root session via `ops/atlas/run_session.py` and returns the session id.

### Bounded workspace write

When voice eventually requests the first truthful write class, it must still route through the same governed session and approval chain.

The write remains limited to:

- one bounded file apply
- inside the declared session workspace root
- receipt-backed with rollback metadata where available
- visible through root status and awareness

### Resume paused session

Current behavior is root-owned and governed:

- locate a `resume_ready` session
- invoke `ops/atlas/resume_session.py`
- validate merge completion, resume-context, paused handoff refs, `stack_lock_digest`, `tool_id`, and `registry_digest`
- dispatch the resumed worker through the existing `_stack` path only
- emit `resume_requested`, `resume_dispatched`, and `resume_completed` or `resume_failed`

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
- voice never mutates Lifeline directly
- voice never treats transcript residue as memory
- voice notifications are advisory only

## Verification

Minimum checks:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what needs attention" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "show blocked sessions" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "run read-only scan on stack status" --mute
```

Expected properties:

- voice queries return current awareness data
- read-only sessions still produce governed receipts and snapshots
- resume uses the same governed root executor as local CLI
- no voice path bypasses session or approval flow
