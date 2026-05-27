# Discord OS Feedback Workflow Canonicalization

Date: 2026-05-27  
Mode: docs-only marker definition and durable current-state receipt  
Status: initial marker admitted

## Final Marker Table Line

- `Discord OS Feedback Workflow Canonicalization: 68%`

## Initial Percent With Justification

`68%` is the smallest honest starting point.

Why it is already well above the conceptual band:

- the live workflow already exists end to end
- the live workflow is governed in production-facing doctrine, not only in aspirational notes
- the strongest operating rules are already visible in Fitness owner docs and ATLAS boundary docs
- the workflow already preserves source-of-truth hierarchy, reviewed-promotion discipline, completion review, audit comments, and proof-gated public updates

Why it is not yet in the high canonicalization band:

- current truth is split across Fitness owner docs, ATLAS boundary docs, DiscordOS separation docs, and Playbook notes
- one canonical formatter contract does not yet exist as a single durable surface
- one canonical lifecycle and state-transition contract does not yet exist as a single durable surface
- one canonical audit comment contract does not yet exist as a single durable surface
- one canonical completion-review contract does not yet exist as a single durable surface
- one canonical release-post boundary contract does not yet exist as a single durable surface
- separation-readiness is partially documented, but not yet frozen as a workflow-specific migration-safe contract set
- no deploy-backed live-proof package yet exists for any future DiscordOS runtime ownership claim in this workflow

## Marker Definition

### Purpose

`Discord OS Feedback Workflow Canonicalization` tracks the extraction, hardening, documentation, and separation-readiness of the Discord feedback workflow as a governed workflow system.

This marker exists to preserve what is already strong in the live workflow while formalizing the missing contracts, lifecycle rules, review gates, and migration boundaries required to treat it as a standalone Discord workflow operating surface rather than only a Fitness-hosted bot feature.

### Scope

This marker includes only the Discord feedback workflow end to end:

1. intake and launcher surfaces
   - `feedback-submission`
   - launcher creation and refresh
   - submit, edit, withdraw, and repair flows
2. bounded workflow state
   - `public.discord_feedback_reports`
   - type, severity, status, area, points, evidence, and forum linkage
   - completion-review fields and success-reaction hygiene
3. visible board behavior
   - thread creation and sync
   - card structure and canonical formatting
   - tag, status, and title conventions
   - audit comment behavior
   - duplicate fold, withdraw, and status mutation visibility
4. review and closure gates
   - reviewed export boundary
   - completion review boundary
   - Definition of Ready and Definition of Done candidates
   - success-reaction closure rule
   - no-post-before-proof rule
5. planning bridge
   - board export
   - reviewed task packet and prompt generation
   - no direct Discord-to-repo or Discord-to-ATLAS mutation
6. public release communication boundary
   - thread audit comments versus `#updates`
   - card-promotion format
   - proof-gated release narration
7. separation readiness
   - DiscordOS-owned versus Fitness-owned concerns
   - shared contract seams
   - migration-safe sequencing
   - no-regression expectations

### Non-Goals

This marker does not absorb:

- moderation or purgatory
- Music Sesh or Spotify Club
- generic Discord command expansion
- unrelated Fitness product work
- unrelated verification work unless directly required by feedback ownership boundaries
- unrelated Vercel or Lifeline work
- generic ATLAS doctrine work not directly tied to this workflow
- any claim that DiscordOS already owns the live runtime

### Dependencies

Primary dependencies:

- `Discord OS Infrastructure Separation`
- `Unified Workflow Convergence`
- Fitness owner docs for live workflow truth
- release/deploy/update proof lanes for public-post proof requirements
- source-truth and env hygiene lanes where they touch ownership or proof seams

### Preserve / Adapt / Strip Model

#### Preserve

- clear source-of-truth hierarchy
- completion review gate
- proof-before-announcement discipline
- audit comment trail
- export-based planning bridge
- bounded row first, thread second
- no direct Discord-to-repo writes
- no direct Discord-to-ATLAS writes from raw workflow state

#### Adapt Carefully

- story-structure improvements
- parent/child or epic grouping only where it adds real workflow clarity
- relationship fields such as `blocked-by`, `related`, or dependency references
- a more explicit lifecycle state machine
- Definition of Ready
- Definition of Done
- more testable acceptance-criteria patterns
- assignee or release-target metadata only where it improves the governed workflow

#### Strip / Do Not Import

- enterprise Jira bloat fields
- SAFe, PI, WSJF, or business-value bureaucracy
- mandatory subtask theater
- automatic release-note generation from raw completion state
- auto-announcement on status change
- flattening everything into generic ticket logic
- any import that weakens the current reviewed-promotion and source-of-truth boundaries

### Completion Standard

This marker reaches `100%` only when all of the following are true:

1. current workflow truth is durably documented
   - actors
   - entrypoints
   - data model
   - lifecycle states
   - audit behavior
   - review gates
   - release boundary
   - current defects and residue
