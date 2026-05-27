# Discord OS Feedback Workflow Live-Proof Criteria

- Date: `2026-05-27`
- Lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `docs-only live-proof criteria freeze`
- Marker posture: `Discord OS Feedback Workflow Canonicalization: 68%`
- Source surfaces:
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICAL-CONTRACTS-PASS-1-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-SEPARATION-BOUNDARY-DECISION-PASS-1-2026-05-27.md`
  - `docs/ops/DISCORD-FEEDBACK-ROLLOUT-ISSUES-NOTE-2026-05-25.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-VERIFICATION.md`

## Objective

Freeze the exact live-proof criteria for the bounded Discord feedback workflow without widening into runtime mutation, schema mutation, migration execution, or owner-transfer claims.

This pass does not:

- move runtime ownership to DiscordOS
- move `discord_feedback_reports`
- change the live Discord responder
- change Vercel hosting
- change Supabase schema or data
- widen into moderation, Music Sesh, or generic command expansion

## Root State

- branch: `main`
- HEAD: `3096f6c`
- status: clean except intentional untracked `archive/`
- validation: green before criteria drafting at `critical=0 error=0 warning=310`

## Durable Starting Truth

The following are already durable:

- the marker is admitted and bounded to the Discord feedback workflow only
- the current live workflow truth is documented as Fitness-hosted
- five canonical workflow contracts are frozen:
  - formatter
  - lifecycle/state-transition
  - audit comment
  - completion-review
  - release-post boundary
- the first separation boundary is frozen:
  - Fitness owns the live runtime concerns
  - DiscordOS future ownership targets are named only as future targets
  - shared seams are explicit

That is enough to define proof criteria.

It is not enough to claim:

- workflow hardening is complete
- runtime ownership has moved
- schema movement is approved
- deployment-backed no-regression extraction is already proven

## Proof-Gate Purpose

These criteria define what counts as trustworthy live evidence before any future claim of:

- workflow hardening completion
- live runtime owner movement
- release/update trust
- no-regression extraction safety

The criteria are intentionally stricter than contract existence.

Static doctrine, local notes, and separation plans can explain what should happen. They are not by themselves proof that the live workflow actually behaves that way.

## Proof Class 1: Bounded Row First, Thread Second

### What Evidence Counts

- deploy-backed or operator-run proof showing a newly submitted feedback item creates the bounded `discord_feedback_reports` row first and only then creates or updates the forum thread
- bounded row identifiers, stored status, and forum linkage that match the visible thread created by the same flow
- read-only verification output or receipt-backed script output proving the row and thread linkage came from the same successful interaction path

### What Does Not Count

- a forum thread existing by itself
- a Discord screenshot without bounded row evidence
- local code intent or contract text alone
- chat testimony that the order is "supposed to" be row first

### Who Owns The Evidence

- Fitness live runtime owner
- Fitness bounded data owner
- ATLAS may hold the receipt that points to the proof

### Unacceptable Regression

- visible thread creation without trustworthy bounded row state
- row creation that fails to preserve stable thread/message linkage
- any workflow path that lets thread-first success appear as a valid submission

## Proof Class 2: Audit Comment Visibility

### What Evidence Counts

- proof that post-creation mutations leave compact visible audit comments in the feedback thread
- read-only thread history or bounded audit receipts showing status update, withdraw, duplicate fold, sync repair, or completion-review actions are visibly recorded
- canary or production-safe proof that audit comments stay in-thread and do not become update-channel posts

### What Does Not Count

- bounded status changes without thread-visible history
- a claim that comments "should have posted"
- release-post evidence from `#updates`
- Discord message history that records only the starter post and no mutation trace

### Who Owns The Evidence

- Fitness live runtime owner for current live behavior
- future DiscordOS runtime owner only after separately proven cutover
- ATLAS may hold summarized receipts

### Unacceptable Regression

- silent board mutations
- audit comments that paste raw payloads or act like public release posts
- audit comments that collapse into noisy or non-compact history

## Proof Class 3: Completion Review Enforcement

### What Evidence Counts

- bounded rows and review artifacts showing public non-testing Fitness app cards marked `Fixed` or `Resolved` enter Completion Review rather than skipping directly to trusted closure
- review receipts, queue outputs, or operator-visible command results proving `pending`, `approved`, and `needs_followup` are treated as real gate states
- live or canary evidence that private `feedback-testing` cards are excluded by default where the workflow says they should be

### What Does Not Count

- stored `fixed` status by itself
- one Discord thread appearing "done"
- implementation completion without review evidence
- chat claims that review "would have happened"

### Who Owns The Evidence

- Fitness live runtime owner for current behavior
- owner-approved review operators for disposition evidence
- ATLAS for durable proof receipts only

### Unacceptable Regression

- public shipped cards bypassing completion review
- completion-review states existing only as implied prose instead of evidence-bearing workflow state
- private canaries being used as public proof by implication

## Proof Class 4: Success Reaction Closure Rule

### What Evidence Counts

