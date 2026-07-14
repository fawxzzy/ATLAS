# Cortex Dual-Mode Replacement Readiness primary-operator replay parity contract freeze

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `docs-only root-bounded replay-parity contract freeze`
- Marker movement: none; remains `90%`

## Decision

The deterministic dry-run primary operator is implemented and proof-backed. The next threshold is not another planner or acceptance schema. It is replay parity proving that the same governed decision remains available with no external adapter and that an optional ChatGPT/Codex projection cannot weaken authority.

Machine-readable doctrine:

- `docs/registry/CORTEX-PRIMARY-OPERATOR-REPLAY-PARITY-CONTRACT.v1.json`

## Replay modes

### Internal no-adapter baseline

Cortex produces the acceptance and receipt pair from the admitted plan, authority envelope, current lease receipts, and current root-truth digests. No ChatGPT or Codex projection is required.

### Optional adapter projection

One explicit adapter projection may be compared with the Cortex baseline. It is transport evidence only and cannot grant external actions, dispatch runtime work, claim mutation, replace `_stack`, or become source-of-truth authority.

## Comparison boundary

Parity covers plan identity, acceptance state, reason codes, source digests, dispatch and mutation flags, operator-plane ownership, adapter-required posture, receipt correlation, and external-action authority.

Allowed classifications are `equivalent`, `cortex_stricter`, `adapter_stricter`, `authority_regression`, `mismatch`, and `blocked`.

Cortex may be stricter than an adapter. An adapter may not be less restrictive than Cortex or claim authority that the accepted task envelope did not grant.

## First implementation boundary

Allowed:

- `ops/cortex/primary_operator_replay_parity.py`
- `tests/test_cortex_primary_operator_replay_parity.py`
- explicit output under `tmp/atlas/**.json`

The implementation is offline and deterministic. It performs no model call, network request, `_stack` dispatch, owner-repository mutation, Git action, Discord write, deployment, secret read, or marker movement.

## Marker decision

The marker remains `90%`.

Parity implementation will close the optional-adapter proof gap, but `100%` still requires one admitted `_stack` dispatch, a durable correlated runtime result, and an independent endgame audit.

## Exact next packet

```text
Cortex Dual-Mode Replacement Readiness replay-backed primary-operator parity first implementation
```

## Reusable knowledge

**RULE - Optional adapters cannot widen authority**

Transport parity is acceptable only when the adapter preserves or narrows the internal operator boundary.

**PATTERN - No-adapter baseline plus adapter projection**

Prove the internal decision path first, then compare one explicit adapter projection without making the adapter a runtime dependency.

**FAILURE MODE - Adapter parity by authority loss**

Two outputs are called equivalent even though the external projection drops blockers, dispatch denials, or receipt correlation.
