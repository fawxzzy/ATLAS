# Discord OS Feedback Workflow Canonical Contracts Pass 1

- Date: `2026-05-27`
- Lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `docs-only workflow contract freeze`
- Marker posture: `Discord OS Feedback Workflow Canonicalization: 68%`
- Source surfaces:
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
  - `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
  - `repos/DiscordOS/docs/contracts/feedback-runtime.md`

## Objective

Freeze the first canonical contracts for the Discord feedback workflow without widening into runtime mutation, schema mutation, migration execution, or deploy claims.

This pass does not:

- mutate Discord runtime behavior
- mutate Supabase rows or schema
- mutate Vercel
- move workflow ownership to DiscordOS
- widen into moderation, Music Sesh, or generic command expansion

## Current Truth Used

The live workflow truth remains:

- Fitness-hosted
- bounded-row first, thread second
- Discord forum is the visible board
- reviewed export is the planning bridge
- completion review is a post-completion gate
- public updates are downstream of shipped proof and curated release intent

Current evidence is strong enough to freeze workflow contracts, but not to claim runtime cutover or new live behavior.

## Preserve / Adapt / Strip Model

### Preserve

- Discord is the visible workflow surface, not engineering truth by itself
- Supabase bounded rows are the workflow source index
- bounded row first, thread second
- export -> reviewed packet/prompt -> approved implementation
- audit comments stay in-thread
- completion review stays required for public shipped-card closure
- no public update post before proof
- no direct Discord-to-repo or Discord-to-ATLAS mutation

### Adapt Carefully

- story-card structure clarity
- parent/child or dependency relationships only where they improve workflow clarity
- a more explicit lifecycle state machine
- Definition of Ready and Definition of Done language
- stronger acceptance-criteria patterns
- release-target or assignee metadata only where they remain bounded and useful

### Strip / Do Not Import

- enterprise Jira bloat fields
- SAFe / PI / WSJF / business-value bureaucracy
- mandatory subtask theater
- auto-announcement on status change
- automatic release-note generation from raw card state
- flattening the workflow into generic ticket logic

## Contract 1: Canonical Formatter Contract

### Purpose

Define the one canonical visible card shape for the Discord feedback workflow so forum threads, exports, review, and later migration work all refer to the same workflow object.

### Inputs

- bounded `discord_feedback_reports` row
- report type
- report status
- completion-review state
- forum linkage
- optional explicit section overrides
- optional evidence links and bounded attachment metadata

### Required Fields / Invariants

- title stays text-only and searchable
- visible type label must be `Bug` or `Feature`
- forum card remains type-aware even when bounded storage is shared
- `Fix` is not a valid new submission type
- visible metadata must preserve:
  - `Type`
  - `Status`
  - `Points`
  - `Area`
  - `Reporter`
  - `Report ID`
  - `Duplicate signals`
- bug cards must preserve:
  - `Problem`
  - `Expected behavior`
  - `Actual behavior`
  - `Steps to reproduce`
  - `Acceptance Criteria`
  - `Evidence`
- feature cards must preserve:
  - `User Story`
  - `Description`
  - `Acceptance Criteria`
  - `Evidence`
- feature cards must not show bug-only sections
- feature cards must not show severity
- points stay Fibonacci-only
- `Backlog` remains a planning tag, not the canonical stored status
- custom emoji remain optional decoration only and must fail soft
- thread titles must not depend on custom emoji

### Allowed Outputs

- canonical starter post body
- canonical thread title
- canonical tag set
- canonical export-ready section ordering
- canonical short-id visibility

### Forbidden Shortcuts

- do not let Discord prose drift independently from bounded structured fields
- do not treat the forum post as the canonical source if it disagrees with the bounded row
- do not inject Jira-style field sprawl into the card body
- do not use the public release-post format inside the feedback thread

### Proof Expectations

- forum starter posts, sync scripts, board exports, and reviewed packets should all be able to render the same sections from the same bounded source
- any formatter change should be provable on public cards, private canaries, and export outputs before being called canonical

### Open Gaps

- one single formatter spec did not exist before this pass
- relationship fields such as blocked-by or related are not yet formally included
- explicit Definition of Ready and Definition of Done markers are still contract-adjacent, not formatter-owned

## Contract 2: Lifecycle / State-Transition Contract

### Purpose

Define the canonical workflow state machine for a feedback card without collapsing review overlays, planning overlays, and release signals into one noisy status field.

### Inputs

- current stored status
- optional completion-review state
- public/private board classification
- status actor and status note
- shipped-proof context when relevant

### Required Fields / Invariants

- canonical stored statuses remain:
  - `new`
  - `needs_info`
  - `confirmed`
  - `fawxzzy_review`
  - `in_progress`
  - `fixed`
  - `closed`
  - `duplicate`
  - `spam`
  - `withdrawn`
- completion review remains a separate explicit state, not an implied side effect
- `Backlog` remains an overlay/planning tag, not a stored status
- feature cards may display `Resolved` where bounded status is stored as `fixed`
- public phase closure is not complete until the configured success reaction is present on the starter post
- public Fitness app cards marked `Fixed` or `Resolved` must enter completion review before final closure is trusted

### Allowed Transitions / Outputs

- `new` -> `needs_info` | `confirmed` | `duplicate` | `spam` | `withdrawn`
- `needs_info` -> `confirmed` | `duplicate` | `spam` | `withdrawn`
- `confirmed` -> `fawxzzy_review` | `in_progress` | `duplicate` | `withdrawn`
- `fawxzzy_review` -> `confirmed` | `in_progress` | `duplicate` | `withdrawn`
- `in_progress` -> `needs_info` | `fixed` | `duplicate` | `withdrawn`
- `fixed` -> completion review `pending` | `needs_followup` | `approved`
- completion review `approved` -> visible success-reaction closure and optional `closed` hygiene
- `closed` may reopen only through an explicit audited regression or follow-up path

### Forbidden Shortcuts

- do not treat `fixed` alone as final public closure
- do not treat `Backlog` as implementation truth or a substitute for review state
- do not move from raw Discord churn to implementation-ready truth without export/review
- do not auto-publish updates from lifecycle transitions

### Proof Expectations

- board tags, exports, review queues, and completion-review surfaces must all agree on lifecycle meaning
- reopened or exceptional paths must leave an audit trail rather than relying on silent status edits

### Open Gaps

- the live docs imply the lifecycle clearly, but no single durable transition table existed before this pass
- Definition of Ready and Definition of Done still need explicit freeze language
- the exact reopened-closed posture should be tightened in a later gate-focused pass

## Contract 3: Audit Comment Contract

### Purpose

Define the canonical in-thread audit surface so feedback cards keep a compact, trustworthy visible history without collapsing into release-post noise.

### Inputs

- report identity
- audit action
- actor label
- optional before/after status
- optional completion-review state
- optional short note
- optional duplicate count
- whether reporter mention is explicitly required

### Required Fields / Invariants

- audit comments remain compact and operational
- audit comments stay inside the feedback thread
- audit comments never replace public release posts
- reporter mention is opt-in only for actions that explicitly require it
- no `@everyone`, `@here`, or broad-role mention
- no raw payloads
- no secrets
- stable action classes include at minimum:
  - `status_update`
  - `completion_review`
  - `withdraw`
  - `reporter_update`
  - `staff_update`
  - `duplicate_signal`
  - `sync_format`

### Allowed Outputs

- compact status-change comment
- compact withdraw comment
- compact duplicate-fold comment
- compact sync/repair comment
- compact completion-review comment

### Forbidden Shortcuts

- do not paste raw structured row data into the thread
- do not use the `Update:` release-post promotion format inside thread history
- do not turn thread history into a changelog for every internal implementation detail
- do not allow audit comments to become the public updates channel by accident

### Proof Expectations

- every post-creation mutation should leave a compact visible audit trace in-thread
- status changes, withdraws, sync repairs, and completion-review outcomes must be reconstructable from thread history plus bounded row state

### Open Gaps

- the live workflow already uses audit comments, but the exact template family is still distributed across code/docs
- the minimal canonical wording patterns for each action class should be tightened in a later template-focused pass

## Contract 4: Completion-Review Contract

### Purpose

Define the canonical post-completion gate for public Fitness feedback cards so public closure reflects reviewed outcome rather than implementation optimism.

### Inputs

- report identity
- public/private board class
- stored status
- completion-review candidate state
- shipped work or resolved candidate
- reviewer identity
- review note
- starter-post reaction state

### Required Fields / Invariants

- completion review is required for public non-testing Fitness app cards marked `Fixed` or `Resolved`
- completion review remains separate from raw status update
- canonical review states remain:
  - `pending`
  - `approved`
  - `needs_followup`
  - `not_required`
- public phase closure is not complete until the success reaction is visibly present on the starter post
- approval may backfill the configured success reaction if it is missing
- private canaries do not become public proof by default

### Allowed Transitions / Outputs

- `fixed` public card -> completion review `pending`
- `pending` -> `approved`
- `pending` -> `needs_followup`
- `needs_followup` -> `pending` after additional shipped work or clarified proof
- `approved` -> success-reaction hygiene and closure-ready state
- `not_required` applies only where the workflow explicitly remains outside the public shipped-card lane

### Forbidden Shortcuts

- do not treat implementation completion as review completion
- do not close a public phase card without the visible success reaction
- do not bypass completion review because a thread “looks done”
- do not let private testing or internal canaries satisfy public completion proof by implication

### Proof Expectations

- public shipped-card closure should be reconstructable from:
  - bounded row state
  - completion-review state
  - visible starter-post success reaction
  - thread audit trace

### Open Gaps

- Definition of Done wording should be frozen explicitly in a later gate package
- the minimal review checklist is still implied more strongly than it is enumerated

## Contract 5: Release-Post Boundary Contract

### Purpose

Define the canonical boundary between thread audit history and public `#updates` release narration so the community board and release history remain separate, trustworthy surfaces.

