# Owner-Lane Agent Service Bus And DiscordOS Ops Native-To-Atlas Gap Matrix And Thin-Ledger Denominator Rebaseline

- Date: `2026-07-14`
- Lane: `ATLAS-root owner-lane orchestration governance`
- Mode: `docs-only backend-neutral gap and denominator contract freeze`
- Scope: `map proven native execution to missing Atlas semantics, freeze a ten-unit native-first denominator, and route the first implementation-backed correlation slice without selecting a ledger backend`
- Control-plane checkpoint: `main@e2ffda9d`
- Marker movement: `Owner-Lane Agent Service Bus & DiscordOS Ops Readiness: 10% -> 20%`

## Native-To-Atlas Gap Matrix

| Capability | Native proof | Atlas responsibility | Contract surface | State |
|---|---|---|---|---|
| Local project and task creation | project ID, task ID, local working directory | component/project identity and governed admission | `ComponentManifest`, `JobEnvelope` | partial |
| Turn execution and continuation | stable task and turn IDs, prior-context continuation | Atlas job/card/task/turn correlation | `JobEnvelope`, `ExecutionReceipt` | missing adoption |
| Result retrieval | terminal turn and final response readable | normalized terminal receipt and evidence classification | `ExecutionReceipt`, `EvidenceBundle` | missing native adapter |
| Runtime policy | native task executes | requested/effective model, effort, speed, permissions, approvals | `JobEnvelope`, `ApprovalRecord`, `ExecutionReceipt` | missing from task read proof |
| Context binding | task receives bounded prompt context | provenance-bound Atlas/Playbook/Cortex context | `ContextPacket` | missing native adapter |
| Resource ownership | local project binding proven | worktree, branch, process, port, browser, writer, expiry, recovery | `WorkerLease` | missing |
| Retry and recovery | same-task continuation proven | state transitions, replay, cancellation, terminal failure, deduplication | `atlas.event.v1`, `ExecutionReceipt` | partial |
| Board and publication | native task can return result | DiscordOS single writer, idempotency, lifecycle, readback | `CardRecord`, `BoardEvent` | implemented elsewhere, not correlated here |
| Marker and knowledge closeout | none native | evidence-backed marker and reusable knowledge promotion | `MarkerEvidence`, `KnowledgeCandidate` | missing correlation |
| Task cleanup | title and archive proven | durable receipt before archive and searchable provenance | `ExecutionReceipt` plus Atlas index | partial |

No row requires a custom worker runtime.

## Fixed Ten-Unit Denominator

Each unit is binary. Documentation alone counts only where the unit is explicitly a governance-contract unit. Implementation units require executable producer/consumer proof and a durable receipt.

| Unit | Definition of done | Current result |
|---:|---|---|
| 1 | Native-first authority, permission, request/receipt, idempotency, lease, and Discord single-writer doctrine is frozen | complete |
| 2 | Native local project/task/turn creation, result read, continuation, title, and archive behavior is directly proven | complete |
| 3 | `JobEnvelope -> native task/turn -> ExecutionReceipt` correlation is implemented and validated | incomplete |
| 4 | Requested and effective runtime policy is captured or explicitly reported unavailable for every governed native task | incomplete |
| 5 | ContextPacket and EvidenceBundle are bound to native task input and terminal output with provenance | incomplete |
| 6 | WorkerLease governs worktree, branch, process, port, browser, and single-writer resource ownership | incomplete |
| 7 | Durable task state, retry, replay, cancellation, failure, and archive-after-receipt behavior is implemented | incomplete |
| 8 | BoardEvent/CardRecord integration reaches DiscordOS through one writer with idempotency and live readback | incomplete |
| 9 | MarkerEvidence and KnowledgeCandidate closeout is correlated to the execution receipt | incomplete |
| 10 | One Atlas, one Mazer, and one Fitness task complete end to end with recovery proof and no authority drift | incomplete |

Completed units: `2 / 10`.

Marker: `20%`.

This rebaseline gives no retroactive credit for adjacent implementations until they are explicitly correlated and proven under this lane.

## Backend-Neutral Ledger Boundary

The future ledger, if required, stores coordination meaning only:

- stable Atlas job/card/task/turn identities;
- state transition and idempotency records;
- requested/effective runtime-policy facts;
- resource leases;
- evidence and execution receipt references;
- board, marker, knowledge, and approval correlations;
- retry/replay/archive audit history.

It does not execute Codex, schedule its own worker loop, store private reasoning, duplicate Git truth, or infer external success without readback.

No backend is selected by this contract.

## Next Package

`Owner-Lane Agent Service Bus & DiscordOS Ops native task correlation first-implementation admission`

The next slice is unit 3 only. It must define and implement the smallest adapter that accepts a validated `JobEnvelope`, records the native task and turn IDs, and emits a validated `ExecutionReceipt` from the terminal result. It must reuse existing Atlas Contracts v2 schemas and validators, remain backend-neutral, and avoid owner-repository or external-system mutation.

## Reusable Governance

**RULE - Percentages measure completed denominator units, not architecture enthusiasm.**

**PATTERN - Native fact, Atlas correlation, contract validation, durable receipt.**

**FAILURE MODE - Adjacent capability counted without lane-specific adoption proof.**

An implementation elsewhere resembles a denominator unit but is credited before its producer, consumer, identity chain, and receipt are proven in the governed lane.