- visible starter-post reaction state showing the configured success reaction is present on fixed/completed public cards after approved completion review
- read-only sync output or operator receipts showing missing success reactions are backfilled correctly
- proof that the reaction is on the starter post, not just on an audit comment

### What Does Not Count

- a resolved tag alone
- a reaction on the wrong message
- "should be there" assumptions based on status alone
- historical memory that the sync command was run once

### Who Owns The Evidence

- Fitness live runtime owner for current production behavior
- operators running read-only sync or doctor verification surfaces

### Unacceptable Regression

- public completed cards lacking the required visible success reaction
- success reactions drifting to audit comments instead of the starter post
- using the reaction as a substitute for bounded status or completion review rather than as closure hygiene

## Proof Class 5: Proof-Before-Update Discipline

### What Evidence Counts

- deploy-backed or operator-verified proof that shipped work exists before any public `#updates` post is treated as valid
- update-draft surfaces tied to real production deployment or real shipped card completion proof
- receipts showing card mutations remain thread-local while public update posts remain downstream of shipped proof

### What Does Not Count

- a drafted `#updates` post without proof
- raw Discord card state alone
- broad release copy without deployment or shipped-card linkage
- a local branch or local code diff with no deployment-backed evidence

### Who Owns The Evidence

- Fitness deploy/update owner for the live update lane
- Fitness workflow owner for shipped-card promotion evidence
- ATLAS for durable proof-gate receipts

### Unacceptable Regression

- public update posts before proof exists
- feedback-card mutations auto-posting to `#updates`
- treating a card state change as a release ledger by itself

## Proof Class 6: Release Boundary Integrity

### What Evidence Counts

- evidence that thread audit comments and `#updates` posts remain distinct artifacts with different purposes
- shipped-card promotion posts that trace back to one report id and shipped proof
- broader release-summary posts that trace back to production deployment proof without pretending to be card history

### What Does Not Count

- reusing thread-audit copy in `#updates`
- using broad release-summary copy as feedback thread history
- one post trying to serve as mutation log, release ledger, and card history at once

### Who Owns The Evidence

- Fitness update owner for the current live publication lane
- future DiscordOS publication owner only after separate proof

### Unacceptable Regression

- collapse of thread history and public release history into one surface
- duplicate public formats for the same shipped card by default
- raw deploy metadata leaking into public user-facing release narration

## Proof Class 7: No-Regression Extraction Safety

### What Evidence Counts

- side-by-side or canary proof that an extraction-facing implementation preserves:
  - bounded row first, thread second
  - stable report id and thread/message linkage
  - lifecycle meaning
  - audit comment behavior
  - completion-review gate
  - success-reaction closure hygiene
  - proof-before-update discipline
- deploy-backed parity evidence if a live responder or worker target changes
- explicit rollback/fail-closed posture when a future extraction lane is exercised

### What Does Not Count

- scaffold contracts by themselves
- adapter type checks by themselves
- static mapping tables with no live or canary behavior proof
- documentation that says the future system "will preserve behavior"

### Who Owns The Evidence

- current Fitness live runtime owner before any cutover
- future DiscordOS owner only after a separately approved and proven runtime lane opens
- ATLAS for the no-regression receipt, not for the runtime proof itself

### Unacceptable Regression

- changed report identity semantics
- changed thread/message linkage semantics
- changed lifecycle meaning between owners
- completion-review weakening during extraction
- loss of proof-before-update discipline during extraction

## Evidence Hierarchy

Highest-confidence evidence for this lane is:

1. deploy-backed production proof
2. read-only operator verification against live bounded row plus live Discord state
3. bounded canary proof where the workflow explicitly allows private canaries
4. durable receipts that point to the above evidence

Lower-confidence surfaces that can support but not replace live proof:

- static contract docs
- separation plans
- rollout issue notes
- local code shape
- chat continuity

## What Remains Explicitly Blocked

Still blocked after this pass:

- runtime migration
- schema migration
- owner-transfer claims
- deploy-backed claims without proof
- any statement that DiscordOS already owns the live feedback workflow

These criteria are proof gates, not approval by implication.

## Marker Interpretation

This pass strengthens the marker, but it does not justify a marker move by itself.

Why:

- proof criteria reduce ambiguity about what future claims must prove
- no new deploy-backed evidence landed here
- no live runtime behavior changed here
- no owner-transfer claim was proven here

## Exact Next Package

`Discord OS Feedback Workflow No-Regression Extraction Checklist`

Why:

- the workflow contracts are frozen
- the first ownership boundary is frozen
- the live-proof gate is now frozen
- the next smallest honest step is to turn those proof classes into a migration-safe checklist for any future extraction-facing lane without opening execution

## Rule

Live-proof criteria must define trustworthy evidence without implying the live runtime owner has already changed.

## Pattern

live Fitness workflow truth -> canonical contracts -> separation boundary -> live-proof criteria -> no-regression extraction checklist -> only then higher-level migration decisions

## Failure Mode

A proof criterion quietly becomes a migration approval or owner-transfer claim without deploy-backed evidence.