### Inputs

- shipped proof
- release/deploy evidence
- update draft or approved card-promotion copy
- whether the shipped item is one card or a broader release summary
- report id when a specific feedback card is promoted

### Required Fields / Invariants

- no public update post before proof
- feedback card mutations do not auto-post to `#updates`
- public updates remain curated and user-facing
- deployment metadata is input, not release copy
- one shipped item gets one appropriate public format
- shipped-card promotion uses the short `Update:` style plus `Report ID`
- broad release summaries remain separate and curated
- thread audit comments and public release posts remain distinct artifacts with different purposes

### Allowed Outputs

- compact in-thread audit comment only
- card-promotion `#updates` post for one shipped feedback card
- broader release-summary `#updates` post for aggregate shipped work

### Forbidden Shortcuts

- do not post every status change to `#updates`
- do not publish both the card-promotion format and a broad release-summary for the same single shipped item by default
- do not let raw deploy metadata become public user copy
- do not let Discord card state become the release ledger

### Proof Expectations

- every public update should be traceable back to shipped proof and curated intent
- every card-promotion post should be traceable back to one known report id
- release history and thread history should remain distinguishable in audits and operator review

### Open Gaps

- the workflow is already strong here, but the release boundary still depends on multiple docs instead of one canonical contract
- explicit operator guidance for choosing card-promotion versus broad release-summary can be tightened further later

