# Cortex Simulation Substrate Readiness Project-Specific Simulation Adapter Selection Contract Freeze And 60 Percent Ratchet

- Date: `2026-07-14`
- Opening checkpoint: `main@7ff2c620`
- Marker movement: `50% -> 60%`

## Decision

Select four project adapter contracts without implementing or activating any owner-lane adapter.

| Adapter | Inputs | Advisory output | Owner | Priority |
| --- | --- | --- | --- | --- |
| Atlas workflow resilience | Root execution, validation, marker, continuity, and replay receipts | likely blocker sequence, recovery rehearsal, and next-proof recommendation | Atlas root | first prototype |
| Mazer play-loop and visual QA | Explicit committed game-test, visual-proof, and release receipts | scenario coverage and regression rehearsal | Mazer | selected, held |
| Fitness progression and release | Explicit contract-valid QA, progression, build, and deployment receipts | workflow and release-risk rehearsal | Fitness | selected, held |
| DiscordOS board and publication | Board-event, publication, idempotency, retry, and readback receipts | card lifecycle and publication-failure rehearsal | DiscordOS | selected, held |

## Shared Boundary

Every adapter is read-only, receipt-driven, digest-bound, summary-only, and advisory. No adapter may read hidden chats, secrets, raw live user data, arbitrary owner files, or browser sessions. No adapter may execute, dispatch, commit, publish, deploy, write Discord, mutate boards, move markers, approve work, or write final receipts.

## Project Constraints

- Atlas uses root receipts only and cannot mutate root truth from simulation output.
- Mazer requires explicit visual-proof provenance and cannot control the persistent live-preview workspace.
- Fitness excludes account secrets, service-role keys, raw health data, and live user records.
- DiscordOS replays receipts only; it remains the sole logical writer, and simulation creates no second writer.

## Selection And Priority

Atlas workflow resilience is selected for the first safe prototype at 70% because it can operate entirely on already-governed root receipts without crossing owner or platform boundaries.

The other three adapters are selected but held until the Atlas prototype proves the shared adapter envelope and each owner lane separately admits its inputs.

## Marker Decision

Move `Cortex Simulation Substrate Readiness` from `50%` to `60%`. The denominator requires project-specific adapters to be selected, not implemented.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness Atlas workflow-resilience safe scenario simulator prototype contract freeze
```

## Governance

**RULE - Selection is not adoption.** Naming an adapter does not authorize owner access or implementation.

**PATTERN - Root-first adapter proving.** Prove the shared envelope on root-owned receipts before asking owner projects to adopt it.

**FAILURE MODE - Adapter selection as authority grant.** A planning matrix is treated as permission to read or mutate owner systems.