2. canonical contracts are defined
   - one canonical formatter contract
   - one canonical lifecycle/state-transition contract
   - one canonical audit comment contract
   - one canonical completion-review contract
   - one canonical release-post boundary contract
3. Jira-derived improvements are translated selectively
   - without breaking current workflow doctrine
   - without importing enterprise noise
   - without collapsing Discord into engineering truth
4. separation readiness is explicit
   - DiscordOS-owned surfaces identified
   - Fitness-owned surfaces identified
   - shared contract seams identified
   - migration sequencing documented
   - no-regression expectations documented
5. durable ATLAS receipts exist
   - marker table updated
   - definition receipt landed
   - current-state assessment landed
   - milestone ladder landed
   - dependency and adjacency map landed

## Current-State Assessment

### What Already Exists

- the live workflow is currently Fitness-hosted and documented as such
- the dedicated user intake entry already exists through the launcher panel in `feedback-submission`
- bounded row creation in `public.discord_feedback_reports` is already upstream of forum thread creation
- the forum board is already explicitly documented as the visible board while Supabase remains the bounded source index
- every post-creation mutation is already expected to leave a compact thread-visible audit comment
- reviewed export already exists as the planning bridge through `feedback:board:export`
- reviewed task packets and Codex-draft prompts already exist as the approved next step after export
- completion review already exists as a required post-completion queue for public Fitness app cards
- starter-post success reaction hygiene is already explicitly required for visible completed-state closure
- public updates are already downstream of shipped proof and curated release intent, not raw card mutations
- DiscordOS separation planning already exists, including workflow boundary docs, separation inventory, and a feedback runtime scaffold contract

### What Is Strong And Must Be Preserved

- Discord is already treated as the visible board, not engineering truth by itself
- Supabase-bounded rows already act as the workflow source index
- the workflow already enforces bounded row first and thread second
- audit comments already preserve visible card history without collapsing into public release posting
- the board-export to reviewed-packet bridge already prevents raw Discord cards from becoming direct implementation authority
- completion review and success-reaction closure already create a stronger post-ship gate than most lightweight community boards
- the updates channel is already downstream of proof and curated release intent rather than raw status churn
- the workflow already behaves more like a governed operating surface than a casual community bot

### What Is Partially Complete

- lifecycle truth exists, but it is split across Fitness board docs, feedback docs, ATLAS workflow-boundary docs, and DiscordOS future-facing contracts
- completion review doctrine exists, but not yet as one canonical contract surface
- card structure and story-card formatting are strong, but formatter truth is still embedded in owner docs rather than frozen as one canonical contract
- separation-readiness exists in inventory and scaffold form, but not yet as one workflow-specific ownership and no-regression package
- Jira-like strengths have been translated informally into story cards, review packets, and board exports, but not yet ratcheted into one explicit preserve/adapt/strip contract

### What Is Missing

- one canonical formatter contract
- one canonical lifecycle/state-transition contract
- one canonical audit comment contract
- one canonical completion-review contract
- one canonical release-post boundary contract
- one explicit workflow-specific separation seam map for the feedback lane only
- one migration-safe no-regression checklist for future DiscordOS extraction
- one live-proof criteria package for any production ownership or workflow behavior claim
- one durable ATLAS receipt that consolidates the current workflow truth under this marker

### What Is Risky

- live workflow truth is currently distributed across multiple surfaces, which increases drift risk when the workflow evolves
- DiscordOS scaffold docs can be misread as proof of live ownership if canonicalization and live-runtime truth are not kept separate
- the workflow is strong enough that operators may start assuming parts are canonical when they are still only implied across multiple docs
- relationship modeling, lifecycle clarity, and readiness/done criteria could drift into generic ticket logic if they are imported without preserve/adapt/strip discipline
- release/audit separation could be weakened if thread history and public updates are later collapsed into one convenience surface

### What Is Blocked

- no future DiscordOS runtime ownership claim can advance without deploy-backed proof
- workflow canonicalization beyond doctrine is blocked on freezing the contract set as dedicated durable surfaces
- separation-safe progress is blocked on making workflow-specific ownership seams explicit instead of leaving them implied inside broader separation inventory
- the requested Jira-extraction and Discord-feedback-to-Jira mapping source does not currently appear to exist as one dedicated durable receipt; present evidence is distributed across Fitness board docs and Playbook notes rather than one formal extraction packet

### What Is Adjacent But Must Remain Separate

- `Discord OS Infrastructure Separation`:
  - runtime, repo, Supabase, env, and cutover ownership
- `Discord Workflow, Publication & Docs Reliability`:
  - operability, posting stability, fallback path clarity, and documentation-channel reliability
- moderation and purgatory lanes
- Music Sesh and Spotify Club lanes
- generic command-router and command-surface expansion
- broader release/deploy/update proof lanes
- unrelated Fitness product backlog and repo implementation work

## Milestone Ladder