## Current Strengths Preserved By These Contracts

- clear source-of-truth hierarchy
- bounded row first, thread second
- visible audit trail without release-channel spam
- reviewed export bridge before implementation
- completion review as a real closure gate
- proof-gated public release narration

## Formalized Gaps Still Remaining

- one dedicated workflow-specific separation boundary package
- explicit Definition of Ready freeze
- explicit Definition of Done freeze
- tighter canonical wording/examples for each audit-comment class
- live-proof criteria for any future DiscordOS runtime-owner claim
- no single dedicated Jira extraction packet was found; current Jira-like lessons remain distributed evidence rather than one canonical import source

## Exact Next Package

`Discord OS Feedback Workflow Separation Boundary Decision Pass 1`

Why:

- the workflow contracts are now frozen
- the next bounded move is to freeze Fitness-owned, DiscordOS-owned, and shared seam ownership for this workflow only
- that advances separation-readiness without widening into runtime or schema execution

## Rule

Discord feedback contract work canonicalizes workflow rules without making Discord engineering truth.

## Pattern

Discord card -> bounded row -> board sync -> export -> reviewed packet/prompt -> implementation -> completion review -> curated release update

## Failure Mode

Raw Discord card state becomes direct implementation authority, auto-announcement source, or duplicate engineering truth.
