# Stack Lock Decision - Fitness Discord Worker Poll Interval Tuning

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: stack-lock decision
Status: accepted into root truth

## Decision

Accept the canonical Fitness repo commit that lowers the Discord worker fallback poll interval from `15s` to `5s` into ATLAS root lock truth and repin `stack.lock.yaml`.

Accepted Fitness commit:

- `8a98f9f2389637d5b1182bb83aedfa13747780cb`
- `perf: tighten discord worker fallback poll`

Previous pinned Fitness commit:

- `2f07fcb5325dadb303e19431ee7326540db90c77`

## Why

This is a narrow runtime tuning package:

- it reduces visible fallback latency when the worker is not able to satisfy a command entirely through the immediate `MESSAGE_CREATE` wakeup path
- it preserves the existing event-driven Gateway model
- it does not widen deploy authority, Discord publication authority, or repo scope
- it passed targeted worker tests and repo verification

## Root Action

- repin `stack.lock.yaml` Fitness commit from `2f07fcb5325dadb303e19431ee7326540db90c77`
  to `8a98f9f2389637d5b1182bb83aedfa13747780cb`
- keep the change recorded as a stack-level receipt, not as a root-owned implementation lane

## Verification

Root validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
