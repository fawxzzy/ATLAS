# DiscordOS Feedback Report-Store Adapter-Consumer Planning Package 2 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback report-store adapter-consumer planning package 2`
- Mode: `docs-only seam planning`
- Control-plane checkpoint: `main@0264005`

## Scope

Plan exactly one named DiscordOS feedback adapter-consumer seam after:

- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`

Chosen port:

- `FeedbackReportStorePort`

In scope:

- one named feedback port surface
- its producer/source surface
- its future consumer/store surface
- its contract shape and ownership boundary

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- row ownership transfer
- worker retarget
- Vercel cutover
- dual-read implementation
- preview/unfurl gate reopening
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is planning only
- the packet stays tied to one named feedback port
- the seam stays read-side only
- no owner-repo tracked content is changed
- Fitness remains the canonical report-row owner
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@0264005ed99899477dfd88e43ad9ddbd47c5b6ab`
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/PREVIEW-UNFURL-AND-DISCORDOS-FOLLOW-ON-QUEUE-REASSESSMENT-2026-05-26.md`
- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`

## Chosen Port

Selected second port:

- `FeedbackReportStorePort`

Current contract shape:

```ts
interface FeedbackReportStorePort {
  getReportReference(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<FitnessReportReference>>;
  getLifecycleState(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<FeedbackLifecycleState>>;
}
```

## Why This Port Was Chosen

`FeedbackReportStorePort` is the right second seam because:

- the readiness gate includes it in the minimum first contract set
- package 1 already isolated report identity lookup into `FeedbackLookupPort`
- the next smallest useful consumer boundary is a read-side projection of the already-owned Fitness row
- the current contract already limits the surface to `FitnessReportReference` and `FeedbackLifecycleState`, which avoids handing DiscordOS the full Fitness row shape

Why it stays small enough:

- it defines two explicit read methods, not a generic row fetch
- it does not approve DiscordOS writes to `discord_feedback_reports`
- it does not require DiscordOS schema landing
- it does not approve row replication, dual-read, or data migration

Why it is not a row-ownership seam:

- `DiscordBugReportRow` in Fitness still contains live host-specific fields such as summary/details content, attachment metadata, audit-related write state, and forum formatting surfaces
- the store port is only a bounded read projection for future DiscordOS consumers
- canonical row truth, Supabase access, and update semantics remain in Fitness

## Producer / Source Surface

Current Fitness-owned producer side:

