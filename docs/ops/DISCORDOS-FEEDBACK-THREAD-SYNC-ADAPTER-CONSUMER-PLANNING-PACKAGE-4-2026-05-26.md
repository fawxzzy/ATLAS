# DiscordOS Feedback Thread-Sync Adapter-Consumer Planning Package 4 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback thread-sync adapter-consumer planning package 4`
- Mode: `docs-only seam planning`
- Control-plane checkpoint: `main@03d7750`

## Scope

Plan exactly one named DiscordOS feedback adapter-consumer seam after:

- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`

Chosen port:

- `FeedbackThreadSyncPort`

In scope:

- one named feedback port surface
- its producer/source surface
- its future consumer surface
- its contract shape and ownership boundary

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- thread-truth ownership transfer
- audit ownership transfer
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
- the seam stays side-effect-bounded and non-activating
- no owner-repo tracked content is changed
- Fitness remains the canonical thread-sync and Discord-write owner for live feedback flows
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@03d7750bb8fed247d50e2e264d695aba2bdceb6e`
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/PREVIEW-UNFURL-AND-DISCORDOS-FOLLOW-ON-QUEUE-REASSESSMENT-2026-05-26.md`
- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`

## Chosen Port

Selected fourth port:

- `FeedbackThreadSyncPort`

Current contract shape:

```ts
interface FeedbackThreadSyncPort {
  syncStarterMessage(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<DiscordOSFeedbackRuntimeState>>;
  syncForumState(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<DiscordOSFeedbackRuntimeState>>;
  syncResolvedReaction(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<null>>;
}
```

## Why This Port Was Chosen

`FeedbackThreadSyncPort` is the right fourth seam because:

- packages 1 through 3 already bounded the read-side identity, store, and broad staff-access inputs
- the next smallest remaining boundary is the thread-sync side-effect family already isolated in `runtime/feedback/forum.ts`
- the current contract already constrains the side-effect surface to three named sync actions rather than a generic Discord writer

Why it stays small enough:

- it covers only thread-sync behavior, not general Discord orchestration
- it does not approve runtime activation or thread ownership transfer
- it does not approve schema landing or dual-read proof
- it keeps audit-comment behavior separate rather than absorbing all feedback side effects into one port

Why it is not a runtime-owner seam:

- current live thread-sync behavior still depends on Fitness-owned row truth, Discord configuration, and route orchestration
- the future port only defines a bounded sync surface, not a transfer of the current Discord responder or worker target
- the canonical record of forum state still remains Fitness-owned in this package

## Producer / Source Surface

Current Fitness-owned producer side:

- `syncDiscordFeedbackStarterMessage(...)` in `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- `syncDiscordFeedbackForumThread(...)` in `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- `ensureDiscordResolvedFeedbackReaction(...)` in `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- route-level orchestration call sites in `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- forum-state recording helpers in `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`

Current side-effect categories already represented by the boundary:

- starter-message patching in an existing feedback forum thread
- forum title synchronization
- forum tag synchronization
- forum-state persistence back into the Fitness-owned report row
- resolved-reaction synchronization on the starter message

What stays Fitness-owned:

- live Discord REST call execution
- live forum channel and thread configuration
- current Fitness-owned persistence of:
  - `discord_forum_title`
  - `discord_forum_applied_tag_ids`
  - `reporter_mentioned_at`
- route-level orchestration that decides when sync should run
- current warning and soft-failure logging behavior

## Consumer Surface

First future consumer class for this seam:

- DiscordOS feedback consumers that already have report identity, bounded store access, and broad staff-access decisions and need to request a thread-sync action without directly importing Fitness thread-sync logic

Consumer examples the seam should eventually support:

- lifecycle flows that need to refresh starter-message content after a report change
- lifecycle flows that need to re-derive forum title and tag state from current report lifecycle
- completion or resolution flows that need to sync the resolved reaction on the public starter message

Current rule:

- this packet plans the thread-sync boundary only
- it does not implement a DiscordOS adapter, Discord writer, or runtime consumer

## Contract Boundary

### Method 1: `syncStarterMessage`

Input:

- `reportId: FeedbackCardId`

Success output:

- `DiscordOSFeedbackRuntimeState`

Represented side-effect:

- patch the existing starter message inside the current feedback forum thread using Fitness-owned report truth

Minimum returned state fields:

- `reportId`
- `forumTitle`
- `forumAppliedTagIds`
- `reporterMentionedAt`
- `runtimeWarnings`
- `lastForumSyncAt`

### Method 2: `syncForumState`

Input:

- `reportId: FeedbackCardId`

Success output:

- `DiscordOSFeedbackRuntimeState`

