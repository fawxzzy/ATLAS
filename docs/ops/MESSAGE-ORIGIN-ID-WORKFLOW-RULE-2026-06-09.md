# Message Origin ID Workflow Rule

Date: 2026-06-09
Status: Active
Scope: ATLAS workflow messaging metadata only

## Purpose

Freeze a visible origin-ID rule for assistant-authored ATLAS workflow messages so message provenance survives restarts, handoffs, and quoted cross-assistant receipts.

## Rule

Every assistant-originated ATLAS workflow response must begin with a visible origin ID.

- ChatGPT format: `CHATGPT-MSG-ID: CGPT-YYYY-MM-DD-###`
- Codex format: `CODEX-MSG-ID: CODEX-YYYY-MM-DD-###`
- Operator or user messages: no origin ID required

The origin ID identifies the source actor only. It does not replace receipts, commit SHAs, PR numbers, validation snapshots, marker breakdowns, or authority boundaries.

## Sequencing Fallback

If exact sequencing cannot be verified after a restart, the assistant should emit a fresh unique suffix while preserving the actor and date prefix. Do not omit the origin ID because the previous ordinal is uncertain.

## Workflow Requirements

- The ID must appear at the start of each ChatGPT or Codex response before substantive content.
- The ID must not be used to imply authority, verification, merge readiness, or marker movement.
- If Codex quotes or summarizes a ChatGPT message, it must not reuse the ChatGPT ID as its own message ID.
- If ChatGPT quotes or summarizes a Codex message, it must not reuse the Codex ID as its own message ID.

## Codex Standing Instruction

Codex-originated ATLAS workflow responses should start with:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
```

After that ID, Codex should continue preserving normal ATLAS output requirements:

- exact files changed
- commands run
- verification results
- marker movement or no-movement
- protected surfaces not touched
- next admissible move

## ChatGPT Standing Instruction

ChatGPT-originated ATLAS workflow responses should start with:

```text
CHATGPT-MSG-ID: CGPT-YYYY-MM-DD-###
```

ChatGPT should keep the existing ATLAS closing requirements after the ID, including the full marker breakdown and `Completion: X%` line.

## Protected-Surface Boundary

This rule is workflow metadata only. By itself it does not authorize touching:

- `archive/`
- `.vercel`
- `.env`
- secret surfaces
- deployment surfaces
- Fitness or other owner-repo code

## Failure Mode

`Originless Transcript Drift`: if assistant messages in a mixed ChatGPT/Codex workflow do not carry actor IDs, restart readers can confuse advice, execution reports, operator summaries, and Codex receipts, then route the next package from the wrong authority surface.

## Marker Decision

- `_stack Readiness`: no movement
- `AI Repetition-to-Automation Pipeline`: no movement

Reason: this receipt freezes message-labeling policy only. It does not add automation capability, broaden proof, or close a blocker lane.
