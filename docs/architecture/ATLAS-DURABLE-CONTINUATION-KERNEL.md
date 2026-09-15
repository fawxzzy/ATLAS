# ATLAS Durable Continuation Kernel

## Status

Wave 1 is a source-proven, local-only extension of `AtlasRuntime`. It is not
installed, globally trusted, deployed, or production-active. The worktree Stop
hook configuration is an inert source fixture until a separate installation
decision explicitly binds and trusts it.

## Decision

ATLAS owns durable continuation state. Codex is a persistent execution surface,
not the system of record. Arbitrary Desktop-owned tasks are not treated as a
durable control contract. ATLAS-owned owner/thread bindings are registered once
and every trigger resumes only that existing thread.

The kernel extends the existing SQLite runtime. It does not introduce a second
scheduler, task protocol, supervisor conversation, heartbeat, cron job, or
polling loop.

## Transaction boundary

One `BEGIN IMMEDIATE` transaction performs the terminal transition:

1. validate the terminal event digest and owner revision;
2. settle the active packet and release its conflict claim;
3. select the deterministic same-owner successor;
4. evaluate embedded authorization and typed cost;
5. reserve the successor conflict claim;
6. insert one content-bound transactional-outbox row; and
7. update desired/observed owner liveness and metrics.

An exception at any step rolls the whole transition back. Exact replay is a
read-only no-op. A changed replay with the same logical identity fails closed.

## Trigger and recovery path

`ContinuationDispatcher` leases one outbox row, durably marks it
sent-unconfirmed, and only then calls a `TriggerAdapter`.
The production-shaped adapter exposes only `start_existing_turn`; it has no
thread-creation method. Its command surface is `codex exec resume <thread>` and
it correlates the separate `thread.started` and `turn.started` JSONL lifecycle
records. Host acknowledgement is persisted separately from owner execution
truth. The bounded post-trigger readback then requires at least one non-reasoning
owner item and a newly persisted, digest-valid checkpoint for the same owner
thread before the outbox becomes `CONFIRMED`. Missing turns, zero-output turns,
and missing or unchanged checkpoints become exact `RECONCILE_ONLY` dead letters;
they are never blind-resubmitted. Prompt/model output and checkpoint content are
never stored in the outbox; only structural counts and checkpoint identities are
retained.

Every production dispatcher, including the event-driven ingress seam, must carry
that checkpoint probe. The compatibility confirmation path is fixture-only.
Startup recovery cannot promote a sent row from bare thread/turn identity; without
the complete acknowledgement, output-count, and advanced-checkpoint proof it
dead-letters the row as unproven readback.

The Stop hook is same-session acceleration and a mutually exclusive delivery
transport. In one SQLite transaction it consumes one `PENDING` row into the
sent-unconfirmed `DISPATCHED` state, binds `delivery_method=STOP_HOOK`, and then
returns only `decision=block` plus packet, context-pack, and trigger identities.
The external dispatcher can therefore never lease that trigger. The decision
requires a digest-valid baseline checkpoint. Finalization additionally requires
an authoritative event-bound trigger key and host turn identity that exactly
match the dispatched row. The currently supported Stop event supplies neither,
so its guarded follow-up returns `{}` and retains the sent-unconfirmed attempt
for bounded startup/readback reconciliation. It never selects a row by owner,
synthesizes a turn identity from checkpoint state, or claims completion from
structural output alone. A future supported transport may use the existing exact
acknowledgement/finalization seam only after supplying both identities. Unbound,
malformed, or unavailable hook evidence likewise returns `{}` and permits the
session to stop.

Startup recovery is an explicit one-shot call:

- expired unsent leases return to `PENDING`;
- bare sent thread/turn readback dead-letters as unproven `RECONCILE_ONLY`;
- an exact acknowledged running turn remains `DISPATCHED` until its execution deadline;
- sent-but-unconfirmed work past its deadline becomes an ambiguity dead letter;
- desired active compute without direct turn evidence becomes
  `UNEXPECTED_IDLE` / `RESUMABLE_QUEUED`.

An absent turn inventory is not evidence of idleness. Active-owner liveness is
reconciled only when the caller supplies an authoritative inventory, including
an explicitly empty inventory. Event ingress without that inventory performs
outbox recovery but cannot create a duplicate continuation turn.

No background scanner is started. Process startup, a local event, or an
explicit operator command invokes one reconciliation pass.
The production existing-thread command streams lifecycle records. It has a
30-second trigger-acknowledgement deadline through the correlated
`thread.started`/`turn.started` pair, followed by a separate 1,800-second owner
execution deadline for bounded output, `turn.completed`, and checkpoint proof.
The acknowledgement atomically replaces the short deadline with the execution
deadline; startup recovery distinguishes an unacknowledged ambiguity from an
acknowledged execution timeout. Matching observed turn identity never extends
or bypasses that execution deadline; an acknowledged row without completed
output and checkpoint proof becomes `APP_READBACK_FAILED` / `RECONCILE_ONLY`
once the deadline passes.
Either timeout is non-echoing `APP_READBACK_FAILED` and cannot become a
replayable capacity claim.

Process lifecycle projection is also state-bound. The event-driven ingress seam
records `STARTED` only inside a transaction that still observes the exact trigger
as acknowledged and `DISPATCHED`. A synchronously confirmed, blocked, failed, or
otherwise terminal dispatch already owns its `EXITED` or `FAILED` event and can
never receive a later contradictory `STARTED` event.

## Authorization, cost, and conflicts

Successor dispatch is automatic only for `AUTO_AUTHORIZED_LOCAL_ONLY` or
`EXPLICIT_AUTHORIZED_LOCAL_ONLY` and `LOCAL_ZERO` or `NO_COST`. Other classes
remain blocked with no outbox row. Conflict claims are unique; one blocked lane
does not prevent another owner/conflict group from advancing. Claim release and
startup reconciliation deterministically promote one dependency-ready waiter
per free conflict key, atomically creating its claim and unique outbox trigger.
The database also permits at most one open outbox trigger per uniquely bound
owner/thread. Migration fails closed when legacy state contains multiple open
rows for one owner instead of guessing which attempt is authoritative.
Exact settlement replay recovers blocked successor identity from durable packet
state even when authorization, cost, or conflict intentionally produced no
outbox row.

Capacity and token exhaustion are resumable queued states. Identity mismatch,
hostile readback, and sent-without-confirmation ambiguity fail closed.
Capacity is never inferred after an adapter invocation begins: lost readback
remains sent-unconfirmed and cannot be leased again.

The application-level cause of a silent accepted turn may remain unknown. The
kernel records the narrower observable boundary as `APP_READBACK_NO_TURN`,
`APP_READBACK_NO_OUTPUT`, `APP_READBACK_NO_CHECKPOINT`, or
`APP_READBACK_FAILED`; each preserves the exact failed outbox row with
`retry_class=RECONCILE_ONLY`.

## Context and privacy

Context packs are canonical, content-addressed JSON limited to 32 KiB. Keys
associated with secrets, credentials, tokens, prompts, transcripts, raw output,
or user content are rejected recursively. Continuation input contains only the
packet identity, context-pack identity, and compact references.

## Evidence required before installation

- focused runtime, outbox, hook, adapter, crash, replay, and restart tests twice;
- existing scheduler and workflow-recovery tests twice;
- full relevant ATLAS contract validation;
- path-ceiling and dirty-root preservation proof;
- hostile independent owner review;
- separate authority for hook installation or a real existing-owner canary.

Machine/app restart acceptance remains outside Wave 1 source authority.
