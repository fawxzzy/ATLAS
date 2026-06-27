# Sandbox Simulation Readiness Local-Only First Validator-Comparison Boundary Contract Freeze - 2026-06-27

- Date: `2026-06-27`
- Scope: `freeze exactly what a future local-only Sandbox validator may compare between the admitted input and expected-output surfaces without admitting validator execution, runner behavior, or any owner-repo, deploy, secret, or live-data widening`
- Lane: `Sandbox Simulation Readiness`
- Mode: `root-owned docs-only validator-comparison-boundary contract freeze`

## Objective

Clear the next exact Sandbox blocker by freezing the smallest honest comparison boundary over the admitted example root so future validator behavior cannot widen comparison meaning ad hoc.

## Executed

1. Froze the input fixture as contextual source material only, not as a direct pass/fail oracle by itself.
2. Froze the expected-output fixture `payload` subtree as the only current committed oracle surface for future comparison.
3. Froze the first bounded comparison family to exact equality over `payload.mode`, exact equality over `payload.status`, and ordered-string comparison over `payload.observations`.
4. Refreshed the maintained Sandbox continuity and restart surfaces so the exact next packet becomes one first validator-candidate-output shape contract freeze.

## Comparison Boundary Contract

### Committed Comparison Inputs

The future local-only validator may derive comparison truth only from:

1. `data/atlas/sandbox/fixtures/local-only-example-stub/inputs/first-input-stub.json`
2. `data/atlas/sandbox/fixtures/local-only-example-stub/expected-output/first-expected-output-stub.json`

Role split:

- the input fixture is contextual source material only
- the expected-output fixture is the current committed oracle surface

### Current Oracle Surface

Only this subtree is currently admitted as comparison truth:

- `expected_output.payload`

Within that subtree, the only currently frozen comparison fields are:

- `payload.mode`
- `payload.status`
- `payload.observations`

### First Bounded Comparison Family

If a later future packet admits real validator behavior, the first bounded comparison family may only:

- compare `payload.mode` by exact string equality
- compare `payload.status` by exact string equality
- compare `payload.observations` by ordered string-list equality

This packet does not admit:

- deep comparison over any future extra fields
- numeric tolerances
- partial-match semantics
- regex semantics
- unordered set semantics
- cross-scenario comparison
- comparison against runtime surfaces outside the frozen validation home

## Ratchet Decision

`Sandbox Simulation Readiness` moves from `39%` to `42%`.

Why:

- the lane already had one admitted validator-report stub and one frozen status-semantics layer
- the next exact ambiguity was what the validator may compare and where the current oracle truth actually lives
- one bounded comparison boundary is now frozen without widening into execution

It stays low because:

- no validator-candidate-output shape is frozen yet
- no validator execution exists
- no runner exists
- no `_stack` or owner-repo widening exists
- no proof-backed adoption exists

## Non-Claim

This does not prove:

- validator behavior
- comparison correctness
- runner behavior
- `_stack` ownership
- owner-repo execution
- safe unattended simulation

## Exact Next Package

- `Sandbox Simulation Readiness local-only first validator-candidate-output shape contract freeze`

Why:

- one bounded comparison boundary now exists over the admitted oracle fields
- the next honest move is to freeze the future candidate-output shape that a local-only validator would project into that boundary
- validator behavior, runner behavior, and wider execution claims remain premature
