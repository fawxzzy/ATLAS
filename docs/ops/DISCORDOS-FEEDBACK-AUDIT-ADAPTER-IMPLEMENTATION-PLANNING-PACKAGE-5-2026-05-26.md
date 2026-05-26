# DiscordOS Feedback Audit Adapter Implementation Planning Package 5 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback audit adapter implementation planning package 5`
- Mode: `docs-only implementation planning`
- Control-plane checkpoint: `main@5b02b79`

## Scope

Plan repo-local adapter implementation for exactly one DiscordOS feedback seam:

- `FeedbackAuditPort`

In scope:

- adapter placement inside `repos/DiscordOS`
- dependency boundary back to Fitness-owned audit-posting execution
- append-only event mapping plan
- normalized failure mapping plan
- composition boundary with lookup, report-store, permission, and thread-sync
- test-shape plan
- stub-to-real adapter evolution plan

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read execution
- lookup/report-store/permission/thread-sync replanning beyond explicit composition notes
- preview/unfurl gate reopening
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is implementation-planning-only
- only one port is in scope
- the seam stays append-bounded and non-activating
- no owner-repo tracked content is changed
- no runtime/schema/data ownership transfer is implied
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@5b02b79d744977d0c99f7ee0fdd0353d8ef4b72a`
- `docs/ops/DISCORDOS-FEEDBACK-SEAM-CHAIN-IMPLEMENTATION-READINESS-CHECKPOINT-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-LOOKUP-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-4-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-AUDIT-ADAPTER-CONSUMER-PLANNING-PACKAGE-5-2026-05-26.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/DiscordOS/src/adapters/feedback/README.md`

## Chosen Port

Selected implementation-planning target:

- `FeedbackAuditPort`

Current contract shape:

```ts
interface FeedbackAuditPort {
  postAuditEvent(event: FeedbackAuditEvent): Promise<DiscordOSFeedbackResult<{ messageId: string | null }>>;
}
```

## Why This Port Is Still Fifth

`FeedbackAuditPort` remains the fifth allowed implementation-planning target because:

- lookup, report-store, permission, and thread-sync planning already define the read-side, policy, and bounded sync prerequisites
- audit is the last separately named side-effect seam in the current contract chain
- the existing contract already keeps the surface event-shaped and append-only instead of widening into generic Discord writes

## Planned Repo-Local Adapter Placement

The current type-only bundle entry should remain:

- `repos/DiscordOS/src/adapters/feedback/index.ts`

Planned future audit implementation placement:

- `repos/DiscordOS/src/adapters/feedback/audit/index.ts`
- `repos/DiscordOS/src/adapters/feedback/audit/event.ts`
- `repos/DiscordOS/src/adapters/feedback/audit/normalize.ts`
- `repos/DiscordOS/src/adapters/feedback/audit/types.ts`

Planned role of each file:

- `audit/index.ts`
  - exposes the contract-facing `FeedbackAuditPort` implementation surface
- `audit/event.ts`
  - holds bounded event-shape validation and mapping for `FeedbackAuditEvent`
- `audit/normalize.ts`
  - holds shared failure/result normalization for audit outcomes
- `audit/types.ts`
  - holds adapter-local dependency shapes without importing Fitness runtime code directly

Why this placement:

- it keeps audit isolated from thread-sync and prevents side-effect category collapse
- it preserves `src/adapters/feedback/index.ts` as the bundle-assembly seam
- it keeps audit append behavior explicit instead of diffusing it across other adapters

## Dependency Boundary Back To Fitness

Fitness remains the live audit-posting executor and thread-reply owner.

The planned DiscordOS adapter should depend on an injected upstream audit executor rather than direct Discord clients, persistence clients, or copied runtime code.

Planned dependency class:

- one audit-posting executor that accepts a bounded `FeedbackAuditEvent`
- returns only the minimum raw result needed for normalization into `{ messageId }`

Boundary rules:

- no direct Discord REST client inside DiscordOS
- no copied Fitness audit helper logic
- no route-level event sequencing inside this adapter
- no direct runtime wiring in this package

## Append-Only Event Mapping Plan

This seam stays append-only.

Expected event categories remain:

- `status_update`
- `completion_review`
- `withdraw`
- `reporter_update`
- `staff_update`
- `duplicate_signal`
- `sync_format`

Planned mapping responsibilities:

- accept bounded `FeedbackAuditEvent` input only
- preserve `reportId`, `action`, and event note semantics
- pass through `includeReporterMention`, status fields, completion-review fields, and duplicate count only as event payload material
- normalize result to `{ messageId: string | null }` on success

Explicit exclusions:

- starter-message sync
- forum title/tag/state sync
- generic thread mutation ownership
- arbitrary Discord message posting outside feedback audit

Rule:

- audit mapping must remain append-only and event-shaped and must not widen into generic Discord write ownership

## Normalized Failure Mapping Plan

The future adapter should normalize upstream outcomes into the existing contract error family:

- audit-posting failure -> `AUDIT_COMMENT_FAILED`
- missing canonical `reportId` or thread surface -> `REPORT_NOT_FOUND`
- structurally invalid event payload -> `INVALID_INPUT`
- transport, auth, unavailable upstream, or non-contract-safe upstream failure -> `UPSTREAM_UNAVAILABLE`

Mapping discipline:

- raw Discord REST details and Fitness audit helper internals must not become DiscordOS contract truth
- warning text may be preserved only when it is contract-safe and append-bounded

## Composition Boundary With Lookup, Report-Store, Permission, And Thread-Sync

Lookup remains responsible for canonical report identity resolution.

Report-store remains responsible for bounded reference and lifecycle projections.

Permission remains responsible for broad staff-access evaluation.

Thread-sync remains responsible for the three bounded sync categories.

Audit remains responsible only for append-only audit posting after the earlier seams have already done their work.

Composition rule:

1. `FeedbackLookupPort`
   - resolves canonical `reportId`
2. `FeedbackReportStorePort`
   - provides any needed reference or lifecycle context
3. `FeedbackPermissionPort`
   - answers only the broad staff-access question where required
4. `FeedbackThreadSyncPort`
   - performs any bounded thread-sync action needed by the flow
5. `FeedbackAuditPort`
   - appends the bounded audit event for the already-determined action

Boundary rule:

- `FeedbackAuditPort` must not absorb thread-sync, route-policy, or row-truth ownership into its own adapter surface

## Test Strategy Shape

This package does not add tests, but it defines the future test shape.

Planned test categories:

1. append-only event fixtures
   - bounded `FeedbackAuditEvent` input -> normalized success with `{ messageId }`
2. failure normalization fixtures
   - upstream failure -> `AUDIT_COMMENT_FAILED`
   - missing target -> `REPORT_NOT_FOUND`
   - invalid event payload -> `INVALID_INPUT`
   - unavailable upstream -> `UPSTREAM_UNAVAILABLE`
3. adapter dependency-injection tests
   - adapter consumes only the injected audit executor
   - adapter does not require Discord, Supabase, or env access
4. category-separation tests
   - audit remains separate from thread-sync behavior

Current tooling constraint:

- DiscordOS still lacks repo-local TypeScript tooling
- any real test implementation requires a separate repo-local tooling or execution lane before adapter execution begins

That tooling dependency does not block planning, but it still blocks implementation execution.

## Stub-To-Real Adapter Evolution Plan

Planned evolution sequence:

1. keep the current bundle and contract surfaces type-only
2. add an audit-only subdirectory under `src/adapters/feedback/audit/`
3. land pure event normalization and dependency-shape code first
4. land bridge-facing wiring only in a later execution-approved repo-local lane
5. reassess again before any runtime/schema/data activation

Why this order:

- it keeps audit append behavior category-bounded
- it prevents audit from turning into a generic write seam
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

- `DiscordOS feedback adapter implementation planning chain checkpoint`

If later execution is considered, a separate execution-readiness lane is still required first.

## Rule / Pattern / Failure Mode

Rule:

- Implementation planning readiness is not implementation execution readiness.

Pattern:

- Seam chain complete -> one-port implementation planning -> later reassess before any execution.

Failure Mode:

- Audit implementation-planning inflation into generic Discord write ownership or repo mutation.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback adapter implementation planning chain checkpoint`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- stop the one-port planning chain here and reassess at the implementation-planning-chain level
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
- `docs/ops/DISCORDOS-FEEDBACK-AUDIT-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-5-2026-05-26.md`

## Next Package

`DiscordOS feedback adapter implementation planning chain checkpoint`

Why:

- audit implementation planning is now packetized as the fifth one-port adapter planning target
- the named one-port planning chain is complete enough to reassess before any repo execution
- execution, runtime, schema, and data mutation still remain blocked
