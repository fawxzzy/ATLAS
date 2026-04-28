# Cortex Receipt Handoff Contract

- Status: Draft
- Date: 2026-04-27
- Scope: Lane M review gate only

## Purpose

`CortexReceiptHandoffDraft` is a Cortex-owned review artifact.

It exists so Cortex can prepare deterministic handoff material for human review before any Lifeline compatibility path or write path exists.

The review gate exists to answer whether a draft is well-formed, reviewable, blocked, and eligible for later Lifeline presentation without turning review state into approval.

## Rule

Receipt handoff review can mark a draft human-review-ready, but it must never mark it auto-approved.

## Pattern

Cortex validates handoff readiness before any Lifeline compatibility or write path exists.

## Failure Mode

Do not let `review_ready`, `receipt_ready`, or `lifeline_candidate` become hidden approval.

## Required Review Inputs

The review gate requires these draft fields:

- `run_id`
- `receipt_title`
- `owner_layer`
- `selected_next_action`
- `next_required_layer`
- `tranche_complete`
- `receipt_ready`
- `blocked`
- `blocked_reason`
- `known_ambient_debt`
- `current_validation_debt`
- `applied_rules`
- `failure_modes_avoided`
- `reviewer_action_required`

Malformed or missing required fields fail clearly.

## Review Decision

The gate emits a deterministic JSON-serializable decision:

- `handoff_valid`
- `human_review_ready`
- `lifeline_candidate`
- `auto_approved`
- `blocked`
- `blocked_reason`
- `required_reviewer_action`

`auto_approved` is always `false`.

## Review Semantics

- `handoff_valid=true` means the draft satisfies the Lane M contract and does not hide an internal contradiction.
- `human_review_ready=true` means the draft is valid review material for a person, even when it is blocked.
- `lifeline_candidate=true` means the draft is valid, reviewable, not blocked, has no current validation debt, and has `receipt_ready=true`.
- `blocked=true` means the draft is not eligible for later Lifeline presentation in its current state.

## Blocking Rules

The review gate must block Lifeline candidacy when:

- `current_validation_debt` is non-empty
- `receipt_ready=false`
- the draft is internally inconsistent with its own blocked state

Examples of internal inconsistency:

- `blocked=false` while `current_validation_debt` is present
- `blocked=false` while `receipt_ready=false`
- `blocked=true` without a `blocked_reason`

## Boundary

Lane M keeps the ownership split explicit:

- Cortex may generate and review handoff drafts.
- Cortex may persist ignored runtime review artifacts.
- Cortex may not write Lifeline receipts.
- Cortex may not call connectors as part of handoff review.
- Cortex may not mutate owner repos as part of this contract.

This review gate is a contract hardening step, not a write path.
