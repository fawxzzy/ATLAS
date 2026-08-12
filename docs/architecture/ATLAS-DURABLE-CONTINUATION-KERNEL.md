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
its readback is reduced to `{thread_id, turn_id, status}` before persistence.
Prompt/model output is never stored.

The Stop hook is same-session acceleration and a mutually exclusive delivery
transport. In one SQLite transaction it consumes one `PENDING` row into the
sent-unconfirmed `DISPATCHED` state, binds `delivery_method=STOP_HOOK`, and then
returns only `decision=block` plus packet, context-pack, and trigger identities.
The external dispatcher can therefore never lease that trigger. Unbound,
malformed, or unavailable hook evidence returns `{}` and permits the session to
stop.

Startup recovery is an explicit one-shot call:

- expired unsent leases return to `PENDING`;
- exact sent readback becomes `CONFIRMED`;
- sent-but-unconfirmed work past its deadline becomes an ambiguity dead letter;
- desired active compute without direct turn evidence becomes
  `UNEXPECTED_IDLE` / `RESUMABLE_QUEUED`.

No background scanner is started. Process startup, a local event, or an
explicit operator command invokes one reconciliation pass.

## Authorization, cost, and conflicts

Successor dispatch is automatic only for `AUTO_AUTHORIZED_LOCAL_ONLY` or
`EXPLICIT_AUTHORIZED_LOCAL_ONLY` and `LOCAL_ZERO` or `NO_COST`. Other classes
remain blocked with no outbox row. Conflict claims are unique; one blocked lane
does not prevent another owner/conflict group from advancing.

Capacity and token exhaustion are resumable queued states. Identity mismatch,
hostile readback, and sent-without-confirmation ambiguity fail closed.
Capacity is never inferred after an adapter invocation begins: lost readback
remains sent-unconfirmed and cannot be leased again.

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
