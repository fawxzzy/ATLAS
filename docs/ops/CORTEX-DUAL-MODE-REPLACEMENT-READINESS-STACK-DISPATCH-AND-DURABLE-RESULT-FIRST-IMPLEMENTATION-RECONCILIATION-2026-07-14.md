# Cortex Dual-Mode Replacement Readiness _stack dispatch and durable result first implementation reconciliation

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `root-owned dispatch preparation and durable result correlation`
- Marker movement: none; remains `90%`

## Executed state

The first implementation is landed in:

- `ops/cortex/primary_operator_stack_dispatch.py`
- `tests/test_cortex_primary_operator_stack_dispatch.py`

The helper prepares one deterministic, authority-bounded `_stack` dispatch request and verified no-change prompt from an accepted Cortex primary-operator decision. It also correlates the resulting `_stack` run manifest, Atlas Contracts v2 JobEnvelope, and ExecutionReceipt back to the Cortex acceptance identity.

## Proven behavior

- unsafe or incomplete primary-operator decisions fail closed;
- request and session identities are deterministic;
- the request denies push, deploy, production, Discord, board, data, and other external mutations;
- the first prompt uses the existing `_stack` verified no-change contract;
- the parent-job chain preserves the Cortex acceptance identity;
- successful and failed terminal `_stack` results remain durably correlated;
- commits, changed paths, and authority actions block the no-change canary;
- preparation reads only explicit Atlas `tmp/atlas/**.json` or `runtime/atlas/**.json` inputs;
- result correlation reads only the three required artifacts beneath `repos/_stack/.codex/logs/**`;
- durable outputs remain restricted to Atlas runtime and temporary surfaces.

Focused proof: `12` tests passed.

The broader Cortex suite currently contains pre-existing feedback owner-layer fixture failures and two state/ambient-debt expectation failures. Those failures do not import or exercise this helper and are tracked as separate baseline debt rather than normalized inside this packet.

## Architecture result

Cortex can now produce the exact bounded request consumed by the existing `_stack` operator plane and can independently reconcile the terminal evidence without creating a competing scheduler or runtime.

The implementation does not itself dispatch work, mutate repositories, or claim external authority. `_stack` remains the execution owner.

## Marker decision

The marker remains `90%`.

The helper and deterministic proof are complete, but the live canary and independent endgame audit are still required before `100%`.

## Exact next packet

```text
Cortex Dual-Mode Replacement Readiness _stack verified no-change live canary and durable correlation
```

## Reusable knowledge

**RULE - Runtime correlation inputs are explicit protected artifacts**

A root correlator may read owner-runtime evidence only through a narrow allowlist of exact artifacts under the canonical owner runtime root.

**PATTERN - Native operator dispatch with root correlation**

Prepare a bounded request at root, execute through the existing owner operator, then correlate its native receipt rather than creating a second execution system.

**FAILURE MODE - Durable-path policy blocks legitimate runtime proof**

Treating local owner-runtime evidence as a committed durable path can either over-broaden absolute-path access or make real result correlation impossible.
