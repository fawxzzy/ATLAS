# Cortex Simulation Substrate Readiness ATLAS Receipt Replay First-Implementation Worker-Cluster Reconciliation And 50 Percent Ratchet

- Date: `2026-07-14`
- Opening checkpoint: `main@04c16d52`
- Marker movement: `40% -> 50%`

## Implemented

- two versioned replay schemas
- `ops/cortex/receipt_replay.py`
- focused replay tests
- one committed mixed-source canary using `atlas.receipt.v1` and `atlas.execution-receipt.v2`
- repository-enforced LF normalization for replay fixtures so raw-byte digests remain portable

The helper verifies raw-byte digests, validates admitted contracts, rejects duplicate IDs, orders observations by recorded time and identity, preserves source status, classifies failure modes, and emits deterministic advisory replay plus schema-valid agent state.

## Canary Result

- status: `ok`
- threshold eligible: true
- receipt contracts: `2 / 2`
- trust class: `committed_replay_fixture`
- transitions: `2`
- success: `1`
- blocked: `1`
- replay ID: `sha256:b076e3e3b235961d06e6a3ef7e60c1acfc2618c8865bc16b3f2cd0bbb7a2acee`

The success cites the proved first read-only scenario helper. The blocker cites the transient working-memory catalog drift found and cleared during the 40% validation cluster. Replay did not execute or rewrite either event.

## Proof And Authority

Focused proof covers deterministic chronology, both receipt contracts, digest mismatch, duplicate identity, unknown contract, fixture-only threshold denial, safe output, unsafe paths, schema-valid agent state, and authority denial. Existing scenario-helper, agent-state, and requirements tests remain green.

Replay authorizes no execution, dispatch, owner mutation, platform mutation, Discord or board write, deployment, approval, final receipt, or automatic marker movement. It uses no model, network, browser, or subprocess.

## Marker Decision

Move `Cortex Simulation Substrate Readiness` from `40%` to `50%` because deterministic workflow/failure-mode replay from admitted Atlas receipt contracts now exists and passes the mixed-source threshold.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness project-specific simulation adapter selection contract freeze
```

## Reusable Governance

**RULE - Receipt replay preserves source status.** Classification may summarize but cannot overwrite receipt truth.

**PATTERN - Mixed success/failure canary.** A replay threshold requires both a successful and a failed or blocked observation from threshold-eligible sources.

**FAILURE MODE - Digestless simulation history.** Replay accepts mutable files without pinning exact source bytes.
