# Discord OS Feedback Workflow No-Regression Extraction Checklist - 2026-05-27

- Date: `2026-05-27`
- Lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `docs-only extraction-safety checklist`
- Marker posture: `Discord OS Feedback Workflow Canonicalization: 68%`
- Source surfaces:
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICAL-CONTRACTS-PASS-1-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-SEPARATION-BOUNDARY-DECISION-PASS-1-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-LIVE-PROOF-CRITERIA-2026-05-27.md`
  - `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
  - `docs/ops/DISCORD-FEEDBACK-ROLLOUT-ISSUES-NOTE-2026-05-25.md`
  - `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-VERIFICATION.md`
  - `repos/DiscordOS/docs/contracts/feedback-runtime.md`

## Objective

Freeze the first migration-safe no-regression checklist for the bounded Discord feedback workflow after canonical contracts, separation boundary, and live-proof criteria are already durable.

This pass does not:

- approve extraction
- move runtime ownership
- move schema or data ownership
- retarget workers or Vercel hosting
- widen into moderation, Music Sesh, or generic Discord command work
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `b1ac4f5`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Durable Starting Truth

The following are already durable:

- marker definition and current-state assessment
- five canonical workflow contracts:
  - formatter
  - lifecycle/state-transition
  - audit comment
  - completion-review
  - release-post boundary
- first separation boundary decision:
  - Fitness still owns the live runtime
  - DiscordOS future ownership targets are named only as future targets
  - shared seams are explicit
- live-proof criteria:
  - bounded row first, thread second
  - audit comment visibility
  - completion review enforcement
  - success reaction closure rule
  - proof-before-update discipline
  - release boundary integrity
  - no-regression extraction safety

That is enough to define a no-regression checklist.

It is not enough to claim:

- extraction approval
- runtime migration
- schema migration
- owner transfer
- deploy-backed cutover truth

## Checklist Purpose

This checklist exists to stop future extraction-facing work from quietly degrading the live governed workflow while contracts and separation plans are being translated into future DiscordOS-owned surfaces.

This checklist is a proof gate.

It is not:

- a migration plan
- a runtime cutover approval
- a schema landing plan
- a DiscordOS owner-transfer claim

## No-Regression Checklist

### 1. Bounded Row First, Thread Second

What must remain true:

- feedback intake success still depends on bounded row creation first and forum thread synchronization second
- no valid submission path may treat thread-first success as acceptable

What evidence proves it:

- deploy-backed or operator-run proof showing the same submission creates the bounded row before the thread
- stable report id, thread id, and message linkage for the same workflow event
- read-only verification receipts that tie row creation and thread creation to the same successful intake

What regression is unacceptable:

- visible thread creation without trustworthy bounded row state
- any intake path that can succeed visibly in Discord while the bounded row is absent, mismatched, or delayed into ambiguity

Who owns the proof:

- current Fitness live runtime owner
- ATLAS may store the receipt that points to the proof

### 2. Audit Comment Visibility

What must remain true:

- every post-creation mutation still leaves a compact visible audit comment inside the feedback thread
- audit comments stay thread-local and do not become update posts

What evidence proves it:

- read-only thread history or receipts showing status update, withdraw, duplicate fold, sync repair, and completion-review traces
- proof that audit comments remain compact and action-specific

What regression is unacceptable:

- silent mutations
- mutation history visible only in storage and not in-thread
- audit comments that become noisy release narration or broad announcement copy

Who owns the proof:

- current Fitness live runtime owner
- future DiscordOS runtime owner only after a separately approved cutover lane exists

### 3. Completion Review Enforcement

What must remain true:

- public non-testing Fitness app cards marked `Fixed` or `Resolved` still enter Completion Review
- completion review remains a real gate, not implied prose

What evidence proves it:

- bounded review state and queue evidence showing `pending`, `approved`, and `needs_followup`
- operator-visible or read-only verification output showing public cards do not bypass the gate

What regression is unacceptable:

- public shipped cards bypass Completion Review
- completion review existing only as documentation while live workflow state no longer proves it
- private canaries being treated as public-proof substitutes by implication

Who owns the proof:

- current Fitness live runtime owner
- review operators for disposition evidence

### 4. Success Reaction Closure Rule

What must remain true:

- public completed cards still require the configured success reaction on the starter post before closure is trusted
- the reaction remains closure hygiene, not a substitute for status or completion review

What evidence proves it:

- starter-post reaction state on public completed cards
- read-only sync or operator receipts showing missing reactions are backfilled correctly

What regression is unacceptable:

- completed public cards missing the required starter-post reaction
- success reaction drifting to audit comments or unrelated messages
- reaction state being used to mask missing completion review evidence

