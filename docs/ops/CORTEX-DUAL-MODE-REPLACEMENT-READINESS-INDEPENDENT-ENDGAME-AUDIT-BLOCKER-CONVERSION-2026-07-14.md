# Cortex Dual-Mode Replacement Readiness independent endgame audit blocker conversion

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Independent decision: `HOLD_90`
- Marker movement: none
- Mode: bounded root implementation and focused proof

## Independent findings

The first endgame audit accepted the real `_stack` dispatch, identity chain, no-change result, and 36-test focused baseline, but held the marker for three exact reasons:

1. the accepted decision and primary receipt remained only under disposable `tmp/atlas`
2. the optional-adapter replay report carried source digests without comparing them
3. the live worker trace contained a recursive Atlas-root search, so `no_secret_read` was not independently proven

The audit also identified one exit-policy defect: a correlated failed run returned success even when `safe_to_close=false`.

## Blocker conversion

The bounded repair changes only the Cortex primary-operator replay and dispatch boundaries plus their focused tests.

### Durable admission

`prepare` now persists:

```text
runtime/atlas/sessions/<acceptance-id>/cortex-primary-operator-decision.json
```

The artifact contains the exact acceptance, primary receipt, and admitted plan. The dispatch request records its root-relative path and byte digest. Terminal correlation reloads the durable artifact and fails closed on any acceptance, receipt, plan, or digest mismatch.

### Complete replay parity

Optional adapter projections must now provide the normalized source digests for the four required replay inputs. The report emits a literal `source_digests` comparison and returns `mismatch` for missing, malformed, or unequal adapter digests. The adapter projection itself is excluded from the compared source set so the contract does not require a self-referential digest.

### Read-scope proof

The generated canary prompt now:

- admits only the exact Atlas-root handoff file
- forbids recursive Atlas-root enumeration
- forbids `secrets/**`, `.env*`, credential, token, and browser-profile reads
- requires the `read-scope-confirmed` no-change assertion

Terminal correlation now reads the exact `_stack` `codex.stdout.log`, inspects command-execution events, and blocks closeout on a secret-path command or recursive Atlas-root read. A correlated failure or blocked read-scope result returns a nonzero process status because only `safe_to_close=true` is terminal success.

## Verification

```text
python -m unittest tests.test_cortex_primary_operator tests.test_cortex_primary_operator_replay_parity tests.test_cortex_primary_operator_stack_dispatch
```

Result:

```text
40 tests passed
```

The focused proof includes explicit mismatch tests for adapter source digests, secret-path reads, and recursive Atlas-root reads.

## Authority preservation

This package performed no `_stack` execution, owner-repository mutation, deployment, push, Discord write, board write, database mutation, secret read, or marker movement.

## Marker decision

The marker remains `90%`. A fresh live no-change canary and a new independent endgame audit are still required before `100%` can be considered.

## Next packet

```text
Cortex Dual-Mode Replacement Readiness repaired live no-change canary and independent endgame re-audit
```
