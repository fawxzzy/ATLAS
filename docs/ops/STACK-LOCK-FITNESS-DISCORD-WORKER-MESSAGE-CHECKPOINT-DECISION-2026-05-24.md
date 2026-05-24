# Stack Lock Decision - Fitness Discord Worker Message Checkpoint

Date: 2026-05-24
Lane: Discord Workflow, Publication & Docs Reliability
Mode: stack-lock decision
Status: accepted into root truth

## Decision

Accept the canonical Fitness repo commit for Discord worker message checkpoint persistence into ATLAS root lock truth and repin `stack.lock.yaml`.

Accepted Fitness commit:

- `2f07fcb5325dadb303e19431ee7326540db90c77`
- `feat: persist discord worker message checkpoints`

Previous pinned Fitness commit:

- `8c94933de07f87b9abb9f0cf174b0229b5be91da`

## Why

This is a narrow canonical repo workflow hardening package:

- it improves restart-safe duplicate avoidance for the Fitness Discord Gateway worker
- it preserves the existing event-driven `MESSAGE_CREATE` wakeup plus interval fallback poll model
- it does not widen deploy authority, Discord publication authority, or public workflow semantics
- it passed targeted worker tests and repo verification

## Root Action

- repin `stack.lock.yaml` Fitness commit from `8c94933de07f87b9abb9f0cf174b0229b5be91da`
  to `2f07fcb5325dadb303e19431ee7326540db90c77`
- keep the change recorded as a stack-level receipt, not as a root-owned implementation lane

## Verification

Root validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
