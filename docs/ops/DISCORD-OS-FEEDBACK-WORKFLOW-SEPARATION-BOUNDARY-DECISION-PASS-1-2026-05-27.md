# Discord OS Feedback Workflow Separation Boundary Decision Pass 1

- Date: `2026-05-27`
- Lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `docs-only separation boundary decision`
- Marker posture: `Discord OS Feedback Workflow Canonicalization: 68%`
- Source surfaces:
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-CANONICAL-CONTRACTS-PASS-1-2026-05-27.md`
  - `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
  - `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
  - `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
  - `docs/ops/DISCORD-FEEDBACK-ROLLOUT-ISSUES-NOTE-2026-05-25.md`
  - `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
  - `repos/DiscordOS/docs/contracts/feedback-runtime.md`

## Objective

Freeze the first explicit separation boundary for the Discord feedback workflow after canonical contracts pass 1 without widening into migration, runtime mutation, schema mutation, or owner-transfer claims.

This pass does not:

- move runtime ownership to DiscordOS
- move `discord_feedback_reports`
- change the live Discord responder
- change the live worker target
- change Vercel hosting
- change Supabase schema or data
- widen into moderation, Music Sesh, or generic Discord command expansion

## Root State

- branch: `main`
- HEAD: `4779fbc`
- status: clean except intentional untracked `archive/`
- validation: green before boundary drafting at `critical=0 error=0 warning=310`

## Durable Starting Truth

The following are already durable:

- the marker is admitted and scoped to the Discord feedback workflow only
- the current live workflow truth is documented as Fitness-hosted
- five canonical workflow contracts are now frozen:
  - formatter
  - lifecycle/state-transition
  - audit comment
  - completion-review
  - release-post boundary
- DiscordOS separation inventory and scaffold seams already exist
- the earlier extraction-readiness gate already concluded that contract/interface scaffolding is the safe ceiling, not runtime copy or cutover

## Separation Boundary Decision

The first safe ownership split for this workflow is:

1. Fitness-owned live runtime concerns remain Fitness-owned
2. DiscordOS-owned future workflow concerns are named as future owners only
3. shared contract seams are frozen as migration-stable dependencies

This is a boundary decision, not an extraction approval.

## Bucket 1: Still Fitness-Owned Live Runtime Concerns

### What It Owns

- live Discord interaction route entrypoint
- live feedback persistence and canonical writer for `discord_feedback_reports`
- live forum thread and starter-post synchronization
- live audit comment posting
- live launcher setup, submit/edit/withdraw flow handling
- live completion-review execution behavior
- live `#updates` draft/publish runtime behavior
- current reporter identity bridge through Fitness-owned account and link surfaces
- current worker target and current Vercel-hosted runtime path

### What It Must Not Own Yet

- future DiscordOS runtime state after approved cutover
- future DiscordOS-owned feedback runtime orchestration
- future DiscordOS-owned workflow execution once cutover is separately proven

### Proof Required Before Movement

- deploy-backed proof that a replacement runtime can answer the same workflow correctly
- proof that bounded row first and thread second still hold
- proof that report ids, thread ids, message ids, and lifecycle meanings survive unchanged
- proof that completion-review and success-reaction closure remain intact
- proof that public update boundaries remain proof-gated and curated
- rollback/fail-closed posture if the new runtime misbehaves

### Unacceptable Regressions

- visible thread creation without trustworthy bounded row state
- changed report identity semantics
- broken audit-comment history
- degraded completion-review gate
- raw Discord card state becoming implementation truth
- public updates posting before proof

## Bucket 2: Candidate DiscordOS-Owned Future Workflow Concerns

### What It Owns

This bucket names future ownership targets only:

- future feedback runtime orchestration
- future feedback lifecycle handling after approved cutover
- future feedback forum synchronization after approved runtime transfer
- future DiscordOS-owned runtime state for feedback board behavior
- future adapter execution for lookup, thread sync, audit, permission, and report-store seams once separately approved

### What It Must Not Own Yet

- current live interaction route
- current live `discord_feedback_reports` canonical writer
- current live Vercel-hosted responder
- current live completion-review runtime behavior
- current live release/update draft runtime behavior
- current Fitness-owned reporter/account identity authority