Represented side-effect:

- recompute and apply forum title and tag state, then persist the resulting state back through the current owner

### Method 3: `syncResolvedReaction`

Input:

- `reportId: FeedbackCardId`

Success output:

- `null`

Represented side-effect:

- apply the resolved success reaction to the current starter message when the lifecycle state requires it

### Failure Contract

These methods should use the existing `DiscordOSFeedbackResult<T>` envelope and normalize failures into the current shared error family where relevant:

- `FORUM_SYNC_FAILED`
- `REACTION_SYNC_FAILED`
- `REPORT_NOT_FOUND`
- `UPSTREAM_UNAVAILABLE`
- `INVALID_INPUT`

Important normalization rule:

- Discord REST details, channel configuration details, and owner-specific persistence internals must not become DiscordOS-owned contract truth
- the future adapter should translate current Fitness thread-sync failures into the shared result shape before a DiscordOS consumer sees them

## Composition With Earlier Seams

Planned future composition:

1. `FeedbackLookupPort`
   - resolves the target report identity
2. `FeedbackReportStorePort`
   - provides reference and lifecycle projections needed before side effects
3. `FeedbackPermissionPort`
   - answers whether the caller has broad staff access when the action requires it
4. `FeedbackThreadSyncPort`
   - performs the bounded thread-sync side effect against the current owner surface

Why composition matters:

- thread-sync should never become a standalone owner-truth surface
- lookup and store still define what report is being acted on
- permission still determines whether a caller may reach the sync path in later action flows

## Ownership Boundary

### Fitness keeps

- canonical report-row truth
- live Discord REST execution
- live persistence of forum-derived row state
- live sequencing of update, withdraw, completion-review, and other flows that trigger sync
- all current warning/logging semantics for partial sync failure

### DiscordOS later receives

- a bounded thread-sync request surface
- a normalized runtime-state response shape
- no ownership of the underlying report row
- no ownership of the current live Discord runtime host
- no ownership of audit-comment behavior in this package

Boundary rule:

- `FeedbackThreadSyncPort` is a bounded thread-sync seam, not a transfer of thread or runtime ownership

## Data Flow

Planned future flow:

1. a DiscordOS feedback consumer already knows the target `reportId`
2. the consumer composes lookup/store/permission seams as needed
3. the consumer calls one of:
   - `syncStarterMessage(reportId)`
   - `syncForumState(reportId)`
   - `syncResolvedReaction(reportId)`
4. the Fitness-owned adapter resolves current row truth and performs the requested thread-sync side effect
5. the adapter returns either:
   - normalized `DiscordOSFeedbackRuntimeState`
   - normalized `null` for resolved-reaction success
   - normalized `DiscordOSFeedbackResult` failure

## Explicit Non-Goals

This package does not plan or approve:

- audit-comment posting through this seam
- thread creation or thread deletion ownership transfer
- direct DiscordOS execution of Discord REST writes
- schema landing
- dual-read proof
- worker retarget
- runtime activation

Why audit stays out of this seam:

- current Fitness boundary already keeps audit-comment behavior as a separate helper
- audit uses its own event-shaped contract surface and should stay independently governable
- combining audit with thread-sync here would widen the port from bounded sync behavior into a generic side-effect bus

## Allowed Future Follow-On Packages

Allowed next tiny planning packets after this one:

1. `DiscordOS feedback audit adapter-consumer planning package 5`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Why `FeedbackAuditPort` is the clearest next packet:

- lookup, store, permission, and thread-sync seams are now explicitly bounded
- audit remains the last major separated side-effect seam in the current contract set
- it can be planned independently without reopening runtime activation or thread ownership transfer

## What Remains Blocked

- all DiscordOS runtime/schema/data mutation
- all worker retargeting
- all Vercel cutover work
- all dual-read implementation
- all thread/runtime ownership transfer
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

1. `DiscordOS feedback audit adapter-consumer planning package 5`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the tiny DiscordOS seam-planning chain one port at a time
- keep audit as its own final side-effect planning packet rather than folding it into thread-sync
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
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-CONSUMER-PLANNING-PACKAGE-4-2026-05-26.md`

## Next Package

`DiscordOS feedback audit adapter-consumer planning package 5`

Why:

- `FeedbackLookupPort` now covers identity resolution
- `FeedbackReportStorePort` now covers bounded read-side reference and lifecycle projection
- `FeedbackPermissionPort` now covers the broad staff-access decision seam
- `FeedbackThreadSyncPort` now bounds the thread-sync side-effect surface
- `FeedbackAuditPort` is the clearest remaining contract seam without reopening runtime activation or ownership transfer
