# DiscordOS Feedback Thread-Sync Adapter Implementation Planning Package 4 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback thread-sync adapter implementation planning package 4`
- Mode: `docs-only implementation planning`
- Control-plane checkpoint: `main@9f3dbae`

## Scope

Plan repo-local adapter implementation for exactly one DiscordOS feedback seam:

- `FeedbackThreadSyncPort`

In scope:

- adapter placement inside `repos/DiscordOS`
- dependency boundary back to Fitness-owned thread-sync execution
- separate handling plan for:
  - starter-message sync
  - forum title/tag/state sync
  - resolved-reaction sync
- normalized failure mapping plan
- composition boundary with lookup, report-store, and permission
- test-shape plan
- stub-to-real adapter evolution plan

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read execution
- lookup/report-store/permission replanning beyond explicit composition notes
- audit planning
- preview/unfurl gate reopening
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is implementation-planning-only
- only one port is in scope
- the seam stays side-effect-bounded and non-activating
- no owner-repo tracked content is changed
- no runtime/schema/data ownership transfer is implied
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@9f3dbaee15156f60911b8f37cc871ea7b3e5a873`
- `docs/ops/DISCORDOS-FEEDBACK-SEAM-CHAIN-IMPLEMENTATION-READINESS-CHECKPOINT-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-LOOKUP-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-CONSUMER-PLANNING-PACKAGE-4-2026-05-26.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/DiscordOS/src/adapters/feedback/README.md`

## Chosen Port

Selected implementation-planning target:

- `FeedbackThreadSyncPort`

Current contract shape:

```ts
interface FeedbackThreadSyncPort {
  syncStarterMessage(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<DiscordOSFeedbackRuntimeState>>;
  syncForumState(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<DiscordOSFeedbackRuntimeState>>;
  syncResolvedReaction(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<null>>;
}
```

## Why This Port Is Still Fourth

`FeedbackThreadSyncPort` remains the fourth allowed implementation-planning target because:

- lookup, report-store, and permission planning already define the read-side and broad-staff prerequisites
- thread-sync is the first side-effect seam that can now be planned against those explicit upstream boundaries
- the existing seam definition already keeps it smaller than a generic Discord write surface
- audit remains separately bounded and should not be absorbed here

## Planned Repo-Local Adapter Placement

The current type-only bundle entry should remain:

- `repos/DiscordOS/src/adapters/feedback/index.ts`

Planned future thread-sync implementation placement:

- `repos/DiscordOS/src/adapters/feedback/thread-sync/index.ts`
- `repos/DiscordOS/src/adapters/feedback/thread-sync/starter-message.ts`
- `repos/DiscordOS/src/adapters/feedback/thread-sync/forum-state.ts`
- `repos/DiscordOS/src/adapters/feedback/thread-sync/resolved-reaction.ts`
- `repos/DiscordOS/src/adapters/feedback/thread-sync/normalize.ts`
- `repos/DiscordOS/src/adapters/feedback/thread-sync/types.ts`

Planned role of each file:

- `thread-sync/index.ts`
  - exposes the contract-facing `FeedbackThreadSyncPort` implementation surface
- `thread-sync/starter-message.ts`
  - holds the starter-message sync dependency shape and result mapping
- `thread-sync/forum-state.ts`
  - holds the forum title/tag/state sync dependency shape and result mapping
- `thread-sync/resolved-reaction.ts`
  - holds the resolved-reaction sync dependency shape and result mapping
- `thread-sync/normalize.ts`
  - holds shared failure/result normalization for thread-sync outcomes
- `thread-sync/types.ts`
  - holds adapter-local dependency shapes without importing Fitness runtime code directly

Why this placement:

- it keeps the three side-effect categories explicit instead of collapsing them into one generic writer
- it preserves `src/adapters/feedback/index.ts` as the bundle-assembly seam
- it keeps audit separate and prevents category bleed

## Dependency Boundary Back To Fitness

Fitness remains the live thread-sync executor and Discord writer.

The planned DiscordOS adapter should depend on injected upstream sync executors rather than direct Discord clients, persistence clients, or copied runtime code.

Planned dependency classes:

- one starter-message sync executor keyed by canonical `reportId`
- one forum-state sync executor keyed by canonical `reportId`
- one resolved-reaction sync executor keyed by canonical `reportId`

Boundary rules:

- no direct Discord REST client inside DiscordOS
- no copied Fitness thread-sync implementation
- no direct persistence of thread-derived state inside DiscordOS
- no direct runtime wiring in this package

## Thread-Sync Category Handling Plan

### `syncStarterMessage`

Planned responsibility:

- request a bounded refresh of the existing starter-message surface for a known `reportId`

Expected success shape:

- normalized `DiscordOSFeedbackRuntimeState`

Explicit exclusions:

- thread creation
- generic message-post ownership
- audit-comment behavior

### `syncForumState`

Planned responsibility:

- request a bounded recomputation of forum title, forum tag state, and persisted runtime state for a known `reportId`

Expected success shape:

- normalized `DiscordOSFeedbackRuntimeState`

Explicit exclusions:

- generic thread moderation
- arbitrary tag editing outside the current feedback state model
- row ownership transfer

### `syncResolvedReaction`

Planned responsibility:

- request a bounded resolved-reaction sync for a known `reportId`

Expected success shape:

- normalized `null`

Explicit exclusions:

- generic reaction management
- broad emoji ownership
- audit-comment behavior

Rule:

- thread-sync must remain limited to the three existing categories and must not widen into generic Discord write ownership

## Normalized Failure Mapping Plan

The future adapter should normalize upstream outcomes into the existing contract error family:

- thread-sync failure on starter-message or forum-state paths -> `FORUM_SYNC_FAILED`
- reaction sync failure -> `REACTION_SYNC_FAILED`
- missing canonical `reportId` or report surface -> `REPORT_NOT_FOUND`
- structurally invalid `reportId` input -> `INVALID_INPUT`
- transport, auth, unavailable upstream, or non-contract-safe upstream failure -> `UPSTREAM_UNAVAILABLE`

Mapping discipline:

- raw Discord REST details and Fitness persistence internals must not become DiscordOS contract truth
- warning text may be preserved only when it is contract-safe and category-bounded

## Composition Boundary With Lookup, Report-Store, And Permission

Lookup remains responsible for canonical report identity resolution.

Report-store remains responsible for bounded reference and lifecycle projections.

Permission remains responsible for broad staff-access evaluation.

Thread-sync remains responsible only for bounded side effects once the earlier seams have already done their work.

Composition rule:

1. `FeedbackLookupPort`
   - resolves canonical `reportId`
2. `FeedbackReportStorePort`
   - provides any needed reference or lifecycle context
3. `FeedbackPermissionPort`
   - answers only the broad staff-access question where required
4. `FeedbackThreadSyncPort`
   - performs one of the three bounded sync actions

Boundary rule:

- `FeedbackThreadSyncPort` must not absorb lookup, row-read, or permission-policy ownership into its own adapter surface

## Test Strategy Shape

This package does not add tests, but it defines the future test shape.

Planned test categories:

1. starter-message sync fixtures
   - upstream success -> `DiscordOSFeedbackRuntimeState`
   - upstream failure -> normalized `FORUM_SYNC_FAILED`
2. forum-state sync fixtures
   - upstream success -> `DiscordOSFeedbackRuntimeState`
   - upstream failure -> normalized `FORUM_SYNC_FAILED`
3. resolved-reaction fixtures
   - upstream success -> `null`
   - upstream failure -> normalized `REACTION_SYNC_FAILED`
4. adapter dependency-injection tests
   - each category consumes only its injected executor
   - adapter does not require Discord, Supabase, or env access
5. category-separation tests
   - starter-message, forum-state, and reaction paths remain explicitly separated

Current tooling constraint:

- DiscordOS still lacks repo-local TypeScript tooling
- any real test implementation requires a separate repo-local tooling or execution lane before adapter execution begins

That tooling dependency does not block planning, but it still blocks implementation execution.

## Stub-To-Real Adapter Evolution Plan

Planned evolution sequence:

1. keep the current bundle and contract surfaces type-only
2. add a thread-sync-only subdirectory under `src/adapters/feedback/thread-sync/`
3. land pure normalization and dependency-shape code first
4. land bridge-facing wiring only in a later execution-approved repo-local lane
5. reassess again before any runtime/schema/data activation

Why this order:

- it keeps side effects category-bounded
- it prevents thread-sync from turning into a generic writer seam
- it preserves the checkpoint rule that implementation-planning readiness is not execution readiness

## What Remains Blocked

- all DiscordOS runtime/schema/data mutation
- all worker retargeting
- all Vercel cutover work
- all dual-read implementation
- all service ownership transfer
- all implementation execution in `repos/DiscordOS`
- preview/unfurl execution and gate reopening
- Playbook stashes
- Lifeline retained worktrees

## Allowed Future Follow-On Package Classes

Allowed next package class:

- `DiscordOS feedback audit adapter implementation planning package 5`

If later execution is considered, a separate execution-readiness lane is still required first.

## Rule / Pattern / Failure Mode

Rule:

- Implementation planning readiness is not implementation execution readiness.

Pattern:

- Seam chain complete -> one-port implementation planning -> later reassess before any execution.

Failure Mode:

- Side-effect-seam implementation-planning inflation into generic Discord write ownership or repo mutation.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback audit adapter implementation planning package 5`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- finish the last separated side-effect seam at the planning layer
- keep all execution and runtime movement closed
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
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-4-2026-05-26.md`

## Next Package

`DiscordOS feedback audit adapter implementation planning package 5`

Why:

- thread-sync implementation planning is now packetized as the fourth one-port adapter planning target
- audit remains the last separately bounded side-effect seam in the current chain
- execution, runtime, schema, and data mutation still remain blocked
