# Cortex Simulation Substrate Readiness First Read-Only Scenario Helper Contract Freeze

- Date: `2026-07-14`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root implementation contract freeze`
- Scope: `freeze one deterministic synthetic-fixture-to-advisory-agent-state helper without model, network, execution, or owner authority`
- Opening checkpoint: `main@74de6d7c52af901aff96b4556c353e133ef7d4d3`
- Marker movement: none

## Admitted Implementation

The first helper is limited to:

- `ops/cortex/read_only_scenario_helper.py`
- `tests/test_cortex_read_only_scenario_helper.py`

It consumes one explicit root-relative synthetic fixture under:

```text
data/cortex/simulation-fixtures/**.json
```

It may write one explicit advisory output under:

```text
tmp/atlas/**.json
```

## CLI

```text
python ops/cortex/read_only_scenario_helper.py --json --input <root-relative-fixture> --output <root-relative-tmp-json> --strict
```

No default output file is allowed.

## Deterministic Behavior

The helper may only:

1. validate a synthetic scenario fixture
2. normalize admitted observations into schema-valid memories
3. select memories using explicit confidence and deterministic ordering
4. derive one clearly labeled advisory reflection
5. derive one candidate plan with `execution_authorized=false`
6. emit `atlas.cortex.simulation.agent-state.v1`

Identical committed inputs must produce identical output bytes.

## Denied Behavior

The helper may not:

- call a model
- access a network
- run commands or subprocesses
- execute a plan or action
- read owner repositories
- read hidden chats, transcripts, sessions, browser state, or secrets
- read raw live user data
- accept unknown or blocked rights
- accept prohibited privacy classes
- accept rejected injection state
- mutate runtime latest files, markers, receipts, Discord, boards, platforms, or deployments

## Proof Matrix

The implementation must prove:

1. deterministic output
2. schema-valid advisory state
3. top-level and plan execution denial
4. synthetic-fixture input guard
5. safe explicit output guard
6. owner, secret, hidden-context, absolute, and traversal path rejection
7. unknown fixture-field rejection
8. unsafe rights, privacy, and injection rejection
9. no file written without explicit output
10. strict-mode failure for advisory gaps or blockers

## Marker Decision

The marker remains `30%` in this contract freeze. It may move to `40%` only after the helper and focused proof land and reconcile.

## Exact Next Packet

```text
Cortex Simulation Substrate Readiness first read-only scenario helper implementation and reconciliation
```