### Proof Required Before Movement

- repo-local implementation proof inside DiscordOS beyond scaffold-only status
- explicit schema landing plan exercised for the feedback domain
- read-only or parity proof that DiscordOS-owned shapes match current live workflow behavior
- deploy-backed proof for any live responder or worker retarget
- migration-safe sequencing that keeps current user flows intact during handoff

### Unacceptable Regressions

- DiscordOS claiming live ownership while Fitness is still serving the workflow
- contract drift between DiscordOS seams and Fitness live behavior
- forcing schema or runtime cutover by documentation momentum
- code copy that drags Fitness-owned identity or persistence assumptions in by convenience

## Bucket 3: Shared Contract Seams That Must Stay Stable

### What It Owns

These seams are shared boundaries, not shared runtime ownership:

- feedback card identity
- lifecycle/status meaning
- audit event meaning
- completion-review meaning
- report lookup result codes and ambiguity semantics
- forum thread/message linkage continuity
- reporter identity reference shape
- release-proof to public-update dependency

### What It Must Not Own Yet

- direct runtime authority
- live canonical writer authority
- hidden dual-write behavior
- implicit transport or publish rights

### Proof Required Before Movement

- stable contract versions across both sides of the seam
- explicit mapping for report id, thread id, message id, status, and completion-review fields
- explicit failure codes for missing report, ambiguity, sync failure, and permission failure
- verified no-regression interpretation across exports, board behavior, and public-update boundaries

### Unacceptable Regressions

- one side changing status meaning silently
- one side changing audit event meaning silently
- report id continuity breaking during migration
- completion-review semantics diverging between owners
- release-post boundary collapsing into thread history or vice versa

## Explicit Ownership Map

| Surface | Current owner | Future owner target | Boundary note |
| --- | --- | --- | --- |
| `discord_feedback_reports` canonical write path | Fitness | DiscordOS later | not approved to move yet |
| forum thread/title/tag sync | Fitness | DiscordOS later | behavior may move only after runtime proof |
| audit comment posting | Fitness | DiscordOS later | audit contract must remain stable first |
| completion review execution behavior | Fitness | DiscordOS later | review contract is frozen, runtime is not transferred |
| report/export planning bridge | shared workflow boundary | shared boundary | export remains planning bridge, not direct runtime transfer |
| reporter/account identity bridge | Fitness | Fitness with explicit consumer contract | should not be casually moved |
| release-proof to `#updates` dependency | shared seam with Fitness proof upstream | shared seam | Discord publication cannot outrun Fitness proof |

## Migration-Safe Sequencing Expectations

The workflow-specific safe sequence is:

1. freeze canonical workflow contracts
2. freeze workflow-specific ownership boundary
3. freeze live-proof criteria
4. freeze migration-safe no-regression checklist
5. only then consider any execution-facing extraction package

This sequence intentionally blocks:

- runtime-first extraction
- schema-first migration by momentum
- documentation that implies owner transfer without deploy-backed proof

## What Remains Explicitly Blocked

Still blocked after this pass:

- runtime migration
- schema migration
- separation execution
- worker retarget
- Vercel cutover
- live-owner transfer claims without proof
- any statement that DiscordOS already owns the live feedback workflow

## Marker Interpretation

This pass strengthens separation-readiness for the feedback workflow marker, but it does not justify a marker move by itself.

Why:

- ownership buckets are now clearer
- the live runtime owner is still unchanged
- the blocked classes remain blocked
- this is a boundary clarification pass, not deploy-backed proof

## Exact Next Package

`Discord OS Feedback Workflow Live-Proof Criteria`

Why:

- the current workflow contracts are frozen
- the first ownership boundary is now explicit
- the next smallest honest step is to define what evidence would actually be required before any live-owner claim or execution-facing extraction lane can open

## Rule

Separation boundary work must clarify ownership without pretending the live runtime owner has already changed.

## Pattern

live Fitness workflow truth -> frozen workflow contracts -> frozen ownership boundary -> live-proof criteria -> only then higher-level migration decisions

## Failure Mode

A separation decision quietly implies runtime migration or ownership transfer without deploy-backed proof.
