# ATLAS Voice Runbook

## Purpose

`ops/atlas/talk.py` is the local voice client for ATLAS.

It is a client on top of the Awareness API and the conversation runtime. It is not a second orchestrator.

## Boundary

Rules:

- chat, voice, CLI, and dashboards are clients
- ATLAS root remains the source of truth
- voice reads through the Awareness API first
- voice routes commands through `ops/atlas/converse.py`
- any action still routes through governed session artifacts and receipts

Current lane posture:

- continuous local streaming speech recognition over one conversation id
- chunked streaming speech synthesis over grounded runtime responses
- barge-in / interrupt cancels speech delivery without mutating conversation state
- read-only first with proposal-only action handling
- spoken completion / approval-needed / blocked notifications through Awareness
- no ambient hotword
- no remote voice execution path in this lane
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

### Grounded multi-turn conversation

Streaming mode keeps one stable `conversation_id` and sends each finalized utterance through `ops/atlas/converse.py`.

Conversation truth stays durable as:

- grounded turn summaries
- retrieved refs
- proposal refs
- authored memory refs
- deterministic provenance

Raw transcript and raw audio are not durable truth.

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

Voice mode and watch mode poll the Awareness API `/atlas/voice` surface and speak when a new item appears in one of these categories:

- `completion`
- `approval_needed`
- `blocked`

Examples:

- an initiative proposal is waiting for operator review
- an active session is waiting for explicit resume or merge follow-up
- a merge request remains open
- the Mazer D2 soak-and-review proposal remains pending

The first poll seeds the baseline and does not replay old notifications.

## Streaming Model

`--stream` runs a continuous microphone loop with these rules:

- recognition stays local using Windows `System.Speech`
- finalized utterances call the same grounded conversation runtime as text mode
- response speech is emitted in short segments so it can be interrupted cleanly
- any new partial utterance during speech counts as barge-in and cancels the remaining spoken response
- interrupt affects speech delivery only; it does not rewind or delete the already-written conversation turn

Local control phrases:

- `stop`
- `stop talking`
- `cancel response`
- `exit atlas`

## Operator Run Logs

Streaming, watch, and one-shot `--command` runs write transcript-safe operator logs under:

- `runtime/atlas/voice/runs/<conversation_id>/<run_id>.jsonl`
- `runtime/atlas/voice/runs/<conversation_id>/<run_id>.summary.json`
- `runtime/atlas/voice/runs/<conversation_id>/latest.summary.json`

Those logs are for validation and operator audit only.

They keep:

- grounded turn ids, refs, intent, action mode, and summaries
- voice notification summaries
- interrupt events and diagnostics

They do not keep:

- raw microphone audio
- raw transcript residue

## Commands

One-shot command:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what needs attention" --mute
```

Continuous streaming voice:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --conversation-id voice-mazer --stream --print-partials
```

Push-to-talk fallback:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --push-to-talk
```

Watch mode:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --watch
```

Inspect the voice read model directly:

```powershell
Invoke-WebRequest "http://127.0.0.1:8765/atlas/voice?conversation_id=voice-mazer" -Headers @{ Authorization = "Bearer local-test" }
```

## Safety Boundary

- voice never reaches around the Awareness API for private state
- voice never bypasses `converse.py` for grounded command handling
- voice never mutates Lifeline directly
- voice never treats transcript residue as memory
- voice interrupt cancels TTS only; it does not bypass or edit durable turn artifacts
- voice notifications are advisory only

## Target-Machine Validation Notes

Use the Mazer initiative as the first real fixture on the target machine:

1. start `--stream` on one stable `conversation_id`
2. ask for the initiative summary
3. ask what repo work is waiting on blessing review
4. ask for the next work proposal
5. interrupt one longer response mid-stream and confirm the conversation manifest and turn refs remain intact

After the run, inspect:

- `runtime/atlas/conversations/<conversation_id>/conversation.manifest.json`
- `runtime/atlas/voice/runs/<conversation_id>/latest.summary.json`
- `runtime/atlas/voice/runs/<conversation_id>/<run_id>.jsonl`

## Known Limitations

- barge-in quality depends on the target machine's default microphone and speaker routing
- open-air speakers may self-trigger interrupts; headphones or separated audio paths are the expected operator setup
- Windows `System.Speech` remains the current local STT/TTS dependency for this lane
- this lane proves local operator audio only; it does not add hotword mode or remote execution

## Verification

Minimum checks:

```powershell
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what needs attention" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what initiatives are active" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "summarize initiative mazer d2 learning scorer" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "propose next work for initiative mazer d2 learning scorer" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --command "what repo work is waiting on blessing review" --mute
python .\ops\atlas\talk.py --base-url http://127.0.0.1:8765 --auth-token local-test --conversation-id voice-mazer --stream --print-partials
Invoke-WebRequest "http://127.0.0.1:8765/atlas/voice?conversation_id=voice-main" -Headers @{ Authorization = "Bearer local-test" }
```

Expected properties:

- voice queries return current awareness data
- proposal-seeking turns author proposal artifacts instead of executing
- the same conversation id can accumulate grounded turns over time
- `/atlas/voice` returns current digests, active session state, filtered notifications, and recent conversation turns
- barge-in stops spoken delivery without corrupting the conversation manifest or turn refs
- transcript-safe run logs land under `runtime/atlas/voice/runs/**`
- each grounded turn remains fetchable through Awareness as `conversation_turn:<turn_id>`
- no voice path bypasses session or approval flow
