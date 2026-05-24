# Stack Lock Decision - Fitness Discord Greeting Triggers

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: stack-lock decision
Status: accepted into root truth

## Decision

Accept the canonical Fitness repo commit that adds greeting aliases and the scheduled goodnight post into ATLAS root lock truth and repin `stack.lock.yaml`.

Accepted Fitness commit:

- `f76357846dded35cb9858d8bc2033280cd804dd0`
- `feat: add discord greeting triggers`

Previous pinned Fitness commit:

- `8a98f9f2389637d5b1182bb83aedfa13747780cb`

## Why

This is a narrow Discord workflow extension:

- it adds exact-match greeting triggers instead of broad phrase interception
- it keeps the secured poll route as the authority path
- it adds a scheduled `10:00 PM` goodnight post beside the existing `Grand Rising` schedule
- it does not widen deploy, release, or publication authority
- it passed targeted worker tests and repo verification

## Root Action

- repin `stack.lock.yaml` Fitness commit from `8a98f9f2389637d5b1182bb83aedfa13747780cb`
  to `f76357846dded35cb9858d8bc2033280cd804dd0`
- keep the change recorded as a stack-level receipt, not as a root-owned implementation lane

## Verification

Root validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