Who owns the proof:

- current Fitness live runtime owner
- operator verification surfaces that inspect thread/message state

### 5. Proof-Before-Update Discipline

What must remain true:

- no public `#updates` post is treated as valid without shipped proof upstream
- feedback card mutations remain thread-local and do not auto-post publicly

What evidence proves it:

- deploy-backed or shipped-proof evidence tied to the update draft or published update
- receipts showing update publication remains downstream of proof and curated release intent

What regression is unacceptable:

- public update posts before proof exists
- feedback-card mutations auto-posting to `#updates`
- raw card-state transitions being treated as release truth

Who owns the proof:

- Fitness deploy/update owner for the current live lane
- ATLAS for durable gate receipts only

### 6. Release Boundary Integrity

What must remain true:

- thread audit comments and `#updates` posts remain distinct artifacts with different purposes
- one shipped feedback card maps to one appropriate public post format rather than duplicated public narratives

What evidence proves it:

- thread audit history that stays operational and compact
- public `#updates` posts that remain curated and traceable to shipped proof
- report-id-bearing shipped-card promotion posts when the lane calls for them

What regression is unacceptable:

- collapse of thread history and public release history into one surface
- duplicate public formats for the same shipped card by default
- raw deploy metadata or thread history leaking into user-facing release narration

Who owns the proof:

- Fitness update owner for the current live publication lane
- future DiscordOS publication owner only after separate proof and approval

### 7. No Direct Discord-To-Engineering Truth Collapse

What must remain true:

- Discord board state remains operational signal, not engineering truth by itself
- raw forum cards still require export and review before implementation work is trusted

What evidence proves it:

- continued use of reviewed export artifacts and reviewed task/prompt generation as the planning bridge
- receipts and workflow docs showing implementation starts from reviewed artifacts rather than raw thread state

What regression is unacceptable:

- raw Discord card state becoming direct repo-work authority
- direct Discord-to-ATLAS or Discord-to-repo mutation becoming normal workflow behavior
- skipped review bridge because the board "already looks structured enough"

Who owns the proof:

- Fitness workflow owner for the live export bridge
- ATLAS for durable reviewed-promotion receipts

### 8. No Duplicate Workflow Truth

What must remain true:

- Supabase bounded rows remain the workflow source index
- Discord remains the visible board
- ATLAS receives reviewed summaries and receipts, not raw duplicate task truth

What evidence proves it:

- workflow docs and receipts still reflect:
  - bounded row truth
  - thread-visible board behavior
  - reviewed export bridge
  - no direct Discord-to-ATLAS or Discord-to-GitHub writes

What regression is unacceptable:

- duplicate task truth across Discord, ATLAS, and repo task systems
- ATLAS storing raw workflow state instead of reviewed summaries
- board export losing its role as the governed planning bridge

Who owns the proof:

- Fitness workflow owner for the live source/index model
- ATLAS for internal durable-summary posture

## Shared Seam Safety Checks

Any extraction-facing package must also prove that these shared seams do not drift:

- report id continuity
- thread id and message id continuity
- lifecycle/status meaning
- audit event meaning
- completion-review meaning
- release-proof dependency

Unacceptable seam regression:

- same workflow object gaining different meaning depending on whether Fitness or DiscordOS currently handles it

Proof owner:

- current Fitness runtime owner before cutover
- future DiscordOS owner only after an explicitly approved execution lane opens

## Explicitly Blocked Classes

Still blocked after this checklist:

- runtime migration
- schema migration
- worker retarget
- Vercel cutover
- live owner transfer claims

This checklist must be consumed as a prerequisite proof gate before any of those classes are reopened.

## Marker Interpretation

This pass strengthens migration-safe clarity for `Discord OS Feedback Workflow Canonicalization`, but it does not justify a marker move by itself.

Why:

- the checklist narrows acceptable future behavior
- no live proof landed here
- no runtime ownership changed here
- no deploy-backed extraction evidence landed here

## Exact Next Package

`Discord OS Feedback Workflow marker ratchet checkpoint 2`

Why:

- the lane now has a durable marker definition, five canonical contracts, a first separation boundary, live-proof criteria, and a no-regression extraction checklist
- the next honest move is to recompute whether that added durable governance should move the marker by a small amount without implying runtime migration or owner transfer

## Rule

No-regression extraction work must define safety gates without implying extraction is already approved.

## Pattern

workflow truth -> canonical contracts -> separation boundary -> live-proof criteria -> no-regression checklist -> only then higher-level extraction decisions

## Failure Mode

A checklist becomes an implicit migration greenlight instead of a bounded proof gate.
