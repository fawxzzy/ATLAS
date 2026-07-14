# Cortex Simulation Substrate Readiness ATLAS Receipt Workflow And Failure-Mode Replay First-Implementation Admission

- Date: `2026-07-14`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Scope: `admit the exact receipt-replay implementation and focused proof surfaces`
- Opening checkpoint: `main@cc4e3b44`
- Marker movement: none

## Basis

The replay contract is frozen in:

- `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-ATLAS-RECEIPT-WORKFLOW-AND-FAILURE-MODE-REPLAY-CONTRACT-FREEZE-2026-07-14.md`
- `docs/registry/CORTEX-SIMULATION-RECEIPT-REPLAY-CONTRACT.v1.json`

This packet admits implementation surfaces only. It does not implement replay or move the marker.

## Admitted Files

The first implementation may create or modify only:

- `schemas/atlas.cortex.simulation.receipt-replay-manifest.v1.json`
- `schemas/atlas.cortex.simulation.receipt-replay.v1.json`
- `ops/cortex/receipt_replay.py`
- `tests/test_cortex_receipt_replay.py`
- `data/cortex/simulation-replays/first-mixed-replay/**.json`
- one implementation reconciliation receipt
- the Cortex Simulation marker, Book, registry, selector, and continuity projections needed for an evidence-backed ratchet

No owner repository or `_stack` implementation surface is admitted.

## Required CLI

```text
python ops/cortex/receipt_replay.py --json --manifest <root-relative-manifest> --output <root-relative-tmp-json> --strict
```

No default output path is allowed.

## Required Behavior

The implementation must:

1. validate the replay manifest
2. admit only the frozen path and trust classes
3. verify raw source-byte digests
4. validate `atlas.receipt.v1` and `atlas.execution-receipt.v2`
5. reject duplicate receipt IDs
6. order receipts by recorded time, ID, and source ref
7. preserve source receipt status and provenance
8. classify success, advisory, failure, and blocked transitions deterministically
9. create schema-valid advisory replay and agent state
10. expose whether threshold-eligible non-contract-fixture evidence participated
11. write only to one explicit `tmp/atlas/**.json` path
12. return nonzero in strict mode for blockers, advisory gaps, or fixture-only threshold evidence

## Required Canary

The committed first mixed replay must contain:

- at least one `atlas.receipt.v1` source
- at least one `atlas.execution-receipt.v2` source
- at least one success-class receipt
- at least one failure or blocked-class receipt
- exact source-byte digests
- at least one `committed_replay_fixture` trust class

The canary is a replay fixture, not a new final receipt. Its content must cite actual Atlas work or validation facts and remain summary-only.

## Required Proof

Focused tests must prove every item in the contract-freeze proof matrix, including fixture-only threshold rejection and a successful mixed-source canary replay.

The implementation cluster must also preserve:

- continuity health `ok`
- selector tests green
- working-memory catalog consistency
- stack validation with zero critical and zero error findings
- no owner, platform, Discord, board, deploy, secret, browser, model, network, or subprocess action

## Authority Boundary

The replay output remains advisory only. It cannot:

- execute or dispatch work
- approve or reject real work
- mutate a source receipt
- write a final receipt
- move a board or marker itself
- publish or deploy
- infer hidden transcript or owner truth

## Marker Decision

The marker remains `40%` until implementation, mixed-source canary replay, focused proof, and reconciliation all pass.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness ATLAS receipt workflow and failure-mode replay prompt-pack and worker handoff contract
```

## Completion

The first implementation boundary is admitted. No implementation, replay, or external action occurred in this packet.
