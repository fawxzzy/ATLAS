# DiscordOS Feedback Report-Store Adapter Implementation Planning Package 2 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback report-store adapter implementation planning package 2`
- Mode: `docs-only implementation planning`
- Control-plane checkpoint: `main@581473e`

## Scope

Plan repo-local adapter implementation for exactly one DiscordOS feedback seam:

- `FeedbackReportStorePort`

In scope:

- adapter placement inside `repos/DiscordOS`
- dependency boundary back to Fitness-owned report-store reads
- projection mapping plan for:
  - `FitnessReportReference`
  - `FeedbackLifecycleState`
- normalized failure mapping plan
- test-shape plan
- stub-to-real adapter evolution plan

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read execution
- lookup replanning beyond explicit composition notes
- permission planning
- thread-sync planning
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
- the seam stays read-side only
- no owner-repo tracked content is changed
- no runtime/schema/data ownership transfer is implied
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@581473efef3371712b7f8d9e1d17f4cd82b56744`
- `docs/ops/DISCORDOS-FEEDBACK-SEAM-CHAIN-IMPLEMENTATION-READINESS-CHECKPOINT-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-LOOKUP-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-CONSUMER-PLANNING-PACKAGE-4-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-AUDIT-ADAPTER-CONSUMER-PLANNING-PACKAGE-5-2026-05-26.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/DiscordOS/src/adapters/feedback/README.md`

## Chosen Port

Selected implementation-planning target:

- `FeedbackReportStorePort`

Current contract shape:

```ts
interface FeedbackReportStorePort {
  getReportReference(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<FitnessReportReference>>;
  getLifecycleState(reportId: FeedbackCardId): Promise<DiscordOSFeedbackResult<FeedbackLifecycleState>>;
}
```

## Why This Port Is Still Second

`FeedbackReportStorePort` remains the second allowed implementation-planning target because:

- the seam-chain readiness checkpoint explicitly cleared one-port repo-local planning after lookup
- `FeedbackLookupPort` planning already isolated report identity resolution and failure normalization
- the next useful seam is a bounded read-side projection of reference and lifecycle state
- this port still avoids permission, thread-sync, and audit side-effect pressure

## Planned Repo-Local Adapter Placement

The current type-only bundle entry should remain:

- `repos/DiscordOS/src/adapters/feedback/index.ts`

Planned future report-store implementation placement:

- `repos/DiscordOS/src/adapters/feedback/report-store/index.ts`
- `repos/DiscordOS/src/adapters/feedback/report-store/reference.ts`
- `repos/DiscordOS/src/adapters/feedback/report-store/lifecycle.ts`
- `repos/DiscordOS/src/adapters/feedback/report-store/normalize.ts`
- `repos/DiscordOS/src/adapters/feedback/report-store/types.ts`

Planned role of each file:

- `report-store/index.ts`
  - exposes the contract-facing `FeedbackReportStorePort` implementation surface
- `report-store/reference.ts`
  - holds reference-projection mapping into `FitnessReportReference`
- `report-store/lifecycle.ts`
  - holds lifecycle-projection mapping into `FeedbackLifecycleState`
- `report-store/normalize.ts`
  - holds shared failure/result normalization for report-store reads
- `report-store/types.ts`
  - holds adapter-local dependency shapes for upstream report-store reads without importing Fitness runtime code directly

Why this placement:

- it keeps report-store isolated from lookup, permission, thread-sync, and audit
- it preserves bundle assembly in `src/adapters/feedback/index.ts`
- it keeps the two read-side projections explicit instead of collapsing them into a generic row-fetch surface

## Dependency Boundary Back To Fitness

Fitness remains the report-store reader and canonical row owner.

The planned DiscordOS adapter should depend on injected upstream read functions rather than direct database or Discord clients.

Planned dependency classes:

- one reference-read dependency keyed by canonical `reportId`
- one lifecycle-read dependency keyed by canonical `reportId`
- both return only the minimum raw projection payload needed for normalization

Boundary rules:

- no direct Supabase client inside DiscordOS
- no copied Fitness row-reader or row-coercion logic
- no DiscordOS-owned row selection or join logic
- no direct runtime wiring in this package

## Projection Mapping Plan

This port stays projection-only.

### `getReportReference`

Expected projection mapping:

- canonical `reportId` -> `FitnessReportReference.reportId`
- reporter Discord identity -> `reporterDiscordUserId`
- optional linked Fitness user id -> `reporterFitnessUserId`
- optional member number -> `reporterMemberNumber`
- optional user kind -> `reporterUserKind`
- thread linkage fields -> `forumChannelId`, `forumThreadId`, `forumMessageId`

Explicit exclusions:

- summary/details content
- attachment metadata
- audit write state
- raw row timestamps beyond what is needed for the reference projection

### `getLifecycleState`

Expected projection mapping:

- current report status -> `status`
- current completion review state -> `completionReviewStatus`
- status mutation metadata -> `statusUpdatedAt`, `statusUpdatedByDiscordUserId`, `statusNote`
- completion review metadata -> `completionReviewedAt`, `completionReviewedByDiscordUserId`, `completionReviewNote`

Explicit exclusions:

- any write capability
- any forum mutation state
- any audit-posting side effects
- any thread-sync orchestration state

Rule:

- report-store mapping must stay bounded to the existing two projection contracts and must not widen into full-row mirroring

## Composition Boundary With Lookup

Lookup remains responsible for resolving identity from user-provided id or prefix.

Report-store remains responsible only for read-side projections after canonical `reportId` is already known.

Composition rule:

- `FeedbackLookupPort` may precede `FeedbackReportStorePort` in a future consumer flow
- `FeedbackReportStorePort` must not absorb prefix-resolution behavior into its own adapter surface

## Normalized Failure Mapping Plan

The future adapter should normalize upstream outcomes into the existing contract error family:

- no matching canonical `reportId` -> `REPORT_NOT_FOUND`
- structurally invalid `reportId` input -> `INVALID_INPUT`
- transport, auth, unavailable upstream, or non-contract-safe upstream failure -> `UPSTREAM_UNAVAILABLE`

Mapping discipline:

- raw Fitness query or storage details must not become DiscordOS contract truth
- user-facing copy remains outside this adapter boundary
- reference and lifecycle readers should share the same failure normalization shape even if their upstream read paths differ

## Test Strategy Shape

This package does not add tests, but it defines the future test shape.

Planned test categories:

1. pure reference projection fixtures
   - raw upstream reference payload -> `FitnessReportReference`
2. pure lifecycle projection fixtures
   - raw upstream lifecycle payload -> `FeedbackLifecycleState`
3. pure failure normalization fixtures
   - missing -> `REPORT_NOT_FOUND`
   - invalid input -> `INVALID_INPUT`
   - unavailable upstream -> `UPSTREAM_UNAVAILABLE`
4. adapter dependency-injection tests
   - reference and lifecycle readers are injected
   - adapter does not require Discord, Supabase, or env access

Current tooling constraint:

- DiscordOS still lacks repo-local TypeScript tooling
- any real test implementation requires a separate repo-local tooling or execution lane before adapter execution begins

That tooling dependency does not block planning, but it still blocks implementation execution.

## Stub-To-Real Adapter Evolution Plan

Planned evolution sequence:

1. keep the current bundle and contract surfaces type-only
2. add a report-store-only subdirectory under `src/adapters/feedback/report-store/`
3. land pure projection mapping and dependency-shape code first
4. land bridge-facing wiring only in a later execution-approved repo-local lane
5. reassess again before any runtime/schema/data activation

Why this order:

- it preserves the read-side-only boundary
- it avoids leaking Fitness row truth into DiscordOS contract code
- it keeps projection logic separable from future transport wiring
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

- `DiscordOS feedback permission adapter implementation planning package 3`

Also still allowed later, one port at a time:

- `DiscordOS feedback thread-sync adapter implementation planning package`
- `DiscordOS feedback audit adapter implementation planning package`

If later execution is considered, a separate execution-readiness lane is still required first.

## Rule / Pattern / Failure Mode

Rule:

- Implementation planning readiness is not implementation execution readiness.

Pattern:

- Seam chain complete -> one-port implementation planning -> later reassess before any execution.

Failure Mode:

- Read-side implementation-planning inflation into row-ownership transfer or repo mutation.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback permission adapter implementation planning package 3`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the one-port planning chain from read-side projection to permission gating
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
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-2-2026-05-26.md`

## Next Package

`DiscordOS feedback permission adapter implementation planning package 3`

Why:

- report-store implementation planning is now packetized as the second read-side adapter target
- permission remains the next one-port planning seam after identity and read-side projection boundaries are explicit
- execution, runtime, schema, and data mutation still remain blocked
