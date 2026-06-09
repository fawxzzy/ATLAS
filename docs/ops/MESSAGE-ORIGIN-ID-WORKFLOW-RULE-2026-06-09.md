# Message Origin ID Workflow Rule - 2026-06-09

- Date: `2026-06-09`
- Owner: ATLAS root
- Mode: `workflow-rule receipt`
- Scope: `ChatGPT/Codex transcript origin labeling`

## Objective

Freeze the operator-requested message-origin ID rule for the ATLAS ChatGPT and Codex workflow so mixed transcripts can be scanned without guessing which assistant generated a message.

## Rule

Every assistant-originated ATLAS workflow message must begin with a visible origin ID.

Required prefixes:

- ChatGPT messages begin with `CHATGPT-MSG-ID: <id>`.
- Codex messages begin with `CODEX-MSG-ID: <id>`.

Operator/user messages do not need an ID.

## ID Shape

Default ID shape:

- `CHATGPT-MSG-ID: CGPT-YYYY-MM-DD-###`
- `CODEX-MSG-ID: CODEX-YYYY-MM-DD-###`

The numeric suffix is a per-day sequence for that actor when possible. If exact sequencing cannot be verified after a restart, the assistant should use a fresh unique suffix and keep the actor/date prefix rather than omitting the ID.

## Workflow Requirements

- The ID must appear at the start of each ChatGPT or Codex response before the substantive content.
- The ID identifies the source actor, not the lane, marker, PR, or receipt.
- The ID does not replace file receipts, commit SHAs, PR numbers, validation snapshots, or marker breakdowns.
- The ID must not be used to imply authority, verification, merge readiness, or marker movement.
- If Codex quotes or summarizes a ChatGPT message, it must not reuse the ChatGPT ID as its own message ID.
- If ChatGPT quotes or summarizes a Codex message, it must not reuse the Codex ID as its own message ID.

## Codex Standing Instruction

When operating on ATLAS work, Codex should prefix every response with:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
```

Codex should preserve the existing ATLAS output requirements after the ID, including:

- exact files changed
- commands run
- verification results
- marker movement or no-movement
- protected surfaces not touched
- next admissible move

## ChatGPT Standing Instruction

When operating on ATLAS work, ChatGPT should prefix every response with:

```text
CHATGPT-MSG-ID: CGPT-YYYY-MM-DD-###
```

ChatGPT should keep the existing ATLAS closing requirements after the ID, including the full marker breakdown and `Completion: X%` line.

## Protected Boundaries

This rule is workflow metadata only. It does not admit touching:

- `C:\ATLAS\repos\fawxzzy-fitness`
- `archive/`
- `.vercel` surfaces
- `.env` surfaces
- secret surfaces
- deployment surfaces

## Failure Mode

`Originless Transcript Drift`:

If assistant messages in a mixed ChatGPT/Codex workflow do not carry actor IDs, restart readers can confuse advice, execution reports, operator summaries, and Codex receipts, then route the next package from the wrong authority surface.

## Marker Decision

- `_stack Readiness`: no movement
- `AI Repetition-to-Automation Pipeline`: no movement

Why:

- this pass freezes a workflow-labeling rule only
- it does not add new automation capability, proof breadth, or marker-closing behavior

## Exact Next Package

- continue the current admitted ATLAS lane only after preserving this message-origin rule in active workflow prompts/surfaces as needed
