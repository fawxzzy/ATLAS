# Automation And Command Candidates

## Purpose

This chapter maps repeated stack work into future automation and command surfaces without skipping current approval gates or owner boundaries.

It is not an implementation plan.

It exists to answer:

- which repeated tasks are good automation candidates
- which surfaces should likely own those automations
- which work should remain human-reviewed
- which work must never be directly automated

## Repeated Operator Tasks

The stack already repeats these tasks often enough to justify command planning:

- validation after docs, receipt, and governance updates
- release prep followed by governed deploy authority
- release proof followed by Discord update drafting or publication
- feedback board sync, board exports, and card closeout review
- local QA/LLEL proof and receipt packaging
- stale surface inventory and dependency checks
- marker table updates after durable lane progress
- doctrine routing from repeated receipts and patterns
- env or secret-path classification before cleanup
- data-hygiene inventory, export, and approval packet preparation

## Candidate `_stack` Commands

`_stack` is the strongest home for commands that coordinate governed execution across repos or enforce shared release policy.

Best candidates:

- `stack validate`
  - run root validation and summarize delta against the last receipt
- `stack release prep <repo>`
  - verify repo-local release prerequisites and package proof pointers
- `stack deploy <repo>`
  - remain the canonical deploy authority wrapper
- `stack update draft <repo>`
  - open or refresh update-draft packaging only after proof exists
- `stack receipt package <lane>`
  - build a consistent receipt skeleton for cross-repo lanes
- `stack marker checkpoint`
  - render the current marker table from durable docs state
- `stack stale-surface audit`
  - inventory duplicate deploy surfaces before deletion approval
- `stack vercel-health`
  - summarize canonical projects, churn, stale surfaces, and provenance drift for the current stack

`_stack` should not become the default home for product-specific runtime logic.

## Candidate Playbook Commands

Playbook is the likely home for doctrine-facing commands that extract reusable operator rules from receipts.

Best candidates:

- `playbook pattern route`
  - classify a new repeated pattern as doctrine, ATLAS-only note, automation candidate, or parked evidence
- `playbook doctrine draft`
  - create a doctrine-ready draft from receipt-backed patterns
- `playbook closeout review`
  - enforce receipt, proof, and owner-boundary checks before a lane is called durable
- `playbook workflow audit`
  - compare a workflow recipe against current practice and note drift

Playbook should remain governance-facing, not runtime-facing.

## Candidate Discord / Fawxzzy Bot Commands

Discord-side commands are best when they improve bounded workflow state without making Discord the hidden engineering source of truth.

Best candidates:

- feedback panel refresh/setup commands
- feedback card creation and bounded edit launchers
- review-state or completion-state promotion helpers
- update-draft helpers that only publish after proof exists
- Music Sesh setup or room-surface refresh commands
- operator-facing thread-pointer or board-split helpers

Good future candidates after DiscordOS separation:

- moderation queue or purgatory workflow helpers
- publication checklist helpers
- release-proof consume-and-draft helpers through explicit contracts

Discord commands should not become a backdoor for deploys, data cleanup, or silent cross-system mutations.

## What Should Remain Human-Reviewed

These surfaces still need a human in the loop even if command scaffolding exists:

- final deploy go/no-go judgment
- final public update wording and timing
- stale surface deletion confirmation
- Supabase cleanup classification and approval
- DiscordOS cutover timing
- doctrine admission
- card acceptance-criteria quality for ambiguous feature work
- brand/preview visual confirmation when manual judgment matters

## What Requires Approval Gates

The following automation classes may assist preparation, but the action itself should stay approval-gated:

- DiscordOS repo bootstrap
- Fitness Supabase mutation
- remote preview/unfurl verification lane opening
- stale Vercel surface deletion
- secret moves, rotation, or deletion
- runtime/Vercel cutover
- schema cutover or live data migration

Commands may prepare artifacts, but they should not silently cross these gates.

## What Must Never Automate Directly

These actions should not be turned into one-step unattended automation:

- deploying by bypassing `_stack`
- posting a Discord update before proof exists
- deleting live or possibly-live infrastructure on stale appearance alone
- mutating Supabase user/profile state without scoped export and rollback posture
- printing or committing secrets
- using `tmp` as a fallback source of truth
- rewriting owner boundaries by convenience

## Relationship To AI Repetition-to-Automation Pipeline

This chapter is the planning spine for that lane.

It turns repeated human work into candidate automation classes, but it also records the boundary between:

- safe preparation automation
- governed execution automation
- permanently human-reviewed decisions

Progress in this chapter should raise automation quality, not automation aggressiveness.

## Relationship To AI Long-Run Batch Orchestration

Long-run orchestration is a later layer on top of these command candidates.

The correct order is:

1. classify repeated work
2. define owner surface
3. define proof and approval boundary
4. implement bounded commands
5. only then consider long-run or chained orchestration

Without that order, batch orchestration becomes hidden policy mutation.

## First Safe Automation Candidates

These are the best first candidates because they prepare or summarize state without crossing risky mutation boundaries:

- root validation summary command
- marker checkpoint render command
- receipt skeleton generator
- stale-surface audit inventory command
- Vercel health and churn summary command
- doctrine routing template generator
- release-proof to update-draft packaging helper
- QA/LLEL proof packet generator
- branch/worktree normalization inventory helper

## Candidate Ownership Matrix

| Candidate class | Best owner | Why |
| --- | --- | --- |
| validation and receipt packaging | `_stack` | shared governed execution surface |
| release proof to update draft | `_stack` plus Discord contract | respects no-post-before-proof rule |
| doctrine routing and pattern extraction | Playbook | governance and reusable operator knowledge |
| Discord feedback/panel helpers | DiscordOS later, Fitness-hosted now | runtime workflow surface |
| Music Sesh setup helpers | DiscordOS later, Fitness-hosted now | runtime workflow surface |
| data-hygiene export and approval prep | owner repo plus ATLAS docs | high-risk prep needs owner context |
| Vercel health classification | Lifeline later, `_stack` first | operational health should become a first-class governed signal |

## Non-Goals

- no command implementation
- no bot expansion in this chapter
- no new deploy path
- no approval-gate bypass
- no runtime ownership change
