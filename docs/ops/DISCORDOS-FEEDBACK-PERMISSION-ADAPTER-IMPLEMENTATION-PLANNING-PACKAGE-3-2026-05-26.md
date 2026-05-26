# DiscordOS Feedback Permission Adapter Implementation Planning Package 3 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback permission adapter implementation planning package 3`
- Mode: `docs-only implementation planning`
- Control-plane checkpoint: `main@b37bbe0`

## Scope

Plan repo-local adapter implementation for exactly one DiscordOS feedback seam:

- `FeedbackPermissionPort`

In scope:

- adapter placement inside `repos/DiscordOS`
- dependency boundary back to Fitness-owned broad staff-access evaluation
- boolean policy mapping plan
- malformed/missing permission normalization plan
- composition boundary with lookup and report-store
- test-shape plan
- stub-to-real adapter evolution plan

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read execution
- lookup/report-store replanning beyond explicit composition notes
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
- the seam stays policy-bounded and non-activating
- no owner-repo tracked content is changed
- no runtime/schema/data ownership transfer is implied
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@b37bbe04ef20fcdae151422947f2380665cf2520`
- `docs/ops/DISCORDOS-FEEDBACK-SEAM-CHAIN-IMPLEMENTATION-READINESS-CHECKPOINT-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-LOOKUP-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/DiscordOS/src/adapters/feedback/README.md`

## Chosen Port

Selected implementation-planning target:

- `FeedbackPermissionPort`

Current contract shape:

```ts
interface FeedbackPermissionPort {
  canAccessAnyFeedbackReport(permissions: string | null): boolean;
}
```

## Why This Port Is Still Third

`FeedbackPermissionPort` remains the third allowed implementation-planning target because:

- the seam-chain readiness checkpoint cleared one-port repo-local planning only
- lookup and report-store planning already define identity and read-side projection seams
- the next narrow seam is the broad staff-access decision that composes with those two earlier seams
- this port can stay policy-bounded without widening into a full authorization engine

## Planned Repo-Local Adapter Placement

The current type-only bundle entry should remain:

- `repos/DiscordOS/src/adapters/feedback/index.ts`

Planned future permission implementation placement:

- `repos/DiscordOS/src/adapters/feedback/permission/index.ts`
- `repos/DiscordOS/src/adapters/feedback/permission/normalize.ts`
- `repos/DiscordOS/src/adapters/feedback/permission/types.ts`

Planned role of each file:

- `permission/index.ts`
  - exposes the contract-facing `FeedbackPermissionPort` implementation surface
- `permission/normalize.ts`
  - holds pure normalization for missing or malformed permission inputs into the current boolean outcome
- `permission/types.ts`
  - holds adapter-local dependency shapes for upstream permission evaluation without importing Fitness runtime code directly

Why this placement:

- it keeps permission isolated from lookup, report-store, thread-sync, and audit
- it preserves `src/adapters/feedback/index.ts` as the bundle-assembly seam
- it keeps the policy seam narrow instead of spreading permission logic across read-side or side-effect seams

## Dependency Boundary Back To Fitness

Fitness remains the live permission interpreter.

The planned DiscordOS adapter should depend on an injected upstream evaluator shape rather than direct Discord clients or copied bitfield logic.

Planned dependency class:

- an adapter-local broad-staff-access evaluator that accepts `permissions: string | null`
- returns only the minimum raw outcome needed for normalization into the contract boolean

Boundary rules:

- no copied Fitness permission-bit parsing logic
- no direct Discord permission interpretation embedded in DiscordOS in this package
- no row-local ownership checks inside this adapter
- no direct runtime wiring in this package

## Boolean Policy Mapping Plan

The future adapter should map only the current broad staff-access question:

- caller has broad staff access across reports -> `true`
- caller lacks broad staff access -> `false`

Current broad access meaning remains Fitness-owned and tied to the live rule around privileged Discord permissions.

This port intentionally does not answer:

- whether the caller owns the report
- whether the report status allows a particular action
- whether a specific downstream mutation should proceed

Rule:

- permission mapping must stay broad-staff-access only and must not widen into action-by-action policy ownership

## Missing / Malformed Permission Normalization Plan

This contract returns `boolean`, not a richer result envelope.

Normalization rule:

- missing permission bitfield -> `false`
- malformed or unusable permission value -> `false`
- valid non-staff permission set -> `false`
- valid broad staff permission set -> `true`

Why:

- it mirrors the current narrow contract shape in `repos/DiscordOS/src/contracts/feedback.ts`
- it preserves the current seam intent without inventing a broader permission error contract mid-chain

## Composition Boundary With Lookup And Report-Store

Lookup remains responsible for report identity resolution.

Report-store remains responsible for read-side reference and lifecycle projection.

Permission remains responsible only for broad staff-access evaluation.

Composition rule:

1. `FeedbackLookupPort`
   - resolves canonical `reportId`
2. `FeedbackReportStorePort`
   - provides reporter reference and lifecycle state when needed
3. `FeedbackPermissionPort`
   - answers only the broad staff-access question
4. a future consumer composes all three to decide whether the action may continue

Boundary rule:

- `FeedbackPermissionPort` must not absorb reporter-ownership checks or lifecycle-based action checks into its own adapter surface

## Test Strategy Shape

This package does not add tests, but it defines the future test shape.

Planned test categories:

1. pure boolean normalization fixtures
   - broad staff permission input -> `true`
   - non-staff permission input -> `false`
   - missing permission input -> `false`
   - malformed permission input -> `false`
2. adapter dependency-injection tests
   - adapter consumes only the injected broad-staff evaluator
   - adapter does not require Discord, Supabase, or env access
3. composition-boundary tests
   - permission adapter remains independent from lookup/store outputs

Current tooling constraint:

- DiscordOS still lacks repo-local TypeScript tooling
- any real test implementation requires a separate repo-local tooling or execution lane before adapter execution begins

That tooling dependency does not block planning, but it still blocks implementation execution.

## Stub-To-Real Adapter Evolution Plan

Planned evolution sequence:

1. keep the current bundle and contract surfaces type-only
2. add a permission-only subdirectory under `src/adapters/feedback/permission/`
3. land pure normalization and dependency-shape code first
4. land bridge-facing wiring only in a later execution-approved repo-local lane
5. reassess again before any runtime/schema/data activation

Why this order:

- it keeps the seam policy-bounded
- it prevents permission logic from drifting into route-level policy ownership
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

- `DiscordOS feedback thread-sync adapter implementation planning package 4`

Also still allowed later, one port at a time:

- `DiscordOS feedback audit adapter implementation planning package`

If later execution is considered, a separate execution-readiness lane is still required first.

## Rule / Pattern / Failure Mode

Rule:

- Implementation planning readiness is not implementation execution readiness.

Pattern:

- Seam chain complete -> one-port implementation planning -> later reassess before any execution.

Failure Mode:

- Policy-seam implementation-planning inflation into permission ownership transfer or repo mutation.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback thread-sync adapter implementation planning package 4`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the one-port planning chain into the first side-effect seam only after read-side and policy seams are explicit
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
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-3-2026-05-26.md`

## Next Package

`DiscordOS feedback thread-sync adapter implementation planning package 4`

Why:

- permission implementation planning is now packetized as the third one-port adapter planning target
- thread-sync is the next remaining seam once lookup, report-store, and permission boundaries are explicit
- execution, runtime, schema, and data mutation still remain blocked