- canonical report row shape in `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- row coercion and select-column normalization in `coerceBugReportRow(...)`
- report lookup helpers such as `findDiscordBugReportByIdOrPrefix(...)` and the underlying full-id/thread-id/short-id readers
- canonical source rows in Fitness table `discord_feedback_reports`

What stays Fitness-owned:

- the canonical `DiscordBugReportRow`
- all direct Supabase access to `discord_feedback_reports`
- report row update semantics
- content-edit, status-update, completion-review, forum-state, and withdraw mutations
- any future widening or narrowing of the live row shape

## Consumer / Store Surface

First future consumer class for this seam:

- DiscordOS feedback consumers that already know `reportId` and need stable read access to reporter reference data or lifecycle state before later policy or orchestration steps

Consumer examples the seam should eventually support:

- post-lookup manage flows that need reporter and thread linkage context
- status or completion-review targeting flows that need current lifecycle state before presenting or validating a next action
- future permission or thread-sync consumers that should read through a store seam instead of importing Fitness row logic

Current rule:

- this packet plans the consumer/store boundary only
- it does not implement a DiscordOS adapter, database reader, or runtime consumer

## Contract Boundary

### Method 1: `getReportReference`

Input:

- `reportId: FeedbackCardId`

Success output:

- `FitnessReportReference`

Current projected fields:

- `reportId`
- `reporterDiscordUserId`
- `reporterFitnessUserId`
- `reporterMemberNumber`
- `reporterUserKind`
- `forumChannelId`
- `forumThreadId`
- `forumMessageId`

Rule:

- this method exposes identity and thread-linkage reference data only
- it does not expose the full card content row

### Method 2: `getLifecycleState`

Input:

- `reportId: FeedbackCardId`

Success output:

- `FeedbackLifecycleState`

Current projected fields:

- `status`
- `completionReviewStatus`
- `statusUpdatedAt`
- `statusUpdatedByDiscordUserId`
- `statusNote`
- `completionReviewedAt`
- `completionReviewedByDiscordUserId`
- `completionReviewNote`

Rule:

- this method exposes mutable lifecycle state as a read-side projection
- it does not grant DiscordOS write ownership over that state

### Failure Contract

Both methods should use the existing `DiscordOSFeedbackResult<T>` envelope and normalize failures into the current shared error family where relevant:

- `REPORT_NOT_FOUND`
- `UPSTREAM_UNAVAILABLE`
- `INVALID_INPUT`

Important normalization rule:

- raw Fitness storage or query details must not become DiscordOS-owned contract truth
- the future adapter should translate current Fitness lookup and read failures into the shared result shape before a DiscordOS consumer sees them

## Ownership Boundary

### Fitness keeps

- canonical report-row truth
- Supabase row selection logic
- live row update semantics
- content and attachment fields that are still tightly coupled to current Fitness-hosted interactions
- all authoritative write paths for lifecycle, forum-state, and audit behavior

### DiscordOS later receives

- a bounded read-side store seam
- stable reference and lifecycle projections
- no direct row ownership
- no right to treat the returned projections as the canonical writable record

Boundary rule:

- `FeedbackReportStorePort` is a projection seam, not a transfer of report storage ownership

## Data Flow

Planned future flow:

1. a DiscordOS feedback consumer already has a canonical `reportId`
2. the consumer calls one of:
   - `getReportReference(reportId)`
   - `getLifecycleState(reportId)`
3. the Fitness-owned adapter reads from `discord_feedback_reports`
4. the adapter returns either:
   - normalized `FitnessReportReference`
   - normalized `FeedbackLifecycleState`
   - normalized `DiscordOSFeedbackResult` failure
5. the DiscordOS consumer decides whether to continue a later policy or orchestration step

## Explicit Non-Goals

This package does not plan or approve:

- direct DiscordOS access to `discord_feedback_reports`
- returning the full `DiscordBugReportRow` to DiscordOS
- summary/details/attachment-content projection as part of this seam
- lifecycle writes through DiscordOS
- forum-state writes
- audit posting
- schema landing
- row replication or export
- dual-read proof
- worker retarget
- runtime activation

Why summary/details stay out of this seam:

- those content fields are still coupled to the current Fitness-hosted edit and formatting flows
- adding them here would widen the seam toward a row-copy contract instead of a narrow store projection

## Allowed Future Follow-On Packages

Allowed next tiny planning packets after this one:

1. `DiscordOS feedback permission adapter-consumer planning package 3`
2. `DiscordOS feedback thread-sync adapter-consumer planning package` only after the read-side seam order remains stable
3. `Fitness Brand Generator Alignment Package`

Why `FeedbackPermissionPort` is the clearest next packet:

- it stays narrow and policy-facing
- it can compose directly with the already-planned lookup and store seams
- it still avoids runtime activation, schema landing, and side-effecting Discord writes

## What Remains Blocked

- all DiscordOS runtime/schema/data mutation
- all worker retargeting
- all Vercel cutover work
- all dual-read implementation
- all report-row ownership transfer
- preview/unfurl execution and gate reopening
- Playbook stashes
- Lifeline retained worktrees

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback permission adapter-consumer planning package 3`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the tiny DiscordOS seam-planning chain one port at a time
- keep the next port policy-focused rather than widening toward runtime or schema work
- route the Fitness generator-alignment mutation into the Fitness owner lane separately
- keep preview/unfurl closed until both its prerequisite and approval are satisfied

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`

## Next Package

`DiscordOS feedback permission adapter-consumer planning package 3`

Why:

- `FeedbackLookupPort` now covers identity resolution
- `FeedbackReportStorePort` now covers bounded read-side reference and lifecycle projection
- `FeedbackPermissionPort` is the next smallest policy seam that can compose with those read-side ports without widening into runtime ownership transfer
