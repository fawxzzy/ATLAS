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
- no write or apply path

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

### Resume paused session

Current behavior is intentionally narrow:

- locate a `resume_ready` session
- fetch the governed session manifest
- return the merge completion ref and resume-context refs

It does **not** invoke a direct resume executor because no root-owned resume executor is currently published.

That keeps the voice surface truthful and avoids bypassing the governed loop.

### Plan and decision authoring

These call `ops/atlas/author_working_memory.py` against the active governed session.

## Notifications

Watch mode polls the Awareness API and speaks when:

- a session state changes
- a blocked worker appears
- a merge request remains open
- a session needs resume follow-up

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
- no voice path bypasses session or approval flow

