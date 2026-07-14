# Owner-Lane Agent Service Bus And DiscordOS Ops Native-First Transport Reconciliation

- Date: `2026-07-14`
- Lane: `ATLAS-root owner-lane orchestration governance`
- Mode: `docs-only native-first transport reconciliation`
- Scope: `supersede the SQLite-first execution-queue assumption, retain the accepted request/receipt and single-writer contracts, and route the next proof to native Codex task/thread capability plus the smallest backend-neutral ledger boundary`
- Control-plane checkpoint: `main@7ca57586`
- Marker movement: `none; Owner-Lane Agent Service Bus & DiscordOS Ops Readiness remains 10%`

## Decision

The accepted target is native Codex execution plus thin Atlas governance.

Atlas does not implement a second worker runtime, custom scheduler, or SQLite execution queue by default. Native ChatGPT/Codex task handoff, Codex threads, worktrees, task events, and existing `_stack` operator commands remain the execution substrate. Atlas may add a backend-neutral ledger only for durable semantics that native execution does not close, including stable job/card correlation, resource leases, receipts, board events, marker evidence, and audit history.

SQLite remains a possible future storage backend. It is not an approved transport or execution runtime.

## Retained Contracts

The July 10 protocol freeze remains authoritative for:

- full local capability with task-scoped authority;
- no mixing of modern permission profiles and legacy sandbox settings;
- requested and effective runtime-policy receipts;
- stable request, task, thread, turn, worktree, commit, card, and receipt identities;
- idempotency and replay-safe external mutations;
- resource leases where writers or local resources collide;
- DiscordOS as the single logical Discord and board writer;
- sync/readback and correlated receipts;
- explicit authority for pushes, deployments, external writes, and live data mutation.

Its SQLite-first transport recommendation and queue-owned worker loop are superseded by this reconciliation.

## Next Proof

The next same-lane packet is:

`Owner-Lane Agent Service Bus & DiscordOS Ops native Codex task/thread capability spike first-implementation admission`

That packet must:

1. Prove the available native task/thread lifecycle on the current desktop host using bounded read-only work.
2. Record which identities, events, resume controls, result surfaces, and workspace bindings are durable and queryable.
3. Separate native capabilities from missing Atlas semantics.
4. Produce a backend-neutral ledger requirement set.
5. Avoid selecting SQLite, Supabase, Vercel Queues, or another backend.
6. Avoid owner-repository mutation, Discord mutation, deployment, secret access, and marker movement.

## Stop Conditions

Stop and return a blocker rather than inventing infrastructure if the spike cannot prove a native capability, if task history cannot be correlated safely, or if the required proof would expose secrets, hidden reasoning, or unrelated archived conversation content.

## Reusable Governance

**RULE - Native capability before custom infrastructure.**

Atlas implements only the durable semantics that remain missing after current native execution capabilities are proven.

**PATTERN - Native execution plus backend-neutral coordination.**

Codex executes work; `_stack` governs local operations; Atlas owns durable meaning; DiscordOS owns external board and publication writes.

**FAILURE MODE - Proposed transport becomes architecture by inertia.**

A detailed queue proposal is routed as the next implementation even after later evidence and an accepted architecture supersede its transport assumption.

