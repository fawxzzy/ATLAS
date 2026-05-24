# Stack Lock Decision - Fitness Discord Goodnight Alias Expansion

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: stack-lock decision
Status: accepted into root truth

## Decision

Accept the canonical Fitness repo commit that expands the exact-match `goodnight` trigger family into ATLAS root lock truth and repin `stack.lock.yaml`.

Accepted Fitness commit:

- `fc5c86a95fb4ba7e1c5da919ed0e56fbb81b5d50`
- `feat: expand discord goodnight aliases`

Previous pinned Fitness commit:

- `f76357846dded35cb9858d8bc2033280cd804dd0`

## Why

This is a narrow Discord workflow refinement:

- it broadens the accepted night aliases without widening into fuzzy phrase interception
- it keeps the secured poll route and worker wakeup model unchanged
- it does not widen deploy, release, or publication authority
- it passed targeted worker tests and repo verification

## Root Action

- repin `stack.lock.yaml` Fitness commit from `f76357846dded35cb9858d8bc2033280cd804dd0`
  to `fc5c86a95fb4ba7e1c5da919ed0e56fbb81b5d50`
- keep the change recorded as a stack-level receipt, not as a root-owned implementation lane

## Verification

Root validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
