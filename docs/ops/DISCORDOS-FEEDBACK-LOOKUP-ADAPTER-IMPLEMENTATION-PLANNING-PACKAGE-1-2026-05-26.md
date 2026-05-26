# DiscordOS Feedback Lookup Adapter Implementation Planning Package 1 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback lookup adapter implementation planning package 1`
- Mode: `docs-only implementation planning`
- Control-plane checkpoint: `main@fb28fa4`

## Scope

Plan repo-local adapter implementation for exactly one DiscordOS feedback seam:

- `FeedbackLookupPort`

In scope:

- adapter placement inside `repos/DiscordOS`
- dependency boundary back to Fitness-owned lookup execution
- contract mapping plan
- normalized failure mapping plan
- test-shape plan
- stub-to-real adapter evolution plan

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read execution
- report-store planning
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
- no owner-repo tracked content is changed
- no runtime/schema/data ownership transfer is implied
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@fb28fa466380871083f9589caf096ac943b2b799`
- `docs/ops/DISCORDOS-FEEDBACK-SEAM-CHAIN-IMPLEMENTATION-READINESS-CHECKPOINT-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
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

- `FeedbackLookupPort`

Current contract shape:

```ts
interface FeedbackLookupPort {
  findReportIdentity(reportIdOrPrefix: string): Promise<DiscordOSFeedbackResult<FeedbackCardIdentity>>;
}
```

## Why This Port Is Still First

`FeedbackLookupPort` remains the first allowed implementation-planning target because:

- the seam-chain readiness checkpoint explicitly named it as the first repo-local adapter planning target
- it is still the smallest read-side seam in the chain
- it isolates identity resolution without pulling lifecycle, thread, audit, or permission coupling into the first adapter package
- it can be planned as a pure contract-mapping boundary before DiscordOS has any runtime, schema, or storage surface

## Planned Repo-Local Adapter Placement

The current type-only bundle entry should remain:

- `repos/DiscordOS/src/adapters/feedback/index.ts`

Planned future lookup-only implementation placement:

- `repos/DiscordOS/src/adapters/feedback/lookup/index.ts`
- `repos/DiscordOS/src/adapters/feedback/lookup/normalize.ts`
- `repos/DiscordOS/src/adapters/feedback/lookup/types.ts`

Planned role of each file:

- `lookup/index.ts`
  - exposes the lookup adapter factory and the contract-facing `FeedbackLookupPort` implementation surface
- `lookup/normalize.ts`
  - holds pure mapping from upstream Fitness lookup outcomes into `DiscordOSFeedbackResult<FeedbackCardIdentity>`
- `lookup/types.ts`
  - holds adapter-local dependency shapes for upstream lookup execution without importing Fitness runtime code directly

Why this placement:

- it keeps lookup isolated from report-store, permission, thread-sync, and audit
- it preserves `src/adapters/feedback/index.ts` as the bundle-assembly seam
- it allows pure result normalization to stay separated from any future transport wiring

## Dependency Boundary Back To Fitness

Fitness remains the lookup executor.

The planned DiscordOS adapter should depend on an injected upstream executor shape rather than direct database or Discord clients.

Planned dependency class:

- an adapter-local lookup source dependency that accepts `reportIdOrPrefix`
- returns only the minimum raw lookup outcome needed for normalization
- can later be satisfied by a Fitness-owned bridge or transport without moving row truth into DiscordOS

Boundary rules:

- no direct Supabase client inside DiscordOS
- no copied Fitness `bug-reports.ts` logic
- no DiscordOS-owned row selection logic
- no direct runtime wiring in this package

## Contract Mapping Plan

The future adapter should map only the minimum identity shape required by `FeedbackLookupPort`.

Expected success mapping:

- Fitness full report id -> `FeedbackCardIdentity.reportId`
- Fitness report type -> `FeedbackCardIdentity.reportType`
- Fitness short display id or prefix display value -> `FeedbackCardIdentity.shortDisplayId`
- Fitness created timestamp -> `FeedbackCardIdentity.createdAt`
- Fitness updated timestamp -> `FeedbackCardIdentity.updatedAt`

Explicit exclusions from this adapter:

- lifecycle state
- reporter reference details
- permission state
- forum thread sync state
- audit event shaping

Rule:

- lookup mapping must stay identity-only and not silently expand into row-reference or lifecycle projection scope

## Normalized Failure Mapping Plan

The future adapter should normalize upstream outcomes into the existing contract error family:

- no matching report -> `REPORT_NOT_FOUND`
- multiple prefix matches -> `REPORT_ID_AMBIGUOUS`
- structurally invalid lookup input -> `INVALID_INPUT`
- transport, auth, unavailable upstream, or non-contract-safe upstream failure -> `UPSTREAM_UNAVAILABLE`

Mapping discipline:

- DiscordOS should not expose raw Fitness error strings as contract truth
- user-facing copy remains outside this adapter boundary
- warning text may be preserved only when it is contract-safe and does not leak owner-runtime internals

## Test Strategy Shape

This package does not add tests, but it defines the future test shape.

Planned test categories:

1. pure success mapping fixtures
   - raw upstream identity payload -> `FeedbackCardIdentity`
2. pure failure normalization fixtures
   - missing -> `REPORT_NOT_FOUND`
   - ambiguous -> `REPORT_ID_AMBIGUOUS`
   - invalid input -> `INVALID_INPUT`
   - unavailable upstream -> `UPSTREAM_UNAVAILABLE`
3. adapter factory dependency-injection tests
   - adapter consumes only the injected lookup source
   - adapter does not require Discord, Supabase, or env access

Current tooling constraint:

- DiscordOS still lacks repo-local TypeScript tooling
- any real test implementation requires a separate repo-local tooling or execution lane before adapter execution begins

That tooling dependency does not block planning, but it still blocks implementation execution.

## Stub-To-Real Adapter Evolution Plan

Planned evolution sequence:

1. keep the current bundle and contract surfaces type-only
2. add a lookup-only subdirectory under `src/adapters/feedback/lookup/`
3. land pure normalization and dependency-shape code first
4. land bridge-facing wiring only in a later execution-approved repo-local lane
5. reassess again before any runtime/schema/data activation

Why this order:

- it keeps the first execution surface pure and testable
- it prevents early coupling to transport or runtime surfaces
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

- `DiscordOS feedback report-store adapter implementation planning package 2`

Also still allowed later, one port at a time:

- `DiscordOS feedback permission adapter implementation planning package`
- side-effect adapter implementation planning only after the read-side implementation-planning chain remains stable

If later execution is considered, a separate execution-readiness lane is still required first.

## Rule / Pattern / Failure Mode

Rule:

- Implementation planning readiness is not implementation execution readiness.

Pattern:

- Seam chain complete -> one-port implementation planning -> later reassess before any execution.

Failure Mode:

- Implementation-planning inflation into repo mutation or runtime-readiness.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback report-store adapter implementation planning package 2`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the read-side implementation-planning chain one port at a time
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
- `docs/ops/DISCORDOS-FEEDBACK-LOOKUP-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-1-2026-05-26.md`

## Next Package

`DiscordOS feedback report-store adapter implementation planning package 2`

Why:

- lookup implementation planning is now packetized
- report-store remains the next read-side boundary in the same one-port planning chain
- execution, runtime, schema, and data mutation still remain blocked