| Checkpoint | Done When | Current Status |
| --- | --- | --- |
| Truth extraction complete | current actors, entrypoints, bounded rows, board behavior, review gates, release boundary, residue, and known risks are recorded from live sources instead of memory | complete in this receipt |
| Marker admission complete | marker line is added to the canonical table and backed by a durable ATLAS receipt with explicit percent logic | complete in this receipt |
| Contract inventory complete | formatter, lifecycle, audit comment, completion-review, and release-post contracts are named, scoped, and source-mapped | complete in this receipt |
| Formatter and lifecycle doctrine complete | one canonical formatter contract and one canonical lifecycle/state-transition contract land as dedicated durable surfaces | not complete |
| Review and closure gates formalized | Definition of Ready, Definition of Done, completion review, success-reaction closure, and no-post-before-proof are frozen as one governed chain | partially complete |
| Planning bridge formalized | export, reviewed packet/prompt generation, and no-direct-write boundaries are frozen as one canonical bridge contract | partially complete |
| Separation boundaries documented | Fitness-owned, DiscordOS-owned, and shared seams are frozen with migration sequencing and no-regression expectations | partially complete |
| Live-proof criteria defined | future production behavior claims and future DiscordOS ownership claims require explicit proof standards and approval posture | not complete |
| Final closeout criteria defined | final closeout says exactly what remains governed-retain, approval-gated, or out of lane and what makes the marker eligible for `100%` | not complete |

## Dependency / Adjacency Map

| Marker or lane | Relationship to this marker | Must remain separate |
| --- | --- | --- |
| `Discord OS Infrastructure Separation` | infrastructure, repo, Supabase, env, and runtime cutover lane that consumes workflow ownership truth from this marker | do not treat workflow canonicalization as proof that runtime migration is done |
| `Unified Workflow Convergence` | broader cross-system boundary map that already contains the high-level Discord workflow chain | do not let this marker absorb unrelated workflow surfaces outside Discord feedback |
| release / deploy / update proof lanes | upstream proof requirement for any public release post and for any future live-runtime claim | this marker does not own deploy execution or proof generation |
| source-truth and env hygiene lanes | relevant where bounded row truth, identity seams, or env ownership affect workflow claims | do not convert this marker into a general secret or env lane |
| `Discord Workflow, Publication & Docs Reliability` | adjacent reliability lane covering posting stability, fallback clarity, and publication reliability | reliability hardening is not the same as canonical contract completion |
| moderation / purgatory | Discord community-ops lane with separate doctrine and reversible-action concerns | not part of this marker |
| Music Sesh / Spotify Club | separate Discord product/runtime lane | not part of this marker |
| generic command expansion | command-surface growth is only relevant when it affects feedback workflow ownership or proof boundaries | do not widen this marker into general bot capability growth |

## Durable Receipt Plan

Canonical ATLAS surfaces for this marker:

- marker table:
  - `docs/atlas-book/02-lanes-and-markers.md`
- durable receipt:
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICALIZATION-2026-05-27.md`
- receipt spine:
  - `docs/atlas-book/05-receipt-index.md`

Recommended supporting future receipts only when the lane actually advances:

- `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICAL-CONTRACTS-PASS-1-2026-05-27.md`
- `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-SEPARATION-BOUNDARY-DECISION-PASS-1-2026-05-27.md`
- `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-LIVE-PROOF-CRITERIA-2026-05-27.md`

The single dedicated receipt is the right initial shape because the current ATLAS structure already supports marker admission through one table update plus one bounded receipt. Additional inventory or decision packages should wait until the lane moves beyond initial canonicalization admission.

## Required Governance Extraction

### Rule

Discord is the visible workflow surface, not engineering truth by itself.

### Pattern

Discord card -> bounded row -> board sync -> export -> reviewed packet/prompt -> implementation -> completion review -> curated release update

### Failure Mode

Raw Discord card state becomes direct implementation authority, auto-announcement source, or duplicate engineering truth.

### Rule

No public update post before proof.

### Failure Mode

Thread audit history and public release history collapse into one noisy, untrustworthy surface.

### Rule

Bounded row first, thread second.

### Failure Mode

A visible thread exists without trustworthy bounded workflow state.

## Follow-Up Lane Recommendations

1. `Discord OS Feedback Workflow Canonical Contracts Pass 1`
   - docs-only
   - freeze one canonical formatter contract, one canonical lifecycle/state-transition contract, one canonical audit comment contract, one canonical completion-review contract, and one canonical release-post boundary contract
2. `Discord OS Feedback Workflow Separation Boundary Decision Pass 1`
   - docs-only
   - freeze Fitness-owned, DiscordOS-owned, and shared-seam ownership for this workflow only
3. `Discord OS Feedback Workflow Live-Proof Criteria`
   - docs-only until an approved proof lane opens
   - define what deploy-backed proof is required before any live runtime-owner or public workflow-progress claim can move

## Validation

Expected validation after this package:

- `python .\\ops\\validation\\validate_stack.py`
